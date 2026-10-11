#!/usr/bin/env python3
"""Índice e decodificação SFW de KK Unity 5.6. Saídas confinadas à pasta do script."""
import os
import argparse, collections, hashlib, json, math, pathlib, re, struct, zlib
import numpy as np
import UnityPy

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_GAME = pathlib.Path(os.environ.get('KK_JOGO') or pathlib.Path.home()/'Downloads/Koikatsu.Party/Koikatsu Party')
BONE_BUNDLE = 'chara/oo_base.unity3d'
ANIM_BUNDLE = 'action/animator/00.unity3d'
ADV_BUNDLE = 'adv/motion/controller/adv/00.unity3d'
POSE_BUNDLE = 'communication/info_00.unity3d'

def save_json(path, data):
    path = (HERE / path).resolve()
    if not path.is_relative_to(HERE): raise ValueError('Saída fora da pasta de trabalho')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n')

def load_bundle(game, relative):
    root = (game / 'abdata').resolve()
    p = (root / relative).resolve()
    if not p.is_relative_to(root / 'action') and p not in [root / x for x in (BONE_BUNDLE,ADV_BUNDLE,POSE_BUNDLE)]:
        raise ValueError(f'Bundle fora da lista permitida: {relative}')
    # Sem resolver dependências globais, sem examinar abdata/h ou seguir symlinks externos.
    return UnityPy.load(p.read_bytes())

def skeleton(game):
    env = load_bundle(game, BONE_BUNDLE)
    root = next(o.read() for o in env.objects if o.type.name == 'Transform'
                and o.read().m_Father.path_id == 0
                and o.read().m_GameObject.read().m_Name == 'p_cf_body_bone')
    nodes = []
    def walk(t, parent):
        name = t.m_GameObject.read().m_Name
        path = name if parent < 0 else nodes[parent]['path']+'/'+name
        i = len(nodes)
        p, r, s = t.m_LocalPosition, t.m_LocalRotation, t.m_LocalScale
        nodes.append(dict(name=name, path=path, parent=parent,
                          translation=[p.x,p.y,p.z], rotation=[r.x,r.y,r.z,r.w], scale=[s.x,s.y,s.z]))
        for c in t.m_Children: walk(c.read(), i)
    walk(root, -1)
    assert len(set(n['name'] for n in nodes)) == len(nodes), 'Nomes duplicados no esqueleto'
    hashes = {0: (0, '')}
    for i, n in enumerate(nodes):
        parts = n['path'].split('/')
        for j in range(len(parts)):
            path = '/'.join(parts[j:]); h = zlib.crc32(path.encode())
            if h in hashes and hashes[h][0] != i: raise ValueError('Colisão CRC32')
            hashes[h] = (i, path)
    # O jogo mistura clipes high/low. Não renomear cf_dd_* para cf_d_*:
    # são auxiliares de deformação com caminhos diferentes, não ossos de movimento.
    # Somente hashes comprovados pelo Avatar low podem ser omitidos no rig high.
    for o in env.objects:
        if o.type.name == 'Avatar' and o.peek_name() == 'cf_body_lowAvatar':
            for h, path in o.read_typetree()['m_TOS']:
                if h not in hashes and re.search(r'/cf_dd_(arm02|thigh02)_[LR](?:/|$)', path):
                    hashes[h] = (-1, path)
    return nodes, hashes

def identity(bundle, pid): return f'{bundle}#{pid}'

def pointer_id(obj, ptr, cab_to_bundle):
    fid, pid = ptr['m_FileID'], ptr['m_PathID']
    if not pid: return None
    bundle = obj['_bundle']
    if fid:
        exts = obj['_externals']
        if fid > len(exts): return f'UNRESOLVED:{fid}#{pid}'
        cab = pathlib.PurePosixPath(exts[fid-1].replace('\\','/')).name.lower()
        bundle = cab_to_bundle.get(cab, f'EXTERNAL:{cab}')
    return identity(bundle,pid)

def controller_states(obj, cabs):
    d = obj['tree']; tos = dict(d['m_TOS']); clips = d['m_AnimationClips']; result=[]
    for sm in d['m_Controller']['m_StateMachineArray']:
        for st in sm['data']['m_StateConstantArray']:
            s = st['data']
            for bt in s['m_BlendTreeConstantArray']:
                for node in bt['data']['m_NodeArray']:
                    n = node['data']; idx = n['m_ClipID']
                    if n['m_ChildIndices'] or idx >= len(clips): continue
                    result.append(dict(clip=pointer_id(obj,clips[idx],cabs),
                        state=tos.get(s.get('m_FullPathID')) or tos.get(s['m_PathID']) or tos.get(s['m_NameID']),
                        speed=s['m_Speed'], state_loop=s['m_Loop'], mirror=s['m_Mirror'] or n['m_Mirror'],
                        cycle_offset=s['m_CycleOffset']+n['m_CycleOffset']))
    return result

def category(name, refs):
    states=' '.join(r['state'] or '' for r in refs).lower()
    if re.search(r'masturbation|lesbian|lewd|momu',name.lower()+' '+states): return 'excluido_sexual'
    if re.search(r'toilet|shower',states): return 'excluido_intimo'
    if name.startswith('sp_') or any(s in name.lower() for s in ['icon','textitem','pulsing','fade']): return 'interface'
    if name.startswith('f_sleep'): return 'sono_deitado'
    if 'aruki' in name or 'walk' in name: return 'caminhada'
    if 'hasiru' in name or 'run_' in name: return 'corrida'
    if name.startswith(('f_talk','f_defense','f_cheer','Stand_Joy','Stand_Oth','Stand_Sad','Stand_Ang')): return 'gesto_reacao'
    if name.startswith(('f_stand','Stand_','Idle_')): return 'idle_em_pe'
    if name.startswith('f_suwari'): return 'sentado'
    if name.startswith('f_tachi'): return 'cotidiano_em_pe'
    if name.startswith('f_syagami'): return 'agachado'
    return 'outro_revisar'

def catalog(game, nodes, hashes):
    controllers=[]; clips=[]; cabs={}; bundles=[]; errors=[]; binding_sets={}; paths={}
    labels={}
    for o in load_bundle(game,POSE_BUNDLE).objects:
        if o.type.name=='MonoBehaviour' and o.peek_name()=='pose_00':
            for row in o.read_typetree()['list']:
                r=row['list']
                if len(r)>=4 and r[1]==ADV_BUNDLE:labels[r[3]]=r[0]
    for path in [*sorted((game/'abdata/action').rglob('*.unity3d')),game/'abdata'/ADV_BUNDLE]:
        rel=path.relative_to(game/'abdata').as_posix()
        try:
            env=load_bundle(game,rel)
            for o in env.objects:
                cabs[o.assets_file.name.lower()] = rel
            counts=collections.Counter(o.type.name for o in env.objects)
            bundles.append(dict(bundle=rel, bytes=path.stat().st_size, objects=dict(counts)))
            for o in env.objects:
                typ=o.type.name
                if typ in ('AnimatorController','AnimatorOverrideController'):
                    controllers.append(dict(id=identity(rel,o.path_id), type=typ, tree=o.read_typetree(),
                        _bundle=rel, _externals=[x.path for x in o.assets_file.externals]))
                elif typ=='AnimationClip':
                    d=o.read_typetree(); m=d['m_MuscleClip']; bind=d['m_ClipBindingConstant']['genericBindings']
                    bs=[]
                    for b in bind:
                        resolved=hashes.get(b['path']) if b['typeID']==4 else None
                        bs.append(dict(hash=b['path'],attribute=b['attribute'],type_id=b['typeID'],
                            path=resolved[1] if resolved else None, bone=nodes[resolved[0]]['name'] if resolved and resolved[0]>=0 else None,
                            auxiliary_low_only=bool(resolved and resolved[0]<0)))
                    binding_id=hashlib.sha256(json.dumps(bs,sort_keys=True).encode()).hexdigest()[:16]
                    binding_sets.setdefault(binding_id,[[b['hash'],b['attribute'],b['type_id']] for b in bs])
                    for b in bs:
                        if b['path'] is not None:paths[str(b['hash'])]={k:v for k,v in b.items() if k not in ('hash','attribute','type_id')}
                    types=collections.Counter(b['typeID'] for b in bind)
                    mode='generic' if set(types)=={4} else ('humanoid_ou_animator' if 95 in types else 'outro')
                    clips.append(dict(id=identity(rel,o.path_id), bundle=rel,path_id=str(o.path_id), name=d['m_Name'],
                        length=m['m_StopTime']-m['m_StartTime'],start=m['m_StartTime'],loop=bool(m['m_LoopTime']),
                        sample_rate=d['m_SampleRate'], mode=mode, binding_types=dict(types),
                        resolved_transform_bindings=sum(b['bone'] is not None for b in bs),binding_count=len(bs),binding_set=binding_id,
                        dialogue_label=labels.get(d['m_Name']) if rel==ADV_BUNDLE else None,controllers=[]))
            print('indexado',rel,dict(counts),flush=True)
        except Exception as exc:
            errors.append(dict(bundle=rel,error=str(exc)))
    byclip={c['id']:c for c in clips}; ctrlmap={c['id']:c for c in controllers}; statecache={}
    def resolve(c, stack=()):
        if c['id'] in statecache:return statecache[c['id']]
        if c['id'] in stack:raise ValueError('Ciclo em override controllers')
        if c['type']=='AnimatorController':rows=controller_states(c,cabs)
        else:
            parent=pointer_id(c,c['tree']['m_Controller'],cabs)
            remap={pointer_id(c,p['m_OriginalClip'],cabs):pointer_id(c,p['m_OverrideClip'],cabs) for p in c['tree']['m_Clips']}
            rows=[]
            if parent in ctrlmap:
                for r in resolve(ctrlmap[parent],(*stack,c['id'])):
                    row=dict(r); row['original_clip']=r['clip']; row['clip']=remap.get(r['clip']) or r['clip'];rows.append(row)
            else:errors.append(dict(controller=c['id'],error='Controller base externo não resolvido',reference=parent))
        statecache[c['id']]=rows;return rows
    ctrlout=[]
    for c in controllers:
        rows=resolve(c);ctrlout.append(dict(id=c['id'],bundle=c['_bundle'],name=c['tree']['m_Name'],type=c['type'],states=rows))
        for r in rows:
            if r['clip'] in byclip:
                byclip[r['clip']]['controllers'].append(dict(controller=c['tree']['m_Name'],controller_id=c['id'],**{k:v for k,v in r.items() if k!='clip'}))
    for c in clips:
        c['category_guess']=category(c['name'],c['controllers'])
        c['selected']=False
    result=dict(format_version=2, scope='abdata/action completo + adv/motion/controller/adv/00 (gestos cotidianos de diálogo); chara/oo_base somente esqueleto/Avatar; communication/info_00 somente rótulos',
        skeleton_bundle=BONE_BUNDLE,skeleton_root='p_cf_body_bone',bone_names_case_sensitive=True,
        bundles=bundles,binding_layout=['path_crc32','attribute','type_id'],paths=paths,binding_sets=binding_sets,controllers=ctrlout,clips=sorted(clips,key=lambda c:(c['bundle'],c['name'],c['path_id'])),errors=errors)
    save_json('catalogo.json',result)
    return result

def decode(d, hashes, fps=30):
    """Curvas compiladas: streamed (polinômio cúbico), dense e constant, nesta ordem.

    Streamed: registros LE (float time, int count, [int index, float4 coeff]).
    coeff = a,b,c,d: f(t0+dt) = ((a*dt+b)*dt+c)*dt+d.
    Frames sentinela ±FLT_MAX/inf fornecem limites; nunca viram chaves exportadas.
    Binding Transform: 1=translation(3), 2=quaternion xyzw(4), 3=scale(3).
    Falha fechada para Humanoid, Euler, PPtr, paths desconhecidos ou layout distinto.
    """
    bindings=d['m_ClipBindingConstant']['genericBindings'];m=d['m_MuscleClip'];clip=m['m_Clip']['data']
    for b in bindings:
        if b['typeID']!=4 or b['attribute'] not in (1,2,3) or b['isPPtrCurve'] or b['path'] not in hashes:
            raise ValueError(f'Binding não suportado (sem retargeting silencioso): {b}')
    if d['m_Legacy'] or d['m_CompressedRotationCurves'] or any(d[k] for k in ['m_PositionCurves','m_RotationCurves','m_ScaleCurves']):
        raise ValueError('Layout legacy/curvas explícitas não suportado por este decoder compilado')
    duration=m['m_StopTime']-m['m_StartTime'];nframes=round(duration*fps)
    times=np.linspace(0,duration,nframes+1);sample_times=times+m['m_StartTime']
    stream=clip['m_StreamedClip'];dense=clip['m_DenseClip'];const=clip['m_ConstantClip']['data']
    ns=stream['curveCount'];nd=dense['m_CurveCount'];total=ns+nd+len(const)
    widths=[4 if b['attribute']==2 else 3 for b in bindings]
    assert sum(widths)==total,(sum(widths),total)
    values=np.empty((len(times),total),np.float64)
    streams=[[] for _ in range(ns)]
    raw=struct.pack('<%dI'%len(stream['data']),*stream['data']);off=0
    while off<len(raw):
        t,count=struct.unpack_from('<fi',raw,off);off+=8
        assert 0<=count<=total and off+count*20<=len(raw)
        for _ in range(count):
            idx,*co=struct.unpack_from('<i4f',raw,off);off+=20
            assert 0<=idx<ns
            streams[idx].append((t,co))
    assert off==len(raw)
    residuals=[]
    for i,keys in enumerate(streams):
        if not keys:raise ValueError(f'Curva streamed vazia: {i}')
        ts=np.array([k[0] for k in keys]);cs=np.array([k[1] for k in keys])
        assert np.all(np.diff(ts)>=0)
        ix=np.clip(np.searchsorted(ts,sample_times,side='right')-1,0,len(ts)-1)
        dt=np.maximum(sample_times-ts[ix],0);dt[np.abs(ts[ix])>1e20]=0
        co=cs[ix];values[:,i]=((co[:,0]*dt+co[:,1])*dt+co[:,2])*dt+co[:,3]
        # Independente do sampling: continuidade dos polinômios até a próxima chave.
        for j in range(len(keys)-1):
            if abs(ts[j])>1e20 or abs(ts[j+1])>1e20:continue
            a,b,c,v=cs[j];delta=ts[j+1]-ts[j]
            if a==b==c==0:continue # step é permitido
            residuals.append(abs(((a*delta+b)*delta+c)*delta+v-cs[j+1,3]))
    if nd:
        data=np.array(dense['m_SampleArray']).reshape(dense['m_FrameCount'],nd)
        ts=dense['m_BeginTime']+np.arange(len(data))/dense['m_SampleRate']
        for i in range(nd):values[:,ns+i]=np.interp(sample_times,ts,data[:,i])
    values[:,ns+nd:]=const
    if not np.isfinite(values).all():raise ValueError('NaN/Inf na animação')
    tracks=[];offset=0;quat_error=0;omitted=[]
    for b,width in zip(bindings,widths):
        v=values[:,offset:offset+width].copy();offset+=width;idx,path=hashes[b['path']]
        prop={1:'translation',2:'rotation',3:'scale'}[b['attribute']]
        if idx<0:
            omitted.append(dict(hash=b['path'],path=path,property=prop,reason='auxiliar exclusivo do Avatar low; ausente no rig high'))
            continue
        if prop=='translation':v[:,0]*=-1 # Unity LH -> glTF RH; Y continua para cima.
        if prop=='rotation':
            norms=np.linalg.norm(v,axis=1);quat_error=max(quat_error,float(np.max(np.abs(norms-1))))
            if min(norms)<0.5:raise ValueError('Quaternion inválido')
            v/=norms[:,None];v[:,1:3]*=-1
            for j in range(1,len(v)):
                if np.dot(v[j-1],v[j])<0:v[j]*=-1
        tracks.append(dict(node=idx,path=path,property=prop,values=v))
    return times,tracks,dict(streamed_components=ns,dense_components=nd,constant_components=len(const),
        max_polynomial_endpoint_residual=max(residuals,default=0),max_quaternion_norm_error_before_normalization=quat_error,
        omitted_low_auxiliary_bindings=omitted)

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--game',type=pathlib.Path,default=DEFAULT_GAME)
    ap.add_argument('--index-only',action='store_true');ap.add_argument('--reuse-index',action='store_true');args=ap.parse_args()
    nodes,hashes=skeleton(args.game)
    save_json('esqueleto.json',dict(coordinate_system='Unity original LH Y-up',bundle=BONE_BUNDLE,nodes=nodes))
    cat=json.loads((HERE/'catalogo.json').read_text()) if args.reuse_index else catalog(args.game,nodes,hashes)
    if args.index_only:return
    from glb import export_glb
    # Itens de h/ (só poses sem toque) são exportados por extrair_espera_h.py, com sua própria allowlist.
    selection=[i for i in json.loads((HERE/'selecao.json').read_text()) if not i.get('bundle','').startswith('h/')];envs={}
    byname=collections.defaultdict(list)
    for bundle in sorted({item.get('bundle',ANIM_BUNDLE) for item in selection}):
        envs[bundle]=load_bundle(args.game,bundle)
        for o in envs[bundle].objects:
            if o.type.name=='AnimationClip':byname[(bundle,o.peek_name())].append(o)
    for c in cat['clips']:
        c['selected']=False;c.pop('export',None)
    report=[]
    for item in selection:
        bundle=item.get('bundle',ANIM_BUNDLE);candidates=byname[(bundle,item['source'])]
        if len(candidates)!=1:raise ValueError('Seleção ambígua/ausente: '+item['source'])
        o=candidates[0];entry=next(c for c in cat['clips'] if c['id']==identity(bundle,o.path_id))
        if entry['category_guess'].startswith('excluido'):raise ValueError('Clipe excluído: '+item['source'])
        # Allowlist revisada no arquivo selecao.json. Não se exporta o catálogo inteiro.
        d=o.read_typetree();times,tracks,stats=decode(d,hashes)
        name=item['name'];file=HERE/'exportados'/f'{name}.glb'
        file.parent.mkdir(exist_ok=True)
        if not file.resolve().is_relative_to(HERE/'exportados'):raise ValueError('Nome de saída inválido')
        meta=dict(item,source_id=entry['id'],length=entry['length'],source_loop=entry['loop'],fps=30,
            coordinate_system='glTF RH Y-up, reflection X from Unity',decoder=stats)
        export_glb(file,nodes,times,tracks,meta)
        entry['selected']=True;entry['export']=str(file.relative_to(HERE))
        for prop in ['translation','rotation']:
            for bone in ['cf_j_root','cf_n_height','cf_j_hips']:
                tr=next((t for t in tracks if nodes[t['node']]['name']==bone and t['property']==prop),None)
                if tr is not None:
                    meta.setdefault('root_motion',{})[bone+'_'+prop]=dict(start=tr['values'][0].tolist(),end=tr['values'][-1].tolist(),span=np.ptp(tr['values'],axis=0).tolist())
        meta['glb']=str(file.relative_to(HERE));meta['bytes']=file.stat().st_size
        report.append(meta);print('exportado',name,round(entry['length'],3),stats,flush=True)
    save_json('catalogo.json',cat);save_json('exportados/manifesto.json',report)

if __name__=='__main__':main()
