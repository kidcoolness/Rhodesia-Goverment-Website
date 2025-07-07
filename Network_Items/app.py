#!/usr/bin/python3

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from extensions import db
from flask_bcrypt import Bcrypt
from flask_session import Session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import os

from routes.soc import soc_bp
from utils.logger import init_log_db, log_visit

from routes.rfi import rfi_bp


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

app.register_blueprint(rfi_bp)

# Flask Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_SAMESITE'] = "Lax"
Session(app)

# Extensions
db.init_app(app)
bcrypt = Bcrypt(app)
init_log_db()

# Flask-Login Setup
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# User Model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    profile_picture = db.Column(db.String(200), nullable=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Middleware logger
@app.before_request
def before_any_request():
    log_visit()

# Register Blueprints
app.register_blueprint(soc_bp)

# Routes
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            session['user_id'] = user.id
            session['role'] = user.role
            return redirect(url_for('dashboard'))

        return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")

@app.route('/logout')
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin')
def admin_dashboard():
    if not current_user.is_authenticated or current_user.role != 'admin':
        return "Access denied", 403
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if not current_user.is_authenticated or current_user.role != 'admin':
        return "Access denied", 403
    user = User.query.get(user_id)
    if user and user.role != 'admin':
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/make_admin/<int:user_id>')
def make_admin(user_id):
    if not current_user.is_authenticated or current_user.role != 'admin':
        return "Access denied", 403
    user = User.query.get(user_id)
    if user and user.role != 'admin':
        user.role = 'admin'
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/dashboard')
def dashboard():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    user_count = User.query.count()
    return render_template('dashboard.html', user_count=user_count)

@app.route('/create_admin')
def create_admin():
    if User.query.filter_by(username='admin11').first():
        return "Admin already exists", 400
    admin_user = User(username='admin11', role='admin')
    admin_user.set_password('123')
    db.session.add(admin_user)
    db.session.commit()
    return "Admin account created"

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            return "Passwords do not match!", 400

        if User.query.filter_by(username=username).first():
            return "Username already exists!", 400

        new_user = User(username=username, role="user")
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/bank')
def bank():
    return render_template('bank.html')

@app.route('/launchcodes')
def launchcodes():
    if not current_user.is_authenticated or current_user.role != 'admin':
        return "Access Denied", 403
    return render_template('launchcodes.html')

@app.route('/employee')
def employee():
    return render_template('employee.html')

@app.route('/landing')
def landing():
    return render_template('landing.html')

@app.route('/edit_user/<int:user_id>', methods=['POST'])
def edit_user(user_id):
    if not current_user.is_authenticated or current_user.role != 'admin':
        return "Access denied", 403
    user = User.query.get(user_id)
    if not user:
        return "User not found", 404
    new_username = request.form.get("username")
    new_role = request.form.get("role")
    if new_username:
        user.username = new_username
    if new_role in ["admin", "user"]:
        user.role = new_role
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/reset_password/<int:user_id>', methods=['POST'])
def reset_password(user_id):
    if not current_user.is_authenticated or current_user.role != 'admin':
        return "Access denied", 403
    user = User.query.get(user_id)
    if not user:
        return "User not found", 404
    new_password = request.form.get("new_password")
    if new_password:
        user.set_password(new_password)
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/profile')
def profile():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    user = User.query.get(current_user.id)
    return render_template('profile.html', user=user)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    user = User.query.get(current_user.id)
    new_username = request.form.get("username")
    new_password = request.form.get("new_password")
    profile_picture = request.files.get("profile_picture")

    if new_username:
        user.username = new_username
    if new_password:
        user.set_password(new_password)
    if profile_picture:
        filename = secure_filename(profile_picture.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        profile_picture.save(file_path)
        user.profile_picture = filename

    db.session.commit()
    return redirect(url_for('profile'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port="80")
