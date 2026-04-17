import os

APP_VERSION = "v3.0.0-dashboard-ux"
DB_FILE = "inventario.db"
LOG_FOLDER = "logs"
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {'pdf'}

# --- DICCIONARIO DE FUEROS (CONFIGURABLE) ---
FUERO_MAPPING = {
    "TTSIVVOC": "Tribunal de Trabajo Sala IV",
    "OGL": "Oficina de Gestion Laboral",
    "SISTEMAS": "Dpto. Informatica San Pedro",
    "VGS": "Violencia de Género 5",
    "VG5": "Violencia de Género 5",
    "SIVL": "Sala IV Laboral",
    "TJO1": "Tribunal de Juicio",
    "TJ01": "Tribunal de Juicio",
    "TJ": "Tribunal de Juicio",
    "CGESE": "Cámara Gesell",
    "JCC8SEC16": "Juzgado civil y Comercial N°8 Secretaria 16",
    "JCC9SEC18": "Juzgado civil y Comercial N°9 Secretaria 18",
    "JCC": "Juzgado Civil y Comercial",
    "PRENSA": "Prensa Poder Judicial de San Pedro de Jujuy",
    "SUPINT": "Superintendencia",
    "EQINT": "Equipo Interdisciplinario",
    "JUZMEN2": "Juzgado de Menores 2",
    "JUZMEN": "Juzgado de Menores",
    "JMEN": "Juzgado de Menores",
    "OGJ": "Oficina de Gestion Judicial",
    "VIOGEN": "Violencia de Género 5",
    "TFSIIIV": "Tribunal de Familia - Sala III",
    "TRIBJU": "Tribunal de Juicio",
    "FAM": "Juzgado de Familia",
    "JF": "Juzgado de Familia",
    "JFAM": "Juzgado de Familia",
    "CORP": "Juzgado de Control - Corp.",
    "JCON": "Juzgado de Control",
    "OMN": "Mandamientos y Notificaciones",
    "OM": "Oficina de Mandamientos",
    "NOT": "Oficina de Notificaciones",
    "BIB": "Biblioteca",
    "ARQ": "Archivo",
    "INT": "Intendencia",
    "MAY": "Mayordomia",
    "MED": "Reconocimiento Medico",
    "PSI": "Psicologia",
    "TS": "Trabajo Social",
    "MESA": "Mesa de Entradas",
    "ME": "Mesa de Entradas",
    "VOC": "Vocalia",
    "DP": "Defensoria Publica",
    "DEF": "Defensoria",
    "MPA": "Ministerio Publico Acusacion",
    "SIGJ": "Sistemas SIGJ"
}

FUERO_COLORS = {
    "Tribunal de Trabajo Sala IV": "#0d6efd",    # Blue
    "Oficina de Gestion Laboral": "#198754",     # Green
    "Dpto. Informatica San Pedro": "#212529",    # Dark
    "Violencia de Género 5": "#d63384",          # Pink
    "Sala IV Laboral": "#fd7e14",                # Orange
    "Tribunal de Juicio": "#6610f2",             # Indigo
    "Cámara Gesell": "#20c997",                  # Teal
    "Juzgado civil y Comercial N°8 Secretaria 16": "#0dcaf0", # Cyan
    "Juzgado civil y Comercial N°9 Secretaria 18": "#0dcaf0", # Cyan
    "Juzgado Civil y Comercial": "#0dcaf0",      # Cyan
    "Equipo Interdisciplinario": "#ffc107",      # Yellow
    "Juzgado de Menores 2": "#dc3545",           # Red
    "Juzgado de Menores": "#dc3545",             # Red
    "Oficina de Gestion Judicial": "#0dcaf0",    # Cyan
    "Tribunal de Familia - Sala III": "#ffc107", # Yellow
    "Juzgado de Familia": "#ffc107",             # Yellow
    "Juzgado de Control - Corp.": "#6c757d",     # Grey
    "Juzgado de Control": "#6c757d",             # Grey
    "Mandamientos y Notificaciones": "#20c997",  # Teal
    "Oficina de Mandamientos": "#20c997",       # Teal
    "Oficina de Notificaciones": "#20c997",     # Teal
    "Biblioteca": "#b91c1c",                     # Dark Red
    "Archivo": "#7c2d12",                       # Brown
    "Intendencia": "#4a5568",                   # Slack Blue
    "Mayordomia": "#4a5568",                    # Slack Blue
    "Reconocimiento Medico": "#10b981",          # Emerald
    "Psicologia": "#ec4899",                    # Pinkish
    "Trabajo Social": "#8b5cf6",                 # Violet
    "Mesa de Entradas": "#3b82f6",              # Bright Blue
    "Vocalia": "#4f46e5",                       # Indigo 600
    "Defensoria": "#92400e",                    # Amber 800
    "Defensoria Publica": "#92400e",             # Amber 800
    "Ministerio Publico Acusacion": "#1e293b",   # Slate 800
    "Sistemas SIGJ": "#000000"                   # Black
}

def detect_fuero(pc_name):
    """Detecta el fuero basado en el prefijo del nombre de la PC."""
    if not pc_name:
        return "Desconocido"
    
    pc_upper = pc_name.upper()
    for prefix in sorted(FUERO_MAPPING.keys(), key=len, reverse=True):
        if pc_upper.startswith(prefix):
            return FUERO_MAPPING[prefix]
    return "Desconocido"

def clean_hex_string(s):
    """
    Limpia strings que vienen como hexadecimal '0x...' decodificando el contenido ASCII
    y eliminando prefijos binarios de control.
    """
    if not s or not isinstance(s, str):
        return s
    
    s = s.strip()
    if s.startswith('0x'):
        try:
            hex_data = s[2:]
            # Asegurar longitud par
            if len(hex_data) % 2 != 0:
                hex_data = '0' + hex_data
            
            bytes_data = bytes.fromhex(hex_data)
            try:
                decoded = bytes_data.decode('utf-8', errors='ignore')
            except:
                decoded = bytes_data.decode('latin-1', errors='ignore')
            
            import re
            # Eliminar caracteres de control no imprimibles (\x00-\x1F y otros)
            # Solo dejamos caracteres imprimibles ASCII (0x20 a 0x7E)
            cleaned = re.sub(r'^[^\x20-\x7E]+', '', decoded)
            cleaned = re.sub(r'[^\x20-\x7E]+$', '', cleaned)
            
            if len(cleaned) > 2:
                return cleaned.strip()
            return decoded.strip()
        except:
            return s
    return s
