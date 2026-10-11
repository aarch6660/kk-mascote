#!/usr/bin/env python3
"""Compara o shader com amostras CPU em planos sintéticos, em Xvnc privado."""
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'personagem'))
from areola_kk import compor_amostra
from compor_olhos import linear, srgb

OUT = ROOT / 'mascote/evidencias/pele-card-2026-10-09/testes'


def amostras():
    y, x = np.mgrid[:128, :128]
    im = np.stack([.2 + .7*x/127, .1 + .8*y/127, np.full_like(x, .3, dtype=float),
                   ((x>3)&(y>3)&(x<124)&(y<124)).astype(float)], axis=-1)
    im = np.round(im*255).astype('uint8')
    Image.fromarray(im).save(OUT / 'canais.png')
    im = im.astype(float)/255
    dados = {'tamanho': .6, 'brilho': .5, 'mistura': 1., 'deformar': 1., 'uv_unity': [1,1,0,0], 'srgb': False}
    casos = []
    for u,v,mask,size,gloss,blend,alpha in [
        (.5,.5,1,.6,.5,1,1),(.6,.7,1,.6,.5,1,1),(.2,.6,1,.6,.5,1,1),(.6,.2,1,.6,.5,1,1),
        (.5,.5,0,.6,.5,1,1),(.3,.3,0,.6,.5,1,1),(.4,.4,1,1.10322547,.5,1,1),(.7,.6,1,.667741656,.5,1,1),
        (.55,.6,1,.6,0,1,1),(.55,.6,1,.6,1,1,1),(.55,.6,1,.6,.5,0,1),(.55,.6,1,.6,.5,.5,1),
        (.5,.5,1,.6,.5,1,0),(.5,.5,1,.6,.5,1,.5),(-.3,1.5,1,.6,.5,1,1),(.4,.4,1,0,.5,1,1)]:
        p=dict(dados,tamanho=size,brilho=gloss,mistura=blend)
        base=[.8,.7,.6];cor=[.9,.6,.4,alpha]
        esperado=np.clip(srgb(compor_amostra(linear(base),im,np.array([u,v]),mask,p,cor)),0,1)
        casos.append({'uv':[u,v],'vermelho':mask,'dados':p,'base':base,'cor':cor,'esperado':esperado.tolist()})
    (OUT/'amostras.json').write_text(json.dumps(casos,indent=2)+'\n')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    amostras()
    server=None
    r,w=os.pipe()
    try:
        with tempfile.TemporaryDirectory(prefix='kk-pele-prova-') as temp:
            with (OUT/'xvnc.log').open('w') as log:
                server=subprocess.Popen(['Xvnc','-displayfd',str(w),'-geometry','900x900','-depth','24',
                    '-localhost','-SecurityTypes','None','-rfbunixpath',temp+'/vnc.sock','-rfbport','0','-nolisten','tcp'],
                    pass_fds=(w,),stdout=log,stderr=subprocess.STDOUT)
            os.close(w);w=None
            if not select.select([r],[],[],15)[0]:raise RuntimeError('Xvnc não iniciou')
            numero=os.read(r,64).decode().strip()
            if not numero.isdigit():raise RuntimeError('Display inválido')
            godot=os.environ.get('GODOT',str(Path.home()/'.local/opt/godot/godot'))
            for modo in ('gl_compatibility','forward_plus'):
                env=dict(os.environ,DISPLAY=':'+numero,KK_PELE_PROVA=str(OUT),KK_PELE_RENDERER=modo,
                         MASCOTE_RUNTIME='',MASCOTE_CACHE=temp+'/cache.json')
                env.pop('WAYLAND_DISPLAY',None)
                with (OUT/(modo+'.log')).open('w') as log:
                    subprocess.run([godot,'--display-driver','x11','--rendering-method',modo,'--audio-driver','Dummy',
                        '--path',str(ROOT/'mascote'),'--script','testes/pele_card.gd'],env=env,stdout=log,
                        stderr=subprocess.STDOUT,check=True,timeout=90)
                texto=(OUT/(modo+'.log')).read_text()
                if 'ERROR:' in texto:raise RuntimeError(texto)
                print(modo,json.loads((OUT/('godot-'+modo+'.json')).read_text()))
    finally:
        os.close(r)
        if w is not None:os.close(w)
        if server is not None:
            server.terminate()
            try:server.wait(timeout=5)
            except subprocess.TimeoutExpired:server.kill();server.wait()


if __name__=='__main__':
    main()
