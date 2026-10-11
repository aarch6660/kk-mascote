#!/usr/bin/env python3
"""Oracle independente: executa IL aritmético original sobre as poses do ensaio.

Não carrega/executa a DLL como programa. Interpreta só métodos auditados e
operações matemáticas/Transform explicitamente permitidas, em dados isolados.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "personagem"))
from auditar_expression import Assembly, VIRTUAL

OUT = ROOT / "mascote/evidencias/expression-kk"


def multiply(a, b):
    x, y, z, w = a
    X, Y, Z, W = b
    return np.array([w*X+x*W+y*Z-z*Y, w*Y-x*Z+y*W+z*X,
                     w*Z+x*Y-y*X+z*W, w*W-x*X-y*Y-z*Z])


def matrix(q):
    x, y, z, w = q / np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])


def inverse(q):
    return q * np.array([-1, -1, -1, 1]) / np.dot(q, q)


def unity_euler(q):
    # Quaternion.eulerAngles, nativo externo: Euler do Unity Y*X*Z.
    m = matrix(q)
    x = math.asin(np.clip(-m[1, 2], -1, 1))
    if abs(m[1, 2]) < 0.999999:
        y, z = math.atan2(m[0, 2], m[2, 2]), math.atan2(m[1, 0], m[1, 1])
    else:
        y, z = math.atan2(-m[2, 0], m[0, 0]), 0.0
    return np.degrees([x, y, z])


class Transform:
    def __init__(self, p=None, q=None, s=None, parent=None):
        self.p = np.array(p if p is not None else [0., 0., 0.])
        self.q = np.array(q if q is not None else [0., 0., 0., 1.])
        self.s = np.array(s if s is not None else [1., 1., 1.])
        self.parent = parent

    def world(self):
        m = np.eye(4)
        m[:3, :3] = matrix(self.q) @ np.diag(self.s)
        m[:3, 3] = self.p
        return self.parent.world() @ m if self.parent else m

    def rotation(self):
        return multiply(self.parent.rotation(), self.q) if self.parent else self.q.copy()

    def get(self, name):
        if name == "localPosition": return self.p.copy()
        if name == "localRotation": return self.q.copy()
        if name == "localScale": return self.s.copy()
        if name == "position": return self.world()[:3, 3]
        if name == "rotation": return self.rotation()
        raise ValueError(name)

    def set(self, name, value):
        if name == "localPosition": self.p = np.array(value)
        elif name == "localRotation": self.q = np.array(value)
        elif name == "localScale": self.s = np.array(value)
        elif name == "position": self.p = (np.linalg.inv(self.parent.world()) @ np.r_[value, 1])[:3] if self.parent else np.array(value)
        elif name == "rotation": self.q = multiply(inverse(self.parent.rotation()), value) if self.parent else np.array(value)
        else: raise ValueError(name)

    def inverse_point(self, v):
        return (np.linalg.inv(self.world()) @ np.r_[v, 1])[:3]


class Ref:
    def __init__(self, container, key): self.container, self.key = container, key
    def get(self): return self.container[self.key]
    def set(self, value): self.container[self.key] = value


def deref(value): return value.get() if isinstance(value, Ref) else value
def clone(value): return value.copy() if isinstance(value, np.ndarray) else value


class Oracle:
    def __init__(self, assembly):
        self.assembly = assembly
        self.methods = {}
        for ty, method in [("ExpressionBone","LateUpdate"),("ConvertRotation","ConvertDegreeToQuaternion"),
                           ("ConvertRotation","ConvertDegreeFromQuaternion"),("ConvertRotation","ConvertRadianFromQuaternion"),
                           ("ConvertRotation","ConvertRadianFromMatrix"),("ConvertRotation","CheckNaN")]:
            _, self.methods[ty+"::"+method] = assembly.method(ty,method)

    def call(self, name, stack):
        method = name.split("::")[-1]
        def pop(n):
            values = stack[-n:]
            del stack[-n:]
            return values
        if name in self.methods:
            n = {"ConvertDegreeToQuaternion":4,"ConvertDegreeFromQuaternion":2,"ConvertRadianFromQuaternion":2,
                 "ConvertRadianFromMatrix":2,"CheckNaN":2}[method]
            value = self.run(name, pop(n))
            if method != "CheckNaN": stack.append(value)
        elif method == "get_dictBone": stack.append(pop(1)[0]["dictBone"])
        elif method == "get_Count": stack.append(len(pop(1)[0]))
        elif method == "get_Item":
            d, key = pop(2); stack.append(d[key])
        elif method in ["op_Implicit","op_Inequality","op_Equality"]:
            if method == "op_Implicit": stack.append(pop(1)[0] is not None)
            else:
                a, b = pop(2); stack.append((a is not b) if method == "op_Inequality" else (a is b))
        elif method in ["get_one","get_zero","get_up","get_right","get_forward","get_identity"]:
            stack.append(np.array({"get_one":[1.,1.,1.],"get_zero":[0.,0.,0.],"get_up":[0.,1.,0.],
                                   "get_right":[1.,0.,0.],"get_forward":[0.,0.,1.],"get_identity":[0.,0.,0.,1.]}[method]))
        elif method == "get_normalized":
            v = deref(pop(1)[0]); n = np.linalg.norm(v); stack.append(v/n if n > 0 else np.zeros(3))
        elif method == "Angle":
            a, b = pop(2); den = np.linalg.norm(a)*np.linalg.norm(b)
            stack.append(math.degrees(math.acos(np.clip(np.dot(a,b)/den,-1,1))) if den > 1e-15 else 0.)
        elif method in ["Abs","Sin","Tan","Sign","Asin","IsNaN"]:
            v = pop(1)[0]
            stack.append({"Abs":abs,"Sin":math.sin,"Tan":math.tan,"Sign":lambda x:1. if x>=0 else -1.,
                          "Asin":math.asin,"IsNaN":math.isnan}[method](v))
        elif method in ["Min","Max","Atan2","Clamp"]:
            args = pop(3 if method == "Clamp" else 2)
            stack.append({"Min":min,"Max":max,"Atan2":math.atan2,"Clamp":lambda x,a,b:np.clip(x,a,b)}[method](*args))
        elif method == "op_Multiply":
            a, b = pop(2)
            stack.append(multiply(a,b) if isinstance(a,np.ndarray) and len(a)==4 and isinstance(b,np.ndarray) else a*b)
        elif method == "op_Division":
            a, b = pop(2); stack.append(a/b)
        elif method == "AngleAxis":
            angle, axis = pop(2); half = math.radians(angle)/2
            stack.append(np.r_[axis*math.sin(half), math.cos(half)])
        elif method == "TRS":
            p, q, s = pop(3); stack.append(Transform(p,q,s).world())
        elif method == ".ctor": stack.append(np.array(pop(3)))
        elif method == "InverseTransformPoint":
            t, v = pop(2); stack.append(t.inverse_point(v))
        elif method == "Translate":
            t,x,y,z,space = pop(5); assert space==1
            t.set("position",t.get("position")+matrix(t.rotation())@np.array([x,y,z]))
        elif method.startswith("get_"): stack.append(pop(1)[0].get(method[4:]))
        elif method.startswith("set_"):
            t,v = pop(2);t.set(method[4:],v)
        elif method == "SetLocalRotationX":
            t,x = pop(2);v = unity_euler(t.q);v[0]=x
            qs = [np.r_[np.eye(3)[i]*math.sin(math.radians(v[i])/2),math.cos(math.radians(v[i])/2)] for i in range(3)]
            t.q = multiply(multiply(qs[1],qs[0]),qs[2])
        elif method.startswith("SetLocal"):
            single = method[-1] in "XYZ"
            args = pop(2 if single else 4);t = args[0]
            field = "localPosition" if "Position" in method else "localScale"
            if single:
                v = t.get(field);v["XYZ".index(method[-1])] = args[1]
            else:v=np.array(args[1:])
            t.set(field,v)
        else: raise ValueError(name)

    def run(self, name, args):
        code = self.methods[name]
        indices = {ins.offset:i for i,ins in enumerate(code)}
        stack, locals_ = [], {}
        i = 0
        while i < len(code):
            ins = code[i];i+=1
            op, arg = ins.opcode.name, ins.operand
            if op.startswith(("ldloc", "stloc")):
                n = arg.index if op.endswith(".s") else int(op.rsplit(".",1)[1])
                if op.startswith("ldloca"): stack.append(Ref(locals_,n))
                elif op.startswith("ldloc"): stack.append(clone(locals_[n]))
                else: locals_[n] = clone(stack.pop())
            elif op.startswith("ldarg"):
                n = arg.index if op.endswith(".s") else int(op.rsplit(".",1)[1])
                stack.append(Ref(args,n) if op.startswith("ldarga") else clone(args[n]))
            elif op == "ldnull": stack.append(None)
            elif op == "ldc.r4": stack.append(arg)
            elif op.startswith("ldc.i4."): stack.append(arg if op.endswith(".s") else int(op.rsplit(".",1)[1]))
            elif op in ["ldfld", "stfld"]:
                field = self.assembly.names[arg.value].split("::")[-1] if arg.value in self.assembly.names else str(self.assembly.tables.MemberRef.rows[(arg.value&0xffffff)-1].Name)
                value = stack.pop() if op=="stfld" else None
                owner = deref(stack.pop())
                if field in "xyz":
                    if op=="stfld": owner["xyz".index(field)] = value
                    else:stack.append(owner["xyz".index(field)])
                elif field.startswith("m") and len(field)==3 and field[1:].isdigit():stack.append(owner[int(field[1]),int(field[2])])
                elif field.startswith("enable"):stack.append(True)
                else:stack.append(owner[field])
            elif op == "ldind.r4":stack.append(deref(stack.pop()))
            elif op == "stind.r4":
                value=stack.pop();stack.pop().set(value)
            elif op in ["add","sub","mul"]:
                b=stack.pop();a=stack.pop();stack.append({"add":lambda:a+b,"sub":lambda:a-b,"mul":lambda:a*b}[op]())
            elif op == "neg":stack.append(-stack.pop())
            elif op in ["call","callvirt","newobj"]:self.call(self.assembly.names[arg.value],stack)
            elif op == "switch":
                value=stack.pop()
                if 0<=value<len(arg):i=indices[arg[value]]
            elif op == "br":i=indices[arg]
            elif op in ["brtrue","brfalse"]:
                value=stack.pop()
                if bool(value)==(op=="brtrue"):i=indices[arg]
            elif op in ["bgt.un","ble.un"]:
                b=stack.pop();a=stack.pop()
                if (a>b if op=="bgt.un" else a<=b):i=indices[arg]
            elif op == "ret":return stack.pop() if stack else None
            else:raise ValueError((name,ins.offset,op,arg))


def main():
    assembly=Assembly();oracle=Oracle(assembly)
    samples=json.loads((OUT/"amostras.json").read_text())
    data=json.loads((ROOT/"bonecas/chika-haruno/saida/expression_kk.json").read_text())
    assert data["formula_sha256"]==hashlib.sha256((ROOT/"mascote/expression_kk_formula.gd").read_bytes()).hexdigest()
    errors=[];cases=0;maximum={"position":0.,"scale":0.,"rotation_matrix":0.}
    for sample in samples:
        transforms={name:Transform(np.array(v["p"])*[-1,1,1],np.array(v["q"])*[1,-1,-1,1],v["s"]) for name,v in sample["entrada"].items()}
        for name,v in sample["entrada"].items(): transforms[name].parent=transforms.get(v["parent"])
        for name,(parent,position) in VIRTUAL.items():transforms[name]=Transform(position,parent=transforms[parent])
        state={"dictBone":{i:transforms[n] for i,n in enumerate(assembly.bones)},"calcTranceform":Transform()}
        oracle.run("ExpressionBone::LateUpdate",[state])
        for name,v in sample["saida"].items():
            t=transforms[name]
            differences={"position":float(np.max(np.abs(t.p-np.array(v["p"])*[-1,1,1]))),
                         "scale":float(np.max(np.abs(t.s-v["s"]))),
                         "rotation_matrix":float(np.max(np.abs(matrix(t.q)-matrix(np.array(v["q"])*[1,-1,-1,1]))))}
            for key,value in differences.items():
                cases+=1;maximum[key]=max(maximum[key],value)
                if value > (0.0001 if key=="rotation_matrix" else 0.00001):
                    errors.append(f"{sample['boneca']}/{sample['coordenada']}/{sample['clipe']}/{name}: {key}={value}")
    result={"passou":not errors,"casos":cases,"amostras":len(samples),"desvio_maximo":maximum,"erros":errors[:40],"fonte":"IL original ExpressionBone + ConvertRotation, interpretado independentemente do GDScript"}
    (OUT/"oracle-il.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(result,ensure_ascii=False));assert not errors


if __name__=="__main__":main()
