# Recursos avançados do TechDiagnóstico

O aplicativo básico funciona sem este guia. Esta configuração é para quem vai administrar um servidor que compartilha casos confirmados e oferece pesquisa integrada na internet.

## Arquivos usados

- `techdiagnostico_servidor.py`: servidor e banco de casos compartilhados.
- `techdiagnostico_config.json`: endereço do servidor e token para o aplicativo.
- `techdiagnostico_requirements.txt`: bibliotecas do servidor.
- `INICIAR_SERVIDOR_WINDOWS.bat`: inicia um servidor apenas neste computador, sem pesquisa integrada.

Para configurar o aplicativo compilado, copie `techdiagnostico_config.json` para a **mesma pasta** de `TechDiagnostico.exe`. Quem usa somente a versão simples não precisa desse arquivo.

## Teste no próprio computador

Abra PowerShell na pasta `avancado` do pacote extraído, instale as bibliotecas e inicie o servidor:

```powershell
py -m pip install -r techdiagnostico_requirements.txt
py -m uvicorn techdiagnostico_servidor:app --host 127.0.0.1 --port 8000
```

Em `techdiagnostico_config.json`, use:

```json
{
  "server_url": "http://127.0.0.1:8000",
  "app_token": ""
}
```

Deixe o terminal do servidor aberto e abra o aplicativo. Cada consulta será enviada ao servidor; avaliações marcadas como resolvidas passam a compor as sugestões para sintomas semelhantes. O arquivo `casos_compartilhados.db` será criado na pasta do servidor.

## Pesquisa integrada à interface

Defina sua chave de API **somente no terminal do servidor**, antes de iniciá-lo:

```powershell
$env:OPENAI_API_KEY = 'sua-chave-de-api'
py -m uvicorn techdiagnostico_servidor:app --host 127.0.0.1 --port 8000
```

O botão de pesquisa passará a consultar o servidor e mostrar resultados com links dentro do aplicativo. A API exige internet e pode gerar cobrança na conta usada. Não coloque a chave de API no arquivo de configuração distribuído com o `.exe`.

## Vários computadores

Para um teste controlado na mesma rede, execute o servidor com `--host 0.0.0.0`. Configure `TECH_ADMIN_TOKEN` no ambiente do servidor e informe o mesmo token em `app_token` na configuração de cada cliente. Substitua `127.0.0.1` pelo endereço IP do computador que hospeda o servidor. Libere acesso à porta conforme a configuração da rede.

Para acesso pela internet, o grupo precisará hospedar o serviço com HTTPS e controle de acesso adequado. O servidor iniciado apenas no seu computador não torna o banco central acessível automaticamente para pessoas fora da rede.

## Limites atuais

- Cada computador também mantém seu histórico local em `%APPDATA%\TechDiagnostico`.
- Se o servidor estiver fora do ar, o retorno fica salvo localmente e não é sincronizado depois.
- Casos confirmados ajudam a sugerir resultados semelhantes; as regras do sistema não são modificadas automaticamente.
- A pesquisa básica abre o navegador quando não há servidor configurado. Com servidor e chave, a pesquisa aparece dentro do aplicativo.
