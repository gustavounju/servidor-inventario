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
        if user:
            session.clear()
            session[AUTH_SESSION_KEY] = user
            generate_csrf_token()
            return redirect(next_url or default_landing_url(user))
        error = "Usuario o clave incorrectos."

    return render_template("login.html", error=error, next_url=next_url, auth_mode_label=auth_mode_label())


@bp_auth.route("/logout", methods=["GET", "POST"])
def logout():
    clear_auth_session()
    return redirect(url_for("auth.login"))
