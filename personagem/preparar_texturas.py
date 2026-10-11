#!/usr/bin/env python3
"""Combina máscaras RGB e cores do card em texturas de cor portáveis."""
import os
import pathlib,json,numpy as np
from PIL import Image
P=pathlib.Path(os.environ.get("BONECA_DIR", str(pathlib.Path(__file__).resolve().parent)));T=P/'trabalho/tex';S=P/'saida/texturas';S.mkdir(parents=True,exist_ok=True)
card=json.loads((P/'card.json').read_text());pecas=json.loads((P/'pecas.json').read_text())['pecas'];cena=json.loads((P/'trabalho/cena.json').read_text());F=card['Custom']['rosto'];C=card['Custom']['corpo'];lookup={x['tipo']:x for x in pecas};mapa={}
def abrir(n,size=(512,512)):
 p=T/(n if n.endswith('.png') else n+'.png')
 return np.array(Image.open(p).convert('RGBA').resize(size,Image.Resampling.BILINEAR))/255 if p.exists() else None
def solido(c,size=(512,512)):return np.broadcast_to(c,(*size[::-1],4)).copy()
def sobre(a,b):
 if b is not None:a[:,:,:3]=a[:,:,:3]*(1-b[:,:,3:4])+b[:,:,:3]*b[:,:,3:4]
 return a
def registro(k,a):
 nome=k.replace('/','_')+'.png';Image.fromarray(np.round(np.clip(a,0,1)*255).astype('uint8')).save(S/nome);mapa[k]=nome
for p in cena['pecas']:
 item=p['selecao'];tipo=item['tipo'];cfg=item.get('config')
 for mal in p['malhas']:
  for i,mat in enumerate(mal['materiais']):
   if mat is None:continue
   go=mal['go'];nm=mat['nome'];key=tipo+'__'+nm
   if key in mapa:continue
   tex=mat['texturas'];size=(512,512);a=solido([1,1,1,1]);alpha=False
   if tipo.startswith('roupa_'):
    size=(1024,1024);a=abrir(item.get('MainTex','0'),size)
    if a is None:a=solido([1,1,1,1],size)
    mask=abrir(item.get('ColorMaskTex','0'),size)
    if mask is not None:
     tinta=np.ones_like(a[:,:,:3])
     for ch in range(3):tinta=tinta*(1-mask[:,:,ch:ch+1])+np.array(cfg['colorInfo'][ch]['baseColor'][:3])*mask[:,:,ch:ch+1]
     a[:,:,:3]*=tinta
    if tipo=='roupa_0':
     # Emblema é um decal separado do padrão da camiseta; guardado em pecas.json.
     pass
   elif tipo.startswith('cabelo_'):
    a=solido(cfg['baseColor']);mask=abrir(tex.get('_ColorMask','0'))
    if mask is not None:
     a[:,:,:3]=np.array(cfg['baseColor'][:3])*(1-mask[:,:,1:2])+np.array(cfg['endColor'][:3])*mask[:,:,1:2]
    detalhe=abrir(tex.get('_DetailMask','0'))
    if detalhe is not None:a[:,:,:3]*=(.8+.2*(1-detalhe[:,:,1:2]))
   elif go=='o_body_a':a=solido(C['skinMainColor'])
   elif go=='cf_O_face':
    a=solido(C['skinMainColor']);make=F['baseMakeup'];cheek=abrir(cena['texturas_card'].get('maquiagem_cheekId','0'))
    if cheek is not None:
     cheek[:,:,:3]=make['cheekColor'][:3];cheek[:,:,3]*=make['cheekColor'][3];a=sobre(a,cheek)
    mole=abrir(cena['texturas_card'].get('rosto_moleId','0'))
    if mole is not None:
     mole[:,:,:3]=F['moleColor'][:3];mole[:,:,3]*=F['moleColor'][3];a=sobre(a,mole)
   elif 'hitomi_00' in nm:
    a=abrir(cena['texturas_card']['iris_0']);a[:,:,:3]*=np.array(F['pupil'][0]['baseColor'][:3]);alpha=True
    for tipo_hi,chave_cor in [('rosto_hlUpId','hlUpColor'),('rosto_hlDownId','hlDownColor')]:
     hi=abrir(cena['texturas_card'][tipo_hi]);hi[:,:,:3]=F[chave_cor][:3];hi[:,:,3]*=F[chave_cor][3];a=sobre(a,hi)
   elif 'sirome' in nm:
    a=solido(F['whiteBaseColor']);shadow=abrir(cena['texturas_card']['rosto_whiteId'])
    if shadow is not None:a[:,:,:3]=a[:,:,:3]*(1-shadow[:,:,3:4])+np.array(F['whiteSubColor'][:3])*shadow[:,:,3:4]
   elif 'mayuge' in go:
    a=abrir(cena['texturas_card']['rosto_eyebrowId']);a[:,:,:3]=F['eyebrowColor'][:3];alpha=True
   elif 'eyeline' in go:
    if 'kage' in nm:a=abrir(tex.get('_MainTex','0'));a[:,:,:3]*=np.array(C['skinSubColor'][:3])
    else:
     a=abrir(cena['texturas_card']['rosto_eyelineDownId' if 'low' in go else 'rosto_eyelineUpId']);a[:,:,:3]*=np.array(F['eyelineColor'][:3])
    alpha=True
   elif 'noseline' in go:
    a=abrir(cena['texturas_card']['rosto_noseId']);a[:,:,:3]=np.array(C['skinSubColor'][:3])*.65;alpha=True
   elif 'tooth' in go or 'canine' in go:a=solido([1,.97,.94,1])
   else:
    a=abrir(tex.get('_MainTex','0'))
    if a is None:a=solido([1,1,1,1])
   if not alpha:a[:,:,3]=1
   registro(key,a)
(P/'trabalho/materiais.json').write_text(json.dumps(mapa,indent=2)+'\n')
print(len(mapa),'texturas de material preparadas')

# Máscaras do corpo vêm das listas das roupas escolhidas, nunca de uma camiseta fixa.
mascara=np.full((2048,2048,4),255,dtype=np.uint8)
mascaras_pecas={tipo:mascara.copy() for tipo in ['roupa_0','roupa_1']}
for item in pecas:
 if item['tipo'] not in ['roupa_0','roupa_1']:continue
 for k,v in item.items():
  if 'BodyMask' in k and isinstance(v,str) and (T/(v+'.png')).exists():
   m=np.array(Image.open(T/(v+'.png')).convert('RGBA').resize((2048,2048),Image.Resampling.NEAREST))
   mascara=np.minimum(mascara,m)
   mascaras_pecas[item['tipo']]=np.minimum(mascaras_pecas[item['tipo']],m)
np.save(P/'trabalho/mascara_corpo.npy',mascara)
for tipo,m in mascaras_pecas.items():np.save(P/('trabalho/mascara_'+tipo+'.npy'),m)

mascara_bra=np.full((2048,2048,4),255,dtype=np.uint8)
for item in pecas:
 if item['tipo']!='roupa_0':continue
 v=item.get('OverBraMask','0')
 if (T/(v+'.png')).exists():mascara_bra=np.array(Image.open(T/(v+'.png')).convert('RGBA').resize((2048,2048),Image.Resampling.NEAREST))
np.save(P/'trabalho/mascara_bra.npy',mascara_bra)
