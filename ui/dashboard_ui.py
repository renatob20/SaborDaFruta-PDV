# ui/dashboard_ui.py
import sys
import os
import subprocess
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
import logging
import traceback

# Garante que os módulos sejam encontrados mesmo quando executados via subprocess
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))




# config básica de logging (stdout)
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")

class DashboardUI(ttk.Window):
    def __init__(self, display_name, role):
        super().__init__(themename="superhero")
        self.title("🍧 Açaiteria o Sabor da Fruta - Painel Principal")
        self.geometry("600x450")
        self.display_name = display_name
        self.role = role
        self.operador = display_name
        self.role = role

        self._build_ui()

    def _build_ui(self):
        ttk.Label(
            self,
            text=f"Bem-vindo(a), {self.display_name}!",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=10)
        ttk.Label(
            self,
            text=f"Perfil: {self.role.capitalize()}",
            font=("Segoe UI", 11)
        ).pack(pady=5)

        menu_frame = ttk.Frame(self, padding=10)
        menu_frame.pack(pady=15)

        # Opções comuns a todos
        ttk.Button(menu_frame, text="🛒 Vendas", width=25, bootstyle=SUCCESS,
                   command=self.abrir_vendas).pack(pady=5)
        ttk.Button(menu_frame, text="⏰ Bater Ponto", width=25, bootstyle=INFO,
                   command=self.bater_ponto).pack(pady=5)

        
        # Opções exclusivas do admin
        if self.role == "admin":
            ttk.Separator(menu_frame, orient="horizontal").pack(fill=X, pady=8)
            ttk.Button(menu_frame, text="📦 Produtos", width=25, bootstyle=PRIMARY,
                       command=self.abrir_produtos).pack(pady=5)
            ttk.Button(menu_frame, text="👤 Usuários", width=25, bootstyle=SECONDARY,
                       command=self.abrir_usuarios).pack(pady=5)
            ttk.Button(menu_frame, text="📈 Relatórios", width=25, bootstyle=WARNING,
                       command=self.abrir_relatorios).pack(pady=5)
            # --- Botão Estoque ---
            ttk.Button(menu_frame, text="📦 Estoque", width=25, bootstyle=SECONDARY,
                       command=self.abrir_estoque).pack(pady=5)


        ttk.Button(self, text="🚪 Sair", bootstyle=DANGER,
                   command=self.sair).pack(pady=25)

    # ==== AÇÕES DO MENU ====

    def abrir_vendas(self):
        """Abre o módulo de vendas como aplicação independente (subprocess)."""
        self.destroy()
        subprocess.Popen([sys.executable, "ui/vendas_ui.py",
                          self.display_name, self.role])

    def abrir_produtos(self):
        """Abre o módulo de produtos sem quebrar o contexto da janela."""
        self.destroy()
        subprocess.Popen([sys.executable, "ui/produtos_ui.py",
                          self.display_name, self.role])

    def abrir_usuarios(self):
        self.destroy()
        subprocess.Popen([sys.executable, "ui/usuarios_ui.py",
                          self.display_name, self.role])

    def abrir_relatorios(self):
        """Abre o módulo de relatórios sem quebrar o contexto da janela."""
        self.destroy()
        subprocess.Popen([sys.executable, "ui/relatorios_ui.py",
                          self.display_name, self.role])


    def bater_ponto(self):
        """Abre o módulo de bater ponto como janela independente (subprocess)."""
        try:
            subprocess.Popen([sys.executable, "ui/bater_ponto_ui.py", self.display_name, self.role])
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir Bater Ponto: {e}")


    def sair(self):
        self.destroy()
        subprocess.Popen([sys.executable, "main.py"])


    def abrir_estoque(self):
        """Abre o módulo de estoque sem quebrar o contexto da janela."""
        self.destroy()
        subprocess.Popen([sys.executable, "ui/estoque_ui.py",
                          self.display_name, self.role])



# Execução direta (para teste)
if __name__ == "__main__":
    if len(sys.argv) >= 3:
        display_name = sys.argv[1]
        role = sys.argv[2]
    else:
        display_name = "Usuário"
        role = "operador"

    app = DashboardUI(display_name, role)
    app.mainloop()
