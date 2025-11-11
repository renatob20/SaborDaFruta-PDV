# ui/login_ui.py
import sys
import os
# garante que imports relativos funcionem quando chamado por subprocess
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys as _sys

from controllers.login_controller import verificar_login

class LoginUI(tk.Frame):
    """
    Frame de login — deve ser instanciado com master=root (root = tk.Tk()).
    main.py faz: root = tk.Tk(); app = LoginUI(master=root); app.mainloop()
    """
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        # configurações da janela principal
        self.master.title("Açaiteria o Sabor da Fruta - Login")
        self.master.geometry("360x220")
        self.master.resizable(False, False)
        self.pack(fill="both", expand=True)
        self._build_ui()   # <-- garante que o método exista

    def _build_ui(self):
        # cabeçalho
        header = ttk.Frame(self, padding=12)
        header.pack(fill="x")
        ttk.Label(header, text="Açaiteria - Acessar Sistema", font=("Segoe UI", 12, "bold")).pack()

        form = ttk.Frame(self, padding=12)
        form.pack(fill="x", pady=6)

        ttk.Label(form, text="Usuário:").grid(row=0, column=0, sticky="w", pady=6)
        ttk.Label(form, text="Senha:").grid(row=1, column=0, sticky="w", pady=6)

        self.username_entry = ttk.Entry(form, width=30)
        self.username_entry.grid(row=0, column=1, padx=6, pady=6)
        self.password_entry = ttk.Entry(form, width=30, show="*")
        self.password_entry.grid(row=1, column=1, padx=6, pady=6)

        btn_frame = ttk.Frame(self, padding=8)
        btn_frame.pack(fill="x")

        ttk.Button(btn_frame, text="Entrar", command=self.login).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Sair", command=self.master.quit).pack(side="right", padx=6)

        # dica / espaço
        ttk.Label(self, text="(Use admin / 1234 se for a primeira execução)").pack(pady=6)

        # foco no campo usuário
        self.username_entry.focus_set()

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showwarning("Atenção", "Preencha usuário e senha.")
            return

        try:
            user = verificar_login(username, password)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao verificar login: {e}")
            return

        if user:
            display = user.get("display_name") or user.get("username") or username
            role = user.get("role", "operador")

            messagebox.showinfo("Bem-vindo", f"Olá, {display}!\nPerfil: {role}")

            # fecha a janela de login
            self.master.destroy()

            # abre o dashboard (arquivo ui/dashboard_ui.py)
            # usamos subprocess para manter o mesmo processo isolado, como você usou antes
            _sys.executable  # garante que a variável exista
            subprocess.Popen([_sys.executable, "ui/dashboard_ui.py", display, role])
        else:
            messagebox.showerror("Erro", "Usuário ou senha inválidos.")
