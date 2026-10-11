#!/usr/bin/env python3
"""Quatro bonecas × três coordenadas, em Xvnc/OpenGL com cache privado."""
import json
import os
from pathlib import Path
import select
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'evidencias/hana-etapa3/previa'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    r, w = os.pipe()
    servidor = None
    try:
        with tempfile.TemporaryDirectory(prefix='kk-previa-roupa-') as tmp:
            servidor = subprocess.Popen(['Xvnc', '-displayfd', str(w), '-geometry', '1920x1080', '-depth', '24',
                '-localhost', '-SecurityTypes', 'None', '-rfbunixpath', tmp + '/vnc.sock', '-rfbport', '0', '-nolisten', 'tcp'],
                pass_fds=(w,), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.close(w)
            w = None
            if not select.select([r], [], [], 15)[0]:
                raise RuntimeError('Xvnc não iniciou')
            numero = os.read(r, 64).decode().strip()
            env = dict(os.environ, DISPLAY=':' + numero, KK_PROVA_RETRATO=str(OUT), KK_PROVA_CACHE=tmp + '/cache.json',
                       MASCOTE_RUNTIME='', MASCOTE_CHAT=tmp + '/chat', MASCOTE_RETRATO='0', MASCOTE_PERFIL='0')
            env.pop('WAYLAND_DISPLAY', None)
            # Mesmo driver/renderizador Intel do lançador real.
            env['__GLX_VENDOR_LIBRARY_NAME'] = 'mesa'
            env['DRI_PRIME'] = 'pci-0000_00_02_0'
            env.pop('__NV_PRIME_RENDER_OFFLOAD', None)
            with (OUT / 'godot.log').open('w') as log:
                subprocess.run([os.environ.get('GODOT', str(Path.home() / '.local/opt/godot/godot')),
                    '--display-driver', 'x11', '--rendering-method', 'gl_compatibility', '--audio-driver', 'Dummy',
                    '--path', str(ROOT), '--script', 'testes/previa_roupas_contexto.gd'],
                    env=env, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
            if 'ERROR:' in (OUT / 'godot.log').read_text():
                raise RuntimeError('Erro na prova Godot; consulte godot.log')
    finally:
        os.close(r)
        if w is not None:
            os.close(w)
        if servidor is not None:
            servidor.terminate()
            servidor.wait(timeout=5)
    bonecas = json.loads((ROOT / 'bonecas/catalogo.json').read_text())
    fonte = ImageFont.truetype('/usr/share/fonts/TTF/DejaVuSans.ttf', 18)
    folha = Image.new('RGB', (840, 530 * len(bonecas)), (22, 24, 31))
    d = ImageDraw.Draw(folha)
    for linha, b in enumerate(bonecas):
        for coluna, modo in enumerate(['uniforme', 'casual', 'pijama']):
            x, y = coluna * 280, linha * 530
            d.text((x + 8, y + 6), b['nome'] + ' · ' + modo, font=fonte, fill='white')
            imagem = Image.open(OUT / (b['id'] + '-' + modo + '.png')).convert('RGBA')
            if sum(imagem.getchannel('A').histogram()[1:]) < 2000:
                raise RuntimeError('Captura vazia: ' + b['id'] + '-' + modo)
            fundo = Image.new('RGBA', imagem.size, (28, 31, 39, 255))
            fundo.alpha_composite(imagem)
            folha.paste(fundo.convert('RGB').resize((280, 500)), (x, y + 30))
    folha.save(OUT / 'prancha.png')
    (OUT / 'resultado.json').write_text(json.dumps(dict(passou=True, capturas=12,
        renderizador='gl_compatibility', bonecas=bonecas), ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
