import winrm
from requests.exceptions import ConnectTimeout, ConnectionError

class RemoteCommander:
    def __init__(self, ip, usuario, senha):
        self.ip = ip
        self.usuario = usuario
        self.senha = senha
        self.session = None

    def conectar(self):
        """
        Estabelece a sessão WinRM.
        Nota: O WinRM não 'conecta' na hora (é stateless), mas aqui configuramos o cliente.
        """
        print(f"🔌 Configurando sessão WinRM para {self.ip}...")
        try:
            self.session = winrm.Session(
                f'http://{self.ip}:5985/wsman', 
                auth=(self.usuario, self.senha), 
                transport='ntlm',
                server_cert_validation='ignore'
            )
            return True
        except Exception as e:
            print(f"❌ Erro ao configurar sessão: {e}")
            return False

    def executar_powershell(self, comando):
        """
        Envia um script PowerShell e retorna o resultado.
        """
        if not self.session:
            return {"status": "erro", "saida": "Sessão não inicializada."}

        try:
            # Executa o comando remoto
            print(f"📡 Enviando comando para {self.ip}...")
            resultado = self.session.run_ps(comando)
            
            # Decodifica a saída (WinRM retorna bytes)
            std_out = resultado.std_out.decode('utf-8', errors='ignore').strip()
            std_err = resultado.std_err.decode('utf-8', errors='ignore').strip()
            
            if resultado.status_code == 0:
                return {"status": "sucesso", "saida": std_out}
            else:
                return {"status": "erro", "saida": f"Erro (Exit Code {resultado.status_code}): {std_err}"}

        except (ConnectTimeout, ConnectionError):
            return {"status": "erro", "saida": f"Timeout: O servidor {self.ip} não respondeu (WinRM porta 5985)."}
        except Exception as e:
            return {"status": "erro", "saida": f"Exceção WinRM: {str(e)}"}

    def testar_conexao(self):
        """
        Roda um comando simples (hostname) para ver se as credenciais funcionam.
        """
        res = self.executar_powershell("hostname")
        if res['status'] == 'sucesso':
            return True, f"Conectado! Hostname: {res['saida']}"
        else:
            return False, res['saida']