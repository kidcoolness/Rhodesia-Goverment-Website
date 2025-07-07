
#!/bin/bash

echo "[+] Applying RFI system patch with circular import fix..."

# 1. Create extensions.py
cat <<EOF > extensions.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
EOF

# 2. Update models/rfi.py
cat <<EOF > models/rfi.py
from extensions import db
from datetime import datetime

class RFI(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), nullable=False, default="Medium")
    status = db.Column(db.String(20), nullable=False, default="Pending")
    requester = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
EOF

# 3. Update routes/rfi.py
cat <<EOF > routes/rfi.py
from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_login import login_required, current_user
from extensions import db
from models.rfi import RFI

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

@rfi_bp.route("/rfi/approve/<int:rfi_id>")
@login_required
def approve_rfi(rfi_id):
    if current_user.role != "admin":
        return "Access denied", 403
    rfi = RFI.query.get(rfi_id)
    if rfi:
        rfi.status = "Approved"
        db.session.commit()
    return redirect(url_for("rfi.rfi_list"))

@rfi_bp.route("/rfi/reject/<int:rfi_id>")
@login_required
def reject_rfi(rfi_id):
    if current_user.role != "admin":
        return "Access denied", 403
    rfi = RFI.query.get(rfi_id)
    if rfi:
        rfi.status = "Rejected"
        db.session.commit()
    return redirect(url_for("rfi.rfi_list"))
EOF

echo "[+] Done. Now update your app.py:"
echo "  1. Add: from extensions import db"
echo "  2. Replace: db = SQLAlchemy(app) with:"
echo "       db.init_app(app)"
echo "  3. Add after app = Flask(...):"
echo "       from routes.rfi import rfi_bp"
echo "       app.register_blueprint(rfi_bp)"
