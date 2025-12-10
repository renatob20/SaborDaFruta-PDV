import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "acaiteria.db")

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Verifica se a coluna antiga ainda existe
    cur.execute("PRAGMA table_info(vendas)")
    cols = [c[1] for c in cur.fetchall()]

    if "quantidade" not in cols:
        print("✔ Tabela já está atualizada. Nada a fazer.")
        return

    print("⚠ Migração necessária: removendo coluna 'quantidade'...")

    # 1 — Renomeia tabela antiga
    cur.execute("ALTER TABLE vendas RENAME TO vendas_old;")

    # 2 — Cria tabela correta
    cur.execute("""
        CREATE TABLE vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_venda TEXT NOT NULL,
            operador TEXT,
            forma_pagamento TEXT,
            valor_recebido REAL,
            troco REAL,
            total REAL DEFAULT 0.0
        );
    """)

    # 3 — Copia os dados compatíveis
    cur.execute("""
        INSERT INTO vendas (id, data_venda, operador, forma_pagamento, valor_recebido, troco, total)
        SELECT id, data_venda, operador, forma_pagamento, valor_recebido, troco, total
        FROM vendas_old;
    """)

    # 4 — Remove tabela antiga
    cur.execute("DROP TABLE vendas_old;")

    conn.commit()
    conn.close()

    print("✅ Migração concluída. Sistema atualizado com sucesso!")

if __name__ == "__main__":
    migrate()
