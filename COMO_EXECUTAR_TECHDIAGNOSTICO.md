# TechDiagnóstico: guia simples

## Para quem vai usar o programa

Receba o arquivo **`TechDiagnostico.exe`** de quem preparou o aplicativo e abra-o com dois cliques no Windows. Você não precisa instalar Python, bibliotecas ou configurar chave de API e servidor.

Responda às perguntas para ver as orientações. Depois de testá-las, use **Sim** ou **Não** para registrar se funcionaram. O botão **Pesquisar soluções na internet** abre uma pesquisa com os sintomas no navegador. Confira os sites encontrados antes de seguir qualquer instrução.

O histórico fica salvo no seu computador, na pasta `%APPDATA%\TechDiagnostico`. Cada computador possui seu próprio histórico nesta versão simples.

## Para quem vai preparar o `.exe` (uma vez, no Windows)

1. Instale Python no computador que vai criar o executável.
2. Coloque `techdiagnostico_interface.py` e `GERAR_EXE_WINDOWS.bat` na mesma pasta.
3. Abra `GERAR_EXE_WINDOWS.bat` com dois cliques. Ele instala os pacotes necessários, caso faltem, e gera `dist\TechDiagnostico.exe`.
4. Distribua esse `.exe`. Quem o receber não precisa repetir esses passos.

O gerador pode ser executado novamente depois de uma atualização do código.

## Alternativa caso a criação do executável falhe

Abra um terminal na pasta dos arquivos e execute:

```powershell
py -m pip install pandas
py techdiagnostico_interface.py
```

## Recursos opcionais para desenvolvimento

O pacote inclui uma pasta **`avancado`** com `GUIA_RECURSOS_AVANCADOS.md` e os arquivos para compartilhar casos confirmados entre instalações e pesquisar dentro do aplicativo. Essas funções exigem hospedar e configurar um servidor; **não fazem parte da configuração necessária para o usuário comum**. O `.exe` básico funciona sem elas.
