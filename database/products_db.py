# database/products_db.py

import os
import sqlite3

DB_PATH = os.path.join("database", "acaiteria.db")

def get_connection():
    os.makedirs("database", exist_ok=True)
    return sqlite3.connect(DB_PATH)


# 1️⃣ CRIA TABELA (COM sabor PERMITINDO NULL)
def create_products_table():
    conn = get_connection()
    cur = conn.cursor()

    # Criar tabela nova se não existir
    cur.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL,
            sabor TEXT,
            preco REAL NOT NULL,
            estoque INTEGER DEFAULT 0
        );
    """)

    conn.commit()
    conn.close()


# 2️⃣ RECRIA A TABELA SE A COLUNA SABOR ESTIVER COMO NOT NULL
def fix_old_products_table():
    conn = get_connection()
    cur = conn.cursor()

    # Verifica colunas
    cur.execute("PRAGMA table_info(produtos);")
    cols = cur.fetchall()

    # Procura a coluna sabor com NOT NULL
    for col in cols:
        if col[1] == "sabor" and col[3] == 1:
            print("⚠️ Tabela antiga detectada. Corrigindo...")

            # salvar produtos antigos
            cur.execute("SELECT id, nome, tipo, sabor, preco, estoque FROM produtos;")
            old_data = cur.fetchall()

            # renomeia tabela
            cur.execute("ALTER TABLE produtos RENAME TO produtos_old;")

            # cria tabela nova correta
            create_products_table()

            # restaura dados
            for p in old_data:
                cur.execute("""
                    INSERT INTO produtos (id, nome, tipo, sabor, preco, estoque)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, p)

            cur.execute("DROP TABLE produtos_old;")
            conn.commit()
            conn.close()
            print("✅ Tabela corrigida com sucesso.")
            return

    conn.close()


# 3️⃣ VERIFICA SE PRODUTO EXISTE
def add_product_if_not_exists(nome, tipo, sabor, preco, estoque=0):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id FROM produtos 
        WHERE nome=? AND tipo=? AND (sabor=? OR sabor IS NULL)
    """, (nome, tipo, sabor))

    exists = cur.fetchone()

    if exists:
        conn.close()
        return False

    cur.execute("""
        INSERT INTO produtos (nome, tipo, sabor, preco, estoque)
        VALUES (?, ?, ?, ?, ?)
    """, (nome, tipo, sabor, preco, estoque))

    conn.commit()
    conn.close()
    return True


# 4️⃣ POPULAR DADOS INICIAIS
def populate_default_products():
    print("📦 Inserindo produtos iniciais...")

    produtos = [
        ("Sorvete", "Sorvete", None, 55.00, 0),

        ("Picolé Chocolate", "Picolé", "Chocolate", 1.50, 200),
        ("Picolé Morango", "Picolé", "Morango", 1.50, 200),
        ("Picolé Uva", "Picolé", "Uva", 1.50, 200),
        ("Picolé Coco", "Picolé", "Coco", 1.50, 200),
        ("Picolé Limão", "Picolé", "Limão", 1.50, 200),

        ("Água Mineral 500ml", "Bebida", None, 3.00, 50),
        ("Refrigerante Lata", "Bebida", None, 6.00, 50),
        ("Suco Natural", "Bebida", None, 7.00, 20),

        ("Copo 300ml", "Copo", None, 10.00, 999),
        ("Copo 500ml", "Copo", None, 12.00, 999),
    ]

    total_inseridos = 0

    for nome, tipo, sabor, preco, estoque in produtos:
        if add_product_if_not_exists(nome, tipo, sabor, preco, estoque):
            print(f"  ✔ {nome}")
            total_inseridos += 1

    print(f"📌 {total_inseridos} produtos adicionados.")


if __name__ == "__main__":
    create_products_table()
    fix_old_products_table()
    populate_default_products()
    print("✅ Produtos configurados!")
