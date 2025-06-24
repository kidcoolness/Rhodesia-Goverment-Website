#!/usr/bin/python3

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_session import Session
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Secure configuration
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")  # Store secret key in env variable
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Secure sessions
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Enable if using HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = "Lax"
Session(app)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Define the User model with role-based access
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    profile_picture = db.Column(db.String(200), nullable=True)  # New field for profile pictures

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

failed_attempts = {}

@app.route('/')
def home():
    if 'user_id' in session:  # If user is logged in, go to dashboard
        return redirect(url_for('dashboard'))
    return render_template('landing.html')  # Show landing page for guests

# User authentication route
@app.route('/login', methods=['GET', 'POST'])
def login():
    print(f"🔎 Debug: Incoming request to /login")
    print(f"🔎 Request method: {request.method}")
    print(f"🔎 Session data: {session}")
    print(f"🔎 User-Agent: {request.headers.get('User-Agent')}")
    
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['role'] = user.role
            return redirect(url_for('dashboard'))

        return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")  # Ensure this page is accessible

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Admin-only route
@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return "Access denied", 403

    users = User.query.all()  # Fetch all users
    return render_template('admin.html', users=users)

@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return "Access denied", 403

    user = User.query.get(user_id)
    if user and user.role != 'admin':  # Prevent deleting admins
        db.session.delete(user)
        db.session.commit()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/make_admin/<int:user_id>')
def make_admin(user_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return "Access denied", 403
    user = User.query.get(user_id)
    if user and user.role != 'admin':  # Prevent promoting existing admins
        user.role = 'admin'
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

# Dashboard (for all logged-in users)
@app.route('/dashboard')
def dashboard():
    print(f"🔎 Debug: Session Data - {session}")  # Print session info
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_count = User.query.count()  # Get total users
    return render_template('dashboard.html', user_count=user_count)

#Route to create an admin account (Run once, then remove for security)
@app.route('/create_admin')
def create_admin():
    if User.query.filter_by(username='admin').first():
        return "Admin already exists", 400

    admin_user = User(username='admin1', role='admin')
    admin_user.set_password('123')  # Change this and remove the route after first use
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
    if 'user_id' not in session or session.get('role') != 'admin':
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
    if 'user_id' not in session or session.get('role') != 'admin':
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
    if 'user_id' not in session or session.get('role') != 'admin':
        return "Access denied", 403

    user = User.query.get(user_id)
    if not user:
        return "User not found", 404

    new_password = request.form.get("new_password")

    if new_password:
        user.set_password(new_password)
        db.session.commit()

    return redirect(url_for('admin_dashboard'))

UPLOAD_FOLDER = 'static/uploads'  # Folder for profile pictures
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

UPLOAD_FOLDER = 'static/uploads'  # Folder for profile pictures
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    new_username = request.form.get("username")
    new_password = request.form.get("new_password")
    profile_picture = request.files.get("profile_picture")

    print(f"New username: {new_username}")  # Debugging
    print(f"New password provided: {bool(new_password)}")  # Debugging
    print(f"Profile picture received: {profile_picture.filename if profile_picture else 'No file'}")  # Debugging

    if new_username:
        user.username = new_username

    if new_password:
        user.set_password(new_password)

    if profile_picture:
        filename = secure_filename(profile_picture.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        profile_picture.save(file_path)
        user.profile_picture = filename  # Store filename in database

    db.session.commit()
    return redirect(url_for('profile'))
    db.session.commit()
    return redirect(url_for('profile'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True,host="192.168.0.4", port="80")
