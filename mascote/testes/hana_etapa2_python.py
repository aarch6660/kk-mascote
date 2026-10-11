#!/usr/bin/env python3
"""Vida própria: relógio, contexto, filas, gatilhos e bash interativo isolado."""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hana import avisar, cerebro, desktop, gatilhos, instalar_hook, memoria, modelo, rotina

ROOT = Path(__file__).resolve().parents[1]
AGORA = datetime(2026, 10, 11, 10, tzinfo=timezone(timedelta(hours=-3)))
casos = 0


def verificar(ok, nome):
    global casos
    casos += 1
    assert ok, nome


def contexto(classe="kitty", titulo="bash", musica=None, baterias=None):
    return dict(janela=dict(**{"class": classe, "title": titulo}, fullscreen=False),
                musica=musica or {}, baterias=baterias or [])


def testar_categorias():
    for classe, titulo, categoria in [
        ("Minecraft", "", "jogo"), ("steam_app_123", "", "jogo"), ("lutris", "", "jogo"),
        ("java", "Minecraft 1.21", "jogo"), ("java", "Outro app", "outro"),
        ("kitty", "nvim main.py", "codigo"), ("kitty", "bash", "outro"),
        ("Code", "", "codigo"), ("firefox", "Artigo", "navegador"),
        ("firefox", "YouTube", "video"), ("mpv", "", "video"), ("spotify", "", "musica"),
        ("kk-mascote", "Minecraft", "outro")]:
        verificar(desktop.categorizar(contexto(classe,titulo)["janela"])==categoria, f"categoria {classe}/{titulo}")
    verificar(desktop.categorizar({"class":"minha-app"}, [{"classes":["minha-*"],"categoria":"jogo"}])=="jogo", "tabela editável")
    verificar(desktop.categorizar({"class":"x"}, [{"classes":["x"],"titulo":"[","categoria":"jogo"}])=="outro", "regex inválida tolerada")
    verificar(desktop.categorizar({"class":"x"},None)=="outro", "classe desconhecida")
    with tempfile.TemporaryDirectory(prefix="kk-mpris-") as tmp:
        with patch.object(desktop.shutil,"which",return_value="/fake"), patch.object(desktop,"comando",side_effect=lambda args:'{}' if args[0]=="hyprctl" else 'Playing'):
            verificar(desktop.coletar(Path(tmp))["musica"]["status"]=="Playing", "MPRIS Playing sem artista/título continua detectado")
    for hora in range(24):
        verificar(rotina.madrugada(AGORA.replace(hour=hora))==(hora<5), f"madrugada {hora}")
    verificar(rotina.madrugada(AGORA.replace(hour=4,minute=59)) and not rotina.madrugada(AGORA.replace(hour=5)), "limite às cinco")


def testar_rotina(base):
    agora = [AGORA]
    m = memoria.Memoria(base / "memoria.json")
    r = rotina.Rotina(m, lambda: agora[0], lambda a,b:a)
    c = contexto()
    r.observar(c, agora[0].timestamp())
    r.confirmar("bom_dia")
    e = avisar.enviar("Comando terminou com erro 2.", base, agora=agora[0].timestamp())
    r.enfileirar(e); r.enfileirar(e)
    verificar(len(m.ler()["rotina"]["eventos"])==1, "aviso não duplica")
    verificar(r.motivo(c,{},True) is None, "trava de quinze minutos")
    agora[0] += timedelta(minutes=15)
    for status in ({"hidden":True},{"game_mode":True}):
        verificar(r.motivo(c,status,True) is None, "aviso acumula em tela cheia/jogo")
    verificar(r.motivo(c,{},True)=="evento:aviso", "entrega aviso ao retornar")
    r.confirmar("evento:aviso","recebido",e["id"])
    verificar(not m.ler()["rotina"]["eventos"], "confirma somente evento entregue")
    agora[0] += timedelta(minutes=15)
    jogo = contexto("steam_app_42")
    r.observar(jogo)
    verificar(r.motivo(jogo,{},True) is None, "janela não comenta imediatamente")
    agora[0] += timedelta(seconds=120)
    r.observar(jogo)
    verificar(r.motivo(jogo,{},True) is None, "janela precisa durar mais de dois minutos")
    agora[0] += timedelta(seconds=1)
    r.observar(jogo)
    verificar(r.motivo(jogo,{},True)=="evento:janela", "janela estável gera comentário")
    r.confirmar("evento:janela")
    musica = contexto("spotify", musica={"status":"Playing"})
    r.observar(musica)
    agora[0] += timedelta(minutes=15)
    r.observar(musica)
    verificar(r.motivo(musica,{},True) is None, "comentários compartilham trava de trinta minutos")
    agora[0] += timedelta(minutes=15)
    r.observar(musica)
    verificar(r.motivo(musica,{},True) in ("evento:janela","evento:musica"), "novo contexto comenta após trinta minutos")
    r.confirmar(r.motivo(musica,{},True))
    # Pausa/troca remove observações antigas, inclusive depois de fullscreen.
    agora[0] += timedelta(minutes=30)
    r.observar(c)
    verificar(r.motivo(c,{},True) is None, "música pausada e janela antiga são descartadas")
    baixo = contexto(baterias=[dict(nome="BAT0",nivel=15,status="Discharging")])
    r.observar(baixo)
    verificar(r.motivo(baixo,{},True)=="evento:bateria", "bateria baixa no limite")
    r.observar(c)
    verificar(r.motivo(c,{},True) is None, "bateria recuperada não avisa")
    carregando = contexto(baterias=[dict(nome="BAT0",nivel=99,status="Charging")])
    cheia = contexto(baterias=[dict(nome="BAT0",nivel=100,status="Full")])
    verificar("bateria_cheia" not in desktop.eventos({},cheia), "login com bateria cheia não provoca evento")
    r.observar(carregando); r.observar(cheia)
    verificar(r.motivo(cheia,{},True)=="evento:bateria_cheia", "transição carregando para cheia")
    r.confirmar("evento:bateria_cheia")
    agora[0] += timedelta(hours=3)
    r.observar(c, AGORA.timestamp()+3*3600)
    verificar(r.motivo(c,{},True) is None, "três horas exatas não são ausência maior que três horas")
    agora[0] += timedelta(hours=3,seconds=1)
    r.observar(c, agora[0].timestamp())
    verificar(r.motivo(c,{},True)=="volta", "ausência maior que três horas")
    r.confirmar("volta")
    # Um aviso vencido e um download removido não sobrevivem à saída de fullscreen.
    expirado = dict(e, id="expirado", expira_em=agora[0].timestamp()-1)
    r.enfileirar(expirado); r.observar(c)
    verificar(r.evento("evento:aviso",c) is None, "aviso expirado descartado")
    for i in range(80):
        r.enfileirar(dict(e,id=str(i),expira_em=agora[0].timestamp()+3600))
    verificar(len(m.ler()["rotina"]["eventos"])==64, "fila tem limite")
    antes = m.ler()["rotina"]["ultima_proativa"]
    r.descartar("79")
    verificar(m.ler()["rotina"]["ultima_proativa"]==antes, "descartar não consome trava de proatividade")


def testar_downloads(base):
    base.mkdir()
    (base / "antigo.txt").write_text("antigo")
    agora = [0.0]
    d = gatilhos.Downloads(base, lambda:agora[0])
    for nome in ("arquivo.part","arquivo.crdownload","arquivo.tmp"):
        (base / nome).write_text("em curso")
    verificar(d.passo()==[], "ignora temporários e existentes")
    arquivo = base / "novo.zip"
    arquivo.write_text("x")
    d.passo(); agora[0]=3
    verificar(d.passo()==[], "três segundos exatos não bastam")
    arquivo.write_text("mudou")
    d.passo(); agora[0]=6.1
    es = d.passo()
    verificar(len(es)==1 and es[0]["motivo"]=="evento:download", "download estável gera um evento")
    verificar(d.passo()==[], "download não repete")
    e = dict(es[0],expira_em=AGORA.timestamp()+3600)
    verificar(rotina.relevante(e,{},AGORA), "download ainda existe e tem mesma assinatura")
    arquivo.unlink()
    verificar(not rotina.relevante(e,{},AGORA), "download removido deixa de ser relevante")
    (base / "arquivo.part").rename(base / "final.zip")
    d.passo(); agora[0]+=4
    verificar(len(d.passo())==1, "renomeação final detectada")


def testar_crash(base):
    base.mkdir()
    p = base / "42"; p.mkdir()
    campos = ["0"]*50; campos[0]="S"; campos[19]="123"
    def stat():
        (p/"stat").write_text("42 (minecraft) "+" ".join(campos))
    stat()
    g = gatilhos.Gatilhos(gatilhos.Downloads(base / "ausente"), proc=base)
    try:
        with patch.object(g,"_journal",return_value=[]):
            verificar(g.passo({})==[], "jogo vivo não é crash")
            campos[0]="Z"; campos[49]="11"; stat()
            verificar(g.passo({})[0]["motivo"]=="evento:crash", "zumbi conhecido termina por sinal")
            verificar(g.passo({})==[], "crash não repete")
            campos[19]="124"; campos[49]=str(2<<8);stat()
            verificar(g.passo({})==[], "saída com erro sem sinal não é crash")
            campos[19]="125"; campos[49]="6";stat()
            verificar(len(g.passo({}))==1, "PID reutilizado tem identidade própria")
        verificar(gatilhos.processo_jogo("java","Minecraft") and not gatilhos.processo_jogo("java","app"), "Java só com evidência Minecraft")
        verificar(gatilhos.processo_jogo("steam_app_42"), "Steam conhecido")
        # journalctl entrega JSON após o PID sumir; os dois observadores deduplicam.
        r,w = os.pipe()
        proc = __import__("unittest.mock",fromlist=["Mock"]).Mock()
        proc.stdout = os.fdopen(r,"rb")
        proc.poll.return_value = None
        proc.wait.return_value = 0
        g.conhecidos["77"] = dict(inicio="987",nome="jogo-custom",visto=time.monotonic())
        dado = dict(COREDUMP_COMM="jogo-custom",COREDUMP_PID="77",COREDUMP_SIGNAL="11")
        os.write(w,(json.dumps(dado)+"\n").encode())
        try:
            with patch.object(gatilhos.shutil,"which",return_value="journalctl"), patch.object(gatilhos.subprocess,"Popen",return_value=proc):
                es = g._journal()
            verificar(len(es)==1 and "sinal 11" in es[0]["texto"], "coredump de jogo conhecido observado sem bloquear")
            os.write(w,(json.dumps(dado)+"\n").encode())
            verificar(g._journal()==[], "coredump repetido deduplicado")
        finally:
            os.close(w)
    finally:
        g.fechar()


def testar_hook(base):
    base.mkdir()
    (base/".bashrc").write_text("# preferências\n")
    verificar(instalar_hook.instalar(base), "instala hook uma vez")
    verificar(not instalar_hook.instalar(base), "não duplica hook")
    verificar((base/".bashrc.antes-hana").read_text()=="# preferências\n", "backup exato")
    hook = ROOT/"hana/shell-hook.bash"
    p = subprocess.run(["bash","--noprofile","--norc","-c",'source "$1"; [[ ! -v _hana_hook_instalado ]]',"bash",str(hook)],capture_output=True)
    verificar(p.returncode==0,"não interativo não instala traps")
    fake = base/"aviso.py"
    fake.write_text('import os,pathlib,sys\np=pathlib.Path(os.environ["HANA_TEST_LOG"])\nwith p.open("a") as f:f.write(sys.argv[1]+"\\n")\n')
    for tipo in ("string","array"):
        log = base/f"{tipo}.log"
        rc = base/f"{tipo}.bashrc"
        comando = 'printf "ANTERIOR:%s\\n" "$?"'
        prompt = f"PROMPT_COMMAND=('{comando}')" if tipo=="array" else f"PROMPT_COMMAND='{comando}'"
        rc.write_text(f'PS1=""\n{prompt}\ntrap \'_hana_debug_contagem=$(( ${{_hana_debug_contagem:-0}}+1 ))\' DEBUG\nsource "{hook}"\nsource "{hook}"\n')
        # Simula passagem de tempo com início injetado, sem aguardar 90 s reais.
        entrada = '_hana_inicio=$((EPOCHSECONDS-91)); _hana_comando=compilar; false\nwait\n_hana_inicio=$((EPOCHSECONDS-90)); _hana_comando=curto; true\nwait\nprintf "DEBUG:%s\\n" "$_hana_debug_contagem"\nexit\n'
        env = dict(os.environ,MASCOTE_HANA_AVISAR=str(fake),HANA_TEST_LOG=str(log))
        p = subprocess.run(["bash","--noprofile","--rcfile",str(rc),"-i"],input=entrada,text=True,capture_output=True,env=env,timeout=10)
        verificar(p.returncode==0,"bash interativo mantém saída: "+tipo)
        linhas = log.read_text().splitlines() if log.exists() else []
        verificar(len(linhas)==1 and "compilar" in linhas[0] and "código de saída 1" in linhas[0], "hook avisa somente comando longo e status: "+tipo)
        verificar("ANTERIOR:1" in p.stdout,"PROMPT_COMMAND anterior recebe status: "+tipo)
        verificar("DEBUG:" in p.stdout and not "DEBUG:0" in p.stdout,"trap DEBUG anterior preservado: "+tipo)


def testar_cerebro(base):
    base.mkdir()
    class Observadores:
        def passo(self, janela): return []
        def fechar(self): pass
    class Modelo:
        parar = __import__("threading").Event()
    with patch.object(cerebro,"Gatilhos",Observadores), patch.object(desktop,"coletar",return_value=contexto("steam_app_42")):
        b = cerebro.Cerebro(base/"dados",base/"runtime",Modelo(),lambda:AGORA)
        try:
            avisar.enviar("Compilação pronta",base/"dados",agora=AGORA.timestamp())
            b._desktop()
            publico = json.loads((base/"runtime/contexto.json").read_text())
            verificar(publico["hora_local"]==10 and publico["janela"]["class"]=="steam_app_42", "publica contexto para Godot")
            verificar(not list((base/"dados/eventos").glob("*.json")),"fila externa consumida após persistir")
            b.preparar([],"evento:aviso")
            verificar(b.entrada()["desktop"]["evento"]["texto"]=="Compilação pronta","modelo recebe evento concreto")
            verificar(all(g in modelo.catalogos()["gesto"] for g in ("gesto_ajeitar_cabelo","gesto_mao_boca","gesto_olhar_longe","gesto_maos_juntas","gesto_reverencia")), "cinco gestos curados")
        finally:
            b.fechar()


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="kk-hana-etapa2-") as tmp:
        base = Path(tmp)
        testar_categorias()
        testar_rotina(base/"rotina")
        testar_downloads(base/"downloads")
        testar_crash(base/"proc")
        testar_hook(base/"shell")
        testar_cerebro(base/"cerebro")
    print(json.dumps(dict(passou=True,casos=casos,erros=[])))
