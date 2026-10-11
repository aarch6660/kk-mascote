#!/usr/bin/env python3
from provar_interacoes import *
def main():
    original=bridge.query("activewindow").get("address");cursor=bridge.query("cursorpos");receptor=None
    executar.hypr_lua('_G.kk_teste_receptor=hl.window_rule({name="kk-teste-receptor",match={title="^KK teste receptor$"},float=true,size="1300 850",move="300 100",no_anim=true,no_follow_mouse=true})')
    executar.hypr_lua('_G.kk_teste_plataforma=hl.window_rule({name="kk-teste-plataforma",match={title="^KK teste plataforma$"},float=true,pin=true,size="700 300",move="700 500",no_anim=true,no_follow_mouse=true})')
    try:
        receptor=subprocess.Popen([sys.executable,str(ROOT/"testes/receptor.py")],stdout=subprocess.DEVNULL,env=dict(os.environ,GDK_BACKEND="wayland"));time.sleep(1)
        p=next(c for c in bridge.query("clients") if c["title"]=="KK teste plataforma")
        subprocess.run([str(ROOT/"iniciar.sh"),"--prova","--seconds","25"],check=True);esperar_status()
        perf={};poses={}
        for nome,estado,pos,apoio in [('em-cima-janela','parada',[1050,500],p['address']),('sentada','sentada',[1385,500],p['address']),('dormindo','dormindo',[1050,1080],'tela')]:
            comando(estado=estado,pos=pos,apoio=apoio)
            time.sleep(4.5 if estado=='dormindo' else 1)
            subprocess.run(['grim',str(E/(nome+'.png'))],check=True)
            poses[nome]=status()
            if estado in ['parada','dormindo']:perf['respirando' if estado=='parada' else 'dormindo']=desempenho()
        (E/'capturas-status.json').write_text(json.dumps(poses,indent=2))
        (E/'desempenho.json').write_text(json.dumps(perf,indent=2))
        # Mesma ação liga/desliga do usuário, com lock ainda mantido.
        subprocess.run([str(ROOT/'iniciar.sh')],check=True)
        assert not (R/'pids.json').exists()
    finally:
        subprocess.run([str(ROOT/'iniciar.sh'),'--parar'])
        if receptor:receptor.terminate();receptor.wait(timeout=5)
        executar.hypr_lua('if _G.kk_teste_receptor then _G.kk_teste_receptor:set_enabled(false);_G.kk_teste_receptor=nil end;if _G.kk_teste_plataforma then _G.kk_teste_plataforma:set_enabled(false);_G.kk_teste_plataforma=nil end')
        pointer(cursor['x'],cursor['y'],'move')
        if original:executar.hypr_lua('hl.dispatch(hl.dsp.focus({window="address:'+original+'"}))')
if __name__=='__main__':main()
