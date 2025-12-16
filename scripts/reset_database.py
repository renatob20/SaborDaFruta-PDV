# scripts/reset_database.py
# -*- coding: utf-8 -*-

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from database.db import ensure_schema
from services.auth_service import create_user


def reset_database():
    db_path = os.path.join(ROOT, "database", "acaiteria.db")

    if os.path.exists(db_path):
        os.remove(db_path)
        print("✅ Banco antigo removido")

    ensure_schema()
    print("✅ Estrutura criada")

    create_user(
        display_name="Administrador",
        username="admin",
        password="1234",
        role="admin"
    )

    print("✅ Usuário admin criado (admin / 1234)")
    print("🎉 Banco pronto para produção!")


if __name__ == "__main__":
    reset_database()
