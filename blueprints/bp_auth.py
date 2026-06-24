import os
import tempfile

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from utils.auth import AUTH_SESSION_KEY, auth_mode_label, clear_auth_session, default_landing_url, generate_csrf_token, is_authenticated, validate_login
from services.pdf_ocr_queue import OcrFileTooLargeError, OcrQueueFullError, pdf_ocr_queue
from utils.extensions import limiter

bp_auth = Blueprint("auth", __name__)


def normalize_next_url(candidate):
    if not candidate or not candidate.startswith("/") or candidate.startswith("//"):
        return default_landing_url()
    return candidate


@bp_auth.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if is_authenticated():
        return redirect(normalize_next_url(request.args.get("next")))

    error = None
    is_pending = False
    next_url = normalize_next_url(request.args.get("next") or request.form.get("next"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = validate_login(username, password)
        if user:
            if not user.get("is_active"):
                error = "Tu usuario está pendiente de aprobación por un administrador."
                is_pending = True
            else:
                session.clear()
                if request.form.get("remember"):
                    session.permanent = True
                session[AUTH_SESSION_KEY] = user
                generate_csrf_token()
                return redirect(next_url or default_landing_url(user))
        else:
            error = "Usuario o clave incorrectos."

    return render_template("login.html", error=error, is_pending=is_pending, next_url=next_url, auth_mode_label=auth_mode_label())


@bp_auth.route("/pdf-local", methods=["GET"])
def pdf_local_tool():
    return render_template("pdf_local_tool_page.html")


@bp_auth.route("/api/local/pdf-ocr", methods=["POST"])
@limiter.limit("20 per minute")
def local_pdf_ocr():
    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        return jsonify({"status": "error", "message": "No se recibió ningún PDF."}), 400

    if not uploaded.filename.lower().endswith(".pdf"):
        return jsonify({"status": "error", "message": "El archivo debe ser PDF."}), 400

    temp_path = None
    try:
        from services.pdf_ocr import LocalOCRConfigurationError, extract_pdf_text_local

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            temp_path = tmp.name
            uploaded.save(temp_path)

        job = pdf_ocr_queue.enqueue(temp_path, uploaded.filename, extract_pdf_text_local)
        temp_path = None
        return jsonify(job), 202
    except OcrQueueFullError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 429
    except OcrFileTooLargeError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 413
    except LocalOCRConfigurationError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


@bp_auth.route("/api/local/pdf-ocr/<job_id>", methods=["GET"])
def local_pdf_ocr_status(job_id):
    job = pdf_ocr_queue.get_status(job_id)
    if not job:
        return jsonify({"status": "error", "message": "Trabajo OCR no encontrado o expirado."}), 404
    return jsonify(job)


@bp_auth.route("/logout", methods=["GET", "POST"])
def logout():
    clear_auth_session()
    return redirect(url_for("auth.login"))

@bp_auth.route("/change_password", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def change_password():
    # Solo usuarios logueados
    if not is_authenticated():
        return redirect(url_for("auth.login"))

    from utils.auth import current_username, update_app_user_password, refresh_session_user
    username = current_username()
    error = None

    if request.method == "POST":
        new_pass = request.form.get("new_password")
        confirm_pass = request.form.get("confirm_password")

        if not new_pass:
            error = "Debes ingresar una nueva clave."
        elif new_pass != confirm_pass:
            error = "Las claves no coinciden."
        elif len(new_pass) < 6:
            error = "La clave debe tener al menos 6 caracteres."
        else:
            try:
                update_app_user_password(username, new_pass)
                refreshed_user = refresh_session_user()
                return redirect(default_landing_url(refreshed_user))
            except Exception as e:
                error = f"Error al cambiar clave: {str(e)}"

    return render_template("change_password.html", username=username, error=error)
