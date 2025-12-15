# controllers/login_controller.py
import sqlite3
import bcrypt
from database.db import get_connection

def verificar_login(username, password):
    """
    Retorna dict com chaves: username, display_name, role
    Ou None se inválido.
    """
    conn = get_connection()  # ← USA A FUNÇÃO DO db.py
    cursor = conn.cursor()
    
    cursor.execute("SELECT username, senha, display_name, role FROM usuarios WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if row:
        username_db, senha_db, display_name_db, role_db = row
        try:
            # senha_db é BLOB (bytes) se tiver sido gravado com bcrypt
            if isinstance(senha_db, str):
                senha_db = senha_db.encode("utf-8")
            if bcrypt.checkpw(password.encode("utf-8"), senha_db):
                return {"username": username_db, "display_name": display_name_db or username_db, "role": role_db}
        except Exception as e:
            print(f"❌ Erro ao verificar senha: {e}")
            return None
    return None