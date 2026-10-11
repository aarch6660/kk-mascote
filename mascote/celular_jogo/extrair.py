#!/usr/bin/env python3
"""Smartphone original do jogo para a pose de escrita (somente leitura).

    $PYTHON_PERSONAGEM mascote/celular_jogo/extrair.py

Lê action/mapitem/00.unity3d e grava aqui p_o_koi_ei_smaho00.obj e as texturas
mt_koi_ei_kagami00(.png/_em.png) usadas por celular.gd.
"""
import os
from pathlib import Path

import UnityPy

AQUI = Path(__file__).resolve().parent
JOGO = Path(os.environ.get("KK_JOGO") or Path.home() / "Downloads/Koikatsu.Party/Koikatsu Party") / "abdata"
MALHA = "p_o_koi_ei_smaho00"
TEXTURAS = ("mt_koi_ei_kagami00", "mt_koi_ei_kagami00_em")

feitos = set()
for o in UnityPy.load(str(JOGO / "action/mapitem/00.unity3d")).objects:
    nome = o.peek_name()
    if o.type.name == "Mesh" and nome == MALHA:
        (AQUI / (MALHA + ".obj")).write_text(o.read().export())
        feitos.add(nome)
    elif o.type.name == "Texture2D" and nome in TEXTURAS:
        o.read().image.save(AQUI / (nome + ".png"))
        feitos.add(nome)
faltando = {MALHA, *TEXTURAS} - feitos
if faltando:
    raise SystemExit("Ausente no pacote: " + ", ".join(sorted(faltando)))
print("Celular extraído em", AQUI)
