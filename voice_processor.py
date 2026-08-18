import os
from services.local_voice import parse_voice_command_locally
from utils.network_policy import local_audio_upload_enabled, local_voice_enabled


def process_voice_command(text_command=None, audio_path=None):
    """
    Procesa dictado localmente cuando solo se envía texto.
    El procesamiento de audio queda deshabilitado por defecto para evitar dependencias externas.
    Devuelve un diccionario.
    """
    if audio_path:
        if not local_audio_upload_enabled():
            return {
                "descripcion": "",
                "solicitante": "",
                "is_done": False,
                "solucion": "",
                "error": "La carga de audio está deshabilitada por configuración local.",
                "mode": "disabled",
            }
        return {
            "descripcion": "",
            "solicitante": "",
            "is_done": False,
            "solucion": "",
            "error": "No hay transcripción local de audio configurada en este servidor.",
            "mode": "disabled",
        }

    if not local_voice_enabled():
        return {
            "descripcion": text_command or "",
            "solicitante": "",
            "is_done": False,
            "solucion": "",
            "error": "El procesamiento de voz local está deshabilitado por configuración.",
            "mode": "disabled",
        }

    return parse_voice_command_locally(text_command or "")
