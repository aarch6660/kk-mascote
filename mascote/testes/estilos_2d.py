#!/usr/bin/env python3
"""Estudos de estilo 2D da Chika em retrato: 6 pixelados + 6 com cara de anime, a partir de duas fontes
(render 3D do mascote e captura do jogo). Só PIL + numpy. Saída em evidencias/estilos-2d/saida/."""
import json, pathlib, sys
import numpy as np
from PIL import Image, ImageFilter, ImageOps

RAIZ = pathlib.Path(__file__).resolve().parents[1] / 'evidencias/estilos-2d'
SAIDA = RAIZ / 'saida'
LADO = 768
RNG = np.random.default_rng(7)

PICO8 = ['#000000','#1D2B53','#7E2553','#008751','#AB5236','#5F574F','#C2C3C7','#FFF1E8',
         '#FF004D','#FFA300','#FFEC27','#00E436','#29ADFF','#83769C','#FF77A8','#FFCCAA']
GAMEBOY = ['#0F380F','#306230','#8BAC0F','#9BBC0F']
AMBAR = ['#14100D','#2A1E16','#3F2A1C','#5C3A22','#7A4A26','#A05A1E','#C86E14','#F08A0C',
         '#FF9E1B','#FFC24D','#FFDFA0','#FFF4E0']
BAYER4 = np.array([[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]]) / 16.0 - 0.5


def hexrgb(lista):
    return np.array([[int(h[i:i+2], 16) for i in (1, 3, 5)] for h in lista], float)


def arr(im):
    return np.asarray(im.convert('RGBA'), float)


def img(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')


def reduzir(im, n):
    """Área média ponderada pelo alfa (evita franja escura) e alfa binário."""
    a = arr(im)
    rgb_pre = a[..., :3] * (a[..., 3:] / 255)
    pre = Image.fromarray(np.dstack([rgb_pre, a[..., 3:]]).astype(np.uint8), 'RGBA').resize((n, n), Image.BOX)
    b = arr(pre)
    al = b[..., 3:]
    rgb = np.where(al > 0, b[..., :3] / np.maximum(al, 1) * 255, 0)
    return np.dstack([rgb, np.where(al > 110, 255, 0)])


def paleta_proxima(rgb, pal, dither=0.0, passo=None):
    if dither:
        h, w = rgb.shape[:2]
        limiar = np.tile(BAYER4, (h // 4 + 1, w // 4 + 1))[:h, :w]
        rgb = rgb + limiar[..., None] * dither
    d = ((rgb[..., None, :] - pal[None, None]) ** 2).sum(-1)
    return pal[d.argmin(-1)]


def desloca(m, dy, dx):
    """Como np.roll, mas sem dar a volta (preenche com zero)."""
    out = np.zeros_like(m)
    h, w = m.shape[:2]
    out[max(dy, 0):h + min(dy, 0), max(dx, 0):w + min(dx, 0)] = m[max(-dy, 0):h + min(-dy, 0), max(-dx, 0):w + min(-dx, 0)]
    return out


def contorno(a, cor=(20, 14, 18), dentro=False):
    """1 px de contorno na silhueta (fora) — clássico de sprite."""
    al = a[..., 3] > 0
    viz = np.zeros_like(al)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        viz |= desloca(al, dy, dx)
    borda = viz & ~al
    out = a.copy()
    out[borda] = [*cor, 255]
    return out


def ampliar(a, n=LADO):
    return img(a).resize((n, n), Image.NEAREST)


def lum(rgb):
    return rgb @ np.array([0.299, 0.587, 0.114])


def bordas(a, limiar=38, grossura=1):
    l = Image.fromarray(np.clip(lum(a[..., :3]), 0, 255).astype(np.uint8))
    e = np.asarray(l.filter(ImageFilter.FIND_EDGES), float)
    m = Image.fromarray(((e > limiar) & (a[..., 3] > 0)).astype(np.uint8) * 255)
    for _ in range(grossura - 1):
        m = m.filter(ImageFilter.MaxFilter(3))
    return np.asarray(m, float) / 255


def hsv(a):
    return np.asarray(img(a).convert('RGB').convert('HSV'), float)


def de_hsv(h, alfa):
    rgb = np.asarray(Image.fromarray(np.clip(h, 0, 255).astype(np.uint8), 'HSV').convert('RGB'), float)
    return np.dstack([rgb, alfa])


# ── pixelados ────────────────────────────────────────────────────────────
def p1_sprite128(im, pal_fixa=None):
    a = reduzir(im, 128)
    q = img(a).convert('RGB').quantize(24, method=Image.Quantize.MEDIANCUT) if pal_fixa is None else \
        img(a).convert('RGB').quantize(palette=pal_fixa, dither=Image.Dither.NONE)
    b = np.dstack([np.asarray(q.convert('RGB'), float), a[..., 3]])
    b[a[..., 3] == 0] = 0
    return ampliar(contorno(b)), q


def p2_pico8(im):
    a = reduzir(im, 96)
    b = np.dstack([paleta_proxima(a[..., :3], hexrgb(PICO8), dither=48), a[..., 3]])
    b[a[..., 3] == 0] = 0
    return ampliar(contorno(b, (0, 0, 0)))


def p3_gameboy(im):
    a = reduzir(im, 64)
    l = lum(a[..., :3])[..., None].repeat(3, -1)
    pal = hexrgb(GAMEBOY)
    tons = np.array([[0, 0, 0], [85, 85, 85], [170, 170, 170], [255, 255, 255]], float)
    d = ((l[..., None, :] + np.tile(BAYER4, (16, 16))[..., None, None] * 70 - tons[None, None]) ** 2).sum(-1)
    b = np.dstack([pal[d.argmin(-1)], a[..., 3]])
    b[a[..., 3] == 0] = 0
    return ampliar(contorno(b, tuple(int(x) for x in pal[0])))


def p4_ambar(im):
    a = reduzir(im, 128)
    pal = hexrgb(AMBAR)
    # Mapeia por luminância para a rampa âmbar (vira uma "gravura" monocromática quente).
    l = lum(a[..., :3]) / 255
    h, w = l.shape
    l = np.clip(l + np.tile(BAYER4, (h // 4 + 1, w // 4 + 1))[:h, :w] * 0.09, 0, 0.999)
    b = np.dstack([pal[(l ** 0.9 * len(pal)).astype(int)], a[..., 3]])
    b[a[..., 3] == 0] = 0
    return ampliar(contorno(b, (20, 16, 13)))


def p5_hd_selout(im):
    a = reduzir(im, 192)
    h = hsv(a)
    h[..., 2] = np.round(h[..., 2] / 255 * 4) / 4 * 235 + 20      # luz em 4 faixas
    h[..., 1] = np.clip(h[..., 1] * 1.12, 0, 255)
    b = de_hsv(h, a[..., 3])
    q = img(b).convert('RGB').quantize(32, method=Image.Quantize.MEDIANCUT).convert('RGB')
    b = np.dstack([np.asarray(q, float), a[..., 3]])
    # sel-out: contorno colorido (a própria cor escurecida), não preto.
    al = b[..., 3] > 0
    viz = np.zeros(al.shape + (3,)); cnt = np.zeros(al.shape)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        m = desloca(al, dy, dx)
        viz += desloca(b[..., :3], dy, dx) * m[..., None]; cnt += m
    borda = (cnt > 0) & ~al
    b[borda, :3] = viz[borda] / cnt[borda][:, None] * 0.38
    b[borda, 3] = 255
    b[~al & ~borda] = 0
    return ampliar(b)


def p6_filtro(im, bloco=6):
    a = arr(im)
    n = LADO // bloco
    m = img(a).resize((n, n), Image.BOX)
    q = m.convert('RGB').quantize(64, method=Image.Quantize.MEDIANCUT).convert('RGB')
    b = np.dstack([np.asarray(q, float), np.where(arr(m)[..., 3] > 110, 255, 0)])
    out = arr(ampliar(b))
    # Grade sutil de "pixel de tela" por cima do 3D ao vivo.
    yy, xx = np.mgrid[0:LADO, 0:LADO]
    grade = ((yy % bloco == 0) | (xx % bloco == 0))
    out[grade & (out[..., 3] > 0), :3] *= 0.86
    return img(out)


# ── anime ────────────────────────────────────────────────────────────────
def a1_cel(im):
    a = arr(im.filter(ImageFilter.ModeFilter(5)))
    h = hsv(a)
    v = h[..., 2] / 255
    h[..., 2] = np.select([v < 0.42, v < 0.78], [0.42, 0.72], 0.98) * 255 * (0.55 + 0.45 * v)  # 3 tons chapados
    h[..., 2] = np.clip(h[..., 2] / np.max(h[..., 2]) * 255, 0, 255)
    h[..., 1] = np.clip(h[..., 1] * 1.1, 0, 255)
    b = de_hsv(h, a[..., 3])
    e = bordas(arr(im), 44, 2)
    b[..., :3] = b[..., :3] * (1 - e[..., None]) + np.array([40, 22, 30]) * e[..., None]
    return img(b)


def a2_vhs90(im):
    a = arr(im.filter(ImageFilter.ModeFilter(3)))
    h = hsv(a)
    h[..., 2] = np.round(h[..., 2] / 255 * 5) / 5 * 255
    h[..., 1] *= 0.82
    b = de_hsv(h, a[..., 3])
    b[..., :3] = b[..., :3] * [1.06, 0.98, 0.88] + [10, 4, 0]          # cel antigo mais quente
    rgb = img(b).convert('RGB')
    ycc = np.asarray(rgb.convert('YCbCr'), float)
    for c in (1, 2):                                                    # croma borrado da fita
        ycc[..., c] = np.asarray(Image.fromarray(ycc[..., c].astype(np.uint8)).filter(ImageFilter.BoxBlur(3)), float)
    rgb = np.asarray(Image.fromarray(ycc.astype(np.uint8), 'YCbCr').convert('RGB'), float)
    rgb[..., 0] = np.roll(rgb[..., 0], 3, 1); rgb[..., 2] = np.roll(rgb[..., 2], -2, 1)  # aberração
    rgb += RNG.normal(0, 7, rgb.shape)                                  # grão
    rgb[::3] *= 0.9                                                     # linhas de varredura
    al = np.asarray(Image.fromarray(a[..., 3].astype(np.uint8)).filter(ImageFilter.MaxFilter(3)), float)
    return img(np.dstack([rgb, al]))


def a3_manga(im):
    a = arr(im)
    l = lum(a[..., :3]) / 255
    h, w = l.shape
    yy, xx = np.mgrid[0:h, 0:w]
    # Retícula: grade de pontos a 45°, raio pela escuridão.
    u = (xx + yy) / 7.0; v = (xx - yy) / 7.0
    dist = np.hypot(u - np.round(u), v - np.round(v))
    tom = np.where(dist < (0.62 - l) * 0.9, 0, 255)
    out = np.select([l < 0.22, l > 0.80], [0, 255], tom)
    e = bordas(a, 34, 2)
    out = np.where(e > 0, 0, out)
    g = np.dstack([out, out, out, a[..., 3]])
    return img(g)


def a4_aquarela(im):
    a = arr(im)
    base = img(a).filter(ImageFilter.ModeFilter(7)).filter(ImageFilter.GaussianBlur(1.6))
    b = arr(base)
    b[..., :3] = b[..., :3] * 0.82 + 255 * 0.18                         # pastel, luz difusa
    # Pigmento acumula na borda das manchas.
    l = lum(b[..., :3]); lb = np.asarray(Image.fromarray(np.clip(l, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(4)), float)
    b[..., :3] *= np.clip(1 - np.maximum(lb - l, 0)[..., None] / 120, 0.7, 1)[..., :, :]
    papel = np.asarray(Image.fromarray(RNG.normal(128, 40, (LADO, LADO)).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), float)
    b[..., :3] *= (0.93 + 0.07 * papel / 255)[..., None]
    e = bordas(a, 40, 1)
    e = np.asarray(Image.fromarray((e * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), float) / 255
    b[..., :3] = b[..., :3] * (1 - 0.6 * e[..., None]) + np.array([110, 70, 60]) * 0.6 * e[..., None]
    al = np.asarray(Image.fromarray(a[..., 3].astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5)), float)
    return img(np.dstack([b[..., :3], al]))


def a5_sticker(im):
    a = arr(im.filter(ImageFilter.ModeFilter(5)))
    q = img(a).convert('RGB').quantize(14, method=Image.Quantize.MEDIANCUT).convert('RGB')
    b = np.dstack([np.asarray(q, float), a[..., 3]])
    e = bordas(arr(im), 50, 2)
    b[..., :3] = b[..., :3] * (1 - e[..., None]) + np.array([45, 30, 40]) * e[..., None]
    sil = Image.fromarray((a[..., 3] > 0).astype(np.uint8) * 255)
    grossa = np.asarray(sil.filter(ImageFilter.MaxFilter(17)), float) / 255
    sombra = np.asarray(sil.filter(ImageFilter.MaxFilter(17)).filter(ImageFilter.GaussianBlur(6)), float) / 255
    sombra = desloca(sombra, 8, 6)
    out = np.zeros_like(b)
    out[..., 3] = sombra * 90
    out[grossa > 0] = [255, 255, 255, 255]                               # borda branca de adesivo
    m = a[..., 3] > 0
    out[m] = b[m]
    return img(out)


def a6_keyvisual(im):
    a = arr(im)
    h = hsv(a); h[..., 1] = np.clip(h[..., 1] * 1.25, 0, 255); b = de_hsv(h, a[..., 3])
    l = lum(b[..., :3])
    brilho = np.where(l > 200, l - 200, 0)[..., None] * b[..., :3] / 255
    glow = np.asarray(img(np.dstack([brilho * 4, np.full(l.shape, 255)])).convert('RGB').filter(ImageFilter.GaussianBlur(10)), float)
    b[..., :3] = 255 - (255 - b[..., :3]) * (255 - glow * 0.8) / 255      # screen
    # Luz de contorno: interior perto da silhueta fica mais claro e rosado.
    sil = Image.fromarray((a[..., 3] > 0).astype(np.uint8) * 255)
    dentro = np.asarray(sil.filter(ImageFilter.MinFilter(9)), float) / 255
    aro = (a[..., 3] > 0) & (dentro == 0)
    b[aro, :3] = b[aro, :3] * 0.5 + np.array([255, 225, 235]) * 0.5
    halo = np.asarray(sil.filter(ImageFilter.GaussianBlur(14)), float)
    out = np.zeros_like(b); out[..., :3] = [255, 214, 170]; out[..., 3] = halo * 0.45
    m = a[..., 3] > 0; out[m] = b[m]
    return img(out)


PIXEL = [('p1', 'Sprite 128 px · cores dela', p1_sprite128), ('p2', '96 px · PICO-8 + dithering', p2_pico8),
         ('p3', '64 px · Game Boy', p3_gameboy), ('p4', '128 px · âmbar da Forja', p4_ambar),
         ('p5', '192 px · HD pixel, contorno colorido', p5_hd_selout), ('p6', 'Filtro por cima do 3D (bloco 6 px)', p6_filtro)]
ANIME = [('a1', 'Cel shading de anime TV', a1_cel), ('a2', 'Anime anos 90 / VHS', a2_vhs90),
         ('a3', 'Mangá P&B com retícula', a3_manga), ('a4', 'Aquarela / estilo Ghibli suave', a4_aquarela),
         ('a5', 'Adesivo (sticker) flat', a5_sticker), ('a6', 'Key visual brilhante', a6_keyvisual)]


def fonte_jogo():
    jogo = Image.open(sys.argv[1]).convert('RGBA')
    return jogo.crop((95, 40, 355, 300)).resize((LADO, LADO), Image.LANCZOS)


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    fontes = {'3d': Image.open(RAIZ / 'base/base.png').convert('RGBA'), 'jogo': fonte_jogo()}
    fontes['jogo'].save(SAIDA / 'jogo_base.png')
    fontes['3d'].save(SAIDA / '3d_base.png')
    for nome, im in fontes.items():
        for chave, _, f in PIXEL + ANIME:
            r = f(im)
            (r[0] if isinstance(r, tuple) else r).save(SAIDA / f'{nome}_{chave}.png', optimize=True)
            print(nome, chave)
    # Animações (render 3D): sprite 128 com paleta fixa (sem cintilar) e cel shading.
    quadros = [Image.open(RAIZ / f'base/quadro_{i:02d}.png').convert('RGBA') for i in range(36)]
    _, pal = p1_sprite128(quadros[0])
    for chave, f in (('p1', lambda q: p1_sprite128(q, pal)[0]), ('a1', a1_cel)):
        fr = [f(q).resize((384, 384), Image.NEAREST if chave == 'p1' else Image.LANCZOS) for q in quadros]
        fr[0].save(SAIDA / f'anim_{chave}.webp', save_all=True, append_images=fr[1:], duration=83, loop=0,
                   lossless=chave == 'p1', quality=88)
        print('anim', chave)
    json.dump({'pixel': [[c, t] for c, t, _ in PIXEL], 'anime': [[c, t] for c, t, _ in ANIME]},
              open(SAIDA / 'indice.json', 'w'), ensure_ascii=False)


if __name__ == '__main__':
    main()
