# 🦑 Kraken Local - Automação de Ambientes Fortes

> Ferramenta de automação para deploy de infraestrutura em ambientes dedicados (SkyOne/Scaling), padronizando a instalação de Banco de Dados (MSSQL/Firebird) e Servidores de Aplicação.

## 🚀 Funcionalidades

### 🏢 Servidor de Banco de Dados
* **Restore Automatizado:**
    * **MSSQL:** Lê metadados do `.bak` (FileListOnly), restaura com nomes lógicos corretos e realoca arquivos MDF/LDF.
    * **Firebird:** Executa `gbak` com parâmetros otimizados.
* **Segurança:**
    * Cria usuários SQL específicos para cada base (padrão `SIGLA_SIS_ID`).
    * Gera senhas fortes automaticamente e as salva em log seguro.
* **Repositório:**
    * Cria a estrutura de pastas padrão (`C:\Fortes`) para ser compartilhada com a rede.
    * Prepara o template do atualizador (CloudUp) já configurado.

### 💻 Servidor de Aplicação
* **Deploy via Rede:**
    * Detecta se os instaladores estão locais; se não, busca automaticamente no compartilhamento do Servidor de Banco.
* **Configuração de Ambiente:**
    * Remove Internet Explorer (DISM).
    * Cria Links Simbólicos (`MKLINK`) para pastas de dados compartilhados (`Usuarios`, `Config`).
* **Atalhos Inteligentes:**
    * Cria atalhos onde o **Destino** é local (Performance) mas o **Iniciar Em** é na rede (Licenciamento).
* **CloudUp Automático:**
    * Instala e configura o `Fortes.ini` e `config.ini` apontando para o servidor de banco correto.

## 🛠️ Como Usar

### Pré-requisitos
Estrutura de pastas necessária na origem (`C:\Kraken`):
- `/Corporativo` (Binários dos sistemas)
- `/Bancos Limpos FB` (.fbk)
- `/Bancos Limpos SQL` (.bak)
- `/CloudUp` (Template do atualizador)

### Compilação (Build)
Para gerar o executável a partir do código fonte (Python + Tkinter):

```bash
# Instale as dependências
pip install ttkthemes pyinstaller

# Gere o binário (ícone opcional)
pyinstaller --noconsole --onefile --icon=assets/kraken.ico --name="Kraken_Local" --collect-all ttkthemes main.py
