import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from controllers.usuario_controller import criar_usuario


class UsuariosUI(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.pack(fill=BOTH, expand=True)
        self._build_ui()

    def _build_ui(self):
        ttk.Label(self, text="Cadastro de Usuário", font=("Segoe UI", 16, "bold")).pack(pady=10)

        form = ttk.Frame(self)
        form.pack(pady=10)

        ttk.Label(form, text="Nome completo:").grid(row=0, column=0, sticky=W, pady=5)
        self.nome_entry = ttk.Entry(form, width=40)
        self.nome_entry.grid(row=0, column=1, pady=5)

        ttk.Label(form, text="CPF:").grid(row=1, column=0, sticky=W, pady=5)
        self.cpf_entry = ttk.Entry(form, width=40)
        self.cpf_entry.grid(row=1, column=1, pady=5)

        ttk.Label(form, text="Celular:").grid(row=2, column=0, sticky=W, pady=5)
        self.celular_entry = ttk.Entry(form, width=40)
        self.celular_entry.grid(row=2, column=1, pady=5)

        ttk.Label(form, text="Usuário (login):").grid(row=3, column=0, sticky=W, pady=5)
        self.usuario_entry = ttk.Entry(form, width=40)
        self.usuario_entry.grid(row=3, column=1, pady=5)

        ttk.Label(form, text="Senha:").grid(row=4, column=0, sticky=W, pady=5)
        self.senha_entry = ttk.Entry(form, width=40, show="*")
        self.senha_entry.grid(row=4, column=1, pady=5)

        ttk.Button(self, text="Salvar Usuário", bootstyle=SUCCESS, command=self.salvar_usuario).pack(pady=15)

    def salvar_usuario(self):
        nome = self.nome_entry.get()
        cpf = self.cpf_entry.get()
        celular = self.celular_entry.get()
        usuario = self.usuario_entry.get()
        senha = self.senha_entry.get()

        if not nome or not cpf or not usuario or not senha:
            messagebox.showwarning("Atenção", "Preencha todos os campos obrigatórios!")
            return

        sucesso = criar_usuario(nome, cpf, celular, usuario, senha)
        if sucesso:
            messagebox.showinfo("Sucesso", f"Usuário {usuario} cadastrado com sucesso!")
            self.limpar_campos()
        else:
            messagebox.showerror("Erro", "Erro ao cadastrar usuário. Verifique se o login já existe.")

    def limpar_campos(self):
        for entry in [self.nome_entry, self.cpf_entry, self.celular_entry, self.usuario_entry, self.senha_entry]:
            entry.delete(0, ttk.END)
