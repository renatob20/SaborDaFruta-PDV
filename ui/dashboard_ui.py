# ui/dashboard_ui.py
import sys, os
import subprocess
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

# Garante que o Python encontre os módulos do projeto
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Import seguro do módulo de ponto
try:
    from ui.bater_ponto_ui import BaterPontoUI
except Exception:
    BaterPontoUI = None

# Import seguro do módulo de vendas
try:
    from ui.vendas_ui import VendasUI
except Exception:
    VendasUI = None

class DashboardUI(ttk.Window):
    def __init__(self, display_name, role):
        super().__init__(themename="superhero")

        self.title("🍧 Açaiteria o Sabor da Fruta - Dashboard")
        self.geometry("600x450")
        self.minsize(600, 450)

        self.display_name = display_name
        self.role = role
        self.operador = display_name

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
        ).pack()

        menu_frame = ttk.Frame(self, padding=10)
        menu_frame.pack(pady=20)

        # ---------- BOTÕES COMUNS ----------
        
        ttk.Button(
            menu_frame,
            text="🛒 Vendas",
            width=25,
            bootstyle=SUCCESS,
            command=self.abrir_vendas
        ).pack(pady=5)

        ttk.Button(
            menu_frame,
            text="⏰ Bater Ponto",
            width=25,
            bootstyle=INFO,
            command=self.abrir_bater_ponto
        ).pack(pady=5)

        # ---------- BOTÕES DO ADMIN ----------
        if self.role == "admin":
            ttk.Separator(menu_frame, orient="horizontal").pack(fill=X, pady=10)

            ttk.Button(
                menu_frame,
                text="📦 Produtos",
                width=25,
                bootstyle=PRIMARY,
                command=self.abrir_produtos
            ).pack(pady=5)

            ttk.Button(
                menu_frame,
                text="👤 Usuários",
                width=25,
                bootstyle=SECONDARY,
                command=self.abrir_usuarios
            ).pack(pady=5)

            ttk.Button(
                menu_frame,
                text="📈 Relatórios",
                width=25,
                bootstyle=WARNING,
                command=self.abrir_relatorios
            ).pack(pady=5)

            ttk.Button(
                menu_frame,
                text="📦 Estoque",
                width=25,
                bootstyle=INFO,
                command=self.abrir_estoque
            ).pack(pady=5)

        # ---------- SAIR ----------
        ttk.Button(
            self,
            text="🚪 Sair",
            bootstyle=DANGER,
            command=self.sair
        ).pack(pady=20)

    def abrir_vendas(self):
        try:
            if VendasUI is None:
                from ui.vendas_ui import VendasUI

            self.withdraw()

            janela = VendasUI(master=self, operador=self.display_name, role=self.role)

            janela.transient(self)
            janela.grab_set()

            def fechar():
                janela.grab_release()
                janela.destroy()
                self.deiconify()

            janela.protocol("WM_DELETE_WINDOW", fechar)

            self.wait_window(janela)

        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir Vendas:\n{e}")

    def abrir_bater_ponto(self):

        """Abre a tela de Bater Ponto como janela filha corretamente (sem criar mainloop extra)."""
        try:
            # import local para evitar import circular em tempo de import do módulo
            from ui.bater_ponto_ui import BaterPontoUI

        # esconde dashboard e abre janela filha
            self.withdraw()
            janela = BaterPontoUI(master=self, operador_display=self.display_name, role=self.role)
            janela.transient(self)
            janela.grab_set()

            def _on_close():
                try:
                    janela.grab_release()
                    janela.destroy()
                finally:
                    self.deiconify()

            janela.protocol("WM_DELETE_WINDOW", _on_close)
            # aguarda fechamento sem criar novo mainloop
            self.wait_window(janela)

        except Exception as e:
            # fallback: exibe erro e tenta abrir em subprocess (compat)
            messagebox.showerror("Erro", f"Não foi possível abrir o módulo de Ponto:\n{e}")
        try:
            import subprocess
            subprocess.Popen([sys.executable, "ui/bater_ponto_ui.py", self.display_name, self.role])
            self.destroy()
        except Exception:
            pass

    def abrir_produtos(self):
        self.destroy()
        subprocess.Popen([sys.executable, "ui/produtos_ui.py", self.display_name, self.role])

    def abrir_usuarios(self):
        self.destroy()
        subprocess.Popen([sys.executable, "ui/usuarios_ui.py", self.display_name, self.role])

    def abrir_relatorios(self):
        try:
            from ui.relatorios_ui import RelatoriosUI

            self.withdraw()

            janela = RelatoriosUI(operador=self.display_name, role=self.role)

            janela.transient(self)
            janela.grab_set()

            def fechar():
                janela.grab_release()
                janela.destroy()
                self.deiconify()

            janela.protocol("WM_DELETE_WINDOW", fechar)
            self.wait_window(janela)

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao abrir Relatórios:\n{e}")

    def abrir_estoque(self):
        try:
            from ui.estoque_ui import EstoqueUI

            self.withdraw()

            janela = EstoqueUI(master=self, operador=self.display_name, role=self.role)

            janela.transient(self)
            janela.grab_set()

            def voltar():
                janela.grab_release()
                janela.destroy()
                self.deiconify()

            janela.protocol("WM_DELETE_WINDOW", voltar)
            self.wait_window(janela)

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir Estoque:\n{e}")

    def sair(self):
        self.destroy()
        subprocess.Popen([sys.executable, "main.py"])


# Execução direta
if __name__ == "__main__":

    if len(sys.argv) >= 3:
        nome = sys.argv[1]
        role = sys.argv[2]
    else:
        nome = "Usuário"
        role = "operador"

    app = DashboardUI(nome, role)
    app.mainloop()

