
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

def open_user_dashboard(user):
    root = ttk.Tk()
    root.title("Painel do Usuário - Açaiteria o Sabor da Fruta")
    root.geometry("400x200")

    ttk.Label(root, text=f"Bem-vindo, {user.display_name}", font=("Arial", 12, "bold")).pack(pady=10)

    ttk.Button(root, text="Formulário de Vendas", width=25).pack(pady=5)
    ttk.Button(root, text="Bater Ponto", width=25).pack(pady=5)
    ttk.Button(root, text="Sair", width=25, command=root.destroy).pack(pady=20)

    root.mainloop()
