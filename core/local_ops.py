import os
import shutil
import socket
import secrets
import string
import subprocess
import time
import re

class LocalManager:
    def __init__(self, log_callback):
        self.log = log_callback
        # --- CAMINHOS PADRÃO (ORIGEM) ---
        self.path_kraken_installers = r"C:\Kraken\Corporativo"
        self.path_kraken_cloudup_fb = r"C:\Kraken\CloudUp\Atualiza_FB\CloudUp\CloudUpCMD"
        self.path_kraken_cloudup_sql = r"C:\Kraken\CloudUp\Atualiza_SQL\Cloudup\CloudupCMD"
        
        # --- DESTINOS ---
        self.destino_fortes = r"C:\Fortes" 
        self.destino_cloudup = r"C:\Atualiza\Cloudup\CloudupCMD"
        self.destino_app_root = r"C:\\"

    def get_drive_dados(self):
        return "D:\\" if os.path.exists("D:\\") else "C:\\"

    def gerar_senha_forte(self, length=14):
        alphabet = string.ascii_letters + string.digits + "!@#$%&"
        return ''.join(secrets.choice(alphabet) for i in range(length))

    def gerar_senha_sistema(self, sigla, sufixo):
        return f"Fortes@{sigla.upper()}{sufixo}!"

    def salvar_credenciais(self, sis, user, pwd):
        """Salva as credenciais geradas em um arquivo txt"""
        arquivo = r"C:\Kraken\Credenciais_Banco.txt"
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        texto = f"[{timestamp}] SISTEMA: {sis} | USUARIO: {user} | SENHA: {pwd}\n"
        try:
            with open(arquivo, "a") as f:
                f.write(texto)
            self.log(f"   📝 Credenciais salvas em: {arquivo}", "sucesso")
        except: pass

    def get_auth_args(self, dados):
        user = dados.get('sql_user')
        pwd = dados.get('sql_pass')
        if user and pwd:
            return f'-U "{user}" -P "{pwd}"'
        return '-E'

    def executar_setup(self, sistemas, dados):
        sigla = dados['sigla']
        sufixo = dados['id']
        tipo_banco = dados['tipo_banco']
        caminho_rede_input = dados['caminho_rede']
        drive_dados = dados['drive_dados']
        hostname = socket.gethostname()

        if not drive_dados.endswith("\\"): drive_dados += "\\"
        
        # Tratamento caminho de rede
        if caminho_rede_input.lower().endswith("\\fortes"):
            caminho_rede_base = caminho_rede_input
        elif caminho_rede_input.lower().endswith("\\fortes\\"):
            caminho_rede_base = caminho_rede_input[:-1]
        else:
            caminho_rede_base = os.path.join(caminho_rede_input, "Fortes")

        senha_sistema = self.gerar_senha_sistema(sigla, sufixo)

        # =========================================================
        # ROLE 1: SERVIDOR DE BANCO
        # =========================================================
        if dados['acoes']['role_db']:
            self.log("=== SERVIDOR DE BANCO ===", "info")
            self.verificar_servicos(tipo_banco)
            
            if not os.path.exists(self.destino_fortes):
                os.makedirs(self.destino_fortes)
            
            for sis in sistemas:
                self.log(f"--- Processando Sistema: {sis} ---")
                nome_banco_user = f"{sigla}_{sis}_{sufixo}" 
                
                # 1. RESTORE
                caminho_backup = dados.get('caminhos_bancos_validos', {}).get(sis)
                if caminho_backup and os.path.exists(caminho_backup):
                     if tipo_banco == "FIREBIRD":
                         self.restaurar_banco_fb(sis, nome_banco_user, drive_dados, caminho_backup)
                     elif tipo_banco == "MSSQL":
                         self.restaurar_banco_sql_smart(sis, nome_banco_user, drive_dados, caminho_backup, dados, senha_sistema)
                     
                     # Salva credenciais após sucesso
                     self.salvar_credenciais(sis, nome_banco_user, senha_sistema)
                else:
                     self.log(f"   ⚠️ Backup não encontrado. Pulando restore.", "aviso")

                # 2. CÓPIA BINÁRIOS
                origem_installer = os.path.join(self.path_kraken_installers, sis)
                destino_local = os.path.join(self.destino_fortes, sis)

                if os.path.exists(origem_installer):
                    if not os.path.exists(destino_local):
                        shutil.copytree(origem_installer, destino_local)
                        self.log("   ✔ Binários copiados para C:\Fortes.", "sucesso")
                    else:
                        self.log(f"   ℹ️ Pasta {sis} já existe.", "aviso")
                else:
                    self.log(f"   ❌ Origem {origem_installer} vazia!", "erro")

                # 3. PREPARAR REPOSITÓRIO CLOUDUP (JÁ CONFIGURADO!)
                origem_cloudup_base = self.path_kraken_cloudup_sql if tipo_banco == "MSSQL" else self.path_kraken_cloudup_fb
                origem_cloudup = os.path.join(origem_cloudup_base, sis)
                destino_repo_cloudup = os.path.join(self.destino_fortes, "_Instaladores", "CloudUp", sis)
                
                self.log(f"   🔍 Buscando CloudUp em: {origem_cloudup}") # LOG DE DEBUG

                if os.path.exists(origem_cloudup):
                    # Se já existe, limpa para garantir config nova
                    if os.path.exists(destino_repo_cloudup):
                        shutil.rmtree(destino_repo_cloudup)
                    
                    # Copia o template
                    shutil.copytree(origem_cloudup, destino_repo_cloudup)
                    
                    # Configura os INIs DENTRO do repositório
                    # Obs: IP aqui usamos o próprio hostname ou o caminho de rede, pois é o servidor de banco
                    self.configurar_cloudup_ini(
                        sis, 
                        nome_banco_user, 
                        tipo_banco, 
                        hostname, # IP/Host
                        drive_dados, 
                        hostname, 
                        senha_sistema, 
                        target_dir=destino_repo_cloudup # Escreve na pasta _Instaladores
                    )
                    self.log("   📦 Repositório CloudUp configurado na rede.", "sucesso")
                else:
                    self.log(f"   ❌ Template CloudUp não encontrado na origem!", "erro")

        # =========================================================
        # ROLE 2: SERVIDOR DE APLICAÇÃO
        # =========================================================
        if dados['acoes']['role_app']:
            self.log("=== SERVIDOR DE APLICAÇÃO ===", "info")
            self.remover_ie()

            if not os.path.exists(self.destino_fortes):
                os.makedirs(self.destino_fortes)

            for sis in sistemas:
                self.log(f"--- Processando App: {sis} ---")
                local_sis = os.path.join(self.destino_fortes, sis) 
                rede_sis = os.path.join(caminho_rede_base, sis) 
                
                # A. COPIAR BINÁRIOS
                origem_local = os.path.join(self.path_kraken_installers, sis)
                origem_rede = rede_sis 
                origem_final = origem_local if os.path.exists(origem_local) else (origem_rede if os.path.exists(origem_rede) else None)
                
                if origem_final:
                    if not os.path.exists(local_sis):
                        try:
                            shutil.copytree(origem_final, local_sis)
                            self.log("   ✔ Cópia concluída.", "sucesso")
                        except: self.log(f"   ❌ Erro cópia.", "erro")
                else:
                    self.log(f"   ❌ Arquivos não encontrados na rede: {origem_rede}", "erro")
                    if not os.path.exists(local_sis): os.makedirs(local_sis)

                # B. MKLINK / ATALHOS
                self.criar_mklink_rede(os.path.join(local_sis, "Usuarios"), os.path.join(rede_sis, "Usuarios"))
                if sis == "PONTO":
                    self.criar_mklink_rede(os.path.join(local_sis, "Config"), os.path.join(rede_sis, "Config"))

                self.criar_atalho_powershell(os.path.join(local_sis, f"{sis}.exe"), os.path.join(local_sis, f"{sis}.lnk"), rede_sis)

                # C. CLOUDUP
                ip_banco_real = dados.get('ip_banco') 
                if not ip_banco_real:
                    match = re.search(r"^\\\\([^\\]+)", camino_rede_base) if 'camino_rede_base' in locals() else None
                    if not match: match = re.search(r"^\\\\([^\\]+)", caminho_rede_base) # Tenta de novo com var certa
                    ip_banco_real = match.group(1) if match else hostname

                nome_banco_user = f"{sigla}_{sis}_{sufixo}"
                
                # Origens Template
                origem_cup_local = os.path.join(self.path_kraken_cloudup_sql if tipo_banco == "MSSQL" else self.path_kraken_cloudup_fb, sis)
                origem_cup_rede = os.path.join(caminho_rede_base, "_Instaladores", "CloudUp", sis)

                origem_final_cup = None
                if os.path.exists(origem_cup_local):
                    origem_final_cup = origem_cup_local
                elif os.path.exists(origem_cup_rede):
                    origem_final_cup = origem_cup_rede
                    self.log("   🌐 Baixando CloudUp da rede...", "info")

                if origem_final_cup:
                    dest_cup_local = os.path.join(self.destino_cloudup, sis)
                    if os.path.exists(dest_cup_local): shutil.rmtree(dest_cup_local)
                    shutil.copytree(origem_final_cup, dest_cup_local)
                    
                    # Reconfigura LOCALMENTE para garantir caminhos certos (C:\Atualiza...)
                    self.configurar_cloudup_ini(
                        sis, nome_banco_user, tipo_banco, ip_banco_real, drive_dados, hostname, senha_sistema, 
                        target_dir=dest_cup_local
                    )
                    self.log("   ✔ CloudUp instalado e configurado.", "sucesso")
                else:
                    self.log(f"   ❌ Template CloudUp não encontrado.", "erro")

    # ==========================
    # AUXILIARES
    # ==========================
    
    def configurar_cloudup_ini(self, sis, nome_banco_user, tipo_banco, ip_banco, drive_dados, hostname, senha_sistema, target_dir):
        """Escreve os INIs na pasta alvo (Seja Repositório ou Local)"""
        
        pasta_fortes_ini = os.path.join(target_dir, "Fortes")
        os.makedirs(pasta_fortes_ini, exist_ok=True)
        caminho_ini = os.path.join(pasta_fortes_ini, "Fortes.ini")
        
        # Dados do Banco (Sempre no drive de dados, ex: D:\BDS\DADOS)
        data_folder_ini = os.path.join(drive_dados, "BDS", "DADOS", sis)

        if tipo_banco == "MSSQL":
            driver, db_file = "MSSQL", f"{ip_banco}:{nome_banco_user}"
            db_user, db_pass = nome_banco_user, senha_sistema
        else:
            driver, db_file = "INTRBASE", f"{ip_banco}/3050:{os.path.join(data_folder_ini, f'{nome_banco_user}.FDB')}"
            db_user, db_pass = "sysdba", "masterkey"

        # ProgramFolder: Aponta para C:\Fortes\SIS (Padrão local de execução)
        local_program_folder = os.path.join(self.destino_fortes, sis)

        with open(caminho_ini, "w") as f:
            f.write(f"[Startup]\nProgramFolder = {local_program_folder}\nDataFolder = {data_folder_ini}\nDatabaseFile = {db_file}\nDriverName = {driver}\nUserName = {db_user}\nPassword = {db_pass}\n\n[Settings]\nContinueUpdateAfterCrashRecovery = True\nAllowOldBackupsRestoration = False\nSkipWarnings = True\nByPassInUseCheck = True\nRetryOnDatabaseInUse = False\n\n[Backup]\nSkipBackupDatabase = True\n")

        with open(os.path.join(target_dir, "config.ini"), "w") as f:
            f.write(f"[Settings]\nBaseDir={target_dir}\nBackupDir={target_dir}\\Backup\nResourceDir={target_dir}\\Atualizadores\nAppRootDir={self.destino_app_root}\nDbServerName={ip_banco}\nSgbd={tipo_banco}\n\n[Operations]\nCustomer=Fortes,ExeName={sis},ExeDirName={sis},AppSubdir=Fortes,DbInstance=,DbName={nome_banco_user},DbUser={db_user},DbPass={db_pass}\n")

    # Mantenha as outras funções (encontrar_gbak, restaurar_..., remover_ie, criar_mklink, criar_atalho) IGUAIS
    def encontrar_gbak(self):
        paths = ["gbak", r"C:\Program Files\Firebird\Firebird_3_0\gbak.exe", r"C:\Program Files (x86)\Firebird\Firebird_3_0\gbak.exe"]
        for p in paths:
            if p == "gbak": continue 
            if os.path.exists(p): return f'"{p}"'
        return "gbak"

    def restaurar_banco_fb(self, sis, nome_banco, drive_dados, arquivo_backup):
        self.log(f"🛠️ [FB] Restaurando {nome_banco}...")
        pasta_dados = os.path.join(drive_dados, "BDS", "DADOS", sis)
        if not os.path.exists(pasta_dados): os.makedirs(pasta_dados)
        arquivo_fdb = os.path.join(pasta_dados, f"{nome_banco}.FDB")
        if os.path.exists(arquivo_fdb):
            self.log(f"   ⚠️ Banco já existe.", "aviso")
            return
        gbak = self.encontrar_gbak()
        cmd = f'{gbak} -c -v -rep -user sysdba -pas masterkey "{arquivo_backup}" "{arquivo_fdb}"'
        try:
            subprocess.run(cmd, shell=True, check=True)
            self.log(f"   ✔ Restore FB Sucesso.", "sucesso")
        except: self.log(f"   ❌ Erro GBAK.", "erro")

    def restaurar_banco_sql_smart(self, sis, nome_banco, drive_dados, arquivo_backup, dados, senha_user):
        self.log(f"🛠️ [SQL] Processando {nome_banco}...", "info")
        auth_args = self.get_auth_args(dados)
        pasta_dados = os.path.join(drive_dados, "BDS", "DADOS", sis)
        pasta_logs = os.path.join(drive_dados, "BDS", "LOG", sis)
        os.makedirs(pasta_dados, exist_ok=True)
        os.makedirs(pasta_logs, exist_ok=True)
        arquivo_mdf = os.path.join(pasta_dados, f"{nome_banco}.mdf")
        arquivo_ldf = os.path.join(pasta_logs, f"{nome_banco}_log.ldf")

        if not os.path.exists(arquivo_mdf):
            cmd_list = f'sqlcmd -S localhost {auth_args} -Q "RESTORE FILELISTONLY FROM DISK = N\'{arquivo_backup}\'" -W -h-1'
            logical_data, logical_log = None, None
            try:
                res = subprocess.run(cmd_list, shell=True, capture_output=True, text=True)
                for line in res.stdout.splitlines():
                    parts = line.split()
                    if len(parts) > 1:
                        if 'D' in parts and not logical_data: logical_data = parts[0]
                        elif 'L' in parts and not logical_log: logical_log = parts[0]
            except: pass

            if logical_data and logical_log:
                query_raw = f"RESTORE DATABASE [{nome_banco}] FROM DISK = N'{arquivo_backup}' WITH FILE = 1, MOVE N'{logical_data}' TO N'{arquivo_mdf}', MOVE N'{logical_log}' TO N'{arquivo_ldf}', NOUNLOAD, REPLACE, STATS = 5"
                try:
                    subprocess.run(f'sqlcmd -S localhost {auth_args} -Q "{query_raw}" -l 60', shell=True, check=True)
                    self.log("   ✔ Restore SQL OK.", "sucesso")
                except: self.log(f"   ❌ Falha Restore.", "erro")
        else: self.log("   ℹ️ Banco já existe.", "aviso")

        query_user = f"USE [master]; IF NOT EXISTS (SELECT * FROM sys.server_principals WHERE name = '{nome_banco}') BEGIN CREATE LOGIN [{nome_banco}] WITH PASSWORD = '{senha_user}', CHECK_POLICY = OFF; END USE [{nome_banco}]; IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = '{nome_banco}') BEGIN CREATE USER [{nome_banco}] FOR LOGIN [{nome_banco}]; END ELSE BEGIN ALTER USER [{nome_banco}] WITH LOGIN = [{nome_banco}]; END ALTER ROLE [db_owner] ADD MEMBER [{nome_banco}];"
        try:
            subprocess.run(f'sqlcmd -S localhost {auth_args} -Q "{query_user}"', shell=True, check=True)
            self.log("   ✔ Usuário SQL Configurado.", "sucesso")
        except: self.log("   ❌ Erro usuário SQL.", "erro")

    def verificar_servicos(self, tipo_banco):
        service = "FirebirdServerDefaultInstance" if tipo_banco == "FIREBIRD" else "MSSQLSERVER"
        try:
            res = subprocess.run(f"sc query {service}", shell=True, capture_output=True, text=True)
            if "RUNNING" in res.stdout: self.log(f"✔ Serviço {service} ON.", "sucesso")
            else: self.log(f"⚠️ Serviço {service} OFF!", "erro")
        except: pass

    def remover_ie(self):
        self.log("🗑️ Removendo IE...", "info")
        try: subprocess.run("dism /online /Remove-Capability /CapabilityName:Browser.InternetExplorer~~~~0.0.11.0", shell=True, check=False, timeout=60)
        except: pass

    def criar_mklink_rede(self, link_local, alvo_rede):
        if os.path.exists(link_local):
            try:
                if os.path.islink(link_local): os.remove(link_local)
                else: shutil.rmtree(link_local)
            except: pass
        self.log(f"   🔗 MKLINK: {link_local} -> {alvo_rede}")
        try:
            subprocess.run(f'mklink /D "{link_local}" "{alvo_rede}"', shell=True, check=True, stdout=subprocess.DEVNULL)
            self.log("   ✔ Link criado.", "sucesso")
        except: self.log("   ❌ Erro Link.", "erro")

    def criar_atalho_powershell(self, alvo_exe, caminho_lnk, work_dir):
        ps = f'$s=(New-Object -COM WScript.Shell).CreateShortcut("{caminho_lnk}");$s.TargetPath="{alvo_exe}";$s.WorkingDirectory="{work_dir}";$s.Save()'
        try: subprocess.run(["powershell", "-Command", ps], check=True)
        except: pass