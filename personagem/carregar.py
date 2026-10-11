"""Carrega somente bundles chara selecionados e dependências nessa mesma pasta."""
import os
import pathlib,json,gc,UnityPy
from mods_corpo import inventario, fonte_bundle, ler_fonte
PASTA=pathlib.Path(__file__).resolve().parent
RAIZ=pathlib.Path(os.environ.get('KK_JOGO') or pathlib.Path.home()/'Downloads/Koikatsu.Party/Koikatsu Party')/'abdata'
def permitido(p):
 p=pathlib.Path(p).resolve()
 if not p.is_relative_to(RAIZ/'chara'):raise ValueError(f'Bundle fora de chara: {p}')
 return p

def indice():
 arq=PASTA/'indice_cab.json'
 if arq.exists():return json.loads(arq.read_text())
 idx={}
 for p in sorted((RAIZ/'chara').glob('*.unity3d')):
  env=UnityPy.load(str(p))
  for f in env.assets:idx[f.name.lower()]=str(p.relative_to(RAIZ))
  del env;gc.collect()
 arq.write_text(json.dumps(idx,indent=2)+'\n');return idx
IDX=None
MOD_IDX=None
def indice_mods():
 global MOD_IDX
 if MOD_IDX is not None:return MOD_IDX
 MOD_IDX={}
 for relativo,fontes in inventario()['bundles'].items():
  for fonte in fontes:
   env=UnityPy.load(ler_fonte(fonte))
   for f in env.assets:
    # Unity CABs são identidades de arquivos serializados, não nomes de assets.
    key=f.name.lower()
    if key in MOD_IDX and MOD_IDX[key]!=fonte:
     raise ValueError('CAB de mods ambíguo: '+key)
    MOD_IDX[key]=fonte
 return MOD_IDX
def carregar(*caminhos):
 global IDX
 if IDX is None:IDX=indice()
 env=UnityPy.Environment();vistos=set();fila=list(caminhos)
 while fila:
  entry=fila.pop()
  if isinstance(entry,dict):
   fonte=entry;s=json.dumps(fonte,sort_keys=True)
  else:
   p=permitido(entry);fonte=fonte_bundle(str(p.relative_to(RAIZ)));s=str(p)
  if s in vistos:continue
  vistos.add(s);env.load_file(ler_fonte(fonte),name=fonte.get('membro',fonte['arquivo']))
  for f in list(env.assets):
   for ext in f.externals:
    key=pathlib.PurePosixPath(ext.path).name.lower()
    if any(x.name.lower()==key for x in env.assets):continue
    dep=IDX.get(key)
    if dep and str(RAIZ/dep) not in vistos:fila.append(RAIZ/dep)
    elif not dep:
     mod=indice_mods().get(key)
     if mod and json.dumps(mod,sort_keys=True) not in vistos:fila.append(mod)
 return env
