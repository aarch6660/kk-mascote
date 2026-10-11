#!/usr/bin/env python3
"""Ensaio curto real: cliques só em janelas próprias; fecha por PID e restaura cursor/foco."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import hypr_bridge as bridge
import executar
spec=importlib.util.spec_from_file_location("medir",ROOT.parent/"janela-teste/medir.py")
medir=importlib.util.module_from_spec(spec);spec.loader.exec_module(medir)
E=ROOT/"evidencias"
R=executar.RUNTIME
POINTER=os.environ.get("MASCOTE_PONTEIRO", "/tmp/kk-mascote-ponteiro")

def cli(*args):
    return subprocess.run(["hyprctl",*args],capture_output=True,text=True,check=True).stdout

def esperar_status(timeout=10):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        try:
            s=json.loads((R/"status.json").read_text())
            if s.get("hull"): return s
        except (OSError,ValueError):pass
        time.sleep(.15)
    raise RuntimeError("Status não apareceu")

def pointer(x,y,action,*extra):
    subprocess.run([POINTER,str(round(x)),str(round(y)),action,*map(str,extra)],check=True,timeout=5)
    time.sleep(.3)

def main():
    original=bridge.query("activewindow").get("address")
    cursor=bridge.query("cursorpos")
    receptor=None
    results={}
    executar.hypr_lua('_G.kk_teste_receptor = hl.window_rule({name="kk-teste-receptor",match={title="^KK teste receptor$"},float=true,pin=false,size="1300 850",move="300 100",no_anim=true})')
    executar.hypr_lua('_G.kk_teste_plataforma = hl.window_rule({name="kk-teste-plataforma",match={title="^KK teste plataforma$"},float=true,pin=false,size="700 300",move="700 500",no_anim=true})')
    try:
        with open(E/"receptor.log","w") as log:
            receptor=subprocess.Popen([sys.executable,str(ROOT/"testes/receptor.py")],stdout=log,stderr=log,env=dict(os.environ,GDK_BACKEND="wayland"))
            time.sleep(1)
            clients=bridge.query("clients")
            back=next(c for c in clients if c["title"]=="KK teste receptor")
            platform=next(c for c in clients if c["title"]=="KK teste plataforma")
            for driver in ["wayland","x11"]:
                executar.hypr_lua('hl.dispatch(hl.dsp.focus({window="address:' + back["address"] + '"}))')
                subprocess.run([str(ROOT/"iniciar.sh"),"--prova","--seconds","22","--driver",driver],check=True)
                status=esperar_status()
                info=json.loads((R/"pids.json").read_text())
                poly=status["hull"]
                # Torso, validado dentro do contorno, sobre nosso receptor.
                x=status["posicao"][0]
                y=status["posicao"][1]-115
                if not bridge.inside_polygon(x,y,poly):
                    candidates=[(a,b) for a in range(round(x)-40,round(x)+40,4) for b in range(round(y)-30,round(y)+30,4) if bridge.inside_polygon(a,b,poly)]
                    x,y=candidates[len(candidates)//2]
                start_log=(E/"receptor.log").read_text().count("RECEIVER_CLICK")
                click_before=status["cliques"]
                pointer(450,700,"click")
                empty_focus=bridge.query("activewindow").get("address")
                after_empty=(E/"receptor.log").read_text().count("RECEIVER_CLICK")
                pointer(x,y,"click")
                time.sleep(.4)
                status=esperar_status()
                inside_focus=bridge.query("activewindow").get("address")
                after_inside=(E/"receptor.log").read_text().count("RECEIVER_CLICK")
                result={"driver_real":status["driver"],"vazio_recebido":after_empty>start_log,
                        "chika_recebeu":status["cliques"]>click_before,"chika_vazou":after_inside>after_empty,
                        "foco_preservado_vazio":empty_focus==back["address"],
                        "foco_preservado_chika":inside_focus==back["address"],
                        "cliques_fora":status["cliques_fora"],"status":status}
                if driver=="x11":
                    # Capturas no estado natural desta prova, sem clicar em aplicações alheias.
                    subprocess.run(["grim",str(E/"em-cima-janela.png")],check=True)
                    time.sleep(3)
                    subprocess.run(["grim",str(E/"sentada.png")],check=True)
                    # CPU de Godot e supervisor, GPU Intel via fdinfo, amostra durante animação.
                    before={k:medir.sample(info[k]) for k in ["godot","runner"]}
                    t0=time.monotonic();time.sleep(3)
                    after={k:medir.sample(info[k]) for k in before};elapsed=time.monotonic()-t0
                    perf={"segundos":elapsed,"cpu_100_porcento":"um núcleo lógico","processos":{}}
                    for k in before:
                        a,b=before[k],after[k]
                        perf["processos"][k]={"cpu_percent":(b["ticks"]-a["ticks"])/os.sysconf("SC_CLK_TCK")/elapsed*100,
                            "rss_mib":b["rss_bytes"]/1024**2,"gpu_intel_busy_percent":{eng:(v-a["intel_ns"].get(eng,v))/elapsed/1e9*100 for eng,v in b["intel_ns"].items()} if b["drm_available"] else None}
                    (E/"desempenho.json").write_text(json.dumps(perf,indent=2))
                    time.sleep(3)
                    subprocess.run(["grim",str(E/"dormindo.png")],check=True)
                results[driver]=result
                subprocess.run([str(ROOT/"iniciar.sh"),"--parar"],check=True)
                time.sleep(.3)
                for name in ["godot.log","runner.log"]:
                    (E/f"{driver}-{name}").write_text((R/name).read_text())
            (E/"cliques.json").write_text(json.dumps(results,indent=2,ensure_ascii=False))
            print(json.dumps({k:{kk:vv for kk,vv in v.items() if kk!="status"} for k,v in results.items()},indent=2))
            assert all(v['vazio_recebido'] and v['chika_recebeu'] and not v['chika_vazou'] and
                       v['foco_preservado_vazio'] and v['foco_preservado_chika'] and v['cliques_fora']==0
                       for v in results.values()), 'Falha no ensaio de clique; consulte cliques.json'
    finally:
        subprocess.run([str(ROOT/"iniciar.sh"),"--parar"])
        if receptor:
            receptor.terminate();receptor.wait(timeout=5)
        executar.hypr_lua('if _G.kk_teste_receptor then _G.kk_teste_receptor:set_enabled(false);_G.kk_teste_receptor=nil end; if _G.kk_teste_plataforma then _G.kk_teste_plataforma:set_enabled(false);_G.kk_teste_plataforma=nil end')
        pointer(cursor["x"],cursor["y"],"move")
        if original: executar.hypr_lua('hl.dispatch(hl.dsp.focus({window="address:' + original + '"}))')

if __name__=="__main__":main()
