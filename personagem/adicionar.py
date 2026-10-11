#!/usr/bin/env python3
"""Um comando: copiar card → gerar → importar → provar no Xvnc privado."""
import pathlib,sys,os,json,hashlib,re,unicodedata,subprocess,shutil,fcntl
from ler_card import ler,legivel
R=pathlib.Path(__file__).resolve().parent.parent
if len(sys.argv)!=2:sys.exit('Uso: ./adicionar-boneca.sh caminho/do/card.png')
fonte=pathlib.Path(sys.argv[1]).expanduser().resolve()
try:card=legivel(ler(fonte))
except Exception as erro:sys.exit('Não foi possível ler o card: '+str(erro))
if card['Parameter'].get('sex')!=1:sys.exit('Este pipeline exige card feminino.')
nome=' '.join(str(card['Parameter'].get(k,'')) for k in ['lastname','firstname']).strip() or fonte.stem
slug=re.sub('[^a-z0-9]+','-',unicodedata.normalize('NFKD',nome).encode('ascii','ignore').decode().lower()).strip('-') or 'boneca'
base=R/'bonecas';base.mkdir(exist_ok=True)
with (base/'.geracao.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 dest=base/slug
 for existente in base.iterdir():
  if (existente/"card.png").is_file() and (existente/"card.png").read_bytes()==fonte.read_bytes():
   dest=existente;break
 if (dest/'card.png').exists() and (dest/'card.png').read_bytes()!=fonte.read_bytes():dest=base/(slug+'-'+hashlib.sha256(fonte.read_bytes()).hexdigest()[:8])
 dest.mkdir(exist_ok=True);(dest/'saida').mkdir(exist_ok=True)
 if fonte!=dest/'card.png':shutil.copy2(fonte,dest/'card.png')
 env=dict(os.environ,BONECA_DIR=str(dest))
 try:
  with (dest/'saida/geracao.log').open('w') as log:
   subprocess.run([str(R/'personagem/gerar.sh')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 finally:
  shutil.rmtree(dest/'trabalho',ignore_errors=True)
  for n in ['personagem.blend','personagem.blend1']:(dest/'saida'/n).unlink(missing_ok=True)
 # Prova faz parte obrigatória do comando; seu erro deixa evidência e retorna falha.
 subprocess.run([sys.executable,str(R/'personagem/provar_visual.py')],env=env,check=True)
 # Casual (5) e pijama (6): sem elas o mascote usa o uniforme, então falha só avisa.
 if os.environ.get('KK_SO_UNIFORME')!='1':
  for c in (5,6):
   (dest/'coordenadas'/('coord_%d'%c)).mkdir(parents=True,exist_ok=True)
   with (dest/'coordenadas'/('coord_%d'%c)/'geracao.log').open('w') as log:
    r=subprocess.run([str(R/'personagem/gerar.sh')],env=dict(env,KK_COORDENADA=str(c)),stdout=log,stderr=subprocess.STDOUT)
   print('Coordenada',c,'ok' if r.returncode==0 else 'FALHOU (ver coordenadas/coord_%d/geracao.log)'%c)
 # Vozes originais da personalidade (Whisper na primeira vez); opcional.
 if os.environ.get('KK_SEM_VOZES')!='1':
  r=subprocess.run([sys.executable,str(R/'mascote/vozes/preparar.py'),dest.name])
  if r.returncode:print('Vozes não preparadas; a boneca usa as interjeições padrão. Tente: mascote/vozes/preparar.py',dest.name)
 print('Boneca pronta:',dest,'— comparação em saida/comparacao_render.png')
