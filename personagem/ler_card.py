#!/usr/bin/env python3
"""Lê PNG + cabeçalho .NET + blocos MessagePack do card, sem acessar o jogo."""
import os
import json,struct,pathlib,msgpack
PASTA=pathlib.Path(os.environ.get("BONECA_DIR", str(pathlib.Path(__file__).resolve().parent)))

def ler(caminho):
 b=caminho.read_bytes();p=8
 while True:
  n=struct.unpack_from('>I',b,p)[0];t=b[p+4:p+8];p+=n+12
  if t==b'IEND':break
 fim=p; produto=struct.unpack_from('<i',b,p)[0];p+=4
 def texto():
  nonlocal p
  n=0;s=0
  while True:
   v=b[p];p+=1;n|=(v&127)<<s;s+=7
   if v<128:break
  r=b[p:p+n].decode();p+=n;return r
 marca=texto();versao=texto();n=struct.unpack_from('<i',b,p)[0];p+=4+n
 n=struct.unpack_from('<i',b,p)[0];p+=4
 header=msgpack.unpackb(b[p:p+n],raw=False,strict_map_key=False);p+=n
 tamanho=struct.unpack_from('<q',b,p)[0];p+=8;base=p
 resultado={'formato':marca,'versao':versao,'produto':produto,'fim_png':fim,'blocos':header['lstInfo']}
 for info in header['lstInfo']:
  buf=b[base+info['pos']:base+info['pos']+info['size']];nome=info['name']
  if nome=='Custom':
   partes={};q=0
   for tipo in ['rosto','corpo','cabelo']:
    z=struct.unpack_from('<i',buf,q)[0];q+=4;partes[tipo]=msgpack.unpackb(buf[q:q+z],raw=False,strict_map_key=False);q+=z
   resultado[nome]=partes
  elif nome=='Coordinate':
   coords=[]
   for coord in msgpack.unpackb(buf,raw=False,strict_map_key=False):
    q=0;dados={}
    for tipo in ['roupa','acessorios']:
     z=struct.unpack_from('<i',coord,q)[0];q+=4;dados[tipo]=msgpack.unpackb(coord[q:q+z],raw=False,strict_map_key=False);q+=z
    dados['habilitar_maquiagem']=bool(coord[q]);q+=1
    z=struct.unpack_from('<i',coord,q)[0];q+=4;dados['maquiagem']=msgpack.unpackb(coord[q:q+z],raw=False,strict_map_key=False);q+=z
    assert q==len(coord)
    coords.append(dados)
   resultado[nome]=coords
  else:resultado[nome]=msgpack.unpackb(buf,raw=False,strict_map_key=False)
 # ExtendedSave v3 fica no BlockHeader; v2 legado é um trailer KKEx.
 # Não buscar strings arbitrárias dentro do PNG: usar a fronteira dos blocos.
 plugins=resultado.get('KKEx',{}) or {}
 fim_dados=base+tamanho
 if fim_dados>len(b):raise ValueError('Blocos do card truncados')
 if fim_dados<len(b):
  p=fim_dados
  if b[p:p+5]==b'\x04KKEx':
   p+=5
   versao_ext,z=struct.unpack_from('<ii',b,p);p+=8
   if versao_ext!=2 or z<0 or p+z>len(b):raise ValueError('Trailer KKEx inválido')
   plugins=msgpack.unpackb(b[p:p+z],raw=False,strict_map_key=False)
   p+=z
  resultado['trailer_nao_decodificado_bytes']=len(b)-p
 if not isinstance(plugins,dict):raise ValueError('KKEx não contém um mapa de plugins')
 resultado['ExtendedPlugins']=plugins
 resultado['fim_dados']=fim_dados
 return resultado

def legivel(x):
 if isinstance(x,bytes):
  try:return legivel(msgpack.unpackb(x,raw=False,strict_map_key=False))
  except Exception:return {'bytes_hex':x.hex()}
 if isinstance(x,dict):return {str(k):legivel(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [legivel(v) for v in x]
 return x
if __name__=='__main__':
 d=legivel(ler(PASTA/'card.png'));(PASTA/'card.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print('Card decodificado:',d['Parameter'])
