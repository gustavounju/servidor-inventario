import hashlib
import os
import queue
import threading
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Callable, Optional


class OcrQueueFullError(RuntimeError):
    """Raised when the OCR queue cannot accept more work."""


class OcrFileTooLargeError(RuntimeError):
    """Raised when the uploaded file exceeds the configured OCR size limit."""


@dataclass
class OcrJob:
    job_id: str
    file_hash: str
    file_path: Optional[str]
    filename: str
    processor: Optional[Callable[[str], str]]
    state: str = "queued"
    message: str = "En cola"
    text: str = ""
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None


class PdfOcrQueue:
    def __init__(self):
        self.max_concurrent = max(1, int(os.environ.get("PDF_OCR_MAX_CONCURRENT", "2")))
        self.max_queue = max(1, int(os.environ.get("PDF_OCR_MAX_QUEUE", "10")))
        self.max_mb = max(1, int(os.environ.get("PDF_OCR_MAX_MB", "100")))
        self.cache_size = max(1, int(os.environ.get("PDF_OCR_CACHE_SIZE", "32")))
        self.job_ttl_seconds = max(300, int(os.environ.get("PDF_OCR_JOB_TTL_SECONDS", "3600")))

        self._queue = queue.Queue(maxsize=self.max_queue)
        self._jobs = {}
        self._cache = OrderedDict()
        self._lock = threading.Lock()

        for index in range(self.max_concurrent):
            worker = threading.Thread(target=self._worker_loop, name=f"pdf-ocr-{index + 1}", daemon=True)
            worker.start()

    def enqueue(self, file_path, filename, processor):
        file_size = os.path.getsize(file_path)
        max_bytes = self.max_mb * 1024 * 1024
        if file_size > max_bytes:
            raise OcrFileTooLargeError(
                f"El OCR acepta hasta {self.max_mb} MB por archivo. Este PDF pesa {(file_size / (1024 * 1024)):.1f} MB."
            )

        file_hash = self._compute_sha256(file_path)
        cached = None
        with self._lock:
            cached = self._cache.get(file_hash)
            if cached is not None:
                self._cache.move_to_end(file_hash)
                job = OcrJob(
                    job_id=uuid.uuid4().hex,
                    file_hash=file_hash,
                    file_path=None,
                    filename=filename,
                    processor=None,
                    state="success",
                    message="Resultado recuperado de cache",
                    text=cached,
                    finished_at=time.time(),
                )
                self._jobs[job.job_id] = job
                self._cleanup_expired_jobs_locked()
                return self._serialize_job_locked(job)

        queued_job = OcrJob(
            job_id=uuid.uuid4().hex,
            file_hash=file_hash,
            file_path=file_path,
            filename=filename,
            processor=processor,
        )

        try:
            self._queue.put_nowait(queued_job)
        except queue.Full as exc:
            raise OcrQueueFullError(
                "El OCR está ocupado. Hay demasiados trabajos en espera. Reintenta en unos minutos."
            ) from exc

        with self._lock:
            self._jobs[queued_job.job_id] = queued_job
            self._cleanup_expired_jobs_locked()
            return self._serialize_job_locked(queued_job)

    def get_status(self, job_id):
        with self._lock:
            self._cleanup_expired_jobs_locked()
            job = self._jobs.get(job_id)
            if not job:
                return None
            return self._serialize_job_locked(job)

    def _worker_loop(self):
        while True:
            job = self._queue.get()
            try:
                with self._lock:
                    job.started_at = time.time()
                    job.state = "running"
                    job.message = "Procesando OCR"

                text = job.processor(job.file_path)

                with self._lock:
                    job.state = "success"
                    job.message = "OCR completado"
                    job.text = text
                    job.finished_at = time.time()
                    self._cache[job.file_hash] = text
                    self._cache.move_to_end(job.file_hash)
                    while len(self._cache) > self.cache_size:
                        self._cache.popitem(last=False)
            except Exception as exc:
                with self._lock:
                    job.state = "error"
                    job.message = str(exc)
                    job.finished_at = time.time()
            finally:
                if job.file_path and os.path.exists(job.file_path):
                    try:
                        os.remove(job.file_path)
                    except OSError:
                        pass
                self._queue.task_done()

    def _serialize_job_locked(self, job):
        data = {
            "job_id": job.job_id,
            "status": job.state,
            "message": job.message,
        }
        if job.state == "queued":
            data["queue_position"] = self._queue_position_locked(job.job_id)
        if job.state == "success":
            data["text"] = job.text
        return data

    def _queue_position_locked(self, job_id):
        with self._queue.mutex:
            for index, queued_job in enumerate(self._queue.queue, start=1):
                if queued_job.job_id == job_id:
                    return index
        return 0

    def _cleanup_expired_jobs_locked(self):
        now = time.time()
        expired = []
        for job_id, job in self._jobs.items():
            reference_time = job.finished_at or job.created_at
            if now - reference_time > self.job_ttl_seconds:
                expired.append(job_id)
        for job_id in expired:
            self._jobs.pop(job_id, None)

    @staticmethod
    def _compute_sha256(file_path):
        digest = hashlib.sha256()
        with open(file_path, "rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
        return digest.hexdigest()


pdf_ocr_queue = PdfOcrQueue()
