import os

APP_VERSION = "v2.1.0-mysql"
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
    "PRENSA": "Prensa Poder Judicial de San Pedro de Jujuy",
    "SUPINT": "Superintendencia",
    "EQINT": "Equipo Interdisciplinario",
    "JUZMEN2": "Juzgado de Menores 2",
    "OGJ": "Oficina de Gestion Judicial",
    "VIOGEN": "Violencia de Género 5",
    "TFSIIIV": "Tribunal de Familia - Sala III",
    "TRIBJU": "Tribunal de Juicio"
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
    "Equipo Interdisciplinario": "#ffc107",      # Yellow
    "Juzgado de Menores 2": "#dc3545",           # Red
    "Oficina de Gestion Judicial": "#0dcaf0",    # Cyan
    "Tribunal de Familia - Sala III": "#ffc107",  # Yellow
    "Tribunal de Juicio": "#6610f2"              # Indigo
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
