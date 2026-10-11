#!/usr/bin/env python3
"""Atualiza a camada original da pele sem regenerar malhas ou preferências."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile

from areola_kk import configurar_areola
from carregar import carregar, RAIZ

ROOT = Path(__file__).resolve().parents[1]


def atomico(path, conteudo):
    fd, nome = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(conteudo)
        os.replace(nome, path)
    finally:
        if os.path.exists(nome):
            os.unlink(nome)


def atualizar(pasta):
    corpo = json.loads((pasta / 'card.json').read_text())['Custom']['corpo']
    pecas = json.loads((pasta / 'pecas.json').read_text())['pecas']
    item = next(p for p in pecas if p['tipo'] == 'corpo_nipId')
    if int(item['id']) != corpo['nipId']:
        raise ValueError('pecas.json não corresponde ao nipId do card')
    fonte = RAIZ / item['MainAB']
    tex = next(o.read() for o in carregar(fonte).objects
               if o.type.name == 'Texture2D' and o.peek_name() == item['NipTex'])
    nome = tex.m_Name + '.png'
    saida = pasta / 'saida'
    dados = json.loads((saida / 'materiais_kk.json').read_text())
    originais = json.loads((saida / 'materiais_unity.json').read_text())
    chave = 'corpo__cf_m_body'
    configurar_areola(dados[chave], corpo, originais[chave], nome, int(tex.m_ColorSpace))
    # Substituição atômica também isola qualquer hardlink de outra boneca.
    import io
    png = io.BytesIO()
    tex.image.save(png, format='PNG')
    atomico(saida / 'visual' / nome, png.getvalue())
    atomico(saida / 'materiais_kk.json', (json.dumps(dados, ensure_ascii=False, indent=2) + '\n').encode())
    texturas = json.loads((saida / 'texturas_originais.json').read_text())
    texturas[nome] = list(tex.image.size)
    atomico(saida / 'texturas_originais.json', (json.dumps(texturas, indent=2) + '\n').encode())
    return {'boneca': pasta.name, 'textura': nome, 'resolucao': list(tex.image.size),
            'parametros': dados[chave]['areola'], 'cor': corpo['nipColor'],
            'fonte': item['MainAB'], 'fonte_sha256': hashlib.sha256(fonte.read_bytes()).hexdigest(),
            'png_sha256': hashlib.sha256(png.getvalue()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pasta', type=Path)
    parser.add_argument('--relatorio', type=Path)
    args = parser.parse_args()
    pastas = [args.pasta] if args.pasta else [p.parent for p in sorted((ROOT / 'bonecas').glob('*/card.json'))]
    resultados = [atualizar(p) for p in pastas]
    raw = json.dumps(resultados, ensure_ascii=False, indent=2) + '\n'
    if args.relatorio:
        atomico(args.relatorio, raw.encode())
    print(raw, end='')


if __name__ == '__main__':
    main()
