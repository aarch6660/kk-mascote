#!/usr/bin/env python3
"""Extrai um allowlist pequeno de clipes cotidianos para mascote e visualizador."""
import hashlib
import json
import math
import os
import pathlib
import shutil
import tempfile

import numpy as np

from extrair import ANIM_BUNDLE, DEFAULT_GAME, HERE, decode, identity, load_bundle, skeleton
from glb import export_glb


# IDs copiados do catalogo.json para que a extração falhe se uma fonte mudar.
TARGETS = [
    ("conversa_gesto_00", "action/animator/00.unity3d#5023215851225158853", "gesto"),
    ("conversa_gesto_03", "action/animator/00.unity3d#-6337597820189136978", "gesto"),
    ("conversa_gesto_07", "action/animator/00.unity3d#-323728162817458208", "gesto"),
    ("conversa_gesto_11", "action/animator/00.unity3d#-3556458055064345838", "gesto"),
    ("correr_normal", "action/animator/00.unity3d#6197228902482319282", "corrida"),
    ("correr_zangada", "action/animator/00.unity3d#-1434750556206090013", "corrida"),
    ("postura_pensativa", "action/animator/00.unity3d#4262814774556020851", "gesto"),
    ("comemorar_02", "action/animator/00.unity3d#-3033933175135553321", "gesto"),
    ("comemorar_03", "action/animator/00.unity3d#1872137345676564267", "gesto"),
    ("sentada_estudo", "action/animator/00.unity3d#839971045493166613", "sentado"),
    ("sentada_leitura", "action/animator/00.unity3d#-5410733543992413108", "sentado"),
    ("sentada_musica", "action/animator/00.unity3d#-2255328365711213542", "sentado"),
]
ALLOWED_BUNDLES = {ANIM_BUNDLE, "adv/motion/controller/adv/00.unity3d"}
MAX_ROOT_NET = 0.01
MAX_ROOT_SPAN = 0.05
MAX_HEIGHT_NET = 0.015
MAX_HIPS_NET = 0.20


def read_json(path):
    return json.loads(path.read_text())


def write_json(path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    os.replace(tmp, path)


def track_for(tracks, nodes, bone, prop):
    return next((t for t in tracks if nodes[t["node"]]["name"] == bone and t["property"] == prop), None)


def vector_metrics(track):
    if track is None:
        return None
    values = np.asarray(track["values"], dtype=np.float64)
    start, end = values[0], values[-1]
    delta = end - start
    span = np.ptp(values, axis=0)
    return {
        "start": start.tolist(), "end": end.tolist(), "delta": delta.tolist(),
        "delta_norm": float(np.linalg.norm(delta)), "span": span.tolist(),
        "span_max_component": float(np.max(span)),
    }


def quaternion_delta_degrees(track):
    if track is None:
        return None
    values = np.asarray(track["values"], dtype=np.float64)
    a, b = values[0], values[-1]
    dot = float(np.clip(abs(np.dot(a, b)), 0.0, 1.0))
    return math.degrees(2 * math.acos(dot))


def validate_bindings(clip, catalog, hashes):
    if clip["mode"] != "generic":
        raise ValueError(f"modo incompatível: {clip['mode']}")
    binding_set = catalog["binding_sets"][clip["binding_set"]]
    unresolved = []
    for bone_hash, attribute, type_id in binding_set:
        path = catalog["paths"].get(str(bone_hash))
        if type_id != 4 or attribute not in (1, 2, 3) or bone_hash not in hashes:
            unresolved.append({"hash": bone_hash, "attribute": attribute, "type_id": type_id})
        elif path is None or (path.get("bone") is None and not path.get("auxiliary_low_only")):
            unresolved.append({"hash": bone_hash, "attribute": attribute, "type_id": type_id})
    if unresolved:
        raise ValueError(f"bindings sem resolução comprovada: {unresolved[:5]}")


def main(targets=TARGETS, relatorio="extrair_anime_resultado.json", descricao="Extração cotidiana seletiva; nome conservador, aguardando inspeção visual."):
    catalog_path = HERE / "catalogo.json"
    selection_path = HERE / "selecao.json"
    manifest_path = HERE / "exportados" / "manifesto.json"
    catalog = read_json(catalog_path)
    selection = read_json(selection_path)
    manifest = read_json(manifest_path)

    if len(targets) > 14 or len({sid for _, sid, _ in targets}) != len(targets):
        raise ValueError("Allowlist excede o limite ou contém source_id duplicado")
    by_id = {clip["id"]: clip for clip in catalog["clips"]}
    existing_sources = {row.get("source_id") for row in manifest}
    existing_names = {row.get("name") for row in manifest}
    project = HERE.parent
    destinations = [project / "mascote" / "anims", project / "visualizador" / "anims"]
    for dest in destinations:
        resolved = dest.resolve()
        if not resolved.is_relative_to(project.resolve()) or not resolved.is_dir():
            raise ValueError(f"Destino ausente ou fora do projeto: {dest}")

    nodes, hashes = skeleton(DEFAULT_GAME)
    envs = {}
    prepared = []
    source_rows = []

    with tempfile.TemporaryDirectory(prefix="extrair-anime-", dir=HERE) as temp_name:
        temp_dir = pathlib.Path(temp_name)
        for name, source_id, category in targets:
            if source_id not in by_id:
                raise ValueError(f"source_id não consta no catálogo: {source_id}")
            clip = by_id[source_id]
            bundle = clip["bundle"]
            if bundle not in ALLOWED_BUNDLES:
                raise ValueError(f"Bundle fora da allowlist cotidiana: {bundle}")
            if clip["selected"] or source_id in existing_sources:
                raise ValueError(f"Fonte já exportada; não duplicar: {source_id}")
            if name in existing_names or (HERE / "exportados" / f"{name}.glb").exists():
                raise ValueError(f"Nome de saída já existe: {name}")
            for dest in destinations:
                if (dest / f"{name}.glb").exists():
                    raise ValueError(f"Destino já possui o clipe: {dest / (name + '.glb')}")

            if bundle not in envs:
                envs[bundle] = load_bundle(DEFAULT_GAME, bundle)
            env = envs[bundle]
            objects = [o for o in env.objects if o.type.name == "AnimationClip" and identity(bundle, o.path_id) == source_id]
            if len(objects) != 1:
                raise ValueError(f"Fonte ausente/ambígua no bundle: {source_id}")
            obj = objects[0]
            data = obj.read_typetree()
            validate_bindings(clip, catalog, hashes)
            times, tracks, stats = decode(data, hashes)

            root = vector_metrics(track_for(tracks, nodes, "cf_j_root", "translation"))
            height = vector_metrics(track_for(tracks, nodes, "cf_n_height", "translation"))
            hips = vector_metrics(track_for(tracks, nodes, "cf_j_hips", "translation"))
            if root is None or hips is None:
                raise ValueError(f"Pista de raiz/quadril ausente: {name}")
            root_rotation_delta = quaternion_delta_degrees(track_for(tracks, nodes, "cf_j_root", "rotation"))
            metrics = {
                "cf_j_root_translation": root,
                "cf_n_height_translation": height,
                "cf_j_hips_translation": hips,
                "cf_j_root_rotation_end_delta_degrees": root_rotation_delta,
                "thresholds": {"root_net": MAX_ROOT_NET, "root_span_component": MAX_ROOT_SPAN,
                               "height_net": MAX_HEIGHT_NET, "hips_net": MAX_HIPS_NET},
            }
            if root["delta_norm"] > MAX_ROOT_NET or root["span_max_component"] > MAX_ROOT_SPAN:
                raise ValueError(f"root motion excede limite: {name}: {metrics}")
            if height is not None and height["delta_norm"] > MAX_HEIGHT_NET:
                raise ValueError(f"translação persistente de altura: {name}: {metrics}")
            if hips["delta_norm"] > MAX_HIPS_NET:
                raise ValueError(f"translação persistente do quadril: {name}: {metrics}")

            item = {"name": name, "source": clip["name"], "bundle": bundle,
                    "category": category, "loop": bool(clip["loop"]),
                    "description": descricao}
            meta = dict(item, source_id=source_id, length=clip["length"], source_loop=clip["loop"], fps=30,
                        coordinate_system="glTF RH Y-up, reflection X from Unity", decoder=stats,
                        root_motion=metrics, glb=f"exportados/{name}.glb")
            temporary_glb = temp_dir / f"{name}.glb"
            export_glb(temporary_glb, nodes, times, tracks, meta)
            meta["bytes"] = temporary_glb.stat().st_size
            meta["sha256"] = hashlib.sha256(temporary_glb.read_bytes()).hexdigest()
            prepared.append((temporary_glb, meta, item, clip))
            source_rows.append({"name": name, "source": clip["name"], "source_id": source_id,
                                "bundle": bundle, "length": clip["length"], "source_loop": clip["loop"],
                                "bindings": {"total": clip["binding_count"],
                                             "resolved": clip["resolved_transform_bindings"],
                                             "omitted_low_auxiliary": len(stats["omitted_low_auxiliary_bindings"])},
                                "metrics": metrics, "sha256": meta["sha256"], "bytes": meta["bytes"]})

        # Confere os destinos antes de publicar qualquer GLB.
        for name, _, _ in targets:
            if any((dest / f"{name}.glb").exists() for dest in destinations):
                raise ValueError(f"Colisão de nome detectada antes da cópia: {name}")

        for temp_glb, meta, item, clip in prepared:
            final = HERE / meta["glb"]
            os.replace(temp_glb, final)
            for dest in destinations:
                shutil.copy2(final, dest / final.name)
            selection.append(item)
            manifest.append(meta)
            clip["selected"] = True
            clip["export"] = meta["glb"]

        write_json(selection_path, selection)
        write_json(manifest_path, manifest)
        write_json(catalog_path, catalog)

    result = {
        "created_at_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "baseline": "evidencias/extrair_anime_baseline.json",
        "count": len(source_rows),
        "destinations": [str(p.relative_to(project)) for p in destinations],
        "thresholds": {"root_net": MAX_ROOT_NET, "root_span_component": MAX_ROOT_SPAN,
                       "height_net": MAX_HEIGHT_NET, "hips_net": MAX_HIPS_NET},
        "clips": source_rows,
    }
    write_json(HERE / "evidencias" / relatorio, result)
    print(json.dumps({"count": len(source_rows), "report": "evidencias/" + relatorio,
                      "clips": [{"name": x["name"], "seconds": round(x["length"], 3), "sha256": x["sha256"]}
                                for x in source_rows]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
