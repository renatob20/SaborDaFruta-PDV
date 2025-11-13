# main.py
import ttkbootstrap as ttk
from ui.login_ui import LoginUI
from database.init_db import init_db

# Inicializa o banco
init_db()

if __name__ == "__main__":
    # Cria a janela principal com ttkbootstrap
    root = ttk.Window(themename="superhero")
    app = LoginUI(master=root)
    root.mainloop()
