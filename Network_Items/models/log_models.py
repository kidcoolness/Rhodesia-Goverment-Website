
import sqlite3

def get_all_logs():
    conn = sqlite3.connect('logs/events.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    logs = {}
    for table in ['login_events', 'file_uploads', 'page_visits', 'account_events', 'live_users']:
        cur.execute(f"SELECT * FROM {table} ORDER BY timestamp DESC LIMIT 50" if table != 'live_users' else "SELECT * FROM live_users")
        logs[table] = [dict(row) for row in cur.fetchall()]
    conn.close()
    return logs
