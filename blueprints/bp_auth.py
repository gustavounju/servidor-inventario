from flask import Blueprint, redirect, render_template, request, session, url_for

from utils.auth import AUTH_SESSION_KEY, auth_mode_label, clear_auth_session, default_landing_url, generate_csrf_token, is_authenticated, validate_login


bp_auth = Blueprint("auth", __name__)


def normalize_next_url(candidate):
    if not candidate or not candidate.startswith("/") or candidate.startswith("//"):
        return default_landing_url()
    return candidate


@bp_auth.route("/login", methods=["GET", "POST"])
def login():
    if is_authenticated():
        return redirect(normalize_next_url(request.args.get("next")))

    error = None
    next_url = normalize_next_url(request.args.get("next") or request.form.get("next"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = validate_login(username, password)
        is_pending = False
        if user:
            if not user.get("is_active"):
                error = "Tu usuario está pendiente de aprobación por un administrador."
                is_pending = True
            else:
                session.clear()
                session[AUTH_SESSION_KEY] = user
                generate_csrf_token()
                return redirect(next_url or default_landing_url(user))
        else:
            error = "Usuario o clave incorrectos."

    return render_template("login.html", error=error, is_pending=is_pending, next_url=next_url, auth_mode_label=auth_mode_label())


@bp_auth.route("/logout", methods=["GET", "POST"])
def logout():
    clear_auth_session()
    return redirect(url_for("auth.login"))


@bp_auth.route("/change_password", methods=["GET", "POST"])
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
                # Refrescar la sesión para que must_change_password sea 0
                refresh_session_user()
                # Ir al dashboard o lo que corresponda
                return redirect(url_for("dashboard.dashboard"))
            except Exception as e:
                error = f"Error al cambiar clave: {str(e)}"

    return render_template("change_password.html", username=username, error=error)
