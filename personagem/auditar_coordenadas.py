#!/usr/bin/env python3
"""Confirma a enumeração de roupas na DLL local, somente leitura."""
import os
import hashlib
import json
from pathlib import Path
import struct

import dnfile

DLL = Path(os.environ.get('KK_JOGO') or Path.home()/'Downloads/Koikatsu.Party/Koikatsu Party')/'Koikatsu Party_Data/Managed/Assembly-CSharp.dll'
OUT = Path(__file__).resolve().parent / 'auditoria_coordenadas.json'


def auditar():
    pe = dnfile.dnPE(str(DLL))
    tables = pe.net.mdtables
    enum = next(t for t in tables.TypeDef.rows if str(t.TypeName) == 'CoordinateType')
    parent = next(n.EnclosingClass.row for n in tables.NestedClass.rows if n.NestedClass.row is enum)
    assert str(parent.TypeName) == 'ChaFileDefine'
    campos = {}
    for campo in enum.FieldList:
        constante = next((c for c in tables.Constant.rows if c.Parent.row is campo.row), None)
        if constante:
            campos[str(campo.row.Name)] = struct.unpack('<i', constante.Value.value)[0]
    assert campos == dict(School01=0, School02=1, Gym=2, Swim=3, Club=4, Plain=5, Pajamas=6)
    return dict(fonte=str(DLL), sha256=hashlib.sha256(DLL.read_bytes()).hexdigest(),
                tipo='ChaFileDefine.CoordinateType', token='0x%08x' % (0x02000000 + tables.TypeDef.rows.index(enum) + 1),
                valores=campos)


if __name__ == '__main__':
    dados = auditar()
    OUT.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dados, ensure_ascii=False))
