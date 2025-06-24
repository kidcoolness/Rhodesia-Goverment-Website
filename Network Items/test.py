from app import app, db
from sqlalchemy import text

with app.app_context():
    with db.engine.connect() as connection:
        result = connection.execute(text("PRAGMA table_info(user);"))  # Use `text()` in SQLAlchemy 2.x
        columns = result.fetchall()

    for col in columns:
        print(col)  # Prints column details
