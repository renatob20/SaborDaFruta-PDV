# ui/usuarios_ui.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from controllers.usuario_controller import cadastrar_usuario, listar_todos_usuarios, obter_usuario, editar_usuario, remover_usuario


class UsuariosUI(ttk.Window):
    def __init__(self, display_name=None, role="admin"):
        super().__init__(themename="superhero")
        
        # ---- Maximiza a Janela (Comportamento padrão para Windows) ----
        try:
            self.state("zoomed")
        except Exception:
            # Fallback para sistemas Windows onde 'zoomed' não está disponível
            # ou em casos muito específicos.
            self.attributes("-zoomed", True)
        
        self.title("👤 Gestão de Usuários")
        self.geometry("900x600")
        self.display_name = display_name
        self.role = role

        self._build_ui()
        self.carregar_usuarios()

    def _build_ui(self):
        header = ttk.Frame(self, padding=10)
        header.pack(fill=X)
        ttk.Label(header, text="Cadastro de Usuários", font=("Segoe UI", 16, "bold")).pack(side=LEFT)

        form = ttk.Frame(self, padding=12)
        form.pack(fill=X, padx=10, pady=6)

        ttk.Label(form, text="Nome completo:").grid(row=0, column=0, sticky=W, padx=5, pady=4)
        ttk.Label(form, text="CPF:").grid(row=1, column=0, sticky=W, padx=5, pady=4)
        ttk.Label(form, text="Celular:").grid(row=2, column=0, sticky=W, padx=5, pady=4)
        ttk.Label(form, text="Usuário (login):").grid(row=3, column=0, sticky=W, padx=5, pady=4)
        ttk.Label(form, text="Senha:").grid(row=4, column=0, sticky=W, padx=5, pady=4)
        ttk.Label(form, text="Função:").grid(row=5, column=0, sticky=W, padx=5, pady=4)

        self.nome_entry = ttk.Entry(form, width=40)
        self.cpf_entry = ttk.Entry(form, width=40)
        self.celular_entry = ttk.Entry(form, width=40)
        self.usuario_entry = ttk.Entry(form, width=40)
        self.senha_entry = ttk.Entry(form, width=40, show="*")
        self.role_combo = ttk.Combobox(form, values=["admin", "operador"], width=38)
        self.role_combo.set("operador")

        self.nome_entry.grid(row=0, column=1, padx=6, pady=4)
        self.cpf_entry.grid(row=1, column=1, padx=6, pady=4)
        self.celular_entry.grid(row=2, column=1, padx=6, pady=4)
        self.usuario_entry.grid(row=3, column=1, padx=6, pady=4)
        self.senha_entry.grid(row=4, column=1, padx=6, pady=4)
        self.role_combo.grid(row=5, column=1, padx=6, pady=4)

        # 🔹 Máscaras automáticas corrigidas (mantêm o cursor)
        self.cpf_entry.bind("<KeyRelease>", self._formatar_cpf)
        self.celular_entry.bind("<KeyRelease>", self._formatar_celular)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=X, padx=10, pady=8)
        ttk.Button(btn_frame, text="💾 Cadastrar / Salvar", bootstyle=SUCCESS, command=self.salvar_usuario).pack(side=LEFT, padx=6)
        ttk.Button(btn_frame, text="🔄 Limpar", bootstyle=SECONDARY, command=self.limpar_campos).pack(side=LEFT, padx=6)
        ttk.Button(btn_frame, text="⬅️ Voltar ao Menu", bootstyle=INFO, command=self.voltar_menu).pack(side=RIGHT, padx=6)

        cols = ("id", "nome", "cpf", "celular", "usuario", "display", "role", "created_at")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", bootstyle="secondary")
        self.tree.heading("id", text="ID"); self.tree.column("id", width=60, anchor="center")
        self.tree.heading("nome", text="Nome completo"); self.tree.column("nome", width=220)
        self.tree.heading("cpf", text="CPF"); self.tree.column("cpf", width=120)
        self.tree.heading("celular", text="Celular"); self.tree.column("celular", width=120)
        self.tree.heading("usuario", text="Usuário"); self.tree.column("usuario", width=120)
        self.tree.heading("display", text="Display"); self.tree.column("display", width=150)
        self.tree.heading("role", text="Função"); self.tree.column("role", width=90, anchor="center")
        self.tree.heading("created_at", text="Criado em"); self.tree.column("created_at", width=150)

        self.tree.pack(fill=BOTH, expand=True, padx=10, pady=8)

        action_frame = ttk.Frame(self)
        action_frame.pack(fill=X, padx=10, pady=6)
        ttk.Button(action_frame, text="✏️ Editar Selecionado", command=self.editar_selecionado).pack(side=LEFT, padx=6)
        ttk.Button(action_frame, text="🗑️ Excluir Selecionado", bootstyle=DANGER, command=self.excluir_selecionado).pack(side=LEFT, padx=6)
        ttk.Button(action_frame, text="🔄 Atualizar Lista", command=self.carregar_usuarios).pack(side=RIGHT, padx=6)

    # ✅ Correção e validação de CPF
    def _formatar_cpf(self, event=None):
        """
        Formata CPF como 000.000.000-00.
        Garante que o cursor fique sempre no final (à direita do último dígito).
        """
        # pega só dígitos e limita a 11
        valor = re.sub(r'\D', '', self.cpf_entry.get())[:11]
       
       # aplica mask
        if len(valor) <= 3:
            formatado = valor
        elif len(valor) <= 6:
            formatado = f"{valor[:3]}.{valor[3:]}"
        elif len(valor) <= 9:
            formatado = f"{valor[:3]}.{valor[3:6]}.{valor[6:]}"
        else:
            formatado = f"{valor[:3]}.{valor[3:6]}.{valor[6:9]}-{valor[9:]}"

        # atualiza campo e posiciona cursor no fim
        self.cpf_entry.delete(0, "end")
        self.cpf_entry.insert(0, formatado)
        self.cpf_entry.icursor("end")


    def _formatar_celular(self, event=None):
        """
        Formata celular brasileiro com DDD: (00) 00000-0000 ou (00) 0000-0000 conforme comprimento.
        Mantém cursor no final.
        """
        valor = re.sub(r'\D', '', self.celular_entry.get())[:11]  # máximo 11 (DDD+9)

        if len(valor) <= 2:
            formatado = valor
        elif len(valor) <= 6:
            formatado = f"({valor[:2]}) {valor[2:]}"
        elif len(valor) <= 10:
            # caso sem 9º dígito (ainda aceita): (dd) 0000-0000
            formatado = f"({valor[:2]}) {valor[2:6]}-{valor[6:]}"
        else:
            # 11 dígitos (DDD + 9 dígitos): (dd) 00000-0000
            formatado = f"({valor[:2]}) {valor[2:7]}-{valor[7:]}"

        self.celular_entry.delete(0, "end")
        self.celular_entry.insert(0, formatado)
        self.celular_entry.icursor("end")

    # ✅ Validação antes de salvar
    def salvar_usuario(self):
        nome = self.nome_entry.get().strip()
        cpf = re.sub(r'\D', '', self.cpf_entry.get())
        celular = re.sub(r'\D', '', self.celular_entry.get())
        usuario = self.usuario_entry.get().strip()
        senha = self.senha_entry.get().strip()
        role = self.role_combo.get().strip()

        # 🔹 Validações automáticas
        if len(cpf) != 11:
            messagebox.showerror("CPF inválido", "O CPF deve conter 11 dígitos numéricos.")
            return
        if len(celular) != 11:
            messagebox.showerror("Celular inválido", "O celular deve conter DDD + 9 dígitos (ex: 11987654321).")
            return

        try:
            success = cadastrar_usuario(nome, cpf, celular, usuario, senha, role)
            if success:
                messagebox.showinfo("Sucesso", f"Usuário {usuario} cadastrado com sucesso.")
                self.limpar_campos()
                self.carregar_usuarios()
        except ValueError as e:
            messagebox.showerror("Erro ao cadastrar", str(e))
        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado: {e}")

    def carregar_usuarios(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        try:
            usuarios = listar_todos_usuarios()
            for u in usuarios:
                self.tree.insert("", "end", values=u)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar usuários: {e}")

    def limpar_campos(self):
        for entry in [self.nome_entry, self.cpf_entry, self.celular_entry, self.usuario_entry, self.senha_entry]:
            entry.delete(0, "end")
        self.role_combo.set("operador")

    def voltar_menu(self):
        import subprocess, sys
        self.destroy()
        subprocess.Popen([sys.executable, "ui/dashboard_ui.py", self.display_name or "Admin", self.role or "admin"])

    def obter_id_selecionado(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Seleção", "Selecione um usuário na lista.")
            return None
        item = self.tree.item(sel[0])
        return item["values"][0]

    def editar_selecionado(self):
        user_id = self.obter_id_selecionado()
        if not user_id:
            return
        user = obter_usuario(user_id)
        if not user:
            messagebox.showerror("Erro", "Usuário não encontrado.")
            return
        EditUserDialog(self, user, self._on_edit_saved)

    def _on_edit_saved(self, updated):
        if updated:
            self.carregar_usuarios()

    def excluir_selecionado(self):
        user_id = self.obter_id_selecionado()
        if not user_id:
            return
        if messagebox.askyesno("Confirmar", "Deseja excluir o usuário selecionado?"):
            try:
                ok = remover_usuario(user_id)
                if ok:
                    messagebox.showinfo("Removido", "Usuário excluído com sucesso.")
                    self.carregar_usuarios()
                else:
                    messagebox.showerror("Erro", "Falha ao excluir usuário.")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao excluir: {e}")


# A janela de edição pode manter o comportamento anterior
class EditUserDialog(ttk.Toplevel):
    pass


if __name__ == "__main__":
    app = UsuariosUI("Admin", "admin")
    app.mainloop()
