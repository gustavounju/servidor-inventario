(() => {
    const state = {
        originalPdfBytes: null,
        originalFileName: "",
        draggedItem: null,
    };

    function byId(id) {
        return document.getElementById(id);
    }

    function config() {
        return window.pdfLocalToolConfig || {};
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

    function updatePageNumbers() {
        Array.from(byId("pdfPagesContainer").children).forEach((child, index) => {
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
            const children = Array.from(container.children);
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
        Array.from(byId("pdfPagesContainer").children).forEach((child) => {
            child.classList.remove("drag-over");
        });
    }

    function movePage(pageDiv, direction) {
        const container = byId("pdfPagesContainer");
        const children = Array.from(container.children);
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
        pageDiv.querySelector("img").style.transform = `rotate(${nextRotation}deg)`;
    }

    function createPageElement(originalIndex, imgData) {
        const pageDiv = document.createElement("div");
        pageDiv.className = "pdf-page-item";
        pageDiv.dataset.originalIndex = String(originalIndex);
        pageDiv.dataset.rotation = "0";
        pageDiv.draggable = true;
        pageDiv.addEventListener("dragstart", handleDragStart);
        pageDiv.addEventListener("dragover", handleDragOver);
        pageDiv.addEventListener("dragenter", handleDragEnter);
        pageDiv.addEventListener("dragleave", handleDragLeave);
        pageDiv.addEventListener("drop", handleDrop);
        pageDiv.addEventListener("dragend", handleDragEnd);

        const label = document.createElement("div");
        label.className = "pdf-page-label";

        const img = document.createElement("img");
        img.src = imgData;
        img.setAttribute("draggable", "false");

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

        controls.append(left, rotateLeft, del, rotateRight, right);
        pageDiv.append(label, img, controls);
        byId("pdfPagesContainer").appendChild(pageDiv);
        updatePageNumbers();
    }

    async function getModifiedPdfBytes() {
        const children = Array.from(byId("pdfPagesContainer").children)
            .filter((child) => child.classList.contains("pdf-page-item"));
        const pageInstructions = children.map((child) => ({
            originalIndex: parseInt(child.dataset.originalIndex, 10),
            rotation: parseInt(child.dataset.rotation || "0", 10),
        }));

        if (!pageInstructions.length) {
            alert("No hay páginas para guardar.");
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

        return pdfDoc.save();
    }

    async function savePdf() {
        const btn = byId("btnSave");
        const originalHtml = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Procesando...';
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
        }
    }

    async function splitPdfBySize() {
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
        for (let i = 0; i < partsCount; i++) {
            const startIdx = i * pagesPerPart;
            const endIdx = Math.min(startIdx + pagesPerPart, totalPages);
            if (startIdx >= totalPages) {
                break;
            }
            const indices = Array.from({ length: endIdx - startIdx }, (_, offset) => startIdx + offset);
            const partDoc = await PDFLib.PDFDocument.create();
            const pages = await partDoc.copyPages(srcDoc, indices);
            pages.forEach((page) => partDoc.addPage(page));
            const partBytes = await partDoc.save();
            await new Promise((resolve) => setTimeout(resolve, 400));
            downloadBlob(partBytes, `parte${i + 1}_${state.originalFileName}`);
        }
    }

    async function compressExtremely(bytes, quality, scale) {
        const loadingTask = pdfjsLib.getDocument(bytes);
        const pdf = await loadingTask.promise;
        const pdfDoc = await PDFLib.PDFDocument.create();

        for (let pageNum = 1; pageNum <= pdf.numPages; pageNum += 1) {
            const page = await pdf.getPage(pageNum);
            const viewport = page.getViewport({ scale });
            const canvas = document.createElement("canvas");
            const context = canvas.getContext("2d");
            canvas.height = viewport.height;
            canvas.width = viewport.width;
            await page.render({ canvasContext: context, viewport }).promise;
            const imgDataUrl = canvas.toDataURL("image/jpeg", quality);
            const imgBytes = await fetch(imgDataUrl).then((res) => res.arrayBuffer());
            const embeddedImg = await pdfDoc.embedJpg(imgBytes);
            const { width, height } = embeddedImg.scale(1.0);
            const newPage = pdfDoc.addPage([width, height]);
            newPage.drawImage(embeddedImg, { x: 0, y: 0, width, height });
        }

        return pdfDoc.save({ useObjectStreams: true });
    }

    async function compressPdf() {
        const btn = byId("btnCompress");
        const originalHtml = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Procesando...';

        try {
            const intermediateBytes = await getModifiedPdfBytes();
            if (!intermediateBytes) {
                return;
            }

            const finalBytes = await compressExtremely(intermediateBytes, 0.6, 1.2);
            const originalSize = intermediateBytes.length / (1024 * 1024);
            const finalSize = finalBytes.length / (1024 * 1024);

            if (finalBytes.length >= intermediateBytes.length) {
                alert(
                    `La rasterización no mejoró el archivo.\n\nTamaño original: ${originalSize.toFixed(2)} MB\nTamaño resultante: ${finalSize.toFixed(2)} MB\n\nNo se descargará el PDF porque quedó más grande.`
                );
                return;
            }

            alert(
                `Proceso completado.\n\nTamaño original: ${originalSize.toFixed(2)} MB\nTamaño nuevo: ${finalSize.toFixed(2)} MB\n\nSe iniciará la descarga.`
            );
            downloadBlob(finalBytes, `rasterizado_${state.originalFileName}`);
        } catch (error) {
            alert(`Error al procesar el PDF: ${error.message}`);
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        }
    }

    async function runLocalPdfOCR() {
        const btn = byId("btnOCR");
        const originalHtml = btn.innerHTML;
        const panel = byId("ocrPanel");
        const textArea = byId("ocrText");
        const status = byId("ocrStatus");

        btn.disabled = true;
        btn.innerHTML = '<i class="bi bi-hourglass-split"></i> OCR...';
        panel.style.display = "block";
        textArea.value = "";
        status.innerText = "Procesando con OCR local del servidor...";

        try {
            const pdfBytes = await getModifiedPdfBytes();
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
            if (data.status === "success") {
                textArea.value = data.text || "";
                status.innerText = `${(data.text || "").length.toLocaleString("es-AR")} caracteres extraídos`;
            } else {
                status.innerText = `Error: ${data.message || "No se pudo procesar el PDF."}`;
            }
        } catch (error) {
            status.innerText = `Error: ${error.message}`;
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        }
    }

    async function loadPdf(file) {
        if (!file) {
            return;
        }
        state.originalFileName = file.name;
        const buffer = await file.arrayBuffer();
        state.originalPdfBytes = new Uint8Array(buffer);
        byId("pdfInfo").innerText = `${file.name} (${(state.originalPdfBytes.length / (1024 * 1024)).toFixed(2)} MB)`;
        byId("pdfPagesContainer").innerHTML = '<div class="pdf-tool-empty"><i class="bi bi-arrow-repeat" style="font-size: 2rem; display: inline-block; animation: spin 1s linear infinite;"></i><p style="margin-top: 10px; font-weight: bold;">Cargando páginas...</p></div>';

        try {
            const loadingTask = pdfjsLib.getDocument(state.originalPdfBytes);
            const pdf = await loadingTask.promise;
            byId("btnSave").style.display = "inline-flex";
            byId("btnOCR").style.display = "inline-flex";
            byId("splitControls").style.display = "inline-flex";
            byId("compressControls").style.display = "inline-flex";
            byId("pdfPagesContainer").innerHTML = "";

            for (let pageNum = 1; pageNum <= pdf.numPages; pageNum += 1) {
                const page = await pdf.getPage(pageNum);
                const viewport = page.getViewport({ scale: 0.6 });
                const canvas = document.createElement("canvas");
                const context = canvas.getContext("2d");
                canvas.height = viewport.height;
                canvas.width = viewport.width;
                await page.render({ canvasContext: context, viewport }).promise;
                createPageElement(pageNum - 1, canvas.toDataURL());
            }
        } catch (error) {
            setEmptyState(`Error al cargar el PDF: ${error.message}`);
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
        URL.revokeObjectURL(url);
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
            } catch (error) {
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
        pdfjsLib.GlobalWorkerOptions.workerSrc = config().workerSrc;
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
