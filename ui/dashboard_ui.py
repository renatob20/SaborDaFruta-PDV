# ui/dashboard_ui.py
import sys
import os
import subprocess
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

# Garante que os módulos sejam encontrados mesmo quando executados via subprocess
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importa a janela de Vendas para abrir como Toplevel no mesmo processo
try:
    from ui.vendas_ui import VendasUI
except Exception:
    # import no topo pode falhar em alguns cenários; faremos import local na função se necessário
    VendasUI = None

class DashboardUI(ttk.Window):
    def __init__(self, display_name, role):
        super().__init__(themename="superhero")
        self.title("🍧 Açaiteria o Sabor da Fruta - Painel Principal")
        self.geometry("600x450")
        self.display_name = display_name
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

        ttk.Button(self, text="🚪 Sair", bootstyle=DANGER,
                   command=self.sair).pack(pady=25)

    # ==== AÇÕES DO MENU ====

    def abrir_vendas(self):
        try:
            # importa localmente se necessário
            if VendasUI is None:
                from ui.vendas_ui import VendasUI

            # oculta o dashboard enquanto a janela de vendas estiver aberta
            self.withdraw()

            vendas_win = VendasUI(master=self, operador=self.display_name, role=self.role)
            vendas_win.transient(self)   # janela filha
            vendas_win.grab_set()        # concentra eventos na janela de vendas

            def _on_vendas_close():
                try:
                    vendas_win.grab_release()
                    vendas_win.destroy()
                finally:
                    self.deiconify()

            vendas_win.protocol("WM_DELETE_WINDOW", _on_vendas_close)
            # aguarda fechamento da janela filha sem criar outro mainloop
            self.wait_window(vendas_win)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir Vendas: {e}")
            # fallback: abrir como subprocess (menos recomendado)
            try:
                subprocess.Popen([sys.executable, "ui/vendas_ui.py", self.display_name, self.role])
                self.destroy()
            except Exception:
                pass

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
        try:
        # import local para evitar erro de import circular
            from ui.relatorios_ui import RelatoriosUI

        # Oculta o dashboard enquanto a janela estiver aberta
            self.withdraw()

            win = RelatoriosUI(operador=self.display_name, role=self.role)
            win.transient(self)  
            win.grab_set()

            def _on_close():
                try:
                    win.grab_release()
                    win.destroy()
                finally:
                    self.deiconify()

            win.protocol("WM_DELETE_WINDOW", _on_close)
            self.wait_window(win)

        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir Relatórios:\n{e}")


    def bater_ponto(self):
        messagebox.showinfo("Ponto", f"Ponto registrado para {self.display_name}!")

    def sair(self):
        self.destroy()
        subprocess.Popen([sys.executable, "main.py"])


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
