#!/usr/bin/env python3
"""Extrai somente a seleção do card; usa o leitor de geometria do Samabake."""
import os
import json,pathlib,os,hashlib,numpy as np
from carregar import carregar,RAIZ
import geometria
from regras_malhas import decisao
PASTA=pathlib.Path(os.environ.get("BONECA_DIR", str(pathlib.Path(__file__).resolve().parent)))
TRAB=PASTA/'trabalho'
def main():
 for p in ['tex','malhas']:(TRAB/p).mkdir(parents=True,exist_ok=True)
 lista=json.loads((PASTA/'pecas.json').read_text())['pecas'];feitas=set();pecas=[]
 for item in lista:
  if 'MainData' not in item or item['MainData']=='p_dummy':continue
  # Roupa de baixo não aparece sob o conjunto; sapatos internos não são os ativos do card.
  if item['tipo']=='roupa_7':continue
  if item['tipo']=='roupa_2' and next((i for i in lista if i['tipo']=='roupa_0'),{}).get('NotBra')=='1':continue
  print('Extraindo',item['tipo'],item['MainData'],flush=True)
  p=geometria.extrair(str(TRAB),item.get('fonte',str(RAIZ/item['MainAB'])),item['MainData'],feitas);p['selecao']=item
  if item['tipo']=='corpo':
   # UncensorSelector troca a geometria do corpo e conserva o material criado
   # por InitBaseCustomTextureBody. O prefab do mod tem um slot nulo intencional.
   materiais=carregar(RAIZ/item.get('materialAB','chara/mm_base.unity3d'))
   original=next(o for o in materiais.objects if o.type.name=='Material' and o.peek_name()==item.get('material','cf_m_body'))
   mat=geometria.material(original,str(TRAB),feitas)
   for m in p['malhas']:
    if m['go']=='o_body_a':m['materiais']=[mat for _ in range(m['submalhas'])]
  if item['tipo']=='cabeca':
   expressao=next(i for i in lista if i['tipo']=='expressao_card')
   for m in p['malhas']:
    if 'gag_eye' in m['go']:
     # Só seleciona a malha gag quando o padrão realmente usa uma textura gag.
     m['ativo']=expressao.get('MainTex','0') not in ['0',''] and m['go']=='cf_O_gag_eye_01'
  if item['tipo'].startswith('roupa_'):
   # Estado cotidiano vestido: os prefabs contêm também versões retiradas.
   import re
   pais={h['nome']:h['pai'] for h in p['hierarquia']}
   for m in p['malhas']:
    n=m['go']
    while n:
     if re.fullmatch(r'n_(top|bot|bra|shorts|gloves|panst|socks|shoes)_[bc]',n):m['ativo']=False;m['motivo_inativo']='variante de roupa parcialmente retirada: '+n
     n=pais.get(n)
  if item['tipo'].startswith('acessorio_'):
   # Slots podem repetir o mesmo prefab: isolar TODOS os nomes de nós e malhas.
   prefixo=item['tipo']+'__'
   for h in p['hierarquia']:
    h['original']=h['nome'];h['nome']=prefixo+h['nome']
    if h['pai']:h['pai']=prefixo+h['pai']
   for m in p['malhas']:
    antigo=TRAB/'malhas'/(m['nome']+'.npz');novo=prefixo+m['nome']
    antigo.rename(TRAB/'malhas'/(novo+'.npz'));m['nome']=novo
    m['bones']=[prefixo+n for n in m['bones']]
    m['go']=prefixo+m['go']
  pecas.append(p)
 # Rig canônico é o mesmo dos clipes, guardado no próprio bundle base.
 env=carregar(RAIZ/'chara/oo_base.unity3d');g,t=geometria.achar_prefab(env,'p_cf_body_bone');hier=[];por_id={};geometria.andar(t,np.eye(4),None,hier,por_id)
 corpo=next(i for i in lista if i['tipo']=='corpo')
 corpo_env=carregar(corpo.get('fonte',RAIZ/corpo['MainAB']))
 for o in corpo_env.objects:
  if o.type.name=='Texture2D' and o.peek_name() in [corpo.get('mainTex','cf_body_00_t'),corpo.get('colorMask','cf_body_00_mc')]:
   tex=o.read();tex.image.save(TRAB/'tex'/(tex.m_Name+'.png'))
 # Texturas externas indicadas nas listas, além das já referenciadas pelos materiais.
 texturas={};espacos={}
 for item in lista:
  caminhos=set(v for k,v in item.items() if isinstance(v,str) and v.startswith('chara/') and not k.startswith('Thumb') and 'thumb' not in v)
  for caminho in caminhos:
   e=carregar(RAIZ/caminho)
   nomes=set(v for k,v in item.items() if isinstance(v,str) and not k.startswith('Thumb'))
   for o in e.objects:
    if o.type.name=='Texture2D' and o.peek_name() in nomes:
     tex=o.read();nome=tex.m_Name+'.png';tex.image.save(TRAB/'tex'/nome);texturas[item['tipo']]=nome;espacos[item['tipo']]=int(tex.m_ColorSpace)
 card=json.loads((PASTA/'card.json').read_text());cobertura=[]
 for p in pecas:
  for m in p['malhas']:
   exportar,motivo=decisao(m,p['selecao']['tipo'],card)
   m['exportar']=exportar;m['decisao_exportacao']=motivo
   with np.load(TRAB/'malhas'/(m['nome']+'.npz')) as a:
    regioes={}
    for grupo,match in [('genital',lambda n:'Vagina' in n or n=='cf_j_kokan'),('anal',lambda n:n in ('cf_j_ana','cf_s_ana')),('mamilos',lambda n:'bnip' in n)]:
     indices=[i for i,n in enumerate(m['bones']) if match(n)]
     pesos=np.where(np.isin(a['BI'],indices),a['BW'],0).sum(axis=1)
     regioes[grupo]={'vertices_com_peso':int(np.count_nonzero(pesos>0)), 'ossos':[m['bones'][i] for i in indices]}
    cobertura.append({'tipo':p['selecao']['tipo'],'nome':m['go'],'extraida':True,'selecionada':exportar,'motivo':motivo,
     'vertices':len(a['P']),'triangulos_por_submalha':[len(a['T'+str(i)]) for i in range(m['submalhas'])],
     'indices_sha256':[hashlib.sha256(a['T'+str(i)].astype('<u4').tobytes()).hexdigest() for i in range(m['submalhas'])],
     'atributos':list(a.files),'morphs':m['shapes'],'frames_morph':m.get('frames_morph',{}),
     'pesos_regionais':regioes,'materiais':[v['nome'] if v else None for v in m['materiais']],
     'origem':p['selecao'].get('fonte',p['selecao']['MainAB'])})
 (PASTA/'saida/geometria_origem.json').write_text(json.dumps(cobertura,ensure_ascii=False,indent=2)+'\n')
 (TRAB/'cena.json').write_text(json.dumps(dict(pecas=pecas,esqueleto=hier,texturas_card=texturas,espacos_texturas_card=espacos),ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
