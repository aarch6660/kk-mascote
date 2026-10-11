#!/usr/bin/env python3
"""Regera somente a íris das bonecas existentes a partir dos assets selecionados."""
import json,pathlib,hashlib
import numpy as np
from PIL import Image
from carregar import carregar,RAIZ
from compor_olhos import compor_iris
ROOT=pathlib.Path(__file__).resolve().parent.parent

def main():
 report=[]
 for pasta in sorted((ROOT/'bonecas').iterdir()):
  if not (pasta/'card.json').exists():continue
  face=json.loads((pasta/'card.json').read_text())['Custom']['rosto']
  pecas={p['tipo']:p for p in json.loads((pasta/'pecas.json').read_text())['pecas']}
  def tex(tipo,field,bundle):
   p=pecas[tipo]
   for o in carregar(RAIZ/p[bundle]).objects:
    if o.type.name=='Texture2D' and o.peek_name()==p[field]:return np.asarray(o.read().image.convert('RGBA'),dtype=float)/255
   raise ValueError('Textura ausente: '+tipo)
  a=compor_iris(tex('iris_0','EyeTex','MainAB'),tex('gradiente_0','ColorMaskTex','ColorMaskAB'),face['pupil'][0])
  out=pasta/'saida/visual/iris.png'
  before=hashlib.sha256(out.read_bytes()).hexdigest()
  # Brilhos selecionados pelo card, compostos em espaço linear.
  from compor_olhos import linear,srgb
  for tipo,field,color in [('rosto_hlUpId','EyeHiUpTex','hlUpColor'),('rosto_hlDownId','EyeHiDownTex','hlDownColor')]:
   b=tex(tipo,field,'MainAB')
   if b.shape[:2]!=a.shape[:2]:
    b=np.asarray(Image.fromarray(np.uint8(b*255+.5)).resize((a.shape[1],a.shape[0]),Image.Resampling.LANCZOS),dtype=float)/255
   c=face[color];alpha=b[:,:,3:4]*c[3]
   a[:,:,:3]=srgb(linear(a[:,:,:3])*(1-alpha)+linear(b[:,:,:3])*linear(c[:3])*alpha)
  tmp=out.with_name('iris-nova.png');Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(tmp);tmp.replace(out)
  report.append({'boneca':pasta.name,'antes':before,'depois':hashlib.sha256(out.read_bytes()).hexdigest()})
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
