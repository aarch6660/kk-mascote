#!/usr/bin/env python3
"""Fixtures GLB sintéticas para regressões do validador de rig corporal."""
from __future__ import annotations

import json
import pathlib
import struct
import sys
import tempfile

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from validar_corpo import _audit_glb  # noqa: E402


def write_fixture(path: pathlib.Path, fault: str | None = None) -> None:
    canonical = json.loads((ROOT / "animacoes" / "esqueleto.json").read_text(encoding="utf-8"))["nodes"]
    document: dict = {
        "asset": {"version": "2.0", "generator": "fixture sintética de validação"},
        "scene": 0,
        "scenes": [{"nodes": [i for i, bone in enumerate(canonical) if bone["parent"] < 0]}],
        "nodes": [
            {"name": bone["name"], "translation": [0, 0, 0], "rotation": [0, 0, 0, 1], "scale": [1, 1, 1]}
            for bone in canonical
        ],
        "meshes": [], "skins": [], "bufferViews": [], "accessors": [], "buffers": [],
    }
    for i, bone in enumerate(canonical):
        if bone["parent"] >= 0:
            document["nodes"][bone["parent"]].setdefault("children", []).append(i)
    root_bone = next(i for i, bone in enumerate(canonical) if bone["parent"] < 0)
    binary = bytearray()

    def add_accessor(array: np.ndarray, kind: str, component: int, target: int | None = None) -> int:
        nonlocal binary
        dtype = {5123: "<u2", 5125: "<u4", 5126: "<f4"}[component]
        values = np.asarray(array)
        if kind == "MAT4":
            values = values.reshape(-1, 4, 4).transpose(0, 2, 1).reshape(-1, 16)
        values = np.asarray(values, dtype=dtype)
        while len(binary) % 4:
            binary.append(0)
        view: dict = {"buffer": 0, "byteOffset": len(binary), "byteLength": values.nbytes}
        if target is not None:
            view["target"] = target
        view_index = len(document["bufferViews"])
        document["bufferViews"].append(view)
        binary.extend(values.tobytes())
        accessor: dict = {"bufferView": view_index, "componentType": component,
                          "count": len(values), "type": kind}
        if kind == "VEC3" and target == 34962:
            accessor["min"] = values.min(axis=0).tolist()
            accessor["max"] = values.max(axis=0).tolist()
        index = len(document["accessors"])
        document["accessors"].append(accessor)
        return index

    matrices = np.repeat(np.eye(4, dtype=np.float32)[None, :, :], len(canonical), axis=0)
    if fault == "bind":
        matrices[0, 0, 3] = 0.02
    inverse_binds = add_accessor(matrices, "MAT4", 5126)
    document["skins"] = [{"name": "synthetic", "joints": list(range(len(canonical))),
                          "skeleton": root_bone, "inverseBindMatrices": inverse_binds}]

    positions = add_accessor(np.asarray([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float32), "VEC3", 5126, 34962)
    normals = add_accessor(np.tile([0, 0, 1], (3, 1)), "VEC3", 5126, 34962)
    tangents = add_accessor(np.tile([1, 0, 0, 1], (3, 1)), "VEC4", 5126, 34962)
    uv = add_accessor(np.asarray([[0, 0], [1, 0], [0, 1]], dtype=np.float32), "VEC2", 5126, 34962)
    color = add_accessor(np.ones((3, 4), dtype=np.float32), "VEC4", 5126, 34962)
    joints = add_accessor(np.zeros((3, 4), dtype=np.uint16), "VEC4", 5123, 34962)
    weights_data = np.tile([1, 0, 0, 0], (3, 1)).astype(np.float32)
    if fault == "weights":
        weights_data[1, 0] = 0.7
    weights = add_accessor(weights_data, "VEC4", 5126, 34962)
    index_data = np.asarray([0, 1, 2] if fault != "indices" else [0, 1, 3], dtype=np.uint32)
    indices = add_accessor(index_data, "SCALAR", 5125, 34963)
    mesh_index = len(document["meshes"])
    document["meshes"].append({"name": "fixture_mesh", "primitives": [{
        "attributes": {"POSITION": positions, "NORMAL": normals, "TANGENT": tangents,
                       "TEXCOORD_0": uv, "COLOR_0": color, "JOINTS_0": joints, "WEIGHTS_0": weights},
        "indices": indices,
    }]})
    mesh_node = len(document["nodes"])
    document["nodes"].append({"name": "fixture_mesh_node", "translation": [0, 0, 0], "rotation": [0, 0, 0, 1],
                              "scale": [1, 1, 1], "mesh": mesh_index, "skin": 0})
    document["nodes"][root_bone].setdefault("children", []).append(mesh_node)
    document["buffers"] = [{"byteLength": len(binary)}]
    json_chunk = json.dumps(document, separators=(",", ":")).encode("utf-8")
    json_chunk += b" " * ((-len(json_chunk)) % 4)
    binary.extend(b"\0" * ((-len(binary)) % 4))
    total = 12 + 8 + len(json_chunk) + 8 + len(binary)
    path.write_bytes(struct.pack("<III", 0x46546C67, 2, total)
                     + struct.pack("<II", len(json_chunk), 0x4E4F534A) + json_chunk
                     + struct.pack("<II", len(binary), 0x004E4942) + binary)


def run() -> dict:
    canonical = json.loads((ROOT / "animacoes" / "esqueleto.json").read_text(encoding="utf-8"))["nodes"]
    results = {}
    with tempfile.TemporaryDirectory(prefix="kk-corpo-fixture-") as temp:
        folder = pathlib.Path(temp)
        for fixture, expected in (("ok", None), ("weights", "WEIGHTS_0 soma fora de 1"),
                                  ("indices", "índices fora da malha"), ("bind", "bind residual")):
            path = folder / f"{fixture}.glb"
            write_fixture(path, None if fixture == "ok" else fixture)
            errors: list[str] = []
            _audit_glb(path, canonical, errors)
            if expected is None:
                assert not errors, f"fixture válida rejeitada: {errors}"
            else:
                assert any(expected in error for error in errors), f"fixture {fixture} não detectada: {errors}"
            results[fixture] = {"passou": (not errors) if expected is None else any(expected in error for error in errors),
                                "erros": errors}
    return {"fixtures": results, "passou": all(x["passou"] for x in results.values())}


if __name__ == "__main__":
    resultado = run()
    print(json.dumps(resultado, ensure_ascii=False, separators=(",", ":")))
    raise SystemExit(0 if resultado["passou"] else 1)
