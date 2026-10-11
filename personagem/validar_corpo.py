#!/usr/bin/env python3
"""Audita estrutura e skinning dos GLBs de uma boneca sem usar Blender.

Leitura somente dos arquivos locais do projeto. A rotina não abre o jogo nem
modifica modelos; para --pasta grava por padrão em saida/validacao_corpo.json,
e para --todas grava relatórios individuais na pasta de evidências.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import struct
import sys
from typing import Any

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
CANONICAL_PATH = ROOT / "animacoes" / "esqueleto.json"
CATALOG_PATH = ROOT / "bonecas" / "catalogo.json"
REPORT_DIR = ROOT / "mascote" / "evidencias" / "corpo-fisica-2026-10-09"
FLOAT_TOL = 1e-4
BIND_TOL = 1e-4


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _read_glb(path: pathlib.Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    if len(raw) < 28:
        raise ValueError("arquivo menor que cabeçalho GLB")
    magic, version, total = struct.unpack_from("<III", raw, 0)
    if magic != 0x46546C67 or version != 2 or total != len(raw):
        raise ValueError(f"cabeçalho GLB inválido (magic={magic:#x}, version={version}, total={total})")
    json_len, json_type = struct.unpack_from("<II", raw, 12)
    if json_type != 0x4E4F534A or 20 + json_len + 8 > len(raw):
        raise ValueError("chunk JSON ausente ou truncado")
    doc = json.loads(raw[20:20 + json_len].decode("utf-8").rstrip(" \0"))
    bin_header = 20 + json_len
    bin_len, bin_type = struct.unpack_from("<II", raw, bin_header)
    if bin_type != 0x004E4942 or bin_header + 8 + bin_len > len(raw):
        raise ValueError("chunk BIN ausente ou truncado")
    return doc, raw[bin_header + 8:bin_header + 8 + bin_len]


def _accessor(doc: dict[str, Any], binary: bytes, index: int) -> np.ndarray:
    a = doc["accessors"][index]
    if "sparse" in a:
        raise ValueError("accessor sparse não esperado neste exportador")
    view = doc["bufferViews"][a["bufferView"]]
    dtype = {5121: "u1", 5123: "<u2", 5125: "<u4", 5126: "<f4"}[a["componentType"]]
    width = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT2": 4, "MAT3": 9, "MAT4": 16}[a["type"]]
    itemsize = np.dtype(dtype).itemsize
    stride = int(view.get("byteStride", width * itemsize))
    start = int(view.get("byteOffset", 0)) + int(a.get("byteOffset", 0))
    count = int(a["count"])
    if stride == width * itemsize:
        out = np.frombuffer(binary, dtype=dtype, count=count * width, offset=start).reshape(count, width)
    else:
        out = np.ndarray((count, width), dtype=dtype, buffer=binary, offset=start, strides=(stride, itemsize)).copy()
    return out


def _trs(node: dict[str, Any]) -> np.ndarray:
    t = np.asarray(node.get("translation", [0, 0, 0]), dtype=np.float64)
    q = np.asarray(node.get("rotation", [0, 0, 0, 1]), dtype=np.float64)
    s = np.asarray(node.get("scale", [1, 1, 1]), dtype=np.float64)
    if "matrix" in node:
        return np.asarray(node["matrix"], dtype=np.float64).reshape(4, 4).T
    if not np.isfinite(t).all() or not np.isfinite(q).all() or not np.isfinite(s).all():
        raise ValueError("TRS contém NaN/Inf")
    qnorm = float(np.linalg.norm(q))
    if qnorm < 1e-12:
        raise ValueError("quaternion de comprimento zero")
    x, y, z, w = q / qnorm
    r = np.array([
        [1 - 2 * (y*y + z*z), 2 * (x*y - z*w), 2 * (x*z + y*w)],
        [2 * (x*y + z*w), 1 - 2 * (x*x + z*z), 2 * (y*z - x*w)],
        [2 * (x*z - y*w), 2 * (y*z + x*w), 1 - 2 * (x*x + y*y)],
    ])
    m = np.eye(4)
    m[:3, :3] = r @ np.diag(s)
    m[:3, 3] = t
    return m


def _triangles(mesh: dict[str, Any], doc: dict[str, Any]) -> int:
    total = 0
    for primitive in mesh.get("primitives", []):
        count = int(doc["accessors"][primitive["indices"]]["count"])
        if count % 3:
            raise ValueError(f"índice não forma triângulos: count={count}")
        total += count // 3
    return total


def _audit_glb(path: pathlib.Path, canonical: list[dict[str, Any]], errors: list[str]) -> dict[str, Any]:
    summary: dict[str, Any] = {"arquivo": path.name, "existe": path.is_file()}
    if not path.is_file():
        _fail(errors, f"{path.name}: arquivo obrigatório ausente")
        return summary
    try:
        doc, binary = _read_glb(path)
    except Exception as exc:
        _fail(errors, f"{path.name}: GLB inválido: {type(exc).__name__}: {exc}")
        return summary

    nodes = doc.get("nodes", [])
    meshes = doc.get("meshes", [])
    skins = doc.get("skins", [])
    summary.update({"nos": len(nodes), "malhas": len(meshes), "skins": len(skins), "animacoes": len(doc.get("animations", []))})
    names: dict[str, list[int]] = {}
    parents: dict[int, int] = {}
    for i, node in enumerate(nodes):
        name = str(node.get("name", ""))
        names.setdefault(name, []).append(i)
        for child in node.get("children", []):
            if not isinstance(child, int) or child < 0 or child >= len(nodes):
                _fail(errors, f"{path.name}: node {i} tem filho inválido {child}")
            elif child in parents:
                _fail(errors, f"{path.name}: node {child} tem mais de um parent")
            else:
                parents[child] = i
        try:
            _trs(node)
        except Exception as exc:
            _fail(errors, f"{path.name}: TRS inválido no node {i} {name!r}: {exc}")
    if len(skins) != 1:
        _fail(errors, f"{path.name}: esperado exatamente um skin, achados {len(skins)}")
        skin = None
    else:
        skin = skins[0]
    bind_result: dict[str, Any] = {}
    joint_set = set(skin.get("joints", [])) if skin is not None else set()
    bone_nodes: dict[str, int] = {}
    mesh_names: dict[str, list[int]] = {}
    for i, node in enumerate(nodes):
        name = str(node.get("name", ""))
        if "mesh" in node:
            mesh_names.setdefault(name, []).append(i)
        elif i in joint_set:
            if name in bone_nodes:
                _fail(errors, f"{path.name}: nome de osso duplicado no skin: {name}")
            else:
                bone_nodes[name] = i
    bone_mesh_collisions = sorted(set(bone_nodes).intersection(mesh_names))
    duplicate_mesh_names = [name for name, indices in mesh_names.items() if len(indices) > 1]

    missing: list[str] = []
    parent_mismatch: list[dict[str, str]] = []
    for bone in canonical:
        name = bone["name"]
        if name not in bone_nodes:
            missing.append(name)
            continue
        expected_parent = canonical[bone["parent"]]["name"] if bone["parent"] >= 0 else None
        actual_index = parents.get(bone_nodes[name])
        actual_parent = nodes[actual_index].get("name") if actual_index is not None else None
        if actual_parent != expected_parent:
            parent_mismatch.append({"osso": name, "esperado": str(expected_parent), "atual": str(actual_parent)})
    if missing:
        _fail(errors, f"{path.name}: {len(missing)} ossos canônicos ausentes; amostra {missing[:5]}")
    if parent_mismatch:
        _fail(errors, f"{path.name}: parent canônico divergente; amostra {parent_mismatch[:3]}")

    if skin is not None:
        joints = skin.get("joints", [])
        if len(set(joints)) != len(joints) or any(not isinstance(j, int) or j < 0 or j >= len(nodes) for j in joints):
            _fail(errors, f"{path.name}: skin tem índices de joints duplicados/fora dos nodes")
        for name in (bone["name"] for bone in canonical):
            if name in bone_nodes and bone_nodes[name] not in joints:
                _fail(errors, f"{path.name}: osso canônico {name} não está listado no skin")
                break
        im_index = skin.get("inverseBindMatrices")
        if im_index is None:
            _fail(errors, f"{path.name}: inverseBindMatrices ausente")
        else:
            try:
                im_accessor = doc["accessors"][im_index]
                raw_ibm = _accessor(doc, binary, im_index)
                if im_accessor.get("type") != "MAT4" or len(raw_ibm) != len(joints):
                    _fail(errors, f"{path.name}: inverseBindMatrices count/type não corresponde aos joints")
                else:
                    # glTF armazena elementos MAT4 column-major no buffer.
                    ibms = raw_ibm.reshape(-1, 4, 4).transpose(0, 2, 1).astype(np.float64)
                    globals_: list[np.ndarray | None] = [None] * len(nodes)
                    def global_matrix(i: int) -> np.ndarray:
                        if globals_[i] is None:
                            parent = parents.get(i)
                            globals_[i] = (global_matrix(parent) if parent is not None else np.eye(4)) @ _trs(nodes[i])
                        return globals_[i]  # type: ignore[return-value]
                    residuals = [float(np.max(np.abs(global_matrix(j) @ ibm - np.eye(4)))) for j, ibm in zip(joints, ibms)]
                    max_residual = max(residuals, default=0.0)
                    bind_result = {"joints": len(joints), "inverse_bind_count": len(ibms), "residuo_max": max_residual,
                                   "residuo_p95": float(np.percentile(residuals, 95)) if residuals else 0.0, "tolerancia": BIND_TOL}
                    if not math.isfinite(max_residual) or max_residual > BIND_TOL:
                        _fail(errors, f"{path.name}: bind residual {max_residual:.6g} > {BIND_TOL:g}")
            except Exception as exc:
                _fail(errors, f"{path.name}: falha ao validar inverseBindMatrices: {type(exc).__name__}: {exc}")
    summary["bind"] = bind_result

    mesh_nodes = 0
    morph_total = 0
    target_summary: list[dict[str, Any]] = []
    weight_min = math.inf
    weight_max = -math.inf
    sum_min = math.inf
    sum_max = -math.inf
    max_joint_index = -1
    index_total = 0
    mesh_by_name = {str(m.get("name", f"mesh-{i}")): m for i, m in enumerate(meshes)}
    scene_nodes = set()
    if doc.get("scenes"):
        def walk(i: int) -> None:
            if i in scene_nodes or not isinstance(i, int) or i < 0 or i >= len(nodes):
                return
            scene_nodes.add(i)
            for child in nodes[i].get("children", []):
                walk(child)
        for root in doc["scenes"][doc.get("scene", 0)].get("nodes", []):
            walk(root)

    for ni, node in enumerate(nodes):
        if "mesh" not in node:
            continue
        mesh_nodes += 1
        if node["mesh"] < 0 or node["mesh"] >= len(meshes):
            _fail(errors, f"{path.name}: node {ni} mesh index inválido")
            continue
        if skin is not None and node.get("skin") not in (0,):
            _fail(errors, f"{path.name}: mesh node {node.get('name')} não usa skin 0")
        mesh = meshes[node["mesh"]]
        weights = mesh.get("weights", [])
        target_names = mesh.get("extras", {}).get("targetNames", [])
        if len(weights) != len(target_names):
            _fail(errors, f"{path.name}: {mesh.get('name')} weights/targetNames divergem ({len(weights)} vs {len(target_names)})")
        if len(set(target_names)) != len(target_names):
            _fail(errors, f"{path.name}: {mesh.get('name')} tem nomes morph duplicados")
        if mesh.get("primitives"):
            first_targets = len(mesh["primitives"][0].get("targets", []))
            if any(len(pr.get("targets", [])) != first_targets for pr in mesh["primitives"]):
                _fail(errors, f"{path.name}: {mesh.get('name')} primitives têm contagens morph distintas")
            if first_targets != len(weights):
                _fail(errors, f"{path.name}: {mesh.get('name')} target count != mesh weights")
        morph_total += len(target_names)
        if target_names:
            target_summary.append({"malha": mesh.get("name"), "targets": len(target_names), "tem_piscar": "piscar" in target_names,
                                  "nomes_sha256": hashlib.sha256("\n".join(target_names).encode()).hexdigest()})
        if mesh.get("name") == "cf_O_face" and "piscar" not in target_names:
            _fail(errors, f"{path.name}: cf_O_face perdeu o morph sintético piscar")

        for pi, primitive in enumerate(mesh.get("primitives", [])):
            attrs = primitive.get("attributes", {})
            required = ["POSITION", "NORMAL", "TANGENT", "TEXCOORD_0", "COLOR_0", "JOINTS_0", "WEIGHTS_0"]
            for key in required:
                if key not in attrs:
                    _fail(errors, f"{path.name}: {mesh.get('name')} primitive {pi} sem {key}")
            decoded: dict[str, np.ndarray] = {}
            for key in required:
                if key not in attrs:
                    continue
                try:
                    values = _accessor(doc, binary, attrs[key])
                    decoded[key] = values
                    if key not in ("JOINTS_0",) and not np.isfinite(values).all():
                        _fail(errors, f"{path.name}: {mesh.get('name')} {key} contém NaN/Inf")
                    if key == "COLOR_0" and (values.min(initial=0) < -FLOAT_TOL or values.max(initial=0) > 1 + FLOAT_TOL):
                        _fail(errors, f"{path.name}: {mesh.get('name')} COLOR_0 fora de [0,1]")
                except Exception as exc:
                    _fail(errors, f"{path.name}: accessor {mesh.get('name')} {key} inválido: {exc}")
            if all(k in decoded for k in ("POSITION", "NORMAL", "TANGENT", "COLOR_0", "JOINTS_0", "WEIGHTS_0")):
                vcount = len(decoded["POSITION"])
                for key, values in decoded.items():
                    if len(values) != vcount:
                        _fail(errors, f"{path.name}: {mesh.get('name')} atributo {key} tem count diferente de POSITION")
                jw = decoded["JOINTS_0"].astype(np.int64)
                ww = decoded["WEIGHTS_0"].astype(np.float64)
                if np.any(ww < -FLOAT_TOL):
                    _fail(errors, f"{path.name}: {mesh.get('name')} pesos negativos")
                sums = ww.sum(axis=1)
                low, high = float(sums.min(initial=1)), float(sums.max(initial=1))
                sum_min, sum_max = min(sum_min, low), max(sum_max, high)
                weight_min, weight_max = min(weight_min, float(ww.min(initial=0))), max(weight_max, float(ww.max(initial=0)))
                if np.any(np.abs(sums - 1.0) > FLOAT_TOL):
                    _fail(errors, f"{path.name}: {mesh.get('name')} WEIGHTS_0 soma fora de 1 (min={low:.7g}, max={high:.7g})")
                max_joint_index = max(max_joint_index, int(jw.max(initial=0)))
                if skin is not None and np.any(jw >= len(skin.get("joints", []))):
                    _fail(errors, f"{path.name}: {mesh.get('name')} JOINTS_0 referencia fora do skin")
                if "indices" not in primitive:
                    _fail(errors, f"{path.name}: {mesh.get('name')} primitive {pi} sem indices")
                else:
                    try:
                        indices = _accessor(doc, binary, primitive["indices"]).reshape(-1).astype(np.int64)
                        index_total += len(indices)
                        if len(indices) % 3:
                            _fail(errors, f"{path.name}: {mesh.get('name')} índice count não múltiplo de 3")
                        if len(indices) and (int(indices.min()) < 0 or int(indices.max()) >= vcount):
                            _fail(errors, f"{path.name}: {mesh.get('name')} índices fora da malha (vertices={vcount})")
                    except Exception as exc:
                        _fail(errors, f"{path.name}: indices inválidos em {mesh.get('name')}: {exc}")
            for ti, target in enumerate(primitive.get("targets", [])):
                for key, accessor_index in target.items():
                    try:
                        values = _accessor(doc, binary, accessor_index)
                        if not np.isfinite(values).all():
                            _fail(errors, f"{path.name}: {mesh.get('name')} morph {ti}/{key} contém NaN/Inf")
                        if "POSITION" in attrs and len(values) != doc["accessors"][attrs["POSITION"]]["count"]:
                            _fail(errors, f"{path.name}: {mesh.get('name')} morph {ti}/{key} count difere da posição")
                    except Exception as exc:
                        _fail(errors, f"{path.name}: morph target {mesh.get('name')} {ti}/{key} inválido: {exc}")
    body_meshes: list[dict[str, Any]] = []
    for mesh_index, mesh in enumerate(meshes):
        mesh_name = str(mesh.get("name", ""))
        if mesh_name != "o_body_a" and not mesh_name.startswith("kk_o_body_a_"):
            continue
        try:
            primitive = mesh["primitives"][0]
            positions = _accessor(doc, binary, primitive["attributes"]["POSITION"]).astype(np.float64)
            body_meshes.append({"nome": mesh_name, "vertices": len(positions), "triangulos": _triangles(mesh, doc),
                                "bounds_min": positions.min(axis=0).tolist(), "bounds_max": positions.max(axis=0).tolist(),
                                "extent": np.ptp(positions, axis=0).tolist()})
        except Exception as exc:
            _fail(errors, f"{path.name}: não foi possível medir a malha corporal {mesh_name}: {exc}")
    summary["geometria"] = {"mesh_nodes": mesh_nodes, "indices": index_total, "pesos_min": weight_min if math.isfinite(weight_min) else None,
                            "pesos_max": weight_max if math.isfinite(weight_max) else None, "soma_pesos_min": sum_min if math.isfinite(sum_min) else None,
                            "soma_pesos_max": sum_max if math.isfinite(sum_max) else None, "joint_index_max": max_joint_index,
                            "morph_targets_total": morph_total, "morphs": target_summary, "malhas_corpo": body_meshes}
    skin_joint_names = [str(nodes[j].get("name", "")) for j in (skin or {}).get("joints", []) if isinstance(j, int) and 0 <= j < len(nodes)]
    summary["ossos"] = {"canonicos_esperados": len(canonical), "canonicos_presentes": len(canonical) - len(missing),
                        "faltantes": missing, "pais_divergentes": parent_mismatch,
                        "nodes_bone_mesh_mesmo_nome": bone_mesh_collisions,
                        "colisoes_nome_mesh_node_permitidas": duplicate_mesh_names,
                        "familias_nos_skin": {prefix: sum(n.startswith(prefix) for n in skin_joint_names)
                                              for prefix in ("cf_j_", "k_f_", "cf_J_", "cf_s_", "cf_d_", "cf_hit_", "a_n_", "cf_pv_", "cf_t_", "cf_O", "cf_n_")},
                        "outros": sum(not n.startswith(("cf_j_", "k_f_", "cf_J_", "cf_s_", "cf_d_", "cf_hit_", "a_n_", "cf_pv_", "cf_t_", "cf_O", "cf_n_")) for n in skin_joint_names)}
    if path.name == "personagem_roupas.glb":
        variants = []
        for name, mesh in mesh_by_name.items():
            if name == "o_body_a" or name.startswith("kk_o_body_a_"):
                index_hashes = []
                for primitive in mesh.get("primitives", []):
                    ix = _accessor(doc, binary, primitive["indices"]).reshape(-1)
                    index_hashes.append(hashlib.sha256(ix.tobytes()).hexdigest())
                node_indices = [i for i, node in enumerate(nodes) if node.get("mesh") == meshes.index(mesh)]
                variants.append({"nome": name, "triangulos": _triangles(mesh, doc), "indices_sha256": index_hashes,
                                 "scene_ativo": any(i in scene_nodes for i in node_indices),
                                 "atributos_reutilizados": bool(mesh.get("primitives") and "POSITION" in mesh["primitives"][0].get("attributes", {}))})
        for variant in variants:
            matching = [other["nome"] for other in variants if other["nome"] != variant["nome"] and variant["indices_sha256"] == other["indices_sha256"]]
            variant["mesmas_faces_que"] = matching
        summary["variantes_corpo"] = variants
        if sum(1 for v in variants if v["scene_ativo"]) > 1:
            summary.setdefault("avisos", []).append("Variantes corporais são alternativas, mas todas estão alcançáveis na cena GLTF padrão; ativar o GLB sem seleção causa superfícies coincidentes.")
    return summary


def audit_folder(folder: pathlib.Path, canonical: list[dict[str, Any]]) -> dict[str, Any]:
    folder = folder.resolve()
    errors: list[str] = []
    card_path = folder / "card.json"
    proportions_path = folder / "proporcoes.json"
    try:
        card = json.loads(card_path.read_text(encoding="utf-8"))
        proportions = json.loads(proportions_path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"card/proporcoes indisponíveis ou inválidos: {type(exc).__name__}: {exc}")
        card, proportions = {}, {}
    glbs = ["personagem.glb", "personagem_idle.glb", "personagem_roupas.glb"]
    reports = [_audit_glb(folder / "saida" / name, canonical, errors) for name in glbs]
    main_glb, idle_glb = reports[:2]
    def morph_signature(report: dict[str, Any]) -> dict[str, tuple[int, str]]:
        return {item["malha"]: (item["targets"], item["nomes_sha256"]) for item in report.get("geometria", {}).get("morphs", [])}
    main_sig, idle_sig = morph_signature(main_glb), morph_signature(idle_glb)
    if main_sig != idle_sig:
        errors.append("personagem.glb e personagem_idle.glb divergem nos canais morph por malha")
    main_joints = main_glb.get("bind", {}).get("joints")
    idle_joints = idle_glb.get("bind", {}).get("joints")
    if main_joints != idle_joints:
        errors.append("personagem.glb e personagem_idle.glb divergem no número de joints")
    body = proportions.get("corpo", {})
    face = proportions.get("rosto", {})
    height = body.get("cf_n_height", {}).get("escala", [])
    result = {"boneca": folder.name, "card": {"sexo": card.get("Parameter", {}).get("sex"), "origem": str(folder.relative_to(ROOT)) if folder.is_relative_to(ROOT) else folder.name},
              "proporcoes": {"ossos_corpo": len(body), "ossos_rosto": len(face), "altura_scale_cf_n_height": height},
              "glbs": reports, "erros": errors, "passou": not errors}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pasta", type=pathlib.Path, help="pasta da boneca (contém card.json e saida/)")
    group.add_argument("--todas", action="store_true", help="audita IDs de bonecas/catalogo.json")
    parser.add_argument("--relatorio", type=pathlib.Path, help="destino do JSON único (somente com --pasta)")
    parser.add_argument("--evidencias", type=pathlib.Path, help="pasta de relatórios individuais (somente com --todas)")
    args = parser.parse_args()
    if args.relatorio is not None and args.todas:
        parser.error("--relatorio só pode ser usado com --pasta")
    if args.evidencias is not None and args.pasta is not None:
        parser.error("--evidencias só pode ser usado com --todas")
    canonical = json.loads(CANONICAL_PATH.read_text(encoding="utf-8"))["nodes"]
    if args.todas:
        folders = [ROOT / "bonecas" / item["id"] for item in json.loads(CATALOG_PATH.read_text(encoding="utf-8"))]
    else:
        folder = args.pasta.expanduser().resolve()
        folders = [folder]
    results = [audit_folder(folder, canonical) for folder in folders]
    for folder, result in zip(folders, results):
        if args.todas:
            out = (args.evidencias.expanduser().resolve() if args.evidencias else REPORT_DIR) / f"{folder.name}.json"
        else:
            out = args.relatorio.expanduser().resolve() if args.relatorio else folder / "saida" / "validacao_corpo.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    payload = {"bonecas": results, "passou": all(result["passou"] for result in results)}
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return 0 if payload["passou"] else 1


if __name__ == "__main__":
    sys.exit(main())
