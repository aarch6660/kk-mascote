"""Publica recursos portáteis; arquivos idênticos compartilham inode (hardlink)."""
import pathlib,json,os,hashlib,subprocess,re
RAIZ=pathlib.Path(__file__).resolve().parent.parent
P=pathlib.Path(os.environ.get('BONECA_DIR',str(RAIZ/'bonecas/chika-haruno')))
G=os.environ.get('GODOT_PERSONAGEM',str(pathlib.Path.home()/'.local/opt/godot/Godot_v4.7.2-stable_linux.x86_64'))
def publicar():
 # Deduplicação local, sem armazenar cópias extras das texturas do jogo.
 vistos={}
 for pasta in sorted((RAIZ/'bonecas').iterdir()):
  if not pasta.is_dir():continue
  for f in pasta.rglob('*.png'):
   if f.name=='card.png':continue
   chave=hashlib.sha256(f.read_bytes()).digest()
   if chave in vistos and f.stat().st_ino!=vistos[chave].stat().st_ino:
    temp=f.with_suffix('.dedup');os.link(vistos[chave],temp);os.replace(temp,f)

   vistos.setdefault(chave,f)
 cards=[]
 for pasta in sorted((RAIZ/'bonecas').iterdir()):
  if not (pasta/'saida/personagem.glb').exists():continue
  c=json.loads((pasta/'card.json').read_text())
  par=c['Parameter'];nome=' '.join(str(par.get(k,'')) for k in ['lastname','firstname']).strip() or pasta.name
  cards.append({'id':pasta.name,'nome':nome})
 (RAIZ/'bonecas/catalogo.json').write_text(json.dumps(cards,ensure_ascii=False,indent=2)+'\n')
 for app in ['visualizador','mascote']:
  dest=RAIZ/app/'bonecas'
  if not dest.exists():dest.symlink_to('../bonecas',target_is_directory=True)
  cmd=[G,'--headless','--path',str(RAIZ/app),'--editor','--import']
  with (P/'saida'/('importacao_'+app+'.log')).open('w') as log:
   subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
   for f in (RAIZ/'bonecas').rglob('*.png.import'):
    s=f.read_text()
    for k,v in {'compress/mode':'0','compress/normal_map':'2','mipmaps/generate':'true','detect_3d/compress_to':'0','process/fix_alpha_border':'false','process/size_limit':'0'}.items():
     s=re.sub(r'(?m)^'+re.escape(k)+r'=.*$',k+'='+v,s)
    f.write_text(s)
   subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
  texto=(P/'saida'/('importacao_'+app+'.log')).read_text()
  if 'SCRIPT ERROR' in texto or '\nERROR:' in texto:raise RuntimeError('Erro de importação em '+app)
if __name__=='__main__':
 publicar()
 with (P/'saida/validacao_rig.log').open('w') as log:
  subprocess.run([G,'--headless','--path',str(RAIZ/'mascote'),'--script','testes/bonecas.gd','--','--boneca='+os.environ.get('KK_BONECA_ID',P.name),'--coordenada='+os.environ.get('KK_COORDENADA','0')],stdout=log,stderr=subprocess.STDOUT,check=True)
 texto=(P/'saida/validacao_rig.log').read_text()
 if 'ERROR' in texto:raise RuntimeError('Falha na validação da boneca')
