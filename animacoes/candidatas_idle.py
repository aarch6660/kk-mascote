#!/usr/bin/env python3
"""Exporta poses em pé originais (f_tachi_*) para inspeção, sem tocar em seleção/manifesto.

Saída: animacoes/candidatas/<fonte>.glb + candidatas/relatorio.json.
Tamanho de corpo: variantes _M quando o jogo separa L/M/S.
"""
import json

from extrair import ANIM_BUNDLE, DEFAULT_GAME, HERE, decode, identity, load_bundle, skeleton
from glb import export_glb
from extrair_anime import track_for, validate_bindings, vector_metrics

OUT = HERE / "candidatas"


def escolher(catalog):
    usados = {c["name"] for c in catalog["clips"] if c.get("selected")}
    nomes = []
    for c in catalog["clips"]:
        n = c["name"]
        if not n.startswith("f_tachi_00_") or n in usados or c["bundle"] != ANIM_BUNDLE:
            continue
        if n[-2:] in ("_L", "_S"):
            continue
        nomes.append(c)
    return nomes


def main():
    catalog = json.loads((HERE / "catalogo.json").read_text())
    OUT.mkdir(exist_ok=True)
    nodes, hashes = skeleton(DEFAULT_GAME)
    env = load_bundle(DEFAULT_GAME, ANIM_BUNDLE)
    por_id = {identity(ANIM_BUNDLE, o.path_id): o for o in env.objects if o.type.name == "AnimationClip"}
    relatorio = []
    for clip in escolher(catalog):
        validate_bindings(clip, catalog, hashes)
        times, tracks, stats = decode(por_id[clip["id"]].read_typetree(), hashes)
        root = vector_metrics(track_for(tracks, nodes, "cf_j_root", "translation"))
        hips = vector_metrics(track_for(tracks, nodes, "cf_j_hips", "translation"))
        meta = dict(name=clip["name"], source=clip["name"], source_id=clip["id"], bundle=ANIM_BUNDLE,
                    length=clip["length"], loop=bool(clip["loop"]), fps=30,
                    coordinate_system="glTF RH Y-up, reflection X from Unity", decoder=stats)
        saida = OUT / f"{clip['name']}.glb"
        export_glb(saida, nodes, times, tracks, meta)
        relatorio.append(dict(name=clip["name"], source_id=clip["id"], length=clip["length"], loop=clip["loop"],
                              root_delta=root and root["delta_norm"], hips_delta=hips and hips["delta_norm"],
                              bytes=saida.stat().st_size))
        print(clip["name"], round(clip["length"], 2), "loop" if clip["loop"] else "único", flush=True)
    (OUT / "relatorio.json").write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
