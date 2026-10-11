#!/usr/bin/env python3
"""Esperas em pé (sem toque) do início da cena H, posição 立ち愛撫.

Regra do projeto mudada pelo usuário em 2026-10-11: abdata/h/ pode ser lido, mas só poses NÃO sexuais
entram no mascote. Aqui só os três estados de espera pura do controlador kha_f_00
(h/anim/female/00_00_00.unity3d, posição 立ち愛撫 em h/list/00_00): S_Idle, M_Idle, L_Idle.
Nenhum estado de toque/ação é lido. Saída em exportados/ (o mascote só os usa depois de integrados).
"""
import hashlib
import json
import pathlib
import sys

import UnityPy

from extrair import DEFAULT_GAME, HERE, decode, skeleton
from glb import export_glb

BUNDLE = "h/anim/female/00_00_00.unity3d"
CONTROLADOR = "kha_f_00"
ESPERAS = {"S_Idle": "parada_espera_h", "M_Idle": "parada_espera_h_m", "L_Idle": "parada_espera_h_l"}


def clipes_do_controlador(env):
    obj = next(o for o in env.objects if o.type.name == "AnimatorController" and o.peek_name() == CONTROLADOR)
    c = obj.read_typetree()
    tos = dict(c["m_TOS"])
    saida = {}
    for s in c["m_Controller"]["m_StateMachineArray"][0]["data"]["m_StateConstantArray"]:
        d = s["data"]
        estado = tos.get(d["m_NameID"])
        if estado not in ESPERAS:
            continue
        ids = [n["data"]["m_ClipID"] for bt in d["m_BlendTreeConstantArray"] for n in bt["data"]["m_NodeArray"]
               if n["data"]["m_ClipID"] != 0xFFFFFFFF]
        if len(ids) != 1:
            raise ValueError(f"{estado}: esperado 1 clipe, achei {ids}")
        saida[estado] = c["m_AnimationClips"][ids[0]]["m_PathID"]
    if set(saida) != set(ESPERAS):
        raise ValueError(f"Estados ausentes: {set(ESPERAS) - set(saida)}")
    return saida


def main():
    caminho = DEFAULT_GAME / "abdata" / BUNDLE
    env = UnityPy.load(caminho.read_bytes())
    por_id = {o.path_id: o for o in env.objects if o.type.name == "AnimationClip"}
    nodes, hashes = skeleton(DEFAULT_GAME)
    relatorio = {"bundle": BUNDLE, "sha256_bundle": hashlib.sha256(caminho.read_bytes()).hexdigest(),
                 "controlador": CONTROLADOR, "posicao": "立ち愛撫 (h/list/00_00)", "clipes": []}
    for estado, pid in clipes_do_controlador(env).items():
        nome = ESPERAS[estado]
        data = por_id[pid].read_typetree()
        times, tracks, stats = decode(data, hashes)
        meta = {"name": nome, "source": estado, "source_id": f"{BUNDLE}#{pid}", "bundle": BUNDLE,
                "category": "idle", "loop": True, "fps": 30,
                "description": "Espera em pé do início da cena H (sem toque); pose de referência do usuário.",
                "coordinate_system": "glTF RH Y-up, reflection X from Unity", "decoder": stats,
                "glb": f"exportados/{nome}.glb"}
        destino = HERE / meta["glb"]
        export_glb(destino, nodes, times, tracks, meta)
        meta["bytes"] = destino.stat().st_size
        meta["sha256"] = hashlib.sha256(destino.read_bytes()).hexdigest()
        meta["duracao"] = float(times[-1]) if len(times) else 0.0
        relatorio["clipes"].append(meta)
        print(nome, estado, pid, round(meta["duracao"], 2), "s")
    (HERE / "extrair_espera_h_resultado.json").write_text(json.dumps(relatorio, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    sys.exit(main())
