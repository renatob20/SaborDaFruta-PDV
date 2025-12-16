# services/auth_service.py
# -*- coding: utf-8 -*-

import bcrypt
from database.db import get_connection


def hash_password(password: str) -> bytes:
    """Gera hash bcrypt"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


def verify_password(password: str, hashed) -> bool:
    """Verifica senha bcrypt com segurança"""
    try:
        # Se vier como string (erro de encoding), tenta converter
        if isinstance(hashed, str):
            # Tenta decodificar do formato que o SQLite salvou
            try:
                hashed = hashed.encode('latin1')
            except:
                return False
        
        return bcrypt.checkpw(password.encode("utf-8"), hashed)
    except Exception as e:
        print(f"❌ Erro ao verificar senha: {e}")
        return False


def create_user(display_name, username, password, role, cpf=None, celular=None, nome_completo=None):
    """Cria usuário com senha criptografada"""
    conn = get_connection()
    cur = conn.cursor()

    senha_hash = hash_password(password)
    
    # Verifica quais colunas existem
    cur.execute("PRAGMA table_info(usuarios)")
    cols = [c[1] for c in cur.fetchall()]
    
    # Monta query dinamicamente baseado nas colunas existentes
    if "nome_completo" in cols and "cpf" in cols and "celular" in cols:
        cur.execute("""
            INSERT INTO usuarios (nome_completo, cpf, celular, display_name, username, senha, role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            nome_completo or display_name,
            cpf or "000.000.000-00",
            celular or "",
            display_name,
            username,
            senha_hash,  # ← Salva como bytes (BLOB)
            role
        ))
    else:
        # Fallback para estrutura antiga
        cur.execute("""
            INSERT INTO usuarios (display_name, username, senha, role)
            VALUES (?, ?, ?, ?)
        """, (display_name, username, senha_hash, role))

    conn.commit()
    conn.close()


def authenticate(username, password):
    """Autentica usuário"""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, display_name, username, senha, role
        FROM usuarios
        WHERE username = ?
    """, (username,))

    user = cur.fetchone()
    conn.close()

    if not user:
        print(f"⚠️ Usuário '{username}' não encontrado")
        return None

    user_id, display_name, username_db, senha_hash, role = user

    if verify_password(password, senha_hash):
        return {
            "id": user_id,
            "display_name": display_name,
            "username": username_db,
            "role": role
        }

    print(f"⚠️ Senha incorreta para '{username}'")
    return None