# models/user_model.py
import sqlite3
import bcrypt
import os

DB_PATH = os.path.join("database", "acaiteria.db")

def get_connection():
    if not os.path.exists("database"):
        os.makedirs("database")
    return sqlite3.connect(DB_PATH)


def create_user_table():
    """
    Cria tabela 'usuarios' com colunas completas.
    Se a tabela já existir, tenta adicionar colunas faltantes (migração leve).
    """
    conn = get_connection()
    cursor = conn.cursor()

    # cria tabela com todas as colunas esperadas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_completo TEXT,
            cpf TEXT UNIQUE,
            celular TEXT,
            username TEXT UNIQUE NOT NULL,
            password BLOB NOT NULL,
            display_name TEXT,
            role TEXT DEFAULT 'operador' CHECK(role IN ('admin', 'operador')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()

    # migração leve: garante que colunas novas existam (sevierem em versões antigas)
    # (Se a coluna já existir, a tentativa de ALTER TABLE será ignorada via try/except)
    cols_to_add = {
        "nome_completo": "TEXT",
        "cpf": "TEXT UNIQUE",
        "celular": "TEXT",
        "display_name": "TEXT"
    }
    for col, col_def in cols_to_add.items():
        try:
            cursor.execute(f"ALTER TABLE usuarios ADD COLUMN {col} {col_def}")
            conn.commit()
        except sqlite3.OperationalError:
            # coluna já existe -> ignora
            pass

    conn.close()


def create_user(nome_completo, cpf, celular, username, password, role="operador", display_name=None):
    """
    Cria um usuário e grava no DB. Retorna True se sucesso.
    Lança ValueError em violação de integridade (usuário/cpf já existem).
    """
    conn = get_connection()
    cursor = conn.cursor()
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    if not display_name:
        display_name = nome_completo or username
    try:
        cursor.execute("""
            INSERT INTO usuarios (nome_completo, cpf, celular, username, password, display_name, role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (nome_completo, cpf, celular, username, hashed, display_name, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        raise ValueError(str(e))
    finally:
        conn.close()


def listar_usuarios():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome_completo, cpf, celular, username, display_name, role, created_at FROM usuarios ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_user_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome_completo, cpf, celular, username, display_name, role, created_at FROM usuarios WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def update_user(user_id, nome_completo, cpf, celular, username, role, display_name=None, password=None):
    """
    Atualiza fields; se password fornecida, atualiza também (hash).
    Retorna True se atualizado.
    """
    conn = get_connection()
    cursor = conn.cursor()
    if not display_name:
        display_name = nome_completo or username
    try:
        if password:
            hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
            cursor.execute("""
                UPDATE usuarios SET nome_completo=?, cpf=?, celular=?, username=?, password=?, display_name=?, role=?
                WHERE id=?
            """, (nome_completo, cpf, celular, username, hashed, display_name, role, user_id))
        else:
            cursor.execute("""
                UPDATE usuarios SET nome_completo=?, cpf=?, celular=?, username=?, display_name=?, role=?
                WHERE id=?
            """, (nome_completo, cpf, celular, username, display_name, role, user_id))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.IntegrityError as e:
        raise ValueError(str(e))
    finally:
        conn.close()


def delete_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


def authenticate(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, password, display_name, role FROM usuarios WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        username_db, password_db, display_name, role = row
        # password_db é bytes (BLOB)
        try:
            if isinstance(password_db, str):
                password_db = password_db.encode("utf-8")
            if bcrypt.checkpw(password.encode("utf-8"), password_db):
                return {"username": username_db, "display_name": display_name or username_db, "role": role}
        except Exception:
            return None
    return None


def create_default_admin():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE role = 'admin'")
    admin_exists = cursor.fetchone()
    conn.close()
    if not admin_exists:
        # cria admin padrão
        try:
            create_user("Administrador", "00000000000", "", "admin", "1234", role="admin", display_name="Administrador")
            print("✅ Usuário padrão: admin / 1234")
        except Exception as e:
            print("Não foi possível criar admin padrão:", e)


def init_user_db():
    create_user_table()
    create_default_admin()


if __name__ == "__main__":
    init_user_db()
    print("user db ready")
