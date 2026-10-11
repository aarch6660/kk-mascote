#!/usr/bin/env python3
"""Núcleo Hana: memória, agenda, desktop, modelo falso e recuperação de entrega."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch, Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import chat_dados
import executar
from hana import cerebro, desktop, memoria, modelo, rotina

casos = 0
def verificar(ok, nome):
    global casos
    casos += 1
    assert ok, nome

def rejeita(funcao, nome):
    try:
        funcao()
    except (ValueError, OSError):
        verificar(True, nome)
    else:
        verificar(False, nome)

AGORA = datetime(2026, 10, 11, 10, 0, tzinfo=timezone(timedelta(hours=-3)))
CONTEXTO = {"janela": {"class": "terminal", "title": "teste", "fullscreen": False},
            "musica": {}, "baterias": []}

STUB = '''#!/usr/bin/env python3
import json, os, pathlib, subprocess, sys, time
args = sys.argv[1:]
assert args[:3] == ['-p', '--model', 'claude-haiku-4-5-20251001']
assert args[args.index('--tools')+1] == ''
assert args[args.index('--setting-sources')+1] == ''
assert '--strict-mcp-config' in args and '--no-session-persistence' in args
assert args[args.index('--output-format')+1] == 'json'
formato = json.loads(args[args.index('--json-schema')+1])
prompt = args[args.index('--system-prompt')+1]
entrada = json.loads(args[-1])
log = pathlib.Path('chamadas.jsonl')
quantas = len(log.read_text().splitlines()) if log.exists() else 0
with log.open('a') as f:
    f.write(json.dumps({'cwd':os.getcwd(),'prompt':prompt,'entrada':entrada})+'\\n')
modo = os.environ.get('HANA_STUB', 'ok')
if modo == 'timeout':
    filho = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(60)'])
    pathlib.Path('filho.pid').write_text(str(filho.pid))
    time.sleep(60)
if modo == 'lento': time.sleep(1)
if modo == 'falha' or (modo == 'retry' and quantas == 0): sys.exit(2)
if modo == 'json_ruim': print('oops'); sys.exit(0)
if modo == 'envelope_ruim': print('[]'); sys.exit(0)
if modo == 'texto_ruim': print(json.dumps({'structured_output':{'texto':''}}));sys.exit(0)
if 'resumo' in formato['properties']:
    assert 'Hana Aoi' not in prompt
    resultado = {'resumo':'Gosta de café e tem tarefas pendentes.'}
else:
    assert 'Hana Aoi' in prompt
    resultado = {'texto':'Tá, anotei. Vou cobrar.', 'tom':'irritado', 'emocao':'Birra',
      'roteiro':'nenhum','gesto':'conversa_03','memoria':{'fatos_novos':['Gosta de café'],
      'tarefas_novas':[{'texto':'Lavar a louça amanhã','data':None}],
      'tarefas_concluidas':[],'tarefas_removidas':[],'nome_usuario':'João'}}
    if modo in ('concluir', 'id_invalido'):
        ids = [t['id'] for t in entrada['memoria']['tarefas']]
        resultado['memoria']['tarefas_concluidas'] = ids if modo=='concluir' else ['lavar a louça']
        assert formato['properties']['memoria']['properties']['tarefas_concluidas']['items']['enum'] == ids
print(json.dumps({'structured_output':resultado},ensure_ascii=False))
'''


def testar_memoria(base):
    m = memoria.Memoria(base / "memoria.json")
    verificar(m.ler()["versao"] == 1, "memória nova versionada")
    m.aplicar({"fatos_novos": ["Café", "café", " Chá "] + [f"f{i}" for i in range(62)],
               "nome_usuario": " João ", "tarefas_novas": [
                   {"texto": "Estudar"}, {"texto": "estudar"}, {"texto": "Sair amanhã"},
                   {"texto": "Atrasada", "data": "2026-10-09"},
                   {"texto": "Inválida", "data": "2026-02-30"}]}, AGORA, "lote", 3)
    d = m.ler()
    verificar(len(d["fatos"]) == 60 and d["fatos"][0] == "f2", "60 fatos; antigos removidos")
    verificar(d["nome_usuario"] == "João" and len(d["tarefas"]) == 3, "nome, dedupe e data inválida")
    verificar([t["data"] for t in d["tarefas"]] == ["2026-10-11", "2026-10-12", "2026-10-09"], "hoje/amanhã/atrasada")
    m.aplicar({"tarefas_novas": [{"texto": "Não duplicar"}]}, AGORA, "lote", 3)
    verificar(m.ler() == d, "operação idempotente depois de reinício")
    ident = d["tarefas"][0]["id"]
    m.aplicar({"tarefas_concluidas": [ident, "inexistente"]}, AGORA)
    m.aplicar({"tarefas_concluidas": [ident]}, AGORA)
    verificar(m.ler()["dias"]["2026-10-11"]["tarefas_feitas"] == [ident], "conclusão registrada uma vez")
    verificar(m.ler()["dias"]["2026-10-11"]["mensagens"] == 3, "contagem por lote confirmado")
    verificar(m.contexto(AGORA)["tarefas"][-1]["atrasada"], "pendências antigas permanecem")
    m.aplicar({"tarefas_removidas": [ident]}, AGORA)
    verificar(len(m.ler()["tarefas"]) == 2, "esquecer tarefa")
    m.resumir("Café", "123")
    rejeita(lambda: m.resumir("x" * 1501, "123"), "limite de resumo")
    for data in ("2026-2-01", "2026-02-30", "hoje", True, []):
        verificar(not memoria.data_valida(data), "data estrita")
    verificar(memoria.data_tarefa("amanhã", None, AGORA.replace(month=12, day=31)) == "2027-01-01", "virada do ano")
    verificar(memoria.dia(AGORA.replace(hour=4)) == "2026-10-10", "virada às cinco")
    antes = m.arquivo.read_bytes()
    with patch.object(memoria.os, "replace", side_effect=OSError("falha de disco")):
        rejeita(lambda: m.aplicar({"fatos_novos": ["não gravado"]}, AGORA), "falha atômica")
    verificar(m.arquivo.read_bytes() == antes and not list(base.glob("*.tmp")), "original preservado e temporário limpo")
    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(lambda i: m.aplicar({"tarefas_novas": [{"texto": f"concorrente {i}"}]}, AGORA), range(20)))
    verificar(len(m.ler()["tarefas"]) == 22, "transações concorrentes não perdem tarefas")
    env = dict(os.environ, MASCOTE_HANA_DIR=str(base / "cli"))
    def cli(*args):
        return subprocess.run([sys.executable, str(memoria.__file__), *args], env=env, capture_output=True, text=True)
    r = cli("--tarefa", "Arrumar amanhã")
    tarefa = json.loads(r.stdout)["tarefas"][0]
    verificar(r.returncode == 0 and memoria.data_valida(tarefa["data"]), "CLI adiciona")
    verificar(cli("--concluir", tarefa["id"]).returncode == 0, "CLI conclui")
    verificar(cli("--esquecer", tarefa["id"]).returncode == 0, "CLI esquece")
    verificar(json.loads(cli("--listar").stdout)["tarefas"] == [], "CLI lista")
    verificar(cli("--tarefa", "x", "--data", "2026-02-30").returncode != 0, "CLI recusa data inválida")
    verificar(cli("--concluir", "sem-id").returncode != 0, "CLI recusa ID ausente")


def testar_schema():
    s = modelo.schema()
    verificar(s["properties"]["texto"]["maxLength"] == 400 and not s["additionalProperties"], "schema estrito")
    for chave, lista in modelo.catalogos().items():
        for valor in lista:
            verificar(modelo.validar({"texto": "Oi", chave: valor})[chave] == valor, "enum válido " + chave)
        for ruim in ([], {}, False, 42, "inventado"):
            r = modelo.validar({"texto": "Oi", chave: ruim})
            verificar(r[chave] in lista, "enum inválido descartado")
    for texto in ("", " " * 5, "x" * 401, [], 10, "\x00oi"):
        rejeita(lambda: modelo.validar({"texto": texto}), "texto inválido")
    r = modelo.validar({"texto": " ok ", "memoria": {"fatos_novos": [" fato ", [], ""],
        "tarefas_novas": [{"texto": "boa", "data": None}, {"texto": "ruim", "data": "2026-02-30"}, []],
        "tarefas_concluidas": ["abc", False, {}], "tarefas_removidas": {}, "nome_usuario": []}})
    verificar(r["memoria"] == {"fatos_novos": ["fato"], "tarefas_novas": [{"texto": "boa", "data": None}],
        "tarefas_concluidas": ["abc"], "tarefas_removidas": [], "nome_usuario": None}, "operações inválidas descartadas")
    campo = modelo.schema(["id-real"])["properties"]["memoria"]["properties"]
    verificar(campo["tarefas_concluidas"]["items"]["enum"] == ["id-real"], "schema restringe IDs à memória")
    r = modelo.validar({"texto": "ok", "memoria": {"tarefas_concluidas": ["id-real", "lavar a louça"],
        "tarefas_removidas": ["inexistente"]}}, ["id-real"])
    verificar(r["memoria"]["tarefas_concluidas"] == ["id-real"] and not r["memoria"]["tarefas_removidas"], "texto de tarefa/ID desconhecido descartados")


def testar_rotina(base):
    m = memoria.Memoria(base / "memoria.json")
    agora = [AGORA]
    r = rotina.Rotina(m, lambda: agora[0], lambda a, b: (a+b)/2)
    r.observar(CONTEXTO, AGORA.timestamp())
    verificar(r.motivo(CONTEXTO, {"hidden": True}, True) is None, "bom dia adiado em fullscreen")
    verificar(r.motivo(CONTEXTO, {}, False) == "bom_dia", "bom dia após login sem input")
    r.confirmar("bom_dia")
    r = rotina.Rotina(m, lambda: agora[0], lambda a, b: (a+b)/2)
    verificar(r.motivo(CONTEXTO, {}, True) is None, "reinício não repete bom dia")
    m.aplicar({"tarefas_novas": [{"texto": "Hoje"}, {"texto": "Ontem", "data": "2026-10-10"}]}, AGORA)
    agora[0] += timedelta(minutes=54)
    verificar(r.motivo(CONTEXTO, {}, True) is None, "não cobra antes de 55min sorteados")
    agora[0] += timedelta(minutes=1)
    for estado, contexto in [({"hidden": True}, CONTEXTO), ({"game_mode": True}, CONTEXTO),
            ({}, dict(CONTEXTO, janela={"fullscreen": True}))]:
        verificar(r.motivo(contexto, estado, True) is None, "silêncio em fullscreen/jogo")
    verificar(r.motivo(CONTEXTO, {}, False) is None, "não cobra usuário ocioso")
    verificar(r.motivo(CONTEXTO, {}, True) == "cobranca", "cobra ao sair de fullscreen")
    r.confirmar("cobranca", "c1")
    r.confirmar("cobranca", "c1")
    verificar(all(t["cobrancas"] == 1 for t in m.ler()["tarefas"]), "cobrança registrada por tarefa")
    verificar(r.motivo(CONTEXTO, {}, True) is None, "intervalo depois da cobrança")
    baixo = dict(CONTEXTO, baterias=[{"nome": "BAT0", "nivel": 15, "status": "Discharging"}])
    r.observar(baixo)
    verificar(r.motivo(baixo, {}, True) is None, "bateria respeita intervalo proativo")
    agora[0] += timedelta(minutes=15)
    verificar(r.motivo(baixo, {}, True) == "evento:bateria", "bateria baixa pendente")
    r.confirmar("evento:bateria")
    r.observar(baixo)
    agora[0] += timedelta(minutes=15)
    verificar(r.motivo(baixo, {}, True) is None, "bateria não repete enquanto baixa")
    agora[0] = AGORA.replace(hour=21)
    verificar(r.motivo(CONTEXTO, {}, True) == "pergunta_noite", "pergunta à noite")
    r.confirmar("pergunta_noite")
    agora[0] = AGORA.replace(day=12, hour=1)
    verificar(r.motivo(CONTEXTO, {}, True) != "pergunta_noite", "noite atravessa meia-noite sem repetir")
    agora[0] = AGORA.replace(day=12, hour=5)
    verificar(r.motivo(CONTEXTO, {}, True) == "bom_dia", "novo dia às cinco")
    r.confirmar("bom_dia")
    agora[0] += timedelta(hours=5)
    r.observar(CONTEXTO, agora[0].timestamp())
    verificar(r.motivo(CONTEXTO, {}, True) == "volta", "retorno após ociosidade longa")
    r.confirmar("volta")
    m.aplicar({"tarefas_novas": [{"texto": "Futura", "data": "2026-10-13"}]}, agora[0])
    agora[0] = agora[0].replace(hour=22)
    verificar(r.motivo(CONTEXTO, {}, True) != "pergunta_noite", "não pergunta se amanhã já tem tarefa")


def testar_desktop(base):
    bat = base / "BAT0"
    bat.mkdir(parents=True)
    (bat / "capacity").write_text("14")
    (bat / "status").write_text("Discharging")
    def cmd(args):
        return json.dumps({"class": "kk-mascote-chat", "title": "ignorar", "fullscreen": 0}) if args[0] == "hyprctl" else "Playing\nArtista\nFaixa"
    with patch.object(desktop.shutil, "which", return_value="/fake"), patch.object(desktop, "comando", side_effect=cmd):
        contexto = desktop.coletar(base)
    verificar(contexto["janela"] == {} and contexto["musica"]["faixa"] == "Faixa", "ignora janela própria; música disponível")
    verificar(set(desktop.eventos({}, contexto)) == {"bateria_baixa", "musica_comecou"}, "eventos iniciais")
    verificar(desktop.eventos(contexto, contexto) == [], "não repete transição")
    cheia = dict(contexto, musica={"status": "Paused"}, baterias=[{"nome": "BAT0", "nivel": 100, "status": "Full"}])
    carregando = dict(contexto, baterias=[{"nome": "BAT0", "nivel": 99, "status": "Charging"}])
    verificar(set(desktop.eventos(carregando, cheia)) == {"musica_parou", "bateria_cheia"}, "música parou/bateria cheia")
    verificar(desktop.eventos({}, CONTEXTO) == ["janela"], "mudança de janela exposta")
    (bat / "capacity").write_text("inválido")
    with patch.object(desktop.shutil, "which", return_value=None):
        verificar(desktop.coletar(base) == {"janela": {}, "musica": {}, "baterias": []}, "ausências e bateria inválida toleradas")
    with patch.object(desktop.subprocess, "run", side_effect=subprocess.TimeoutExpired("fake", 0.7)):
        verificar(desktop.comando(["fake"]) == "", "timeout curto tolerado")


def chamadas(pasta):
    return [json.loads(l) for l in (pasta / "chamadas.jsonl").read_text().splitlines()]


def testar_modelo(base, stub):
    rejeita(lambda: modelo.Modelo(pasta=Path(modelo.__file__).parent, binario=stub), "cwd nunca repositório")
    for modo in ("ok", "retry", "falha", "json_ruim", "envelope_ruim", "texto_ruim", "timeout"):
        pasta = base / modo
        m = modelo.Modelo(pasta, binario=str(stub), timeout=0.15 if modo == "timeout" else 2)
        with patch.dict(os.environ, HANA_STUB=modo):
            resposta = m.responder({"motivo": "resposta"})
        falhou = modo not in ("ok", "retry")
        verificar(resposta["texto"] == ("aff, travei. manda de novo" if falhou else "Tá, anotei. Vou cobrar."), "stub " + modo)
        verificar(len(chamadas(pasta)) == (1 if modo == "ok" else 2), "uma repetição " + modo)
        verificar(all(Path(c["cwd"]) == pasta for c in chamadas(pasta)), "cwd isolado " + modo)
        if modo == "timeout":
            pid = int((pasta / "filho.pid").read_text())
            # Um neto terminado pode estar brevemente zombie até ser coletado pelo init.
            stat = Path(f"/proc/{pid}/stat")
            verificar(not stat.exists() or stat.read_text().rsplit(")", 1)[1].split()[0] == "Z", "timeout termina grupo próprio")
    m = modelo.Modelo(base / "resumo", binario=str(stub), timeout=2)
    verificar(m.resumir({"historico": []}) == "Gosta de café e tem tarefas pendentes.", "resumo separado sem persona")
    for modo in ("concluir", "id_invalido"):
        m = modelo.Modelo(base / modo, binario=str(stub), timeout=2)
        with patch.dict(os.environ, HANA_STUB=modo):
            resposta = m.responder({"memoria": {"tarefas": [{"id": "id-real", "texto": "lavar a louça"}]}})
        verificar(resposta["memoria"]["tarefas_concluidas"] == (["id-real"] if modo=="concluir" else []), "cliente valida IDs reais: " + modo)
    persona = base / "persona.md"
    persona.write_text("Hana Aoi PERSONA_ATUAL")
    with patch.object(modelo, "PERSONA", persona):
        verificar("PERSONA_ATUAL" in modelo.sistema(), "persona lida novamente")
    m = modelo.Modelo(base / "cancelar", binario=str(stub), timeout=60)
    with patch.dict(os.environ, HANA_STUB="timeout"), ThreadPoolExecutor() as pool:
        future = pool.submit(m.responder, {})
        limite = time.monotonic()+2
        while not (m.pasta / "filho.pid").exists() and time.monotonic()<limite:
            time.sleep(0.01)
        inicio = time.monotonic()
        m.parar.set()
        try:
            future.result(timeout=2)
            verificar(False, "cancelar modelo")
        except modelo.Cancelado:
            verificar(time.monotonic()-inicio < 2, "encerramento cancela subprocesso")


def testar_cerebro(base, stub):
    rt = base / "runtime"
    rt.mkdir(parents=True)
    chat_dados.HIST = base / "chat"
    pid = os.getpid()
    identidade = executar.identity(pid)
    prefs = {"hana_auto": True, "modo_mensagens": True, "voz_sintetica": False}
    mensagem = {"ativa": True, "autor": "Codex", "id": "leitura-terminal"}
    def status(ativo=True):
        memoria.gravar_atomico(rt / "pids.json", {"godot": pid, "godot_starttime": identidade if ativo else "inativo"})
        memoria.gravar_atomico(rt / "status.json", {"pid": pid, "timestamp": time.time(), "preferencias": prefs, "mensagem": mensagem})
    def novo():
        pasta = base / "dados"
        m = modelo.Modelo(pasta, binario=str(stub), timeout=2)
        return cerebro.Cerebro(pasta, rt, m, lambda: AGORA)
    def enviado(b):
        fim = time.monotonic()+3
        while time.monotonic() < fim:
            status()
            b.passo()
            if b.pendencia and b.pendencia["envio"]:
                return b.pendencia["id"]
            time.sleep(0.01)
        raise AssertionError("resposta não enfileirada: " + repr(b.pendencia) + " chamada=" + repr(b.chamada))
    def recibo(ident, estado):
        (rt / "falas" / (ident + ".json")).unlink(missing_ok=True)
        memoria.gravar_atomico(rt / "recibos-fala" / (ident + ".json"), {"estado": estado})
    with patch.object(cerebro, "Gatilhos", return_value=Mock(passo=lambda janela: [], fechar=lambda: None)), patch.object(desktop, "coletar", return_value=CONTEXTO), patch.object(cerebro, "JUNTAR_POR", 0.04):
        b = novo()
        try:
            a = chat_dados.registrar("usuario", "Tenho uma tarefa")
            status(False)
            b.passo()
            verificar(b.pendencia is None and len(chat_dados.novas("Hana", False)) == 1, "inativa não consome nem chama modelo")
            prefs["hana_auto"] = False
            status(); b.passo()
            verificar(b.pendencia is None, "pref desligada não responde")
            prefs["hana_auto"] = True
            status(); b.passo()
            verificar(len(list((rt / "atividades").glob("*.json"))) == 1, "inicia leitura imediatamente")
            chat_dados.registrar("usuario", "E gosto de café")
            ident = enviado(b)
            entrada = chamadas(b.pasta)[0]["entrada"]
            verificar(len(entrada["mensagens_usuario"]) == 2 and entrada["motivo"] == "resposta", "agrupa mensagens numa chamada")
            verificar(set(entrada) == {"agora", "desktop", "memoria", "historico", "motivo", "mensagens_usuario"}, "contexto completo")
            payload = json.loads((rt / "falas" / (ident+".json")).read_text())
            verificar(payload["autor"] == "Hana" and payload["preparacao"] == {"tom": "irritado"}, "mesma ponte e tom do modelo")
            verificar(len(chat_dados.novas("Hana", False)) == 2 and len(b.memoria.ler()["tarefas"]) == 1, "cursor aguarda entrega; memória aplicada")
            # Reinício depois de publicar: acompanha recibo sem chamar modelo de novo.
        finally:
            b.fechar()
        b = novo()
        try:
            status(); b.passo()
            verificar(len(chamadas(b.pasta)) == 1 and b.pendencia["id"] == ident, "retoma entrega após reinício")
            chat_dados.registrar("usuario", "Outra mensagem enquanto ela escreve")
            recibo(ident, "concluida")
            b.passo()
            verificar(len(chat_dados.novas("Hana", False)) == 1, "confirma lote sem consumir mensagem posterior")
            ident2 = enviado(b)
            verificar(len(b.memoria.ler()["tarefas"]) == 1, "memória não duplica tarefas")
            recibo(ident2, "interrompida")
            b.passo()
            verificar(b.pendencia is None and chat_dados.novas("Hana", False) == [], "clique não reenvia resposta")
            chat_dados.registrar("usuario", "Sessão vai cair")
            ident3 = enviado(b)
            status(False); b.passo()
            verificar(b.pendencia["resposta"] is not None and b.pendencia["envio"] is None, "queda preserva resposta")
            verificar(enviado(b) == ident3 and len(chamadas(b.pasta)) == 3, "retenta mesma resposta/id sem nova chamada")
            recibo(ident3, "erro")
            b.passo()
            verificar(b.pendencia is not None, "erro de entrega mantém pendência")
            enviado(b)
            recibo(ident3, "concluida"); b.passo()
            # Resumo em segundo plano; o caminho principal volta imediatamente.
            for i in range(cerebro.RESUMIR_APOS + 1):
                chat_dados.registrar("personagem", f"Histórico {i}", autor="Teste")
            inicio = time.monotonic(); b._resumir()
            verificar(time.monotonic()-inicio < 0.1 and b.resumo is not None, "resumo fora do caminho crítico")
            b.resumo.result(timeout=2); b._resumir()
            verificar(bool(b.memoria.ler()["resumo"]) and bool(b.memoria.ler()["resumo_ate"]), "resumo/cursor persistidos")
        finally:
            b.fechar()
        # Falha/timeout atravessam o cérebro inteiro e usam a resposta de reserva.
        for modo in ("falha", "timeout"):
            chat_dados.HIST = base / ("chat-" + modo)
            pasta = base / ("dados-" + modo)
            m = modelo.Modelo(pasta, binario=str(stub), timeout=0.15 if modo=="timeout" else 2)
            with patch.dict(os.environ, HANA_STUB=modo):
                b = cerebro.Cerebro(pasta, rt, m, lambda: AGORA)
                try:
                    chat_dados.registrar("usuario", "Mensagem para reserva")
                    ident = enviado(b)
                    d = json.loads((rt / "falas" / (ident+".json")).read_text())
                    verificar(d["texto"] == "aff, travei. manda de novo", "cérebro envia reserva em " + modo)
                    recibo(ident, "concluida"); b.passo()
                finally:
                    b.fechar()
    # O daemon completo também encerra limpo com SIGTERM (sem abrir o mascote).
    bin_dir = base / "bin"
    bin_dir.mkdir()
    (bin_dir / "claude").symlink_to(stub)
    env = dict(os.environ, MASCOTE_RUNTIME=str(base / "sem-sessao"), MASCOTE_HANA_DIR=str(base / "daemon"),
               MASCOTE_CHAT=str(base / "daemon-chat"), PATH=str(bin_dir)+":"+os.environ.get("PATH", ""))
    p = subprocess.Popen([sys.executable, str(cerebro.__file__)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(0.15)
    p.terminate()
    _, err = p.communicate(timeout=3)
    verificar(p.returncode == 0 and b"forma limpa" in err, "daemon encerra por sinal")
    verificar(not (base / "daemon/chamadas.jsonl").exists(), "daemon inativo não chama modelo")


def testar_fila(base):
    chat_dados.HIST = base / "hist"
    ident = chat_dados.registrar("usuario", "Ainda sem resposta")
    for i in range(chat_dados.LIMITE + 1):
        chat_dados.registrar("personagem", f"p{i}")
    verificar(len(chat_dados.listar(500)) == chat_dados.LIMITE, "chat visual mantém limite")
    verificar([m["id"] for m in chat_dados.novas("Hana", False)] == [ident], "fila sobrevive à poda visual")
    chat_dados.confirmar("Hana", ident)
    verificar(not list((chat_dados.HIST / ".pendentes-hana").glob("*.json")), "confirmação limpa fila persistente")


def testar_supervisor(base):
    with (base / "supervisor.log").open("w") as log:
        filho = executar.FilhoSupervisionado([sys.executable, "-c", "raise SystemExit(3)"], log, os.environ.copy())
        filho.passo(0)
        filho.processo.wait(timeout=2)
        filho.passo(1)
        verificar(filho.processo is None and filho.proximo == 2, "backoff inicial")
        filho.passo(1.5)
        verificar(filho.processo is None, "não reinicia antes do backoff")
        filho.passo(2)
        filho.processo.wait(timeout=2)
        filho.passo(3)
        verificar(filho.proximo == 5 and filho.backoff == 4, "backoff cresce após nova queda")
        filho.comando = [sys.executable, "-c", "import time; time.sleep(60)"]
        filho.passo(5)
        filho.passo(66)
        verificar(filho.backoff == 1, "filho estável restaura backoff")
        p = filho.processo
        filho.fechar()
        verificar(p.poll() is not None, "supervisor encerra apenas seu filho")


with tempfile.TemporaryDirectory(prefix="kk-hana-testes-") as pasta:
    base = Path(pasta)
    stub = base / "claude-falso"
    stub.write_text(STUB)
    stub.chmod(0o700)
    testar_schema()
    testar_memoria(base / "memoria")
    testar_rotina(base / "rotina")
    testar_desktop(base / "power")
    testar_modelo(base / "modelo", stub)
    testar_cerebro(base / "cerebro", stub)
    testar_fila(base / "fila")
    testar_supervisor(base)
print(json.dumps({"casos": casos, "passou": True, "erros": []}, ensure_ascii=False))
