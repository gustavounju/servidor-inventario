import os
from database.db_core import get_db_connection

def get_app_setting(key, default_value=""):
    """
    Recupera una configuración global desde la base de datos (tabla app_settings).
    Si no la encuentra en la BD o hay un error, recurre a os.environ / .env.
    """
    try:
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT setting_value FROM app_settings WHERE setting_key = %s AND is_active = 1", 
                (key,)
            ).fetchone()
            
            if row and row.get("setting_value") is not None:
                val = str(row["setting_value"]).strip()
                # Desencriptar si es necesario
                if key.endswith("PASSWORD") and val.startswith("ENC:"):
                    from utils.crypto import decrypt_secret
                    val = decrypt_secret(val)
                return val
    except Exception:
        # Fallback en caso de que la tabla app_settings no exista aún (migraciones incompletas)
        pass
    
    # Fallback a variable de entorno
    return os.environ.get(key, default_value).strip()
