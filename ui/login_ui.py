import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
from models.user_model import authenticate  # <---- corrigido aqui

class LoginUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Açaiteria o Sabor da Fruta - Login")
        self.root.geometry("350x200")
        self.root.resizable(False, False)

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()

        tk.Label(root, text="Usuário:").pack(pady=5)
        tk.Entry(root, textvariable=self.username_var).pack()

        tk.Label(root, text="Senha:").pack(pady=5)
        tk.Entry(root, textvariable=self.password_var, show="*").pack()

        tk.Button(root, text="Entrar", command=self.login).pack(pady=15)

    def login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        if not username or not password:
            messagebox.showwarning("Atenção", "Por favor, preencha usuário e senha.")
            return

        user = authenticate(username, password)

        if user:
            nome_usuario = user["display_name"]
            role = user["role"]

            messagebox.showinfo("Bem-vindo", f"Olá, {nome_usuario}!\nPerfil: {role}")

            # Fecha a tela de login
            self.root.destroy()

            # Abre a aplicação principal (PySide6)
            subprocess.Popen([sys.executable, "app.py", nome_usuario, role])
        else:
            messagebox.showerror("Erro", "Usuário ou senha inválidos.")
