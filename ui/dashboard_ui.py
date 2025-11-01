import subprocess
import sys
import os
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox


class DashboardUI(ttk.Window):
    def __init__(self, display_name, role):
        super().__init__()
        self.title("Açaiteria o Sabor da Fruta - Painel Principal")
        self.geometry("600x400")
        self.display_name = display_name
        self.role = role

        self._build_ui()

    def _build_ui(self):
        # ====== Título superior ======
        header = ttk.Frame(self, padding=10)
        header.pack(fill=X)

        ttk.Label(
            header,
            text=f"Bem-vindo(a), {self.display_name}!",
            font=("Segoe UI", 14, "bold")
        ).pack(side=LEFT, padx=10)

        ttk.Label(
            header,
            text=f"Perfil: {self.role.capitalize()}",
            font=("Segoe UI", 11)
        ).pack(side=RIGHT, padx=10)

        # ====== Menu lateral ======
        menu_frame = ttk.Frame(self, bootstyle="secondary", padding=10)
        menu_frame.pack(side=LEFT, fill=Y)

        ttk.Label(menu_frame, text="Menu", font=("Segoe UI", 13, "bold")).pack(pady=10)

        # Opções comuns a todos
        ttk.Button(menu_frame, text="Vendas", bootstyle=SUCCESS, width=25, command=self.abrir_vendas).pack(pady=5)
        ttk.Button(menu_frame, text="Bater Ponto", bootstyle=INFO, width=25, command=self.bater_ponto).pack(pady=5)

        # Opções exclusivas do admin
        if self.role == "admin":
            ttk.Separator(menu_frame, orient=HORIZONTAL).pack(fill=X, pady=10)
            ttk.Button(menu_frame, text="Produtos", bootstyle=PRIMARY, width=25, command=self.abrir_produtos).pack(pady=5)
            ttk.Button(menu_frame, text="Relatórios", bootstyle=PRIMARY, width=25, command=self.abrir_relatorios).pack(pady=5)
            ttk.Button(menu_frame, text="Usuários", bootstyle=PRIMARY, width=25, command=self.abrir_usuarios).pack(pady=5)

        ttk.Separator(menu_frame, orient=HORIZONTAL).pack(fill=X, pady=10)
        ttk.Button(menu_frame, text="Sair do Sistema", bootstyle=DANGER, width=25, command=self.sair).pack(pady=10)

        # ====== Área principal (conteúdo dinâmico futuro) ======
        self.main_frame = ttk.Frame(self, padding=20)
        self.main_frame.pack(side=RIGHT, fill=BOTH, expand=True)

        ttk.Label(self.main_frame, text="Painel do Sistema", font=("Segoe UI", 15, "bold")).pack(pady=50)

    # ========================================================
    #               AÇÕES DOS BOTÕES
    # ========================================================
    def abrir_vendas(self):
        self.destroy()
        subprocess.Popen([sys.executable, "ui/vendas_ui.py", self.display_name, self.role])

    def abrir_produtos(self):
        self.destroy()
        subprocess.Popen([sys.executable, "ui/produtos_ui.py", self.display_name, self.role])

    def abrir_relatorios(self):
        messagebox.showinfo("Relatórios", "Módulo de relatórios em desenvolvimento.")

    def abrir_usuarios(self):
        self.destroy()
        subprocess.Popen([sys.executable, "ui/usuarios_ui.py", self.display_name, self.role])

    def bater_ponto(self):
        messagebox.showinfo("Ponto", f"Ponto registrado para {self.display_name}!")

    def sair(self):
        self.destroy()
        subprocess.Popen([sys.executable, "main.py"])


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        display_name = sys.argv[1]
        role = sys.argv[2]
    else:
        display_name = "Usuário"
        role = "operador"

    app = DashboardUI(display_name, role)
    app.mainloop()
