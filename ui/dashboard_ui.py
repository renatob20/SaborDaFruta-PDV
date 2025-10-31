import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os

class DashboardUI(tk.Tk):
    def __init__(self, display_name, role):
        super().__init__()
        self.title("Açaiteria o Sabor da Fruta - Painel Principal")
        self.geometry("500x400")
        self.display_name = display_name
        self.role = role

        self._build_ui()

    def _build_ui(self):
        tk.Label(self, text=f"Bem-vindo(a), {self.display_name}!", font=("Arial", 14, "bold")).pack(pady=10)
        tk.Label(self, text=f"Perfil: {self.role.capitalize()}", font=("Arial", 11)).pack(pady=5)

        frame = tk.Frame(self)
        frame.pack(pady=20)

        # Opções visíveis para todos
        tk.Button(frame, text="Vendas", width=25, command=self.abrir_vendas).pack(pady=5)
        tk.Button(frame, text="Bater Ponto", width=25, command=self.bater_ponto).pack(pady=5)

        # Opções exclusivas do admin
        if self.role == "admin":
            tk.Button(frame, text="Produtos", width=25, command=self.abrir_produtos).pack(pady=5)
            tk.Button(frame, text="Relatórios", width=25, command=self.abrir_relatorios).pack(pady=5)
            tk.Button(frame, text="Usuários", width=25, command=self.abrir_usuarios).pack(pady=5)

        tk.Button(self, text="Sair", command=self.sair).pack(pady=20)

    def abrir_vendas(self):
        self.destroy()
        subprocess.Popen([sys.executable, "ui/vendas_ui.py", self.display_name, self.role])

    def abrir_produtos(self):
        self.destroy()
        subprocess.Popen([sys.executable, "ui/produtos_ui.py", self.display_name, self.role])

    def abrir_relatorios(self):
        messagebox.showinfo("Relatórios", "Módulo de relatórios em desenvolvimento.")

    def abrir_usuarios(self):
        messagebox.showinfo("Usuários", "Módulo de usuários em desenvolvimento.")

    def bater_ponto(self):
        messagebox.showinfo("Ponto", f"Ponto registrado para {self.display_name}!")

    def sair(self):
        self.destroy()
        messagebox.showinfo("Logout", "Você saiu do sistema.")
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
