#!/usr/bin/env python3
"""Cinco gestos cotidianos originais, escolhidos nas pranchas de f_tachi_*."""
import extrair_anime

# Esses cinco clipes só têm variante única; nenhuma variante _M consta no catálogo.
GESTOS = [
    ("gesto_ajeitar_cabelo", "action/animator/00.unity3d#1573606561269526734", "gesto"),
    ("gesto_mao_boca", "action/animator/00.unity3d#512709581550201381", "gesto"),
    ("gesto_olhar_longe", "action/animator/00.unity3d#-3984594730550675038", "gesto"),
    ("gesto_maos_juntas", "action/animator/00.unity3d#-8284073135051822929", "gesto"),
    ("gesto_reverencia", "action/animator/00.unity3d#-2806088812363181893", "gesto"),
]

if __name__ == "__main__":
    extrair_anime.main(GESTOS, "extrair_gestos_hana_resultado.json",
                       "Gesto cotidiano original; execução única, reverência reservada a cumprimento.")
