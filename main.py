import sys
import os
import tkinter as tk
from ttkthemes import ThemedTk
from gui.setup_window import SetupWindow

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)

if __name__=="__main__":
    root = ThemedTk(theme='radiance')
    root.title('Kraken | Setup Dedicados Skyone')
    root.geometry('700x800')

    # icone
    try:
        icon_path = resource_path(os.path.join('assets','kraken.ico'))
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except Exception as e:
        print(f'Não foi possivel encontra o arquivo kraken.ico... | Console: {e}')
        pass

        
    app = SetupWindow(root)
    root.mainloop()