from flask import jsonify

def success_response(data=None, message: str = None, status_code: int = 200):
    """
    Normaliza la respuesta de éxito JSON en la API.
    Estructura: { "status": "success", "data": data, "message": message }
    """
    payload = {"status": "success"}
    if data is not None:
        payload["data"] = data
    if message is not None:
        payload["message"] = message
    return jsonify(payload), status_code

def error_response(code: str, message: str, details=None, status_code: int = 400):
    """
    Normaliza la respuesta de error JSON en la API.
    Estructura: { "status": "error", "error": { "code": code, "message": message, "details": details } }
    """
    payload = {
        "status": "error",
        "error": {
            "code": code,
            "message": message
        }
    }
    if details is not None:
        payload["error"]["details"] = details
    return jsonify(payload), status_code
