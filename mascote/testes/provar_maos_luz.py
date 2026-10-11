#!/usr/bin/env python3
"""Provas do corpo e interações na cena real em Xvnc privado, sem supervisor ou IPC do Hyprland."""
import os,pathlib,subprocess,tempfile,select
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 destino=ROOT/'evidencias/maos-luz'
 destino.mkdir(exist_ok=True)
 servidor=None
 r,w=os.pipe()
 try:
  with tempfile.TemporaryDirectory(prefix='kk-maos-luz-') as t:
   with open(t+'/xvnc.log','w') as log:
    servidor=subprocess.Popen(['Xvnc','-displayfd',str(w),'-geometry','1920x1080','-depth','24','-localhost','-SecurityTypes','None','-rfbunixpath',t+'/vnc.sock','-rfbport','0','-nolisten','tcp'],pass_fds=(w,),stdout=log,stderr=subprocess.STDOUT)
    os.close(w);w=None
    if not select.select([r],[],[],15)[0]:raise RuntimeError('Xvnc não iniciou')
    numero=os.read(r,64).decode().strip();assert numero.isdigit()
    env=dict(os.environ,DISPLAY=':'+numero,KK_PROVA_RETRATO=str(destino),MASCOTE_RETRATO='0',MASCOTE_RUNTIME='')
    env.pop('WAYLAND_DISPLAY',None)
    if os.environ.get('KK_PROVA_GPU') == 'intel':
     env['DRI_PRIME']='pci-0000_00_02_0';env['__GLX_VENDOR_LIBRARY_NAME']='mesa'
     for key in ['__NV_PRIME_RENDER_OFFLOAD','__VK_LAYER_NV_optimus','VK_LOADER_DRIVERS_SELECT']:env.pop(key,None)
    with (destino/'godot.log').open('w') as log:
     subprocess.run([os.environ.get('GODOT',str(pathlib.Path.home()/'.local/opt/godot/godot')),'--display-driver','x11','--rendering-method','gl_compatibility','--audio-driver','Dummy','--path',str(ROOT),'--script','testes/maos_luz.gd'],env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=90)
    assert 'ERROR' not in (destino/'godot.log').read_text(),(destino/'godot.log').read_text()
    print("Capturas concluídas")
 finally:
  os.close(r)
  if w is not None:os.close(w)
  if servidor is not None:
   servidor.terminate()
   try:servidor.wait(timeout=5)
   except subprocess.TimeoutExpired:servidor.kill();servidor.wait()
if __name__=='__main__':main()
