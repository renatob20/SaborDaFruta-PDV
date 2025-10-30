# database/init_db.py
from models.user_model import init_user_db
from models.sales_model import create_sales_table

def init_db():
    init_user_db()
    create_sales_table()
    print("✅ Banco de dados inicializado com sucesso.")

if __name__ == "__main__":
    init_db()
