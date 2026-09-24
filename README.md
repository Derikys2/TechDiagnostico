# TechDiagnóstico

Sistema especialista em Python para diagnóstico inicial de problemas comuns em computadores.

O aplicativo apresenta perguntas em uma interface Tkinter, aplica uma base de regras e mostra possíveis causas e orientações. As consultas ficam registradas localmente em SQLite, e o pandas é usado para resumir o histórico.

## Funcionalidades

- Questionário guiado por etapas;
- Diagnósticos básicos de energia, vídeo, temperatura, armazenamento, memória, internet, áudio e USB;
- Verificações simples de cabos e conexões;
- Histórico local de consultas em SQLite;
- Registro indicando se uma orientação resolveu o problema;
- Pesquisa relacionada aos sintomas no navegador;
- Opção avançada de servidor para compartilhar casos confirmados;
- Geração de executável para Windows com PyInstaller.

## Executar pelo Python

```bash
python -m pip install pandas
```

Execute a interface:

```bash
python techdiagnostico_interface.py
```

## Criar o executável no Windows

```powershell
py -m pip install pandas pyinstaller
py -m PyInstaller --noconfirm --clean --onefile --windowed --name TechDiagnostico techdiagnostico_interface.py
```

O executável será criado em `dist\TechDiagnostico.exe`.

## Recursos avançados

O servidor opcional registra casos confirmados compartilhados e permite integrar pesquisa online. Consulte `GUIA_RECURSOS_AVANCADOS.md` antes de usar essa parte.

## Estrutura

| Arquivo | Finalidade |
|---|---|
| `techdiagnostico_interface.py` | Aplicativo desktop |
| `techdiagnostico_servidor.py` | Servidor opcional de casos compartilhados |
| `techdiagnostico_requirements.txt` | Dependências do servidor |
| `GERAR_EXE_WINDOWS.bat` | Geração simplificada do executável |
| `INICIAR_SERVIDOR_WINDOWS.bat` | Inicialização local do servidor |
| `COMO_EXECUTAR_TECHDIAGNOSTICO.md` | Guia para uso comum |
| `GUIA_RECURSOS_AVANCADOS.md` | Configuração dos recursos avançados |

## Observação

Os resultados são orientações iniciais baseadas em regras e não substituem uma análise técnica presencial.
