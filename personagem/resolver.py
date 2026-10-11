#!/usr/bin/env python3
"""Resolve IDs pelas tabelas ChaListData originais. Acesso ao jogo somente leitura."""
import os
import pathlib,json,msgpack,UnityPy
from mods_corpo import selecionar, escrever_inventario
PASTA=pathlib.Path(os.environ.get("BONECA_DIR", str(pathlib.Path(__file__).resolve().parent)))
JOGO=pathlib.Path(os.environ.get('KK_JOGO') or pathlib.Path.home()/'Downloads/Koikatsu.Party/Koikatsu Party')/'abdata'
def coordenada():
 valor=os.environ.get('KK_COORDENADA','0')
 if valor not in [str(i) for i in range(7)]:raise ValueError('KK_COORDENADA precisa ser um inteiro de 0 a 6')
 return int(valor)
def pasta_coordenada(pasta,n):
 if n==0 or (pasta.parent.name=='coordenadas' and pasta.name=='coord_'+str(n)):return pasta
 return pasta/'coordenadas'/('coord_'+str(n))
def tabelas():
 resultado={}
 for bundle in sorted((JOGO/'list/characustom').glob('*.unity3d')):
  env=UnityPy.load(str(bundle))
  for o in env.objects:
   if o.type.name!='TextAsset':continue
   t=o.read();raw=t.m_Script.encode('utf-8','surrogateescape')
   try:d=msgpack.unpackb(raw,raw=False,strict_map_key=False)
   except Exception:continue
   if not isinstance(d,dict) or 'dictList' not in d:continue
   categoria=t.m_Name.rsplit('_',1)[0]
   for id,campos in d['dictList'].items():
    resultado[(categoria,int(id))]={'lista':str(bundle.relative_to(JOGO)), 'tabela':t.m_Name,**dict(zip(d['lstKey'],campos))}
 return resultado
if __name__=='__main__':
 c=json.loads((PASTA/'card.json').read_text());n=coordenada();coord=c['Coordinate'][n];t=tabelas();out=[]
 def add(tipo,cat,id,config=None):
  row=t.get((cat,id))
  if row is None:raise ValueError(f'ID não encontrado: {cat}/{id}')
  out.append(dict(tipo=tipo,categoria=cat,id=id,config=config,**row))
 out.append(selecionar(c))
 add('cabeca','bo_head',c['Custom']['rosto']['headId'])
 for i,cat in enumerate(['bo_hair_b','bo_hair_f','bo_hair_s','bo_hair_o']):add('cabelo_'+str(i),cat,c['Custom']['cabelo']['parts'][i]['id'],c['Custom']['cabelo']['parts'][i])
 for i,cat in enumerate(['co_top','co_bot','co_bra','co_shorts','co_gloves','co_panst','co_socks','co_shoes','co_shoes']):
  parte=coord['roupa']['parts'][i]
  if parte['id']!=0:add('roupa_'+str(i),cat,parte['id'],parte)
 f=c['Custom']['rosto']
 for chave,cat in [('detailId','mt_face_detail'),('eyebrowId','mt_eyebrow'),('noseId','mt_nose'),('hlUpId','mt_eye_hi_up'),('hlDownId','mt_eye_hi_down'),('whiteId','mt_eye_white'),('eyelineUpId','mt_eyeline_up'),('eyelineDownId','mt_eyeline_down'),('moleId','mt_mole'),('lipLineId','mt_lipline')]:add('rosto_'+chave,cat,f[chave])
 for i,olho in enumerate(f['pupil']):
  add('iris_'+str(i),'mt_eye',olho['id'],olho);add('gradiente_'+str(i),'mt_eye_gradation',olho['gradMaskId'])
 for chave,cat in [('eyeshadowId','mt_eyeshadow'),('cheekId','mt_cheek'),('lipId','mt_lip')]:add('maquiagem_'+chave,cat,f['baseMakeup'][chave])
 b=c['Custom']['corpo']
 for chave,cat in [('detailId','mt_body_detail'),('sunburnId','mt_sunburn'),('nipId','mt_nip'),('underhairId','mt_underhair')]:add('corpo_'+chave,cat,b[chave])
 for i,id in enumerate(b['paintId']):add('pintura_corpo_'+str(i),'mt_body_paint',id)
 for i,id in enumerate(f['baseMakeup']['paintId']):add('pintura_rosto_'+str(i),'mt_face_paint',id)
 # skinId é serializado, mas não é consultado pelo ChaControl desta versão.
 # Não existe categoria mt_*_skin nas listas: a pele usa MainTex do prefab + cores.
 for tipo,dados in [('corpo',b),('rosto',f)]:
  out.append(dict(tipo=tipo+'_skinId',id=dados['skinId'],origem='Campo legado sem leitura no ChaControl local; pele procedural do prefab.'))
 cats=['ao_none','ao_hair','ao_head','ao_face','ao_neck','ao_body','ao_waist','ao_leg','ao_arm','ao_hand','ao_kokan']
 for i,parte in enumerate(coord['acessorios']['parts']):
  if parte['type']==120:continue
  add('acessorio_'+str(i),cats[parte['type']-120],parte['id'],parte)
 add('brilho_cabelo','mt_hairgloss',c['Custom']['cabelo']['glossId'])
 add('expressao_card','cha_eyeset',c['Status']['eyesPtn'])
 for i,peca in enumerate(coord['roupa']['parts']):
  if peca['emblemeId']:add('emblema_'+str(i),'mt_emblem',peca['emblemeId'])
 destino=pasta_coordenada(PASTA,n);destino.mkdir(parents=True,exist_ok=True)
 (destino/'pecas.json').write_text(json.dumps({'coordenada':n,'pecas':out},ensure_ascii=False,indent=2)+'\n')
 (destino/'saida').mkdir(exist_ok=True)
 (destino/'saida/selecao_corpo.json').write_text(json.dumps(out[0],ensure_ascii=False,indent=2)+'\n')
 escrever_inventario(destino/'saida/mods_locais.json')
 for x in out:print(x['tipo'],x.get('MainAB'),x.get('MainData'),x.get('Name'))
