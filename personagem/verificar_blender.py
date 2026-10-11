"""Reabre o GLB, mede o idle e renderiza o piscar com as chaves preservadas."""
import os
import bpy,pathlib,json,numpy as np
from mathutils import Vector
P=pathlib.Path(os.environ.get("BONECA_DIR", str(pathlib.Path(__file__).resolve().parent)));S=P/'saida'
bpy.ops.wm.open_mainfile(filepath=str(S/'personagem.blend'))
scene=bpy.context.scene
scene.camera.location=(0,-4,1.3);scene.camera.rotation_euler=(Vector((0,0,1.3))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.ortho_scale=.62;scene.render.resolution_x=700;scene.render.resolution_y=700
for ob in scene.objects:
 if ob.type=='MESH' and ob.data.shape_keys:
  for key in ob.data.shape_keys.key_blocks:
   if key.name=='piscar':key.value=1
scene.render.filepath=str(S/'previa_piscar.png');bpy.ops.render.render(write_still=True)
# Quatro tempos do mesmo clipe, medidos na geometria já deformada.
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(S/'personagem_idle.glb'),bone_heuristic='TEMPERANCE');scene=bpy.context.scene;arm=next(o for o in scene.objects if o.type=='ARMATURE');frames=[0,18,36,54];result=[]
for f in frames:
 scene.frame_set(f);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
 result.append(dict(quadro=f,mao_esquerda=list(arm.matrix_world@arm.pose.bones['cf_j_hand_L'].matrix.translation),cabeca=list(arm.matrix_world@arm.pose.bones['cf_j_head'].matrix.translation)))
(S/'validacao_idle_quadros.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
assert np.ptp(np.array([x['mao_esquerda'] for x in result]),axis=0).max()>.005
