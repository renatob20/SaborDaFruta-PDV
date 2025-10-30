# models/user_model.py
import sqlite3
import bcrypt
import os

DB_PATH = os.path.join("database", "acaiteria.db")

def create_user_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password BLOB NOT NULL,
            display_name TEXT NOT NULL,
            role TEXT DEFAULT 'operador' CHECK(role IN ('admin', 'operador')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def create_user(username, password, display_name, role="operador"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    try:
        cursor.execute("""
            INSERT INTO usuarios (username, password, display_name, role)
            VALUES (?, ?, ?, ?)
        """, (username, hashed, display_name, role))
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError("Usuário já existe!")
    finally:
        conn.close()

def authenticate(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT username, password, display_name, role FROM usuarios WHERE username = ?
    """, (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        username_db, password_db, display_name, role = row
        if bcrypt.checkpw(password.encode("utf-8"), password_db):
            return {"username": username_db, "display_name": display_name, "role": role}
    return None

def create_default_admin():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE role = 'admin'")
    admin_exists = cursor.fetchone()
    if not admin_exists:
        create_user("admin", "1234", "Administrador", "admin")
    conn.close()

def init_user_db():
    create_user_table()
    create_default_admin()

if __name__ == "__main__":
    init_user_db()
    print("user db ready")
