#!/usr/bin/env python3
"""Ponte local para qualquer agente publicar texto no mascote, sem depender de API de IA."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import subprocess
import time
import unicodedata
import uuid
import math

RUNTIME = Path(os.environ.get("MASCOTE_RUNTIME", str(Path(os.environ.get("XDG_RUNTIME_DIR", f"/tmp/kk-mascote-{os.getuid()}"))/"kk-mascote")))
CATALOGO_FACIAL = json.loads(Path(__file__).with_name("expressoes.json").read_text())
EMOCOES = tuple(CATALOGO_FACIAL['perfis'])

GESTOS = json.loads(Path(__file__).with_name("gestos.json").read_text())["clipes"]
MENSAGENS = json.loads(Path(__file__).with_name("mensagens.json").read_text())

def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFKD', texto.lower()) if not unicodedata.combining(c))

def emocao_texto(texto):
    t = normalizar(texto)
    t = re.sub(r'\b(?:nao (?:estou|esta|e)|sem)\s+(?:trist\w*|medo|raiva)\b', '', t)
    grupos = [
        ("Timidez", [r"\btimid\w*", r"\bvergonha\b"]),
        ("Pensativa", [r"\bestou pensando\b", r"\bdeixe-me pensar\b"]),
        ("Tédio", [r"\bentediad\w*", r"\btedio\b"]),
        ("Tristeza", [r'\btrist\w*', r'\bsinto muito\b', r'\blamento\b', r'\bsaudade\b', r'\bdecepcion\w*', r'\binfeliz\b']),
        ("Raiva", [r'\braiva\b', r'\bfurios\w*', r'\birritad\w*', r'\bodio\b']),
        ("Medo", [r'\bmedo\b', r'\bassustad\w*', r'\bapavorad\w*']),
        ("Preocupação", [r'\bpreocupad\w*', r'\breceio\b', r'\bansios\w*']),
        ("Felicidade", [r'\bfeliz\b', r'\balegr\w*', r'\botimo\b', r'\bmaravilh\w*', r'\bconseguimos\b', r'\bdeu certo\b']),
        ("Surpresa", [r'\bsurpres\w*', r'\binacreditavel\b', r'\buau\b']),
        ("Confiança", [r'\bconfiante\b', r'\bconte comigo\b'])]
    for nome, padroes in grupos:
        if any(re.search(p, t) for p in padroes): return nome
    return "Neutra"

def validar_face(face):
    if face is None: return {}
    if not isinstance(face, dict): raise ValueError('Face deve ser um objeto.')
    for chave, valor in face.items():
        if chave == 'intensidade':
            if isinstance(valor, bool) or not isinstance(valor, (int,float)) or not math.isfinite(valor) or not 0 <= valor <= 1:
                raise ValueError('Intensidade facial deve estar entre 0 e 1.')
        elif chave in ('olhos','sobrancelhas','boca'):
            if isinstance(valor,str):
                if valor not in EMOCOES: raise ValueError('Perfil facial inválido.')
            elif isinstance(valor,dict):
                if not 1 <= len(valor) <= 4: raise ValueError('Use até quatro formas por grupo facial.')
                for nome,peso in valor.items():
                    if nome not in CATALOGO_FACIAL['formas'][chave]: raise ValueError('Forma facial desconhecida.')
                    if isinstance(peso,bool) or not isinstance(peso,(int,float)) or not math.isfinite(peso) or not 0 <= peso <= 1:
                        raise ValueError('Peso facial deve estar entre 0 e 1.')
                if sum(valor.values()) > 1.000001: raise ValueError('A soma dos pesos deve ser no máximo 1.')
            else: raise ValueError('Use perfil ou objeto com formas e pesos.')
        elif chave == 'vogais_amplas':
            if not isinstance(valor,bool): raise ValueError('Vogais amplas deve ser booleano.')
        else: raise ValueError('Controle facial desconhecido.')
    return dict(face)

def validar_atuacao(cenas, texto):
    if cenas is None: return []
    if not isinstance(cenas,list) or len(cenas)>16: raise ValueError('Use até 16 cenas de atuação.')
    anterior = -1
    for cena in cenas:
        if not isinstance(cena,dict) or set(cena)-{'indice','emocao','face','gesto','movimento','olhar','efeito','som','deslocamento','enquadramento'}:
            raise ValueError('Cena de atuação inválida.')
        indice=cena.get('indice')
        if isinstance(indice,bool) or not isinstance(indice,int) or not anterior < indice < len(texto):
            raise ValueError('Índices devem crescer e estar dentro do texto.')
        anterior=indice
        if 'emocao' in cena and cena['emocao'] not in EMOCOES: raise ValueError('Emoção inválida na cena.')
        validar_face(cena.get('face'))
        if 'gesto' in cena and (not isinstance(cena['gesto'],str) or cena['gesto'] not in GESTOS): raise ValueError('Gesto inválido na cena.')
        if 'movimento' in cena and cena['movimento'] not in ('concordar','negar','inclinar','nenhum'):
            raise ValueError('Movimento inválido na cena.')
        if 'olhar' in cena:
            olhar=cena['olhar']
            if not isinstance(olhar,list) or len(olhar)!=2 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or abs(v)>1 for v in olhar):
                raise ValueError('Olhar deve conter dois valores entre -1 e 1.')
        if 'enquadramento' in cena and cena['enquadramento'] not in ('normal','corpo'):
            raise ValueError('Enquadramento deve ser normal ou corpo.')
        if 'deslocamento' in cena:
            trajeto = cena['deslocamento']
            if not isinstance(trajeto,dict) or set(trajeto)!={'pixels','duracao'}:
                raise ValueError('Deslocamento deve conter pixels e duração.')
            for chave,limites in [('pixels',(-180,180)),('duracao',(0.5,6))]:
                valor=trajeto.get(chave,2.0)
                if isinstance(valor,bool) or not isinstance(valor,(int,float)) or not math.isfinite(valor) or not limites[0]<=valor<=limites[1]:
                    raise ValueError('Deslocamento fora do limite: '+chave)
        for chave, lista in [('efeito','efeitos'),('som','sons')]:
            if chave in cena and (not isinstance(cena[chave],str) or cena[chave] not in MENSAGENS[lista]):
                raise ValueError('Efeito ou som desconhecido.')
    return json.loads(json.dumps(cenas,ensure_ascii=False))

def validar(texto, autor, emocao="auto", gesto="auto", face=None, atuacao=None, preparacao=None):
    if not isinstance(texto, str) or not texto.strip() or len(texto) > 1200:
        raise ValueError('Use texto não vazio com até 1.200 caracteres.')
    if not isinstance(autor, str) or not autor.strip() or len(autor) > 48:
        raise ValueError('Autor deve ter de 1 a 48 caracteres.')
    if any(ord(c) < 32 and c not in '\n\t' for c in texto+autor):
        raise ValueError('Caracteres de controle não são aceitos.')
    if emocao != 'auto' and emocao not in EMOCOES: raise ValueError('Emoção inválida.')
    if gesto != 'auto' and gesto not in GESTOS: raise ValueError('Gesto inválido.')
    resultado = {'texto': texto.strip(), 'autor': autor.strip(), 'emocao': emocao_texto(texto) if emocao == 'auto' else emocao}
    ajustes = validar_face(face)
    if ajustes: resultado['face'] = ajustes
    if gesto != 'auto': resultado['gesto'] = gesto
    cenas = validar_atuacao(atuacao,resultado['texto'])
    if cenas: resultado['atuacao'] = cenas
    if preparacao is not None:
        from encenar import validar as validar_preparacao
        resultado['preparacao'] = validar_preparacao(preparacao)
    return resultado

def enviar(texto, autor="Codex", emocao="auto", runtime=RUNTIME, voz=True, gesto="auto", face=None, atuacao=None, preparacao=None, roteiro=None, identificador=None):
    if identificador is not None and (not isinstance(identificador, str)
            or not re.fullmatch(r'[a-zA-Z0-9_-]{1,100}', identificador)):
        raise ValueError('Identificador inválido.')
    if roteiro is not None:
        if atuacao:
            raise ValueError('Escolha roteiro ou cenas manuais.')
        from roteiros import montar
        atuacao = montar(texto.strip(),roteiro)
    payload = validar(texto, autor, emocao, gesto, face, atuacao, preparacao)
    state = json.loads((runtime/'status.json').read_text())
    info = json.loads((runtime/'pids.json').read_text())
    pid = info['godot']
    actual = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[19]
    if actual != info.get('godot_starttime') or state.get('pid') != pid:
        raise RuntimeError('Mascote não está ativo nesta sessão.')
    inbox = runtime/'falas'
    inbox.mkdir(mode=0o700, exist_ok=True)
    message_id = identificador or f'{time.time_ns():020d}-{uuid.uuid4().hex}'
    audio_path = runtime/'audio'/(message_id+'.wav')
    prefs = state.get('preferencias', {})
    # Modo mensagens: ela escreve a resposta no celular; voz sintética só se ligada no menu.
    if prefs.get('modo_mensagens') or not prefs.get('voz_sintetica', False):
        voz = False
    if voz:
        audio_path.parent.mkdir(mode=0o700, exist_ok=True)
        # Remove apenas sínteses antigas, inclusive de sessões encerradas.
        for old in audio_path.parent.glob('*.wav'):
            try:
                if time.time()-old.stat().st_mtime > 600: old.unlink(missing_ok=True)
            except FileNotFoundError: pass
        interpreter = os.environ.get('MASCOTE_TTS_PYTHON', str(Path.home()/'.local/share/pipx/venvs/edge-tts/bin/python'))
        try:
            result = subprocess.run([interpreter, str(Path(__file__).with_name('voz.py'))],
                input=json.dumps({'texto': payload['texto'], 'arquivo': str(audio_path)}),
                text=True, capture_output=True, timeout=55, check=True)
            payload['audio'] = json.loads(result.stdout)
            # A síntese pode levar segundos: confira novamente a sessão de destino.
            current = json.loads((runtime/'pids.json').read_text())
            if current.get('godot') != pid or current.get('godot_starttime') != actual:
                raise RuntimeError('A sessão mudou durante a geração da voz.')
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            audio_path.unlink(missing_ok=True)
            raise RuntimeError('Falha ao gerar voz; tente novamente ou use --sem-voz.') from exc
    payload.update(id=message_id, pid_destino=pid, criado_em=time.time())
    tmp = inbox/(message_id+'.tmp')
    try:
        with tmp.open('x', encoding='utf-8') as file:
            os.chmod(tmp, 0o600)
            json.dump(payload, file, ensure_ascii=False)
        tmp.replace(inbox/(message_id+'.json'))
    except Exception:
        audio_path.unlink(missing_ok=True)
        raise
    finally:
        tmp.unlink(missing_ok=True)
    return {'id': message_id, 'estado': 'enfileirada', 'autor': payload['autor'], 'emocao': payload['emocao']}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('texto', nargs='?')
    parser.add_argument('--gesto', default='auto', choices=['auto', *GESTOS], help='Escolhe um gesto original para a resposta')
    parser.add_argument('--face-json',type=Path,help='Arquivo JSON com formas e pesos faciais')
    parser.add_argument('--atuacao-json',type=Path,help='Arquivo JSON com cenas por índice do texto')
    from roteiros import ROTEIROS
    parser.add_argument('--roteiro',choices=ROTEIROS,help='Direção de atuação: explicacao, comedia, agradecimento ou animada')
    parser.add_argument('--preparacao-json',type=Path,help='Leitura, reação ao tom e digitação antes da resposta')
    parser.add_argument('--intensidade', type=float, help='Intensidade facial entre 0 e 1')
    for grupo in ('olhos','sobrancelhas','boca'):
        parser.add_argument('--'+grupo, choices=EMOCOES, help='Perfil independente de '+grupo)
    parser.add_argument('--sem-voz', action='store_true', help='Envia apenas balão e articulação visual, sem síntese online')
    parser.add_argument('--stdin', action='store_true', help='Lê o texto da entrada padrão')
    parser.add_argument('--autor', default='Codex', help='Ex.: Codex ou Claude')
    parser.add_argument('--emocao', default='auto', choices=['auto', *EMOCOES])
    parser.add_argument('--esperar', type=float, default=0, help='Aguarda confirmação de início por até N segundos')
    args = parser.parse_args()
    if args.esperar < 0 or args.esperar > 60: parser.error('--esperar deve estar entre 0 e 60 segundos')
    if args.stdin == bool(args.texto): parser.error('Forneça o texto ou --stdin')
    try:
        face = json.loads(args.face_json.read_text()) if args.face_json else {}
        if not isinstance(face,dict): raise ValueError('Face deve ser um objeto.')
        face.update({k:getattr(args,k) for k in ('intensidade','olhos','sobrancelhas','boca') if getattr(args,k) is not None})
        cenas = json.loads(args.atuacao_json.read_text()) if args.atuacao_json else []
        preparacao = json.loads(args.preparacao_json.read_text()) if args.preparacao_json else None
        resultado = enviar(sys.stdin.read(4801) if args.stdin else args.texto, args.autor, args.emocao, voz=not args.sem_voz, gesto=args.gesto, face=face, atuacao=cenas, preparacao=preparacao, roteiro=args.roteiro)
        deadline = time.monotonic()+args.esperar
        ack = RUNTIME/'recibos-fala'/(resultado['id']+'.json')
        while time.monotonic() < deadline:
            if ack.exists():
                resultado = json.loads(ack.read_text());break
            time.sleep(0.1)
        print(json.dumps(resultado, ensure_ascii=False))
        if resultado['estado'] == 'erro': return 1
        return 0
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        print(f'Não foi possível falar: {exc}', file=sys.stderr)
        return 1
if __name__ == '__main__': sys.exit(main())
