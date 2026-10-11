#!/usr/bin/env python3
"""Extrai metadados de DynamicBone de bundles Koikatsu explicitamente permitidos.

Somente leitura dos bundles. Saída limitada a bonecas/*/saida/fisica_kk.json e à
pasta de evidências autorizada. Nenhuma busca recursiva de bundles é feita.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import tempfile
from collections import defaultdict

import UnityPy
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
GAME = pathlib.Path(os.environ.get("KK_JOGO") or pathlib.Path.home()/"Downloads/Koikatsu.Party/Koikatsu Party")
CHARA = GAME / "abdata/chara"
DLL = GAME / "Koikatsu Party_Data/Managed/Assembly-CSharp.dll"
AUDITED_DLL_SHA256 = "3bae621468ca2de1b1f4fd428e2819d2835b23b64f0e104b2874d0615b5c5f2d"
EVIDENCE = ROOT / "mascote/evidencias/corpo-fisica-2026-10-09"

# Lista deliberadamente fechada: este script não pode ser usado para abrir h/.
ALLOWED = {
    "oo_base.unity3d",
    "bo_hair_b_00.unity3d", "bo_hair_b_10.unity3d",
    "bo_hair_f_00.unity3d", "bo_hair_f_10.unity3d",
    "bo_hair_s_00.unity3d",
    "co_top_00.unity3d", "co_top_00_01.unity3d", "co_bot_00.unity3d",
    "co_bra_00.unity3d", "co_shorts_00.unity3d", "co_socks_00.unity3d", "co_shoes_00.unity3d",
}
CARDS = {
    "chika-haruno": {"body": (0.04758089780807495, -0.3016130328178406)},
    "sawai-hinata": {"body": (0.6645163297653198, 0.6419352889060974)},
    "mizuno-ayaka": {"body": (0.5, 0.5)},
}


def sha(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def atomic_json(path: pathlib.Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def ptr(v):
    if isinstance(v, dict) and "m_PathID" in v:
        return {"file_id": int(v.get("m_FileID", 0)), "path_id": int(v["m_PathID"])}
    return None


def safe(value):
    if isinstance(value, dict):
        return {str(k): safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [safe(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def clamp01(x):
    return min(1.0, max(0.0, float(x)))


def tree_lerp(samples, u):
    if u < 0.5:
        t = 2.0 * u
        return float(samples[0]) + (float(samples[1]) - float(samples[0])) * t, t
    t = 2.0 * (u - 0.5)
    return float(samples[1]) + (float(samples[2]) - float(samples[1])) * t, t


def bust_overrides(body, dll_sha):
    if dll_sha != AUDITED_DLL_SHA256:
        raise ValueError("Assembly-CSharp.dll difere da versão auditada; refaça a leitura de BustSoft/BustGravity antes de exportar física")
    softness = float(body["bustSoftness"])
    weight = float(body["bustWeight"])
    q = float(body["shapeValueBody"][4])
    u = clamp01(softness * q + 0.01)
    damping, t = tree_lerp((0.2, 0.1, 0.1), u)
    elasticity, _ = tree_lerp((0.2, 0.15, 0.05), u)
    stiffness, _ = tree_lerp((1.0, 0.1, 0.01), u)
    gravity_t = clamp01(weight)
    gravity_y = (0.0 + (-0.005 - 0.0) * gravity_t) * q * softness * 0.5
    return {
        "status": "resolved",
        "bust": {
            "softness_u": u, "tree_lerp_t": t,
            "damping": damping, "elasticity": elasticity, "stiffness": stiffness,
            "gravity_unity": {"x": 0.0, "y": gravity_y, "z": 0.0},
            "pattern_indices": [0], "apply_terminal": True, "apply_to": "bust",
            "source_values_raw": {"bustSoftness": softness, "shapeValueBody_index4": q,
                                  "bustWeight": weight},
        },
        "source": {
            "dll_sha256": dll_sha,
            "evidence": "mascote/evidencias/corpo-fisica-2026-10-09/bust_sliders.json",
            "method_tokens": {
                "BustSoft.ReCalc": "0x06001da8", "BustSoft.TreeLerp": "0x06001da9",
                "BustGravity.ReCalc": "0x06001dac", "DynamicBone_Ver02.setSoftParams": "0x060000fb",
                "DynamicBone_Ver02.setGravity": "0x060000fa",
            },
            "coefficients": {
                "softness_u": "clamp(bustSoftness * shapeValueBody[4] + 0.01, 0, 1)",
                "damping_samples": [0.2, 0.1, 0.1],
                "elasticity_samples": [0.2, 0.15, 0.05],
                "stiffness_samples": [1.0, 0.1, 0.01],
                "tree_lerp": "lerp(s0,s1,2*u) for u<0.5; else lerp(s1,s2,2*(u-0.5))",
                "gravity_y": "lerp(0,-0.005,clamp(bustWeight,0,1))*shapeValueBody[4]*bustSoftness*0.5",
            },
        },
    }


class Bundle:
    def __init__(self, filename: str, fonte=None):
        if fonte is None and (filename not in ALLOWED or "/" in filename or "\\" in filename):
            raise ValueError(f"bundle fora da allowlist: {filename!r}")
        if fonte is None:
            self.path = (CHARA / filename).resolve(strict=True)
            self.path.relative_to(CHARA.resolve(strict=True))
            self.env = UnityPy.load(str(self.path))
        else:
            from mods_corpo import ler_fonte
            self.path = GAME/fonte['arquivo']
            self.env = UnityPy.load(ler_fonte(fonte))
        self.objects = {int(o.path_id): o for o in self.env.objects}
        self.script_names = {}
        for o in self.env.objects:
            if o.type.name == "MonoScript":
                try:
                    self.script_names[int(o.path_id)] = o.read_typetree().get("m_ClassName", "")
                except Exception:
                    pass
        self.go_names = {}
        self.transforms = {}
        self.go_transform = {}
        self.transform_go = {}
        for o in self.env.objects:
            try:
                if o.type.name == "GameObject":
                    self.go_names[int(o.path_id)] = o.read().m_Name
                elif o.type.name == "Transform":
                    d = o.read_typetree()
                    self.transforms[int(o.path_id)] = d
                    gp = ptr(d.get("m_GameObject"))
                    if gp and gp["file_id"] == 0:
                        self.go_transform[gp["path_id"]] = int(o.path_id)
                        self.transform_go[int(o.path_id)] = gp["path_id"]
            except Exception:
                continue
        self.children = defaultdict(list)
        self.parent = {}
        for tid, d in self.transforms.items():
            p = ptr(d.get("m_Father"))
            if p and p["file_id"] == 0 and p["path_id"]:
                self.parent[tid] = p["path_id"]
        for tid, d in self.transforms.items():
            listed = []
            for value in d.get("m_Children", []) or []:
                child = ptr(value)
                if child and child["file_id"] == 0 and child["path_id"] in self.transforms:
                    listed.append(child["path_id"])
            self.children[tid] = listed
        # Defensive fallback for malformed/incomplete m_Children typetrees.
        for tid, parent in self.parent.items():
            if tid not in self.children[parent]:
                self.children[parent].append(tid)
        self._path_cache = {}

    def transform_path(self, tid: int | None):
        if tid is None:
            return None
        if tid in self._path_cache:
            return self._path_cache[tid]
        parts, current, seen = [], tid, set()
        while current and current in self.transforms and current not in seen:
            seen.add(current)
            go = self.transform_go.get(current)
            parts.append(self.go_names.get(go, f"transform:{current}"))
            current = self.parent.get(current)
        result = "/".join(reversed(parts))
        self._path_cache[tid] = result
        return result

    def pptr_name(self, value):
        p = ptr(value)
        if not p or p["file_id"] != 0:
            return {"ref": p, "resolved": False}
        obj = self.objects.get(p["path_id"])
        if not obj:
            return {"ref": p, "resolved": False}
        if obj.type.name == "Transform":
            return {"ref": p, "resolved": True, "path": self.transform_path(p["path_id"]),
                    "name": self.go_names.get(self.transform_go.get(p["path_id"]))}
        if obj.type.name == "GameObject":
            return {"ref": p, "resolved": True, "name": self.go_names.get(p["path_id"])}
        return {"ref": p, "resolved": True, "type": obj.type.name}

    @staticmethod
    def _v3(value, default=(0.0, 0.0, 0.0)):
        if not isinstance(value, dict):
            return np.array(default, dtype=float)
        return np.array([value.get(k, default[i]) for i, k in enumerate(("x", "y", "z"))], dtype=float)

    def world_matrix(self, tid, cache=None):
        cache = cache if cache is not None else {}
        if tid in cache:
            return cache[tid]
        d = self.transforms[tid]
        p = self._v3(d.get("m_LocalPosition"))
        s = self._v3(d.get("m_LocalScale"), (1.0, 1.0, 1.0))
        qd = d.get("m_LocalRotation", {})
        x, y, z, w = (float(qd.get(k, default)) for k, default in zip(("x", "y", "z", "w"), (0, 0, 0, 1)))
        rot = np.array([
            [1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
            [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
            [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)],
        ])
        local = np.eye(4)
        local[:3, :3] = rot @ np.diag(s)
        local[:3, 3] = p
        parent = self.parent.get(tid)
        cache[tid] = self.world_matrix(parent, cache) @ local if parent in self.transforms else local
        return cache[tid]

    def solver_local_position(self, parent_tid, child_tid):
        cache = {}
        parent_world = self.world_matrix(parent_tid, cache)
        child_world = self.world_matrix(child_tid, cache)
        point = np.linalg.inv(parent_world) @ child_world @ np.array([0.0, 0.0, 0.0, 1.0])
        return {"x": float(point[0]), "y": float(point[1]), "z": float(point[2])}

    def components(self):
        for o in self.env.objects:
            if o.type.name != "MonoBehaviour":
                continue
            try:
                d = o.read_typetree()
                s = ptr(d.get("m_Script"))
                cls = self.script_names.get(s["path_id"], "") if s and s["file_id"] == 0 else ""
                if cls not in ("DynamicBone", "DynamicBone_Ver02", "DynamicBoneCollider", "DynamicBoneReferenceCtrl"):
                    continue
                g = ptr(d.get("m_GameObject"))
                goid = g["path_id"] if g and g["file_id"] == 0 else None
                tid = self.go_transform.get(goid)
                yield {"obj": o, "data": d, "class": cls, "go_id": goid,
                       "go_name": self.go_names.get(goid, ""), "transform_id": tid}
            except Exception:
                continue

    def descendant_transform_ids(self, root_tid):
        if not root_tid:
            return set()
        out, stack = set(), [root_tid]
        while stack:
            t = stack.pop()
            if t in out:
                continue
            out.add(t)
            stack.extend(self.children.get(t, ()))
        return out

    def descendant_transforms_ordered(self, root_tid):
        out, seen, stack = [], set(), [root_tid] if root_tid else []
        while stack:
            tid = stack.pop()
            if tid in seen:
                continue
            seen.add(tid)
            out.append(tid)
            stack.extend(reversed(self.children.get(tid, ())))
        return out

    def collider(self, d, pathid):
        go = ptr(d.get("m_GameObject"))
        goid = go["path_id"] if go and go["file_id"] == 0 else None
        tid = self.go_transform.get(goid)
        return {
            "source_path_id": pathid,
            "game_object": self.go_names.get(goid, ""),
            "transform_path": self.transform_path(tid),
            "enabled": bool(d.get("m_Enabled", 0)),
            "center_local_unity": safe(d.get("m_Center")),
            "radius_unity": d.get("m_Radius"), "height_unity": d.get("m_Height"),
            "direction_enum": d.get("m_Direction"), "bound_enum": d.get("m_Bound"),
        }

    def classic_chain(self, d):
        """Resolve DynamicBone's actual traversal, including exclusions/notRolls."""
        root = ptr(d.get("m_Root"))
        if not root or root["file_id"] != 0:
            return {"resolved": False, "reason": "root PPtr unresolved"}
        exclusions = {p["path_id"] for v in (d.get("m_Exclusions", []) or [])
                      if (p := ptr(v)) and p["file_id"] == 0}
        not_rolls = {p["path_id"] for v in (d.get("m_notRolls", []) or [])
                     if (p := ptr(v)) and p["file_id"] == 0}
        particles, bypassed = [], []

        def append(tid, parent_index):
            if tid in exclusions or tid not in self.transforms:
                return
            idx = len(particles)
            particles.append({"particle_index": idx, "parent_index": parent_index,
                              "transform": self.pptr_name({"m_FileID": 0, "m_PathID": tid})})
            direct = self.children.get(tid, [])
            bypass_child = None
            for child in direct:
                if child in exclusions:
                    continue
                if child in not_rolls:
                    bypass_child = child
                    continue
                append(child, idx)
            # IL's notRoll branch bypasses the selected direct child and appends
            # its surviving children beneath the current particle.
            if bypass_child is not None:
                bypassed.append(bypass_child)
                for child in self.children.get(bypass_child, []):
                    if child in exclusions or child in not_rolls:
                        continue
                    append(child, idx)

        append(root["path_id"], -1)
        return {
            "resolved": True,
            "exclusions": [self.pptr_name({"m_FileID": 0, "m_PathID": t}) for t in sorted(exclusions)],
            "not_rolls": [self.pptr_name({"m_FileID": 0, "m_PathID": t}) for t in sorted(not_rolls)],
            "bypassed_not_roll_transforms": [self.pptr_name({"m_FileID": 0, "m_PathID": t}) for t in bypassed],
            "effective_particles": particles,
            "traversal_note": "notRolls child is omitted; its eligible children are appended under current particle (one-level bypass)",
        }

    def dynamic(self, comp, colliders_by_pid):
        d, cls = comp["data"], comp["class"]
        if cls == "DynamicBone_Ver02":
            root = ptr(d.get("Root"))
            root_ref = self.pptr_name(d.get("Root"))
            bones = [ptr(v) for v in d.get("Bones", []) or []]
            patterns = []
            for ptn in d.get("Patterns", []) or []:
                particles = []
                params = ptn.get("Params", []) or []
                for i, par in enumerate(params):
                    transform_id = bones[i]["path_id"] if i < len(bones) and bones[i] and bones[i]["file_id"] == 0 else None
                    transform_data = self.transforms.get(transform_id, {}) if transform_id else {}
                    effective_transform = self.pptr_name({"m_FileID": 0, "m_PathID": transform_id}) if transform_id else None
                    particles.append({
                        "particle_index": i, "parent_index": i - 1,
                        "is_terminal": False,
                        "name": (effective_transform or {}).get("name", par.get("Name")),
                        "transform": effective_transform,
                        "parameter_reference_transform": self.pptr_name(par.get("RefTransform")),
                        "local_position_unity": safe(transform_data.get("m_LocalPosition")),
                        "solver_local_position_unity": (self.solver_local_position(
                            bones[i - 1]["path_id"], transform_id) if i > 0 and transform_id and
                            bones[i - 1] and bones[i - 1]["file_id"] == 0 else None),
                        "solver_local_position_semantics": "CalcLocalPosition(parent.Transform.InverseTransformPoint(child.Position)); parent uses prior effective Bones transform; index 0 has no CalcLocalPosition call",
                        "local_rotation_xyzw": safe(transform_data.get("m_LocalRotation")),
                        "local_scale": safe(transform_data.get("m_LocalScale")),
                        "is_rotation_calc": bool(par.get("IsRotationCalc", 0)),
                        "damping": par.get("Damping"), "elasticity": par.get("Elasticity"),
                        "stiffness": par.get("Stiffness"), "inert": par.get("Inert"),
                        "next_bone_length_scale": par.get("NextBoneLength"),
                        "collision_radius_unity": par.get("CollisionRadius"),
                        "is_move_limit": bool(par.get("IsMoveLimit", 0)),
                        "move_limit_min_local": safe(par.get("MoveLimitMin")),
                        "move_limit_max_local": safe(par.get("MoveLimitMax")),
                        "keep_length_fraction_min": par.get("KeepLengthLimitMin"),
                        "keep_length_fraction_max": par.get("KeepLengthLimitMax"),
                        "is_crush": bool(par.get("IsCrush", 0)),
                        "crush_move_area_min": par.get("CrushMoveAreaMin"),
                        "crush_move_area_max": par.get("CrushMoveAreaMax"),
                        "crush_add_xy_min": par.get("CrushAddXYMin"),
                        "crush_add_xy_max": par.get("CrushAddXYMax"),
                    })
                terminal = {
                    "particle_index": len(particles), "parent_index": len(particles) - 1,
                    "is_terminal": True, "name": "(EndOffset)", "transform": None,
                    "local_position_unity": safe(ptn.get("EndOffset")),
                    "local_rotation_xyzw": None, "local_scale": None,
                    "is_rotation_calc": False,
                    "damping": 0.0, "elasticity": 0.0, "stiffness": 0.0, "inert": 0.0,
                    "parameter_origin": "DynamicBone_Ver02::BoneParameter .ctor defaults copied by AppendParticles",
                    "next_bone_length_scale": 1.0,
                    "collision_radius_unity": 0.0,
                    "is_move_limit": False, "move_limit_min_local": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "move_limit_max_local": {"x": 0.0, "y": 0.0, "z": 0.0}, "keep_length_fraction_min": 0.0,
                    "keep_length_fraction_max": 0.0, "is_crush": False,
                    "crush_move_area_min": 0.0, "crush_move_area_max": 0.0,
                    "crush_add_xy_min": 0.0, "crush_add_xy_max": 0.0,
                }
                particles.append(terminal)
                patterns.append({
                    "name": ptn.get("Name"), "gravity_unity": safe(ptn.get("Gravity")),
                    "terminal_end_offset_local_unity": safe(ptn.get("EndOffset")),
                    "serialized_end_offset_parameters": {
                        "damping": ptn.get("EndOffsetDamping"), "elasticity": ptn.get("EndOffsetElasticity"),
                        "stiffness": ptn.get("EndOffsetStiffness"), "inert": ptn.get("EndOffsetInert"),
                        "effective_use_in_solver": "not proven by current IL trace",
                    },
                    "particles": particles,
                })
            coll = []
            raw_colliders = d.get("Colliders", []) or []
            for c in raw_colliders:
                cp = ptr(c)
                if cp and cp["file_id"] == 0 and cp["path_id"] == 0:
                    continue  # Unity serializa slots vazios como PPtr(0).
                if cp and cp["file_id"] == 0:
                    item = colliders_by_pid.get(cp["path_id"])
                    coll.append(item if item else {"source_path_id": cp["path_id"], "resolved": False})
                else:
                    coll.append({"ref": cp, "resolved": False})
            return {
                "engine_type": cls, "component_path_id": int(comp["obj"].path_id),
                "comment": d.get("Comment"), "component_game_object": comp["go_name"],
                "component_transform_path": self.transform_path(comp["transform_id"]),
                "root_transform": root_ref,
                "root_is_first_bone": bool(root and d.get("Bones") and ptr(d["Bones"][0]) == root),
                "update_rate_hz": d.get("UpdateRate"), "reflect_speed": d.get("ReflectSpeed"),
                "heavy_loop_max_count": d.get("HeavyLoopMaxCount"), "force_unity": safe(d.get("Force")),
                "gravity_unity": safe(d.get("Gravity")), "ptn_no": d.get("PtnNo"),
                "bone_transforms": [self.pptr_name(v) for v in d.get("Bones", []) or []],
                "colliders": coll, "serialized_collider_slots": len(raw_colliders), "patterns": patterns,
                "drag_and_drop_asset_ref": safe(d.get("DragAndDrop")),
            }
        # DynamicBone uses AnimationCurves, exclusions and colliders; do not map it
        # into the Ver02 parameter model.
        fields = ("m_Root", "m_UpdateRate", "m_Damping", "m_DampingDistrib", "m_Elasticity",
                  "m_ElasticityDistrib", "m_Stiffness", "m_StiffnessDistrib", "m_Inert",
                  "m_InertDistrib", "m_Radius", "m_RadiusDistrib", "m_EndLength", "m_EndOffset",
                  "m_Gravity", "m_Force", "m_Colliders", "m_Exclusions", "m_FreezeAxis",
                  "m_DistantDisable", "m_ReferenceObject", "m_DistanceToObject", "m_notRolls")
        raw_colliders = d.get("m_Colliders", []) or []
        return {
            "engine_type": cls, "component_path_id": int(comp["obj"].path_id),
            "component_game_object": comp["go_name"],
            "component_transform_path": self.transform_path(comp["transform_id"]),
            "root_transform": self.pptr_name(d.get("m_Root")),
            "serialized_parameters": {k.removeprefix("m_"): safe(d.get(k)) for k in fields if k in d and k not in ("m_Colliders",)},
            "resolved_exclusions": [self.pptr_name(v) for v in d.get("m_Exclusions", []) or []],
            "resolved_not_rolls": [self.pptr_name(v) for v in d.get("m_notRolls", []) or []],
            "effective_chain": self.classic_chain(d),
            "serialized_collider_slots": len(raw_colliders),
            "colliders": [colliders_by_pid.get(ptr(v)["path_id"], {"ref": ptr(v), "resolved": False})
                          if ptr(v) and ptr(v)["file_id"] == 0 else {"ref": ptr(v), "resolved": False}
                          for v in raw_colliders if not (ptr(v) and ptr(v)["file_id"] == 0 and ptr(v)["path_id"] == 0)],
        }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pasta", type=pathlib.Path, default=ROOT,
                    help="raiz do projeto; deve conter bonecas/ e mascote/evidencias/")
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--boneca", action="append", choices=sorted(CARDS),
                       help="repita para limitar a coleta; padrão: as três bonecas")
    group.add_argument("--boneca-dir", type=pathlib.Path,
                       help="extrai só este diretório com card.json e pecas.json; não atualiza evidências")
    ap.add_argument("--saida-relatorio", type=pathlib.Path,
                    help="padrão: mascote/evidencias/corpo-fisica-2026-10-09/auditoria_fisica_kk.json")
    args = ap.parse_args()
    project = args.pasta.resolve(strict=True)
    if not (project / "bonecas").is_dir():
        raise SystemExit("--pasta precisa ser a raiz kk-mascote com bonecas/")
    if args.boneca_dir:
        if args.saida_relatorio:
            raise SystemExit("--boneca-dir é isolado e não aceita --saida-relatorio")
        card_dirs = [(args.boneca_dir.resolve(strict=True).name, args.boneca_dir.resolve(strict=True))]
    else:
        card_dirs = [(name, project / "bonecas" / name) for name in (args.boneca or sorted(CARDS))]
    dll_path = DLL.resolve(strict=True)
    dll_sha = sha(dll_path)
    bundle_cache = {}

    def get_bundle(filename):
        if filename not in bundle_cache:
            bundle_cache[filename] = Bundle(filename)
        return bundle_cache[filename]

    # Read only the explicit bundle list, never enumerate StreamingAssets or h/.
    common = get_bundle("oo_base.unity3d")
    all_colls = list(common.components())
    colliders_by_pid = {int(c["obj"].path_id): common.collider(c["data"], int(c["obj"].path_id))
                        for c in all_colls if c["class"] == "DynamicBoneCollider"}
    body_phys = [common.dynamic(c, colliders_by_pid) for c in all_colls
                 if c["class"] == "DynamicBone_Ver02"]
    body_root_go = next((gid for gid, name in common.go_names.items() if name == "p_cf_body_bone"), None)
    body_root_tid = common.go_transform.get(body_root_go)
    body_root_descendants = common.descendant_transform_ids(body_root_tid)
    colliders_by_transform = defaultdict(list)
    for c in all_colls:
        if c["class"] == "DynamicBoneCollider" and c["transform_id"] in body_root_descendants:
            colliders_by_transform[c["transform_id"]].append(colliders_by_pid[int(c["obj"].path_id)])
    all_body_colliders = [collider for tid in common.descendant_transforms_ordered(body_root_tid)
                          for collider in colliders_by_transform.get(tid, [])]
    legacy_filtered_body_colliders = [v for v in all_body_colliders
                                      if v["game_object"].lower().startswith(("cf_hit_arm", "cf_hit_spine", "cf_hit_neck",
                                                                              "cf_hit_head", "cf_hit_shoulder"))]
    body_ctrl = [{"component_path_id": int(c["obj"].path_id), "game_object": c["go_name"],
                  "transform_path": common.transform_path(c["transform_id"]), "fields": safe(c["data"])}
                 for c in all_colls if c["class"] == "DynamicBoneReferenceCtrl"]
    report = {"version": 1, "engine": "Koikatsu.DynamicBone", "coordinate_system": "Unity local-space, Unity units",
              "dll": {"path": str(DLL), "sha256": dll_sha}, "bonecas": {}}

    written = []
    for char, card_dir in card_dirs:
        card_dir = card_dir.resolve(strict=True)
        card_file, parts_file = card_dir / "card.json", card_dir / "pecas.json"
        if not card_file.is_file() or not parts_file.is_file():
            raise SystemExit(f"diretório de boneca precisa conter card.json e pecas.json: {card_dir}")
        card, parts_doc = json.loads(card_file.read_text(encoding="utf-8")), json.loads(parts_file.read_text(encoding="utf-8"))
        items = parts_doc.get("pecas", [])
        selected_items = [p for p in items if str(p.get("tipo", "")).startswith(("cabelo_", "roupa_"))
                          and p.get("MainAB", "").startswith("chara/") and p.get("MainData") not in (None, "", "p_dummy")]
        seen, assets = set(), []
        for part in selected_items:
            bundle_name = pathlib.PurePosixPath(part["MainAB"]).name
            if bundle_name not in ALLOWED:
                continue
            bundle = get_bundle(bundle_name)
            prefab_name = part["MainData"]
            root_go = next((gid for gid, name in bundle.go_names.items() if name == prefab_name), None)
            if root_go is None:
                assets.append({"slot": part.get("tipo"), "bundle": bundle_name, "prefab": prefab_name,
                               "resolved": False, "reason": "prefab GameObject não encontrado"})
                continue
            root_tid = bundle.go_transform.get(root_go)
            tids = bundle.descendant_transform_ids(root_tid)
            comps = list(bundle.components())
            collider_map = {int(c["obj"].path_id): bundle.collider(c["data"], int(c["obj"].path_id))
                            for c in comps if c["class"] == "DynamicBoneCollider"}
            dynamics = [bundle.dynamic(c, collider_map) for c in comps
                        if c["class"] in ("DynamicBone", "DynamicBone_Ver02") and c["transform_id"] in tids]
            for c in comps:
                if c["class"] == "DynamicBoneReferenceCtrl" and c["transform_id"] in tids:
                    dynamics.append({"engine_type": "DynamicBoneReferenceCtrl", "component_path_id": int(c["obj"].path_id),
                                     "component_game_object": c["go_name"], "serialized_fields": safe(c["data"])})
            copy_body_colliders = bundle_name.startswith(("co_top_", "co_bot_"))
            runtime_binding = {
                "status": "resolved", "copy_dynamic_bone": copy_body_colliders,
                "applies_to_component_class": "DynamicBone",
                "source": {
                    "method": "ChaControl.LoadCharaFbxDataAsync",
                    "iterator_method": "<LoadCharaFbxDataAsync>c__Iterator13.MoveNext",
                    "dll_sha256": dll_sha,
                    "evidence": "mascote/evidencias/corpo-fisica-2026-10-09/colliders-runtime-il.md",
                },
                "runtime_colliders": all_body_colliders if copy_body_colliders else [],
                "note": ("Every classic DynamicBone receives all colliders under p_cf_body_bone; serialized PPtrs are retained as source data."
                         if copy_body_colliders else "This loader callsite passes copyDynamicBone=false; no body colliders are injected by this flow."),
            }
            for dynamic in dynamics:
                if dynamic.get("engine_type") == "DynamicBone":
                    dynamic["runtime_colliders"] = all_body_colliders if copy_body_colliders else []
                    dynamic["runtime_collider_copy"] = copy_body_colliders
            assets.append({"slot": part.get("tipo"), "bundle": bundle_name, "prefab": prefab_name,
                           "root_transform_path": bundle.transform_path(root_tid), "resolved": True,
                           "dynamic_bones": dynamics, "runtime_collider_binding": runtime_binding})
            seen.add(bundle_name)
        body = card.get("Custom", {}).get("corpo", {})
        selected_body = next((p for p in items if p.get('tipo')=='corpo'),{})
        if selected_body.get('pacote'):
            mod = Bundle(selected_body['MainAB'],selected_body['fonte'])
            root_go = next(gid for gid,name in mod.go_names.items() if name==selected_body['MainData'])
            tids = mod.descendant_transform_ids(mod.go_transform[root_go])
            comps = [c for c in mod.components() if c['transform_id'] in tids]
            collmap = {int(c['obj'].path_id):mod.collider(c['data'],int(c['obj'].path_id)) for c in comps if c['class']=='DynamicBoneCollider'}
            dynamics = [mod.dynamic(c,collmap) for c in comps if c['class']=='DynamicBone']
            assets.append({'slot':'corpo_mod','bundle':selected_body['MainAB'],'prefab':selected_body['MainData'],
                           'resolved':True,'fonte':selected_body['fonte'],'dynamic_bones':dynamics,
                           'runtime_collider_binding':{'status':'serialized','copy_dynamic_bone':False,
                            'note':'BoneImplantProcess conserva os componentes e colliders da subárvore implantada.'}})
        boneca = {
            "version": 1, "engine": "Koikatsu.DynamicBone", "coordenada": parts_doc.get("coordenada", 0),
            "coordinate_system": "Unity local-space, Unity units",
            "card_sources": {"card_json_sha256": sha(card_file), "pecas_json_sha256": sha(parts_file)},
            "card_bust_fields_raw": {"bustSoftness": body.get("bustSoftness"), "bustWeight": body.get("bustWeight"),
                                      "shapeValueBody_index4": (body.get("shapeValueBody") or [None] * 5)[4]},
            "runtime_overrides": bust_overrides(body, dll_sha),
            "source_bundles": {},
            "body_dynamic_bone_ver02": body_phys,
            "body_collider_inventory_unassigned": all_body_colliders,
            "body_collider_inventory_prefix_filtered": legacy_filtered_body_colliders,
            "body_collider_inventory_scope": {"root_transform_path": common.transform_path(body_root_tid),
                                               "selection": "all DynamicBoneCollider components under p_cf_body_bone; no name/anatomy filter"},
            "body_reference_controllers": body_ctrl,
            "selected_parts": assets,
            "limits": ["DynamicBone (classic) serialized curves are retained as raw Unity typetrees; no conversion to Ver02.",
                       "Cross-bundle/external references not present in the serialized component are left unresolved.",
                       "Bust slider formulae and Top/Bot collider copy are resolved for the audited DLL only.",
                       "Clothing-state selection/blending of Ver02 patterns remains unresolved.",
                       "Corpo mod: DynamicBone serializado importado; alterações de plugins durante cenas H não são executadas.",
                       "Overrides externos de DynamicBoneEditor/Pushup ainda precisam de adaptação quando efetivos."],
        }
        for b in sorted({"oo_base.unity3d", *seen}):
            path = (CHARA / b).resolve(strict=True)
            path.relative_to(CHARA.resolve(strict=True))
            boneca["source_bundles"][b] = {"sha256": sha(path), "size_bytes": path.stat().st_size}
        out_file = card_dir / "saida/fisica_kk.json"
        atomic_json(out_file, boneca)
        written.append(str(out_file))
        report["bonecas"][char] = {"saida": str(out_file.relative_to(project)) if out_file.is_relative_to(project) else str(out_file), "sha256": sha(out_file),
                                   "body_dynamic_bone_count": len(body_phys),
                                   "selected_part_dynamic_count": sum(len(a.get("dynamic_bones", [])) for a in assets)}

    if not args.boneca_dir:
        rel_path = args.saida_relatorio or (project / "mascote/evidencias/corpo-fisica-2026-10-09/auditoria_fisica_kk.json")
        atomic_json(rel_path, report)
    print(json.dumps({"generated": written, "manifest": None if args.boneca_dir else str(rel_path),
                      "metadata": report}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
