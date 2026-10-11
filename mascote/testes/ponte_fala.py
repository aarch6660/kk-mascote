#!/usr/bin/env python3
import concurrent.futures
import json
import os
from pathlib import Path
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import falar
casos=0
def check(ok):
 global casos
 casos+=1
 assert ok
for texto,emocao in [('Estou triste com isso.','Tristeza'),('Sinto muito pela perda.','Tristeza'),('Não estou triste.','Neutra'),('Deu certo, estou feliz!','Felicidade'),('Estou com medo.','Medo'),('Estou furiosa!','Raiva'),('Estou preocupada.','Preocupação'),('Conte comigo.','Confiança'),('Uau, que surpresa!','Surpresa'),('Olá, tudo bem?','Neutra')]:
 check(falar.emocao_texto(texto)==emocao)
for emocao in ['Timidez','Pensativa','Seriedade','Tédio']:
 check(falar.validar('Uma resposta.','Codex',emocao)['emocao']==emocao)
check(falar.validar('Olá','Codex','Felicidade','stand_joy_02')['gesto']=='stand_joy_02')
try:falar.validar('Olá','Codex','Neutra','dormir_00')
except ValueError:check(True)
else:check(False)
check(falar.validar('Estou triste.','Codex','Felicidade')['emocao']=='Felicidade')
for texto,autor,emocao in [('', 'Codex','auto'),('a'*1201,'Claude','auto'),('Teste','a'*49,'auto'),('Teste\x00','Codex','auto'),('Teste','Codex','inventada')]:
 try:falar.validar(texto,autor,emocao)
 except ValueError:check(True)
 else:check(False)
with tempfile.TemporaryDirectory(prefix='kk-fala-python-') as pasta:
 runtime=Path(pasta)
 pid=os.getpid()
 start=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]
 (runtime/'pids.json').write_text(json.dumps({'godot':pid,'godot_starttime':start}))
 (runtime/'status.json').write_text(json.dumps({'pid':pid}))
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  resultados=list(pool.map(lambda i:falar.enviar('Mensagem simultânea %d: olá!'%i,'Codex' if i%2 else 'Claude',runtime=runtime,voz=False),range(30)))
 arquivos=list((runtime/'falas').glob('*.json'))
 check(len(arquivos)==30 and len({r['id'] for r in resultados})==30)
 for arquivo in arquivos:
  d=json.loads(arquivo.read_text())
  check(d['pid_destino']==pid and d['id']==arquivo.stem and d['autor'] in ['Codex','Claude'])
 check(not list((runtime/'falas').glob('*.tmp')))
 (runtime/'pids.json').write_text(json.dumps({'godot':pid,'godot_starttime':'invalido'}))
 try:falar.enviar('Teste','Codex',runtime=runtime,voz=False)
 except RuntimeError:check(True)
 else:check(False)
print(json.dumps({'casos':casos,'passou':True,'erros':[]}))
