#!/usr/bin/env python3
"""Demonstração com voz na instância ativa; não inicia ou altera preferências."""
import json
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import falar
texto='Pronto! Agora minha expressão acompanha cada trecho da conversa. Vamos pensar um instante... Sim, já podemos seguir! Olha a piscadela! E agora volto ao sorriso. Você pode testar o carinho na cabeça e observar como a reação muda e depois se acalma.'
cenas=[
 {'indice':0,'emocao':'Riso','face':{'intensidade':0.7},'gesto':'conversa_03'},
 {'indice':texto.index('Vamos pensar'),'emocao':'Curiosidade','face':{'intensidade':0.8,'sobrancelhas':{'gimoL_op':0.45}},'movimento':'inclinar','olhar':[-0.3,-0.1]},
 {'indice':texto.index('Sim,'),'emocao':'Felicidade','face':{'intensidade':0.75,'sobrancelhas':'Neutra'},'gesto':'stand_joy_00','movimento':'concordar'},
 {'indice':texto.index('Olha a piscadela'),'emocao':'Piscadela esquerda','face':{'intensidade':1}},
 {'indice':texto.index('E agora'),'emocao':'Felicidade','face':{'intensidade':0.75,'sobrancelhas':'Neutra'},'gesto':'conversa_05'}]
r=falar.enviar(texto,'Codex','Riso',atuacao=cenas)
ack=falar.RUNTIME/'recibos-fala'/(r['id']+'.json')
for _ in range(50):
 if ack.exists():
  r=json.loads(ack.read_text());break
 time.sleep(0.1)
print(json.dumps(r,ensure_ascii=False))
