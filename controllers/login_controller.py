# controllers/login_controller.py
import sqlite3
import bcrypt
import os

DB_PATH = os.path.join("database", "acaiteria.db")

def verificar_login(username, password):
    """
    Retorna dict com chaves: username, display_name, role
    Ou None se inválido.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username, password, display_name, role FROM usuarios WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if row:
        username_db, password_db, display_name_db, role_db = row
        try:
            # password_db é BLOB (bytes) se tiver sido gravado com bcrypt
            if isinstance(password_db, str):
                password_db = password_db.encode("utf-8")
            if bcrypt.checkpw(password.encode("utf-8"), password_db):
                return {"username": username_db, "display_name": display_name_db or username_db, "role": role_db}
        except Exception:
            # em caso de qualquer problema com bcrypt, trata como falha
            return None
    return None
