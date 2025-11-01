# ui/main_admin_ui.py

from ui.admin_users_ui import AdminUsersUI

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox


def open_user_manager(current_user):
    """Abre a janela de gerenciamento de usuários"""
    win = ttk.Toplevel()
    AdminUsersUI(win, current_user)

def open_admin_dashboard(user):
    root = ttk.Tk()
    root.title("Painel do Administrador - Açaiteria o Sabor da Fruta")
    root.geometry("400x300")

    ttk.Label(root, text=f"Bem-vindo, {user.display_name} (Admin)", font=("Arial", 12, "bold")).pack(pady=15)

    ttk.Button(root, text="Formulário de Vendas", width=25).pack(pady=5)
    ttk.Button(root, text="Controle de Ponto", width=25).pack(pady=5)
    ttk.Button(root, text="Gerenciar Produtos", width=25).pack(pady=5)

    # ⚙️ BOTÃO DE GERENCIAR USUÁRIOS — chama o método acima
    ttk.Button(root, text="Gerenciar Usuários", width=25,
              command=lambda: open_user_manager(user)).pack(pady=5)

    ttk.Button(root, text="Sair", width=25, command=root.destroy).pack(pady=20)

    root.mainloop()
