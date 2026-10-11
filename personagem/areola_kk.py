"""Parâmetros e referência numérica da camada corporal de main_skin.

UV1 do Unity chega como UV2 ao Godot, com V invertido no GLB. A cor dos
vértices é uma máscara de coordenadas; não é uma tinta a multiplicar na pele.
"""
import math

import numpy as np

from compor_olhos import amostrar_clamp, linear


def configurar_areola(conf, corpo, material, textura, espaco_cor):
    """Conecta os dados originais do card sem trocar a textura geral da pele."""
    uv = material['uv_texturas']['_overtex1']
    floats = material['floats']
    if espaco_cor not in (0, 1):
        raise ValueError('TextureColorSpace Unity desconhecido')
    dados = {
        'tamanho': float(corpo['areolaSize']),
        'brilho': float(corpo['nipGlossPower']),
        'mistura': float(floats['_tex1mask']),
        'deformar': float(floats['_nip']),
        'uv_unity': [*uv['escala'], *uv['offset']],
        'id': int(corpo['nipId']),
        'srgb': espaco_cor == 1,
    }
    cor = list(corpo['nipColor'])
    valores = [dados[k] for k in ('tamanho', 'brilho', 'mistura', 'deformar')]
    valores += dados['uv_unity'] + cor
    if len(cor) != 4 or not all(math.isfinite(v) for v in valores):
        raise ValueError('Parâmetros de pigmentação inválidos no card/material')
    conf['areola'] = dados
    conf['texturas']['_overtex1'] = textura
    conf.setdefault('sobre_cores', {})['_overtex1'] = cor


def coordenadas_areola(uv2_godot, vermelho, dados):
    """DXBC main_skin, primeiro bloco: UV radial + COLOR.r + Texture ST."""
    uv = np.asarray(uv2_godot, dtype=float).copy()
    uv[..., 1] = 1.0 - uv[..., 1]
    radial = np.clip(np.linalg.norm(uv - .5, axis=-1) * 16.6666698 - 1, 0, 1)
    tamanho = dados['tamanho']
    ajustada = uv * (2 - 1.4 * tamanho) + .7 * tamanho - .5
    uv += radial[..., None] * dados['deformar'] * (ajustada - uv)
    uv *= np.asarray(vermelho)[..., None]
    st = dados['uv_unity']
    uv = uv * st[:2] + st[2:]
    uv[..., 1] = 1.0 - uv[..., 1]
    return uv


def compor_amostra(base_linear, textura, uv2_godot, vermelho, dados, cor_srgb):
    """Oráculo CPU em linear; usa pixels, não renderiza uma personagem."""
    uv = coordenadas_areola(uv2_godot, vermelho, dados)
    imagem = np.asarray(textura, dtype=float).copy()
    if dados['srgb']:
        imagem[..., :3] = linear(imagem[..., :3])
    amostra = amostrar_clamp(imagem, uv[..., 0], uv[..., 1])
    cor = linear(np.asarray(cor_srgb[:3]))
    multiply = amostra[..., :3] * cor
    mascara = amostra[..., :1] * (cor + amostra[..., 1:2] * dados['brilho'] * .33)
    tinta = multiply + np.clip(dados['mistura'], 0, 1) * (mascara - multiply)
    alpha = amostra[..., 3:4] * cor_srgb[3]
    return np.asarray(base_linear) * (1 - alpha) + tinta * alpha
