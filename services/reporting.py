import datetime
from io import BytesIO
from fpdf import FPDF
from database.db_core import get_db_connection

# Helper para fechas en español
def format_date_es(d_obj):
    if isinstance(d_obj, str):
        try:
            d_obj = datetime.datetime.strptime(d_obj, "%Y-%m-%d")
        except:
            return d_obj
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    return f"{dias[d_obj.weekday()]} {d_obj.day:02d}/{d_obj.month:02d}/{d_obj.year}"

def format_datetime_es(datetime_str):
    if not datetime_str: return ""
    try:
        dt_obj = datetime.datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        return f"{dt_obj.day:02d}/{dt_obj.month:02d}/{dt_obj.year} {dt_obj.hour:02d}:{dt_obj.minute:02d}"
    except:
        if ' ' in datetime_str: return datetime_str.split(' ')[1][:5]
        return datetime_str

class PDFReport(FPDF):
    def __init__(self, title="Reporte - Inventario GOLD", orientation='P', unit='mm', format='A4'):
        super().__init__(orientation, unit, format)
        self.report_title = title

    def header(self):
        self.set_font('Arial', 'B', 15)
        self.set_text_color(33, 37, 41)
        self.cell(0, 10, self.report_title, 0, 1, 'C')
        self.ln(5)
        self.set_draw_color(13, 110, 253)
        self.set_line_width(1)
        current_width = self.w - 20
        self.line(10, 25, 10 + current_width, 25)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        ahora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}} - Generado el {ahora}', 0, 0, 'C')
