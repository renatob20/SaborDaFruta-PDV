import os
import sys
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from database.products_db import get_connection

print("=" * 80)
print("FIX COMPLETO: Recriando tabelas de vendas com schema correto")
print("=" * 80)

conn = get_connection()
cur = conn.cursor()

# 1. Verifica schema atual
print("\n[1] Schema ATUAL da tabela vendas:")
try:
    cur.execute("PRAGMA table_info(vendas)")
    cols = cur.fetchall()
    for col in cols:
        print(f"    {col}")
except Exception as e:
    print(f"    Erro ao verificar: {e}")

# 2. Renomeia tabela antiga
print("\n[2] Renomeando tabela vendas antiga...")
try:
    cur.execute("ALTER TABLE vendas RENAME TO vendas_old")
    print("    ✅ Tabela renomeada para vendas_old")
except Exception as e:
    print(f"    ⚠️ Erro (pode não existir): {e}")

# 3. Cria tabela vendas CORRETA
print("\n[3] Criando tabela vendas com schema CORRETO...")
try:
    cur.execute("""
        CREATE TABLE vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_produto TEXT NOT NULL,
            data_venda TEXT NOT NULL,
            operador TEXT,
            forma_pagamento TEXT,
            valor_recebido REAL,
            troco REAL,
            total REAL DEFAULT 0.0
        )
    """)
    print("    ✅ Tabela vendas criada com sucesso")
except Exception as e:
    print(f"    ❌ Erro ao criar: {e}")

# 4. Garante tabela venda_items
print("\n[4] Criando tabela venda_items (se não existir)...")
try:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS venda_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venda_id INTEGER NOT NULL,
            produto_id INTEGER,
            produto_nome TEXT,
            tipo TEXT,
            quantidade INTEGER,
            peso_kg REAL,
            preco_unitario REAL,
            subtotal REAL,
            FOREIGN KEY(venda_id) REFERENCES vendas(id)
        )
    """)
    print("    ✅ Tabela venda_items criada/verificada")
except Exception as e:
    print(f"    ❌ Erro: {e}")

# 5. Salva mudanças
conn.commit()

# 6. Verifica schema final
print("\n[5] Schema FINAL da tabela vendas:")
cur.execute("PRAGMA table_info(vendas)")
cols = cur.fetchall()
for col in cols:
    print(f"    {col[1]:20} {col[2]:15} {'NOT NULL' if col[3] else 'nullable'}")

# 7. Conta registros
try:
    cur.execute("SELECT COUNT(*) FROM vendas")
    count = cur.fetchone()[0]
    print(f"\n    Total de vendas: {count}")
except Exception:
    print("    Total de vendas: 0 (tabela nova)")

conn.close()

print("\n" + "=" * 80)
print("✅ FIX CONCLUÍDO - Banco pronto para usar")
print("=" * 80)
print("\nPróximos passos:")
print("1. Feche a aplicação completamente")
print("2. Execute: python main.py")
print("3. Teste criar uma venda")