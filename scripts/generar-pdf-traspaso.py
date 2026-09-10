"""Render the two canonical handoff documents. Requires reportlab; no network calls."""

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, KeepTogether, PageBreak, PageTemplate, Paragraph, Spacer,
)
from reportlab.platypus.tableofcontents import TableOfContents


ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    ROOT / "docs/inventario-modular/traspaso-tareas-lan-2026-09-10.md",
    ROOT / "docs/inventario-modular/instalacion-tareas-lan-2026-09-10.md",
]
OUTPUT = ROOT / "output/pdf/traspaso-tareas-lan.pdf"
INK = colors.HexColor("#20282a")
TEAL = colors.HexColor("#15685f")
GREY = colors.HexColor("#657270")
STYLES = getSampleStyleSheet()
STYLES.add(ParagraphStyle("Body", fontName="Helvetica", fontSize=10, leading=14,
                          textColor=INK, spaceAfter=7, splitLongWords=True))
STYLES.add(ParagraphStyle("Part", parent=STYLES["Body"], fontName="Helvetica-Bold",
                          fontSize=23, leading=28, spaceAfter=18, keepWithNext=True))
STYLES.add(ParagraphStyle("Section", parent=STYLES["Body"], fontName="Helvetica-Bold",
                          fontSize=14, leading=18, textColor=TEAL,
                          spaceBefore=15, spaceAfter=9, keepWithNext=True))
STYLES.add(ParagraphStyle("Command", fontName="Courier", fontSize=8, leading=11,
                          textColor=INK, backColor=colors.HexColor("#f0f3f2"),
                          borderPadding=7, spaceBefore=6, spaceAfter=10,
                          splitLongWords=True, alignment=TA_LEFT))
STYLES.add(ParagraphStyle("Item", parent=STYLES["Body"], leftIndent=12,
                          firstLineIndent=-9, spaceAfter=5))
STYLES.add(ParagraphStyle("SmallLabel", parent=STYLES["Body"], fontSize=9,
                          textColor=GREY, spaceAfter=12))
STYLES.add(ParagraphStyle("CoverTitle", parent=STYLES["Part"]))
STYLES.add(ParagraphStyle("CoverSection", parent=STYLES["Section"]))


def inline(text):
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r'<font name="Courier" size="8.8">\1</font>', escaped)
    return re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", escaped)


class HandoffDoc(BaseDocTemplate):
    def afterFlowable(self, flowable):
        if not isinstance(flowable, Paragraph):
            return
        style = flowable.style.name
        if style in {"Part", "Section"}:
            title = flowable.getPlainText()
            key = "heading-" + str(self.seq.nextf("heading"))
            self.canv.bookmarkPage(key)
            level = 0 if style == "Part" else 1
            self.canv.addOutlineEntry(title, key, level=level, closed=False)
            self.notify("TOCEntry", (level, title, self.page, key))


def chrome(canvas, doc):
    canvas.saveState()
    width, height = A4
    if doc.page > 1:
        canvas.setFillColor(GREY)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(20 * mm, height - 14 * mm, "INVENTARIO MODULAR / TRASPASO Y OPERACION LAN")
        canvas.setStrokeColor(colors.HexColor("#d4dfdc"))
        canvas.line(20 * mm, height - 17 * mm, width - 20 * mm, height - 17 * mm)
    canvas.setFillColor(GREY)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(20 * mm, 13 * mm, "10.09.2026  |  Uso interno  |  Sin credenciales")
    canvas.drawRightString(width - 20 * mm, 13 * mm, str(doc.page))
    canvas.restoreState()


def markdown_flowables(path):
    result, paragraph, code = [], [], []
    in_code = False

    def flush():
        if paragraph:
            style = "Item" if re.match(r"^(?:- |\d+\. )", paragraph[0]) else "Body"
            result.append(Paragraph(inline(" ".join(paragraph)), STYLES[style]))
            paragraph.clear()

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("```"):
            flush()
            if in_code:
                # A Paragraph wraps long commands visually without changing the editable Markdown.
                content = "<br/>".join(html.escape(row).replace(" ", "&#160;") for row in code)
                result.append(KeepTogether([Paragraph(content or " ", STYLES["Command"])]))
                code.clear()
            in_code = not in_code
        elif in_code:
            code.append(line)
        elif line.startswith("# "):
            flush()
            result.append(Paragraph(inline(line[2:]), STYLES["Part"]))
        elif line.startswith("## "):
            flush()
            result.append(Paragraph(inline(line[3:]), STYLES["Section"]))
        elif not line.strip():
            flush()
        elif re.match(r"^(?:- |\d+\. )", line):
            flush()
            # Continuation lines belong to the same list item, not a new paragraph.
            paragraph.append(line)
        elif paragraph and re.match(r"^(?:- |\d+\. )", paragraph[0]):
            paragraph.append(line.strip())
        else:
            paragraph.append(line)
    flush()
    if in_code:
        raise ValueError(f"Unclosed code fence in {path}")
    return result


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = HandoffDoc(str(OUTPUT), pagesize=A4, title="Inventario Modular - Traspaso e instalacion LAN",
                     author="Proyecto Inventario Modular", leftMargin=20 * mm,
                     rightMargin=20 * mm, topMargin=24 * mm, bottomMargin=23 * mm)
    doc.addPageTemplates(PageTemplate(id="main", frames=[Frame(
        doc.leftMargin, doc.bottomMargin, doc.width, doc.height,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)], onPage=chrome))
    story = [Spacer(1, 30 * mm), Paragraph("CENTRO JUDICIAL SAN PEDRO", STYLES["SmallLabel"]),
             Paragraph("Inventario Modular", STYLES["CoverTitle"]),
             Paragraph("Tareas, visor y Android LAN", STYLES["CoverSection"]),
             Paragraph("Documento de continuidad tecnica<br/>y puesta en marcha sin Internet", STYLES["Body"]),
             Spacer(1, 14 * mm),
             Paragraph("Entrega: 10 de septiembre de 2026<br/>Rama: primeros-pasos", STYLES["Body"]),
             Spacer(1, 12 * mm),
             Paragraph("ESTADO DE LA ENTREGA", STYLES["SmallLabel"]),
             Paragraph("Servidor y web verificados localmente. APK piloto compilada. "
                       "Pendientes: firma release, HTTPS institucional y prueba en telefonos reales.", STYLES["Body"]),
             Paragraph("No se desplego en produccion. Este documento explica como preparar, "
                       "validar, instalar y revertir la entrega sin servicios externos.", STYLES["Body"]),
             PageBreak(), Paragraph("Contenido", STYLES["CoverTitle"])]
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle("TOCPart", fontName="Helvetica-Bold", fontSize=11,
                                     leading=15, spaceBefore=10),
                       ParagraphStyle("TOCSection", fontName="Helvetica", fontSize=9,
                                     leading=12, leftIndent=12, spaceBefore=4)]
    story.extend([toc, PageBreak()])
    for i, source in enumerate(SOURCES):
        if i:
            story.append(PageBreak())
        story.extend(markdown_flowables(source))
    doc.multiBuild(story)
    print(OUTPUT)


if __name__ == "__main__":
    main()
