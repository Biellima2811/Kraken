Kraken_V1/
│
├── main.py                  # Ponto de entrada (Inicia a GUI)
├── config.py                # Constantes globais (Caminhos padrão Fortes, etc)
│
├── gui/                     # Interface Gráfica (Radiance Theme)
│   ├── __init__.py
│   ├── main_window.py       # A tela principal com as abas de servidores
│   └── components.py        # Botões e Inputs reutilizáveis
│
└── core/                    # O Cérebro
    ├── __init__.py
    ├── commander.py         # Gerencia a conexão WinRM (O "Tentáculo Mestre")
    │
    └── services/            # Módulos específicos (baseados no Loky)
        ├── firebird.py      # Comandos de GFIX/GBAK adaptados
        ├── mssql.py         # Comandos de SQLCMD adaptados
        └── system.py        # MKLINK, Cópia de arquivos, Instalação