#!/usr/bin/env python3
"""Verifica o mascote real com LUT/sprite nos dois renderers, em Xvnc privado."""
import pathlib,os,subprocess,tempfile,select,json
import numpy as np
from medir_cabelo import R,ROIS,medir
G=os.environ.get('GODOT_PERSONAGEM',str(pathlib.Path.home()/'.local/opt/godot/godot'))
def main():
 r,w=os.pipe();servidor=None
 relatorio={}
 try:
  with tempfile.TemporaryDirectory(prefix='kk-cor-apps-') as t:
   with open(pathlib.Path(t)/'xvnc.log','w') as log:
    servidor=subprocess.Popen(['Xvnc','-displayfd',str(w),'-geometry','1000x1100','-depth','24','-localhost','-SecurityTypes','None','-rfbunixpath',t+'/vnc.sock','-rfbport','0','-nolisten','tcp'],pass_fds=(w,),stdout=log,stderr=subprocess.STDOUT)
    os.close(w);w=None
    if not select.select([r],[],[],15)[0]:raise RuntimeError('Xvnc não iniciou')
    numero=os.read(r,64).decode().strip();assert numero.isdigit()
    for modo in ['forward_plus','gl_compatibility']:
     dest=R/'bonecas/provas_cor_apps'/modo;dest.mkdir(parents=True,exist_ok=True)
     env=dict(os.environ,DISPLAY=':'+numero,KK_PROVA_CORES=str(dest))
     with (dest/'godot.log').open('w') as out:
      subprocess.run([G,'--display-driver','x11','--rendering-method',modo,'--audio-driver','Dummy','--path',str(R/'mascote'),'--script','testes/cores.gd'],env=env,stdout=out,stderr=subprocess.STDOUT,check=True,timeout=120)
     log=(dest/'godot.log').read_text();assert 'ERROR' not in log,log
     relatorio[modo]={}
     for nome,roi in ROIS.items():
      a=medir(dest/(nome+'.png'),roi['render']);b=medir(R/'bonecas'/nome/'saida/render_rosto.png',roi['render'])
      erro=float(np.linalg.norm(np.array(a['lab_d65'])-b['lab_d65']))
      relatorio[modo][nome]={'mascote':a,'delta_e76_visualizador':round(erro,3)}
      assert erro<3,(modo,nome,erro)
   (R/'bonecas/provas_cor_apps/validacao.json').write_text(json.dumps(relatorio,ensure_ascii=False,indent=2)+'\n')
   print(json.dumps({m:{n:v['delta_e76_visualizador'] for n,v in d.items()} for m,d in relatorio.items()}))
 finally:
  os.close(r)
  if w is not None:os.close(w)
  if servidor is not None:
   servidor.terminate()
   try:servidor.wait(timeout=5)
   except subprocess.TimeoutExpired:servidor.kill();servidor.wait()
if __name__=='__main__':main()
