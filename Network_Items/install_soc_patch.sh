
#!/bin/bash

echo "[+] Setting up Rhodesian SOC patch..."

# Ensure we're in the Flask app root
APP_ROOT=$(pwd)

# Create directories if missing
mkdir -p utils models templates/logs static/assets/css

# Download SOC patch zip
ZIP_PATH="soc_upgrade_patch.zip"
if [ ! -f "$ZIP_PATH" ]; then
    echo "[!] Patch zip not found. Place 'soc_upgrade_patch.zip' in project root."
    exit 1
fi

# Unzip patch
unzip -o "$ZIP_PATH" -d .

# Add SOC blueprint if not exists
ROUTES_FILE="routes/soc.py"
mkdir -p routes
if [ ! -f "$ROUTES_FILE" ]; then
cat <<EOF > $ROUTES_FILE
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models.log_models import get_all_logs

soc_bp = Blueprint('soc', __name__)

@soc_bp.route("/soc")
@login_required
def soc_dashboard():
    if current_user.role != "soc_admin":
        return "Access Denied", 403
    logs = get_all_logs()
    return render_template("soc.html", logs=logs)
EOF
    echo "[+] Created routes/soc.py"
fi

# Register blueprint if not already in app.py
APP_FILE="app.py"
if ! grep -q "register_blueprint(soc_bp)" "$APP_FILE"; then
    sed -i '' '/from flask_session import Session/a\
from routes.soc import soc_bp
' "$APP_FILE"
    sed -i '' '/app = Flask(__name__)/a\
app.register_blueprint(soc_bp)
' "$APP_FILE"
    echo "[+] Registered SOC blueprint in app.py"
fi

# Create log DB
mkdir -p logs
python3 -c "from utils.logger import init_log_db; init_log_db()"
echo "[+] Log database initialized at logs/events.db"

echo "[✔] SOC patch installed. Start Flask and visit /soc as a soc_admin."
