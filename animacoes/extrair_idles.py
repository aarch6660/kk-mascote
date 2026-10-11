#!/usr/bin/env python3
"""Poses de espera originais (f_tachi_*) usadas como base da parada.

Escolhidas pelas pranchas de candidatas_idle.py + ../mascote/testes/previa_idle.py.
"""
import extrair_anime

IDLES = [
    ("parada_relaxada", "action/animator/00.unity3d#361097640689683045", "idle"),      # f_tachi_00_21
    ("parada_maos_atras", "action/animator/00.unity3d#3096026579852264979", "idle"),   # f_tachi_00_20
    ("parada_timida", "action/animator/00.unity3d#3650696579081538623", "idle"),       # f_tachi_00_16_00_M
    ("parada_balanco", "action/animator/00.unity3d#6446696548850211258", "idle"),      # f_tachi_00_12
]

if __name__ == "__main__":
    extrair_anime.main(IDLES, "extrair_idles_resultado.json",
                       "Pose de espera original do jogo, base da parada do mascote.")
