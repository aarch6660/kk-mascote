"""Grava glTF 2.0 com TRS locais exatos; manequim geométrico SFW para inspeção."""
import json, struct
import numpy as np

def trs(p,q,s):
    x,y,z,w=q
    r=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
    m=np.eye(4);m[:3,:3]=r*np.array(s);m[:3,3]=p;return m

def converted_nodes(nodes):
    out=[];world=[]
    for i,n in enumerate(nodes):
        p=np.array(n['translation']);p[0]*=-1
        q=np.array(n['rotation']);q[1:3]*=-1;q/=np.linalg.norm(q)
        nn=dict(name=n['name'],translation=p.tolist(),rotation=q.tolist(),scale=n['scale'])
        out.append(nn);m=trs(p,q,n['scale'])
        if n['parent']>=0:
            out[n['parent']].setdefault('children',[]).append(i);m=world[n['parent']]@m
        world.append(m)
    return out,np.array(world)

def mannequin(nodes,world):
    # Apenas geometria abstrata, sem malhas, materiais ou texturas corporais do jogo.
    byname={n['name']:i for i,n in enumerate(nodes)}
    verts=[];joints=[];colors=[];faces=[]
    def color(name):
        return [.12,.65,.85,1] if name.endswith('_L') else ([1,.38,.12,1] if name.endswith('_R') else [.65,.72,.8,1])
    def part(points,triangles,bone):
        base=len(verts);verts.extend(points);faces.extend([[base+a,base+b,base+c] for a,b,c in triangles])
        joints.extend([[bone,0,0,0]]*len(points));colors.extend([color(nodes[bone]['name'])]*len(points))
    def rod(a,b,r):
        i,j=byname[a],byname[b];p=world[i,:3,3];end=world[j,:3,3];axis=end-p
        length=np.linalg.norm(axis)
        if length<1e-5:return
        axis/=length;u=np.cross(axis,[0,1,0] if abs(axis[1])<.9 else [1,0,0]);u/=np.linalg.norm(u);v=np.cross(axis,u)
        pts=[center+r*(np.cos(k*np.pi/4)*u+np.sin(k*np.pi/4)*v) for center in (p,end) for k in range(8)]
        tri=[]
        for k in range(8):
            nxt=(k+1)%8;tri.extend([(k,nxt,8+nxt),(k,8+nxt,8+k)])
        tri.extend((0,k+1,k) for k in range(1,7));tri.extend((8,8+k,8+k+1) for k in range(1,7))
        part(pts,tri,i)
    chains=[(['cf_j_hips','cf_j_spine01','cf_j_spine02','cf_j_spine03','cf_j_neck','cf_j_head'],.037),
            (['cf_j_hips','cf_j_waist01','cf_j_waist02'],.04)]
    for side in ['L','R']:
        chains.extend([(['cf_j_spine03',f'cf_j_shoulder_{side}',f'cf_j_arm00_{side}',f'cf_j_forearm01_{side}',f'cf_j_hand_{side}'],.022),
            (['cf_j_waist02',f'cf_j_thigh00_{side}',f'cf_j_leg01_{side}',f'cf_j_leg03_{side}',f'cf_j_foot_{side}',f'cf_j_toes_{side}'],.027),
            ([f'cf_j_hand_{side}',f'cf_j_middle01_{side}',f'cf_j_middle03_{side}'],.018)])
    for chain,r in chains:
        for a,b in zip(chain,chain[1:]):rod(a,b,r)
    # Cabeça elipsoidal, rígida ao osso head; pequeno nariz mostra orientação.
    i=byname['cf_j_head']
    def ellipsoid(center,scale):
        pts=[];tri=[]
        for v in range(1,8):
            for u in range(12):
                p=np.array(center)+np.array(scale)*[np.sin(np.pi*v/8)*np.cos(2*np.pi*u/12),np.cos(np.pi*v/8),np.sin(np.pi*v/8)*np.sin(2*np.pi*u/12)]
                pts.append((world[i]@np.r_[p,1])[:3])
        for v in range(6):
            for u in range(12):
                a=v*12+u;b=v*12+(u+1)%12;c=b+12;d=a+12;tri.extend([(a,b,c),(a,c,d)])
        top=len(pts);pts.append((world[i]@np.r_[np.array(center)+[0,scale[1],0],1])[:3]);bottom=len(pts);pts.append((world[i]@np.r_[np.array(center)-[0,scale[1],0],1])[:3])
        for u in range(12):tri.extend([(top,(u+1)%12,u),(bottom,72+u,72+(u+1)%12)])
        part(pts,tri,i)
    ellipsoid([0,.08,.015],[.085,.11,.085]);ellipsoid([0,.07,.1],[.022,.02,.035])
    return np.array(verts),np.array(faces),np.array(joints),np.array(colors)

def export_glb(path,nodes,times,tracks,meta):
    gn,world=converted_nodes(nodes);verts,faces,joints,colors=mannequin(nodes,world)
    doc=dict(asset=dict(version='2.0',generator='KK SFW Stage 1 - extrair.py / glb.py'),
             scene=0,scenes=[dict(name='KK_SFW',nodes=[len(gn)])],nodes=gn,
             bufferViews=[],accessors=[],buffers=[],animations=[])
    buf=bytearray()
    def accessor(data,typ,component=5126,target=None,bounds=False):
        nonlocal buf
        dtype={5126:'<f4',5123:'<u2',5125:'<u4'}[component];arr=np.asarray(data,dtype=dtype)
        while len(buf)%4:buf.append(0)
        view=dict(buffer=0,byteOffset=len(buf),byteLength=arr.nbytes)
        if target:view['target']=target
        vid=len(doc['bufferViews']);doc['bufferViews'].append(view);buf.extend(arr.tobytes())
        count=len(arr) if typ!='SCALAR' else arr.size
        acc=dict(bufferView=vid,componentType=component,count=count,type=typ)
        if bounds:
            a=arr.reshape(count,-1);acc['min']=a.min(axis=0).tolist();acc['max']=a.max(axis=0).tolist()
        idx=len(doc['accessors']);doc['accessors'].append(acc);return idx
    rootidx=len(gn);meshidx=rootidx+1
    gn.append(dict(name='KK_Mascote',children=[0,meshidx]));gn.append(dict(name='Manequim_SFW',mesh=0,skin=0))
    doc['skins']=[dict(name='Skeleton3D',joints=list(range(len(nodes))),skeleton=0,
        inverseBindMatrices=accessor(np.linalg.inv(world).transpose(0,2,1).reshape(-1,16),'MAT4'))]
    weights=np.zeros((len(verts),4));weights[:,0]=1
    attributes=dict(POSITION=accessor(verts,'VEC3',target=34962,bounds=True),
                    JOINTS_0=accessor(joints,'VEC4',5123,34962),WEIGHTS_0=accessor(weights,'VEC4',target=34962),
                    COLOR_0=accessor(colors,'VEC4',target=34962))
    doc['meshes']=[dict(name='Manequim_geometrico',primitives=[dict(attributes=attributes,indices=accessor(faces.flatten(),'SCALAR',5123,34963),material=0)])]
    doc['materials']=[dict(name='Manequim',doubleSided=True,pbrMetallicRoughness=dict(metallicFactor=0,roughnessFactor=.8))]
    anim=dict(name=meta['name']+('_loop' if meta.get('loop') else ''),samplers=[],channels=[],extras=meta)
    fulltime=accessor(times,'SCALAR',bounds=True);endtime=accessor(times[[0,-1]],'SCALAR',bounds=True)
    # Dois pontos para tracks constantes; mantém inclusive valores constantes diferentes do rest.
    for tr in tracks:
        v=tr['values'];constant=np.max(np.abs(v-v[0]))<1e-8
        if constant:v=v[[0,-1]]
        s=dict(input=endtime if constant else fulltime,output=accessor(v,'VEC4' if tr['property']=='rotation' else 'VEC3'),interpolation='LINEAR')
        anim['channels'].append(dict(sampler=len(anim['samplers']),target=dict(node=tr['node'],path=tr['property'])))
        anim['samplers'].append(s)
    doc['animations']=[anim];doc['buffers']=[dict(byteLength=len(buf))]
    raw=json.dumps(doc,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode();raw+=b' '*((-len(raw))%4);buf+=b'\0'*((-len(buf))%4)
    path.write_bytes(struct.pack('<III',0x46546c67,2,12+8+len(raw)+8+len(buf))+struct.pack('<II',len(raw),0x4e4f534a)+raw+struct.pack('<II',len(buf),0x004e4942)+buf)
