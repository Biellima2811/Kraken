import tkinter as tk
from tkinter import ttk, messagebox
from core.commander import RemoteCommander
import threading

class KrakenApp:
    def __init__(self, root):
        self.root = root
        
        # Configuração da Grade Principal (O segredo do Grid)
        # Dizemos ao Tkinter: "A coluna 0 e 1 devem crescer igualmente"
        self.root.columnconfigure(0, weight=1) 
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(1, weight=1) # A linha do meio (painéis) deve expandir

        # --- 1. Cabeçalho (Ocupa as 2 colunas) ---
        header_frame = ttk.Frame(root, padding=20)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        ttk.Label(header_frame, text="🦑 KRAKEN", font=("Impact", 24)).pack(side='left')
        ttk.Label(header_frame, text="| Automação Dedicada", font=("Helvetica", 12)).pack(side='left', padx=10, pady=(10,0))
        
        # --- 2. Área dos Servidores (Lado a Lado) ---
        
        # Lado Esquerdo: Banco de Dados (Coluna 0)
        self.frame_db = ttk.Labelframe(root, text=" Servidor Banco de Dados ", padding=15)
        self.frame_db.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Lado Direito: Aplicação (Coluna 1)
        self.frame_app = ttk.Labelframe(root, text=" Servidor Aplicação / Template ", padding=15)
        self.frame_app.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

        # Preenche os campos usando Grid interno
        self.inputs_db = self.criar_formulario_grid(self.frame_db, "10.110.xxx.xxx")
        self.inputs_app = self.criar_formulario_grid(self.frame_app, "10.110.xxx.xxx")

        # --- 3. Rodapé e Console (Ocupam as 2 colunas) ---
        footer_frame = ttk.Frame(root, padding=10)
        footer_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
        
        self.btn_liberar = ttk.Button(footer_frame, text="LIBERAR O KRAKEN (Iniciar)", command=self.iniciar_automacao)
        self.btn_liberar.pack(fill='x', ipady=10)
        
        # Console
        self.console_frame = ttk.Labelframe(root, text=" Log de Operações ", padding=10)
        self.console_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0,10))
        # Dá um peso para o console crescer um pouco se redimensionar
        self.root.rowconfigure(3, weight=0) 

        self.txt_console = tk.Text(self.console_frame, height=8, bg="#2e2e2e", fg="#00ff00", font=("Consolas", 9))
        self.txt_console.pack(fill='both', expand=True)

    def criar_formulario_grid(self, parent, placeholder_ip):
        """Cria os campos alinhados com Grid"""
        campos = {}
        
        # Configura a coluna 1 (onde ficam os Inputs) para expandir
        parent.columnconfigure(1, weight=1)

        # Linha 0: IP
        ttk.Label(parent, text="IP Privado:").grid(row=0, column=0, sticky="w", pady=5)
        ip = ttk.Entry(parent)
        ip.insert(0, placeholder_ip)
        ip.grid(row=0, column=1, sticky="ew", pady=5, padx=5)
        campos['ip'] = ip

        # Linha 1: Usuário
        ttk.Label(parent, text="Usuário Admin:").grid(row=1, column=0, sticky="w", pady=5)
        user = ttk.Entry(parent)
        user.insert(0, "Parceiro")
        user.grid(row=1, column=1, sticky="ew", pady=5, padx=5)
        campos['user'] = user

        # Linha 2: Senha
        ttk.Label(parent, text="Senha:").grid(row=2, column=0, sticky="w", pady=5)
        senha = ttk.Entry(parent, show="*")
        senha.grid(row=2, column=1, sticky="ew", pady=5, padx=5)
        campos['senha'] = senha

        # Linha 3: Divisor
        ttk.Separator(parent, orient='horizontal').grid(row=3, column=0, columnspan=2, sticky="ew", pady=15)

        # Linha 4: Funções (Checkbox)
        lbl_roles = ttk.Label(parent, text="Funções deste servidor:")
        lbl_roles.grid(row=4, column=0, columnspan=2, sticky="w")

        vars_roles = {
            'banco': tk.BooleanVar(value=True),
            'app': tk.BooleanVar(value=False),
            'repo': tk.BooleanVar(value=False)
        }
        
        # Checkboxes também no grid
        ttk.Checkbutton(parent, text="Hospeda Banco (SQL/FB)", variable=vars_roles['banco']).grid(row=5, column=0, columnspan=2, sticky="w")
        ttk.Checkbutton(parent, text="Hospeda Aplicação (IIS)", variable=vars_roles['app']).grid(row=6, column=0, columnspan=2, sticky="w")
        ttk.Checkbutton(parent, text="Repositório (C:\\Fortes)", variable=vars_roles['repo']).grid(row=7, column=0, columnspan=2, sticky="w")
        
        campos['roles'] = vars_roles
        return campos

    def log(self, mensagem):
        self.txt_console.insert(tk.END, f">> {mensagem}\n")
        self.txt_console.see(tk.END)
        self.root.update()

    def iniciar_automacao(self):
        # 1. Coleta e Valida Dados
        dados_db = {k: v.get() for k,v in self.inputs_db.items() if k != 'roles'}
        dados_app = {k: v.get() for k,v in self.inputs_app.items() if k != 'roles'}
        
        if not dados_db['ip'] or not dados_app['ip']:
            messagebox.showwarning("Erro", "Preencha os IPs dos servidores!")
            return

        # 2. Inicia o Processo em Background (Thread)
        # Isso impede que a janela congele ("Não Respondendo")
        self.btn_liberar.config(state="disabled", text="⏳ Executando...")
        thread = threading.Thread(target=self._processo_setup, args=(dados_db, dados_app))
        thread.start()

    def _processo_setup(self, dados_db, dados_app):
        """Lógica pesada que roda em background"""
        try:
            self.log("🦑 O Kraken acordou...")
            
            # --- TESTE DO SERVIDOR DE BANCO ---
            self.log(f"----------------------------------------")
            self.log(f"🔎 Alvo 1 (Banco): {dados_db['ip']}")
            
            cmd_db = RemoteCommander(dados_db['ip'], dados_db['user'], dados_db['senha'])
            cmd_db.conectar()
            
            sucesso, msg = cmd_db.testar_conexao()
            if sucesso:
                self.log(f"✅ {msg}")
            else:
                self.log(f"❌ Falha: {msg}")
                self.log("⚠️ Abortando operação no Banco de Dados.")
                # Aqui poderíamos dar return, mas vamos tentar o App

            # --- TESTE DO SERVIDOR DE APP ---
            self.log(f"----------------------------------------")
            self.log(f"🔎 Alvo 2 (App): {dados_app['ip']}")
            
            cmd_app = RemoteCommander(dados_app['ip'], dados_app['user'], dados_app['senha'])
            cmd_app.conectar()
            
            sucesso_app, msg_app = cmd_app.testar_conexao()
            if sucesso_app:
                self.log(f"✅ {msg_app}")
            else:
                self.log(f"❌ Falha: {msg_app}")

        except Exception as e:
            self.log(f"🔥 Erro Crítico no Kraken: {e}")
        finally:
            # Reativa o botão (precisa usar o after do tk se for mexer na GUI, 
            # mas para habilitar botão costuma passar direto, senão usamos root.after)
            self.btn_liberar.config(state="normal", text="LIBERAR O KRAKEN (Iniciar)")
            self.log("----------------------------------------")
            self.log("💤 Ciclo finalizado.")