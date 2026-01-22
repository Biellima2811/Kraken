import time

class FirebirdManager:
    def __init__(self, remote_comander):
        self.remote = remote_comander
    
    def verificar_instalacao(self):
        # Verifica se o Firebird está rodando
        res = self.remote.executar_powershell("Get-Service Firebird* | Select-Object Status, Name")
        if "Running" in res['saida']:
            return True, "Serviço Firebird está RODANDO"
        return False, "⚠️ -  Serviço Firebird NÃO encontrado ou parado!"
    