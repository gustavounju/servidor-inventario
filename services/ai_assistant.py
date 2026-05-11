from classifier import SimpleNaiveBayes, SEED_DATA
from database.db_core import get_db_connection
import json
import os
import re
import unicodedata
from dotenv import load_dotenv

# Instancia global del clasificador local Naive Bayes
ai_classifier = SimpleNaiveBayes()
load_dotenv()

ALLOWED_CATEGORIES = {
    "Audiencias",
    "Hardware",
    "Software",
    "Red/Conectividad",
    "Impresoras",
    "Usuarios",
    "General",
}
GROQ_CATEGORY_MODEL = os.environ.get("GROQ_CATEGORY_MODEL", "llama-3.3-70b-versatile")
GROQ_CATEGORY_TIMEOUT = float(os.environ.get("GROQ_CATEGORY_TIMEOUT", "4"))
_groq_client = None

KEYWORD_CATEGORY_RULES = [
    (
        "Audiencias",
        {
            "gesell", "geselle", "camara gesell", "camara geselle", "audiencia",
            "audiencias", "video grabada", "videograbada", "grabacion de audiencia",
            "grabar audiencia",
        },
    ),
    (
        "Software",
        {
            "reinstalar", "reinstalacion", "re instalar", "formatear", "formateo",
            "instalar windows", "reinstalar windows", "sistema operativo", "windows",
            "office", "word", "excel", "backup", "respaldo",
        },
    ),
    (
        "Impresoras",
        {
            "impresora", "imprimir", "imprime", "impresion", "toner", "cartucho",
            "tinta", "papel", "bandeja", "atascado", "atascada", "atasco",
        },
    ),
    (
        "Hardware",
        {
            "camara", "camera", "webcam", "microfono", "mic", "auricular", "auriculares",
            "parlante", "parlantes", "monitor", "pantalla", "teclado", "mouse", "raton",
            "scanner", "escaner", "lector", "usb", "cable hdmi", "hdmi", "proyector",
            "pc", "computadora", "cpu", "notebook", "equipo nuevo", "nueva pc",
            "llevar pc", "llevar la pc", "llevar nueva pc", "llevar la nueva pc",
            "cambiar pc", "reemplazar pc",
        },
    ),
    (
        "Red/Conectividad",
        {
            "internet", "wifi", "wi fi", "red", "carpeta compartida", "ip",
            "vpn", "conexion", "conectividad", "navegador", "pagina",
        },
    ),
    (
        "Usuarios",
        {
            "clave", "contrasena", "password", "usuario bloqueado", "dominio",
            "login", "acceso", "correo",
        },
    ),
]


def _normalize_text(text):
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"\s+", " ", text.lower()).strip()
    return text


def _keyword_category(descripcion):
    normalized = _normalize_text(descripcion)
    if not normalized:
        return None

    padded = f" {normalized} "
    for category, keywords in KEYWORD_CATEGORY_RULES:
        for keyword in keywords:
            key = _normalize_text(keyword)
            if " " in key:
                if key in normalized:
                    return category
            elif re.search(rf"\b{re.escape(key)}\b", padded):
                return category
    return None


def _normalize_category(category):
    normalized = _normalize_text(category)
    aliases = {
        "hardware": "Hardware",
        "audiencia": "Audiencias",
        "audiencias": "Audiencias",
        "gesell": "Audiencias",
        "geselle": "Audiencias",
        "perifericos": "Hardware",
        "periferico": "Hardware",
        "camara": "Hardware",
        "software": "Software",
        "sistema": "Software",
        "aplicacion": "Software",
        "aplicaciones": "Software",
        "red": "Red/Conectividad",
        "red conectividad": "Red/Conectividad",
        "conectividad": "Red/Conectividad",
        "internet": "Red/Conectividad",
        "impresora": "Impresoras",
        "impresoras": "Impresoras",
        "impresion": "Impresoras",
        "usuarios": "Usuarios",
        "usuario": "Usuarios",
        "cuentas": "Usuarios",
        "general": "General",
    }
    if category in ALLOWED_CATEGORIES:
        return category
    return aliases.get(normalized)


def _get_groq_client():
    global _groq_client
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None
    if _groq_client is None:
        from groq import Groq
        _groq_client = Groq(api_key=api_key, timeout=GROQ_CATEGORY_TIMEOUT, max_retries=0)
    return _groq_client


def _groq_category(descripcion):
    client = _get_groq_client()
    if client is None:
        return None

    categories = ", ".join(sorted(ALLOWED_CATEGORIES))
    prompt = f"""
Clasifica una tarea de soporte técnico judicial en UNA sola categoría.
Categorías válidas: {categories}.

Reglas:
- Cámara, webcam, micrófono, auriculares, teclado, mouse, monitor, scanner y periféricos físicos => Hardware.
- Cámara Gesell/Geselle, audiencias, audiencia videograbada o grabación de audiencia => Audiencias.
- Reinstalar PC, formatear, reinstalar Windows, sistema operativo, Office o backup => Software.
- Nueva PC, llevar/cambiar/reemplazar PC, computadora, notebook o CPU => Hardware.
- Impresora, toner, tinta, papel, impresión o atasco => Impresoras.
- Internet, WiFi, red, VPN, IP, conexión o carpetas compartidas => Red/Conectividad.
- Claves, usuarios, permisos, acceso, correo o cuentas => Usuarios.
- Programas, Windows, Office, sistema, errores de aplicación o backup => Software.
- Si no alcanza la información => General.

Responde exclusivamente JSON: {{"categoria": "..."}}.

Tarea: "{descripcion}"
"""
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=GROQ_CATEGORY_MODEL,
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content.strip()
        data = json.loads(content)
        return _normalize_category(data.get("categoria", ""))
    except Exception as e:
        print(f"Groq category fallback: {e}")
        return None

def train_ai_model():
    """Entrena la IA con datos semilla + datos históricos de la DB."""
    try:
        # 1. Entrenar con Semilla (Base Knowledge)
        ai_classifier.train(SEED_DATA)
        print(f"IA: Entrenada con {len(SEED_DATA)} ejemplos semilla.")

        # 2. Entrenar con Datos del Usuario (Incremental Learning)
        conn = get_db_connection()
        tasks = conn.execute("SELECT descripcion, categoria FROM tasks WHERE categoria IS NOT NULL AND categoria != ''").fetchall()
        conn.close()

        user_data = [(t['descripcion'], t['categoria']) for t in tasks]
        if user_data:
            ai_classifier.train(user_data)
            print(f"IA: Refinada con {len(user_data)} tareas históricas.")
        
    except Exception as e:
        print(f"Error entrenando IA: {e}")

def predict_category(descripcion):
    """Clasifica la tarea con reglas rápidas, Groq y fallback local Naive Bayes."""
    if not descripcion:
        return "General"

    rule_prediction = _keyword_category(descripcion)
    if rule_prediction:
        return rule_prediction

    groq_prediction = _groq_category(descripcion)
    if groq_prediction:
        return groq_prediction
    
    # Fallback local: siempre disponible aunque Groq falle o no tenga API key.
    prediction = ai_classifier.predict(descripcion)
    return prediction
