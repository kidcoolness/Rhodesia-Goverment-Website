
#!/bin/bash

echo "[+] Installing RFI Ticketing System..."

# Ensure we're in Flask root
mkdir -p models routes templates

# Write RFI model
mkdir -p models
cat <<EOF > models/rfi.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class RFI(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), nullable=False, default="Medium")
    status = db.Column(db.String(20), nullable=False, default="Pending")
    requester = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
EOF

# Write RFI route
mkdir -p routes
cat <<EOF > routes/rfi.py
from flask import Blueprint, render_template, request, redirect, url_for, session
from models.rfi import db, RFI
from flask_login import login_required, current_user

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

# Templates
mkdir -p templates

cat <<EOF > templates/rfi_new.html
{% extends 'base.html' %}
{% block content %}
<h2>Submit New RFI</h2>
<form method="POST">
    <div class="mb-3">
        <label class="form-label">Title</label>
        <input name="title" class="form-control" required>
    </div>
    <div class="mb-3">
        <label class="form-label">Description</label>
        <textarea name="description" class="form-control" rows="4" required></textarea>
    </div>
    <div class="mb-3">
        <label class="form-label">Priority</label>
        <select name="priority" class="form-select">
            <option>Low</option>
            <option selected>Medium</option>
            <option>High</option>
        </select>
    </div>
    <button type="submit" class="btn btn-primary">Submit RFI</button>
</form>
{% endblock %}
EOF

cat <<EOF > templates/rfi_overview.html
{% extends 'base.html' %}
{% block content %}
<h2>RFI Dashboard</h2>
<table class="table table-striped">
    <thead>
        <tr>
            <th>Title</th><th>Requester</th><th>Priority</th><th>Status</th><th>Submitted</th>
            {% if session.get('role') == 'admin' %}<th>Actions</th>{% endif %}
        </tr>
    </thead>
    <tbody>
    {% for rfi in rfis %}
        <tr>
            <td>{{ rfi.title }}</td>
            <td>{{ rfi.requester }}</td>
            <td>{{ rfi.priority }}</td>
            <td>{{ rfi.status }}</td>
            <td>{{ rfi.timestamp.strftime('%Y-%m-%d %H:%M') }}</td>
            {% if session.get('role') == 'admin' %}
            <td>
                <a href="{{ url_for('rfi.approve_rfi', rfi_id=rfi.id) }}" class="btn btn-success btn-sm">Approve</a>
                <a href="{{ url_for('rfi.reject_rfi', rfi_id=rfi.id) }}" class="btn btn-danger btn-sm">Reject</a>
            </td>
            {% endif %}
        </tr>
    {% endfor %}
    </tbody>
</table>
{% endblock %}
EOF

echo "[+] RFI components installed. Don't forget to:"
echo "1. Add \`from routes.rfi import rfi_bp\` to app.py"
echo "2. Register with \`app.register_blueprint(rfi_bp)\`"
echo "3. Run db.create_all() to initialize tables"
