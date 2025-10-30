import sqlite3
import bcrypt

def autenticar_usuario(usuario, senha):
    conn = sqlite3.connect("database/db.sqlite3")
    cursor = conn.cursor()

    cursor.execute("SELECT nome, senha, tipo FROM usuarios WHERE usuario = ?", (usuario,))
    user = cursor.fetchone()

    conn.close()

    if user and bcrypt.checkpw(senha.encode(), user[1].encode()):
        return user[0], user[2]  # retorna nome e tipo
    return None
