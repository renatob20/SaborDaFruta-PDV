import sys
import os
import sqlite3
import traceback

# garante imports
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

print("=" * 70)
print("TEST: bater_ponto_db — diagnóstico completo")
print("=" * 70)

# 1. Test get_connection
print("\n1. Testando get_connection()...")
try:
    from database.products_db import get_connection
    conn = get_connection()
    print("   ✅ get_connection() OK — usando acaiteria.db")
    conn.close()
except Exception as e:
    print(f"   ❌ Erro ao importar/chamar get_connection(): {e}")
    traceback.print_exc()
    sys.exit(1)

# 2. Test ensure_tables
print("\n2. Testando ensure_tables()...")
try:
    from database.bater_ponto_db import ensure_tables
    ensure_tables()
    print("   ✅ ensure_tables() OK — tabela ponto_batidas criada/validada")
except Exception as e:
    print(f"   ❌ Erro ao rodar ensure_tables(): {e}")
    traceback.print_exc()
    sys.exit(1)

# 3. Test listar_operadores
print("\n3. Testando listar_operadores()...")
try:
    from database.bater_ponto_db import listar_operadores
    ops = listar_operadores()
    print(f"   ✅ listar_operadores() retornou {len(ops)} operadores:")
    for op in ops:
        print(f"      {op}")
    if not ops:
        print("   ⚠️  AVISO: lista vazia! Verificar tabela usuarios no banco.")
except Exception as e:
    print(f"   ❌ Erro ao rodar listar_operadores(): {e}")
    traceback.print_exc()

# 4. Inspecionar schema da tabela usuarios
print("\n4. Inspecionando schema da tabela usuarios...")
try:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(usuarios)")
    cols = cur.fetchall()
    print(f"   Colunas encontradas:")
    for col in cols:
        print(f"      {col}")
    conn.close()
except Exception as e:
    print(f"   ❌ Erro ao inspecionar schema: {e}")
    traceback.print_exc()

# 5. Test registrar_batida
print("\n5. Testando registrar_batida()...")
try:
    from database.bater_ponto_db import registrar_batida
    # assume primeiro operador (id=1)
    bid = registrar_batida(1, "entrada")
    print(f"   ✅ Batida registrada com ID: {bid}")
except Exception as e:
    print(f"   ❌ Erro ao registrar batida: {e}")
    traceback.print_exc()

# 6. Test listar_batidas_periodo
print("\n6. Testando listar_batidas_periodo()...")
try:
    from database.bater_ponto_db import listar_batidas_periodo
    batidas = listar_batidas_periodo(periodo="diario")
    print(f"   ✅ listar_batidas_periodo('diario') retornou {len(batidas)} registros:")
    for b in batidas[:5]:  # mostra primeiros 5
        print(f"      {b}")
except Exception as e:
    print(f"   ❌ Erro ao listar batidas: {e}")
    traceback.print_exc()

print("\n" + "=" * 70)
print("TESTE CONCLUÍDO")
print("=" * 70)