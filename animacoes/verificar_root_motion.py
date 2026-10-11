#!/usr/bin/env python3
"""Mede translações globais da raiz nos GLBs exportados, sem acessar o jogo."""
import pathlib,json,struct,numpy as np
P=pathlib.Path(__file__).resolve().parent
def medir(nome):
 b=(P/'exportados'/(nome+'.glb')).read_bytes();n=struct.unpack_from('<I',b,12)[0];d=json.loads(b[20:20+n]);raw=b[28+n:]
 def ler(i):
  a=d['accessors'][i];v=d['bufferViews'][a['bufferView']];c={'SCALAR':1,'VEC3':3,'VEC4':4}[a['type']]
  return np.frombuffer(raw,dtype='<f4',count=a['count']*c,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,c)
 out={}
 for ch in d['animations'][0]['channels']:
  name=d['nodes'][ch['target']['node']]['name']
  if ch['target']['path']=='translation' and name in ['p_cf_body_bone','cf_j_root','cf_n_height','cf_j_hips']:
   v=ler(d['animations'][0]['samplers'][ch['sampler']]['output']);out[name]=dict(inicio=v[0].tolist(),fim=v[-1].tolist(),deslocamento=(v[-1]-v[0]).tolist(),amplitude=np.ptp(v,axis=0).tolist())
 root=out.get('cf_j_root');assert root is not None
 no_lugar=max(root['amplitude'])<1e-5
 return dict(clipe=nome,raiz=out,no_lugar=no_lugar,observacao='cf_j_root permanece fixo; cf_j_hips oscila no ciclo, sem deslocamento acumulado.' if no_lugar else 'A raiz desloca-se; requer variante no lugar.')
if __name__=='__main__':
 r=[medir(n) for n in ['caminhar','caminhar_zangada']];(P/'root_motion.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print([(x['clipe'],x['no_lugar']) for x in r])
