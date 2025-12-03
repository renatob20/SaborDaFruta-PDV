# database/bater_ponto_db.py

import os
import sqlite3
from datetime import datetime, timedelta
import csv

# tenta usar a mesma conexão do módulo products_db (acaiteria.db)
try:
    from database.products_db import get_connection
except Exception:
    # fallback mínimo
    def get_connection():
        os.makedirs("database", exist_ok=True)
        return sqlite3.connect(os.path.join("database", "acaiteria.db"))

# cria tabela ponto_batidas se necessário
def ensure_tables():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ponto_batidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            funcionario_id INTEGER NOT NULL,
            tipo TEXT NOT NULL, -- 'entrada' ou 'saida'
            timestamp TEXT NOT NULL
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ponto_func_ts ON ponto_batidas(funcionario_id, timestamp)")
    conn.commit()
    conn.close()

# retorna lista de operadores [(id, display_name, username), ...]
def listar_operadores():
    conn = get_connection()
    cur = conn.cursor()
    # tenta campos comuns na tabela usuarios
    try:
        cur.execute("SELECT id, display_name, username FROM usuarios ORDER BY display_name")
        rows = cur.fetchall()
    except Exception:
        # fallback para esquemas diferentes
        try:
            cur.execute("SELECT id, nome, username FROM usuarios ORDER BY nome")
            rows = cur.fetchall()
        except Exception:
            rows = []
    conn.close()
    return rows

# registra uma batida e retorna id inserido
def registrar_batida(funcionario_id: int, tipo: str):
    ts = datetime.now().isoformat(sep=' ')
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO ponto_batidas (funcionario_id, tipo, timestamp) VALUES (?, ?, ?)",
                (funcionario_id, tipo, ts))
    conn.commit()
    bid = cur.lastrowid
    conn.close()
    return bid

# lista batidas (join com usuarios) mais recentes, opcionalmente por funcionario
def listar_batidas(funcionario_id=None, limit=500):
    conn = get_connection()
    cur = conn.cursor()
    q = """
        SELECT p.id, u.display_name, p.tipo, p.timestamp
        FROM ponto_batidas p
        LEFT JOIN usuarios u ON p.funcionario_id = u.id
    """
    params = []
    if funcionario_id is not None:
        q += " WHERE p.funcionario_id = ?"
        params.append(funcionario_id)
    q += " ORDER BY p.timestamp DESC LIMIT ?"
    params.append(limit)
    cur.execute(q, params)
    rows = cur.fetchall()
    conn.close()
    return rows

# lista batidas filtrando por periodo: diario, semanal, mensal
def listar_batidas_periodo(periodo: str = "diario", funcionario_id=None):
    now = datetime.now()
    if periodo == "diario":
        start = datetime(now.year, now.month, now.day)
    elif periodo == "semanal":
        start = datetime(now.year, now.month, now.day) - timedelta(days=now.weekday())
    elif periodo == "mensal":
        start = datetime(now.year, now.month, 1)
    else:
        start = datetime(1970, 1, 1)

    start_ts = start.isoformat(sep=' ')
    conn = get_connection()
    cur = conn.cursor()
    q = """
        SELECT p.id, u.display_name, p.tipo, p.timestamp
        FROM ponto_batidas p
        LEFT JOIN usuarios u ON p.funcionario_id = u.id
        WHERE p.timestamp >= ?
    """
    params = [start_ts]
    if funcionario_id is not None:
        q += " AND p.funcionario_id = ?"
        params.append(funcionario_id)
    q += " ORDER BY p.timestamp DESC"
    cur.execute(q, params)
    rows = cur.fetchall()
    conn.close()
    return rows

# exporta batidas para CSV
def exportar_batidas_csv(path: str, funcionario_id=None):
    rows = listar_batidas(funcionario_id=funcionario_id, limit=10000)
    with open(path, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "funcionario_id", "tipo", "timestamp", "nome"])
        for r in rows:
            writer.writerow(r)
    return path

# wrapper compatível com UI moderna
def exportar_csv(path: str, funcionario_id=None):
    return exportar_batidas_csv(path, funcionario_id=funcionario_id)

# função para atualizar batida (usada pelo Ajustar Ponto)
def atualizar_batida(batida_id: int, novo_tipo: str):
    novo_tipo = (novo_tipo or "").strip().lower()
    if novo_tipo not in ("entrada", "saida"):
        raise ValueError("novo_tipo inválido")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE ponto_batidas SET tipo = ? WHERE id = ?", (novo_tipo, batida_id))
    conn.commit()
    conn.close()
    return True

# teste rápido
if __name__ == "__main__":
    ensure_tables()
    print("ponto_batidas OK")
