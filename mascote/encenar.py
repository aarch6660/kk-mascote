#!/usr/bin/env python3
"""Sinaliza leitura/reação na Chika durante um turno ativo de Codex ou Claude."""
import argparse
import json
import os
import time
import uuid
from pathlib import Path
import falar

CATALOGO = json.loads(Path(__file__).with_name('mensagens.json').read_text())

def validar(preparacao):
    if preparacao is None: return {}
    if not isinstance(preparacao, dict) or set(preparacao)-{'tom','intensidade','leitura','digitacao','duracao'}:
        raise ValueError('Preparação inválida.')
    import math
    for chave, valor in preparacao.items():
        if chave == 'tom':
            if not isinstance(valor,str) or valor not in CATALOGO['tons']: raise ValueError('Tom desconhecido.')
        else:
            limites = {'intensidade':(0,1),'leitura':(0,5),'digitacao':(0,5),'duracao':(3,60)}
            lo, hi = limites[chave]
            if isinstance(valor,bool) or not isinstance(valor,(float,int)) or not math.isfinite(valor) or not lo<=valor<=hi:
                raise ValueError('Valor de preparação fora do intervalo: '+chave)
    return dict(preparacao)

def enviar(autor='Codex', tom='curioso', duracao=30, intensidade=0.65, runtime=falar.RUNTIME, texto=None):
    autor=falar.validar('Leitura',autor)['autor']
    if texto:
        # Mensagem que o usuário mandou pelo terminal: aparece como bolha dele no chat.
        import chat_dados
        state=json.loads((runtime/'status.json').read_text())
        chat_dados.registrar('usuario',texto,boneca=state.get('preferencias',{}).get('boneca',''))
    dados=validar({'tom':tom,'duracao':duracao,'intensidade':intensidade})
    state=json.loads((runtime/'status.json').read_text())
    info=json.loads((runtime/'pids.json').read_text())
    pid=info['godot']
    actual=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]
    if state.get('pid')!=pid or actual!=info.get('godot_starttime'): raise RuntimeError('Sessão do mascote inativa.')
    pasta=runtime/'atividades'
    pasta.mkdir(mode=0o700,exist_ok=True)
    identificador=f'{time.time_ns():020d}-{uuid.uuid4().hex}'
    payload=dict(id=identificador,autor=autor,tipo='leitura',preparacao=dados,pid_destino=pid,criado_em=time.time())
    tmp=pasta/(identificador+'.tmp')
    try:
        with tmp.open('x') as f:
            os.chmod(tmp,0o600)
            json.dump(payload,f,ensure_ascii=False)
        tmp.replace(pasta/(identificador+'.json'))
    finally: tmp.unlink(missing_ok=True)
    return {'id':identificador,'estado':'enfileirada','autor':autor,'tom':tom}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--autor',default='Codex')
    p.add_argument('--tom',choices=CATALOGO['tons'],default='curioso')
    p.add_argument('--duracao',type=float,default=30)
    p.add_argument('--intensidade',type=float,default=0.65)
    p.add_argument('--texto',help='Mensagem do usuário (vinda do terminal) para mostrar no chat')
    a=p.parse_args()
    try: print(json.dumps(enviar(a.autor,a.tom,a.duracao,a.intensidade,texto=a.texto),ensure_ascii=False))
    except (OSError,ValueError,RuntimeError,KeyError) as e: p.exit(1,str(e)+'\n')

if __name__=='__main__': main()
