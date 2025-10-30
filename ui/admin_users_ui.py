# ui/admin_users_ui.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from services.auth_service import create_user, list_users, get_user_by_id, update_user, delete_user

class UserForm(simpledialog.Dialog):
    def __init__(self, parent, title=None, user=None):
        self.user = user  # dicionário ou None
        super().__init__(parent, title=title)

    def body(self, master):
        tk.Label(master, text="Username:").grid(row=0, column=0, sticky='e')
        self.username_entry = tk.Entry(master)
        self.username_entry.grid(row=0, column=1)

        tk.Label(master, text="Senha:").grid(row=1, column=0, sticky='e')
        self.password_entry = tk.Entry(master, show="*")
        self.password_entry.grid(row=1, column=1)

        tk.Label(master, text="Nome (exibido):").grid(row=2, column=0, sticky='e')
        self.display_entry = tk.Entry(master)
        self.display_entry.grid(row=2, column=1)

        tk.Label(master, text="Perfil:").grid(row=3, column=0, sticky='e')
        self.role_combo = ttk.Combobox(master, values=["user", "admin"], state="readonly")
        self.role_combo.grid(row=3, column=1)

        if self.user:
            self.username_entry.insert(0, self.user.get("username", ""))
            self.display_entry.insert(0, self.user.get("display_name", ""))
            self.role_combo.set(self.user.get("role", "user"))
            # Em edição, senha em branco = mantém atual
        else:
            self.role_combo.set("user")

        return self.username_entry

    def apply(self):
        self.result = {
            "username": self.username_entry.get().strip(),
            "password": self.password_entry.get(),
            "display_name": self.display_entry.get().strip(),
            "role": self.role_combo.get()
        }

class AdminUsersUI:
    def __init__(self, master, current_user):
        self.master = master
        self.current_user = current_user
        master.title("Gerenciar Usuários - Admin")
        master.geometry("600x400")

        # Treeview
        cols = ("id", "username", "display_name", "role", "created_at")
        self.tree = ttk.Treeview(master, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
            self.tree.column(c, anchor="center")
        self.tree.pack(expand=True, fill="both", padx=10, pady=10)

        # Buttons
        btn_frame = tk.Frame(master)
        btn_frame.pack(fill="x", padx=10, pady=5)
        tk.Button(btn_frame, text="Novo Usuário", command=self.new_user).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Editar", command=self.edit_user).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Excluir", command=self.delete_user).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Atualizar Listagem", command=self.load_users).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Fechar", command=master.destroy).pack(side="right", padx=5)

        self.load_users()

    def load_users(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        users = list_users()
        for u in users:
            self.tree.insert("", "end", values=(u["id"], u["username"], u["display_name"] or "", u["role"], u["created_at"]))

    def new_user(self):
        form = UserForm(self.master, title="Criar Usuário")
        if hasattr(form, "result") and form.result:
            try:
                create_user(
                    username=form.result["username"],
                    password=form.result["password"],
                    display_name=form.result["display_name"],
                    role=form.result["role"]
                )
                messagebox.showinfo("Sucesso", "Usuário criado com sucesso.")
                self.load_users()
            except Exception as e:
                messagebox.showerror("Erro ao criar", str(e))

    def edit_user(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Seleção", "Selecione um usuário para editar.")
            return
        item = self.tree.item(sel[0])
        user_id = item["values"][0]
        user = get_user_by_id(user_id)
        if not user:
            messagebox.showerror("Erro", "Usuário não encontrado.")
            return
        form = UserForm(self.master, title="Editar Usuário", user=user)
        if hasattr(form, "result") and form.result:
            try:
                # se password em branco, update_user mantém a senha
                pw = form.result["password"]
                update_user(
                    user_id=user_id,
                    username=form.result["username"],
                    password=pw if pw != "" else None,
                    display_name=form.result["display_name"],
                    role=form.result["role"]
                )
                messagebox.showinfo("Sucesso", "Usuário atualizado.")
                self.load_users()
            except Exception as e:
                messagebox.showerror("Erro ao editar", str(e))

    def delete_user(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Seleção", "Selecione um usuário para excluir.")
            return
        item = self.tree.item(sel[0])
        user_id = item["values"][0]
        username = item["values"][1]
        if username == "admin":
            messagebox.showwarning("Proteção", "Não é permitido excluir o usuário 'admin' primário.")
            return
        if messagebox.askyesno("Confirmar", f"Confirma exclusão do usuário '{username}'?"):
            if delete_user(user_id):
                messagebox.showinfo("Removido", "Usuário excluído.")
                self.load_users()
            else:
                messagebox.showerror("Erro", "Falha ao excluir usuário.")
