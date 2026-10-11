#!/usr/bin/env python3
"""Vídeo de prova da respiração ofegante (Xvnc privado): quadros do Godot + áudio remontado do log.

    $PYTHON_PERSONAGEM mascote/testes/video_ofegar.py  →  evidencias/ofegar/ofegar.mp4
"""
import json, os, select, subprocess, tempfile
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'evidencias/ofegar'
SR, FPS = 48000, 30
GODOT = os.environ.get('GODOT', str(Path.home() / '.local/opt/godot/godot'))


def gravar(tmp):
    r, w = os.pipe()
    sv = subprocess.Popen(['Xvnc', '-displayfd', str(w), '-geometry', '1920x1080', '-depth', '24', '-localhost',
                           '-SecurityTypes', 'None', '-rfbunixpath', tmp + '/vnc.sock', '-rfbport', '0', '-nolisten', 'tcp'],
                          pass_fds=(w,), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.close(w)
    try:
        assert select.select([r], [], [], 15)[0], 'Xvnc não iniciou'
        env = dict(os.environ, DISPLAY=':' + os.read(r, 64).decode().strip(), KK_VIDEO_SAIDA=tmp,
                   MASCOTE_RUNTIME='', __GLX_VENDOR_LIBRARY_NAME='mesa', DRI_PRIME='pci-0000_00_02_0')
        env.pop('WAYLAND_DISPLAY', None)
        with (OUT / 'godot.log').open('w') as log:
            subprocess.run([GODOT, '--display-driver', 'x11', '--rendering-method', 'gl_compatibility', '--audio-driver', 'Dummy',
                            '--path', str(ROOT), '--fixed-fps', str(FPS), '--script', 'testes/video_ofegar.gd'],
                           env=env, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=900)
    finally:
        sv.terminate(); sv.wait(5); os.close(r)


def decodificar(arquivo):
    raw = subprocess.run(['ffmpeg', '-v', 'quiet', '-i', str(arquivo), '-f', 's16le', '-ac', '1', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def audio(quadros):
    # Cada quadro: o som que estava tocando, posição e volume → copia 1/30 s daquele trecho.
    total = np.zeros(len(quadros) * SR // FPS + SR, np.float32)
    cache = {}
    for q in quadros:
        for canal, ganho_base in (('ofegar', 1.0), ('reacao', 1.0)):
            s = q[canal]
            if not s or not s.get('arquivo'):
                continue
            caminho = ROOT.parent / 'bonecas' / q['boneca'] / 'vozes' / s['arquivo']
            if caminho not in cache:
                cache[caminho] = decodificar(caminho)
            fonte = cache[caminho]
            ini = int(s['pos'] * SR); n = SR // FPS; dst = q['q'] * SR // FPS
            trecho = fonte[ini:ini + n]
            total[dst:dst + len(trecho)] += trecho * ganho_base * 10 ** (s['db'] / 20)
    return np.clip(total, -1, 1)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='kk-video-ofegar-') as tmp:
        gravar(tmp)
        quadros = json.loads(Path(tmp, 'audio.json').read_text())
        fonte = ImageFont.truetype('/usr/share/fonts/TTF/DejaVuSans.ttf', 22)
        for q in quadros:
            im = Image.open(Path(tmp) / f"q{q['q']:05d}.png").convert('RGBA')
            fundo = Image.new('RGBA', im.size, (24, 26, 34, 255)); fundo.alpha_composite(im)
            # Modo retrato: o busto já ocupa o quadro, com resolução real no rosto.
            im = fundo.convert('RGB').resize((720, 720))
            d = ImageDraw.Draw(im)
            d.rectangle((0, 0, 720, 64), fill=(0, 0, 0))
            d.text((10, 6), q['legenda'], font=fonte, fill='white')
            estado = f"ofegando ({q['motivo']}) · rosto: {q['emocao']}" if q['ativo'] else f"rosto: {q['emocao']}"
            d.text((10, 36), estado, font=ImageFont.truetype('/usr/share/fonts/TTF/DejaVuSans.ttf', 16),
                   fill=(255, 140, 160) if q['ativo'] else (180, 180, 180))
            im.save(Path(tmp) / f"v{q['q']:05d}.png")
        a = (audio(quadros) * 32767).astype(np.int16)
        wav = Path(tmp) / 'a.raw'; wav.write_bytes(a.tobytes())
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', str(Path(tmp) / 'v%05d.png'),
                        '-f', 's16le', '-ar', str(SR), '-ac', '1', '-i', str(wav), '-shortest',
                        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '23', '-c:a', 'aac', '-b:a', '128k',
                        str(OUT / 'ofegar.mp4')], check=True)
        (OUT / 'quadros.json').write_text(json.dumps(quadros, ensure_ascii=False))
        ativos = [q for q in quadros if q['ativo']]
        print(json.dumps({'quadros': len(quadros), 'segundos': round(len(quadros) / FPS, 1),
                          'ofegando_s': round(len(ativos) / FPS, 1),
                          'motivos': sorted({q['motivo'] for q in ativos if q['motivo']}),
                          'emocoes_ofegando': sorted({q['emocao'] for q in ativos}),
                          'video': str(OUT / 'ofegar.mp4')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
