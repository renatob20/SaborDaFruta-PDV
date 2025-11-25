"""
database/ponto_db.py

Banco de dados para o módulo de Bater Ponto.

Usa a tabela `usuarios` para identificar os funcionários.
Armazena marcações (entrada/saída) ilimitadas por dia.
Permite exportação em CSV.
"""

import os
import sqlite3
from datetime import datetime

# -------------------------------------------
# Conexão com o mesmo banco do sistema inteiro
# -------------------------------------------
DB_PATH = os.path.join("database", "acaiteria.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_connection():
    return sqlite3.connect(DB_PATH)

# -------------------------------------------
# Criação da tabela de batidas
# -------------------------------------------
def ensure_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bater_ponto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            funcionario_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,              -- entrada | saída
            timestamp TEXT NOT NULL,
            FOREIGN KEY(funcionario_id) REFERENCES usuarios(id)
        );
    """)

    conn.commit()
    conn.close()


# -------------------------------------------
# Listar funcionários (role = operador)
# -------------------------------------------
def listar_operadores():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, COALESCE(display_name, username), username
        FROM usuarios
        WHERE role = 'operador'
        ORDER BY display_name COLLATE NOCASE;
    """)

    rows = cur.fetchall()
    conn.close()

    return rows


# -------------------------------------------
# Registrar batida
# -------------------------------------------
def registrar_batida(funcionario_id: int, tipo: str):
    tipo = tipo.lower().strip()
    if tipo not in ("entrada", "saida", "saída"):
        raise ValueError("Tipo inválido. Use: entrada, saida.")

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO bater_ponto (funcionario_id, tipo, timestamp)
        VALUES (?, ?, ?)
    """, (funcionario_id, tipo, ts))

    conn.commit()
    last_id = cur.lastrowid
    conn.close()

    return last_id


# -------------------------------------------
# Listar batidas (todas ou por funcionário)
# -------------------------------------------
def listar_batidas(funcionario_id=None, limit=200):
    conn = get_connection()
    cur = conn.cursor()

    if funcionario_id:
        cur.execute("""
            SELECT b.id, b.funcionario_id, b.tipo, b.timestamp,
                   COALESCE(u.display_name, u.username)
            FROM bater_ponto b
            LEFT JOIN usuarios u ON u.id = b.funcionario_id
            WHERE b.funcionario_id = ?
            ORDER BY b.timestamp DESC
            LIMIT ?
        """, (funcionario_id, limit))
    else:
        cur.execute("""
            SELECT b.id, b.funcionario_id, b.tipo, b.timestamp,
                   COALESCE(u.display_name, u.username)
            FROM bater_ponto b
            LEFT JOIN usuarios u ON u.id = b.funcionario_id
            ORDER BY b.timestamp DESC
            LIMIT ?
        """, (limit,))

    rows = cur.fetchall()
    conn.close()

    return rows


# -------------------------------------------
# Exportar CSV
# -------------------------------------------
def exportar_batidas_csv(path, funcionario_id=None):
    import csv
    rows = listar_batidas(funcionario_id, limit=10000)

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "funcionario_id", "tipo", "timestamp", "nome"])

        for r in rows:
            w.writerow(r)

    return path


# -------------------------------------------
# Execução direta (teste)
# -------------------------------------------
if __name__ == "__main__":
    ensure_tables()
    print("Tabela bater_ponto OK.")
    print("Operadores:", listar_operadores())
