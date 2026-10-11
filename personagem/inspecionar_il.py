"""Inspeção local de IL do jogo, somente leitura; auxiliar de engenharia reversa."""
import os
import dnfile,pathlib,sys
from dncil.cil.body import CilMethodBody
from dncil.cil.body.reader import CilMethodBodyReaderBytes
p=pathlib.Path(os.environ.get('KK_JOGO') or pathlib.Path.home()/'Downloads/Koikatsu.Party/Koikatsu Party')/'Koikatsu Party_Data/Managed/Assembly-CSharp.dll'
pe=dnfile.dnPE(str(p));tables=pe.net.mdtables
names={0x06000000+i:str(m.Name) for i,m in enumerate(tables.MethodDef.rows,1)}
names.update({0x04000000+i:str(m.Name) for i,m in enumerate(tables.Field.rows,1)})
names.update({0x02000000+i:str(m.TypeName) for i,m in enumerate(tables.TypeDef.rows,1)})
names.update({0x0a000000+i:str(m.Name) for i,m in enumerate(tables.MemberRef.rows,1)})
for t in tables.TypeDef.rows:
 if str(t.TypeName) not in ['ChaControl','ShapeBodyInfoFemale','ShapeHeadInfoFemale','ShapeInfoBase','ShapeInfoBase+ShapeInfo'] and not any(v in str(t.TypeName) for v in ['ChangeHairAsync','ChangeHeadAsync']):continue
 print('TYPE',t.TypeName)
 for mindex in t.MethodList:
  m=mindex.row
  if not any(v.lower() in str(m.Name).lower() for v in sys.argv[1:]):continue
  print('METHOD',m.Name)
  if not m.Rva:continue
  body=CilMethodBody(CilMethodBodyReaderBytes(pe.get_data(m.Rva,100000)))
  for ins in body.instructions:
   v=ins.operand
   if hasattr(v,'value'):
    token=v.value
    if token>>24==0x70:v=repr(pe.net.user_strings.get(token&0xffffff).value)
    else:v=names.get(token,hex(token))
   print(ins.offset,ins.opcode.name,v)
