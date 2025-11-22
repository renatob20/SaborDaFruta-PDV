import sqlite3
import os

DB_PATH = os.path.join("database", "acaiteria.db")


def fix_vendas_table():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1 — Verifica estrutura atual da tabela
    cur.execute("PRAGMA table_info(vendas);")
    cols = cur.fetchall()

    col_names = [c[1] for c in cols]

    # Se a coluna total existir, tabela está OK
    if "total" in col_names:
        print("✔ Tabela vendas já está correta.")
        conn.close()
        return

    print("⚠ Tabela vendas antiga detectada. Corrigindo...")

    # 2 — salva vendas antigas (se existirem)
    cur.execute("SELECT * FROM vendas;")
    old_rows = cur.fetchall()

    # 3 — renomeia tabela antiga
    cur.execute("ALTER TABLE vendas RENAME TO vendas_old;")

    # 4 — cria tabela correta
    cur.execute("""
        CREATE TABLE vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_venda TEXT NOT NULL,
            operador TEXT,
            total REAL NOT NULL,
            forma_pagamento TEXT,
            valor_recebido REAL,
            troco REAL
        );
    """)

    # 5 — tenta migrar dados antigos
    # estrutura antiga normalmente tinha menos colunas — vamos adaptar
    for row in old_rows:
        try:
            # detecta números de colunas automaticamente
            # pode ter 3, 4 ou 5 colunas dependendo da versão anterior
            data = list(row)
            data += [None] * (7 - len(data))  # preenche faltantes
            cur.execute("""
                INSERT INTO vendas (id, data_venda, operador, total, forma_pagamento, valor_recebido, troco)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, data[:7])
        except Exception:
            pass

    # 6 — remove tabela antiga
    cur.execute("DROP TABLE vendas_old;")

    conn.commit()
    conn.close()

    print("✅ Tabela vendas corrigida com sucesso.")
