from flask import Blueprint, abort, redirect, render_template, url_for
from utils.auth import current_technician_identity, current_user

bp_tecnicos = Blueprint('tecnicos', __name__)

@bp_tecnicos.route("/tecnicos")
def tecnicos_view():
    if current_user().get("role") == "operador":
        return redirect(url_for("operadores.operadores_view"))
    return render_template("tecnicos.html", mobile_identity=current_technician_identity())

@bp_tecnicos.route("/tecnicos/scanner")
def tecnicos_scanner_view():
    if current_user().get("role") == "operador":
        abort(403)
    return render_template("mobile_scanner.html")
