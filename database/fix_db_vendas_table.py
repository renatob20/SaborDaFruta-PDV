import sqlite3
import os

DB_PATH = os.path.join("database", "acaiteria.db")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Descobre colunas existentes
cur.execute("PRAGMA table_info(vendas)")
cols = [c[1] for c in cur.fetchall()]

# Campos novos que vamos garantir
required_columns = {
    "tipo_produto": "TEXT",
    "valor_recebido": "REAL DEFAULT 0.0",
    "troco": "REAL DEFAULT 0.0",
    "total": "REAL DEFAULT 0.0"
}

for col, col_type in required_columns.items():
    if col not in cols:
        print(f"▶ Adicionando coluna: {col}")
        try:
            cur.execute(f"ALTER TABLE vendas ADD COLUMN {col} {col_type}")
        except Exception as e:
            print(f"⚠ Erro ao adicionar {col}: {e}")

conn.commit()
conn.close()

print("\n✅ Correção concluída — execute novamente o sistema!")
