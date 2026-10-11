#!/usr/bin/env python3
"""Coordenadas exportadas, contexto efetivo do cérebro e rejeição de índices inválidos."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'mascote'))
from hana import cerebro, desktop

casos = 0


def verificar(ok, nome):
    global casos
    casos += 1
    assert ok, nome


def testar_contexto():
    for n, nome in [(0, 'uniforme'), (5, 'casual'), (6, 'pijama')]:
        estado = {'roupa': {'coordenada': n}, 'preferencias': {'roupa_modo': 'automatica'}}
        verificar(desktop.roupa(estado) == dict(coordenada=n, nome=nome, modo='automatica'), 'roupa efetiva')
        b = cerebro.Cerebro.__new__(cerebro.Cerebro)
        b.relogio = lambda: datetime(2026, 10, 11, 23)
        b.contexto = {'roupa': {'nome': 'desatualizada'}}
        b.pendencia = {'motivo': 'resposta', 'mensagens': []}
        b.memoria = SimpleNamespace(contexto=lambda agora: {})
        b.sessao = lambda: (estado, [123, 'teste'])
        with patch.object(cerebro.chat_dados, 'listar', return_value=[]):
            verificar(b.entrada()['desktop']['roupa']['nome'] == nome, 'modelo recebe roupa carregada mesmo antes da atualização do desktop')
    for invalido in [{}, {'roupa': None}, {'roupa': {'coordenada': 4}}, {'roupa': {'coordenada': True}}]:
        verificar(desktop.roupa(invalido) == {}, 'estado inválido não inventa roupa')
    with tempfile.TemporaryDirectory(prefix='kk-roupa-contexto-') as tmp:
        b.runtime = Path(tmp)
        b.contexto = {}
        b.desktop_due = float('inf')
        b._desktop(estado)
        verificar(b.contexto['roupa']['nome'] == 'pijama', 'estado de roupa não aguarda polling de cinco segundos')


def testar_exportacao():
    auditoria = json.loads((ROOT / 'personagem/auditoria_coordenadas.json').read_text())
    verificar(auditoria['valores'] == dict(School01=0, School02=1, Gym=2, Swim=3, Club=4, Plain=5, Pajamas=6), 'enum nativa')
    verificar(hashlib.sha256(Path(auditoria['fonte']).read_bytes()).hexdigest() == auditoria['sha256'], 'DLL auditada permanece idêntica')
    for boneca in json.loads((ROOT / 'bonecas/catalogo.json').read_text()):
        original = ROOT / 'bonecas' / boneca['id']
        card = json.loads((original / 'card.json').read_text())
        for n in [5, 6]:
            pasta = original / 'coordenadas' / f'coord_{n}'
            pecas = json.loads((pasta / 'pecas.json').read_text())
            verificar(pecas['coordenada'] == n, 'metadados da coordenada')
            verificar((pasta / 'card.png').read_bytes() == (original / 'card.png').read_bytes(), 'card preservado')
            selecionadas = {p['tipo']: p for p in pecas['pecas']}
            for i, parte in enumerate(card['Coordinate'][n]['roupa']['parts']):
                tipo = f'roupa_{i}'
                verificar((tipo in selecionadas) == (parte['id'] != 0), 'ID zero é ausência de peça')
                if parte['id']:
                    verificar(selecionadas[tipo]['id'] == parte['id'], 'peça pertence à coordenada')
            fisica = json.loads((pasta / 'saida/fisica_kk.json').read_text())
            verificar(fisica['coordenada'] == n, 'física específica da coordenada')
            esperadas = {p['tipo'] for p in pecas['pecas'] if p['tipo'].startswith(('cabelo_', 'roupa_'))
                         and p.get('MainData') not in (None, '', 'p_dummy')}
            # corpo_mod: DynamicBones do corpo UncensorSelector, auditado à parte.
            partes = [p for p in fisica['selected_parts'] if p['slot'] != 'corpo_mod']
            verificar({p['slot'] for p in partes} == esperadas, 'todas as peças reais auditadas, inclusive roupa de outro bundle')
            for parte in fisica['selected_parts']:
                if parte['slot'] == 'corpo_mod':
                    verificar(parte['resolved'] and parte['prefab'] == selecionadas['corpo']['MainData'], 'física do corpo selecionado')
            for parte in partes:
                verificar(parte['resolved'] and parte['prefab'] == selecionadas[parte['slot']]['MainData'], 'física do prefab selecionado')
            validacao = json.loads((pasta / 'saida/validacao_corpo.json').read_text())
            verificar(validacao['passou'] and not validacao['erros'], 'três GLBs válidos')
            verificar(not (pasta / 'trabalho').exists(), 'intermediários limpos')
    with tempfile.TemporaryDirectory(prefix='kk-roupa-indice-') as tmp:
        for valor in ['-1', '7', '1.0', '../5']:
            r = subprocess.run(['bash', str(ROOT / 'personagem/gerar.sh')],
                               env=dict(os.environ, BONECA_DIR=tmp, KK_COORDENADA=valor), capture_output=True)
            verificar(r.returncode != 0 and not list(Path(tmp).iterdir()), 'índice inválido rejeitado antes de escrever')


def testar_resolver():
    # Exercita o caso sem blusa e sem qualquer roupa sem escrever nos cards reais.
    with tempfile.TemporaryDirectory(prefix='kk-roupa-vazia-') as tmp:
        pasta = Path(tmp)
        card = json.loads((ROOT / 'bonecas/chika-haruno/card.json').read_text())
        for peca in card['Coordinate'][5]['roupa']['parts']:
            peca['id'] = 0
            peca['emblemeId'] = 0
        (pasta / 'card.json').write_text(json.dumps(card))
        (pasta / 'pecas.json').write_text('uniforme preservado')
        python = os.environ.get('PYTHON_PERSONAGEM', str(Path.home() / 'Games/samabake-mascote/.venv/bin/python'))
        subprocess.run([python, str(ROOT / 'personagem/resolver.py')],
                       env=dict(os.environ, BONECA_DIR=tmp, KK_COORDENADA='5'), check=True, stdout=subprocess.DEVNULL)
        verificar((pasta / 'pecas.json').read_text() == 'uniforme preservado', 'resolver direto não sobrescreve coordenada zero')
        partes = json.loads((pasta / 'coordenadas/coord_5/pecas.json').read_text())
        verificar(partes['coordenada'] == 5 and not any(p['tipo'].startswith('roupa_') for p in partes['pecas']),
                  'coordenada totalmente vazia é válida e preserva corpo e cabeça')


if __name__ == '__main__':
    testar_contexto()
    testar_exportacao()
    testar_resolver()
    dados = dict(passou=True, casos=casos)
    (ROOT / 'mascote/evidencias/hana-etapa3/python.json').write_text(json.dumps(dados, indent=2) + '\n')
    print(json.dumps(dados))
