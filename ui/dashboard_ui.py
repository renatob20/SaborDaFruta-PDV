# ui/dashboard_ui.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from PIL import Image, ImageTk
import logging

logging.basicConfig(level=logging.DEBUG)

class DashboardUI(ttk.Frame):
    """Dashboard - Frame principal de navegação"""
    
    def __init__(self, master, display_name, role):
        super().__init__(master)
        self.master = master
        self.pack(fill=BOTH, expand=True)
        
        self.display_name = display_name
        self.role = role
        self.operador = display_name
        
        # Maximiza janela
        try:
            self.master.state("zoomed")
        except:
            try:
                self.master.attributes("-zoomed", True)
            except:
                pass
        
        # Carrega imagens
        self.logo_img = None
        self._load_images()
        
        self._build_ui()

    def _load_images(self):
        """Carrega banner"""
        try:
            logo_path = os.path.join("assets", "imagens", "acai-banner02.png")
            if os.path.exists(logo_path):
                logo_original = Image.open(logo_path)
                logo_resized = logo_original.resize((800, 140), Image.Resampling.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(logo_resized)
        except Exception as e:
            logging.error(f"Erro ao carregar banner: {e}")
            self.logo_img = None

    def _build_ui(self):
        # Container principal
        main_container = ttk.Frame(self)
        main_container.pack(fill=BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_container, style="Dark.TFrame")
        header_frame.pack(fill=X, padx=0, pady=0)
        
        if self.logo_img:
            banner_label = ttk.Label(header_frame, image=self.logo_img)
            banner_label.pack(pady=10)
        else:
            ttk.Label(header_frame, text="🍧 Açaiteria o Sabor da Fruta",
                     font=("Segoe UI", 28, "bold"), 
                     foreground="#FFFFFF").pack(pady=20)
        
        # Separador
        separator = ttk.Frame(header_frame, height=2, style="success.TFrame")
        separator.pack(fill=X, padx=50, pady=(0, 10))
        
        # Usuário logado
        user_frame = ttk.Frame(main_container)
        user_frame.pack(pady=15)
        
        ttk.Label(user_frame, text=f"👤 {self.display_name}",
                 font=("Segoe UI", 14, "bold"), 
                 foreground="#4ECDC4").pack()
        
        badge_color = "#FF6B6B" if self.role == "admin" else "#95E1D3"
        badge_text = "🔑 Administrador" if self.role == "admin" else "👨‍💼 Operador"
        
        ttk.Label(user_frame, text=badge_text, font=("Segoe UI", 10),
                 foreground=badge_color).pack(pady=3)
        
        # Menu de navegação
        menu_container = ttk.Frame(main_container)
        menu_container.pack(pady=10, padx=40, fill=BOTH, expand=True)
        
        menu_container.columnconfigure(0, weight=1)
        menu_container.columnconfigure(1, weight=1)
        
        row = 0
        
        # Vendas
        btn_vendas = ttk.Button(menu_container, text="🛒  Realizar Venda",
                               bootstyle="success", command=self.abrir_vendas, width=30)
        btn_vendas.grid(row=row, column=0, columnspan=2, pady=8, padx=5, sticky="ew")
        row += 1
        
        # Bater Ponto
        btn_ponto = ttk.Button(menu_container, text="⏰  Registrar Ponto",
                              bootstyle="info", command=self.bater_ponto, width=28)
        btn_ponto.grid(row=row, column=0, columnspan=2, pady=5, padx=5, sticky="ew")
        
        # Área administrativa
        if self.role == "admin":
            row += 1
            ttk.Separator(menu_container, orient="horizontal").grid(
                row=row, column=0, columnspan=2, pady=15, sticky="ew")
            
            row += 1
            ttk.Label(menu_container, text="🔐 ÁREA ADMINISTRATIVA",
                     font=("Segoe UI", 11, "bold"), 
                     foreground="#FFD93D").grid(row=row, column=0, columnspan=2, pady=(0, 10))
            
            row += 1
            ttk.Button(menu_container, text="📦  Produtos", bootstyle="primary-outline",
                      command=self.abrir_produtos, width=28).grid(row=row, column=0, pady=5, padx=5, sticky="ew")
            ttk.Button(menu_container, text="📊  Estoque", bootstyle="primary-outline",
                      command=self.abrir_estoque, width=28).grid(row=row, column=1, pady=5, padx=5, sticky="ew")
            
            row += 1
            ttk.Button(menu_container, text="👥  Usuários", bootstyle="warning-outline",
                      command=self.abrir_usuarios, width=28).grid(row=row, column=0, pady=5, padx=5, sticky="ew")
            ttk.Button(menu_container, text="📈  Relatórios", bootstyle="warning-outline",
                      command=self.abrir_relatorios, width=28).grid(row=row, column=1, pady=5, padx=5, sticky="ew")
        
        # Botão Sair
        ttk.Button(main_container, text="🚪  Sair do Sistema", bootstyle="danger-outline",
                  command=self.sair, width=30).pack(pady=20)
        
        # Footer
        footer_frame = ttk.Frame(main_container)
        footer_frame.pack(side="bottom", fill="x", pady=10)
        
        ttk.Label(footer_frame, text="Versão 1.0.0", font=("Segoe UI", 8),
                 foreground="#808080").pack()
        ttk.Label(footer_frame, text="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                 font=("Segoe UI", 8), foreground="#404040").pack(pady=(5, 2))
        ttk.Label(footer_frame, text="▦ RBS Technology", font=("Segoe UI", 10, "bold"),
                 foreground="#4ECDC4").pack()
        ttk.Label(footer_frame, text="Seu negócio, nossa tecnologia",
                 font=("Segoe UI", 8, "italic"), foreground="#808080").pack(pady=(0, 5))

    # ✅ NAVEGAÇÃO CORRETA - Sem subprocess
    def abrir_vendas(self):
        self.destroy()
        from ui.vendas_ui import VendasUI
        VendasUI(master=self.master, display_name=self.display_name, role=self.role)

    def abrir_produtos(self):
        self.destroy()
        from ui.produtos_ui import ProdutosUI
        ProdutosUI(master=self.master, display_name=self.display_name, role=self.role)

    def abrir_usuarios(self):
        self.destroy()
        from ui.usuarios_ui import UsuariosUI
        UsuariosUI(master=self.master, display_name=self.display_name, role=self.role)

    def abrir_relatorios(self):
        self.destroy()
        from ui.relatorios_ui import RelatoriosUI
        RelatoriosUI(master=self.master, display_name=self.display_name, role=self.role)

    def bater_ponto(self):
        self.destroy()
        from ui.bater_ponto_ui import BaterPontoUI
        BaterPontoUI(master=self.master, operador_display=self.display_name, role=self.role)

    def abrir_estoque(self):
        self.destroy()
        from ui.estoque_ui import EstoqueUI
        EstoqueUI(master=self.master, operador_display=self.display_name, role=self.role)

    def sair(self):
        """Volta para tela de login"""
        self.destroy()
        from ui.login_ui import LoginUI
        LoginUI(master=self.master)