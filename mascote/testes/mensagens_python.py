import concurrent.futures,json,os,sys,tempfile,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import encenar,falar
casos=0
def check(ok):
 global casos
 casos+=1
 assert ok
for tom in encenar.CATALOGO['tons']:
 check(encenar.validar({'tom':tom,'leitura':0,'digitacao':5,'intensidade':1})['tom']==tom)
for dados in [[],{'tom':'raivosa'},{'tom':[]},{'leitura':-1},{'digitacao':6},{'duracao':61},{'duracao':0},{'intensidade':float('nan')},{'leitura':True},{'shell':'executar'}]:
 try: encenar.validar(dados)
 except ValueError: check(True)
 else: check(False)
texto='Olá, vamos conversar!'
cenas=[{'indice':0,'efeito':'espirais','som':'duvida'},{'indice':5,'efeito':'nenhum'}]
check(falar.validar(texto,'Codex',atuacao=cenas,preparacao={'tom':'confuso'})['preparacao']=={'tom':'confuso'})
for cenas_erradas in [[{'indice':0,'efeito':'outro'}],[{'indice':0,'som':'gemido'}],[{'indice':0,'efeito':[]}]]:
 try:falar.validar_atuacao(cenas_erradas,texto)
 except ValueError:check(True)
 else:check(False)
with tempfile.TemporaryDirectory(prefix='kk-mensagens-python-') as pasta:
 r=Path(pasta);pid=os.getpid();start=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]
 (r/'pids.json').write_text(json.dumps({'godot':pid,'godot_starttime':start}))
 (r/'status.json').write_text(json.dumps({'pid':pid}))
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  ids=list(pool.map(lambda i:encenar.enviar('Teste A' if i%2 else 'Teste B',tom='curioso',runtime=r)['id'],range(24)))
 arquivos=list((r/'atividades').glob('*.json'))
 check(len(arquivos)==24 and len(set(ids))==24)
 check(not list((r/'atividades').glob('*.tmp')))
 for p in arquivos:
  d=json.loads(p.read_text())
  check(d['pid_destino']==pid and d['tipo']=='leitura' and d['preparacao']['tom']=='curioso')
 falar.enviar(texto,'Codex',runtime=r,voz=False,preparacao={'tom':'surpreso'},atuacao=cenas)
 d=json.loads(next((r/'falas').glob('*.json')).read_text())
 check(d['preparacao']['tom']=='surpreso' and d['atuacao']==cenas)
 (r/'pids.json').write_text(json.dumps({'godot':pid,'godot_starttime':'outra-sessao'}))
 try:encenar.enviar(runtime=r)
 except RuntimeError:check(True)
 else:check(False)
 check(len(list((r/'atividades').glob('*.json')))==24)
print(json.dumps({'casos':casos,'passou':True}))
