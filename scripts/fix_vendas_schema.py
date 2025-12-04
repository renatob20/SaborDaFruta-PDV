import os
import sys
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from database.products_db import get_connection

print("=" * 70)
print("FIX: Adicionando colunas faltantes à tabela vendas")
print("=" * 70)

conn = get_connection()
cur = conn.cursor()

# Verifica esquema atual da tabela vendas
cur.execute("PRAGMA table_info(vendas)")
cols = [r[1] for r in cur.fetchall()]
print(f"\nColunas existentes em 'vendas': {cols}")

# Adiciona colunas faltantes
colunas_faltantes = []

if "valor_recebido" not in cols:
    print("\n  ❌ Falta coluna 'valor_recebido' — adicionando...")
    try:
        cur.execute("ALTER TABLE vendas ADD COLUMN valor_recebido REAL;")
        colunas_faltantes.append("valor_recebido")
        print("  ✅ Coluna 'valor_recebido' adicionada")
    except Exception as e:
        print(f"  ⚠️ Erro ao adicionar 'valor_recebido': {e}")
else:
    print("  ✅ Coluna 'valor_recebido' já existe")

if "troco" not in cols:
    print("\n  ❌ Falta coluna 'troco' — adicionando...")
    try:
        cur.execute("ALTER TABLE vendas ADD COLUMN troco REAL;")
        colunas_faltantes.append("troco")
        print("  ✅ Coluna 'troco' adicionada")
    except Exception as e:
        print(f"  ⚠️ Erro ao adicionar 'troco': {e}")
else:
    print("  ✅ Coluna 'troco' já existe")

if "forma_pagamento" not in cols:
    print("\n  ❌ Falta coluna 'forma_pagamento' — adicionando...")
    try:
        cur.execute("ALTER TABLE vendas ADD COLUMN forma_pagamento TEXT;")
        colunas_faltantes.append("forma_pagamento")
        print("  ✅ Coluna 'forma_pagamento' adicionada")
    except Exception as e:
        print(f"  ⚠️ Erro ao adicionar 'forma_pagamento': {e}")
else:
    print("  ✅ Coluna 'forma_pagamento' já existe")

if "total" not in cols:
    print("\n  ❌ Falta coluna 'total' — adicionando...")
    try:
        cur.execute("ALTER TABLE vendas ADD COLUMN total REAL DEFAULT 0.0;")
        colunas_faltantes.append("total")
        print("  ✅ Coluna 'total' adicionada")
    except Exception as e:
        print(f"  ⚠️ Erro ao adicionar 'total': {e}")
else:
    print("  ✅ Coluna 'total' já existe")

# Salva as mudanças
if colunas_faltantes:
    conn.commit()
    print(f"\n✅ Banco atualizado: {len(colunas_faltantes)} coluna(s) adicionada(s)")
else:
    print("\n✅ Banco já possui todas as colunas necessárias")

# Mostra schema final
print("\n" + "=" * 70)
print("Schema FINAL da tabela vendas:")
print("=" * 70)
cur.execute("PRAGMA table_info(vendas)")
for row in cur.fetchall():
    print(f"  {row}")

conn.close()
print("\n" + "=" * 70)
print("FIX CONCLUÍDO")
print("=" * 70)