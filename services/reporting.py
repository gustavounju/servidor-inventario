import datetime
from fpdf import FPDF

# Helper para fechas en español
def format_date_es(d_obj):
    if not d_obj: return ""
    if isinstance(d_obj, str):
        try:
            d_obj = datetime.datetime.strptime(d_obj, "%Y-%m-%d")
        except:
            return d_obj
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    try:
        return f"{dias[d_obj.weekday()]} {d_obj.day:02d}/{d_obj.month:02d}/{d_obj.year}"
    except:
        return str(d_obj)

def format_datetime_es(dt_val):
    if not dt_val: return ""
    
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

    try:
        if isinstance(dt_val, str):
            # Si es string
            try:
                dt_obj = datetime.datetime.strptime(dt_val, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                dt_obj = datetime.datetime.fromisoformat(dt_val.replace('Z', '+00:00'))
        else:
            # Si ya es datetime (MySQL/PyMySQL)
            dt_obj = dt_val

        nombre_dia = dias[dt_obj.weekday()]
        nombre_mes = meses[dt_obj.month]
        return f"{nombre_dia} {dt_obj.day:02d} de {nombre_mes} del {dt_obj.year} a las {dt_obj.hour:02d}:{dt_obj.minute:02d}"
    except Exception:
        # Fallback en caso de formato inesperado
        return str(dt_val)

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


import re

def normalize_ram_spec(spec: str, fallback_gb=None) -> str:
    """
    Normaliza el string de especificación de RAM:
    1. Redondea capacidades decimales (ej. 7.3 GB -> 8 GB).
    2. Auto-clasifica DDR (DDR1/2/3/4/5) basándose en la velocidad en MHz si no está especificado.
    """
    if not spec or str(spec).strip().upper() in ("N/A", "NONE", ""):
        if fallback_gb:
            try:
                val = float(fallback_gb)
                return f"{int(round(val))} GB RAM"
            except Exception:
                pass
        return "N/D"
    
    spec_str = str(spec).strip()
    
    # 1. Redondear números decimales (ej: 7.3 GB -> 8 GB)
    def replace_decimal(match):
        num_str = match.group(1)
        try:
            val = float(num_str)
            return f"{int(round(val))}"
        except Exception:
            return match.group(0)
            
    spec_str = re.sub(r"\b(\d+\.\d+)\b", replace_decimal, spec_str)
    
    # 2. Si tiene velocidad en MHz pero no tiene la palabra 'DDR', clasificarla según la velocidad
    if "DDR" not in spec_str.upper():
        speed_match = re.search(r"\b(\d{3,4})\s*(?:MHz|mhz)?\b", spec_str)
        if speed_match:
            try:
                speed = int(speed_match.group(1))
                ram_type = ""
                if speed > 0:
                    if speed <= 450: ram_type = "DDR"
                    elif speed <= 900: ram_type = "DDR2"
                    elif speed <= 2100: ram_type = "DDR3"
                    elif speed <= 4200: ram_type = "DDR4"
                    else: ram_type = "DDR5"
                
                if ram_type:
                    # Insertar el tipo DDR antes de '@' o al final si no hay '@'
                    if "@" in spec_str:
                        parts = spec_str.split("@", 1)
                        spec_str = f"{parts[0].strip()} {ram_type} @ {parts[1].strip()}"
                    else:
                        spec_str = f"{spec_str} {ram_type}"
            except Exception:
                pass
                
    return spec_str

