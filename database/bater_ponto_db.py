# database/bater_ponto_db.py
"""
Banco de dados do módulo Bater Ponto.
Integra com a tabela `usuarios` já existente no sistema.

Funções exportadas:
- ensure_tables()
- listar_operadores()
- registrar_batida(funcionario_id, tipo)  # tipo: 'entrada' ou 'saida'
- listar_batidas(funcionario_id=None, limit=500)
- listar_batidas_periodo(periodo='diario', funcionario_id=None)
- contar_batidas_dia(funcionario_id)
- exportar_batidas_csv(path, funcionario_id=None)
- exportar_csv(path, funcionario_id=None)  # alias compatibilidade
"""

import os
import sqlite3
from datetime import datetime, date, timedelta

# tenta reutilizar o get_connection do projeto
try:
    from database.db import get_connection
except Exception:
    def get_connection():
        db_path = os.path.join("database", "acaiteria.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        return sqlite3.connect(db_path)

# ----------------------------
# Criação de tabela
# ----------------------------
def ensure_tables():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ponto_batidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            funcionario_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,               -- 'entrada' ou 'saida'
            timestamp TEXT NOT NULL,
            FOREIGN KEY(funcionario_id) REFERENCES usuarios(id)
        );
    """)
    conn.commit()
    conn.close()

# ----------------------------
# Listar operadores (role = operador)
# ----------------------------
def listar_operadores():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, COALESCE(display_name, username) AS display, username
        FROM usuarios
        WHERE role = 'operador'
        ORDER BY display COLLATE NOCASE
    """)
    rows = cur.fetchall()
    conn.close()
    return rows  # list of tuples (id, display, username)

# ----------------------------
# Registrar batida
# ----------------------------
def registrar_batida(funcionario_id: int, tipo: str):
    tipo = (tipo or "").strip().lower()
    if tipo not in ("entrada", "saida"):
        raise ValueError("tipo deve ser 'entrada' ou 'saida'")

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO ponto_batidas (funcionario_id, tipo, timestamp) VALUES (?, ?, ?)",
                (funcionario_id, tipo, ts))
    conn.commit()
    bid = cur.lastrowid
    conn.close()
    return bid

# ----------------------------
# Listar batidas (simples)
# ----------------------------
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
    return rows  # (id, funcionario_id, tipo, timestamp, nome)

# ----------------------------
# Listar batidas por período (diario, semanal, mensal)
# ----------------------------
def listar_batidas_periodo(periodo: str = "diario", funcionario_id=None):
    periodo = (periodo or "diario").strip().lower()
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
        # filtra por data local atual
        cur.execute("SELECT date('now','localtime')")
        dia = cur.fetchone()[0]
        base += " AND DATE(b.timestamp) = DATE(?) "
        params.append(dia)
    elif periodo == "semanal":
        base += " AND DATE(b.timestamp) BETWEEN DATE('now', '-6 days') AND DATE('now', 'localtime') "
    elif periodo == "mensal":
        base += " AND strftime('%Y-%m', b.timestamp) = strftime('%Y-%m', 'now', 'localtime') "

    if funcionario_id:
        base += " AND b.funcionario_id = ? "
        params.append(funcionario_id)

    base += " ORDER BY b.id DESC "

    cur.execute(base, params)
    rows = cur.fetchall()
    conn.close()
    return rows

# ----------------------------
# Conta quantas batidas o funcionário tem no dia atual (localtime)
# ----------------------------
def contar_batidas_dia(funcionario_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM ponto_batidas
        WHERE funcionario_id = ?
        AND DATE(timestamp) = DATE('now', 'localtime')
    """, (funcionario_id,))
    cnt = cur.fetchone()[0] or 0
    conn.close()
    return int(cnt)

# ----------------------------
# Exportar CSV
# ----------------------------
def exportar_batidas_csv(path: str, funcionario_id: int = None):
    import csv
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    rows = listar_batidas(funcionario_id=funcionario_id, limit=10000)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "funcionario_id", "tipo", "timestamp", "nome"])
        for r in rows:
            writer.writerow(r)
    return path

# alias compatibilidade com UI antigo
def exportar_csv(path: str, funcionario_id: int = None):
    return exportar_batidas_csv(path, funcionario_id=funcionario_id)


# execução direta para teste
if __name__ == "__main__":
    ensure_tables()
    print("Tabela ponto_batidas verificada.")
    print("Operadores:", listar_operadores()[:10])
