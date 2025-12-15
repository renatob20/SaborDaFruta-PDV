import sqlite3
from datetime import datetime
from database.db import get_connection  # ← USAR A FUNÇÃO

def registrar_venda(tipo_produto, sabor, quantidade, valor_unit, forma_pagamento, operador, observacoes=""):
    conn = get_connection()  # ← USAR A FUNÇÃO
    cursor = conn.cursor()

    valor_total = quantidade * valor_unit
    data_venda = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO vendas (data_venda, tipo_produto, sabor, quantidade, valor_unit, valor_total, forma_pagamento, operador, observacoes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data_venda, tipo_produto, sabor, quantidade, valor_unit, valor_total, forma_pagamento, operador, observacoes))

    conn.commit()
    conn.close()
