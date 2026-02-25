import os

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
    "EQINT": "Equipo Interdisciplinario"
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
    "Equipo Interdisciplinario": "#ffc107"       # Yellow
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
