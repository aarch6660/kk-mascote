"""Monta as peças no Blender e grava GLB com TRS originais, sem reorientar ossos.
O escritor glTF direto evita a mudança de eixos dos edit bones pelo exportador.
Uso: blender -b -t 4 -P personagem/montar_blender.py
"""
import os
import bpy,json,pathlib,sys,math,struct,copy,numpy as np
from mathutils import Matrix,Vector,Euler
P=pathlib.Path(os.environ.get("BONECA_DIR", str(pathlib.Path(__file__).resolve().parent)));T=P/'trabalho';S=P/'saida';S.mkdir(exist_ok=True)
cena=json.loads((T/'cena.json').read_text());prop=json.loads((P/'proporcoes.json').read_text());card=json.loads((P/'card.json').read_text());mats=json.loads((T/'materiais.json').read_text())
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent/'animacoes'));from glb import converted_nodes
orig=json.loads((pathlib.Path(__file__).resolve().parent.parent/'animacoes/esqueleto.json').read_text())['nodes'];gn,worldbase=converted_nodes(orig)
# Hierarquia canônica inteira (580 nós), seguida dos ossos exclusivos das peças.
nodes=[];parents=[];baseworld={};world={};byn={}
def decompor(M):
 l,r,s=Matrix(M.tolist()).decompose();return dict(translation=list(l),rotation=[r.x,r.y,r.z,r.w],scale=list(s))
def personalizar(L,n,tipo):
 v=prop.get(tipo,{}).get(n)
 if not v:return L
 tr=decompor(L);pos=np.array(tr['translation']);sc=np.array(tr['scale']);rot=Matrix(L.tolist()).to_quaternion()
 for a,x in v.get('posicao',{}).items():pos['xyz'.index(a)]=x*(-1 if a=='x' else 1)
 if 'escala' in v:sc=np.array(v['escala'])
 if 'rotacao_graus' in v:
  # Euler Unity ZXY, espelhado em X para glTF destro.
  e=v['rotacao_graus'];rot=Euler(tuple(math.radians(x) for x in [e[0],-e[1],-e[2]]),'ZXY').to_quaternion()
 return np.array(Matrix.LocRotScale(Vector(pos),rot,Vector(sc)))
def add(n,p,L,tipo):
 if n in byn:return
 idx=len(nodes);byn[n]=idx;parents.append(p);Lp=personalizar(L,n,tipo);nodes.append(dict(name=n,**decompor(Lp)))
 world[n]=(world[p]@Lp if p else Lp)
 if p:nodes[byn[p]].setdefault('children',[]).append(idx)
for i,n in enumerate(orig):
 name=n['name'];pa=orig[n['parent']]['name'] if n['parent']>=0 else None;baseworld[name]=worldbase[i];L=np.linalg.inv(baseworld[pa])@baseworld[name] if pa else baseworld[name];add(name,pa,L,'corpo')
for p in cena['pecas']:
 tipo=p['selecao']['tipo'];pref=p['prefab'];p['_orig']={h['nome']:np.array(h['mundo']) for h in p['hierarquia']};pa='cf_s_head' if tipo=='cabeca' else ('cf_J_FaceUp_tz' if tipo.startswith('cabelo') else 'p_cf_body_bone')
 if tipo.startswith('acessorio_'):
  cfg=p['selecao']['config'];pa=cfg['parentKey'] or p['selecao']['Parent']
  if pa=='none':pa='p_cf_body_bone'
  if pa not in world:raise ValueError('Parent de acessório não encontrado: '+pa)
 p['_base']=world[pa] if tipo in ['cabeca'] or tipo.startswith('cabelo') else np.eye(4)
 implantes={i['origem']:i['destino'] for i in p.get('implantes',[])}
 for h in p['hierarquia']:
  n=h['nome'];hp=h['pai'];L=np.linalg.inv(p['_orig'][hp])@p['_orig'][n] if hp else p['_orig'][n]
  if n in implantes:hp=implantes[n]
  if hp is None:
   hp=pa
   if tipo.startswith('cabelo'):
    cfg=p['selecao']['config'];L=np.array(Matrix.LocRotScale(Vector((-cfg['pos'][0],cfg['pos'][1],cfg['pos'][2])),Euler(tuple(math.radians(x) for x in cfg['rot']),'ZXY').to_quaternion(),Vector(cfg['scl'])))@L
  if tipo.startswith('acessorio_'):
   original=h['original']
   move=0 if original=='N_move' else (1 if original=='N_move2' else None)
   if move is not None:
    valores=cfg['addMove'][2];pos,rot,scl=valores[move*3:move*3+3]
    if p['selecao'].get('HideHair')=='1':pos,rot,scl=[0,0,0],[0,0,0],[1,1,1]
    # IL UpdateAccessoryMoveFromInfo: posição em centímetros; Euler Unity ZXY.
    L=np.array(Matrix.LocRotScale(Vector((-pos[0]*.01,pos[1]*.01,pos[2]*.01)),Euler(tuple(math.radians(x) for x in (rot[0],-rot[1],-rot[2])),'ZXY').to_quaternion(),Vector(scl)))
  add(n,hp,L,'rosto'  if tipo=='cabeca' else 'corpo')
# Escritor glTF: posições em mundo Y-up, inverse bind exatos, morph targets originais.
doc=dict(asset=dict(version='2.0',generator='KK card → UnityPy → Blender, exportador TRS fiel'),scene=0,scenes=[dict(name=card['Parameter'].get('firstname','Boneca'),nodes=[0])],nodes=nodes,bufferViews=[],accessors=[],buffers=[],meshes=[],materials=[],textures=[],images=[],samplers=[dict(magFilter=9729,minFilter=9987,wrapS=10497,wrapT=10497)],skins=[],extensionsUsed=['KHR_materials_unlit'])
buf=bytearray()
def view(raw,target=None):
 while len(buf)%4:buf.append(0)
 d=dict(buffer=0,byteOffset=len(buf),byteLength=len(raw));buf.extend(raw)
 if target:d['target']=target
 idx=len(doc['bufferViews']);doc['bufferViews'].append(d);return idx

def acc(a,typ,component=5126,target=None):
 a=np.asarray(a,dtype={5126:'<f4',5123:'<u2',5125:'<u4'}[component]);d=dict(bufferView=view(a.tobytes(),target),componentType=component,count=a.size if typ=='SCALAR' else len(a),type=typ)
 if typ=='VEC3':d.update(min=a.min(0).tolist(),max=a.max(0).tolist())
 idx=len(doc['accessors']);doc['accessors'].append(d);return idx
matids={}
def material(tipo,m):
 key=tipo+'__'+m['nome']
 if key in matids:return matids[key]
 raw=(S/'texturas'/mats[key]).read_bytes();ii=len(doc['images']);doc['images'].append(dict(name=key,mimeType='image/png',bufferView=view(raw)));ti=len(doc['textures']);doc['textures'].append(dict(source=ii,sampler=0))
 d=dict(name=key,pbrMetallicRoughness=dict(baseColorTexture=dict(index=ti),metallicFactor=0,roughnessFactor=1),extensions={'KHR_materials_unlit':{}},doubleSided=True)
 if any(s in m['nome'] for s in ['mayuge','eyeline','noseline','hitomi_00']):d.update(alphaMode='BLEND')
 idx=len(doc['materials']);doc['materials'].append(d);matids[key]=idx;return idx
jointnames=list(byn);jointids={n:i for i,n in enumerate(jointnames)};ibm=np.array([np.linalg.inv(world[n]).T.flatten() for n in jointnames]);doc['skins']=[dict(name='Skeleton3D',joints=list(range(len(jointnames))),skeleton=0,inverseBindMatrices=acc(ibm,'MAT4'))]
guardar_roupa=os.environ.get('KK_GUARDAR_ROUPA')=='1'
report=[]
for p in cena['pecas']:
 tipo=p['selecao']['tipo'];pref=p['prefab']
 for m in p['malhas']:
  if not m['exportar']:continue
  d=np.load(T/'malhas'/(m['nome']+'.npz'));V=d['P'].astype(float);N=d['N'].astype(float);BI=d['BI'];BW=d['BW'];A=np.zeros((len(V),3,3));D=np.zeros((len(V),3));J=np.zeros_like(BI)
  for k in range(4):
   for j in np.unique(BI[:,k]):
    name=m['bones'][j];M=world[name]@np.linalg.inv(p['_orig'][name]);sel=BI[:,k]==j;w=BW[sel,k,None];A[sel]+=w[:,:,None]*M[:3,:3];D[sel]+=w*M[:3,3];J[sel,k]=jointids[name]
  VV=np.einsum('nij,nj->ni',A,V)+D;NN=np.einsum('nij,nj->ni',np.linalg.inv(A+np.eye(3)[None]*1e-12).transpose(0,2,1),N);NN/=np.maximum(np.linalg.norm(NN,axis=1,keepdims=True),1e-12)
  uv=d['UV'][:,:2].copy();uv[:,1]=1-uv[:,1]
  attrs=dict(POSITION=acc(VV,'VEC3',target=34962),NORMAL=acc(NN,'VEC3',target=34962),TEXCOORD_0=acc(uv,'VEC2',target=34962),JOINTS_0=acc(J,'VEC4',5123,34962),WEIGHTS_0=acc(BW,'VEC4',target=34962))
  # Tangentes explícitas: o importador não as cria para o fallback unlit.
  tg=np.zeros_like(VV);bt=np.zeros_like(VV)
  for si in range(m['submalhas']):
   tt=d['T'+str(si)]
   if not len(tt):continue
   e1=VV[tt[:,1]]-VV[tt[:,0]];e2=VV[tt[:,2]]-VV[tt[:,0]]
   u1=uv[tt[:,1]]-uv[tt[:,0]];u2=uv[tt[:,2]]-uv[tt[:,0]]
   de=u1[:,0]*u2[:,1]-u1[:,1]*u2[:,0];iv=np.divide(1,de,out=np.zeros_like(de),where=abs(de)>1e-12)
   tangent=(e1*u2[:,1,None]-e2*u1[:,1,None])*iv[:,None]
   bitangent=(e2*u1[:,0,None]-e1*u2[:,0,None])*iv[:,None]
   for vi in range(3):np.add.at(tg,tt[:,vi],tangent);np.add.at(bt,tt[:,vi],bitangent)
  tg-=NN*(NN*tg).sum(1)[:,None];tg/=np.maximum(np.linalg.norm(tg,axis=1,keepdims=True),1e-12)
  tw=np.where((np.cross(NN,tg)*bt).sum(1)<0,-1,1)
  if 'TANGENT' in d:
   src=d['TANGENT'];original=np.einsum('nij,nj->ni',A,src[:,:3]);original-=NN*(NN*original).sum(1)[:,None]
   norms=np.linalg.norm(original,axis=1,keepdims=True);valid=norms[:,0]>1e-9
   original/=np.maximum(norms,1e-12)
   tg[valid]=original[valid];tw[valid]=-src[valid,3] # inversão V da UV
  attrs['TANGENT']=acc(np.c_[tg,tw],'VEC4',target=34962)
  # Cores originais controlam o casco; não embutir iluminação nos vértices.
  cores=d['COR'].copy() if 'COR' in d else np.ones((len(VV),4))
  if cores.max()>1:cores/=255.0
  attrs['COLOR_0']=acc(cores,'VEC4',target=34962)
  if 'UV1' in d:
   uv2=d['UV1'].copy();uv2[:,1]=1-uv2[:,1];attrs['TEXCOORD_1']=acc(uv2,'VEC2',target=34962)
  for canal in (2,3):
   if 'UV'+str(canal) in d:
    uvc=d['UV'+str(canal)].copy();uvc[:,1]=1-uvc[:,1]
    attrs['TEXCOORD_'+str(canal)]=acc(uvc,'VEC2',target=34962)
  targets=[dict(POSITION=acc(np.einsum('nij,nj->ni',A,d['S_'+name]),'VEC3',target=34962)) for name in m['shapes']]
  for target,name in zip(targets,m['shapes']):
   if 'SN_'+name in d:
    nm=np.linalg.inv(A+np.eye(3)[None]*1e-12).transpose(0,2,1)
    normal=np.einsum('nij,nj->ni',nm,N+d['SN_'+name]);normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-12)
    target['NORMAL']=acc(normal-NN,'VEC3',target=34962)
  nomes_shapes=list(m['shapes'])
  # Morph sintético legado; canais originais continuam disponíveis. O mascote
  # usa as pálpebras nativas e desativa o recuo da íris, que a apagava cedo demais.
  if m['go'] in ['cf_O_face','cf_O_noseline','cf_O_eyeline','cf_O_eyeline_low','cf_Ohitomi_L','cf_Ohitomi_R','cf_Ohitomi_L02','cf_Ohitomi_R02']:
   delta=np.zeros_like(VV)
   if m['go'].startswith('cf_Ohitomi'):
    delta[:]=np.array([0,0,-.07])
   else:
    fechada=next((n for n in m['shapes'] if n.startswith('eye_') and n.endswith('_def_cl')),None)
    aberta=next((n for n in m['shapes'] if n.startswith('eye_') and n.endswith('_def_op')),None)
    if fechada:delta=np.einsum('nij,nj->ni',A,d['S_'+fechada]-(d['S_'+aberta] if aberta else 0))
   targets.append(dict(POSITION=acc(delta,'VEC3',target=34962)));nomes_shapes.append('piscar')
  prims=[]
  for i in range(m['submalhas']):
   tri=d['T'+str(i)].copy()
   if not len(tri):continue
   if m['go']=='o_body_a':
    # Máscara corporal indicada pela camiseta: vermelho = regiões visíveis.
    mask=np.load(T/'mascara_corpo.npy');tuv=d['UV'][tri,:2];xx=np.clip((tuv[:,:,0]*mask.shape[1]).astype(int),0,mask.shape[1]-1);yy=np.clip(((1-tuv[:,:,1])*mask.shape[0]).astype(int),0,mask.shape[0]-1);keep=((mask[yy,xx,0]>180).all(1))
    tri=tri[keep]
   if tipo=='roupa_2':
    mask=np.load(T/'mascara_bra.npy');tuv=d['UV'][tri,:2];xx=np.clip((tuv[:,:,0]*mask.shape[1]).astype(int),0,mask.shape[1]-1);yy=np.clip(((1-tuv[:,:,1])*mask.shape[0]).astype(int),0,mask.shape[0]-1)
    tri=tri[(mask[yy,xx,0]>180).all(1)]
   if not len(tri):continue
   pr=dict(attributes=attrs,indices=acc(tri.flatten(),'SCALAR',5125,34963),material=material(tipo,m['materiais'][i]))
   if targets:pr['targets']=targets
   prims.append(pr)
  if not prims:continue
  mesh=dict(name=m['go'],primitives=prims)
  if targets:mesh.update(weights=[1.0 if name.endswith('_def_op') and name.startswith(('eye_','mayuge.')) or name.endswith('_def_cl') and name.startswith(('mouth_','kuti_')) else 0.0 for name in nomes_shapes],extras=dict(targetNames=nomes_shapes))
  mi=len(doc['meshes']);doc['meshes'].append(mesh);ni=len(nodes);nodes.append(dict(name=m['go'],mesh=mi,skin=0));nodes[0].setdefault('children',[]).append(ni);report.append(dict(nome=m['go'],vertices=len(V),shapes=len(targets)))
  if guardar_roupa and (m['go']=='o_body_a' or tipo=='roupa_2'):
   variantes=['01','10','11'] if m['go']=='o_body_a' else ['sem_blusa']
   for variante in variantes:
    vp=[]
    if m['go']=='o_body_a':
     mask=np.full((2048,2048,4),255,dtype=np.uint8)
     for slot in range(2):
      if variante[slot]=='0':mask=np.minimum(mask,np.load(T/('mascara_roupa_'+str(slot)+'.npy')))
    for si in range(m['submalhas']):
     tri=d['T'+str(si)].copy()
     if m['go']=='o_body_a':
      tuv=d['UV'][tri,:2];xx=np.clip((tuv[:,:,0]*mask.shape[1]).astype(int),0,mask.shape[1]-1);yy=np.clip(((1-tuv[:,:,1])*mask.shape[0]).astype(int),0,mask.shape[0]-1)
      tri=tri[(mask[yy,xx,0]>180).all(1)]
     if not len(tri):continue
     pr=dict(attributes=attrs,indices=acc(tri.flatten(),'SCALAR',5125,34963),material=material(tipo,m['materiais'][si]))
     if targets:pr['targets']=targets
     vp.append(pr)
    if not vp:continue
    vm=copy.deepcopy(mesh);vm['name']='kk_'+m['go']+'_'+variante;vm['primitives']=vp
    mi=len(doc['meshes']);doc['meshes'].append(vm);ni=len(nodes)
    nodes.append(dict(name=vm['name'],mesh=mi,skin=0));nodes[0].setdefault('children',[]).append(ni)

def gravar(path,document,data):
 document['buffers']=[dict(byteLength=len(data))];raw=json.dumps(document,separators=(',',':'),ensure_ascii=False).encode();raw+=b' '*((-len(raw))%4);data=bytes(data)+b'\0'*((-len(data))%4);path.write_bytes(struct.pack('<III',0x46546c67,2,28+len(raw)+len(data))+struct.pack('<II',len(raw),0x4e4f534a)+raw+struct.pack('<II',len(data),0x004e4942)+data)

def ler_glb(path):
 b=path.read_bytes();n=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+n]),b[28+n:]
if guardar_roupa:
 gravar(S/'personagem_roupas.glb',doc,buf)
 print('GLB com variantes de roupas concluído.',flush=True)
 sys.exit(0)
# O GLB principal fica sem animação; a prova contém canais copiados integralmente do idle.
gravar(S/'personagem.glb',doc,buf)
a,ab=ler_glb(pathlib.Path(__file__).resolve().parent.parent/'animacoes/exportados/idle_em_pe.glb');prova=copy.deepcopy(doc);pb=bytearray(buf)
while len(pb)%4:pb.append(0)
base=len(pb);pb.extend(ab);vo=len(prova['bufferViews']);ao=len(prova['accessors'])
for v in a['bufferViews']:v=copy.deepcopy(v);v['byteOffset']=v.get('byteOffset',0)+base;prova['bufferViews'].append(v)
for ac in a['accessors']:ac=copy.deepcopy(ac);ac['bufferView']+=vo;prova['accessors'].append(ac)
anim=copy.deepcopy(a['animations'][0])
for sm in anim['samplers']:sm['input']+=ao;sm['output']+=ao
for ch in anim['channels']:ch['target']['node']=byn[a['nodes'][ch['target']['node']]['name']]
prova['animations']=[anim];gravar(S/'personagem_idle.glb',prova,pb)
(S/'validacao.json').write_text(json.dumps(dict(ossos_canonicos=len(orig),ossos_totais=len(jointnames),malhas=report,canais_idle=len(anim['channels']),nomes_ausentes=[],observacao='Canais do idle copiados por nome exato, sem retarget.'),ensure_ascii=False,indent=2)+'\n')
# Montagem real no Blender pela importação do GLB recém-gravado e inspeção renderizada.
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(S/'personagem.glb'),bone_heuristic='TEMPERANCE')
scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=640;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.film_transparent=False;scene.render.image_settings.file_format='PNG';scene.world=bpy.data.worlds.new('Fundo');scene.world.color=(.045,.055,.075);scene.view_settings.view_transform='Standard'
arm=next(o for o in scene.objects if o.type=='ARMATURE');assert all(n['name'] in arm.data.bones for n in orig)
# Posição neutra para as prévias sem editar o repouso exportado.
for name,ang in [('cf_j_arm00_L',72),('cf_j_arm00_R',-72)]:
 b=arm.pose.bones[name];bpy.context.view_layer.update();mw=arm.matrix_world@b.matrix;loc=mw.translation;b.matrix=arm.matrix_world.inverted()@Matrix.Translation(loc)@Matrix.Rotation(math.radians(ang),4,'Y')@Matrix.Translation(-loc)@mw
bpy.context.view_layer.update();points=[o.matrix_world@v.co for o in scene.objects if o.type=='MESH' for v in o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices];xyz=np.array(points);lo=xyz.min(0);hi=xyz.max(0);target=Vector((lo+hi)/2)
camd=bpy.data.cameras.new('Camera');camd.type='ORTHO';camd.ortho_scale=float(hi[2]-lo[2])*1.22;cam=bpy.data.objects.new('Camera',camd);scene.collection.objects.link(cam);scene.camera=cam
# Materiais sem luz exportam KHR_materials_unlit; prévia reproduz a mesma textura toon.
def render(nome,offset):
 cam.location=target+Vector(offset);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(S/nome);bpy.ops.render.render(write_still=True)
render('previa_frente.png',(0,-4,.05));render('previa_lado.png',(4,0,.05))
bpy.ops.wm.save_as_mainfile(filepath=str(S/'personagem.blend'))
# Reimporta a prova para avaliar exatamente os canais glTF aplicados, sem ação manual.
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(S/'personagem_idle.glb'),bone_heuristic='TEMPERANCE');scene=bpy.context.scene;scene.render.fps=30;scene.frame_set(18);scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=640;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='Standard';scene.world=bpy.data.worlds.new('Fundo');scene.world.color=(.045,.055,.075)
camd=bpy.data.cameras.new('Camera');camd.type='ORTHO';camd.ortho_scale=float(hi[2]-lo[2])*1.22;cam=bpy.data.objects.new('Camera',camd);scene.collection.objects.link(cam);scene.camera=cam;cam.location=target+Vector((1,-4,.1));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(S/'previa_idle.png');bpy.ops.render.render(write_still=True)
print('Montagem, GLBs e três prévias concluídos.',flush=True)
