"""Extrai DXBC cotidiano para inspecionar com vkd3d-compiler, sem alterar o jogo."""
import sys,json
from pathlib import Path

from carregar import carregar,RAIZ
from UnityPy.export.ShaderConverter import ShaderProgram
from UnityPy.helpers import CompressionHelper
from UnityPy.streams import EndianBinaryReader
out=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).with_name('auditoria_cor')
out.mkdir(parents=True,exist_ok=True)
names={'Shader Forge/create_eye','Shader Forge/main_skin','Shader Forge/main_opaque','Shader Forge/toon_eye_lod0','Shader Forge/main_hair','Shader Forge/create_head','Shader Forge/create_body'}
for o in carregar(RAIZ/'chara/bo_head_00.unity3d',RAIZ/'chara/co_top_00.unity3d').objects:
 if o.type.name!='Shader':continue
 sh=o.read();name=sh.m_ParsedForm.m_Name
 if name not in names:continue
 names.remove(name)
 raw=CompressionHelper.decompress_lz4(bytes(sh.compressedBlob)[sh.offsets[0]:sh.offsets[0]+sh.compressedLengths[0]],sh.decompressedLengths[0])
 program=ShaderProgram(EndianBinaryReader(raw,endian='<'),o.version)
 passes=sh.m_ParsedForm.m_SubShaders[0].m_Passes
 pas=next((p for p in passes if any(n[0]=='_RampG' for n in p.m_NameIndices)),passes[0])
 sub=pas.progFragment.m_SubPrograms[0];data=program.m_SubPrograms[sub.m_BlobIndex].m_ProgramCode
 pos=data.index(b'DXBC');key=name.split('/')[-1]
 (out/(key+'.dxbc')).write_bytes(data[pos:])
 print(key,'names',pas.m_NameIndices,flush=True)
 params={'name':name,'names':pas.m_NameIndices,'buffers':str(sub.m_ConstantBuffers),'textures':str(sub.m_TextureParams),'keywords':program.m_SubPrograms[sub.m_BlobIndex].m_Keywords}
 (out/(key+'.json')).write_text(json.dumps(params,indent=2))
