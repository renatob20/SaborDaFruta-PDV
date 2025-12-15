import sqlite3
import bcrypt
from database.db import get_connection  # ← ADICIONAR

def autenticar_usuario(usuario, senha):
    conn = get_connection()  # ← USAR A FUNÇÃO
    cursor = conn.cursor()

    cursor.execute("SELECT nome, senha, tipo FROM usuarios WHERE usuario = ?", (usuario,))
    user = cursor.fetchone()

    conn.close()

    if user and bcrypt.checkpw(senha.encode(), user[1].encode()):
        return user[0], user[2]  # retorna nome e tipo
    return None
