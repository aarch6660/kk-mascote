import json
import os
from pathlib import Path
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import eventos
import falar
casos = 0
def check(ok):
 global casos
 casos += 1
 assert ok
for face in [{'intensidade':-1},{'intensidade':2},{'intensidade':float('nan')},{'intensidade':True},{'olhos':'inventado'},{'outro':0}]:
 try: falar.validar_face(face)
 except ValueError: check(True)
 else: check(False)
with tempfile.TemporaryDirectory(prefix='kk-eventos-python-') as temp:
 r=Path(temp)
 pid=os.getpid()
 start=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]
 (r/'pids.json').write_text(json.dumps({'godot':pid,'godot_starttime':start}))
 (r/'status.json').write_text(json.dumps({'pid':pid,'sessao_eventos':'nova'}))
 (r/'eventos').mkdir()
 for i in range(1,4):
  (r/'eventos'/f'{i}.json').write_text(json.dumps({'pid':pid,'sessao':'nova','sequencia':i,'tipo':'clique','regiao':'Cabeça'}))
 (r/'eventos'/'antiga.json').write_text(json.dumps({'pid':pid,'sessao':'velha','sequencia':8}))
 check(len(eventos.ler(runtime=r)['eventos'])==3)
 check(len(eventos.ler(runtime=r)['eventos'])==3)
 check(len(eventos.ler(consumir=True,runtime=r)['eventos'])==3)
 check(eventos.ler(runtime=r)['eventos']==[])
 check(len(eventos.ler(autor='Claude',runtime=r)['eventos'])==3)
 (r/'eventos'/'5.json').write_text(json.dumps({'pid':pid,'sessao':'nova','sequencia':5}))
 check(eventos.ler(runtime=r)['lacuna'])
 check(falar.enviar('Teste','Codex','Felicidade',runtime=r,voz=False,face={'intensidade':0.5,'sobrancelhas':'Neutra'})['estado']=='enfileirada')
 msg=json.loads(next((r/'falas').glob('*.json')).read_text())
 check(msg['face']=={'intensidade':0.5,'sobrancelhas':'Neutra'})
 (r/'pids.json').write_text(json.dumps({'godot':pid,'godot_starttime':'reutilizado'}))
 try: eventos.ler(runtime=r)
 except RuntimeError: check(True)
 else: check(False)
print(json.dumps({'passou':True,'casos':casos}))
