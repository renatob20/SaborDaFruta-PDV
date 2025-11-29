# ui/dashboard_ui.py  — PARTE A
import sys
import os
import subprocess
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

# garante que imports relativos funcionem quando executado diretamente
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

"""
DashboardUI - versão unificada e segura.

Principais mudanças:
- Usa import "late-bound" (dinâmico) para evitar import circular.
- Não passa 'master' automaticamente para as UIs filhas (evita erro de assinatura).
- Usa _open_child_window(import_path, class_name, **kwargs) para abrir telas filhas.
- Quando possível abre a UI no mesmo processo (sem criar novo mainloop) usando wait_window.
- Se houver erro, exibe messagebox e tenta fallback por subprocess (compatibilidade).
"""

# ui/dashboard_ui.py  — PARTE B

class DashboardUI(ttk.Window):
    def __init__(self, display_name="Usuário", role="operador"):
        super().__init__(themename="superhero")
        self.title("🍧 Açaiteria o Sabor da Fruta - Painel Principal")
        self.geometry("600x460")
        self.minsize(560, 420)

        # dados vindos do login
        self.display_name = display_name
        self.role = role
        self.operador = display_name  # compatibilidade com telas filhas que usam .operador

        self._build_ui()

    def _build_ui(self):
        # header
        header = ttk.Frame(self, padding=12)
        header.pack(fill="x")
        ttk.Label(header, text=f"Bem-vindo(a), {self.display_name}!", font=("Segoe UI", 16, "bold")).pack(pady=(4,2))
        ttk.Label(header, text=f"Perfil: {self.role.capitalize()}", font=("Segoe UI", 11)).pack()

        # menu central
        menu_frame = ttk.Frame(self, padding=12)
        menu_frame.pack(pady=16)

        # Botões principais (sempre usar import local nas funções para evitar ciclos)
        ttk.Button(menu_frame, text="🛒 Vendas", width=25, bootstyle=SUCCESS, command=self.abrir_vendas).pack(pady=6)
        ttk.Button(menu_frame, text="⏰ Bater Ponto", width=25, bootstyle=INFO, command=self.abrir_bater_ponto).pack(pady=6)
        ttk.Button(menu_frame, text="📦 Estoque", width=25, bootstyle=SECONDARY, command=self.abrir_estoque).pack(pady=6)

        # separador e opções admin
        if self.role == "admin":
            ttk.Separator(menu_frame, orient="horizontal").pack(fill="x", pady=10)
            ttk.Button(menu_frame, text="📦 Produtos", width=25, bootstyle=PRIMARY, command=self.abrir_produtos).pack(pady=6)
            ttk.Button(menu_frame, text="👤 Usuários", width=25, bootstyle=SECONDARY, command=self.abrir_usuarios).pack(pady=6)
            ttk.Button(menu_frame, text="📈 Relatórios", width=25, bootstyle=WARNING, command=self.abrir_relatorios).pack(pady=6)

        # sair
        ttk.Button(self, text="🚪 Sair", bootstyle=DANGER, command=self.sair).pack(pady=20)

    # utilitário: abrir janela com padrão seguro (filha no mesmo processo)
    def _open_child_window(self, import_path: str, class_name: str, *args, **kwargs) -> bool:
        """
        Importa dinamicamente a UI filha e a abre como janela filha (sem criar mainloop extra).
        - import_path: e.g. "ui.vendas_ui"
        - class_name: e.g. "VendasUI"
        - kwargs: passamos apenas argumentos simples (operador, role, etc).
        Retorna True se abriu com sucesso, False caso contrário.
        """
        try:
            module = __import__(import_path, fromlist=[class_name])
            cls = getattr(module, class_name)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível carregar {class_name}:\n{e}")
            return False

        try:
            # Cria instância da janela filha. Evitamos passar 'master' por padrão:
            # muitos módulos esperam apenas (operador, role) e deram erro quando recebiam master.
            win = cls(*args, **kwargs)
        except TypeError as e:
            # Tentativa alternativa: algumas UIs aceitam master como primeiro arg.
            try:
                win = cls(master=self, *args, **kwargs)
            except Exception as e2:
                messagebox.showerror("Erro", f"Falha ao criar {class_name}:\n{e}\n{e2}")
                return False
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao criar {class_name}:\n{e}")
            return False

        # Se a janela filha for um ttk.Window (novo root), marcamos transient() e wait_window.
        try:
            # tenta definir filho/parent relationship de forma segura
            try:
                win.transient(self)
            except Exception:
                pass
            try:
                win.grab_set()
            except Exception:
                pass

            def _on_child_close():
                try:
                    win.grab_release()
                except Exception:
                    pass
                try:
                    win.destroy()
                finally:
                    try:
                        self.deiconify()
                    except Exception:
                        pass

            win.protocol("WM_DELETE_WINDOW", _on_child_close)

            # opcional: oculta o dashboard enquanto a janela filha estiver aberta
            try:
                self.withdraw()
            except Exception:
                pass

            # Espera a janela fechar (sem criar novo mainloop)
            try:
                self.wait_window(win)
            except Exception:
                # se wait_window falhar (porwin não ser um widget tkinter), só retorna.
                pass
            return True
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao abrir a janela {class_name}:\n{e}")
            return False

    # ação sair
    def sair(self):
        try:
            subprocess.Popen([sys.executable, "main.py"])
        except Exception:
            pass
        finally:
            try:
                self.destroy()
            except Exception:
                pass

# ui/dashboard_ui.py  — PARTE C

    # ==== AÇÕES DO MENU - wrappers que usam _open_child_window ==== #

    def abrir_vendas(self):
        # abre a tela de vendas (passa operador e role)
        self._open_child_window("ui.vendas_ui", "VendasUI", operador=self.display_name, role=self.role)

    def abrir_bater_ponto(self):
        # abre a tela Bater Ponto (nova UI)
        self._open_child_window("ui.bater_ponto_ui", "BaterPontoUI", operador_display=self.display_name, role=self.role)

    def abrir_estoque(self):
        self._open_child_window("ui.estoque_ui", "EstoqueUI", operador=self.display_name, role=self.role)

    def abrir_produtos(self):
        self._open_child_window("ui.produtos_ui", "ProdutosUI", operador=self.display_name, role=self.role)

    def abrir_usuarios(self):
        self._open_child_window("ui.usuarios_ui", "UsuariosUI", operador=self.display_name, role=self.role)

    def abrir_relatorios(self):
        self._open_child_window("ui.relatorios_ui", "RelatoriosUI", operador=self.display_name, role=self.role)


# Execução direta (para teste)
if __name__ == "__main__":
    if len(sys.argv) >= 3:
        display_name = sys.argv[1]
        role = sys.argv[2]
    else:
        display_name = "Usuario"
        role = "operador"

    app = DashboardUI(display_name, role)
    app.mainloop()
