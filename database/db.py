import sqlite3
import os

def get_connection():
    # garante pasta e usa o mesmo arquivo que products_db.py
    os.makedirs("database", exist_ok=True)
    db_path = os.path.join("database", "acaiteria.db")
    return sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)

def get_connection():
    db_path = os.path.join("database", "db.sqlite3")
    return sqlite3.connect(db_path)