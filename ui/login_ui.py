# ui/login_ui.py
import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
from controllers.login_controller import verificar_login

class LoginUI(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("Açaiteria o Sabor da Fruta - Login")
        self.master.geometry("350x200")
        self.pack(fill="both", expand=True)
        self._build_ui()

    def _build_ui(self):
        tk.Label(self, text="Usuário:").pack(pady=5)
        self.username_entry = tk.Entry(self)
        self.username_entry.pack()

        tk.Label(self, text="Senha:").pack(pady=5)
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack()

        tk.Button(self, text="Entrar", command=self.login).pack(pady=15)

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showwarning("Atenção", "Por favor, preencha usuário e senha.")
            return

        user = verificar_login(username, password)

        if user:
            display = user.get("display_name") or user.get("username") or username
            role = user.get("role", "operador")

            messagebox.showinfo("Bem-vindo", f"Olá, {display}!\nPerfil: {role}")

            # Fecha login
            self.master.destroy()

            # Abre a aplicação principal (PySide6)
            subprocess.Popen([sys.executable, "ui/dashboard_ui.py", display, role])
        else:
            messagebox.showerror("Erro", "Usuário ou senha inválidos.")
