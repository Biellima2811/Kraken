import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import datetime
from core.local_ops import LocalManager

class SetupWindow:
    def __init__(self, root):
        self.root = root
        self.setup_logging()
        self.manager = LocalManager(self.log)

        # Configuração do Grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main_frame = ttk.Frame(root, padding=15)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(9, weight=1)

        # --- Cabeçalho ---
        ttk.Label(main_frame, text="🦑 KRAKEN ", font=("Impact", 20)).grid(row=0, column=0, pady=(0, 5))
        ttk.Label(main_frame, text="Ambiente Dedicado (V3.0 - Auth SQL)", font=("Helvetica", 10)).grid(row=1, column=0, pady=(0, 15))

        # 1. Identificação
        frame_cli = ttk.LabelFrame(main_frame, text=" 1. Identificação do Cliente ", padding=10)
        frame_cli.grid(row=2, column=0, sticky="ew", pady=5)
        
        ttk.Label(frame_cli, text="Sigla (ABC):").pack(side='left', padx=5)
        self.entry_sigla = ttk.Entry(frame_cli, width=15)
        self.entry_sigla.pack(side='left', padx=5)
        self.entry_sigla.insert(0, "ABC")

        ttk.Label(frame_cli, text="ID (123):").pack(side='left', padx=5)
        self.entry_id = ttk.Entry(frame_cli, width=15)
        self.entry_id.pack(side='left', padx=5)
        self.entry_id.insert(0, "123")

        # 2. Configuração de Rede e Banco
        frame_rede = ttk.LabelFrame(main_frame, text=" 2. Configuração de Rede e Banco ", padding=10)
        frame_rede.grid(row=3, column=0, sticky="ew", pady=5)
        
        # Linha 1: Drive e Rede
        frame_line1 = ttk.Frame(frame_rede)
        frame_line1.pack(fill='x', pady=2)
        
        ttk.Label(frame_line1, text="Drive Dados:").pack(side='left')
        self.combo_drive = ttk.Combobox(frame_line1, values=self.get_drives_disponiveis(), width=5, state="normal")
        self.combo_drive.current(0) 
        self.combo_drive.pack(side='left', padx=5)

        ttk.Label(frame_line1, text="Rede Banco (\\\\SRV):").pack(side='left', padx=(10, 5))
        self.entry_caminho_rede = ttk.Entry(frame_line1, width=30)
        self.entry_caminho_rede.insert(0, r"\\FORT-BD-01") 
        self.entry_caminho_rede.pack(side='left', padx=5)

        # Linha 2: Tipo e Credenciais (NOVO!)
        frame_line2 = ttk.Frame(frame_rede)
        frame_line2.pack(fill='x', pady=5)

        ttk.Label(frame_line2, text="Tipo:").pack(side='left')
        self.combo_banco = ttk.Combobox(frame_line2, values=["MSSQL", "FIREBIRD"], state="readonly", width=10)
        self.combo_banco.current(0) # MSSQL agora como padrão pra testar
        self.combo_banco.pack(side='left', padx=5)

        # Campos opcionais para SA
        ttk.Label(frame_line2, text="User SQL (sa):").pack(side='left', padx=(10, 5))
        self.entry_sql_user = ttk.Entry(frame_line2, width=15)
        self.entry_sql_user.pack(side='left')
        
        ttk.Label(frame_line2, text="Senha SQL:").pack(side='left', padx=(5, 5))
        self.entry_sql_pass = ttk.Entry(frame_line2, width=20, show="*")
        self.entry_sql_pass.pack(side='left')

        # 3. Sistemas
        frame_sis = ttk.LabelFrame(main_frame, text=" 3. Seleção de Sistemas ", padding=10)
        frame_sis.grid(row=4, column=0, sticky="ew", pady=5)

        self.sistemas = {
            "AC": tk.BooleanVar(value=True),
            "AG": tk.BooleanVar(value=False),
            "PONTO": tk.BooleanVar(value=False),
            "PATRIO": tk.BooleanVar(value=False),
            "RH": tk.BooleanVar(value=False),
            "CARGAS": tk.BooleanVar(value=False),
            "FROTA": tk.BooleanVar(value=False),
        }
        
        r, c = 0, 0
        for sigla, var in self.sistemas.items():
            ttk.Checkbutton(frame_sis, text=sigla, variable=var).grid(row=r, column=c, sticky='w', padx=10, pady=2)
            c += 1
            if c > 3: c, r = 0, r + 1

        # 4. Ações
        frame_acoes = ttk.LabelFrame(main_frame, text=" 4. Perfil deste Servidor ", padding=10)
        frame_acoes.grid(row=5, column=0, sticky="ew", pady=5)
        
        self.var_role_db = tk.BooleanVar(value=False)
        self.var_role_app = tk.BooleanVar(value=False)

        ttk.Checkbutton(frame_acoes, text="[SOU BANCO] Restaurar Bases (FB/SQL)", variable=self.var_role_db).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(frame_acoes, text="[SOU APP] Criar Pastas, MKLINK Rede, Atalhos...", variable=self.var_role_app).grid(row=1, column=0, sticky="w")

        # Botão
        self.btn_run = ttk.Button(main_frame, text="EXECUTAR PROCEDIMENTOS", command=self.iniciar)
        self.btn_run.grid(row=6, column=0, sticky="ew", pady=15, ipady=5)

        # Log
        self.txt_log = tk.Text(main_frame, height=10, bg="white", fg="black", font=("Consolas", 9))
        self.txt_log.grid(row=9, column=0, sticky="nsew", padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.txt_log.yview)
        scrollbar.grid(row=9, column=1, sticky="ns")
        self.txt_log['yscrollcommand'] = scrollbar.set

        self.txt_log.tag_config("erro", foreground="red", font=("Consolas", 9, "bold"))
        self.txt_log.tag_config("sucesso", foreground="green", font=("Consolas", 9, "bold"))
        self.txt_log.tag_config("aviso", foreground="#ff8c00")
        self.txt_log.tag_config("info", foreground="blue")

    def get_drives_disponiveis(self):
        drives = []
        if os.path.exists("D:\\"): drives.append("D:\\")
        drives.append("C:\\")
        return drives

    def setup_logging(self):
        if not os.path.exists("Logs"): os.makedirs("Logs")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_file = os.path.join("Logs", f"Kraken_Sessao_{timestamp}.txt")
        with open(self.log_file, "w", encoding="utf-8") as f:
            f.write(f"--- LOG KRAKEN LOCAL INICIADO EM {timestamp} ---\n")

    def log(self, msg, tipo="normal"):
        timestamp = datetime.datetime.now().strftime("[%H:%M:%S]")
        texto_completo = f"{timestamp} {msg}"
        tag = tipo if tipo in ["erro", "sucesso", "aviso", "info"] else None
        self.txt_log.insert(tk.END, f">> {msg}\n", tag)
        self.txt_log.see(tk.END)
        try:
            with open(self.log_file, "a", encoding="utf-8") as f: f.write(texto_completo + "\n")
        except: pass

    def iniciar(self):
        sistemas = [s for s, v in self.sistemas.items() if v.get()]
        if not sistemas:
            messagebox.showwarning("Aviso", "Selecione sistemas!")
            return

        tipo_banco = self.combo_banco.get()
        # Validação de Arquivos
        caminhos_bancos = {} 
        if self.var_role_db.get():
            ext = ".fbk" if tipo_banco == "FIREBIRD" else ".bak"
            pasta_limpa = r"C:\Kraken\Bancos Limpos FB" if tipo_banco == "FIREBIRD" else r"C:\Kraken\Bancos Limpos SQL"
            
            for sis in sistemas:
                arquivo_padrao = os.path.join(pasta_limpa, f"{sis}{ext}")
                if os.path.exists(arquivo_padrao):
                    caminhos_bancos[sis] = arquivo_padrao
                else:
                    self.log(f"Backup padrão não encontrado: {arquivo_padrao}", "aviso")
                    arquivo = filedialog.askopenfilename(title=f"Selecione Backup {sis}", filetypes=[("Backup", f"*{ext}")])
                    if arquivo: caminhos_bancos[sis] = arquivo
                    else:
                        messagebox.showwarning("Parar", f"Backup do {sis} obrigatório.")
                        return

        dados = {
            "sigla": self.entry_sigla.get().upper(),
            "id": self.entry_id.get(),
            "tipo_banco": tipo_banco,
            "caminho_rede": self.entry_caminho_rede.get(),
            "drive_dados": self.combo_drive.get(),
            "sql_user": self.entry_sql_user.get(), # NOVO
            "sql_pass": self.entry_sql_pass.get(), # NOVO
            "caminhos_bancos_validos": caminhos_bancos,
            "acoes": {
                "role_db": self.var_role_db.get(),
                "role_app": self.var_role_app.get(),
            }
        }

        self.btn_run.config(state="disabled")
        t = threading.Thread(target=self._run_thread, args=(sistemas, dados))
        t.daemon = True
        t.start()

    def _run_thread(self, sistemas, dados):
        try:
            self.log("🦑 Kraken Iniciado...", "info")
            self.log(f"📂 Drive: {dados['drive_dados']} | Banco: {dados['tipo_banco']}", "info")
            if dados['sql_user']:
                self.log(f"🔑 Usando credenciais SQL fornecidas: {dados['sql_user']}", "aviso")
            
            self.manager.executar_setup(sistemas, dados)
            self.log("✅ Processo Finalizado!", "sucesso")
            messagebox.showinfo("Sucesso", "Procedimentos Concluídos!")
        except Exception as e:
            self.log(f"🔥 ERRO FATAL: {e}", "erro")
            import traceback
            self.log(traceback.format_exc())
            messagebox.showerror("Erro", str(e))
        finally:
            self.root.after(0, lambda: self.btn_run.config(state="normal"))