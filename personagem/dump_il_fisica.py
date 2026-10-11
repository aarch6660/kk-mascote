#!/usr/bin/env python3
"""Grava um dump IL direcionado do solver Koikatsu para evidência local."""
from __future__ import annotations

import hashlib
import os
import pathlib
import tempfile

import dnfile
from dncil.cil.body import CilMethodBody
from dncil.cil.body.reader import CilMethodBodyReaderBytes

GAME = pathlib.Path(os.environ.get("KK_JOGO") or pathlib.Path.home()/"Downloads/Koikatsu.Party/Koikatsu Party")
DLL = GAME / "Koikatsu Party_Data/Managed/Assembly-CSharp.dll"
OUT = pathlib.Path(__file__).resolve().parents[1] / "mascote/evidencias/corpo-fisica-2026-10-09/dump-dynamicbone-il.txt"
TARGETS = {
    "DynamicBone_Ver02": {"SetupParticles", "AppendParticles", "AppendParticlePtn", "CalcLocalPosition",
                           "setPtn", "PtnBlend",
                           "ApplyParticlesToTransforms", "UpdateParticles1", "UpdateParticles2",
                           "SkipUpdateParticles", "UpdateDynamicBones"},
    "DynamicBone": {"SetupParticles", "AppendParticles", "UpdateDynamicBones", "UpdateParticles1",
                    "UpdateParticles2", "ApplyParticlesToTransforms"},
    "DynamicBone_Ver02::BoneParameter": {".ctor"},
    "DynamicBone_Ver02::ParticlePtn": {".ctor"},
    "DynamicBone_Ver02::Particle": {".ctor"},
    "DynamicBone::Particle": {".ctor"},
    "ChaControl": {"getDynamicBoneBust", "InitDynamicBoneBust", "ReSetupDynamicBoneBust",
                   "UpdateBustSoftnessAndGravity", "ChangeBustSoftness", "UpdateBustSoftness",
                   "ChangeBustGravity", "UpdateBustGravity", "ChangeClothesTopParts",
                   "ChangeClothesBot", "ChangeClothesBra", "ChangeClothesShorts"},
}


def atomic_write(path: pathlib.Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def main() -> None:
    if not DLL.is_file():
        raise SystemExit(f"Assembly-CSharp.dll não encontrado: {DLL}")
    h = hashlib.sha256(DLL.read_bytes()).hexdigest()
    pe = dnfile.dnPE(str(DLL))
    tables = pe.net.mdtables
    names = {}
    method_tokens = {}
    for table, prefix, attr in ((tables.MethodDef, 0x06000000, "Name"),
                                (tables.Field, 0x04000000, "Name"),
                                (tables.TypeDef, 0x02000000, "TypeName"),
                                (tables.MemberRef, 0x0A000000, "Name")):
        for i, row in enumerate(table.rows, 1):
            names[prefix + i] = str(getattr(row, attr))
            if prefix == 0x06000000:
                method_tokens[id(row)] = prefix + i
    nested = {}
    if hasattr(tables, "NestedClass"):
        for row in tables.NestedClass.rows:
            try:
                nested[row.NestedClass.row] = str(row.EnclosingClass.row.TypeName)
            except Exception:
                pass
    out = ["Koikatsu Assembly-CSharp.dll targeted IL dump",
           f"DLL: {DLL}", f"SHA256: {h}",
           "Tokens are resolved to metadata member names where available.",
           "Coordinates and solver behavior are not rewritten here; this is an IL listing.", ""]
    for td in tables.TypeDef.rows:
        type_name = str(td.TypeName)
        parent = nested.get(td)
        qualified = f"{parent}::{type_name}" if parent else type_name
        wanted = TARGETS.get(qualified)
        # Parent type names may be absent from the metadata label for a few rows;
        # retain strict exact matching for the two solver classes.
        if not wanted:
            wanted = TARGETS.get(type_name) if type_name in ("DynamicBone", "DynamicBone_Ver02", "ChaControl") else None
        if not wanted:
            continue
        for method_index in td.MethodList:
            m = method_index.row
            method_name = str(m.Name)
            if method_name not in wanted:
                continue
            out += [f"{'=' * 88}", f"TYPE {qualified}",
                    f"METHOD {method_name} token=0x{method_tokens.get(id(m), 0):08x} RVA=0x{m.Rva:x}"]
            if not m.Rva:
                out.append("<no method body>")
                continue
            body = CilMethodBody(CilMethodBodyReaderBytes(pe.get_data(m.Rva, 100000)))
            for ins in body.instructions:
                operand = ins.operand
                if hasattr(operand, "value"):
                    token = operand.value
                    if token >> 24 == 0x70:
                        try:
                            operand = repr(pe.net.user_strings.get(token & 0xFFFFFF).value)
                        except Exception:
                            operand = f"0x{token:08x}"
                    else:
                        operand = names.get(token, f"0x{token:08x}")
                out.append(f"IL_{ins.offset:04x}: {ins.opcode.name:<16} {operand if operand is not None else ''}")
            out.append("")
    atomic_write(OUT, "\n".join(out))
    print(f"{OUT}\nSHA256(DLL)={h}\nbytes={OUT.stat().st_size}")


if __name__ == "__main__":
    main()
