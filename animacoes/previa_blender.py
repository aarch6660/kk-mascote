"""Reimporta GLBs reais, valida ossos e renderiza amostras com Blender Workbench."""
import bpy,json,pathlib,sys,math
import numpy as np
from mathutils import Vector
HERE=pathlib.Path(__file__).resolve().parent
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
manifest=json.loads((HERE/'exportados/manifesto.json').read_text())
choose=set(args)
reports=[]
for item in manifest:
    if choose and item['name'] not in choose:continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene;scene.render.fps=30
    bpy.ops.import_scene.gltf(filepath=str(HERE/item['glb']),bone_heuristic='TEMPERANCE')
    arm=next(o for o in scene.objects if o.type=='ARMATURE')
    mesh=next(o for o in scene.objects if o.type=='MESH')
    assert len(arm.data.bones)==580,(item['name'],len(arm.data.bones))
    assert arm.animation_data and arm.animation_data.action,item['name']
    action=arm.animation_data.action;start,end=action.frame_range
    print('ANIM',item['name'],start,end,len(arm.data.bones),flush=True)
    samples=[float(start+(end-start)*f) for f in [0,.25,.5,.75]]
    bounds=[];poses=[]
    for f in samples:
        scene.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update()
        dg=bpy.context.evaluated_depsgraph_get();ev=mesh.evaluated_get(dg);me=ev.to_mesh()
        bounds.extend([mesh.matrix_world@v.co for v in me.vertices]);ev.to_mesh_clear()
        poses.append({n:list(arm.matrix_world@arm.pose.bones[n].matrix.translation) for n in ['cf_j_head','cf_j_hips','cf_j_hand_L','cf_j_hand_R','cf_j_foot_L','cf_j_foot_R']})
    xyz=np.array(bounds);lo=xyz.min(axis=0);hi=xyz.max(axis=0);target=Vector((lo+hi)/2)
    camdata=bpy.data.cameras.new('Camera');camdata.type='ORTHO';camdata.ortho_scale=max(1.5,float(max(hi-lo))*1.35)
    cam=bpy.data.objects.new('Camera',camdata);scene.collection.objects.link(cam)
    cam.location=target+Vector((2,-4,1.3));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
    scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=320;scene.render.resolution_y=320;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
    scene.world=bpy.data.worlds.new('World')
    sh=scene.display.shading;sh.light='STUDIO';sh.color_type='VERTEX';sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.background_type='WORLD';scene.world.color=(.035,.045,.06)
    scene.view_settings.view_transform='Standard'
    folder=HERE/'previa'/item['name'];folder.mkdir(parents=True,exist_ok=True)
    for k,f in enumerate(samples):
        scene.frame_set(int(f),subframe=f-int(f));scene.render.filepath=str(folder/f'{k:02}.png');bpy.ops.render.render(write_still=True)
    reports.append(dict(name=item['name'],bones=len(arm.data.bones),frames=[float(start),float(end)],samples=samples,world_positions_blender=poses,bounds=[lo.tolist(),hi.tolist()]))
(HERE/'previa'/'validacao_blender.json').write_text(json.dumps(reports,indent=2))
