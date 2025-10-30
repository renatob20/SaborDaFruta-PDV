# ui/main_admin_ui.py
import tkinter as tk
from ui.admin_users_ui import AdminUsersUI

def open_user_manager(current_user):
    """Abre a janela de gerenciamento de usuários"""
    win = tk.Toplevel()
    AdminUsersUI(win, current_user)

def open_admin_dashboard(user):
    root = tk.Tk()
    root.title("Painel do Administrador - Açaiteria o Sabor da Fruta")
    root.geometry("400x300")

    tk.Label(root, text=f"Bem-vindo, {user.display_name} (Admin)", font=("Arial", 12, "bold")).pack(pady=15)

    tk.Button(root, text="Formulário de Vendas", width=25).pack(pady=5)
    tk.Button(root, text="Controle de Ponto", width=25).pack(pady=5)
    tk.Button(root, text="Gerenciar Produtos", width=25).pack(pady=5)

    # ⚙️ BOTÃO DE GERENCIAR USUÁRIOS — chama o método acima
    tk.Button(root, text="Gerenciar Usuários", width=25,
              command=lambda: open_user_manager(user)).pack(pady=5)

    tk.Button(root, text="Sair", width=25, command=root.destroy).pack(pady=20)

    root.mainloop()
