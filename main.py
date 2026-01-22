import tkinter as tk
# from ttkthemes import ThemedTk  <-- Comente esta linha
from gui.main_window import KrakenApp

if __name__ == "__main__":
    # --- MODO DE SEGURANÇA (TKINTER PADRÃO) ---
    root = tk.Tk()  # Usamos tk.Tk() normal em vez de ThemedTk
    # root = ThemedTk(theme="radiance") <-- Comente esta linha
    
    root.title("Project Kraken v1.0 - Dedicated Ops")
    root.geometry("950x700")
    
    app = KrakenApp(root)
    root.mainloop()