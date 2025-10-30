import sqlite3
import os

def get_connection():
    db_path = os.path.join("database", "db.sqlite3")
    return sqlite3.connect(db_path)
