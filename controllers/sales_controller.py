import sqlite3
from datetime import datetime

def registrar_venda(tipo_produto, sabor, quantidade, valor_unit, forma_pagamento, operador, observacoes=""):
    conn = sqlite3.connect("database/db.sqlite3")
    cursor = conn.cursor()

    valor_total = quantidade * valor_unit
    data_venda = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO vendas (data_venda, tipo_produto, sabor, quantidade, valor_unit, valor_total, forma_pagamento, operador, observacoes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data_venda, tipo_produto, sabor, quantidade, valor_unit, valor_total, forma_pagamento, operador, observacoes))

    conn.commit()
    conn.close()
