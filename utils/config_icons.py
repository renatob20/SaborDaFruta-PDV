# utils/config_icons.py
"""
Gerenciador centralizado de ícones e imagens do sistema.
Facilita a manutenção e padronização visual.
"""

import os
import logging
from PIL import Image, ImageTk

class IconManager:
    """Gerencia o carregamento e cache de ícones do sistema."""
    
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.icons_path = os.path.join(self.base_path, "assets", "icons")
        self.images_path = os.path.join(self.base_path, "assets", "images")
        
        # Cache de imagens carregadas
        self._cache = {}
        
        logging.info(f"📁 Icons path: {self.icons_path}")
        logging.info(f"📁 Images path: {self.images_path}")
    
    def set_window_icon(self, window):
        """
        Define o ícone da janela.
        
        Args:
            window: Janela tkinter/ttkbootstrap
        """
        try:
            icon_path = os.path.join(self.icons_path, "app.ico")
            if os.path.exists(icon_path):
                window.iconbitmap(icon_path)
                logging.info(f"✅ Ícone da janela carregado: {icon_path}")
                return True
            else:
                logging.warning(f"⚠️ Ícone não encontrado: {icon_path}")
                return False
        except Exception as e:
            logging.error(f"❌ Erro ao carregar ícone da janela: {e}")
            return False
    
    def load_logo(self, size=(120, 120)):
        """
        Carrega o logo principal do sistema.
        
        Args:
            size: Tupla (largura, altura) para redimensionar
            
        Returns:
            ImageTk.PhotoImage ou None
        """
        cache_key = f"logo_{size[0]}x{size[1]}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            logo_path = os.path.join(self.images_path, "acai.png")
            if os.path.exists(logo_path):
                img = Image.open(logo_path)
                img_resized = img.resize(size, Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img_resized)
                self._cache[cache_key] = photo
                logging.info(f"✅ Logo carregado: {logo_path} ({size[0]}x{size[1]})")
                return photo
            else:
                logging.warning(f"⚠️ Logo não encontrado: {logo_path}")
                return None
        except Exception as e:
            logging.error(f"❌ Erro ao carregar logo: {e}")
            return None
    
    def load_splash(self, size=(300, 300), opacity=30):
        """
        Carrega imagem de splash/background com transparência.
        
        Args:
            size: Tupla (largura, altura)
            opacity: Opacidade (0-255, onde 0 é transparente)
            
        Returns:
            ImageTk.PhotoImage ou None
        """
        cache_key = f"splash_{size[0]}x{size[1]}_{opacity}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            splash_path = os.path.join(self.images_path, "acai-splash.png")
            if os.path.exists(splash_path):
                img = Image.open(splash_path)
                img_resized = img.resize(size, Image.Resampling.LANCZOS)
                # Aplicar transparência
                if img_resized.mode != 'RGBA':
                    img_resized = img_resized.convert('RGBA')
                img_resized.putalpha(opacity)
                photo = ImageTk.PhotoImage(img_resized)
                self._cache[cache_key] = photo
                logging.info(f"✅ Splash carregado: {splash_path}")
                return photo
            else:
                logging.warning(f"⚠️ Splash não encontrado: {splash_path}")
                return None
        except Exception as e:
            logging.error(f"❌ Erro ao carregar splash: {e}")
            return None
    
    def load_custom_image(self, filename, size=None):
        """
        Carrega uma imagem personalizada.
        
        Args:
            filename: Nome do arquivo na pasta images
            size: Tupla (largura, altura) opcional
            
        Returns:
            ImageTk.PhotoImage ou None
        """
        cache_key = f"custom_{filename}_{size}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            img_path = os.path.join(self.images_path, filename)
            if os.path.exists(img_path):
                img = Image.open(img_path)
                if size:
                    img = img.resize(size, Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self._cache[cache_key] = photo
                logging.info(f"✅ Imagem carregada: {img_path}")
                return photo
            else:
                logging.warning(f"⚠️ Imagem não encontrada: {img_path}")
                return None
        except Exception as e:
            logging.error(f"❌ Erro ao carregar imagem: {e}")
            return None
    
    def clear_cache(self):
        """Limpa o cache de imagens."""
        self._cache.clear()
        logging.info("🧹 Cache de imagens limpo")


# Instância global (singleton)
_icon_manager = None

def get_icon_manager():
    """Retorna a instância singleton do IconManager."""
    global _icon_manager
    if _icon_manager is None:
        _icon_manager = IconManager()
    return _icon_manager


# ========== FUNÇÕES DE CONVENIÊNCIA ==========

def set_window_icon(window):
    """Atalho para definir ícone da janela."""
    return get_icon_manager().set_window_icon(window)

def load_logo(size=(120, 120)):
    """Atalho para carregar logo."""
    return get_icon_manager().load_logo(size)

def load_splash(size=(300, 300), opacity=30):
    """Atalho para carregar splash."""
    return get_icon_manager().load_splash(size, opacity)


# ========== TESTE ==========
if __name__ == "__main__":
    import ttkbootstrap as ttk
    
    logging.basicConfig(level=logging.INFO)
    
    # Teste do gerenciador
    manager = get_icon_manager()
    
    # Criar janela de teste
    root = ttk.Window(themename="superhero")
    root.title("Teste de Ícones")
    root.geometry("400x400")
    
    # Definir ícone da janela
    manager.set_window_icon(root)
    
    # Carregar e exibir logo
    logo = manager.load_logo((150, 150))
    if logo:
        ttk.Label(root, image=logo).pack(pady=20)
    
    # Carregar e exibir splash
    splash = manager.load_splash((200, 200), opacity=50)
    if splash:
        ttk.Label(root, image=splash).pack(pady=20)
    
    ttk.Label(root, text="Teste de Ícones", font=("Arial", 16)).pack(pady=10)
    
    root.mainloop()