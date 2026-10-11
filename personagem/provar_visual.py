#!/usr/bin/env python3
"""Captura real no Godot/Vulkan em Xvnc privado e monta comparação.
Não abre janela na sessão do usuário. Finaliza só o servidor criado aqui.
"""
import os
import pathlib,subprocess,os,tempfile,select,json
from PIL import Image,ImageDraw,ImageFont
P=pathlib.Path(os.environ.get("BONECA_DIR", str(pathlib.Path(__file__).resolve().parent.parent/"bonecas/chika-haruno")));S=P/'saida';V=pathlib.Path(__file__).resolve().parent.parent/'visualizador'
G=os.environ.get('GODOT_PERSONAGEM',str(pathlib.Path.home()/'.local/opt/godot/Godot_v4.7.2-stable_linux.x86_64'))
def comparar():
 fonte=ImageFont.truetype('/usr/share/fonts/TTF/DejaVuSans.ttf',21)
 pequenos=ImageFont.truetype('/usr/share/fonts/TTF/DejaVuSans.ttf',15)
 out=Image.new('RGB',(2200,800),'#242730');dr=ImageDraw.Draw(out)
 paineis=[('Koikatsu — card original',P/'card.png',0,420),('Godot — expressão do card',S/'render_card.png',430,460),('Godot — olhos normais',S/'render_rosto.png',900,460),('Godot — frente',S/'render_frente.png',1370,410),('Godot — 3⁄4',S/'render_tres_quartos.png',1790,410)]
 for titulo,p,x,w in paineis:
  dr.text((x+10,15),titulo,font=fonte,fill='white')
  if p:
   im=Image.open(p).convert('RGB');escala=min((w-20)/im.width,910/im.height);im=im.resize((round(im.width*escala),round(im.height*escala)),Image.Resampling.LANCZOS);out.paste(im,(x+(w-im.width)//2,65))
 linhas=['Godot • Vulkan / Forward+ • materiais KK reconstruídos; comparação não comprova igualdade com o jogo.', 'Cores e peças do card; câmera, pose, iluminação e física podem diferir do editor original.']
 for j,t in enumerate(linhas):dr.text((16,655+j*23),t,font=pequenos,fill='#dddde5')
 out.save(S/'comparacao_render.png')
def main():
 r,w=os.pipe();servidor=None
 try:
  with tempfile.TemporaryDirectory(prefix='kk-prova-') as temp:
   with open(pathlib.Path(temp)/'xvnc.log','w') as log:
    servidor=subprocess.Popen(['Xvnc','-displayfd',str(w),'-geometry','1000x1100','-depth','24','-localhost','-SecurityTypes','None','-rfbunixpath',temp+'/vnc.sock','-rfbport','0','-nolisten','tcp'],pass_fds=(w,),stdout=log,stderr=subprocess.STDOUT)
    os.close(w);w=None
    if not select.select([r],[],[],15)[0]:raise RuntimeError('Xvnc não iniciou')
    numero=os.read(r,64).decode().strip()
    if not numero.isdigit():raise RuntimeError('Display virtual inválido')
    env=dict(os.environ,DISPLAY=':'+numero)
    with (S/'render_godot.log').open('w') as out:
     subprocess.run([G,'--display-driver','x11','--rendering-method','forward_plus','--audio-driver','Dummy','--path',str(V),'--','--prova','--boneca='+P.name],env=env,stdout=out,stderr=subprocess.STDOUT,check=True,timeout=120)
   log=(S/'render_godot.log').read_text()
   if 'ERROR:' in log or 'SHADER ERROR' in log:raise RuntimeError('Erro no Godot; ver render_godot.log')
   for n in ['frente','tres_quartos','rosto','card']:
    im=Image.open(S/f'render_{n}.png');assert im.size==(900,1000)
   validar=json.loads((S/'validacao_visual_godot.json').read_text());assert not validar['faltantes']
   comparar();print('Quatro capturas Godot e comparacao_render.png gravadas.')
 finally:
  os.close(r)
  if w is not None:os.close(w)
  if servidor is not None:
   servidor.terminate()
   try:servidor.wait(timeout=5)
   except subprocess.TimeoutExpired:servidor.kill();servidor.wait()
if __name__=='__main__':main()
