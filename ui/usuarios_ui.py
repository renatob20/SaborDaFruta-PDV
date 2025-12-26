# ui/usuarios_ui.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from controllers.usuario_controller import (
    cadastrar_usuario, 
    listar_todos_usuarios, 
    obter_usuario, 
    editar_usuario, 
    remover_usuario
)


class UsuariosUI(ttk.Frame):  # ✅ FRAME, não Window!
    """Tela de Usuários - Padrão produtos/vendas"""
    
    def __init__(self, master, display_name="Admin", role="admin"):
        super().__init__(master)  # ✅ PRIMEIRO
        self.master = master
        self.pack(fill=BOTH, expand=True)  # ✅ DEPOIS
        
        # Atributos
        self.display_name = display_name
        self.role = role
        
        # Maximiza janela
        try:
            self.master.state("zoomed")
        except:
            try:
                self.master.attributes("-zoomed", True)
            except:
                pass
        
        # Constrói UI
        self._build_ui()
        self.carregar_usuarios()

    def _build_ui(self):
        """Constrói interface"""
        
        # Container principal
        main_container = ttk.Frame(self)
        main_container.pack(fill=BOTH, expand=True, padx=15, pady=15)
        
        # ========== HEADER ==========
        header_frame = ttk.Frame(main_container, style="Dark.TFrame")
        header_frame.pack(fill=X, padx=0, pady=0)
        
        ttk.Label(
            header_frame, 
            text="👤 Cadastro de Usuários",
            font=("Segoe UI", 18, "bold"), 
            foreground="#FFFFFF"
        ).pack(pady=10)
        
        # Separador
        separator = ttk.Frame(header_frame, height=2, style="success.TFrame")
        separator.pack(fill=X, padx=50, pady=(0, 10))
        
               
        # ========== FORMULÁRIO ==========
        form = ttk.Labelframe(main_container, text="Dados do Usuário", padding=15)
        form.pack(fill=X, pady=(10, 0))
        
        # Labels
        ttk.Label(form, text="Nome completo:", font=("Segoe UI", 10)).grid(
            row=0, column=0, sticky=W, padx=5, pady=6
        )
        ttk.Label(form, text="CPF:", font=("Segoe UI", 10)).grid(
            row=1, column=0, sticky=W, padx=5, pady=6
        )
        ttk.Label(form, text="Celular:", font=("Segoe UI", 10)).grid(
            row=2, column=0, sticky=W, padx=5, pady=6
        )
        ttk.Label(form, text="Usuário (login):", font=("Segoe UI", 10)).grid(
            row=3, column=0, sticky=W, padx=5, pady=6
        )
        ttk.Label(form, text="Senha:", font=("Segoe UI", 10)).grid(
            row=4, column=0, sticky=W, padx=5, pady=6
        )
        ttk.Label(form, text="Função:", font=("Segoe UI", 10)).grid(
            row=5, column=0, sticky=W, padx=5, pady=6
        )

        # Campos
        self.nome_entry = ttk.Entry(form, width=45)
        self.cpf_entry = ttk.Entry(form, width=45)
        self.celular_entry = ttk.Entry(form, width=45)
        self.usuario_entry = ttk.Entry(form, width=45)
        self.senha_entry = ttk.Entry(form, width=45, show="*")
        self.role_combo = ttk.Combobox(form, values=["admin", "operador"], width=43)
        self.role_combo.set("operador")

        self.nome_entry.grid(row=0, column=1, padx=6, pady=6, sticky=W)
        self.cpf_entry.grid(row=1, column=1, padx=6, pady=6, sticky=W)
        self.celular_entry.grid(row=2, column=1, padx=6, pady=6, sticky=W)
        self.usuario_entry.grid(row=3, column=1, padx=6, pady=6, sticky=W)
        self.senha_entry.grid(row=4, column=1, padx=6, pady=6, sticky=W)
        self.role_combo.grid(row=5, column=1, padx=6, pady=6, sticky=W)

        # Máscaras automáticas
        self.cpf_entry.bind("<KeyRelease>", self._formatar_cpf)
        self.celular_entry.bind("<KeyRelease>", self._formatar_celular)

        # ========== BOTÕES ==========
        btn_frame = ttk.Frame(main_container)
        btn_frame.pack(fill=X, pady=10)
        
        ttk.Button(btn_frame, text="💾 Cadastrar / Salvar", bootstyle=SUCCESS,
                  command=self.salvar_usuario).pack(side=LEFT, padx=6)
        ttk.Button(btn_frame, text="🔄 Limpar", bootstyle=SECONDARY,
                  command=self.limpar_campos).pack(side=LEFT, padx=6)
        ttk.Button(btn_frame, text="🔙 Voltar ao Menu ", bootstyle=INFO,
                  command=self.voltar_menu).pack(side=RIGHT, padx=6)
            

        # ========== TABELA ==========
        table_frame = ttk.Labelframe(main_container, text="Usuários Cadastrados", padding=10)
        table_frame.pack(fill=BOTH, expand=True, pady=(10, 0))
        
        cols = ("id", "nome", "cpf", "celular", "usuario", "display", "role", "created_at")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", 
                                bootstyle="secondary", height=12)
        
        # Headings
        self.tree.heading("id", text="ID")
        self.tree.heading("nome", text="Nome completo")
        self.tree.heading("cpf", text="CPF")
        self.tree.heading("celular", text="Celular")
        self.tree.heading("usuario", text="Usuário")
        self.tree.heading("display", text="Display")
        self.tree.heading("role", text="Função")
        self.tree.heading("created_at", text="Criado em")
        
        # Columns
        self.tree.column("id", width=60, anchor="center")
        self.tree.column("nome", width=220)
        self.tree.column("cpf", width=120)
        self.tree.column("celular", width=120)
        self.tree.column("usuario", width=120)
        self.tree.column("display", width=150)
        self.tree.column("role", width=90, anchor="center")
        self.tree.column("created_at", width=150)

        self.tree.pack(fill=BOTH, expand=True, side=LEFT)
        
        # Scrollbar
        sb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        sb.pack(side=RIGHT, fill=Y)

        # ========== AÇÕES ==========
        action_frame = ttk.Frame(main_container)
        action_frame.pack(fill=X, pady=(10, 0))
        
        ttk.Button(action_frame, text="✏️ Editar Selecionado",
                  command=self.editar_selecionado).pack(side=LEFT, padx=6)
        ttk.Button(action_frame, text="🗑️ Excluir Selecionado", bootstyle=DANGER,
                  command=self.excluir_selecionado).pack(side=LEFT, padx=6)
        ttk.Button(action_frame, text="🔄 Atualizar Lista",
                  command=self.carregar_usuarios).pack(side=RIGHT, padx=6)

    # ========== MÁSCARAS ==========
    def _formatar_cpf(self, event=None):
        """Formata CPF: 000.000.000-00"""
        valor = re.sub(r'\D', '', self.cpf_entry.get())[:11]
       
        if len(valor) <= 3:
            formatado = valor
        elif len(valor) <= 6:
            formatado = f"{valor[:3]}.{valor[3:]}"
        elif len(valor) <= 9:
            formatado = f"{valor[:3]}.{valor[3:6]}.{valor[6:]}"
        else:
            formatado = f"{valor[:3]}.{valor[3:6]}.{valor[6:9]}-{valor[9:]}"

        self.cpf_entry.delete(0, "end")
        self.cpf_entry.insert(0, formatado)
        self.cpf_entry.icursor("end")

    def _formatar_celular(self, event=None):
        """Formata celular: (00) 00000-0000"""
        valor = re.sub(r'\D', '', self.celular_entry.get())[:11]

        if len(valor) <= 2:
            formatado = valor
        elif len(valor) <= 6:
            formatado = f"({valor[:2]}) {valor[2:]}"
        elif len(valor) <= 10:
            formatado = f"({valor[:2]}) {valor[2:6]}-{valor[6:]}"
        else:
            formatado = f"({valor[:2]}) {valor[2:7]}-{valor[7:]}"

        self.celular_entry.delete(0, "end")
        self.celular_entry.insert(0, formatado)
        self.celular_entry.icursor("end")

    # ========== AÇÕES ==========
    def salvar_usuario(self):
        """Salva usuário"""
        nome = self.nome_entry.get().strip()
        cpf = re.sub(r'\D', '', self.cpf_entry.get())
        celular = re.sub(r'\D', '', self.celular_entry.get())
        usuario = self.usuario_entry.get().strip()
        password = self.senha_entry.get().strip()
        role = self.role_combo.get().strip()

        # Validações
        if len(cpf) != 11:
            messagebox.showerror("CPF inválido", "O CPF deve conter 11 dígitos numéricos.")
            return
        if len(celular) != 11:
            messagebox.showerror("Celular inválido", "O celular deve conter DDD + 9 dígitos.")
            return

        try:
            success = cadastrar_usuario(nome, cpf, celular, usuario, password, role)
            if success:
                messagebox.showinfo("Sucesso", f"Usuário {usuario} cadastrado com sucesso.")
                self.limpar_campos()
                self.carregar_usuarios()
        except ValueError as e:
            messagebox.showerror("Erro ao cadastrar", str(e))
        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado: {e}")

    def carregar_usuarios(self):
        """Carrega usuários na tabela"""
        for r in self.tree.get_children():
            self.tree.delete(r)
        
        try:
            usuarios = listar_todos_usuarios()
            for u in usuarios:
                self.tree.insert("", "end", values=u)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar usuários: {e}")

    def limpar_campos(self):
        """Limpa formulário"""
        for entry in [self.nome_entry, self.cpf_entry, self.celular_entry, 
                     self.usuario_entry, self.senha_entry]:
            entry.delete(0, "end")
        self.role_combo.set("operador")

    def obter_id_selecionado(self):
        """Retorna ID do usuário selecionado"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Seleção", "Selecione um usuário na lista.")
            return None
        item = self.tree.item(sel[0])
        return item["values"][0]

    def editar_selecionado(self):
        """Edita usuário selecionado"""
        user_id = self.obter_id_selecionado()
        if not user_id:
            return
        
        user = obter_usuario(user_id)
        if not user:
            messagebox.showerror("Erro", "Usuário não encontrado.")
            return
        
        # TODO: Implementar janela de edição (Toplevel)
        messagebox.showinfo("Em desenvolvimento", 
                          "Funcionalidade de edição será implementada.")

    def excluir_selecionado(self):
        """Exclui usuário selecionado"""
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

    def voltar_menu(self):
        """Volta para dashboard - SEM subprocess"""
        self.destroy()
        from ui.dashboard_ui import DashboardUI
        DashboardUI(master=self.master, 
                    display_name=self.display_name, 
                    role=self.role)