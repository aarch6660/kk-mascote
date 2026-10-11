#!/usr/bin/env python3
"""Ensaio de leitura e resposta com voz na instância ativa; cliques interrompem."""
import json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import encenar,eventos,falar

def main():
 eventos.ler('Codex',True)
 inicio=encenar.enviar('Codex',tom='ousado',intensidade=0.75)
 texto='Li sua ideia e preparei este pequeno ensaio. Uma proposta ousada? Primeiro, aquela surpresa! Depois eu penso, digito e respondo com um sorriso. E se aparecer uma confusão engraçada... olha as espirais nos olhos! Logo elas desaparecem e eu volto à conversa. Também há interjeições curtas de surpresa, dúvida e alegria, além de teclas suaves durante a digitação. Você pode desligar esses sons no menu Atuação por mensagens. O agente escolhe as reações pelo contexto do que você escreveu. Agora a Chika consegue representar melhor cada momento da conversa!'
 cenas=[
  {'indice':0,'emocao':'Curiosidade','face':{'intensidade':0.55},'gesto':'conversa_03','movimento':'inclinar'},
  {'indice':texto.index('Uma proposta'),'emocao':'Surpresa','face':{'intensidade':0.8},'gesto':'stand_oth_01','efeito':'surpresa'},
  {'indice':texto.index('Depois eu penso'),'emocao':'Sorriso travesso','face':{'intensidade':0.65},'gesto':'conversa_05','movimento':'concordar'},
  {'indice':texto.index('E se aparecer'),'emocao':'Dúvida','face':{'intensidade':0.65},'gesto':'conversa_03','movimento':'inclinar'},
  {'indice':texto.index('olha as espirais'),'efeito':'espirais'},
  {'indice':texto.index('Logo elas'),'emocao':'Felicidade','face':{'intensidade':0.55,'sobrancelhas':'Neutra'},'efeito':'nenhum','gesto':'conversa_05'},
  {'indice':texto.index('Agora a Chika'),'emocao':'Riso','face':{'intensidade':0.7,'sobrancelhas':'Neutra'},'gesto':'stand_joy_02','movimento':'concordar','efeito':'alegria'}
 ]
 r=falar.enviar(texto,'Codex','Felicidade',atuacao=cenas,preparacao={'tom':'ousado','digitacao':2.4})
 print(json.dumps({'id':r['id'],'leitura_id':inicio['id'],'estado':'enviada'},ensure_ascii=False),flush=True)
 ack=falar.RUNTIME/'recibos-fala'/(r['id']+'.json')
 registro=[];vistos=set();deadline=time.monotonic()+70
 while time.monotonic()<deadline:
  try:
   s=json.loads((falar.RUNTIME/'status.json').read_text())
   msg=s.get('mensagem',{});b=s.get('balao',{})
   chave=(msg.get('fase'),b.get('ativo'),s.get('expressao'),msg.get('efeito'))
   if chave not in vistos:
    vistos.add(chave)
    registro.append({'fase':msg.get('fase'),'tom':msg.get('tom'),'expressao':s.get('expressao'),'efeito':msg.get('efeito'),'voz':s.get('voz',{}).get('ativa'),'celular':msg.get('celular'),'fala_id':b.get('id')})
   if ack.exists():
    r=json.loads(ack.read_text())
    if r['estado'] in ['concluida','interrompida','erro']: break
  except (FileNotFoundError,json.JSONDecodeError): pass
  time.sleep(0.1)
 eventos_novos=eventos.ler('Codex',True)['eventos']
 resultado={'recibo':r,'estados':registro,'eventos':[e for e in eventos_novos if e.get('tipo') in ['fase_mensagem','atuacao','fala_inicio','fala_concluida','fala_interrompida','atividade_interrompida']]}
 destino=Path(__file__).resolve().parents[1]/'evidencias/modo-mensagens/demo-real.json'
 destino.write_text(json.dumps(resultado,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'estado':r['estado'],'fases':sorted(set(x['fase'] for x in registro if x['fase'])),'efeitos':sorted(set(x['efeito'] for x in registro if x['efeito'])),'cenas':sum(e['tipo']=='atuacao' for e in resultado['eventos'])},ensure_ascii=False))
 if r['estado']=='erro': raise RuntimeError(r)
if __name__=='__main__':main()
