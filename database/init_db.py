# database/init_db.py

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from models.user_model import init_user_db
from models.sales_model import create_sales_table
from database.products_db import create_products_table, fix_old_products_table, populate_default_products

def init_db():
    print("🔧 Inicializando banco de dados...")

    init_user_db()
    create_sales_table()

    create_products_table()
    fix_old_products_table()
    populate_default_products()

    print("✅ Banco de dados inicializado com sucesso.")

if __name__ == "__main__":
    init_db()
