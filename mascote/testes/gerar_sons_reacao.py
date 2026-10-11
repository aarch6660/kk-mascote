#!/usr/bin/env python3
"""Gera uma vez interjeições de atuação e teclas suaves; não lê assets do jogo."""
import concurrent.futures,json,math,os,random,struct,subprocess,wave,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import voz
DEST=ROOT/'sons'
def aparar(p,dados):
    nz=[i for i,v in enumerate(dados['envoltoria']) if v>0.01]
    if not nz: raise RuntimeError('Interjeição silenciosa: '+str(p))
    with wave.open(str(p),'rb') as w:
        params=w.getparams();rate=w.getframerate();raw=w.readframes(w.getnframes())
    inicio=max(0,round((nz[0]-3)*voz.STEP*rate))
    fim=min(len(raw)//2,round((nz[-1]+8)*voz.STEP*rate))
    with wave.open(str(p),'wb') as w:
        w.setparams(params);w.writeframes(raw[inicio*2:fim*2])
    duracao,envelope=voz.analisar(p)
    dados.update(duracao=duracao,envoltoria=envelope)
    return dados
def gerar(item):
 nome,texto=item
 p=DEST/(nome+'.wav')
 r=subprocess.run([str(Path.home()/'.local/share/pipx/venvs/edge-tts/bin/python'),str(ROOT/'voz.py')],input=json.dumps({'texto':texto,'arquivo':str(p)}),text=True,capture_output=True,check=True,timeout=55)
 dados=aparar(p,json.loads(r.stdout))
 return nome,{'texto':texto,'voz':dados.get('voz'),'duracao':dados['duracao'],'passo':dados['passo'],'envoltoria':dados['envoltoria']}
def main():
 DEST.mkdir(exist_ok=True)
 if '--aparar' in sys.argv:
  catalogo=json.loads((DEST/'catalogo.json').read_text())
  for nome,dados in catalogo.items():aparar(DEST/(nome+'.wav'),dados)
  (DEST/'catalogo.json').write_text(json.dumps(catalogo,ensure_ascii=False,indent=2)+'\n')
  print(json.dumps({k:round(v['duracao'],3) for k,v in catalogo.items()}))
  return
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  catalogo=dict(pool.map(gerar,[('surpresa','Ah!'),('duvida','Ué?'),('alegria','Oba!')]))
 (DEST/'catalogo.json').write_text(json.dumps(catalogo,ensure_ascii=False,indent=2)+'\n')
 # Pequenos toques percussivos, baixos e espaçados; não capturam teclado real.
 rng=random.Random(101)
 sr=22050
 samples=[0.0]*int(sr*1.6)
 for inicio in [0.04,0.16,0.37,0.51,0.64,0.97,1.12,1.35]:
  freq=rng.uniform(1100,1800)
  for k in range(int(sr*0.027)):
   f=k/sr
   samples[int(inicio*sr)+k] += (math.sin(f*math.tau*freq)*0.65+rng.uniform(-1,1)*0.35)*math.exp(-f*190)*0.12
 with wave.open(str(DEST/'digitacao.wav'),'wb') as w:
  w.setparams((1,2,sr,0,'NONE','not compressed'))
  w.writeframes(b''.join(struct.pack('<h',round(v*32767)) for v in samples))
 print(json.dumps({k:{'texto':v['texto'],'duracao':v['duracao']} for k,v in catalogo.items()},ensure_ascii=False))
if __name__=='__main__':main()
