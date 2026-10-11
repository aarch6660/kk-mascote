#!/usr/bin/env python3
"""Renderiza a base dos estudos de estilo 2D em Xvnc privado (não toca no mascote ligado)."""
import os,pathlib,subprocess,tempfile,select
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 destino=ROOT/'evidencias/estilos-2d/base';destino.mkdir(parents=True,exist_ok=True)
 r,w=os.pipe();servidor=None
 try:
  with tempfile.TemporaryDirectory(prefix='kk-estilos-') as t:
   with open(t+'/xvnc.log','w') as log:
    servidor=subprocess.Popen(['Xvnc','-displayfd',str(w),'-geometry','1024x1024','-depth','24','-localhost','-SecurityTypes','None','-rfbunixpath',t+'/vnc.sock','-rfbport','0','-nolisten','tcp'],pass_fds=(w,),stdout=log,stderr=subprocess.STDOUT)
    os.close(w);w=None
    if not select.select([r],[],[],15)[0]:raise RuntimeError('Xvnc não iniciou')
    numero=os.read(r,64).decode().strip()
    env=dict(os.environ,DISPLAY=':'+numero,KK_PROVA_RETRATO=str(destino),KK_PROVA_CACHE=t+'/cache.json',MASCOTE_RUNTIME='')
    env.pop('WAYLAND_DISPLAY',None)
    with (destino/'godot.log').open('w') as log:
     subprocess.run([str(pathlib.Path.home()/'.local/opt/godot/godot'),'--display-driver','x11','--rendering-method','gl_compatibility','--audio-driver','Dummy','--fixed-fps','12','--path',str(ROOT),'--script','testes/previa_estilos.gd'],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
 finally:
  os.close(r)
  if w is not None:os.close(w)
  if servidor: servidor.terminate();servidor.wait(timeout=5)
if __name__=='__main__':main()
