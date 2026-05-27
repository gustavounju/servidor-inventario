(() => {
    const state = {
        originalPdfBytes: null,
        originalFileName: "",
        draggedItem: null,
        pdfDocument: null,
        infoBaseText: "",
        loadToken: 0,
        compressRunId: 0,
        thumbnailObserver: null,
        thumbnailQueue: [],
        pendingThumbs: new Set(),
        renderingThumbs: new Set(),
        thumbnailCache: new Map(),
        maxParallelThumbs: 2,
    };

    class CancellationError extends Error {
        constructor(message) {
            super(message);
            this.name = "CancellationError";
        }
    }

    function byId(id) {
        return document.getElementById(id);
    }

    function config() {
        return window.pdfLocalToolConfig || {};
    }

    function resolveWorkerSrc() {
        const configured = config().workerSrc || "/static/vendor/pdfjs/pdf.worker.min.js";
        try {
            const url = new URL(configured, window.location.origin);
            if (url.origin !== window.location.origin) {
                return `${window.location.origin}${url.pathname}${url.search}${url.hash}`;
            }
            return url.toString();
        } catch (_error) {
            if (configured.startsWith("/")) {
                return `${window.location.origin}${configured}`;
            }
            return configured;
        }
    }

    function buildOcrStatusUrl(jobId) {
        const template = config().ocrStatusEndpointTemplate || "";
        if (template.includes("__JOB_ID__")) {
            return template.replace("__JOB_ID__", encodeURIComponent(jobId));
        }
        return `${config().ocrEndpoint.replace(/\/$/, "")}/${encodeURIComponent(jobId)}`;
    }

    function updateToolbarInfo(statusText = "") {
        const suffix = statusText ? ` | ${statusText}` : "";
        byId("pdfInfo").innerText = `${state.infoBaseText}${suffix}`.trim();
    }

    function setEmptyState(message) {
        byId("pdfPagesContainer").innerHTML = `
            <div class="pdf-tool-empty">
                <i class="bi bi-file-earmark-pdf" style="font-size: 5rem; opacity: 0.5;"></i>
                <p style="font-size: 1.1rem; margin-top: 16px; font-weight: bold; color: var(--pdf-text);">${message}</p>
                <p style="font-size: 0.9rem; opacity: 0.8; max-width: 560px; margin: 8px auto;">
                    Todo el procesamiento se realiza dentro de la intranet. El archivo no se envía a servicios externos.
                </p>
            </div>`;
    }

    function resetPdfState() {
        state.loadToken += 1;
        state.compressRunId += 1;
        state.originalPdfBytes = null;
        state.originalFileName = "";
        state.pdfDocument = null;
        state.draggedItem = null;
        state.thumbnailQueue = [];
        state.pendingThumbs.clear();
        state.renderingThumbs.clear();
        if (state.thumbnailObserver) {
            state.thumbnailObserver.disconnect();
            state.thumbnailObserver = null;
        }
        state.thumbnailCache.forEach((cached) => {
            if (cached.url) {
                URL.revokeObjectURL(cached.url);
            }
        });
        state.thumbnailCache.clear();
    }

    function yieldToBrowser() {
        return new Promise((resolve) => setTimeout(resolve, 0));
    }

    function getVisiblePageItems() {
        return Array.from(byId("pdfPagesContainer").children)
            .filter((child) => child.classList.contains("pdf-page-item"));
    }

    function updatePageNumbers() {
        getVisiblePageItems().forEach((child, index) => {
            const label = child.querySelector(".pdf-page-label");
            if (label) {
                label.innerText = `Pág. ${index + 1}`;
            }
        });
    }

    function handleDragStart() {
        state.draggedItem = this;
        this.classList.add("dragging");
    }

    function handleDragOver(event) {
        event.preventDefault();
        return false;
    }

    function handleDragEnter() {
        if (this !== state.draggedItem) {
            this.classList.add("drag-over");
        }
    }

    function handleDragLeave() {
        this.classList.remove("drag-over");
    }

    function handleDrop(event) {
        event.stopPropagation();
        if (state.draggedItem !== this) {
            const container = byId("pdfPagesContainer");
            const children = getVisiblePageItems();
            const draggedIndex = children.indexOf(state.draggedItem);
            const targetIndex = children.indexOf(this);
            if (draggedIndex < targetIndex) {
                container.insertBefore(state.draggedItem, this.nextElementSibling);
            } else {
                container.insertBefore(state.draggedItem, this);
            }
            updatePageNumbers();
        }
        return false;
    }

    function handleDragEnd() {
        this.classList.remove("dragging");
        getVisiblePageItems().forEach((child) => {
            child.classList.remove("drag-over");
        });
    }

    function movePage(pageDiv, direction) {
        const container = byId("pdfPagesContainer");
        const children = getVisiblePageItems();
        const index = children.indexOf(pageDiv);
        if (direction === -1 && index > 0) {
            container.insertBefore(pageDiv, children[index - 1]);
        } else if (direction === 1 && index < children.length - 1) {
            container.insertBefore(pageDiv, children[index + 2]);
        }
        updatePageNumbers();
    }

    function rotatePage(pageDiv, delta) {
        const currentRotation = parseInt(pageDiv.dataset.rotation || "0", 10);
        const nextRotation = ((currentRotation + delta) % 360 + 360) % 360;
        pageDiv.dataset.rotation = String(nextRotation);
        const img = pageDiv.querySelector("img");
        if (img) {
            img.style.transform = `rotate(${nextRotation}deg)`;
        }
    }

    function getThumbnailScale(pageCount, fileSizeMb) {
        if (pageCount >= 240 || fileSizeMb >= 120) {
            return 0.28;
        }
        if (pageCount >= 120 || fileSizeMb >= 60) {
            return 0.36;
        }
        if (pageCount >= 60 || fileSizeMb >= 25) {
            return 0.46;
        }
        return 0.58;
    }

    function createPageElement(originalIndex) {
        const pageDiv = document.createElement("div");
        pageDiv.className = "pdf-page-item";
        pageDiv.dataset.originalIndex = String(originalIndex);
        pageDiv.dataset.rotation = "0";
        pageDiv.dataset.thumbReady = "0";
        pageDiv.draggable = true;
        pageDiv.addEventListener("dragstart", handleDragStart);
        pageDiv.addEventListener("dragover", handleDragOver);
        pageDiv.addEventListener("dragenter", handleDragEnter);
        pageDiv.addEventListener("dragleave", handleDragLeave);
        pageDiv.addEventListener("drop", handleDrop);
        pageDiv.addEventListener("dragend", handleDragEnd);

        const label = document.createElement("div");
        label.className = "pdf-page-label";

        const previewShell = document.createElement("div");
        previewShell.className = "pdf-page-preview";

        const skeleton = document.createElement("div");
        skeleton.className = "pdf-page-skeleton";

        const img = document.createElement("img");
        img.alt = `Vista previa página ${originalIndex + 1}`;
        img.setAttribute("draggable", "false");
        img.loading = "lazy";

        previewShell.append(skeleton, img);

        const controls = document.createElement("div");
        controls.className = "pdf-controls";

        const left = document.createElement("button");
        left.className = "pdf-ctrl-move";
        left.innerHTML = '<i class="bi bi-arrow-left"></i>';
        left.title = "Mover página atrás";
        left.addEventListener("click", (event) => {
            event.stopPropagation();
            movePage(pageDiv, -1);
        });

        const rotateLeft = document.createElement("button");
        rotateLeft.className = "pdf-ctrl-rotate-left";
        rotateLeft.innerHTML = '<i class="bi bi-arrow-counterclockwise"></i>';
        rotateLeft.title = "Girar a la izquierda";
        rotateLeft.addEventListener("click", (event) => {
            event.stopPropagation();
            rotatePage(pageDiv, -90);
        });

        const del = document.createElement("button");
        del.className = "pdf-ctrl-delete";
        del.innerHTML = '<i class="bi bi-trash"></i>';
        del.title = "Eliminar página";
        del.addEventListener("click", (event) => {
            event.stopPropagation();
            pageDiv.remove();
            updatePageNumbers();
            updateThumbnailProgress();
        });

        const rotateRight = document.createElement("button");
        rotateRight.className = "pdf-ctrl-rotate-right";
        rotateRight.innerHTML = '<i class="bi bi-arrow-clockwise"></i>';
        rotateRight.title = "Girar a la derecha";
        rotateRight.addEventListener("click", (event) => {
            event.stopPropagation();
            rotatePage(pageDiv, 90);
        });

        const right = document.createElement("button");
        right.className = "pdf-ctrl-move";
        right.innerHTML = '<i class="bi bi-arrow-right"></i>';
        right.title = "Mover página adelante";
        right.addEventListener("click", (event) => {
            event.stopPropagation();
            movePage(pageDiv, 1);
        });

        const ocrBtn = document.createElement("button");
        ocrBtn.innerHTML = '<i class="bi bi-text-paragraph"></i>';
        ocrBtn.title = "Extraer texto de esta página (OCR)";
        ocrBtn.style.background = "#2563eb";
        ocrBtn.style.color = "#fff";
        ocrBtn.addEventListener("click", (event) => {
            event.stopPropagation();
            const rot = parseInt(pageDiv.dataset.rotation || "0", 10);
            runLocalPdfOCR(originalIndex, rot);
        });

        controls.append(left, rotateLeft, del, ocrBtn, rotateRight, right);
        pageDiv.append(label, previewShell, controls);
        byId("pdfPagesContainer").appendChild(pageDiv);
    }

    function initializeThumbnailObserver() {
        if (state.thumbnailObserver) {
            state.thumbnailObserver.disconnect();
        }

        state.thumbnailObserver = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    scheduleThumbnailRender(entry.target);
                }
            });
        }, {
            root: byId("pdfPagesContainer"),
            rootMargin: "260px 0px",
            threshold: 0.01,
        });

        getVisiblePageItems().forEach((item) => state.thumbnailObserver.observe(item));
    }

    function scheduleThumbnailRender(pageDiv) {
        const pageIndex = parseInt(pageDiv.dataset.originalIndex, 10);
        if (pageDiv.dataset.thumbReady === "1" || state.pendingThumbs.has(pageIndex) || state.renderingThumbs.has(pageIndex)) {
            return;
        }
        state.pendingThumbs.add(pageIndex);
        state.thumbnailQueue.push(pageIndex);
        pumpThumbnailQueue();
    }

    async function pumpThumbnailQueue() {
        while (state.renderingThumbs.size < state.maxParallelThumbs && state.thumbnailQueue.length > 0) {
            const pageIndex = state.thumbnailQueue.shift();
            if (pageIndex === undefined || state.renderingThumbs.has(pageIndex)) {
                continue;
            }
            state.pendingThumbs.delete(pageIndex);
            state.renderingThumbs.add(pageIndex);
            renderThumbnail(pageIndex, state.loadToken)
                .catch(() => {})
                .finally(() => {
                    state.renderingThumbs.delete(pageIndex);
                    pumpThumbnailQueue();
                });
        }
    }

    async function canvasToBlob(canvas, type, quality) {
        if (canvas.toBlob) {
            return new Promise((resolve) => canvas.toBlob(resolve, type, quality));
        }
        const dataUrl = canvas.toDataURL(type, quality);
        const response = await fetch(dataUrl);
        return response.blob();
    }

    function updateThumbnailProgress() {
        const total = getVisiblePageItems().length;
        const loaded = getVisiblePageItems().filter((item) => item.dataset.thumbReady === "1").length;
        if (!total) {
            updateToolbarInfo();
            return;
        }
        updateToolbarInfo(`Miniaturas ${loaded}/${total}`);
    }

    async function renderThumbnail(pageIndex, loadToken) {
        if (!state.pdfDocument || loadToken !== state.loadToken) {
            return;
        }

        const pageDiv = getVisiblePageItems().find((item) => parseInt(item.dataset.originalIndex, 10) === pageIndex);
        if (!pageDiv) {
            return;
        }

        const cached = state.thumbnailCache.get(pageIndex);
        if (cached) {
            applyThumbnail(pageDiv, cached.url);
            updateThumbnailProgress();
            return;
        }

        const page = await state.pdfDocument.getPage(pageIndex + 1);
        if (loadToken !== state.loadToken) {
            throw new CancellationError("La carga del PDF fue reemplazada por otro archivo.");
        }

        const fileSizeMb = state.originalPdfBytes.length / (1024 * 1024);
        const scale = getThumbnailScale(state.pdfDocument.numPages, fileSizeMb);
        const viewport = page.getViewport({ scale });
        const canvas = document.createElement("canvas");
        const context = canvas.getContext("2d", { alpha: false });
        canvas.width = Math.max(1, Math.floor(viewport.width));
        canvas.height = Math.max(1, Math.floor(viewport.height));

        await page.render({ canvasContext: context, viewport }).promise;
        if (loadToken !== state.loadToken) {
            throw new CancellationError("La carga del PDF fue reemplazada por otro archivo.");
        }

        const blob = await canvasToBlob(canvas, "image/jpeg", 0.72);
        const url = URL.createObjectURL(blob);
        state.thumbnailCache.set(pageIndex, { url });
        applyThumbnail(pageDiv, url);
        canvas.width = 0;
        canvas.height = 0;
        updateThumbnailProgress();
    }

    function applyThumbnail(pageDiv, imageUrl) {
        const img = pageDiv.querySelector("img");
        const skeleton = pageDiv.querySelector(".pdf-page-skeleton");
        if (!img) {
            return;
        }
        img.src = imageUrl;
        img.style.display = "block";
        if (skeleton) {
            skeleton.style.display = "none";
        }
        const rotation = parseInt(pageDiv.dataset.rotation || "0", 10);
        img.style.transform = `rotate(${rotation}deg)`;
        pageDiv.dataset.thumbReady = "1";
    }

    function getPageInstructions() {
        const pageInstructions = getVisiblePageItems().map((child) => ({
            originalIndex: parseInt(child.dataset.originalIndex, 10),
            rotation: parseInt(child.dataset.rotation || "0", 10),
        }));

        if (!pageInstructions.length) {
            alert("No hay páginas para guardar.");
            return null;
        }
        return pageInstructions;
    }

    async function getModifiedPdfBytes() {
        const pageInstructions = getPageInstructions();
        if (!pageInstructions) {
            return null;
        }

        const pdfDoc = await PDFLib.PDFDocument.create();
        const srcDoc = await PDFLib.PDFDocument.load(state.originalPdfBytes);
        const copiedPages = await pdfDoc.copyPages(srcDoc, pageInstructions.map((item) => item.originalIndex));

        copiedPages.forEach((page, index) => {
            const rotation = pageInstructions[index].rotation;
            if (rotation) {
                const currentAngle = page.getRotation ? page.getRotation().angle : 0;
                page.setRotation(PDFLib.degrees((currentAngle + rotation) % 360));
            }
            pdfDoc.addPage(page);
        });

        return pdfDoc.save({ useObjectStreams: true });
    }

    async function savePdf() {
        const btn = byId("btnSave");
        const originalHtml = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Procesando...';
        updateToolbarInfo("Preparando descarga...");

        try {
            const pdfBytes = await getModifiedPdfBytes();
            if (pdfBytes) {
                downloadBlob(pdfBytes, `modificado_${state.originalFileName}`);
            }
        } catch (error) {
            alert(`Error al guardar el PDF: ${error.message}`);
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
            updateToolbarInfo();
        }
    }

    async function splitPdfBySize() {
        const btn = byId("btnSplit");
        const originalHtml = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Dividiendo...';

        try {
            const pdfBytes = await getModifiedPdfBytes();
            if (!pdfBytes) {
                return;
            }

            const maxSizeMb = parseFloat(byId("maxMbInput").value) || 5;
            const currentSizeMb = pdfBytes.length / (1024 * 1024);
            if (currentSizeMb <= maxSizeMb) {
                alert(`El documento pesa ${currentSizeMb.toFixed(2)} MB, menor o igual a ${maxSizeMb} MB. No hace falta dividirlo.`);
                return;
            }

            const srcDoc = await PDFLib.PDFDocument.load(pdfBytes);
            const totalPages = srcDoc.getPageCount();
            if (totalPages < 2) {
                alert("El documento tiene una sola página y no se puede dividir más.");
                return;
            }

            const partsCount = Math.ceil(currentSizeMb / maxSizeMb);
            const pagesPerPart = Math.ceil(totalPages / partsCount);

            for (let i = 0; i < partsCount; i += 1) {
                const startIdx = i * pagesPerPart;
                const endIdx = Math.min(startIdx + pagesPerPart, totalPages);
                if (startIdx >= totalPages) {
                    break;
                }

                updateToolbarInfo(`Dividiendo parte ${i + 1}/${partsCount}...`);
                const indices = Array.from({ length: endIdx - startIdx }, (_, offset) => startIdx + offset);
                const partDoc = await PDFLib.PDFDocument.create();
                const pages = await partDoc.copyPages(srcDoc, indices);
                pages.forEach((page) => partDoc.addPage(page));
                const partBytes = await partDoc.save({ useObjectStreams: true });
                downloadBlob(partBytes, `parte${i + 1}_${state.originalFileName}`);
                await yieldToBrowser();
            }
        } catch (error) {
            alert(`Error al dividir el PDF: ${error.message}`);
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
            updateToolbarInfo();
        }
    }

    async function tryBasicCompression(bytes) {
        const pdfDoc = await PDFLib.PDFDocument.load(bytes);
        return pdfDoc.save({ useObjectStreams: true });
    }

    function getCompressionProfiles(byteLength, pageCount) {
        if (byteLength >= 90 * 1024 * 1024 || pageCount >= 180) {
            return [
                { quality: 0.58, scale: 0.9, label: "Balanceado" },
                { quality: 0.48, scale: 0.8, label: "Fuerte" },
                { quality: 0.38, scale: 0.7, label: "Agresivo" },
            ];
        }
        if (byteLength >= 30 * 1024 * 1024 || pageCount >= 80) {
            return [
                { quality: 0.66, scale: 1.0, label: "Balanceado" },
                { quality: 0.56, scale: 0.9, label: "Fuerte" },
                { quality: 0.46, scale: 0.8, label: "Agresivo" },
            ];
        }
        return [
            { quality: 0.72, scale: 1.0, label: "Leve" },
            { quality: 0.6, scale: 0.9, label: "Balanceado" },
            { quality: 0.5, scale: 0.8, label: "Fuerte" },
        ];
    }

    async function compressRasterized(bytes, profile, runId) {
        const loadingTask = pdfjsLib.getDocument({
            data: bytes,
            disableAutoFetch: true,
            isEvalSupported: false,
        });
        const pdf = await loadingTask.promise;
        const pdfDoc = await PDFLib.PDFDocument.create();

        for (let pageNum = 1; pageNum <= pdf.numPages; pageNum += 1) {
            if (runId !== state.compressRunId) {
                throw new CancellationError("Compresión cancelada por una nueva operación.");
            }

            updateToolbarInfo(`Comprimiendo ${profile.label}: página ${pageNum}/${pdf.numPages}`);
            const page = await pdf.getPage(pageNum);
            const viewport = page.getViewport({ scale: profile.scale });
            const canvas = document.createElement("canvas");
            const context = canvas.getContext("2d", { alpha: false });
            canvas.height = Math.max(1, Math.floor(viewport.height));
            canvas.width = Math.max(1, Math.floor(viewport.width));
            await page.render({ canvasContext: context, viewport }).promise;
            const blob = await canvasToBlob(canvas, "image/jpeg", profile.quality);
            const imgBytes = await blob.arrayBuffer();
            const embeddedImg = await pdfDoc.embedJpg(imgBytes);
            const { width, height } = embeddedImg.scale(1.0);
            const newPage = pdfDoc.addPage([width, height]);
            newPage.drawImage(embeddedImg, { x: 0, y: 0, width, height });
            canvas.width = 0;
            canvas.height = 0;
            await yieldToBrowser();
        }

        return pdfDoc.save({ useObjectStreams: true });
    }

    async function compressPdf() {
        const btn = byId("btnCompress");
        const originalHtml = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Comprimiendo...';
        state.compressRunId += 1;
        const runId = state.compressRunId;

        try {
            const intermediateBytes = await getModifiedPdfBytes();
            if (!intermediateBytes) {
                return;
            }

            const srcDoc = await PDFLib.PDFDocument.load(intermediateBytes);
            const pageCount = srcDoc.getPageCount();
            const originalSize = intermediateBytes.length / (1024 * 1024);
            let bestBytes = await tryBasicCompression(intermediateBytes);
            let bestLabel = "Optimización estructural";

            const levelSelect = byId("compressLevelSelect");
            const selectedLevel = levelSelect ? levelSelect.value : "leve";

            let profilesToTry = [];
            if (selectedLevel === "leve") {
                profilesToTry = [{ quality: 0.85, scale: 2.5, label: "Leve" }];
            } else if (selectedLevel === "medio") {
                profilesToTry = [{ quality: 0.75, scale: 1.5, label: "Moderado" }];
            } else if (selectedLevel === "agresivo") {
                profilesToTry = [{ quality: 0.60, scale: 1.0, label: "Agresivo" }];
            } else {
                profilesToTry = getCompressionProfiles(intermediateBytes.length, pageCount);
            }

            for (const profile of profilesToTry) {
                if (runId !== state.compressRunId) {
                    throw new CancellationError("Compresión cancelada.");
                }

                const candidateBytes = await compressRasterized(intermediateBytes, profile, runId);
                if (candidateBytes.length < bestBytes.length) {
                    bestBytes = candidateBytes;
                    bestLabel = profile.label;
                }
                
                // Si estamos en automático, cortamos rápido si logramos un -35%
                if (selectedLevel === "auto" && candidateBytes.length <= intermediateBytes.length * 0.65) {
                    break;
                }
            }

            const finalSize = bestBytes.length / (1024 * 1024);
            if (bestBytes.length >= intermediateBytes.length) {
                alert(
                    `No se encontró un perfil que reduzca el archivo.\n\nTamaño original: ${originalSize.toFixed(2)} MB\nTamaño resultante: ${finalSize.toFixed(2)} MB`
                );
                return;
            }

            alert(
                `Compresión completada con perfil "${bestLabel}".\n\nTamaño original: ${originalSize.toFixed(2)} MB\nTamaño nuevo: ${finalSize.toFixed(2)} MB`
            );
            downloadBlob(bestBytes, `comprimido_${state.originalFileName}`);
        } catch (error) {
            if (error instanceof CancellationError) {
                return;
            }
            alert(`Error al procesar el PDF: ${error.message}`);
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
            updateToolbarInfo();
        }
    }

    async function pollOcrJob(jobId, statusNode, textArea) {
        while (true) {
            await new Promise((resolve) => setTimeout(resolve, 1200));
            const response = await fetch(buildOcrStatusUrl(jobId), { method: "GET" });
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || "No se pudo consultar el estado del OCR.");
            }

            if (data.status === "queued") {
                const position = data.queue_position || 0;
                statusNode.innerText = position > 0
                    ? `En cola. Hay ${position - 1} trabajo(s) antes del tuyo...`
                    : "En cola...";
                continue;
            }

            if (data.status === "running") {
                statusNode.innerText = "Procesando OCR en el servidor...";
                continue;
            }

            if (data.status === "success") {
                textArea.value = data.text || "";
                statusNode.innerText = `${(data.text || "").length.toLocaleString("es-AR")} caracteres extraídos`;
                return;
            }

            throw new Error(data.message || "El OCR terminó con error.");
        }
    }

    async function runLocalPdfOCR(singlePageIndex, pageRotation) {
        if (singlePageIndex instanceof Event) {
            singlePageIndex = null;
            pageRotation = 0;
        }

        const btn = byId("btnOCR");
        const originalHtml = btn.innerHTML;
        const panel = byId("ocrPanel");
        const textArea = byId("ocrText");
        const status = byId("ocrStatus");

        btn.disabled = true;
        btn.innerHTML = '<i class="bi bi-hourglass-split"></i> OCR...';
        panel.style.display = "block";
        textArea.value = "";
        status.innerText = singlePageIndex !== null ? "Procesando página seleccionada..." : "Procesando con OCR local del servidor...";

        try {
            let pdfBytes;
            if (singlePageIndex !== null) {
                const pdfDoc = await PDFLib.PDFDocument.create();
                const srcDoc = await PDFLib.PDFDocument.load(state.originalPdfBytes);
                const copiedPages = await pdfDoc.copyPages(srcDoc, [singlePageIndex]);
                const page = copiedPages[0];
                if (pageRotation) {
                    const currentAngle = page.getRotation ? page.getRotation().angle : 0;
                    page.setRotation(PDFLib.degrees((currentAngle + pageRotation) % 360));
                }
                pdfDoc.addPage(page);
                pdfBytes = await pdfDoc.save({ useObjectStreams: true });
            } else {
                pdfBytes = await getModifiedPdfBytes();
            }

            if (!pdfBytes) {
                status.innerText = "No hay páginas para procesar.";
                return;
            }

            const formData = new FormData();
            formData.append("file", new Blob([pdfBytes], { type: "application/pdf" }), state.originalFileName || "documento.pdf");
            const response = await fetch(config().ocrEndpoint, {
                method: "POST",
                body: formData,
            });
            const data = await response.json();

            if (!response.ok) {
                status.innerText = `Error: ${data.message || "No se pudo encolar el OCR."}`;
                return;
            }

            if (data.status === "success") {
                textArea.value = data.text || "";
                status.innerText = `${(data.text || "").length.toLocaleString("es-AR")} caracteres extraídos`;
                return;
            }

            if (!data.job_id) {
                status.innerText = "Error: el servidor no devolvió identificador de trabajo OCR.";
                return;
            }

            status.innerText = data.queue_position && data.queue_position > 1
                ? `En cola. Hay ${data.queue_position - 1} trabajo(s) antes del tuyo...`
                : "En cola. Esperando turno...";
            await pollOcrJob(data.job_id, status, textArea);
        } catch (error) {
            status.innerText = `Error: ${error.message}`;
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        }
    }

    function showLargeFileWarning(fileSizeMb, pageCount) {
        if (fileSizeMb < 120 && pageCount < 160) {
            return;
        }
        alert(
            `Este PDF pesa ${fileSizeMb.toFixed(2)} MB y tiene ${pageCount} páginas.\n\n` +
            "La herramienta activará carga perezosa de miniaturas y compresión por lotes. " +
            "Aun así, puede haber mayor consumo de memoria en el navegador."
        );
    }

    async function loadPdf(file) {
        if (!file) {
            return;
        }

        resetPdfState();
        const loadToken = state.loadToken;
        state.originalFileName = file.name;
        state.originalPdfBytes = new Uint8Array(await file.arrayBuffer());
        const fileSizeMb = state.originalPdfBytes.length / (1024 * 1024);
        if (fileSizeMb > 500) {
            resetPdfState();
            setEmptyState("Este PDF supera el límite interactivo de 500 MB.");
            alert("La herramienta no abre PDFs de más de 500 MB. Para ese tamaño hace falta un flujo batch separado.");
            return;
        }
        state.infoBaseText = `${file.name} (${fileSizeMb.toFixed(2)} MB)`;
        updateToolbarInfo("Leyendo documento...");
        byId("pdfPagesContainer").innerHTML = '<div class="pdf-tool-empty"><i class="bi bi-arrow-repeat" style="font-size: 2rem; display: inline-block; animation: spin 1s linear infinite;"></i><p style="margin-top: 10px; font-weight: bold;">Cargando estructura del PDF...</p></div>';

        try {
            const loadingTask = pdfjsLib.getDocument({
                data: state.originalPdfBytes,
                disableAutoFetch: true,
                isEvalSupported: false,
            });
            const pdf = await loadingTask.promise;
            if (loadToken !== state.loadToken) {
                throw new CancellationError("La carga del PDF fue reemplazada.");
            }

            state.pdfDocument = pdf;
            byId("btnSave").style.display = "inline-flex";
            byId("btnOCR").style.display = "inline-flex";
            byId("splitControls").style.display = "inline-flex";
            byId("compressControls").style.display = "inline-flex";
            byId("pdfPagesContainer").innerHTML = "";

            showLargeFileWarning(fileSizeMb, pdf.numPages);

            for (let pageNum = 1; pageNum <= pdf.numPages; pageNum += 1) {
                createPageElement(pageNum - 1);
                if (pageNum % 20 === 0) {
                    updateToolbarInfo(`Preparando páginas ${pageNum}/${pdf.numPages}...`);
                    await yieldToBrowser();
                }
            }

            updatePageNumbers();
            initializeThumbnailObserver();
            getVisiblePageItems().slice(0, 8).forEach((item) => scheduleThumbnailRender(item));
            updateThumbnailProgress();
        } catch (error) {
            if (error instanceof CancellationError) {
                return;
            }
            setEmptyState(`Error al cargar el PDF: ${error.message}`);
            updateToolbarInfo();
        }
    }

    function downloadBlob(bytes, filename) {
        const blob = new Blob([bytes], { type: "application/pdf" });
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = filename;
        document.body.appendChild(anchor);
        anchor.click();
        anchor.remove();
        setTimeout(() => URL.revokeObjectURL(url), 4000);
    }

    function copyOcrText() {
        const text = byId("ocrText").value || "";
        if (!text) {
            alert("No hay texto OCR para copiar.");
            return;
        }
        const status = byId("ocrStatus");

        const fallbackCopy = () => {
            const temp = document.createElement("textarea");
            temp.value = text;
            temp.setAttribute("readonly", "readonly");
            temp.style.position = "fixed";
            temp.style.left = "-9999px";
            temp.style.top = "-9999px";
            document.body.appendChild(temp);
            temp.focus();
            temp.select();
            temp.setSelectionRange(0, temp.value.length);
            let copied = false;
            try {
                copied = document.execCommand("copy");
            } catch (_error) {
                copied = false;
            }
            temp.remove();
            if (copied) {
                status.innerText = "Texto copiado al portapapeles.";
            } else {
                status.innerText = "No se pudo copiar automáticamente.";
                alert("No se pudo copiar automáticamente el texto OCR.");
            }
        };

        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text)
                .then(() => {
                    status.innerText = "Texto copiado al portapapeles.";
                })
                .catch(() => {
                    fallbackCopy();
                });
            return;
        }

        fallbackCopy();
    }

    function init() {
        if (!window.pdfjsLib || !window.PDFLib) {
            return;
        }
        pdfjsLib.GlobalWorkerOptions.workerSrc = resolveWorkerSrc();
        setEmptyState("Selecciona un archivo PDF para comenzar a editarlo.");
        byId("pdfInput").addEventListener("change", (event) => loadPdf(event.target.files[0]));
        byId("btnOpen").addEventListener("click", () => byId("pdfInput").click());
        byId("btnSave").addEventListener("click", savePdf);
        byId("btnOCR").addEventListener("click", runLocalPdfOCR);
        byId("btnSplit").addEventListener("click", splitPdfBySize);
        byId("btnCompress").addEventListener("click", compressPdf);
        byId("btnCopyOCR").addEventListener("click", copyOcrText);
    }

    document.addEventListener("DOMContentLoaded", init);
})();
