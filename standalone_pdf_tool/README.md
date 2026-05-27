# Editor PDF Local Standalone

Mini app Flask para usar la herramienta PDF sin levantar todo el sistema de inventario.

## Punto de acceso

- `http://127.0.0.1:5090/pdf-local`
- Salud: `http://127.0.0.1:5090/health`

## Windows

Desde la carpeta del proyecto:

```powershell
.\.venv\Scripts\python.exe .\standalone_pdf_tool\app.py
```

## Ubuntu

Dentro del entorno virtual:

```bash
source .venv/bin/activate
python standalone_pdf_tool/app.py
```

## Variables opcionales

- `PDF_TOOL_HOST=0.0.0.0`
- `PDF_TOOL_PORT=5090`
- `PDF_TOOL_DEBUG=false`
- `PDF_OCR_LANG=spa+eng`
- `PDF_OCR_DPI=300`
- `PDF_OCR_MIN_CHARS=20`
- `TESSERACT_CMD=/usr/bin/tesseract`

## Dependencias del OCR local

Ubuntu:

```bash
sudo apt update
sudo apt install -y poppler-utils tesseract-ocr tesseract-ocr-spa
```

Python:

```bash
pip install Flask pypdf pytesseract pdf2image Pillow
```
