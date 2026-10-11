# Extrai peças de personagem do Samabake Scramble para um formato intermediário
# (npz + json) que o montar_blender.py lê.
#
# Cada peça = (bundle, nome do prefab). Os vértices saem já "skinados" na pose de
# repouso do próprio prefab, em espaço de mundo Unity convertido para destro
# (x negado). O Blender liga cada malha ao esqueleto do corpo pelo nome do bone.
#
# uso: extrair.py saida/ bundle:prefab [bundle:prefab ...]
import json, os, sys
import numpy as np
from types import SimpleNamespace
from UnityPy.helpers.MeshHelper import MeshHandler
from carregar import carregar

def trs(t):
    p, r, s = t.m_LocalPosition, t.m_LocalRotation, t.m_LocalScale
    x, y, z, w = r.x, r.y, r.z, r.w
    R = np.array([
        [1-2*(y*y+z*z), 2*(x*y-z*w),   2*(x*z+y*w)],
        [2*(x*y+z*w),   1-2*(x*x+z*z), 2*(y*z-x*w)],
        [2*(x*z-y*w),   2*(y*z+x*w),   1-2*(x*x+y*y)]])
    M = np.eye(4)
    M[:3, :3] = R * np.array([s.x, s.y, s.z])
    M[:3, 3] = [p.x, p.y, p.z]
    return M

def mat4(m):
    return np.array([[m.e00, m.e01, m.e02, m.e03],
                     [m.e10, m.e11, m.e12, m.e13],
                     [m.e20, m.e21, m.e22, m.e23],
                     [m.e30, m.e31, m.e32, m.e33]])

# Unity (canhoto) -> destro: espelha X.
S = np.diag([-1.0, 1, 1, 1])

def achar_prefab(env, nome):
    for o in env.objects:
        if o.type.name == "GameObject":
            g = o.read()
            if g.m_Name == nome:
                for c in g.m_Component:
                    t = c.component.deref_parse_as_object()
                    if type(t).__name__ == "Transform" and t.m_Father.path_id == 0:
                        return g, t
    raise SystemExit(f"prefab {nome} não achado")

def andar(t, pai_mundo, pai_nome, saida, por_id):
    go = t.m_GameObject.read()
    W = pai_mundo @ trs(t)
    saida.append({"nome": go.m_Name, "pai": pai_nome, "mundo": (S @ W @ S).tolist(), "ativo": bool(go.m_IsActive)})
    por_id[t.object_reader.path_id] = (go, W)
    por_id[("go", t.m_GameObject.path_id)] = (go, W)
    for c in t.m_Children:
        andar(c.read(), W, go.m_Name, saida, por_id)

def textura(ptr, pasta, feitas):
    if not ptr.path_id: return None
    tex = ptr.read()
    arq = tex.m_Name + ".png"
    if arq not in feitas:
        try:
            tex.image.save(os.path.join(pasta, "tex", arq))
            feitas.add(arq)
        except Exception as e:
            print("   textura falhou", tex.m_Name, e)
            return None
    return arq

def material(ptr, pasta, feitas):
    if not ptr.path_id: return None
    m = ptr.read()
    sp = m.m_SavedProperties
    return {
        "nome": m.m_Name,
        "shader": m.m_Shader.read().m_ParsedForm.m_Name if m.m_Shader.path_id else None,
        "uv_texturas": {k: {"escala": [v.m_Scale.x, v.m_Scale.y], "offset": [v.m_Offset.x, v.m_Offset.y]} for k, v in sp.m_TexEnvs},
        "texturas": {k: a for k, v in sp.m_TexEnvs if (a := textura(v.m_Texture, pasta, feitas))},
        "cores": {k: [c.r, c.g, c.b, c.a] for k, c in sp.m_Colors},
        "floats": {k: v for k, v in sp.m_Floats},
    }

def malha(smr, go, por_id, pasta, feitas, prefixo):
    mesh = smr.m_Mesh.read()
    h = MeshHandler(mesh); h.process()
    V = np.array(h.m_Vertices, dtype=np.float64)[:, :3]
    N = np.array(h.m_Normals, dtype=np.float64)[:, :3] if h.m_Normals else np.zeros_like(V)
    UV = np.array(h.m_UV0, dtype=np.float64) if h.m_UV0 else np.zeros((len(V), 2))
    nomes_bones, mundos = [], []
    for b in smr.m_Bones:
        g, W = por_id.get(b.path_id, (None, None))
        if g is None:
            g = b.read().m_GameObject.read(); W = None
        nomes_bones.append(g.m_Name); mundos.append(W)
    binds = [mat4(m) for m in mesh.m_BindPose]

    if nomes_bones and h.m_BoneWeights:
        BI = np.zeros((len(V), 4), np.int32); BW = np.zeros((len(V), 4))
        bi = np.array(h.m_BoneIndices, dtype=np.int32).reshape(len(V), -1)[:, :4]
        bw = np.array(h.m_BoneWeights, dtype=np.float64).reshape(len(V), -1)[:, :4]
        BI[:, :bi.shape[1]] = bi; BW[:, :bw.shape[1]] = bw
        skin = [(W @ B) if W is not None else None for W, B in zip(mundos, binds)]
        P = np.zeros_like(V); NN = np.zeros_like(V); A = np.zeros((len(V), 3, 3))
        Vh = np.c_[V, np.ones(len(V))]
        for k in range(4):
            for j in np.unique(BI[:, k]):
                M = skin[j]
                if M is None: continue
                sel = (BI[:, k] == j) & (BW[:, k] > 0)
                w = BW[sel, k][:, None]
                P[sel] += w * (Vh[sel] @ M.T)[:, :3]
                NN[sel] += w * (N[sel] @ M[:3, :3].T)
                A[sel] += w[:, :, None] * M[:3, :3]
    else:
        # malha sem skin: presa ao próprio GameObject
        W = por_id[("go", smr.m_GameObject.path_id)][1]
        P = (np.c_[V, np.ones(len(V))] @ W.T)[:, :3]
        NN = N @ W[:3, :3].T
        A = np.broadcast_to(W[:3, :3], (len(V), 3, 3)).copy()
        BI = np.zeros((len(V),4),np.int32)
        BW = np.zeros((len(V),4)); BW[:,0] = 1
        nomes_bones = [go.m_Name]

    # Normais usam inversa-transposta; deltas de morph precisam da mesma base.
    normal_matrix = np.linalg.inv(A + np.eye(3)[None] * 1e-12).transpose(0, 2, 1)
    NN = np.einsum('nij,nj->ni', normal_matrix, N)
    NN /= np.maximum(np.linalg.norm(NN, axis=1, keepdims=True), 1e-12)
    # para destro
    P[:, 0] *= -1; NN[:, 0] *= -1
    tris = [np.array(t, dtype=np.int32)[:, ::-1] if len(t) else np.zeros((0, 3), np.int32) for t in h.get_triangles()]

    shapes = {}; shape_normals = {}; frames = {}
    bs = mesh.m_Shapes
    if bs and bs.channels:
        for ch in bs.channels:
            frames[ch.name] = [float(bs.fullWeights[ch.frameIndex+i]) for i in range(ch.frameCount)]
            if ch.frameCount != 1:
                raise ValueError('Morph com múltiplos frames exige controlador de interpolação: '+ch.name)
            fr = bs.shapes[ch.frameIndex + ch.frameCount - 1]
            d = np.zeros_like(V)
            dn = np.zeros_like(N)
            for sv in bs.vertices[fr.firstVertex: fr.firstVertex + fr.vertexCount]:
                d[sv.index] = (sv.vertex.x, sv.vertex.y, sv.vertex.z)
                if fr.hasNormals: dn[sv.index] = (sv.normal.x, sv.normal.y, sv.normal.z)
            d = np.einsum("nij,nj->ni", A, d)
            d[:, 0] *= -1
            shapes[ch.name] = d.astype(np.float32)
            if fr.hasNormals:
                n = np.einsum('nij,nj->ni',normal_matrix,N+dn)
                n /= np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-12)
                n[:,0] *= -1
                shape_normals[ch.name] = (n-NN).astype(np.float32)

    nome = f"{prefixo}__{go.m_Name}"
    dados = {"P": P.astype(np.float32), "N": NN.astype(np.float32), "UV": UV.astype(np.float32)}
    if h.m_Colors:
        cores = np.asarray(h.m_Colors, dtype=np.float32)
        if cores.max() > 1: cores /= 255.0
        dados['COR'] = cores
    for i in range(1, 4):
        uvx = getattr(h, f"m_UV{i}", None)
        if uvx: dados[f"UV{i}"] = np.array(uvx, dtype=np.float32)[:, :2]
    for i, t in enumerate(tris): dados[f"T{i}"] = t
    if BI is not None: dados["BI"] = BI; dados["BW"] = BW.astype(np.float32)
    for k, d in shapes.items(): dados["S_" + k] = d
    for k, d in shape_normals.items(): dados['SN_'+k] = d
    if h.m_Tangents:
        tangents = np.asarray(h.m_Tangents,dtype=float)
        xyz = np.einsum('nij,nj->ni',A,tangents[:,:3]);xyz[:,0]*=-1
        xyz-=NN*(NN*xyz).sum(1)[:,None]
        xyz/=np.maximum(np.linalg.norm(xyz,axis=1,keepdims=True),1e-12)
        dados['TANGENT']=np.c_[xyz,-tangents[:,3]].astype(np.float32)
    np.savez_compressed(os.path.join(pasta, "malhas", nome + ".npz"), **dados)
    mats = [material(m, pasta, feitas) for m in smr.m_Materials]
    return {"nome": nome, "go": go.m_Name, "ativo": bool(go.m_IsActive) and bool(smr.m_Enabled),
            "bones": nomes_bones, "materiais": mats, "submalhas": len(tris), "shapes": list(shapes), 'frames_morph':frames}

def extrair(pasta, bundle, prefab, feitas):
    env = carregar(bundle)
    g, t = achar_prefab(env, prefab)
    hier, por_id = [], {}
    andar(t, np.eye(4), None, hier, por_id)
    componente = {}
    for c in g.m_Component:
        obj=c.component.deref()
        if obj.type.name=='MonoBehaviour':
            d=obj.read_typetree()
            if 'rendNormal' in d:
                componente=d
    grupos={}
    for grupo in ['rendNormal','rendAlpha','rendHair']:
        for ptr in componente.get(grupo,[]):
            if ptr['m_PathID']:grupos[ptr['m_PathID']]=grupo
    malhas = []
    for pid, (go, W) in list(por_id.items()):
        if isinstance(pid, tuple): continue
        for c in go.m_Component:
            obj = c.component.deref()
            if obj.type.name != "SkinnedMeshRenderer" and obj.type.name != "MeshRenderer": continue
            r = obj.read()
            if obj.type.name == "MeshRenderer":
                filtro = next((cc.component.read() for cc in go.m_Component if cc.component.deref().type.name == 'MeshFilter'), None)
                if filtro is None: continue
                r = SimpleNamespace(m_Mesh=filtro.m_Mesh, m_Bones=[], m_GameObject=r.m_GameObject,
                                    m_Materials=r.m_Materials, m_Enabled=r.m_Enabled)
            if not r.m_Mesh.path_id: continue
            try:
                malhas.append(malha(r, go, por_id, pasta, feitas, prefab))
                malhas[-1]["grupo_cor"]=grupos.get(obj.path_id,"rendNormal")
                print("  ", go.m_Name, "ok", "ativo" if malhas[-1]["ativo"] else "inativo", len(malhas[-1]["shapes"]), "shapes")
            except Exception as e:
                raise RuntimeError("Falha ao extrair malha "+go.m_Name) from e
    implantes=[]
    objetos={v.path_id:v for v in env.objects}
    for o in env.objects:
        if o.type.name!='MonoBehaviour':continue
        tree=o.read_typetree()
        gp=tree.get('m_GameObject',{})
        if ('go',gp.get('m_PathID')) not in por_id or 'trfSrc' not in tree:continue
        src=tree['trfSrc'];dst=tree['trfDst']
        if src.get('m_FileID') or dst.get('m_FileID'):raise ValueError('Implante com referência externa ainda não resolvida')
        st=objetos[src['m_PathID']].read();dt=objetos[dst['m_PathID']].read()
        implantes.append({'origem':st.m_GameObject.read().m_Name,'destino':dt.m_GameObject.read().m_Name,
                         'pai_original':st.m_Father.read().m_GameObject.read().m_Name,
                         'semantica':'SetParent(destino,false): preserva TRS local'})
    return {"prefab": prefab, "bundle": bundle, "hierarquia": hier, "malhas": malhas, "componente":componente, 'implantes':implantes}

if __name__ == "__main__":
    pasta = sys.argv[1]
    os.makedirs(os.path.join(pasta, "malhas"), exist_ok=True)
    os.makedirs(os.path.join(pasta, "tex"), exist_ok=True)
    feitas = set(os.listdir(os.path.join(pasta, "tex")))
    pecas = []
    for arg in sys.argv[2:]:
        bundle, prefab = arg.rsplit(":", 1)
        print("==", prefab)
        pecas.append(extrair(pasta, bundle, prefab, feitas))
    json.dump({"pecas": pecas}, open(os.path.join(pasta, "cena.json"), "w"))
