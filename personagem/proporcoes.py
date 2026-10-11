#!/usr/bin/env python3
"""Avalia tabelas de shape e aritmética de ShapeBody/HeadInfoFemale do jogo.
O pequeno interpretador aceita somente as instruções matemáticas desses métodos.
Não executa DLLs nem escreve no jogo. O resultado são TRS locais por nome de osso.
"""
import os
import json,pathlib,struct,subprocess,sys,numpy as np,UnityPy,dnfile
from carregar import RAIZ
PASTA=pathlib.Path(os.environ.get("BONECA_DIR", str(pathlib.Path(__file__).resolve().parent)))

def curvas(bundle,nome):
 env=UnityPy.load(str(RAIZ/bundle));obj=next(o for o in env.objects if o.type.name=='TextAsset' and o.peek_name()==nome)
 b=obj.read().m_Script.encode('utf8','surrogateescape');p=4;out={}
 for i in range(struct.unpack_from('<i',b)[0]):
  n=b[p];p+=1;name=b[p:p+n].decode();p+=n;z=struct.unpack_from('<i',b,p)[0];p+=4;rows=[]
  for j in range(z):rows.append(struct.unpack_from('<i9f',b,p));p+=40
  out[name]=np.array(rows)
 assert p==len(b)
 return out

def fontes(curves,tabela,valores,nomes):
 src={i:{'vctPos':dict.fromkeys('xyz',0.),'vctRot':dict.fromkeys('xyz',0.),'vctScl':dict.fromkeys('xyz',1.)} for i in nomes}
 ids={v:k for k,v in nomes.items()}
 for linha in tabela.splitlines():
  a=linha.split('\t');idx=int(a[0]);name=a[1];flags=list(map(int,a[2:]));curve=curves[name];frame=valores[idx]*curve[-1,0]
  # Extrapola também valores fora de 0..1 presentes no card.
  k=min(max(int(np.searchsorted(curve[:,0],frame)-1),0),len(curve)-2);f=(frame-curve[k,0])/(curve[k+1,0]-curve[k,0]);v=curve[k,1:]*(1-f)+curve[k+1,1:]*f
  # AnimationKeyInfo.GetInfo usa Mathf.LerpAngle em cada eixo de rotação.
  # Interpolar 0 → 359 como escalares fazia a saia da Rena girar cerca de 82°.
  delta=np.mod(curve[k+1,4:7]-curve[k,4:7],360.0)
  delta=np.where(delta>180.0,delta-360.0,delta)
  v[3:6]=curve[k,4:7]+delta*np.clip(f,0.0,1.0)
  for j,flag in enumerate(flags):
   if flag:src[ids[name]][['vctPos','vctRot','vctScl'][j//3]]['xyz'[j%3]]=float(v[j])
 return src

def avaliar(lines,src,dst):
 self={'dictSrc':src,'dictDst':{k:{'trfBone':v} for k,v in dst.items()},'updateMask':7,'InitEnd':True};stack=[];loc={};resultado={};code=[]
 for l in lines.splitlines():
  a=l.split(' ',2)
  if a[0].isdigit():code.append((int(a[0]),a[1],a[2]))
 pos={o[0]:i for i,o in enumerate(code)};ip=0
 while ip<len(code):
  offset,op,arg=code[ip];ip+=1
  if op=='ldarg.0':stack.append(self)
  elif op=='ldnull':stack.append(None)
  elif op.startswith('ldc.i4.'):
   stack.append(int(arg) if op=='ldc.i4.s' else (-1 if op.endswith('m1') else int(op.rsplit('.',1)[1])))
  elif op=='ldc.r4':stack.append(float(arg))
  elif op in ['ldfld','ldflda']:stack.append(stack.pop()[arg])
  elif op.startswith('ldloca'):stack.append(('local',int(arg[arg.index('0x')+2:-1],16)))
  elif op.startswith('ldloc.'):stack.append(loc[int(op.rsplit('.',1)[1])])
  elif op.startswith('stloc.'):loc[int(op.rsplit('.',1)[1])]=stack.pop()
  elif op in ['add','mul','sub','div','and']:
   b=stack.pop();a=stack.pop();stack.append({'add':lambda:a+b,'mul':lambda:a*b,'sub':lambda:a-b,'div':lambda:a/b,'and':lambda:a&b}[op]())
  elif op=='neg':stack.append(-stack.pop())
  elif op in ['brtrue','brfalse']:
   v=stack.pop()
   if bool(v)==(op=='brtrue'):ip=pos[int(arg)]
  elif op=='br':ip=pos[int(arg)]
  elif op=='bge.un':
   b=stack.pop();a=stack.pop()
   if a>=b:ip=pos[int(arg)]
  elif op in ['call','callvirt']:
   if arg=='get_InitEnd':stack.pop();stack.append(True)
   elif arg=='get_Count':stack.append(len(stack.pop()))
   elif arg=='get_Item':key=stack.pop();d=stack.pop();stack.append(d[key])
   elif arg=='TryGetValue':
    ref=stack.pop();key=stack.pop();d=stack.pop();loc[ref[1]]=d.get(key);stack.append(key in d)
   elif arg.startswith('SetLocal'):
    quantidade=3 if arg in ['SetLocalScale','SetLocalRotation'] else 1;vals=[stack.pop() for _ in range(quantidade)][::-1];bone=stack.pop();out=resultado.setdefault(bone,{})
    if arg=='SetLocalScale':out['escala']=vals
    elif arg=='SetLocalRotation':out['rotacao_graus']=vals
    else:out.setdefault('posicao',{})[arg[-1].lower()]=vals[0]
   else:raise ValueError((offset,op,arg))
  elif op=='ret':break
  else:raise ValueError((offset,op,arg))
 return resultado

def main():
 dll=RAIZ.parent/'Koikatsu Party_Data/Managed/Assembly-CSharp.dll';pe=dnfile.dnPE(str(dll));tab=pe.net.mdtables
 def enum(idx):return {i:str(f.row.Name) for i,f in enumerate(tab.TypeDef.rows[idx-1].FieldList[1:])}
 text=subprocess.check_output([sys.executable,str(pathlib.Path(__file__).resolve().parent/'inspecionar_il.py'),'Update']).decode();card=json.loads((PASTA/'card.json').read_text());tables=UnityPy.load(str(RAIZ/'list/customshape.unity3d'));tables={o.peek_name():o.read().m_Script for o in tables.objects if o.type.name=='TextAsset'}
 resultado={}
 for tipo,classe,srcidx,dstidx,bundle,asset,tabela,key in [('corpo','ShapeBodyInfoFemale',0x426,0x425,'chara/oo_base.unity3d','cf_anmShapeBody','cf_custombody','shapeValueBody'),('rosto','ShapeHeadInfoFemale',0x42c,0x42b,'chara/bo_head_00.unity3d','cf_anmShapeHead_00','cf_customhead','shapeValueFace')]:
  parte=text.split('TYPE '+classe+'\n')[1].split('METHOD Update\n')[1].split('METHOD UpdateAlways')[0]
  src=fontes(curvas(bundle,asset),tables[tabela],card['Custom'][tipo][key],enum(srcidx));resultado[tipo]=avaliar(parte,src,enum(dstidx));print(tipo,len(resultado[tipo]),'ossos personalizados')
 (PASTA/'proporcoes.json').write_text(json.dumps(resultado,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
