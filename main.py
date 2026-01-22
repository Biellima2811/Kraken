import tkinter as tk
from ttkthemes import ThemedTk
from gui.main_window import KrakenApp
import os
import sys

def resource_path(relative_path):
    """Obtém caminho absoluto para recursos (funciona em Dev e PyInstaller)"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    # Inicializa com o tema Radiance
    root = ThemedTk(theme="radiance")
    root.title("Project Kraken v1.1 - Local Ops")
    root.geometry("950x750")
    
    # --- CONFIGURAÇÃO DO ÍCONE ---
    try:
        icon_path = resource_path(os.path.join("assets", "kraken.ico"))
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
        else:
            print(f"⚠️ Ícone não encontrado em: {icon_path}")
    except Exception as e:
        print(f"Erro ao carregar ícone: {e}")
    # -----------------------------
    
    app = KrakenApp(root)
    root.mainloop()