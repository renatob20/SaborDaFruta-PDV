# database/bater_ponto_db.py

import os
import sqlite3
from datetime import datetime
# usa função get_connection do projeto se existir
try:
    from database.db import get_connection
except Exception:
    def get_connection():
        db_path = os.path.join("database", "acaiteria.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        return sqlite3.connect(db_path)
# cria tabela se necessário
def ensure_tables():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ponto_batidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            funcionario_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY(funcionario_id) REFERENCES usuarios(id)
        );
    """)
    conn.commit()
    conn.close()
def listar_operadores():
    """Retorna lista de (id, display_name, username)."""
    conn = get_connection()
    cur = conn.cursor()
    # se tabela usuarios não existir, erro será lançado e tratado na UI
    cur.execute("SELECT id, display_name, username FROM usuarios WHERE role = 'operador' ORDER BY COALESCE(display_name, username) COLLATE NOCASE")
    rows = cur.fetchall()
    conn.close()
    result = []
    for r in rows:
        uid, display, username = r
        display_final = display if display and display.strip() else username
        result.append((uid, display_final, username))
    return result
def registrar_batida(funcionario_id: int, tipo: str):
    tipo = (tipo or "").strip().lower()
    if tipo not in ("entrada", "saida"):
        raise ValueError("tipo deve ser 'entrada' ou 'saida'")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO ponto_batidas (funcionario_id, tipo, timestamp) VALUES (?, ?, ?)", (funcionario_id, tipo, ts))
    conn.commit()
    bid = cur.lastrowid
    conn.close()
    return bid
def listar_batidas(funcionario_id=None, limit=500):
    conn = get_connection()
    cur = conn.cursor()
    if funcionario_id:
        cur.execute("""
            SELECT b.id, b.funcionario_id, b.tipo, b.timestamp, COALESCE(u.display_name, u.username)
            FROM ponto_batidas b
            LEFT JOIN usuarios u ON u.id = b.funcionario_id
            WHERE b.funcionario_id = ?
            ORDER BY b.id DESC
            LIMIT ?
        """, (funcionario_id, limit))
    else:
        cur.execute("""
            SELECT b.id, b.funcionario_id, b.tipo, b.timestamp, COALESCE(u.display_name, u.username)
            FROM ponto_batidas b
            LEFT JOIN usuarios u ON u.id = b.funcionario_id
            ORDER BY b.id DESC
            LIMIT ?
        """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows
def listar_batidas_periodo(periodo: str = "diario", funcionario_id=None):
    periodo = (periodo or "").lower().strip()
    conn = get_connection()
    cur = conn.cursor()
    base = """
        SELECT b.id, b.funcionario_id, b.tipo, b.timestamp, COALESCE(u.display_name, u.username)
        FROM ponto_batidas b
        LEFT JOIN usuarios u ON u.id = b.funcionario_id
        WHERE 1=1
    """
    params = []
    if periodo == "diario":
        cur.execute("SELECT date('now', 'localtime')")
        dia = cur.fetchone()[0]
        base += " AND DATE(timestamp) = DATE(?) "
        params.append(dia)
    elif periodo == "semanal":
        base += " AND DATE(timestamp) BETWEEN DATE('now', '-6 days') AND DATE('now', 'localtime') "
    elif periodo == "mensal":
        base += " AND strftime('%Y-%m', timestamp) = strftime('%Y-%m', 'now', 'localtime') "
    if funcionario_id:
        base += " AND funcionario_id = ? "
        params.append(funcionario_id)
    base += " ORDER BY b.id DESC "
    cur.execute(base, params)
    rows = cur.fetchall()
    conn.close()
    return rows
def exportar_batidas_csv(path: str, funcionario_id=None):
    import csv
    rows = listar_batidas(funcionario_id=funcionario_id, limit=10000)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
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
