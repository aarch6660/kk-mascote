#!/usr/bin/env python3
"""Audita ExpressionBone e transpila seu LateUpdate, sem executar/escrever no jogo.

A versão instalada cria o componente em ChaControl.InitializeExpression: os alvos
vêm da enum BoneName, não de um MonoBehaviour serializado chamado Expression.
Somente oo_base.unity3d é aberto. A DLL precisa ser a versão auditada.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re

import dnfile
from dncil.cil.body import CilMethodBody
from dncil.cil.body.reader import CilMethodBodyReaderBytes

from auditar_fisica_kk import AUDITED_DLL_SHA256, Bundle, DLL, ROOT, atomic_json, sha
from dump_il_fisica import atomic_write

EVIDENCE = ROOT / "mascote/evidencias/expression-kk"
VIRTUAL = {
    "n_goal_forearm_L": ("cf_j_shoulder_L", [0.0, 0.30000001192092896, 0.0]),
    "n_goal_forearm_R": ("cf_j_shoulder_R", [0.0, 0.30000001192092896, 0.0]),
    "n_leg_goal_L": ("cf_j_waist02", [-0.08299999684095383, 0.4000000059604645, -0.00800000037997961]),
    "n_leg_goal_R": ("cf_j_waist02", [0.08299999684095383, 0.4000000059604645, -0.00800000037997961]),
}


class Assembly:
    def __init__(self):
        if sha(DLL) != AUDITED_DLL_SHA256:
            raise ValueError("DLL diferente da auditada; refaça a auditoria antes de portar ExpressionBone")
        self.pe = dnfile.dnPE(str(DLL))
        self.tables = self.pe.net.mdtables
        self.types = {str(t.TypeName): t for t in self.tables.TypeDef.rows
                      if str(t.TypeName) in ["ExpressionBone", "ConvertRotation", "TransformPositionEx",
                                             "TransformRotationEx", "TransformScaleEx", "ChaControl"]}
        self.names = {}
        for td in self.tables.TypeDef.rows:
            for m in td.MethodList:
                self.names[0x06000000 + m.row_index] = str(td.TypeName) + "::" + str(m.row.Name)
            for f in td.FieldList:
                self.names[0x04000000 + f.row_index] = str(td.TypeName) + "::" + str(f.row.Name)
        for i, m in enumerate(self.tables.MemberRef.rows, 1):
            self.names[0x0A000000 + i] = str(getattr(m.Class.row, "TypeName", "Dictionary")) + "::" + str(m.Name)
        # BoneName é aninhada em ExpressionBone; não confundir enums homônimas.
        td = next(r.NestedClass.row for r in self.tables.NestedClass.rows
                  if r.EnclosingClass.row is self.types["ExpressionBone"] and str(r.NestedClass.row.TypeName) == "BoneName")
        self.bones = [str(f.row.Name) for f in td.FieldList[1:]]

    def method(self, type_name, name):
        mi = next(v for v in self.types[type_name].MethodList if str(v.row.Name) == name)
        m = mi.row
        body = CilMethodBody(CilMethodBodyReaderBytes(self.pe.get_data(m.Rva, 100000)))
        return 0x06000000 + mi.row_index, body.instructions

    def dump(self, type_name, name):
        token, code = self.method(type_name, name)
        lines = [f"TYPE {type_name} METHOD {name} token=0x{token:08x}"]
        for ins in code:
            value = ins.operand
            if hasattr(value, "value"):
                tok = value.value
                value = repr(self.pe.net.user_strings.get(tok & 0xffffff).value) if tok >> 24 == 0x70 else self.names.get(tok, hex(tok))
            lines.append(f"IL_{ins.offset:04x}: {ins.opcode.name:<16} {value if value is not None else ''}")
        return "\n".join(lines)


class Transpiler:
    """Subset fechado do IL aritmético: falha se aparecer uma instrução nova.

    Produz fórmulas GDScript com ifs nativos; nenhum interpretador IL roda por frame.
    A pilha deve estar vazia nas junções e todos os saltos devem ir para a frente.
    """
    def __init__(self, assembly):
        self.assembly = assembly
        _, self.code = assembly.method("ExpressionBone", "LateUpdate")
        self.indices = {ins.offset: i for i, ins in enumerate(self.code)}
        self.stack = []
        self.lines = []
        self.locals = set()
        self.assignments = {}
        self.targets = set()

    def emit(self, line, indent, ins):
        self.lines.append("\t" * indent + line + f" # IL_{ins.offset:04x}")

    def pop(self, n):
        args = self.stack[-n:]
        del self.stack[-n:]
        return args

    def local(self, ins):
        n = ins.operand.index if ins.opcode.name.endswith(".s") else int(ins.opcode.name.rsplit(".", 1)[1])
        self.locals.add(n)
        return f"v{n}"

    def call(self, ins, indent):
        name = self.assembly.names[ins.operand.value]
        method = name.split("::")[-1]
        if method == "get_dictBone":
            self.pop(1)
            self.stack.append("e.ossos")
        elif method == "get_Count":
            self.stack.append(self.pop(1)[0] + ".size()")
        elif method == "get_Item":
            _, index = self.pop(2)
            self.stack.append('e.ossos[%s]' % json.dumps(self.assembly.bones[int(index)]))
        elif method == "op_Implicit":
            self.stack.append("(" + self.pop(1)[0] + " != null)")
        elif method in ["op_Inequality", "op_Equality"]:
            a, b = self.pop(2)
            self.stack.append(f"({a}{'!=' if method == 'op_Inequality' else '=='}{b})")
        elif method in ["get_one", "get_up"]:
            self.stack.append("Vector3.ONE" if method == "get_one" else "Vector3.UP")
        elif method == "get_normalized":
            self.stack.append(self.pop(1)[0] + ".normalized()")
        elif method in ["Abs", "Sin", "Tan", "Sign", "Min", "Max"]:
            args = self.pop(2 if method in ["Min", "Max"] else 1)
            fn = {"Abs":"absf", "Sin":"sin", "Tan":"tan", "Sign":"e.sinal", "Min":"minf", "Max":"maxf"}[method]
            self.stack.append(fn + "(" + ",".join(args) + ")")
        elif method in ["Angle", "op_Multiply", "op_Division"]:
            a, b = self.pop(2)
            self.stack.append(f"e.angulo({a},{b})" if method == "Angle" else f"({a}{'*' if method == 'op_Multiply' else '/'}{b})")
        elif method == "ConvertDegreeFromQuaternion":
            order, q = self.pop(2)
            self.stack.append(f"e.euler({order},{q})")
        elif method == "ConvertDegreeToQuaternion":
            order, x, y, z = self.pop(4)
            self.stack.append(f"e.quaternion({order},Vector3({x},{y},{z}))")
        elif method == "InverseTransformPoint":
            bone, value = self.pop(2)
            self.stack.append(f"{bone}.inverter_ponto({value})")
        elif method == "Translate":
            bone, x, y, z, space = self.pop(5)
            assert space == "1", "Translate deve usar Space.Self"
            self.emit(f"{bone}.transladar(Vector3({x},{y},{z}))", indent, ins)
        elif method.startswith("get_") or method.startswith("set_"):
            field = {"localPosition":"posicao_local", "localRotation":"rotacao_local", "localScale":"escala_local",
                     "position":"posicao", "rotation":"rotacao"}[method[4:]]
            if method.startswith("get_"):
                self.stack.append(self.pop(1)[0] + "." + field)
            else:
                bone, value = self.pop(2)
                self.target(bone)
                self.emit(f"{bone}.{field} = {value}", indent, ins)
        elif method.startswith("SetLocal"):
            single = method[-1] in "XYZ"
            args = self.pop(2 if single else 4)
            bone, values = args[0], args[1:]
            self.target(bone)
            field = "posicao_local" if "Position" in method else ("escala_local" if "Scale" in method else "rotacao_local")
            if field == "rotacao_local":
                assert method == "SetLocalRotationX"
                self.emit(f"{bone}.definir_rotacao_x({values[0]})", indent, ins)
            elif single:
                # Vector3 é valor, não referência: o setter deve receber o vetor completo.
                self.emit(f"{bone}.definir_eixo({json.dumps(field)},{'XYZ'.index(method[-1])},{values[0]})", indent, ins)
            else:
                self.emit(f"{bone}.{field} = Vector3({','.join(values)})", indent, ins)
        else:
            raise ValueError(f"Chamada não suportada: {name}")

    def target(self, bone):
        value = self.assignments.get(bone, bone)
        match = re.fullmatch(r'e.ossos\["(.+)"\]', value)
        if match:
            self.targets.add(match[1])
        else:
            assert value == "e.calculo", value

    def block(self, start, end, indent):
        i = start
        while i < end:
            ins = self.code[i]
            op, arg = ins.opcode.name, ins.operand
            if op == "ldarg.0": self.stack.append("e")
            elif op == "ldnull": self.stack.append("null")
            elif op.startswith("ldc.i4."): self.stack.append(str(arg if op.endswith(".s") else int(op.rsplit(".",1)[1])))
            elif op == "ldc.r4": self.stack.append(repr(arg))
            elif op.startswith("ldloc"): self.stack.append(self.local(ins))
            elif op.startswith("stloc"):
                local, value = self.local(ins), self.pop(1)[0]
                self.assignments[local] = value
                self.emit(f"{local} = {value}", indent, ins)
            elif op == "ldfld":
                field = self.assembly.names[arg.value].split("::")[-1]
                owner = self.pop(1)[0]
                if field.startswith("enable"):
                    value = "e.ligado" if field == "enable" else f'e.habilitados.get("{field[6:]}",true)'
                elif field == "calcTranceform": value = "e.calculo"
                else:
                    assert field in "xyz"
                    value = f"{owner}.{field}"
                self.stack.append(value)
            elif op == "stfld":
                owner, value = self.pop(2)
                field = self.assembly.names[arg.value].split("::")[-1]
                assert field in "xyz"
                self.emit(f"{owner}.{field} = {value}", indent, ins)
            elif op in ["mul", "add", "sub"]:
                a, b = self.pop(2)
                self.stack.append(f"({a}{ {'mul':'*','add':'+','sub':'-'}[op] }{b})")
            elif op == "neg": self.stack.append("(-" + self.pop(1)[0] + ")")
            elif op in ["call", "callvirt"]: self.call(ins, indent)
            elif op == "ret":
                assert not self.stack
                self.emit("return", indent, ins)
            elif op == "br":
                assert not self.stack
                return self.indices[arg]
            elif op in ["brtrue", "brfalse", "bgt.un"]:
                if op == "bgt.un":
                    a, b = self.pop(2)
                    condition = f"{a} <= {b}"
                else:
                    condition = self.pop(1)[0]
                    if op == "brtrue": condition = "not (" + condition + ")"
                assert not self.stack
                target = self.indices[arg]
                assert i < target <= end, (ins.offset, arg, end)
                self.emit(f"if {condition}:", indent, ins)
                join = self.block(i + 1, target, indent + 1)
                if join > target:
                    assert join <= end
                    self.emit("else:", indent, ins)
                    self.block(target, join, indent + 1)
                    i = join
                else:
                    i = target
                continue
            else:
                raise ValueError((ins.offset, op, arg))
            i += 1
        return end

    def generate(self):
        self.block(0, len(self.code), 1)
        declarations = ["\tvar v%d" % n for n in sorted(self.locals)]
        return "\n".join(["extends RefCounted", "# Gerado por personagem/auditar_expression.py; não editar as fórmulas à mão.",
                          f"# Assembly-CSharp.dll SHA256 {AUDITED_DLL_SHA256}",
                          "# ExpressionBone.LateUpdate 0x0600237b. Cada instrução emitida registra o offset IL.",
                          "func aplicar(e) -> void:"] + declarations + self.lines) + "\n"


def audit():
    assembly = Assembly()
    compiler = Transpiler(assembly)
    source = compiler.generate()
    bundle = Bundle("oo_base.unity3d")
    root = next(tid for tid, go in bundle.transform_go.items() if bundle.go_names[go] == "p_cf_body_00")
    subtree = bundle.descendant_transform_ids(root)
    names = {bundle.go_names[bundle.transform_go[tid]]: tid for tid in subtree}
    references = []
    for i, name in enumerate(assembly.bones):
        if name in VIRTUAL:
            parent, position = VIRTUAL[name]
            references.append({"index":i, "name":name, "virtual":True, "parent":parent, "local_position_unity":position})
        elif name in names:
            tid = names[name]
            tree = bundle.transforms[tid]
            references.append({"index":i, "name":name, "virtual":False, "source_path_id":tid,
                               "path":bundle.transform_path(tid), "local_position_unity":tree["m_LocalPosition"],
                               "local_rotation_xyzw":tree["m_LocalRotation"], "local_scale":tree["m_LocalScale"]})
        else:
            raise ValueError("Referência ausente do prefab: " + name)
    data = {"version":1, "component":"ExpressionBone", "source":{"bundle":str(bundle.path), "bundle_sha256":sha(bundle.path),
            "prefab":"p_cf_body_00", "dll":str(DLL), "dll_sha256":AUDITED_DLL_SHA256},
            "methods":{"initialize_component":"0x06001cfd", "initialize_targets":"0x06002377", "late_update":"0x0600237b",
                       "euler_to_quaternion":"0x06004744", "quaternion_to_euler":"0x06004745", "matrix_to_euler":"0x06004747"},
            "semantics":{"coordinates":"Unity original; Godot espelha X, sem conversão de unidade",
                         "targets_origin":"enum ExpressionBone.BoneName; componente adicionado em InitializeExpression",
                         "rotation_orders":{"3":"YZX", "4":"ZXY", "5":"ZYX"}, "restore":"Propriedades auxiliares voltam à animação antes de cada avaliação"},
            "references":references, "targets":sorted(compiler.targets), "formula_sha256":hashlib.sha256(source.encode()).hexdigest()}
    methods = [("ChaControl","InitializeExpression"),("ExpressionBone","Initialize"),("ExpressionBone","LateUpdate"),
               ("ConvertRotation","ConvertDegreeToQuaternion"),("ConvertRotation","ConvertDegreeFromQuaternion"),
               ("ConvertRotation","ConvertRadianFromMatrix"),("ConvertRotation","CheckNaN"),
               ("TransformRotationEx","SetLocalRotationX")]
    dump = f"DLL {DLL}\nSHA256 {AUDITED_DLL_SHA256}\n\n" + "\n\n".join(assembly.dump(*m) for m in methods)
    return data, source, dump


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boneca-dir", type=pathlib.Path)
    parser.add_argument("--verificar", action="store_true", help="Confere saídas existentes, sem reescrever")
    args = parser.parse_args()
    data, source, dump = audit()
    if args.boneca_dir:
        (args.boneca_dir/"saida").resolve().relative_to((ROOT/"bonecas").resolve())
    paths = [(args.boneca_dir / "saida/expression_kk.json")] if args.boneca_dir else [p.parent / "expression_kk.json" for p in sorted((ROOT/"bonecas").rglob("fisica_kk.json"))]
    formula = ROOT / "mascote/expression_kk_formula.gd"
    if args.verificar:
        assert formula.read_text() == source, "Fórmula diverge do IL"
        for path in paths: assert json.loads(path.read_text()) == data, f"Dados divergentes: {path}"
    else:
        for path in paths: atomic_json(path, data)
        atomic_write(formula, source)
        atomic_write(EVIDENCE/"expression-auditado-il.txt", dump)
    print(json.dumps({"passou":True,"referencias":len(data["references"]),"alvos":len(data["targets"]),"saidas":len(paths)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
