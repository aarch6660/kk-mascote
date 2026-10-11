#!/usr/bin/env python3
"""Extrai a graduação comum das câmeras do editor, sem escrever no jogo.
Lê somente level2 (CustomScene), sharedassets2 e UserData/config/system.xml.
Não varre cenas nem bundles de outros modos.
"""
import os
import hashlib,json,pathlib,struct,xml.etree.ElementTree as ET
import UnityPy
from UnityPy.classes import PPtr
R=pathlib.Path(__file__).resolve().parent.parent
J=pathlib.Path(os.environ.get('KK_JOGO') or pathlib.Path.home()/'Downloads/Koikatsu.Party/Koikatsu Party')
def extrair():
 p=J/'Koikatsu Party_Data';env=UnityPy.load(str(p/'level2'),str(p/'sharedassets2.assets'))
 saida=R/'bonecas/visual_comum';saida.mkdir(exist_ok=True)
 cameras=[]
 for o in env.objects:
  if o.type.name!='MonoBehaviour':continue
  m=o.read(check_read=False)
  if m.m_Script.read().m_ClassName!='AmplifyColorEffect':continue
  b=o.get_raw_data()
  # Layout da DLL AmplifyColor: Tonemapper, Exposure, WhitePoint,
  # ApplyDithering (4 bytes alinhados), QualityLevel, BlendAmount, LutTexture.
  tone,exposure,white,dither,quality,blend=struct.unpack_from('<iffiif',b,32)
  file_id,path_id=struct.unpack_from('<iq',b,56)
  tex=PPtr(m_FileID=file_id,m_PathID=path_id,assetsfile=o.assets_file).read()
  assert tone==0 and exposure==1 and blend==0 and tex.m_Name=='Lut_Amount'
  assert (tex.m_Width,tex.m_Height,tex.m_ColorSpace)==(1024,32,0)
  tex.image.save(saida/'Lut_Amount.png')
  cameras.append({'nome':m.m_GameObject.read().m_Name,'componente_path_id':o.path_id,'lut_path_id':path_id,'tonemapper':tone,'exposure':exposure,'blend':blend,'quality':quality})
 assert {c['nome'] for c in cameras}=={'Camera','CoordinateCamera'}
 config=J/'UserData/config/system.xml';etc=ET.parse(config).getroot().find('Etc')
 shadow=float(etc.findtext('shadowDepth'));ramp=int(etc.findtext('rampId'))
 dados={'lut':'Lut_Amount.png','lut_tamanho':32,'ambiente_kk':[.019,.027,.039,1-shadow],'rampa_global':f'gt_ramp_{ramp:02d}.png','fontes':{str(f.relative_to(J)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [p/'level2',p/'sharedassets2.assets',config]},'cameras':cameras,'observacao':'LUT original, força integral. RGB global linear recuperado do IL. Character.UpdateGlobalShader passa shadowDepth diretamente ao alfa no Unity; a reconstrução de iluminação Godot usa a força complementar 1-shadowDepth, comum a todas as bonecas. Não é equivalência integral da iluminação Unity; sem calibração por boneca.'}
 (saida/'cores_kk.json').write_text(json.dumps(dados,ensure_ascii=False,indent=2)+'\n')
 print('LUT e iluminação comum do editor extraídas.')
if __name__=='__main__':extrair()
