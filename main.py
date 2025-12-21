# main.py
"""
Sabor da Fruta PDV - Sistema de Ponto de Venda
Ponto de entrada principal do sistema
VERSÃO CORRIGIDA: Melhor tratamento de erros para executável
"""

import os
import sys
import traceback
import logging

# Configura logging para capturar erros
log_file = os.path.join(os.path.expanduser("~"), "SaborDaFruta-PDV", "error.log")
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Adiciona pasta raiz ao path
if getattr(sys, 'frozen', False):
    # Executável PyInstaller
    ROOT = os.path.dirname(sys.executable)
    logger.info(f"Modo: Executável - Pasta: {ROOT}")
else:
    # Modo desenvolvimento
    ROOT = os.path.dirname(os.path.abspath(__file__))
    logger.info(f"Modo: Desenvolvimento - Pasta: {ROOT}")

sys.path.insert(0, ROOT)

# Importa versão
try:
    from config.version import __version__, __app_name__
    logger.info(f"🍦 {__app_name__} v{__version__}")
    print(f"🍦 {__app_name__} v{__version__}")
except ImportError as e:
    logger.warning(f"Arquivo de versão não encontrado: {e}")
    print("⚠️ Arquivo de versão não encontrado")
    __version__ = "1.0.0"
    __app_name__ = "Sabor da Fruta PDV"

# Inicializa banco de dados
print("🔧 Inicializando banco de dados...")
logger.info("Inicializando banco de dados...")

try:
    from database.db import ensure_schema, criar_usuario_admin_padrao
    
    if ensure_schema():
        logger.info("Schema do banco verificado com sucesso")
        print("✅ Schema do banco verificado")
        
        if criar_usuario_admin_padrao():
            logger.info("Usuário admin verificado")
            print("✅ Usuário admin verificado")
        else:
            logger.warning("Falha ao verificar usuário admin")
    else:
        logger.error("Falha ao verificar schema")
        print("❌ Falha ao verificar schema")

except Exception as e:
    logger.error(f"Erro ao inicializar banco: {e}")
    logger.error(traceback.format_exc())
    print(f"❌ Erro ao inicializar banco: {e}")
    
    # Mostra erro em janela
    try:
        import tkinter.messagebox as mbox
        mbox.showerror(
            "Erro de Inicialização",
            f"Erro ao inicializar banco de dados:\n{e}\n\n"
            f"Log salvo em:\n{log_file}"
        )
    except:
        pass

# Popula produtos iniciais (só na primeira vez)
try:
    from database.products_db import populate_default_products
    populate_default_products()
    logger.info("Produtos padrão verificados")
except Exception as e:
    logger.warning(f"Erro ao popular produtos: {e}")
    # Não é crítico, continua

# Inicia interface
print("🚀 Iniciando interface...")
logger.info("Iniciando interface gráfica...")

def handle_exception(exc_type, exc_value, exc_traceback):
    """Handler global para exceções não tratadas"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger.error("Exceção não tratada:")
    logger.error("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    
    try:
        import tkinter.messagebox as mbox
        error_msg = f"{exc_type.__name__}: {exc_value}"
        mbox.showerror(
            "Erro Fatal",
            f"Ocorreu um erro inesperado:\n\n{error_msg}\n\n"
            f"Log salvo em:\n{log_file}\n\n"
            f"Por favor, contate o suporte."
        )
    except:
        pass

# Instala handler global
sys.excepthook = handle_exception

if __name__ == "__main__":
    try:
        import ttkbootstrap as ttk
        from ui.login_ui import LoginUI
        
        logger.info("Criando janela principal...")
        
        # Cria a janela principal com ttkbootstrap
        root = ttk.Window(themename="superhero")
        
        logger.info("Criando interface de login...")
        
        # Cria a interface de login passando o master
        app = LoginUI(master=root)
        
        logger.info("Iniciando loop principal...")
        
        # Inicia o loop principal
        root.mainloop()
        
        logger.info("Aplicação encerrada normalmente")
        
    except KeyboardInterrupt:
        logger.info("Sistema encerrado pelo usuário (Ctrl+C)")
        print("\n⏹️ Sistema encerrado pelo usuário")

    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        logger.error(traceback.format_exc())
        print(f"❌ Erro fatal: {e}")
        
        try:
            import tkinter.messagebox as mbox
            mbox.showerror(
                "Erro Fatal", 
                f"Erro fatal ao iniciar:\n{e}\n\n"
                f"Log salvo em:\n{log_file}"
            )
        except:
            pass
        
        sys.exit(1)