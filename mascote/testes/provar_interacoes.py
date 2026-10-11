#!/usr/bin/env python3
"""Validação real com janelas próprias, comandos de pose e limpeza garantida."""
from provar_tela import *

def status():return json.loads((R/"status.json").read_text())

def comando(**campos):
    bridge.atomic_json(R/"comando.json",dict(campos,nonce=time.monotonic()))
    time.sleep(.5)

def aguardar(condicao, limite=2):
    fim=time.monotonic()+limite
    while time.monotonic()<fim:
        if condicao(status()):return True
        time.sleep(.1)
    return False

def ponto():
    s=status();poly=s["hull"]
    candidates=[]
    for y in range(round(min(p[1] for p in poly))+4,round(max(p[1] for p in poly))-4,5):
        for x in range(round(min(p[0] for p in poly))+4,round(max(p[0] for p in poly))-4,5):
            if bridge.inside_polygon(x,y,poly):
                # Distância às ARESTAS; vértices esparsos superestimavam a margem.
                clearance=float('inf')
                for a,b in zip(poly,poly[1:]+poly[:1]):
                    dx,dy=b[0]-a[0],b[1]-a[1]
                    t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy))) if dx*dx+dy*dy else 0
                    clearance=min(clearance,(x-a[0]-t*dx)**2+(y-a[1]-t*dy)**2)
                candidates.append((clearance,x,y))
    if not candidates:raise RuntimeError("Sem ponto dentro da silhueta")
    # O ponto mais largo pode ser a cabeça, que muda durante o olhar/blend.
    # Este ensaio de controles mira o torso; bordas continuam um teste separado.
    sentado=s['estado'] in ('sentada','cochilo')
    torso_y=s['posicao'][1]-(50 if sentado else 115)*s['escala']/.75
    torso=[p for p in candidates if abs(p[2]-torso_y)<25*s['escala']/.75]
    _,x,y=max(torso or candidates)
    return x,y

def desempenho(segundos=3):
    info=json.loads((R/"pids.json").read_text())
    before={k:medir.sample(info[k]) for k in ["godot","runner"]};t0=time.monotonic()
    time.sleep(segundos);elapsed=time.monotonic()-t0
    result={"segundos":elapsed,"fps":status()["fps"],"processos":{}}
    for k,a in before.items():
        b=medir.sample(info[k])
        result["processos"][k]={"cpu_percent_um_nucleo":(b["ticks"]-a["ticks"])/os.sysconf("SC_CLK_TCK")/elapsed*100,
            "rss_mib":b["rss_bytes"]/1024**2,"gpu_intel_busy_percent":{eng:(v-a["intel_ns"].get(eng,v))/elapsed/1e9*100 for eng,v in b["intel_ns"].items()} if b["drm_available"] else None}
    return result

def main():
    original=bridge.query("activewindow").get("address")
    workspace=bridge.query("activeworkspace")["id"]
    cursor=bridge.query("cursorpos")
    anim=bridge.query("getoption animations:enabled").get("bool",True)
    saved=Path.home()/".cache/forja/kk-mascote.json"
    cache_before=saved.read_bytes() if saved.exists() else None
    receptor=None;checks={};perf={}
    executar.hypr_lua('_G.kk_teste_receptor = hl.window_rule({name="kk-teste-receptor",match={title="^KK teste receptor$"},float=true,pin=false,size="1300 850",move="300 100",no_anim=true,no_follow_mouse=true})')
    executar.hypr_lua('_G.kk_teste_plataforma = hl.window_rule({name="kk-teste-plataforma",match={title="^KK teste plataforma$"},float=true,pin=false,size="700 300",move="700 500",no_anim=true})')
    try:
        with open(E/"interacoes-receptor.log","w") as log:
            receptor=subprocess.Popen([sys.executable,str(ROOT/"testes/receptor.py")],stdout=log,stderr=log,env=dict(os.environ,GDK_BACKEND="wayland"))
            time.sleep(1)
            clients=bridge.query("clients")
            platform=next(c for c in clients if c["title"]=="KK teste plataforma")
            executar.hypr_lua('hl.dispatch(hl.dsp.focus({window="address:'+platform["address"]+'"}))')
            subprocess.run([str(ROOT/"iniciar.sh"),"--prova","--seconds","65","--driver","x11"],check=True)
            esperar_status()
            comando(estado="parada",pos=[1050,500],apoio=platform["address"])
            before=status();x,y=ponto();pointer(x,y,"up")
            checks["rodinha_aumenta"]=status()["escala"]>before["escala"]
            x,y=ponto();pointer(x,y,"drag",round(x+100),round(y-100))
            s=status();checks["arrasto_solto"]=not s["arrastando"] and s["posicao"][0]>before["posicao"][0]+40
            comando(estado="parada",pos=[1050,500],apoio=platform["address"])
            x,y=ponto();pointer(x,y,"right");s=status();checks["menu_abriu"]=s["menu"]
            mx,my=s["menu_pos"];pointer(mx+70,my+48,"click")
            checks["tamanho_padrao"]=abs(status()["escala"]-.75)<.001
            x,y=ponto();pointer(x,y,"right");s=status();mx,my=s["menu_pos"]
            pointer(mx+70,my+16,"click");checks["menu_dorme"]=status()["estado"]=="cochilo"
            time.sleep(1)  # Espera o blend para não mirar a cabeça da pose anterior.
            x,y=ponto();pointer(x,y,"right");s=status();mx,my=s["menu_pos"]
            pointer(mx+70,my+16,"click");checks["menu_acorda"]=aguardar(lambda s:s["estado"]=="parada");checks["apos_acordar"]=status()["estado"]
            comando(estado="parada",pos=[1050,500],apoio=platform["address"])
            before=status()["posicao"]
            executar.hypr_lua('hl.dispatch(hl.dsp.window.move({window="address:'+platform["address"]+'",x=60,y=30,relative=true}))')
            time.sleep(.6);after=status()["posicao"]
            checks["acompanha_janela"]=abs(after[0]-before[0]-60)<2 and abs(after[1]-before[1]-30)<2
            executar.hypr_lua('hl.dispatch(hl.dsp.window.move({window="address:'+platform["address"]+'",x=700,y=500,relative=false}))')
            time.sleep(.5)
            comando(estado="parada",pos=[1050,500],apoio=platform["address"])
            pointer(450,750,"move")
            executar.hypr_lua('hl.dispatch(hl.dsp.focus({window="address:'+platform["address"]+'"}))')
            subprocess.run(["grim",str(E/"em-cima-janela.png")],check=True)
            perf["respirando"]=desempenho()
            comando(estado="sentada",pos=[1385,500],apoio=platform["address"])
            time.sleep(1)
            subprocess.run(["grim",str(E/"sentada.png")],check=True)
            comando(estado="dormindo",pos=[1050,1080],apoio="tela")
            time.sleep(4.5)
            subprocess.run(["grim",str(E/"dormindo.png")],check=True)
            perf["dormindo"]=desempenho()
            executar.hypr_lua('hl.dispatch(hl.dsp.window.fullscreen({window="address:'+platform["address"]+'",action="set",mode="fullscreen",layout_aware=false}))')
            checks["oculta_fullscreen"]=aguardar(lambda s:s["hidden"])
            if not checks["oculta_fullscreen"]:
                diagnosis={'janela':next(( {k:c.get(k) for k in ('address','fullscreen','fullscreenClient','mapped','hidden','workspace')} for c in bridge.query('clients') if c['address']==platform['address']),{}),'desktop':bridge.snapshot(),'status':status()}
                (E/'fullscreen-falha.json').write_text(json.dumps(diagnosis,indent=2))
            executar.hypr_lua('hl.dispatch(hl.dsp.window.fullscreen({window="address:'+platform["address"]+'",action="unset",mode="fullscreen",layout_aware=false}))')
            checks["volta_fullscreen"]=aguardar(lambda s:not s["hidden"])
            executar.hypr_lua('hl.config({animations={enabled=false}})')
            checks["oculta_modo_jogo"]=aguardar(lambda s:s["hidden"])
            executar.hypr_lua('hl.config({animations={enabled='+str(anim).lower()+'}})')
            time.sleep(.6);checks["volta_modo_jogo"]=not status()["hidden"]
            alvo=max(w["id"] for w in bridge.query("workspaces") if w["id"]>0)+10
            executar.hypr_lua('hl.dispatch(hl.dsp.focus({workspace='+str(alvo)+'}))')
            time.sleep(.6)
            own=next(c for c in bridge.query("clients") if c["class"]=="kk-mascote")
            checks["fixa_workspace"]=own["pinned"] and not status()["hidden"]
            executar.hypr_lua('hl.dispatch(hl.dsp.focus({workspace='+str(workspace)+'}))')
            time.sleep(.6)
            comando(estado="parada",pos=[1050,500],apoio=platform["address"])
            executar.hypr_lua('hl.dispatch(hl.dsp.window.close({window="address:'+platform["address"]+'"}))')
            time.sleep(.35);s=status()
            checks["cai_janela_fecha"]=s["apoio"]!=platform["address"] and s["posicao"][1]>500
            checks["ewmh"]=subprocess.check_output(["xprop","-display",json.loads((R/"pids.json").read_text())["display"],"-id",str(int(s["xid"])),"_NET_WM_STATE"],text=True).strip()
            subprocess.run([str(ROOT/"iniciar.sh"),"--parar"],check=True)
            checks["prova_preserva_cache"]=(saved.read_bytes() if saved.exists() else None)==cache_before
            (E/"interacoes.json").write_text(json.dumps(checks,indent=2,ensure_ascii=False))
            (E/"desempenho.json").write_text(json.dumps(perf,indent=2,ensure_ascii=False))
            (E/"interacoes-godot.log").write_text((R/"godot.log").read_text())
            print(json.dumps(checks,indent=2,ensure_ascii=False))
            assert all(v for v in checks.values() if isinstance(v,bool)), 'Falha no ensaio de interações; consulte interacoes.json'
    finally:
        subprocess.run([str(ROOT/"iniciar.sh"),"--parar"])
        executar.hypr_lua('hl.config({animations={enabled='+str(anim).lower()+'}})')
        executar.hypr_lua('hl.dispatch(hl.dsp.focus({workspace='+str(workspace)+'}))')
        if receptor:
            receptor.terminate();receptor.wait(timeout=5)
        executar.hypr_lua('if _G.kk_teste_receptor then _G.kk_teste_receptor:set_enabled(false);_G.kk_teste_receptor=nil end; if _G.kk_teste_plataforma then _G.kk_teste_plataforma:set_enabled(false);_G.kk_teste_plataforma=nil end')
        pointer(cursor["x"],cursor["y"],"move")
        if original:executar.hypr_lua('hl.dispatch(hl.dsp.focus({window="address:'+original+'"}))')

if __name__=="__main__":main()
