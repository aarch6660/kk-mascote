#!/usr/bin/env python3
from provar_interacoes import *
def main():
    original=bridge.query("activewindow").get("address");cursor=bridge.query("cursorpos");receptor=None
    executar.hypr_lua('_G.kk_teste_receptor=hl.window_rule({name="kk-teste-receptor",match={title="^KK teste receptor$"},float=true,pin=false,size="1300 850",move="300 100",no_anim=true,no_follow_mouse=true})')
    executar.hypr_lua('_G.kk_teste_plataforma=hl.window_rule({name="kk-teste-plataforma",match={title="^KK teste plataforma$"},float=true,pin=false,size="700 300",move="700 500",no_anim=true})')
    checks={}
    try:
        receptor=subprocess.Popen([sys.executable,str(ROOT/"testes/receptor.py")],stdout=subprocess.DEVNULL,env=dict(os.environ,GDK_BACKEND="wayland"));time.sleep(1)
        p=next(c for c in bridge.query("clients") if c["title"]=="KK teste plataforma")
        subprocess.run([str(ROOT/"iniciar.sh"),"--prova","--seconds","30"],check=True);esperar_status()
        comando(estado="parada",pos=[1050,500],apoio=p["address"])
        time.sleep(1)
        for nome,indice in [("padrao",1),("dormir",0),("acordar",0)]:
            x,y=ponto();pointer(x,y,"right");time.sleep(.3);s=status()
            print(nome,'antes',s['estado'],'menu',s['menu'],'botoes',s['botoes'],flush=True)
            if not s["menu"]:checks[nome]=False;continue
            bx,by,bw,bh=s["botoes"][indice];pointer(bx+bw/2,by+bh/2,"click");time.sleep(.4)
            s=status();print(nome,'depois',s['estado'],s['escala'],flush=True)
            checks[nome]=s['estado']=='cochilo' if nome=='dormir' else s['estado']=='parada'
            time.sleep(1)
        before=status()['escala'];x,y=ponto();pointer(x,y,'up');time.sleep(.5)
        checks['rodinha']=status()['escala']>before
        (E/'menu.json').write_text(json.dumps(checks,indent=2))
        (E/'menu-godot.log').write_text((R/'godot.log').read_text())
        assert all(checks.values()), 'Falha no ensaio do menu; consulte menu.json'
    finally:
        subprocess.run([str(ROOT/"iniciar.sh"),"--parar"])
        if receptor:receptor.terminate();receptor.wait(timeout=5)
        executar.hypr_lua('if _G.kk_teste_receptor then _G.kk_teste_receptor:set_enabled(false);_G.kk_teste_receptor=nil end;if _G.kk_teste_plataforma then _G.kk_teste_plataforma:set_enabled(false);_G.kk_teste_plataforma=nil end')
        pointer(cursor['x'],cursor['y'],'move')
        if original:executar.hypr_lua('hl.dispatch(hl.dsp.focus({window="address:'+original+'"}))')
if __name__=='__main__':main()
