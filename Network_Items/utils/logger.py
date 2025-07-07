
import sqlite3
from datetime import datetime
from flask import request
from flask_login import current_user
import os

DB_PATH = 'logs/events.db'

def init_log_db():
    os.makedirs("logs", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS login_events (
        id INTEGER PRIMARY KEY,
        user TEXT,
        ip TEXT,
        status TEXT,
        timestamp TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS file_uploads (
        id INTEGER PRIMARY KEY,
        user TEXT,
        filename TEXT,
        timestamp TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS page_visits (
        id INTEGER PRIMARY KEY,
        user TEXT,
        endpoint TEXT,
        ip TEXT,
        method TEXT,
        timestamp TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS live_users (
        user TEXT,
        ip TEXT,
        path TEXT,
        last_seen TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS account_events (
        user TEXT,
        action TEXT,
        target TEXT,
        timestamp TEXT
    )""")
    conn.commit()
    conn.close()

def log_visit():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    username = getattr(current_user, 'username', 'guest')
    ip = request.remote_addr
    path = request.path
    now = datetime.utcnow().isoformat()

    cur.execute("INSERT INTO page_visits (user, endpoint, ip, method, timestamp) VALUES (?, ?, ?, ?, ?)", (
        username, path, ip, request.method, now
    ))

    cur.execute("DELETE FROM live_users WHERE user = ?", (username,))
    cur.execute("INSERT INTO live_users (user, ip, path, last_seen) VALUES (?, ?, ?, ?)", (
        username, ip, path, now
    ))

    conn.commit()
    conn.close()

def log_account_event(actor, action, target):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute("INSERT INTO account_events (user, action, target, timestamp) VALUES (?, ?, ?, ?)", (
        actor, action, target, now
    ))
    conn.commit()
    conn.close()
