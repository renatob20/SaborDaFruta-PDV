# main.py
"""
Sabor da Fruta PDV - Sistema de Ponto de Venda
Ponto de entrada principal do sistema
"""

import os
import sys

# Adiciona pasta raiz ao path
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

# Importa versão
try:
    from config.version import __version__, __app_name__
    print(f"🍦 {__app_name__} v{__version__}")
except ImportError:
    print("⚠️ Arquivo de versão não encontrado")
    __version__ = "1.0.0"
    __app_name__ = "Sabor da Fruta PDV"

# Inicializa banco de dados
print("🔧 Inicializando banco de dados...")
from database.db import ensure_schema, criar_usuario_admin_padrao

try:
    ensure_schema()
    criar_usuario_admin_padrao()
    print("✅ Banco de dados inicializado")
except Exception as e:
    print(f"❌ Erro ao inicializar banco: {e}")
    import traceback
    traceback.print_exc()

# Popula produtos iniciais (só na primeira vez)
try:
    from database.products_db import populate_default_products
    populate_default_products()
except Exception as e:
    # Se der erro, provavelmente já tem produtos
    pass

# Inicia interface
print("🚀 Iniciando interface...")

if __name__ == "__main__":
    try:
        import ttkbootstrap as ttk
        from ui.login_ui import LoginUI
        
        # Cria a janela principal com ttkbootstrap
        root = ttk.Window(themename="superhero")
        
        # Cria a interface de login passando o master
        app = LoginUI(master=root)
        
        # Inicia o loop principal
        root.mainloop()
        
    except KeyboardInterrupt:
        print("\n⏹️ Sistema encerrado pelo usuário")
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        input("Pressione ENTER para fechar...")