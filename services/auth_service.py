import bcrypt
from database.db import get_connection
from models.user_model import User

def authenticate(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user_row = cursor.fetchone()
    conn.close()

    if user_row and bcrypt.checkpw(password.encode('utf-8'), user_row["password_hash"]):
        return User(
            id=user_row["id"],
            username=user_row["username"],
            display_name=user_row["display_name"],
            role=user_row["role"]
        )
    return None

def create_user(username: str, password: str, display_name: str = None, role: str = "user"):
    username = username.strip()
    if role not in ("admin", "user"):
        raise ValueError("Role inválida. Use 'admin' ou 'user'.")

    if len(password) < 4:
        raise ValueError("Senha muito curta (mínimo 4 caracteres).")

    conn = get_connection()
    cursor = conn.cursor()
    # checar se já existe
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        raise ValueError("Usuário já existe.")

    pw_bytes = password.encode('utf-8')
    hashed = bcrypt.hashpw(pw_bytes, bcrypt.gensalt())

    cursor.execute(
        "INSERT INTO users (username, password_hash, display_name, role) VALUES (?, ?, ?, ?)",
        (username, hashed, display_name, role)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id

def list_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, display_name, role, created_at FROM users ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    # retornar lista de dicionários
    return [dict(r) for r in rows]

def get_user_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, display_name, role FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_user(user_id, username=None, password=None, display_name=None, role=None):
    # validações básicas
    conn = get_connection()
    cursor = conn.cursor()
    # checar existência
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        raise ValueError("Usuário não encontrado.")

    updates = []
    params = []

    if username is not None:
        username = username.strip()
        # checar duplicidade
        cursor.execute("SELECT id FROM users WHERE username = ? AND id != ?", (username, user_id))
        if cursor.fetchone():
            conn.close()
            raise ValueError("Outro usuário com esse username já existe.")
        updates.append("username = ?")
        params.append(username)

    if password is not None:
        if password != "":
            if len(password) < 4:
                conn.close()
                raise ValueError("Senha muito curta (mínimo 4 caracteres).")
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            updates.append("password_hash = ?")
            params.append(hashed)

    if display_name is not None:
        updates.append("display_name = ?")
        params.append(display_name)

    if role is not None:
        if role not in ("admin", "user"):
            conn.close()
            raise ValueError("Role inválida.")
        updates.append("role = ?")
        params.append(role)

    if not updates:
        conn.close()
        return True

    sql = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
    params.append(user_id)
    cursor.execute(sql, params)
    conn.commit()
    conn.close()
    return True

def delete_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    changed = cursor.rowcount
    conn.commit()
    conn.close()
    return changed > 0