#!/usr/bin/env python3
"""Mede franja frontal com polígonos fixos, sem selecionar pixels pela cor.
As câmeras diferem: ROIs anatômicas equivalentes, não registro pixel a pixel.
RGB médio sRGB (0–255), HSV da média e Delta E 76 em CIELAB D65.
"""
import json,pathlib,sys,hashlib
import numpy as np
from PIL import Image,ImageDraw
R=pathlib.Path(__file__).resolve().parent.parent
ARQ=R/'bonecas/medicoes_cabelo.json'
ROIS={
 'chika-haruno':{'card':[(64,36),(158,23),(176,49),(155,82),(125,98),(91,88),(62,78)],'render':[(320,180),(455,163),(510,204),(502,292),(462,349),(403,379),(373,333),(309,351),(297,295)]},
 'sawai-hinata':{'card':[(80,43),(101,32),(120,35),(120,54),(113,66),(107,87),(96,83),(91,61),(80,76)],'render':[(326,182),(405,158),(464,174),(453,241),(438,286),(408,363),(384,331),(367,270),(334,337)]},
 'mizuno-ayaka':{'card':[(109,31),(128,30),(143,40),(149,59),(148,71),(137,73),(124,57),(115,48)],'render':[(416,218),(468,204),(520,246),(550,314),(545,385),(514,412),(480,372),(455,310)]}}
def lab(rgb):
 s=np.asarray(rgb)/255;l=np.where(s<=.04045,s/12.92,((s+.055)/1.055)**2.4)
 xyz=(np.array([[.4124564,.3575761,.1804375],[.2126729,.7151522,.072175],[.0193339,.119192,.9503041]])@l)/[.95047,1,1.08883]
 f=np.where(xyz>(6/29)**3,np.cbrt(xyz),xyz/(3*(6/29)**2)+4/29)
 return np.array([116*f[1]-16,500*(f[0]-f[1]),200*(f[1]-f[2])])
def medir(path,poly):
 import colorsys
 im=Image.open(path).convert('RGB');mask=Image.new('L',im.size);ImageDraw.Draw(mask).polygon(poly,fill=255)
 px=np.array(im)[np.array(mask)>0];rgb=px.mean(0);h,s,v=colorsys.rgb_to_hsv(*(rgb/255))
 return {'rgb_srgb_255':rgb.round(2).tolist(),'hsv_media':{'h_graus':round(h*360,2),'s_percentual':round(s*100,2),'v_percentual':round(v*100,2)},'pixels':len(px),'sha256_imagem':hashlib.sha256(path.read_bytes()).hexdigest(),'lab_d65':lab(rgb).round(3).tolist()}
def main():
 etapa=sys.argv[1]
 if etapa=='antes' and ARQ.exists():raise SystemExit('Antes já preservado; não sobrescrever a medição histórica.')
 d=json.loads(ARQ.read_text()) if ARQ.exists() else {'metodo':'Franja frontal, polígonos anatômicos fixos desenhados manualmente em cada câmera; sem filtro cromático, fundo/pele/contorno evitados. Médias em sRGB; HSV calculado sobre RGB médio; Delta E 76 da média (não é métrica de igualdade de iluminação).','bonecas':{}}
 for nome,rois in ROIS.items():
  p=R/'bonecas'/nome;b=d['bonecas'].setdefault(nome,{'regioes':rois,'card':medir(p/'card.png',rois['card'])})
  b[etapa]=medir(p/'saida/render_rosto.png',rois['render']);b[etapa]['delta_e76_card']=round(float(np.linalg.norm(np.array(b['card']['lab_d65'])-b[etapa]['lab_d65'])),2)
  print(nome,'card',b['card']['rgb_srgb_255'],etapa,b[etapa]['rgb_srgb_255'],'ΔE',b[etapa]['delta_e76_card'])
 ARQ.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
