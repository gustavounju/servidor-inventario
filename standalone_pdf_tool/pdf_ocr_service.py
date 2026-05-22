import os

from pypdf import PdfReader


class LocalOCRConfigurationError(RuntimeError):
    """Raised when local OCR dependencies are unavailable."""


def extract_pdf_text_local(file_path):
    language = os.environ.get("PDF_OCR_LANG", "spa+eng")
    dpi = int(os.environ.get("PDF_OCR_DPI", "300"))
    min_chars = int(os.environ.get("PDF_OCR_MIN_CHARS", "20"))

    pages = []
    reader = PdfReader(file_path)

    for page_number, page in enumerate(reader.pages, start=1):
        extracted_text = (page.extract_text() or "").strip()
        if len(extracted_text) >= min_chars:
            pages.append((page_number, extracted_text, "embedded"))
            continue

        ocr_text = _ocr_page_with_tesseract(
            file_path=file_path,
            page_number=page_number,
            language=language,
            dpi=dpi,
        )
        pages.append((page_number, ocr_text.strip(), "ocr"))

    formatted_pages = []
    for page_number, text, source in pages:
        body = text if text else "[Sin texto reconocido]"
        formatted_pages.append(f"===== PAGINA {page_number} ({source}) =====\n{body}")

    return "\n\n".join(formatted_pages).strip()


def _ocr_page_with_tesseract(file_path, page_number, language, dpi):
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except ImportError as exc:
        raise LocalOCRConfigurationError(
            "Faltan dependencias Python para OCR local. Instala `pytesseract`, `pdf2image` y `Pillow`."
        ) from exc

    tesseract_cmd = os.environ.get("TESSERACT_CMD", "").strip()
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    try:
        images = convert_from_path(
            file_path,
            dpi=dpi,
            first_page=page_number,
            last_page=page_number,
            fmt="png",
            thread_count=1,
        )
    except Exception as exc:
        raise LocalOCRConfigurationError(
            "No se pudo convertir el PDF a imagen. En Ubuntu instala `poppler-utils`."
        ) from exc

    if not images:
        return ""

    try:
        return pytesseract.image_to_string(images[0], lang=language)
    except pytesseract.TesseractNotFoundError as exc:
        raise LocalOCRConfigurationError(
            "Tesseract no esta instalado o no esta en PATH. En Ubuntu instala `tesseract-ocr` y `tesseract-ocr-spa`."
        ) from exc
    except Exception as exc:
        raise LocalOCRConfigurationError(f"Error ejecutando OCR local: {exc}") from exc
