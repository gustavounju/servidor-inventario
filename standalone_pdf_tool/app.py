import os
import sys
import tempfile

from flask import Flask, jsonify, redirect, render_template, request, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pdf_ocr_service import LocalOCRConfigurationError, extract_pdf_text_local
from services.pdf_ocr_queue import OcrFileTooLargeError, OcrQueueFullError, pdf_ocr_queue

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(PROJECT_ROOT, "static"),
)


@app.get("/")
def index():
    return redirect(url_for("pdf_local_tool"))


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/pdf-local")
def pdf_local_tool():
    return render_template("pdf_local_tool_standalone.html")


@app.post("/api/local/pdf-ocr")
def local_pdf_ocr():
    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        return jsonify({"status": "error", "message": "No se recibió ningún PDF."}), 400

    if not uploaded.filename.lower().endswith(".pdf"):
        return jsonify({"status": "error", "message": "El archivo debe ser PDF."}), 400

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            temp_path = tmp.name
            uploaded.save(temp_path)

        job = pdf_ocr_queue.enqueue(temp_path, uploaded.filename, extract_pdf_text_local)
        temp_path = None
        return jsonify(job), 202
    except OcrQueueFullError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 429
    except OcrFileTooLargeError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 413
    except LocalOCRConfigurationError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


@app.get("/api/local/pdf-ocr/<job_id>")
def local_pdf_ocr_status(job_id):
    job = pdf_ocr_queue.get_status(job_id)
    if not job:
        return jsonify({"status": "error", "message": "Trabajo OCR no encontrado o expirado."}), 404
    return jsonify(job)


if __name__ == "__main__":
    host = os.environ.get("PDF_TOOL_HOST", "0.0.0.0")
    port = int(os.environ.get("PDF_TOOL_PORT", "5090"))
    debug = os.environ.get("PDF_TOOL_DEBUG", "false").strip().lower() == "true"
    print(f"Editor PDF Local standalone en http://{host}:{port}/pdf-local")
    app.run(host=host, port=port, debug=debug)
