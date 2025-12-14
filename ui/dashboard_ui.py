# ui/dashboard_ui.py
import sys
import os
import subprocess
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
import logging
import traceback
from PIL import Image, ImageTk

# Garante que os módulos sejam encontrados mesmo quando executados via subprocess
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# config básica de logging (stdout)
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")

class DashboardUI(ttk.Window):
    def __init__(self, display_name, role):
        super().__init__(themename="superhero")
        
        # ---- Maximiza a Janela ----
        try:
            self.state("zoomed")
        except Exception:
            self.attributes("-zoomed", True)
        
        self.title("🍧 Açaiteria o Sabor da Fruta - Sistema PDV")
        self.geometry("800x600")
        self.display_name = display_name
        self.role = role
        self.operador = display_name
        
        # ========== CARREGAR ÍCONE DA JANELA ==========
        self._set_window_icon()
        
        # ========== CARREGAR IMAGENS ==========
        self.logo_img = None
        self.acai_bg = None
        self._load_images()
        
        self._build_ui()

    def _set_window_icon(self):
        """Define o ícone da janela (APENAS no dashboard)."""
        try:
            icon_path = os.path.join("assets", "icons", "app.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
                logging.info(f"✅ Ícone carregado: {icon_path}")
        except Exception as e:
            # Falha silenciosa - não é crítico
            logging.debug(f"Ícone não carregado: {e}")

    def _load_images(self):
        """Carrega as imagens do sistema."""
        try:
            # ========== LOGO HEADER (BANNER HORIZONTAL) ==========
            # Imagem: 1600x280 - banner horizontal com logo da açaiteria
            logo_path = os.path.join("assets", "imagens", "acai-banner02.png")
            if os.path.exists(logo_path):
                logo_original = Image.open(logo_path)
                # Redimensionar para caber no header (largura máxima 800px, altura 140px)
                logo_resized = logo_original.resize((800, 140), Image.Resampling.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(logo_resized)
                logging.info(f"✅ Banner carregado: {logo_path}")
            else:
                # Sem aviso - usa fallback silenciosamente
                self.logo_img = None
                logging.debug(f"Banner não encontrado, usando fallback de texto")
            
        except Exception as e:
            logging.error(f"❌ Erro ao carregar imagens: {e}")
            self.logo_img = None
            traceback.print_exc()

    def _build_ui(self):
        # ========== CONTAINER PRINCIPAL ==========
        main_container = ttk.Frame(self)
        main_container.pack(fill=BOTH, expand=True)
        
        # ========== HEADER COM BANNER (SEM DIVISÃO) ==========
        header_frame = ttk.Frame(main_container, style="Dark.TFrame")
        header_frame.pack(fill=X, padx=0, pady=0)
        
        # ========== BANNER HORIZONTAL ==========
        if self.logo_img:
            # Banner horizontal centralizado
            banner_label = ttk.Label(header_frame, image=self.logo_img)
            banner_label.pack(pady=10)
        else:
            # Fallback: Texto estilizado
            ttk.Label(
                header_frame,
                text="🍧 Açaiteria o Sabor da Fruta",
                font=("Segoe UI", 28, "bold"),
                foreground="#FFFFFF"
            ).pack(pady=20)
        
        # ========== LINHA DECORATIVA (OPCIONAL) ==========
        separator = ttk.Frame(header_frame, height=2, style="success.TFrame")
        separator.pack(fill=X, padx=50, pady=(0, 10))
        
        # ========== USUÁRIO LOGADO ==========
        user_frame = ttk.Frame(main_container)
        user_frame.pack(pady=15)
        
        ttk.Label(
            user_frame,
            text=f"👤 {self.display_name}",
            font=("Segoe UI", 14, "bold"),
            foreground="#4ECDC4"
        ).pack()
        
        # Badge do perfil
        badge_color = "#FF6B6B" if self.role == "admin" else "#95E1D3"
        badge_text = "🔑 Administrador" if self.role == "admin" else "👨‍💼 Operador"
        
        badge_label = ttk.Label(
            user_frame,
            text=badge_text,
            font=("Segoe UI", 10),
            foreground=badge_color
        )
        badge_label.pack(pady=3)
        
        # ========== MENU DE NAVEGAÇÃO ==========
        menu_container = ttk.Frame(main_container)
        menu_container.pack(pady=10, padx=40, fill=BOTH, expand=True)
        
        # Grid com 2 colunas
        menu_container.columnconfigure(0, weight=1)
        menu_container.columnconfigure(1, weight=1)
        
        # ========== BOTÕES PRINCIPAIS (TODOS OS USUÁRIOS) ==========
        row = 0
        
        # Vendas - Destaque especial
        btn_vendas = ttk.Button(
            menu_container,
            text="🛒  Realizar Venda",
            bootstyle="success",
            command=self.abrir_vendas,
            width=30
        )
        btn_vendas.grid(row=row, column=0, columnspan=2, pady=8, padx=5, sticky="ew")
        btn_vendas.configure(cursor="hand2")
        
        row += 1
        
        # Bater Ponto
        btn_ponto = ttk.Button(
            menu_container,
            text="⏰  Registrar Ponto",
            bootstyle="info",
            command=self.bater_ponto,
            width=28
        )
        btn_ponto.grid(row=row, column=0, columnspan=2, pady=5, padx=5, sticky="ew")
        btn_ponto.configure(cursor="hand2")
        
        # ========== ÁREA ADMINISTRATIVA ==========
        if self.role == "admin":
            row += 1
            
            # Separador visual
            ttk.Separator(menu_container, orient="horizontal").grid(
                row=row, column=0, columnspan=2, pady=15, sticky="ew"
            )
            
            row += 1
            
            ttk.Label(
                menu_container,
                text="🔐 ÁREA ADMINISTRATIVA",
                font=("Segoe UI", 11, "bold"),
                foreground="#FFD93D"
            ).grid(row=row, column=0, columnspan=2, pady=(0, 10))
            
            row += 1
            
            # Linha 1: Produtos e Estoque
            btn_produtos = ttk.Button(
                menu_container,
                text="📦  Produtos",
                bootstyle="primary-outline",
                command=self.abrir_produtos,
                width=28
            )
            btn_produtos.grid(row=row, column=0, pady=5, padx=5, sticky="ew")
            btn_produtos.configure(cursor="hand2")
            
            btn_estoque = ttk.Button(
                menu_container,
                text="📊  Estoque",
                bootstyle="primary-outline",
                command=self.abrir_estoque,
                width=28
            )
            btn_estoque.grid(row=row, column=1, pady=5, padx=5, sticky="ew")
            btn_estoque.configure(cursor="hand2")
            
            row += 1
            
            # Linha 2: Usuários e Relatórios (MESMA COR AMARELA)
            btn_usuarios = ttk.Button(
                menu_container,
                text="👥  Usuários",
                bootstyle="warning-outline",  # ALTERADO: mesmo estilo do Relatórios
                command=self.abrir_usuarios,
                width=28
            )
            btn_usuarios.grid(row=row, column=0, pady=5, padx=5, sticky="ew")
            btn_usuarios.configure(cursor="hand2")
            
            btn_relatorios = ttk.Button(
                menu_container,
                text="📈  Relatórios",
                bootstyle="warning-outline",
                command=self.abrir_relatorios,
                width=28
            )
            btn_relatorios.grid(row=row, column=1, pady=5, padx=5, sticky="ew")
            btn_relatorios.configure(cursor="hand2")
        
        # ========== BOTÃO SAIR ==========
        btn_sair = ttk.Button(
            main_container,
            text="🚪  Sair do Sistema",
            bootstyle="danger-outline",
            command=self.sair,
            width=30
        )
        btn_sair.pack(pady=20)
        btn_sair.configure(cursor="hand2")
        
        # ========== FOOTER COM BRANDING ==========
        footer_frame = ttk.Frame(main_container)
        footer_frame.pack(side="bottom", fill="x", pady=10)
        
        # Linha 1: Versão do sistema
        ttk.Label(
            footer_frame,
            text="Versão 1.0.0",
            font=("Segoe UI", 8),
            foreground="#808080"
        ).pack()
        
        # Linha 2: Assinatura RBS Technology
        ttk.Label(
            footer_frame,
            text="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            font=("Segoe UI", 8),
            foreground="#404040"
        ).pack(pady=(5, 2))
        
        ttk.Label(
            footer_frame,
            text="▦ RBS Technology",
            font=("Segoe UI", 10, "bold"),
            foreground="#4ECDC4"
        ).pack()
        
        ttk.Label(
            footer_frame,
            text="Seu negócio, nossa tecnologia",
            font=("Segoe UI", 8, "italic"),
            foreground="#808080"
        ).pack(pady=(0, 5))

    # ========== AÇÕES DO MENU ==========

    def abrir_vendas(self):
        """Abre o módulo de vendas."""
        self.destroy()
        subprocess.Popen([sys.executable, "ui/vendas_ui.py",
                          self.display_name, self.role])

    def abrir_produtos(self):
        """Abre o módulo de produtos."""
        self.destroy()
        subprocess.Popen([sys.executable, "ui/produtos_ui.py",
                          self.display_name, self.role])

    def abrir_usuarios(self):
        """Abre o módulo de usuários."""
        self.destroy()
        subprocess.Popen([sys.executable, "ui/usuarios_ui.py",
                          self.display_name, self.role])

    def abrir_relatorios(self):
        """Abre o módulo de relatórios."""
        self.destroy()
        subprocess.Popen([sys.executable, "ui/relatorios_ui.py",
                          self.display_name, self.role])

    def bater_ponto(self):
        """Abre o módulo de bater ponto."""
        try:
            subprocess.Popen([sys.executable, "ui/bater_ponto_ui.py", 
                            self.display_name, self.role])
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir Bater Ponto: {e}")

    def abrir_estoque(self):
        """Abre o módulo de estoque."""
        self.destroy()
        subprocess.Popen([sys.executable, "ui/estoque_ui.py",
                          self.display_name, self.role])

    def sair(self):
        """Retorna para tela de login."""
        self.destroy()
        subprocess.Popen([sys.executable, "main.py"])


# Execução direta (para teste)
if __name__ == "__main__":
    if len(sys.argv) >= 3:
        display_name = sys.argv[1]
        role = sys.argv[2]
    else:
        display_name = "Usuário Teste"
        role = "admin"  # Para teste, usar admin para ver todas as opções

    app = DashboardUI(display_name, role)
    app.mainloop()