import json,math,os,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import falar
casos=0
def check(ok):
 global casos
 casos+=1
 assert ok
check(set(falar.CATALOGO_FACIAL["caricatos"]).issubset(falar.EMOCOES))
check(len(falar.EMOCOES)==28)
check(falar.validar_face({'olhos':{'winkl_op':0.5},'sobrancelhas':{'gimoL_op':0.3},'vogais_amplas':True}))
for face in [{'olhos':{'def_op':0.8,'winkl_op':0.8}},{'boca':{'a_s_op':1}},{'olhos':{'inventado':1}},{'olhos':{'def_op':float('nan')}},{'olhos':{'def_op':True}},{'olhos':{}},{'vogais_amplas':1}]:
 try:falar.validar_face(face)
 except ValueError:check(True)
 else:check(False)
texto='Olá! Vamos testar.'
cenas=[{'indice':0,'emocao':'Curiosidade','face':{'intensidade':0.7},'movimento':'inclinar'},{'indice':5,'emocao':'Felicidade','gesto':'conversa_03','olhar':[0.4,0]}]
check(falar.validar_atuacao(cenas,texto)==cenas)
for atuacao in [[{'indice':True}],[{'indice':-1}],[{'indice':100}],[{'indice':3},{'indice':1}],[{'indice':0,'olhar':[2,0]}],[{'indice':0,'gesto':{}}],[{'indice':0,'movimento':'outro'}],[{'indice':0,'extra':1}]]:
 try:falar.validar_atuacao(atuacao,texto)
 except ValueError:check(True)
 else:check(False)
with tempfile.TemporaryDirectory(prefix='kk-atuacao-python-') as pasta:
 r=Path(pasta);pid=os.getpid();start=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]
 (r/'pids.json').write_text(json.dumps({'godot':pid,'godot_starttime':start}))
 (r/'status.json').write_text(json.dumps({'pid':pid}))
 falar.enviar(texto,'Codex',runtime=r,voz=False,atuacao=cenas)
 payload=json.loads(next((r/'falas').glob('*.json')).read_text())
 check(payload['atuacao']==cenas)
print(json.dumps({'casos':casos,'passou':True}))
