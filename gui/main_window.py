import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
from datetime import datetime
from core.commander import RemoteComander as RC
from core.services.firebird import FirebirdManager

class KrakenApp:
    def __init__(self, root):
        self.root = root
        self.log_file = self.iniciar_sistema_logs() # Cria arquivo de log novo
        
        # --- CONFIGURAÇÃO DO GRID ---
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(1, weight=1)

        # --- 1. CABEÇALHO ---
        header_frame = ttk.Frame(root, padding=20)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        ttk.Label(header_frame, text="🦑 KRAKEN", font=("Impact", 24)).pack(side='left')
        ttk.Label(header_frame, text="| Automação Dedicada (Local/Remoto)", font=("Helvetica", 12)).pack(side='left', padx=10, pady=(10,0))
        
        # --- 2. ÁREA DOS SERVIDORES ---
        self.frame_db = ttk.Labelframe(root, text=" Servidor Banco de Dados ", padding=15)
        self.frame_db.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        self.frame_app = ttk.Labelframe(root, text=" Servidor Aplicação / Template ", padding=15)
        self.frame_app.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

        # SE ESTIVER RODANDO NO SERVIDOR, O IP DE CONEXÃO É O PRIVADO!
        self.inputs_db = self.criar_formulario_grid(self.frame_db, "10.110.xxx.xxx", "10.110.xxx.xxx")
        self.inputs_app = self.criar_formulario_grid(self.frame_app, "10.110.xxx.xxx", "10.110.xxx.xxx")

        # --- 3. RODAPÉ ---
        footer_frame = ttk.Frame(root, padding=10)
        footer_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
        
        self.btn_liberar = ttk.Button(footer_frame, text="LIBERAR O KRAKEN (Iniciar)", command=self.iniciar_automacao)
        self.btn_liberar.pack(fill='x', ipady=10)

        lbl_assinatura = ttk.Label(footer_frame, text='© 2026 Feito por Gabriel Levi · Uso interno · Todos os direitos reservados.')
        lbl_assinatura.pack(side='bottom', pady=(5, 0))

        # --- 4. CONSOLE ---
        self.console_frame = ttk.Labelframe(root, text=" Log de Operações ", padding=10)
        self.console_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0,10))
        self.root.rowconfigure(3, weight=0)

        self.txt_console = tk.Text(self.console_frame, height=8, bg="#2e2e2e", fg="#00ff00", font=("Consolas", 9))
        self.txt_console.pack(fill='both', expand=True)

    def iniciar_sistema_logs(self):
        """Cria pasta Logs e retorna o caminho do arquivo da sessão"""
        if not os.path.exists("Logs"):
            os.makedirs("Logs")
        
        nome_arq = f"Logs/sessao_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
        with open(nome_arq, "w", encoding="utf-8") as f:
            f.write(f"--- KRAKEN LOG INICIADO EM {datetime.now()} ---\n")
        return nome_arq

    def criar_formulario_grid(self, parent, place_conn, place_priv):
        campos = {}
        parent.columnconfigure(1, weight=1)

        # Mudei o nome para ficar claro que pode ser qualquer IP
        ttk.Label(parent, text="IP Conexão (WinRM):").grid(row=0, column=0, sticky="w", pady=5)
        ip_conn = ttk.Entry(parent)
        ip_conn.insert(0, place_conn)
        ip_conn.grid(row=0, column=1, sticky="ew", pady=5, padx=5)
        campos['ip_conexao'] = ip_conn # CHAVE NOVA

        ttk.Label(parent, text="IP Interno (Config):").grid(row=1, column=0, sticky="w", pady=5)
        ip_priv = ttk.Entry(parent)
        ip_priv.insert(0, place_priv)
        ip_priv.grid(row=1, column=1, sticky="ew", pady=5, padx=5)
        campos['ip_privado'] = ip_priv

        ttk.Label(parent, text="Usuário Admin:").grid(row=2, column=0, sticky="w", pady=5)
        user = ttk.Entry(parent)
        user.insert(0, "Parceiro")
        user.grid(row=2, column=1, sticky="ew", pady=5, padx=5)
        campos['user'] = user

        ttk.Label(parent, text="Senha:").grid(row=3, column=0, sticky="w", pady=5)
        senha = ttk.Entry(parent, show="*")
        senha.grid(row=3, column=1, sticky="ew", pady=5, padx=5)
        campos['senha'] = senha

        ttk.Separator(parent, orient='horizontal').grid(row=4, column=0, columnspan=2, sticky="ew", pady=15)

        ttk.Label(parent, text="Funções deste servidor:").grid(row=5, column=0, columnspan=2, sticky="w")
        
        vars_roles = {
            'banco': tk.BooleanVar(value=True),
            'app': tk.BooleanVar(value=False),
            'repo': tk.BooleanVar(value=False)
        }
        
        ttk.Checkbutton(parent, text="Hospeda Banco (SQL/FB)", variable=vars_roles['banco']).grid(row=6, column=0, columnspan=2, sticky="w")
        ttk.Checkbutton(parent, text="Hospeda Aplicação (IIS)", variable=vars_roles['app']).grid(row=7, column=0, columnspan=2, sticky="w")
        ttk.Checkbutton(parent, text="Repositório (C:\\Fortes)", variable=vars_roles['repo']).grid(row=8, column=0, columnspan=2, sticky="w")
        
        campos['roles'] = vars_roles
        return campos

    def log(self, mensagem):
        # 1. Tela
        self.txt_console.insert(tk.END, f">> {mensagem}\n")
        self.txt_console.see(tk.END)
        
        # 2. Arquivo (Append)
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%H:%M:%S")
                f.write(f"[{timestamp}] {mensagem}\n")
        except Exception:
            pass # Não queremos travar o app por erro de log

    def iniciar_automacao(self):
        # Filtra os dados dos inputs
        dados_db = {k: v.get() for k,v in self.inputs_db.items() if k != 'roles'}
        dados_app = {k: v.get() for k,v in self.inputs_app.items() if k != 'roles'}
        
        # --- CORREÇÃO DO ERRO 'ip' AQUI ---
        # Agora usamos a chave certa 'ip_conexao'
        if not dados_db['ip_conexao'] or not dados_app['ip_conexao']:
            messagebox.showwarning("Erro", "Preencha os IPs de Conexão!")
            return

        self.btn_liberar.config(state="disabled", text="⏳ Conectando aos tentáculos...")
        
        t = threading.Thread(target=self._processo_setup, args=(dados_db, dados_app))
        t.daemon = True
        t.start()

    def _processo_setup(self, dados_db, dados_app):
        try:
            self.log("🦑 O Kraken iniciou a operação...")
            
            # ==========================================================
            # ETAPA 1: SERVIDOR DE BANCO DE DADOS
            # ==========================================================
            if dados_db['roles']['banco'].get(): # Só faz se o checkbox estiver marcado
                self.log(f"----------------------------------------")
                self.log(f"🔎 Conectando ao Banco: {dados_db['ip_conexao']}...")
                
                cmd_db = RemoteCommander(dados_db['ip_conexao'], dados_db['user'], dados_db['senha'])
                
                if cmd_db.conectar():
                    sucesso, msg = cmd_db.testar_conexao()
                    if sucesso:
                        self.log(f"✅ Conexão OK: {msg}")
                        
                        # --- AQUI COMEÇA A AUTOMAÇÃO REAL ---
                        self.log("🚀 Iniciando Protocolo de Manutenção Firebird...")
                        fb_man = FirebirdManager(cmd_db)
                        
                        # 1. Verifica se tem Firebird
                        ok, status_fb = fb_man.verificar_instalacao()
                        self.log(status_fb)
                        
                        if ok:
                            # Lista de sistemas para dar manutenção (Pode virar config depois)
                            sistemas = ["AC", "AG", "PATRIO", "PONTO"] 
                            for sis in sistemas:
                                fb_man.realizar_manutencao(sis, self.log)
                        # ------------------------------------
                    else:
                        self.log(f"❌ Falha no Teste: {msg}")
                else:
                    self.log("❌ Falha de Sessão WinRM no Banco.")

            # ==========================================================
            # ETAPA 2: SERVIDOR DE APLICAÇÃO
            # ==========================================================
            if dados_app['roles']['app'].get():
                self.log(f"----------------------------------------")
                self.log(f"🔎 Conectando ao App: {dados_app['ip_conexao']}...")
                
                cmd_app = RemoteCommander(dados_app['ip_conexao'], dados_app['user'], dados_app['senha'])
                
                if cmd_app.conectar():
                    sucesso, msg = cmd_app.testar_conexao()
                    if sucesso:
                        self.log(f"✅ Conexão OK: {msg}")
                        self.log("ℹ️ Módulo de Instalação de App ainda não implementado (Próximo Passo)")
                        # AQUI ENTRARÁ O SCRIPT DE CÓPIA DE ARQUIVOS
                    else:
                        self.log(f"❌ Falha no Teste: {msg}")
                else:
                    self.log("❌ Falha de Sessão WinRM no App.")

        except Exception as e:
            self.log(f"🔥 ERRO CRÍTICO NA THREAD: {e}")
            import traceback
            self.log(traceback.format_exc())
        finally:
            self.log("----------------------------------------")
            self.log("💤 Ciclo finalizado.")
            self.root.after(0, lambda: self.btn_liberar.config(state="normal", text="LIBERAR O KRAKEN (Iniciar)"))