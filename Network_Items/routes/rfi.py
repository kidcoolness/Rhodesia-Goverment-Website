from flask import Blueprint, render_template, request, redirect, url_for, session
from models.rfi import RFI
from flask_login import login_required, current_user
from extensions import db
from flask import jsonify

rfi_bp = Blueprint('rfi', __name__)

@rfi_bp.route("/rfi/new", methods=["GET", "POST"])
@login_required
def new_rfi():
    if request.method == "POST":
        new_rfi = RFI(
            title=request.form["title"],
            description=request.form["description"],
            priority=request.form["priority"],
            requester=current_user.username
        )
        db.session.add(new_rfi)
        db.session.commit()
        return redirect(url_for("rfi.rfi_list"))
    return render_template("rfi_new.html")

@rfi_bp.route("/rfi")
@login_required
def rfi_list():
    rfis = RFI.query.order_by(RFI.timestamp.desc()).all()
    return render_template("rfi_overview.html", rfis=rfis)

@rfi_bp.route("/rfi/approve/<int:rfi_id>", methods=["POST"])
@login_required
def approve_rfi(rfi_id):
    rfi = RFI.query.get(rfi_id)
    if not rfi:
        return jsonify({"error": "RFI not found"}), 404

    if current_user.role not in ["admin", "soc_admin"]:
        return jsonify({"error": "Unauthorized"}), 403

    rfi.status = "Approved"
    db.session.commit()
    return jsonify({"success": True, "status": "Approved"})


@rfi_bp.route("/rfi/deny/<int:rfi_id>", methods=["POST"])
@login_required
def deny_rfi(rfi_id):
    rfi = RFI.query.get(rfi_id)
    if not rfi:
        return jsonify({"error": "RFI not found"}), 404

    if current_user.role not in ["admin", "soc_admin"]:
        return jsonify({"error": "Unauthorized"}), 403

    rfi.status = "Denied"
    db.session.commit()
    return jsonify({"success": True, "status": "Denied"})

@rfi_bp.route("/rfi/delete/<int:rfi_id>", methods=["POST"])
@login_required
def delete_rfi(rfi_id):
    rfi = RFI.query.get(rfi_id)
    if not rfi:
        return jsonify({ "error": "RFI not found" }), 404

    if current_user.role in ["admin", "soc_admin"] or current_user.username == rfi.requester:
        db.session.delete(rfi)
        db.session.commit()
        return jsonify({ "success": True })
    
    return jsonify({ "error": "Access denied" }), 403

@login_required
def delete_rfi(rfi_id):
    rfi = RFI.query.get(rfi_id)
    if not rfi:
        return "RFI not found", 404

    if current_user.role in ["admin", "soc_admin"] or current_user.username == rfi.requester:
        db.session.delete(rfi)
        db.session.commit()
        return redirect(url_for("rfi.rfi_list"))
    
    return "Access denied", 403
