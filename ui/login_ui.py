# ui/login_ui.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

from controllers.login_controller import verificar_login

class LoginUI(ttk.Frame):
    """Frame de login - Navegação sem subprocess"""
    
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack(fill="both", expand=True)
        self._build_ui()

    def _build_ui(self):
        # Cabeçalho
        header = ttk.Frame(self, padding=12)
        header.pack(fill="x")
        ttk.Label(header, text="Açaiteria - Acessar Sistema", 
                 font=("Segoe UI", 12, "bold")).pack()

        # Formulário
        form = ttk.Frame(self, padding=12)
        form.pack(fill="x", pady=6)

        ttk.Label(form, text="Usuário:").grid(row=0, column=0, sticky="w", pady=6)
        ttk.Label(form, text="Senha:").grid(row=1, column=0, sticky="w", pady=6)

        self.username_entry = ttk.Entry(form, width=30)
        self.username_entry.grid(row=0, column=1, padx=6, pady=6)
        
        self.password_entry = ttk.Entry(form, width=30, show="*")
        self.password_entry.grid(row=1, column=1, padx=6, pady=6)

        # Bind Enter
        self.password_entry.bind('<Return>', lambda e: self.login())

        # Botões
        btn_frame = ttk.Frame(self, padding=8)
        btn_frame.pack(fill="x")

        ttk.Button(btn_frame, text="Entrar", 
                  command=self.login).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Sair", 
                  command=self.master.quit).pack(side="right", padx=6)

        # Dica
        ttk.Label(self, text="(Use admin / 1234 se for a primeira execução)", 
                 font=("Segoe UI", 8)).pack(pady=6)

        # Foco no usuário
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

            # ✅ NAVEGAÇÃO CORRETA - Sem subprocess
            self.destroy()
            from ui.dashboard_ui import DashboardUI
            DashboardUI(master=self.master, display_name=display, role=role)
        else:
            messagebox.showerror("Erro", "Usuário ou senha inválidos.")