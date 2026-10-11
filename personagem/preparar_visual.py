#!/usr/bin/env python3
"""Materiais KK auditáveis, texturas originais e parâmetros para ShaderMaterial.
Só lê chara; não modifica o jogo. Não redimensiona texturas originais.
"""
import os
import json,pathlib,shutil,numpy as np
from PIL import Image
from carregar import carregar,RAIZ
from extrair_cor_kk import extrair
from compor_olhos import compor_iris,linear,srgb
from areola_kk import configurar_areola
extrair()
cores_kk=json.loads((pathlib.Path(__file__).resolve().parent.parent/'bonecas/visual_comum/cores_kk.json').read_text())
P=pathlib.Path(os.environ.get("BONECA_DIR", str(pathlib.Path(__file__).resolve().parent))); T=P/'trabalho/tex'; S=P/'saida/visual'; S.mkdir(parents=True,exist_ok=True)
cena=json.loads((P/'trabalho/cena.json').read_text()); card=json.loads((P/'card.json').read_text()); F=card['Custom']['rosto']; C=card['Custom']['corpo']; itens={i['tipo']:i for i in json.loads((P/'pecas.json').read_text())['pecas']}
# Materiais de composição do jogo: guardados à parte para auditar UV/layout.
composicao={}
for bundle in ['oo_base.unity3d','bo_head_00.unity3d']:
 for o in carregar(RAIZ/'chara'/bundle).objects:
  if o.type.name=='Material':
   m=o.read()
   if m.m_Name in ['cf_m_face_create','cf_m_body_create']:
    composicao[m.m_Name]={'shader':m.m_Shader.read().m_ParsedForm.m_Name,'cores':{k:[v.r,v.g,v.b,v.a] for k,v in m.m_SavedProperties.m_Colors},'floats':dict(m.m_SavedProperties.m_Floats)}
(P/'saida/materiais_composicao_unity.json').write_text(json.dumps(composicao,indent=2)+'\n')
# Rampas são definidas globalmente no jogo, não serializadas em cada material.
for o in carregar(RAIZ/'chara/mt_ramp_00.unity3d').objects:
 if o.type.name=='Texture2D':
  tex=o.read();tex.image.save(T/(tex.m_Name+'.png'))
def abrir(n,size=None):
 im=Image.open(T/n).convert('RGBA')
 if size and im.size!=size:im=im.resize(size,Image.Resampling.LANCZOS)
 return np.asarray(im,dtype=float)/255

def guardar(n,a):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(S/n)
def sobre(a,n,c):
 if not n or not (T/n).exists():return
 b=abrir(n,(a.shape[1],a.shape[0]));w=b[:,:,3:4]*c[3];a[:,:,:3]=a[:,:,:3]*(1-w)+np.array(c[:3])*w

def pele(face):
 nome='cf_face_00' if face else 'cf_body_00'
 # _Color2 atua no verde da máscara; _MainTex conserva boca/detalhes pintados.
 main_nome=nome+'_t.png' if face else itens['corpo'].get('mainTex',nome+'_t')+'.png'
 mask_nome=nome+'_mc.png' if face else itens['corpo'].get('colorMask',nome+'_mc')+'.png'
 main=abrir(main_nome) if (T/main_nome).exists() else np.ones((1024,1024,4))
 size=(main.shape[1],main.shape[0]);a=main.copy();a[:,:,:3]*=C['skinMainColor'][:3]
 if (T/mask_nome).exists():
  mask=abrir(mask_nome,size);a[:,:,:3]=main[:,:,:3]*(np.array(C['skinMainColor'][:3])*(1-mask[:,:,1:2])+np.array(C['skinSubColor'][:3])*mask[:,:,1:2])
 if face and "maquiagem_cheekId" in cena["texturas_card"]:
  # _tex4uv serializado em cf_m_face_create: posicionamento de blush separado
  # da atlas principal. Mantém a imagem fonte; amostra só a região do decal.
  b=abrir(cena['texturas_card']['maquiagem_cheekId'])
  yy,xx=np.mgrid[0:a.shape[0],0:a.shape[1]]
  layout=composicao['cf_m_face_create']['cores']['_tex4uv']
  u=(xx/a.shape[1]-layout[0])*(1-layout[2])+.5;v=(yy/a.shape[0]-layout[1])*abs(layout[3])+.5
  valido=(u>=0)&(u<=1)&(v>=0)&(v<=1)
  w=b[np.clip((v*b.shape[0]).astype(int),0,b.shape[0]-1),np.clip((u*b.shape[1]).astype(int),0,b.shape[1]-1),3:4]*valido[:,:,None]*F['baseMakeup']['cheekColor'][3]
  a[:,:,:3]=a[:,:,:3]*(1-w)+np.array(F['baseMakeup']['cheekColor'][:3])*w
  # Boca do MainTex já tem a região correta; não pintar toda a face com lipColor.
  # Pinta do card tem layout independente: deixada ao overlay do jogo, documentada.
 a[:,:,3]=1; n='pele_rosto.png' if face else 'pele_corpo.png';guardar(n,a);return n
pele_face=pele(True);pele_body=pele(False)
manifest={};fontes={};shaders={};bundles_vistos=set()
for p in cena['pecas']:
 tipo=p['selecao']['tipo'];item=p['selecao'];cfg=item.get('config')
 for mal in p['malhas']:
  if not mal.get('exportar',mal['ativo']):continue
  for mat in mal['materiais']:
   if mat is None:continue
   key=tipo+'__'+mat['nome'];fontes[key]=mat
   if key in manifest:continue
   tex=dict(mat['texturas']);co=mat['cores'];fl=mat['floats'];go=mal['go']; cabelo=tipo.startswith('cabelo');face=go=='cf_O_face';skin=face or go=='o_body_a';olhos=any(s in go for s in ['hitomi','eyeline','mayuge','noseline','tooth','gag_eye'])
   conf={'texturas':{},'cor':[1,1,1,1],'cor2':[1,1,1,1],'cor3':[1,1,1,1], 'sombra':co.get('_ShadowColor',co.get('_shadowcolor',[.75,.8,.9,1])), 'linha':co.get('_LineColor',[.5,.5,.5,.5]),'rosto':face,'olhos':olhos,'cabelo':cabelo,'alpha':any(s in mat['nome'] for s in ['mayuge','eyeline','noseline','hitomi_00','gageye']), 'rim':fl.get('_rimV',0)*.14,'rim_potencia':2+fl.get('_rimpower',.5)*4,'normal_forca':.35,'sombra_extensao':fl.get('_ShadowExtend',.5),'especular':fl.get('_SpecularPower',0), 'especular_altura':fl.get('_SpeclarHeight',.985),'linha_r':fl.get('_DetailRLineR',0),'linha_g':fl.get('_DetailBLineG',0)}
   conf['contorno']=0 if olhos or face else fl.get('_linewidth',.3)*.004
   conf['cor_contorno']=cfg['outlineColor'] if cabelo else [x*.26 for x in (C['skinSubColor'] if skin else ((cfg['color'][0] if tipo.startswith('acessorio_') else cfg['colorInfo'][0]['baseColor']) if cfg else [.3,.25,.3,1]))[:3]]+[1]
   if skin:conf['cor_contorno']=C['skinSubColor'][:3]+[1]
   if cabelo:
    conf.update(cor=cfg['baseColor'],cor2=cfg['startColor'],cor3=cfg['endColor']);tex['_HairGloss']=cena['texturas_card']['brilho_cabelo'];tex['_RampG']=cores_kk['rampa_global']
   elif tipo.startswith('acessorio_'):
    comp=p.get('componente',{});cores=cfg['color']
    if mal.get('grupo_cor')=='rendHair':
     conf['cor']=conf['cor2']=conf['cor3']=card['Custom']['cabelo']['parts'][0]['startColor']
    elif mal.get('grupo_cor')=='rendAlpha':
     conf['alpha']=True;conf['cor']=cores[3];conf['contorno']=0
    else:
     for idx,param in enumerate(['cor','cor2','cor3']):
      conf[param]=cores[idx] if comp.get('useColor%02d'%(idx+1),False) else co.get(['_Color','_Color2','_Color3'][idx],[1,1,1,1])
    if comp.get('noOutline'):conf['contorno']=0
   elif tipo.startswith('roupa'):
    conf.update(cor=cfg['colorInfo'][0]['baseColor'],cor2=cfg['colorInfo'][1]['baseColor'],cor3=cfg['colorInfo'][2]['baseColor'])
    for k,field in [('_MainTex','MainTex'),('_ColorMask','ColorMaskTex')]:
     if item.get(field,'0')!='0':tex[k]=item[field]+'.png'
   elif go=='o_tang':
    conf['cor']=co.get('_Color',[1,.7,.7,1])
    conf['cor2']=co.get('_Color2',[0,0,0,1])
    conf['cor3']=co.get('_Color3',[0,0,0,1])
   elif 'gag_eye' in go:
    tex['_MainTex']=itens['expressao_card'].get('MainTex','cf_t_gageye_01')+'.png'
   elif skin:
    conf['sobre_cores']={}
    if face:
     if 'maquiagem_eyeshadowId' in cena['texturas_card']:
      tex['_overtex3']=cena['texturas_card']['maquiagem_eyeshadowId']
      conf['sobre_cores']['_overtex3']=F['baseMakeup']['eyeshadowColor']
     else:tex.pop('_overtex3',None)
     # UV3 do Unity é uma transformação afim de UV0 nesta cabeça.
     dados=np.load(P/'trabalho/malhas'/(mal['nome']+'.npz'))
     uv=dados['UV'][:,:2].copy();uv[:,1]=1-uv[:,1]
     aux=dados['UV3'].copy();aux[:,1]=1-aux[:,1]
     coef=np.linalg.lstsq(np.c_[uv,np.ones(len(uv))],aux,rcond=None)[0]
     erro=float(np.max(abs(np.c_[uv,np.ones(len(uv))]@coef-aux)))
     if erro>1e-4:raise ValueError('UV de maquiagem não afim: exportar atributo extra')
     conf['uv_maquiagem']=[float(coef[0,0]),float(coef[1,1]),float(coef[2,0]),float(coef[2,1])]
     conf['erro_uv_maquiagem']=erro
    conf['sombra']=C['skinSubColor']
    if face:conf['linha']=C['skinSubColor']
    tex['_MainTex']=pele_face if face else pele_body
   else:
    # Olhos/traços: camadas em resolução nativa; sem sombra da luz.
    n=cena['texturas_card'].get('iris_0') if 'hitomi_00' in mat['nome'] else None
    if n:
     a=compor_iris(abrir(n),abrir(cena['texturas_card']['gradiente_0']),F['pupil'][0])
     for tt,cc in [('rosto_hlUpId','hlUpColor'),('rosto_hlDownId','hlDownColor')]:
      b=abrir(cena['texturas_card'][tt],(a.shape[1],a.shape[0]));c=F[cc];w=b[:,:,3:4]*c[3]
      a[:,:,:3]=srgb(linear(a[:,:,:3])*(1-w)+linear(b[:,:,:3])*linear(c[:3])*w)
     tex['_MainTex']='iris.png';guardar('iris.png',a)
    elif 'sirome' in mat['nome']:
     a=abrir(cena['texturas_card']['rosto_whiteId']);w=a[:,:,0:1];a[:,:,:3]=np.array(F['whiteBaseColor'][:3])*w+np.array(F['whiteSubColor'][:3])*(1-w);a[:,:,3]=1;guardar('esclera.png',a);tex['_MainTex']='esclera.png'
    elif 'mayuge' in go:tex['_MainTex']=cena['texturas_card']['rosto_eyebrowId'];conf['cor']=F['eyebrowColor']
    elif 'eyeline' in go:
     if 'kage' in mat['nome']:conf['cor']=C['skinSubColor']
     else:tex['_MainTex']=cena['texturas_card']['rosto_eyelineDownId' if 'low' in go else 'rosto_eyelineUpId'];conf['cor']=F['eyelineColor']
    elif 'noseline' in go:tex['_MainTex']=cena['texturas_card']['rosto_noseId'];conf['cor']=C['skinSubColor']
   for k,v in tex.items():
    if (T/v).exists():shutil.copy2(T/v,S/v)
    if (S/v).exists():conf['texturas'][k]=v
   conf['texturas']['_RampG']=cores_kk['rampa_global']
   if not skin and not cabelo and not tipo.startswith('acessorio_') and '_ColorMask' not in tex:conf['cor']=conf['cor'] if olhos else co.get('_Color',[1,1,1,1])
   manifest[key]=conf
   if go=='o_body_a':
    textura=cena['texturas_card']['corpo_nipId']
    shutil.copy2(T/textura,S/textura)
    configurar_areola(conf,C,mat,textura,cena['espacos_texturas_card']['corpo_nipId'])
    # ChaControl.ChangeSettingUnderhair/Color: _overtex2 e _overcolor2.
    pelos=cena['texturas_card']['corpo_underhairId']
    shutil.copy2(T/pelos,S/pelos)
    conf['texturas']['_overtex2']=pelos
    conf.setdefault('sobre_cores',{})['_overtex2']=C['underhairColor']
    uv=mat['uv_texturas']['_overtex2']
    conf['uv_pelos_unity']=[*uv['escala'],*uv['offset']]
    conf['pelos_srgb']=cena['espacos_texturas_card']['corpo_underhairId']==1
    conf['origem_corpo']=itens['corpo']['guid']
   # Texto exportado contém propriedades/passes; DXBC não é descompilado pelo UnityPy.
   if item['MainAB'] in bundles_vistos:continue
   bundles_vistos.add(item['MainAB'])
   for o in carregar(RAIZ/item['MainAB']).objects:
    if o.type.name=='Shader':
     sh=o.read();name=sh.m_ParsedForm.m_Name
     if name not in shaders:
      shaders[name]=True;out=P/'saida/shaders_unity';out.mkdir(exist_ok=True);(out/(name.replace('/','_')+'.shader')).write_text(sh.export())
for f in T.glob('gt_ramp_*.png'):shutil.copy2(f,S/f.name)
(P/'saida/materiais_kk.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(P/'saida/materiais_unity.json').write_text(json.dumps(fontes,ensure_ascii=False,indent=2)+'\n')
(P/'saida/texturas_originais.json').write_text(json.dumps({f.name:list(Image.open(f).size) for f in S.glob('*.png')},indent=2)+'\n')
print(len(manifest),'materiais KK preparados, em resolução original')
