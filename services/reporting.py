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

def round_to_standard_ram(gb: float) -> int:
    """Redondea una capacidad de RAM a los tamaños estándares de módulos de hardware."""
    tiers = [1, 2, 4, 6, 8, 12, 16, 24, 32, 64, 128]
    return min(tiers, key=lambda x: abs(x - gb))


def guess_ddr_from_processor(processor: str) -> str:
    """Infiere la tecnología DDR más probable a partir de la descripción del procesador."""
    if not processor or str(processor).strip().upper() in ("N/A", "NONE", ""):
        return "DDR3"
    
    proc = str(processor).upper()
    
    # AMD Ryzen
    if "RYZEN" in proc:
        match = re.search(r"RYZEN\s+\d+\s+(\d)\d{3}", proc)
        if match and int(match.group(1)) >= 7:
            return "DDR5"
        return "DDR4"
        
    # Intel Core (i3, i5, i7, i9)
    if "CORE" in proc or "I3-" in proc or "I5-" in proc or "I7-" in proc or "I9-" in proc:
        match = re.search(r"I\d-\s*(\d+)", proc)
        if match:
            gen_num = match.group(1)
            # 4 dígitos (ej: 4590 -> 4ta gen -> DDR3)
            if len(gen_num) == 4:
                first_digit = int(gen_num[0])
                if first_digit <= 4:
                    return "DDR3"
                else:
                    return "DDR4"
            # 5 o más dígitos (ej: 10400 -> 10ma gen -> DDR4; 12400 -> 12va gen)
            elif len(gen_num) >= 5:
                first_two = int(gen_num[:2])
                if first_two >= 12:
                    return "DDR4" # en ámbito judicial la mayoría de 12va/13va usa DDR4
                return "DDR4"
        if "CORE 2" in proc:
            return "DDR2"
            
    # Intel Pentium y Celeron
    if "PENTIUM" in proc or "CELERON" in proc:
        if "G" in proc:
            match = re.search(r"G(\d)", proc)
            if match:
                digit = int(match.group(1))
                if digit >= 4: return "DDR4"
                return "DDR3"
        return "DDR2"
        
    return "DDR3"


def normalize_ram_spec(spec: str, fallback_gb=None, processor: str = None) -> str:
    """
    Normaliza el string de especificación de RAM:
    1. Redondea capacidades decimales (ej. 7.3 GB -> 8 GB) a los estándares de hardware.
    2. Auto-clasifica DDR (DDR1/2/3/4/5) basándose en la velocidad en MHz.
    3. Si sigue sin clasificar, infiere el tipo DDR a partir del procesador.
    """
    guessed_type = guess_ddr_from_processor(processor) if processor else "DDR"
    
    if not spec or str(spec).strip().upper() in ("N/A", "NONE", ""):
        if fallback_gb:
            try:
                val = float(fallback_gb)
                rounded = round_to_standard_ram(val)
                return f"{rounded} GB {guessed_type}"
            except Exception:
                pass
        return "N/D"
    
    spec_str = str(spec).strip()
    
    # 1. Redondear números decimales (ej: 7.3 GB -> 8 GB)
    def replace_decimal(match):
        num_str = match.group(1)
        try:
            val = float(num_str)
            return f"{round_to_standard_ram(val)}"
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
        else:
            # Si no hay velocidad pero tampoco tiene la palabra DDR, inyectar el DDR adivinado del procesador
            if "@" in spec_str:
                parts = spec_str.split("@", 1)
                spec_str = f"{parts[0].strip()} {guessed_type} @ {parts[1].strip()}"
            elif "GB" in spec_str:
                spec_str = spec_str.replace("GB", f"GB {guessed_type}")
            else:
                spec_str = f"{spec_str} {guessed_type}"
                
    return spec_str

