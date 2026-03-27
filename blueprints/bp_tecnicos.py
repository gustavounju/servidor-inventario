from flask import Blueprint, render_template
from utils.auth import current_technician_identity

bp_tecnicos = Blueprint('tecnicos', __name__)

@bp_tecnicos.route("/tecnicos")
def tecnicos_view():
    return render_template("tecnicos.html", mobile_identity=current_technician_identity())
