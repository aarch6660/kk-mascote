"""Valida skinId legado, isolamento de slots e transformações reais de acessórios."""
import pathlib,json,struct,tempfile,subprocess,sys,os,numpy as np
R=pathlib.Path(__file__).resolve().parent.parent
from resolver import coordenada
coord=coordenada()
resultados=[]
for b in json.loads((R/'bonecas/catalogo.json').read_text()):
 p=R/'bonecas'/b['id']
 if coord:p=p/'coordenadas'/('coord_'+str(coord))
 c=json.loads((p/'card.json').read_text());raw=(p/'saida/personagem.glb').read_bytes();n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);nodes={x['name']:x for x in g['nodes'] if 'mesh' not in x}
 assert len(nodes)==len([x for x in g['nodes'] if 'mesh' not in x]),'Nome de osso duplicado'
 canonical=json.loads((R/'animacoes/esqueleto.json').read_text())['nodes']
 pais={g['nodes'][filho]['name']:pai['name'] for pai in g['nodes'] for filho in pai.get('children',[])}
 for osso in canonical:
  assert osso['name'] in nodes
  if osso['parent']>=0:assert pais[osso['name']]==canonical[osso['parent']]['name']
 data=raw[28+n:]
 for mesh in g['meshes']:
  for pr in mesh['primitives']:
   attrs=pr['attributes'];assert all(k in attrs for k in ['TANGENT','COLOR_0','JOINTS_0','WEIGHTS_0'])
   for k in ['TANGENT','COLOR_0','POSITION','NORMAL','WEIGHTS_0']:
    ac=g['accessors'][attrs[k]];bv=g['bufferViews'][ac['bufferView']]
    a=np.frombuffer(data,dtype='<f4',count=ac['count']*({'VEC3':3,'VEC4':4}[ac['type']]),offset=bv.get('byteOffset',0)+ac.get('byteOffset',0))
    assert np.isfinite(a).all(),k
    if k=='COLOR_0':assert a.min()>=0 and a.max()<=1
 count=0
 for slot,a in enumerate(c['Coordinate'][coord]['acessorios']['parts']):
  if a['type']==120:continue
  count+=1;nome='acessorio_'+str(slot)+'__N_move';move=nodes[nome]
  pos,rot,scl=a['addMove'][2][:3]
  assert np.allclose(move['translation'],np.array(pos)*[-.01,.01,.01],atol=1e-6)
  assert np.allclose(move['scale'],scl,atol=1e-6)
  # Quat Unity: Ry * Rx * Rz, seguido do espelhamento de X.
  def q(axis,ang):
   v=np.zeros(4);v[axis]=np.sin(np.deg2rad(ang)/2);v[3]=np.cos(np.deg2rad(ang)/2);return v
  def mul(a,b):return np.r_[a[3]*b[:3]+b[3]*a[:3]+np.cross(a[:3],b[:3]),a[3]*b[3]-a[:3]@b[:3]]
  quat=mul(mul(q(1,-rot[1]),q(0,rot[0])),q(2,-rot[2]));actual=np.array(move['rotation'])
  assert np.allclose(quat,actual,atol=1e-6) or np.allclose(-quat,actual,atol=1e-6)
  raiz=next(x for x in g['nodes'] if x['name']==a['parentKey'])
  prefab=next(x for x in nodes if x.startswith('acessorio_'+str(slot)+'__p_'))
  assert g['nodes'].index(nodes[prefab]) in raiz['children'],'Parent incorreto'
 resultados.append({'boneca':b['id'],'slots':count,'nomes_unicos':True,'parent_trs_card':True,'ossos_canonicos':len(canonical),'atributos_finitos':True})
with tempfile.TemporaryDirectory(prefix='kk-skinid-') as t:
 c=json.loads((R/'bonecas/chika-haruno/card.json').read_text());c['Custom']['corpo']['skinId']=7;c['Custom']['rosto']['skinId']=3;p=pathlib.Path(t);(p/'card.json').write_text(json.dumps(c))
 subprocess.run([sys.executable,str(R/'personagem/resolver.py')],env=dict(os.environ,BONECA_DIR=t,KK_COORDENADA='0'),stdout=subprocess.DEVNULL,check=True)
 pecas=json.loads((p/'pecas.json').read_text())['pecas'];assert next(x for x in pecas if x['tipo']=='corpo_skinId')['id']==7;assert next(x for x in pecas if x['tipo']=='rosto_skinId')['id']==3
out={'bonecas':resultados,'skinid_alternativo':{'corpo':7,'rosto':3,'aceitos':True}}
(R/'bonecas'/('testes_pipeline.json' if coord==0 else 'testes_pipeline_coord_%d.json' % coord)).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False))
