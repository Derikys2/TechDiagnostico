"""Sistema especialista com interface Tkinter, SQLite e resumo em pandas.

Instale: python -m pip install pandas
Execute: python techdiagnostico_interface.py
"""

import sqlite3
import tkinter as tk
import json
import os
import re
import shutil
import sys
import threading
import urllib.error
import urllib.request
from urllib.parse import quote_plus
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

import pandas as pd


PASTA_APLICATIVO = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
PASTA_DADOS = Path(os.getenv("APPDATA", str(Path.home()))) / "TechDiagnostico"
PASTA_DADOS.mkdir(parents=True, exist_ok=True)
BANCO = PASTA_DADOS / "techdiagnostico.db"
# Reaproveita o histórico das versões anteriores executadas pelo Python.
BANCO_ANTIGO = PASTA_APLICATIVO / "techdiagnostico.db"
if not BANCO.exists() and BANCO_ANTIGO.is_file() and BANCO_ANTIGO != BANCO:
    shutil.copy2(BANCO_ANTIGO, BANCO)


def carregar_configuracao():
    arquivo = PASTA_APLICATIVO / "techdiagnostico_config.json"
    if not arquivo.exists():
        return {}
    try:
        with arquivo.open("r", encoding="utf-8") as entrada:
            dados = json.load(entrada)
        return dados if isinstance(dados, dict) else {}
    except (OSError, ValueError):
        return {}


CONFIG = carregar_configuracao()
SERVIDOR = os.getenv("TECH_SERVER_URL", CONFIG.get("server_url", "")).rstrip("/")
TOKEN = os.getenv("TECH_APP_TOKEN", CONFIG.get("app_token", ""))


def chamar_servidor(rota, dados):
    if not SERVIDOR:
        raise ConnectionError("Servidor compartilhado não configurado")
    corpo = json.dumps(dados).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if TOKEN:
        headers["X-App-Token"] = TOKEN
    pedido = urllib.request.Request(SERVIDOR + rota, data=corpo,
                                    headers=headers, method="POST")
    try:
        with urllib.request.urlopen(pedido, timeout=35) as resposta:
            return json.load(resposta)
    except urllib.error.HTTPError as erro:
        try:
            detalhe = json.load(erro).get("detail", erro.reason)
        except (ValueError, OSError):
            detalhe = erro.reason
        raise ConnectionError(f"Servidor: {detalhe}") from erro

PERGUNTAS = {
    "liga": "O computador liga?",
    "ventoinhas": "As ventoinhas funcionam?",
    "imagem": "O monitor mostra imagem?",
    "tomada_funciona": "Você confirmou que a tomada funciona com outro aparelho?",
    "cabo_forca_solto": "O cabo de energia parece solto ou mal encaixado?",
    "filtro_desligado": "O filtro de linha ou a régua de tomadas está desligado?",
    "monitor_ligado": "A luz de energia do monitor está acesa?",
    "cabo_video_solto": "O cabo de vídeo parece solto ou mal encaixado?",
    "entrada_monitor_errada": "A entrada selecionada no monitor é diferente da usada pelo cabo?",
    "outro_monitor_funciona": "Outro monitor ou TV mostra imagem com esse computador?",
    "temperatura_alta": "A temperatura parece alta?",
    "desliga": "O computador desliga sozinho?",
    "lento": "O computador está lento?",
    "espaco_baixo": "O armazenamento está quase cheio?",
    "arquivos_corrompidos": "Há arquivos corrompidos ou ilegíveis?",
    "inicio_lento": "O sistema demora muito a iniciar?",
    "tela_azul": "Aparece tela azul?",
    "trava_reinicia": "Há travamentos ou reinicializações frequentes?",
    "propagandas": "Aparecem propagandas inesperadas?",
    "programas_estranhos": "Há programas desconhecidos instalados?",
    "falha_em_jogos": "O problema ocorre durante jogos ou programas pesados?",
    "falhas_graficas": "Há falhas gráficas ou tela preta durante o uso?",
    "internet": "O computador consegue acessar a internet?",
    "outros_sem_internet": "Outros aparelhos também estão sem internet nesta rede?",
    "cabo_rede_solto": "Se você usa cabo de rede, ele parece solto?",
    "wifi_desligado": "O Wi-Fi está desligado no computador?",
    "sem_som": "O computador está sem som?",
    "som_mudo": "O volume está no mudo ou muito baixo?",
    "audio_solto": "O cabo do fone ou da caixa de som está solto?",
    "usb_falha": "Algum mouse, teclado ou outro dispositivo USB parou de funcionar?",
    "usb_outra_porta": "Você testou e ele funcionou em outra porta USB?",
}

PERGUNTAS_ENERGIA = ("tomada_funciona", "cabo_forca_solto", "filtro_desligado")
PERGUNTAS_VIDEO = ("monitor_ligado", "cabo_video_solto", "entrada_monitor_errada",
                   "outro_monitor_funciona")
PERGUNTAS_USO = ("temperatura_alta", "desliga", "lento", "espaco_baixo",
                 "arquivos_corrompidos", "inicio_lento", "tela_azul", "trava_reinicia",
                 "propagandas", "programas_estranhos", "falha_em_jogos", "falhas_graficas")
PERGUNTAS_PERIFERICOS = ("internet", "sem_som", "usb_falha")

# Base de conhecimento: nome, condições, explicação e recomendação.
REGRAS = [
    ("Possível mau contato no cabo de energia", {"liga": False, "cabo_forca_solto": True},
     "O computador não liga e foi observado que o cabo de energia parece solto.",
     "Desligue da tomada e encaixe novamente o cabo externo, sem abrir a fonte."),
    ("Possível falta de energia na tomada", {"liga": False, "tomada_funciona": False},
     "A tomada ainda não foi confirmada como funcional.",
     "Teste a tomada com outro aparelho que você saiba estar funcionando."),
    ("Possível filtro de linha desligado", {"liga": False, "filtro_desligado": True},
     "O filtro de linha desligado pode impedir a chegada de energia ao computador.",
     "Verifique o botão do filtro de linha e seu cabo de energia."),
    ("Possível problema na alimentação elétrica", {"liga": False, "ventoinhas": False},
     "Não há sinais de inicialização nem movimento das ventoinhas.",
     "Confira tomada, cabo e filtro de linha. Nunca abra a fonte."),
    ("Possível mau contato no cabo de vídeo", {"liga": True, "imagem": False,
                                               "cabo_video_solto": True},
     "O computador liga, não mostra imagem e o cabo de vídeo parece solto.",
     "Desligue monitor e computador e recoloque o cabo de vídeo nas duas pontas."),
    ("Possível entrada incorreta no monitor", {"liga": True, "imagem": False,
                                                "entrada_monitor_errada": True},
     "A entrada selecionada no monitor não corresponde à conexão usada.",
     "Selecione no monitor a entrada HDMI ou DisplayPort onde o cabo está conectado."),
    ("Possível falta de energia no monitor", {"liga": True, "imagem": False,
                                               "monitor_ligado": False},
     "O computador liga, mas a luz de energia do monitor não está acesa.",
     "Confira tomada, botão e cabo de energia externo do monitor."),
    ("Possível falha no monitor ou no cabo usado", {"liga": True, "imagem": False,
                                                    "outro_monitor_funciona": True},
     "Outro monitor ou TV apresentou imagem com o mesmo computador.",
     "Verifique o monitor original e seu cabo de vídeo; teste outro cabo se possível."),
    ("Possível problema de vídeo ou monitor", {"liga": True, "ventoinhas": True, "imagem": False},
     "O computador dá sinais de energia, mas não apresenta imagem.",
     "Confira monitor, entrada selecionada e cabo de vídeo."),
    ("Possível superaquecimento", {"temperatura_alta": True, "desliga": True},
     "A temperatura alta coincide com desligamentos inesperados.",
     "Verifique a ventilação e as ventoinhas. Se persistir, procure um técnico."),
    ("Possível falta de espaço", {"lento": True, "espaco_baixo": True},
     "O armazenamento quase cheio pode contribuir para a lentidão.",
     "Libere espaço removendo arquivos desnecessários."),
    ("Possível falha no SSD ou HD", {"arquivos_corrompidos": True, "inicio_lento": True},
     "Arquivos corrompidos e inicialização demorada podem indicar falha de armazenamento.",
     "Faça backup dos arquivos importantes e avalie a saúde do SSD ou HD."),
    ("Possível falha na memória RAM", {"tela_azul": True, "trava_reinicia": True},
     "Telas azuis acompanhadas de travamentos podem ter relação com a memória.",
     "Execute um diagnóstico de memória e consulte um técnico se houver erros."),
    ("Possível software indesejado", {"propagandas": True, "programas_estranhos": True},
     "Propagandas e programas desconhecidos podem indicar software indesejado.",
     "Faça uma verificação completa com uma ferramenta de segurança confiável."),
    ("Possível problema no driver de vídeo",
     {"falha_em_jogos": True, "falhas_graficas": True, "temperatura_alta": False},
     "Há falhas gráficas durante jogos, sem alta temperatura relatada.",
     "Consulte o site oficial do fabricante para atualizar o driver de vídeo."),
    ("Possível problema no roteador ou na rede", {"internet": False,
                                                   "outros_sem_internet": True},
     "Outros aparelhos também estão sem conexão na mesma rede.",
     "Confira o roteador e o serviço de internet; reinicie o roteador se necessário."),
    ("Possível mau contato no cabo de rede", {"internet": False,
                                               "cabo_rede_solto": True},
     "Foi observado que o cabo de rede parece solto.",
     "Reencaixe o cabo nas duas pontas e confira se a conexão voltou."),
    ("Wi-Fi possivelmente desligado", {"internet": False, "wifi_desligado": True},
     "O Wi-Fi do computador está desligado.",
     "Ative o Wi-Fi e verifique se a rede aparece na lista de conexões."),
    ("Possível problema de conexão", {"internet": False},
     "O sistema funciona, mas não acessa a internet.",
     "Teste a rede em outro aparelho e confira Wi-Fi, cabo e roteador."),
    ("Volume desativado ou muito baixo", {"sem_som": True, "som_mudo": True},
     "O computador está sem som e o volume está mudo ou muito baixo.",
     "Aumente o volume do sistema e do aplicativo e desative o mudo."),
    ("Possível mau contato no cabo de áudio", {"sem_som": True, "audio_solto": True},
     "O fone ou a caixa de som parece estar mal conectado.",
     "Reencaixe o conector externo ou teste outra saída de áudio."),
    ("Possível problema na saída de áudio", {"sem_som": True},
     "O computador está sem som e a causa não foi confirmada pelas perguntas.",
     "Confira o dispositivo de saída escolhido no sistema e teste outro fone."),
    ("Possível mau contato na porta USB", {"usb_falha": True,
                                            "usb_outra_porta": True},
     "O dispositivo funciona em outra porta, sugerindo problema na primeira conexão.",
     "Use a porta que funciona e confira visualmente a outra, sem forçar o conector."),
    ("Falha USB ainda sem causa confirmada", {"usb_falha": True,
                                              "usb_outra_porta": False},
     "O dispositivo ainda não foi confirmado como funcional em outra porta.",
     "Teste outra porta USB e, se possível, outro computador."),
]

GENERICAS = {
    "Possível problema na alimentação elétrica": {
        "Possível mau contato no cabo de energia", "Possível falta de energia na tomada",
        "Possível filtro de linha desligado"},
    "Possível problema de vídeo ou monitor": {
        "Possível mau contato no cabo de vídeo", "Possível entrada incorreta no monitor",
        "Possível falta de energia no monitor", "Possível falha no monitor ou no cabo usado"},
    "Possível problema de conexão": {
        "Possível problema no roteador ou na rede", "Possível mau contato no cabo de rede",
        "Wi-Fi possivelmente desligado"},
    "Possível problema na saída de áudio": {
        "Volume desativado ou muito baixo", "Possível mau contato no cabo de áudio"},
}


def conectar():
    # O arquivo do banco é criado automaticamente na primeira conexão.
    conexao = sqlite3.connect(BANCO)
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def criar_tabelas():
    with conectar() as conexao:
        conexao.executescript("""
            CREATE TABLE IF NOT EXISTS consultas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_hora TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS respostas (
                consulta_id INTEGER NOT NULL,
                sintoma TEXT NOT NULL,
                valor INTEGER NOT NULL CHECK (valor IN (0, 1)),
                PRIMARY KEY (consulta_id, sintoma),
                FOREIGN KEY (consulta_id) REFERENCES consultas(id)
            );
            CREATE TABLE IF NOT EXISTS diagnosticos (
                consulta_id INTEGER NOT NULL,
                nome TEXT NOT NULL,
                PRIMARY KEY (consulta_id, nome),
                FOREIGN KEY (consulta_id) REFERENCES consultas(id)
            );
            CREATE TABLE IF NOT EXISTS retornos (
                consulta_id INTEGER NOT NULL,
                nome TEXT NOT NULL,
                resolvido INTEGER NOT NULL CHECK (resolvido IN (0, 1)),
                PRIMARY KEY (consulta_id, nome),
                FOREIGN KEY (consulta_id, nome) REFERENCES diagnosticos(consulta_id, nome)
            );
        """)


def diagnosticar(fatos):
    encontrados = [regra for regra in REGRAS if all(
        chave in fatos and fatos[chave] is esperado
        for chave, esperado in regra[1].items()
    )]
    nomes = {regra[0] for regra in encontrados}
    return [regra for regra in encontrados if not (
        regra[0] in GENERICAS and nomes.intersection(GENERICAS[regra[0]])
    )]


def salvar_consulta(fatos, encontrados):
    """Salva consulta, respostas e diagnósticos numa única transação."""
    with conectar() as conexao:
        cursor = conexao.execute(
            "INSERT INTO consultas (data_hora) VALUES (?)",
            (datetime.now().astimezone().isoformat(timespec="seconds"),),
        )
        consulta_id = cursor.lastrowid
        conexao.executemany(
            "INSERT INTO respostas (consulta_id, sintoma, valor) VALUES (?, ?, ?)",
            [(consulta_id, chave, int(valor)) for chave, valor in fatos.items()],
        )
        conexao.executemany(
            "INSERT INTO diagnosticos (consulta_id, nome) VALUES (?, ?)",
            [(consulta_id, regra[0]) for regra in encontrados] or
            [(consulta_id, "Inconclusivo")],
        )
    return consulta_id


def resumo_historico():
    with conectar() as conexao:
        historico = pd.read_sql_query("""
            SELECT c.id, c.data_hora, d.nome AS diagnostico
            FROM consultas AS c
            JOIN diagnosticos AS d ON d.consulta_id = c.id
            ORDER BY c.id DESC, d.nome
        """, conexao)
        total = conexao.execute("SELECT COUNT(*) FROM consultas").fetchone()[0]
    return historico, total


def salvar_retorno(consulta_id, nome, resolvido):
    with conectar() as conexao:
        conexao.execute(
            "INSERT INTO retornos (consulta_id, nome, resolvido) VALUES (?, ?, ?) "
            "ON CONFLICT(consulta_id, nome) DO UPDATE SET resolvido = excluded.resolvido",
            (consulta_id, nome, int(resolvido)),
        )


class Aplicacao(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TechDiagnóstico | Sistema especialista")
        self.geometry("780x660")
        self.minsize(650, 500)
        self.etapa = "energia"
        self.respostas = {}
        self.opcoes = {}
        self.ids_remotos = {}
        self.consulta_atual = None

        topo = ttk.Frame(self, padding=16)
        topo.pack(fill="x")
        ttk.Label(topo, text="TechDiagnóstico", font=("Arial", 20, "bold")).pack(anchor="w")
        ttk.Label(topo, text="Orientação inicial baseada em regras, sujeita a outras causas.").pack(anchor="w")

        corpo = ttk.Frame(self, padding=(16, 0, 16, 0))
        corpo.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(corpo, highlightthickness=0)
        barra = ttk.Scrollbar(corpo, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=barra.set)
        barra.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.conteudo = ttk.Frame(self.canvas, padding=(4, 4, 12, 4))
        self.janela_canvas = self.canvas.create_window((0, 0), window=self.conteudo, anchor="nw")
        self.conteudo.bind("<Configure>", lambda _: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.janela_canvas, width=e.width))

        rodape = ttk.Frame(self, padding=16)
        rodape.pack(fill="x")
        self.botao_continuar = ttk.Button(rodape, text="Continuar", command=self.continuar)
        self.botao_continuar.pack(side="right")
        ttk.Button(rodape, text="Ver histórico", command=self.ver_historico).pack(side="left")
        ttk.Button(rodape, text="Nova consulta", command=self.nova_consulta).pack(side="left", padx=8)
        self.mostrar_perguntas(("liga", "ventoinhas"), "1. Energia")

    def limpar(self):
        for widget in self.conteudo.winfo_children():
            widget.destroy()
        self.canvas.yview_moveto(0)

    def mostrar_perguntas(self, chaves, titulo):
        self.limpar()
        ttk.Label(self.conteudo, text=titulo, font=("Arial", 15, "bold")).pack(anchor="w", pady=8)
        self.opcoes = {}
        for chave in chaves:
            bloco = ttk.LabelFrame(self.conteudo, text=PERGUNTAS[chave], padding=10)
            bloco.pack(fill="x", pady=6)
            variavel = tk.StringVar(value="")
            self.opcoes[chave] = variavel
            ttk.Radiobutton(bloco, text="Sim", variable=variavel, value="sim").pack(side="left", padx=10)
            ttk.Radiobutton(bloco, text="Não", variable=variavel, value="nao").pack(side="left", padx=10)
        self.botao_continuar.configure(state="normal", text="Continuar")

    def continuar(self):
        if not all(variavel.get() for variavel in self.opcoes.values()):
            messagebox.showwarning("Respostas pendentes", "Responda todas as perguntas desta etapa.")
            return
        self.respostas.update({chave: var.get() == "sim" for chave, var in self.opcoes.items()})
        if self.etapa == "energia":
            if not self.respostas["liga"]:
                self.etapa = "energia_detalhes"
                self.mostrar_perguntas(PERGUNTAS_ENERGIA, "2. Verificações de energia")
                return
            self.etapa = "imagem"
            self.mostrar_perguntas(("imagem",), "2. Imagem")
        elif self.etapa == "imagem":
            if not self.respostas["imagem"]:
                self.etapa = "video_detalhes"
                self.mostrar_perguntas(PERGUNTAS_VIDEO, "3. Monitor e cabos")
                return
            self.etapa = "sintomas"
            self.mostrar_perguntas(PERGUNTAS_USO, "3. Sintomas durante o uso")
        elif self.etapa == "sintomas":
            self.etapa = "perifericos"
            self.mostrar_perguntas(PERGUNTAS_PERIFERICOS, "4. Internet, áudio e USB")
        elif self.etapa == "perifericos":
            detalhes = []
            if not self.respostas["internet"]:
                detalhes.extend(("outros_sem_internet", "cabo_rede_solto", "wifi_desligado"))
            if self.respostas["sem_som"]:
                detalhes.extend(("som_mudo", "audio_solto"))
            if self.respostas["usb_falha"]:
                detalhes.append("usb_outra_porta")
            if detalhes:
                self.etapa = "perifericos_detalhes"
                self.mostrar_perguntas(detalhes, "5. Verificações específicas")
            else:
                self.mostrar_resultado()
        else:
            self.mostrar_resultado()

    def mostrar_resultado(self):
        encontrados = diagnosticar(self.respostas)
        try:
            codigo = salvar_consulta(self.respostas, encontrados)
        except sqlite3.Error as erro:
            messagebox.showerror("Erro ao salvar", str(erro))
            return
        self.etapa = "resultado"
        self.consulta_atual = codigo
        self.limpar()
        ttk.Label(self.conteudo, text=f"Resultado da consulta #{codigo}",
                  font=("Arial", 15, "bold")).pack(anchor="w", pady=8)
        if not encontrados:
            ttk.Label(self.conteudo, text="Resultado inconclusivo. Procure um técnico para avaliar o computador.",
                      wraplength=680).pack(anchor="w", pady=8)
        for nome, _, explicacao, recomendacao in encontrados:
            bloco = ttk.LabelFrame(self.conteudo, text=nome, padding=12)
            bloco.pack(fill="x", pady=8)
            ttk.Label(bloco, text=f"Motivo: {explicacao}", wraplength=650).pack(anchor="w", pady=4)
            ttk.Label(bloco, text=f"Orientação: {recomendacao}", wraplength=650).pack(anchor="w", pady=4)
            botoes = ttk.Frame(bloco)
            botoes.pack(anchor="w", pady=5)
            ttk.Label(botoes, text="Depois de testar, essa orientação resolveu?").pack(side="left")
            ttk.Button(botoes, text="Sim", command=lambda n=nome: self.confirmar(n, True)).pack(side="left", padx=5)
            ttk.Button(botoes, text="Não", command=lambda n=nome: self.confirmar(n, False)).pack(side="left")
        if SERVIDOR:
            ttk.Label(self.conteudo, text="Casos semelhantes confirmados:",
                      font=("Arial", 11, "bold")).pack(anchor="w", pady=(10, 3))
            self.texto_compartilhado = ttk.Label(self.conteudo, text="Consultando servidor...",
                                                wraplength=690)
            self.texto_compartilhado.pack(anchor="w")
            for nome, *_ in encontrados:
                self.em_thread(lambda n=nome, f=self.respostas.copy(), c=codigo:
                               self.enviar_caso(c, n, f))
            self.em_thread(lambda f=self.respostas.copy(): self.consultar_casos(f))
        ttk.Button(self.conteudo, text="Pesquisar soluções na internet",
                   command=self.pesquisar_web).pack(anchor="w", pady=14)
        self.botao_continuar.configure(state="disabled")

    def em_thread(self, tarefa):
        threading.Thread(target=tarefa, daemon=True).start()

    def enviar_caso(self, consulta_id, nome, fatos):
        try:
            remoto = chamar_servidor("/casos", {"sintomas": fatos, "sugestao": nome})
            self.after(0, lambda: self.ids_remotos.__setitem__((consulta_id, nome), remoto["id"]))
            with conectar() as conexao:
                retorno = conexao.execute(
                    "SELECT resolvido FROM retornos WHERE consulta_id = ? AND nome = ?",
                    (consulta_id, nome),
                ).fetchone()
            if retorno:
                self.enviar_retorno(remoto["id"], bool(retorno[0]))
        except (ConnectionError, OSError, ValueError):
            pass  # O histórico local continua disponível.

    def consultar_casos(self, fatos):
        try:
            itens = chamar_servidor("/sugestoes", {"sintomas": fatos, "sugestao": "Consulta"})
            texto = "; ".join(f"{item['sugestao']} ({item['casos_confirmados_semelhantes']} casos)"
                              for item in itens) or "Nenhum caso semelhante confirmado ainda."
        except (ConnectionError, OSError, ValueError) as erro:
            texto = f"Não foi possível consultar casos compartilhados: {erro}"
        self.after(0, lambda: self.texto_compartilhado.configure(text=texto)
                   if self.texto_compartilhado.winfo_exists() else None)

    def confirmar(self, nome, resolveu):
        consulta_id = self.consulta_atual
        try:
            salvar_retorno(consulta_id, nome, resolveu)
        except sqlite3.Error as erro:
            messagebox.showerror("Erro ao registrar retorno", str(erro))
            return
        remoto = self.ids_remotos.get((consulta_id, nome))
        if remoto:
            self.em_thread(lambda: self.enviar_retorno(remoto, resolveu))
            messagebox.showinfo("Retorno registrado", "Obrigado! A avaliação foi salva.")
        else:
            messagebox.showinfo("Retorno registrado", "Sua avaliação foi salva no histórico.")

    def enviar_retorno(self, remoto, resolveu):
        try:
            chamar_servidor(f"/casos/{remoto}/retorno", {"resolvido": resolveu})
        except (ConnectionError, OSError, ValueError):
            pass

    def pesquisar_web(self):
        sintomas = [PERGUNTAS[chave] for chave, valor in self.respostas.items()
                    if valor and chave in PERGUNTAS and chave not in ("liga", "imagem", "ventoinhas")]
        if not sintomas:
            sintomas = ["computador não liga" if not self.respostas.get("liga", True)
                        else "computador liga mas não mostra imagem"]
        if SERVIDOR:
            self.em_thread(lambda: self.executar_pesquisa(sintomas[:8]))
        else:
            # A pesquisa abre no navegador e não exige conta, chave ou servidor.
            consulta = "como resolver problema computador " + " ".join(sintomas[:4])
            webbrowser.open("https://www.google.com/search?q=" + quote_plus(consulta))

    def executar_pesquisa(self, sintomas):
        try:
            texto = chamar_servidor("/pesquisar", {"sintomas": sintomas})["texto"]
        except (ConnectionError, OSError, ValueError) as erro:
            texto = f"Não foi possível pesquisar: {erro}"
        self.after(0, lambda: self.mostrar_pesquisa(texto))

    def mostrar_pesquisa(self, texto):
        janela = tk.Toplevel(self)
        janela.title("Orientações pesquisadas")
        janela.geometry("770x530")
        area = tk.Text(janela, wrap="word", padx=14, pady=14)
        area.pack(fill="both", expand=True)
        area.insert("1.0", texto)
        for indice, item in enumerate(re.finditer(r"https?://[^\s<>]+", texto)):
            endereco = item.group().rstrip(".,);]")
            etiqueta = f"link_{indice}"
            area.tag_add(etiqueta, f"1.0 + {item.start()} chars",
                         f"1.0 + {item.start() + len(endereco)} chars")
            area.tag_configure(etiqueta, foreground="blue", underline=True)
            area.tag_bind(etiqueta, "<Button-1>",
                          lambda _evento, url=endereco: webbrowser.open(url))
        area.configure(state="disabled")

    def nova_consulta(self):
        self.etapa = "energia"
        self.respostas = {}
        self.ids_remotos = {}
        self.mostrar_perguntas(("liga", "ventoinhas"), "1. Energia")

    def ver_historico(self):
        try:
            historico, total = resumo_historico()
        except (sqlite3.Error, pd.errors.DatabaseError) as erro:
            messagebox.showerror("Erro no histórico", str(erro))
            return
        janela = tk.Toplevel(self)
        janela.title("Histórico de consultas")
        janela.geometry("780x470")
        ttk.Label(janela, text=f"Consultas realizadas: {total}",
                  font=("Arial", 13, "bold"), padding=12).pack(anchor="w")
        if historico.empty:
            ttk.Label(janela, text="Ainda não há consultas registradas.", padding=12).pack(anchor="w")
            return
        contagem = historico["diagnostico"].value_counts()
        resumo = "Diagnósticos mais registrados: " + "; ".join(
            f"{nome}: {quantidade}" for nome, quantidade in contagem.head(3).items()
        )
        ttk.Label(janela, text=resumo, padding=12, wraplength=740).pack(anchor="w")
        tabela = ttk.Treeview(janela, columns=("id", "data", "diagnostico"), show="headings")
        for coluna, titulo, largura in (("id", "Nº", 60), ("data", "Data", 220),
                                        ("diagnostico", "Diagnóstico", 470)):
            tabela.heading(coluna, text=titulo)
            tabela.column(coluna, width=largura)
        tabela.pack(fill="both", expand=True, padx=12, pady=12)
        for linha in historico.head(200).itertuples(index=False):
            tabela.insert("", "end", values=(linha.id, linha.data_hora, linha.diagnostico))


if __name__ == "__main__":
    criar_tabelas()
    Aplicacao().mainloop()
