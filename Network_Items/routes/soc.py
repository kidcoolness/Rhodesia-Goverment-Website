from flask import Blueprint, render_template
from flask_login import login_required, current_user

soc_bp = Blueprint('soc', __name__)

@soc_bp.route("/soc")
@login_required
def soc_dashboard():
    if current_user.role != "soc_admin":
        return "Access Denied", 403
    return render_template("soc.html", logs={})  # <- Fix: empty logs passed

@soc_bp.route("/soc/logs")
@login_required
def get_soc_logs():
    if current_user.role != "soc_admin":
        return "Access Denied", 403
    from models.log_models import get_all_logs
    logs = get_all_logs()
    return render_template("partials/soc_tables.html", logs=logs)
