# main.py
from database.init_db import init_db
import tkinter as tk
from ui.login_ui import LoginUI

if __name__ == "__main__":
    init_db()           # cria tabelas e admin padrão
    root = tk.Tk()
    app = LoginUI(root)
    root.mainloop()
