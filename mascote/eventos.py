#!/usr/bin/env python3
"""Consulta eventos locais da sessão ativa; não inicia agentes nem chama APIs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
from falar import RUNTIME


def ler(autor='Codex', consumir=False, runtime=RUNTIME):
    info = json.loads((runtime/'pids.json').read_text())
    status = json.loads((runtime/'status.json').read_text())
    pid = info['godot']
    start = Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]
    if start != info.get('godot_starttime') or status.get('pid') != pid:
        raise RuntimeError('Mascote não está ativo nesta sessão.')
    sessao = status.get('sessao_eventos')
    if not sessao: raise RuntimeError('Reinicie o mascote para habilitar eventos.')
    pasta = runtime/'leitores-eventos'
    cursor = pasta/(hashlib.sha256(autor.encode()).hexdigest()+'.json')
    try: anterior = json.loads(cursor.read_text())
    except (OSError, ValueError): anterior = {}
    desde = anterior.get('sequencia',0) if anterior.get('sessao') == sessao else 0
    eventos = []
    for arquivo in sorted((runtime/'eventos').glob('*.json')):
        try: evento = json.loads(arquivo.read_text())
        except (OSError, ValueError): continue
        if evento.get('pid') == pid and evento.get('sessao') == sessao and evento.get('sequencia',0) > desde:
            eventos.append(evento)
    eventos.sort(key=lambda e:e['sequencia'])
    lacuna = bool(eventos and eventos[0]['sequencia'] > desde+1)
    if consumir and eventos:
        pasta.mkdir(mode=0o700,parents=True,exist_ok=True)
        # Serializar consumidores do mesmo autor é responsabilidade de quem integra.
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w',dir=pasta,delete=False,encoding='utf-8') as f:
            json.dump({'sessao':sessao,'sequencia':eventos[-1]['sequencia']},f)
            tmp = Path(f.name)
        tmp.replace(cursor)
    return {'eventos':eventos,'lacuna':lacuna,'sessao':sessao,'status':{
        k:status.get(k) for k in ('toque_ativo','regiao_toque','interacao','balao','estado')}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--autor',default='Codex')
    parser.add_argument('--consumir',action='store_true',help='Avança o cursor deste autor')
    parser.add_argument('--esperar',type=float,default=0,help='Espera eventos por até 60 segundos')
    args = parser.parse_args()
    if not 0 <= args.esperar <= 60: parser.error('Espera deve estar entre 0 e 60 segundos.')
    deadline = time.monotonic()+args.esperar
    try:
        while True:
            resultado = ler(args.autor,args.consumir)
            if resultado['eventos'] or time.monotonic() >= deadline: break
            time.sleep(0.1)
        print(json.dumps(resultado,ensure_ascii=False))
    except (OSError,ValueError,KeyError,RuntimeError) as exc:
        parser.exit(1,f'Não foi possível ler eventos: {exc}\n')

if __name__ == '__main__': main()
