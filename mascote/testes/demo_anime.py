#!/usr/bin/env python3
"""Duas falas caricatas na instância ativa; respeita clique e preserva preferências."""
import json
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import encenar,eventos,falar

def main():
    registro={'preferencias_antes':json.loads((falar.RUNTIME/'status.json').read_text())['preferencias'],'falas':[]}
    contexto=eventos.ler('Codex',consumir=True)
    if contexto['status'].get('toque_ativo'):
        print('Demonstração adiada: contato ativo.');return
    encenar.enviar('Codex',tom='curioso',intensidade=0.7)
    exemplos=[
        ('explicacao','Vamos organizar o dia em três passos. Primeiro, escolhemos uma tarefa pequena e começamos com calma. Depois, fazemos uma pausa para pensar no próximo passo. Olha só: uma ideia grande pode virar várias ações pequenas! No final, conferimos o que funcionou e comemoramos o progresso.'),
        ('comedia','Eu tinha uma explicação muito séria para dar. Mas apareceu uma dúvida enorme: onde foi parar o meu biscoito? Será que ele saiu correndo sozinho? Ah, descobri: estava bem aqui do meu lado! Agora posso rir da confusão e continuar a conversa.'),
    ]
    for roteiro,texto in exemplos:
        item={'roteiro':roteiro,'texto':texto,'estados':[],'voz_observada':False,'offset_min':0.0,'offset_max':0.0}
        registro['falas'].append(item)
        envio=falar.enviar(texto,autor='Codex',emocao='Curiosidade',roteiro=roteiro,
            preparacao={'tom':'curioso' if roteiro=='explicacao' else 'confuso','leitura':1.1,'digitacao':1.0,'intensidade':0.7})
        item['id']=envio['id']
        print(json.dumps({'roteiro':roteiro,'id':envio['id'],'estado':'enviada'},ensure_ascii=False),flush=True)
        prazo=time.monotonic()+90
        ack=falar.RUNTIME/'recibos-fala'/(envio['id']+'.json')
        vistos=set()
        while time.monotonic()<prazo:
            s=json.loads((falar.RUNTIME/'status.json').read_text())
            if s.get('balao',{}).get('id')==envio['id']:
                a=s.get('atuacao',{})
                item['voz_observada']|=s.get('voz',{}).get('ativa',False)
                item['offset_min']=min(item['offset_min'],a.get('deslocamento',0))
                item['offset_max']=max(item['offset_max'],a.get('deslocamento',0))
                chave=(s.get('expressao'),s.get('clipe'),a.get('andando'),a.get('enquadramento'),s.get('mensagem',{}).get('efeito'))
                if chave not in vistos:
                    vistos.add(chave)
                    detalhe={'expressao':chave[0],'clipe':chave[1],'andando':chave[2],'enquadramento':chave[3],'efeito':chave[4]}
                    item['estados'].append(detalhe)
                    print(json.dumps(detalhe,ensure_ascii=False),flush=True)
            if ack.exists():
                item['recibo']=json.loads(ack.read_text())
                if item['recibo']['estado'] in ['concluida','interrompida','erro']:break
            time.sleep(0.1)
        item['eventos']=eventos.ler('Codex',consumir=True)['eventos']
        if item.get('recibo',{}).get('estado')!='concluida':break
        time.sleep(1)
    registro['preferencias_depois']=json.loads((falar.RUNTIME/'status.json').read_text())['preferencias']
    registro['preferencias_preservadas']=registro['preferencias_antes']==registro['preferencias_depois']
    destino=Path(__file__).resolve().parents[1]/'evidencias/anime-2026-10-09/demo-real.json'
    destino.write_text(json.dumps(registro,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'registro':str(destino),'preferencias_preservadas':registro['preferencias_preservadas'],'concluidas':sum(f.get('recibo',{}).get('estado')=='concluida' for f in registro['falas'])},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
