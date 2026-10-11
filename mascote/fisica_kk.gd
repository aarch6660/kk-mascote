extends RefCounted
# Adaptação das cadeias DynamicBone cotidianas. A fonte acompanha cada card.
# Partículas vivem em mundo; os transforms da animação são amostrados sem a
# correção anterior, inclusive quando o modelo inteiro gira.
var dados: Dictionary = {}
var cadeias: Array = []
var ossos: Dictionary = {}
var bases: Dictionary = {}
var ultimos: Dictionary = {}
var avisos: Array = []
var passos := 0
var colisoes := 0

func energia() -> float:
	var maior := 0.0
	for c in cadeias:
		if not c.pronta: continue
		for p in c.particulas:
			var velocidade: Vector3 = (Vector3(p.pos)-Vector3(p.prev))*float(c.rate)
			maior = maxf(maior,velocidade.length_squared())
	return maior
const Colisores = preload("res://colisores_kk.gd")

static func vetor_unity(v) -> Vector3:
	if v is Dictionary: return Vector3(-float(v.get("x",0)),float(v.get("y",0)),float(v.get("z",0)))
	return Vector3.ZERO

static func curva(curve: Dictionary, t: float) -> float:
	var keys: Array = curve.get("m_Curve",[])
	if keys.is_empty(): return 1.0
	if t <= float(keys[0].time): return float(keys[0].value)
	for j in range(1,keys.size()):
		var a: Dictionary = keys[j-1]
		var b: Dictionary = keys[j]
		if t > float(b.time): continue
		var h := float(b.time)-float(a.time)
		if h<=0: return float(b.value)
		var u := (t-float(a.time))/h
		if not is_finite(float(a.outSlope)) or not is_finite(float(b.inSlope)): return float(a.value)
		# Interpolação Hermite das AnimationCurves Unity (slopes por segundo).
		return (2*u*u*u-3*u*u+1)*float(a.value)+(u*u*u-2*u*u+u)*h*float(a.outSlope)+(-2*u*u*u+3*u*u)*float(b.value)+(u*u*u-u*u)*h*float(b.inSlope)
	return float(keys[-1].value)

func configurar(sk: Skeleton3D, caminho: String) -> void:
	dados = {}
	cadeias.clear()
	ossos.clear()
	bases.clear()
	ultimos.clear()
	avisos.clear()
	if not FileAccess.file_exists(caminho):
		avisos.append("Metadados de física ausentes: "+caminho)
		return
	var fonte = JSON.parse_string(FileAccess.get_file_as_string(caminho))
	if not fonte is Dictionary or fonte.get("version")!=1:
		avisos.append("Versão de física inválida: "+caminho)
		return
	dados = fonte
	for componente in dados.get("body_dynamic_bone_ver02",[]): adicionar_ver02(sk,componente)
	for parte in dados.get("selected_parts",[]):
		for componente in parte.get("dynamic_bones",[]):
			if componente.get("engine_type")=="DynamicBone": adicionar_classico(sk,componente,str(parte.slot))
			else: avisos.append("Componente secundário não suportado: "+str(componente.get("engine_type")))

func adicionar_ver02(sk: Skeleton3D, fonte: Dictionary) -> void:
	var padroes: Array = fonte.get("patterns",[])
	if padroes.is_empty(): return
	var no := clampi(int(fonte.get("ptn_no",0)),0,padroes.size()-1)
	var padrao: Dictionary = padroes[no]
	var c := {"tipo":"DynamicBone_Ver02","slot":"corpo","fonte":fonte,"particulas":[],"tempo":0.0,"pronta":false,"rate":maxf(1,float(fonte.update_rate_hz)),"max_passos":maxi(1,int(fonte.heavy_loop_max_count)),"reflect":float(fonte.reflect_speed),"component":sk.find_bone(str(fonte.root_transform.get("name",""))),"gravidade":vetor_unity(padrao.gravity_unity),"forca":vetor_unity(fonte.force_unity),"freeze":0,"peso":1.0}
	c.colisores = preparar_colisores(sk,fonte.get("colliders",[]))
	var overrides: Dictionary = dados.get("runtime_overrides",{}).get("bust",{})
	var busto := str(fonte.bone_transforms[0].get("name","")).begins_with("cf_j_bust")
	if busto and no==0 and not overrides.is_empty(): c.gravidade = vetor_unity(overrides.gravity_unity)
	for original in padrao.particles:
		var p: Dictionary = original.duplicate(true)
		p.i = -1 if p.is_terminal else sk.find_bone(str(p.name))
		if not p.is_terminal and p.i<0:
			avisos.append("Osso corporal não exportado: "+str(p.name))
			return
		p.pai = int(p.parent_index)
		p.terminal = p.is_terminal
		p.rotacao = p.is_rotation_calc
		p.pos = Vector3.ZERO
		p.prev = Vector3.ZERO
		p.radius = maxf(0,float(p.collision_radius_unity))
		p.local = vetor_unity(p.local_position_unity)
		if p.pai>=0 and not p.terminal:
			var pai: Dictionary = c.particulas[p.pai]
			p.local = sk.get_bone_global_pose(pai.i).affine_inverse()*sk.get_bone_global_pose(p.i).origin
		for campo in ["damping","elasticity","stiffness","inert"]:
			p[campo] = clampf(float(overrides[campo]) if busto and no==0 and overrides.has(campo) else float(p[campo]),0,1)
		c.particulas.append(p)
	for p in c.particulas:
		if p.i>=0: ossos[p.i] = true
	cadeias.append(c)

func adicionar_classico(sk: Skeleton3D, fonte: Dictionary, slot: String) -> void:
	var raiz := sk.find_bone(str(fonte.root_transform.get("name","")))
	if raiz<0:
		avisos.append("Raiz de física não exportada: "+str(fonte.root_transform.get("name")))
		return
	var cfg: Dictionary = fonte.serialized_parameters
	# Referências ainda não resolvidas são declaradas, nunca associadas por chute.
	if not cfg.get("Exclusions",[]).is_empty() and not fonte.get("effective_chain",{}).get("resolved",false):
		avisos.append("Exclusions sem nomes resolvidos em "+str(fonte.component_path_id))
		return
	var c := {"tipo":"DynamicBone","slot":slot,"fonte":fonte,"parametros":cfg,"particulas":[],"tempo":0.0,"pronta":false,"rate":maxf(1,float(cfg.get("UpdateRate",60))),"max_passos":3,"reflect":1.0,"component":sk.find_bone(str(fonte.component_game_object)),"gravidade":vetor_unity(cfg.get("Gravity",{})),"forca":vetor_unity(cfg.get("Force",{})),"freeze":int(cfg.get("FreezeAxis",0)),"peso":1.0}
	c.colisores = preparar_colisores(sk,fonte.get("runtime_colliders",fonte.get("colliders",[])))
	if fonte.get("effective_chain",{}).get("resolved",false):
		for original in fonte.effective_chain.effective_particles:
			var i := sk.find_bone(str(original.transform.get("name","")))
			if i<0:
				avisos.append("Partícula não exportada: "+str(original.transform.get("name")))
				return
			var pai := int(original.parent_index)
			var d := float(c.particulas[pai].distancia)+(sk.get_bone_global_pose(i).origin-sk.get_bone_global_pose(c.particulas[pai].i).origin).length() if pai>=0 else 0.0
			c.particulas.append({"i":i,"pai":pai,"distancia":d,"local":sk.get_bone_pose_position(i),"pos":Vector3.ZERO,"prev":Vector3.ZERO,"rotacao":true,"terminal":false})
	else: adicionar_descendentes(sk,c,raiz,-1,0.0)
	var total := 0.0
	for p in c.particulas: total = maxf(total,float(p.distancia))
	for p in c.particulas:
		var t := float(p.distancia)/total if total>0 else 0.0
		for campo in ["Damping","Elasticity","Stiffness","Inert","Radius"]:
			p[campo.to_lower()] = float(cfg.get(campo,0))*curva(cfg.get(campo+"Distrib",{}),t)
		for campo in ["damping","elasticity","stiffness","inert"]: p[campo] = clampf(p[campo],0,1)
		p.radius = maxf(0,p.radius)
		ossos[p.i] = true
	cadeias.append(c)

func adicionar_descendentes(sk: Skeleton3D, c: Dictionary, i: int, pai: int, distancia: float) -> void:
	var idx: int = c.particulas.size()
	var local := sk.get_bone_pose_position(i)
	var d := distancia+((sk.get_bone_global_pose(i).origin-sk.get_bone_global_pose(c.particulas[pai].i).origin).length() if pai>=0 else 0.0)
	c.particulas.append({"i":i,"pai":pai,"distancia":d,"local":local,"pos":Vector3.ZERO,"prev":Vector3.ZERO,"rotacao":true,"terminal":false})
	for filho in sk.get_bone_children(i): adicionar_descendentes(sk,c,filho,idx,d)
	# Os cards atuais não usam EndLength/EndOffset no tipo clássico.
	if sk.get_bone_children(i).is_empty() and (float(c.parametros.get("EndLength",0))>0 or vetor_unity(c.parametros.get("EndOffset",{}))!=Vector3.ZERO):
		avisos.append("EndLength/EndOffset clássico ainda não suportado: "+sk.get_bone_name(i))

func restaurar(sk: Skeleton3D) -> void:
	for i in ultimos:
		var atual := sk.get_bone_pose(i)
		var ultimo: Transform3D = ultimos[i]
		var base: Transform3D = bases[i]
		# O AnimationMixer pode atualizar posição e rotação separadamente.
		if atual.origin.is_equal_approx(ultimo.origin): sk.set_bone_pose_position(i,base.origin)
		if atual.basis.get_rotation_quaternion().is_equal_approx(ultimo.basis.get_rotation_quaternion()): sk.set_bone_pose_rotation(i,base.basis.get_rotation_quaternion())
	ultimos.clear()
	bases.clear()

func reiniciar() -> void:
	for c in cadeias:
		c.pronta = false
		c.tempo = 0.0

func preparar_colisores(sk: Skeleton3D, fontes: Array) -> Array:
	var resolvidos: Array = []
	for fonte in fontes:
		var i := sk.find_bone(str(fonte.get("game_object","")))
		if i<0:
			avisos.append("Colisor não exportado: "+str(fonte.get("game_object","")))
			continue
		if not fonte.get("enabled",false): continue
		resolvidos.append({"i":i,"centro":vetor_unity(fonte.center_local_unity),"raio":maxf(0,float(fonte.radius_unity)),"altura":maxf(0,float(fonte.height_unity)),"eixo":int(fonte.direction_enum),"dentro":int(fonte.bound_enum)==1})
	return resolvidos

func colidir(pos: Vector3, raio_particula: float, colisor: Dictionary, frame: Transform3D) -> Vector3:
	var escala := frame.basis.x.length()
	var raio := maxf(0,float(colisor.raio)*escala+(-raio_particula if colisor.dentro else raio_particula))
	var metade := float(colisor.altura)*0.5-float(colisor.raio)
	if metade<=0: return Colisores.esfera(pos,frame*Vector3(colisor.centro),raio,colisor.dentro)
	var eixo := Vector3.ZERO
	eixo[int(colisor.eixo)] = metade
	return Colisores.capsula(pos,frame*(Vector3(colisor.centro)-eixo),frame*(Vector3(colisor.centro)+eixo),raio,colisor.dentro)

func amostrar(sk: Skeleton3D, c: Dictionary) -> Array:
	var frames: Array = []
	for p in c.particulas:
		if p.i>=0: frames.append(sk.global_transform*sk.get_bone_global_pose(p.i))
		else:
			var pai: Transform3D = frames[p.pai]
			frames.append(Transform3D(pai.basis,pai*p.local))
	return frames

func atualizar(sk: Skeleton3D, dt: float, impulso: Vector3) -> void:
	if dt<=0: return
	for c in cadeias:
		var frames := amostrar(sk,c)
		var objeto := sk.global_transform*sk.get_bone_global_pose(c.component) if c.component>=0 else sk.global_transform
		var frames_colisores: Array = []
		for colisor in c.colisores: frames_colisores.append(sk.global_transform*sk.get_bone_global_pose(colisor.i))
		if not c.pronta:
			for j in frames.size():
				c.particulas[j].pos = frames[j].origin
				c.particulas[j].prev = frames[j].origin
			c.frames = frames
			c.objeto = objeto
			c.objeto_passo = objeto
			c.gravidade_local = Transform3D(frames[0]).basis.orthonormalized().inverse()*Vector3(c.gravidade)
			c.frames_colisores = frames_colisores
			c.pronta = true
		var h := 1.0/float(c.rate)
		var anterior := float(c.tempo)
		c.tempo += dt
		var quantidade := mini(int(floor((float(c.tempo)+0.00000001)/h)),int(c.max_passos))
		for j in quantidade:
			var t := clampf((h-anterior+j*h)/dt,0,1)
			var alvos: Array = []
			for k in frames.size(): alvos.append(Transform3D(c.frames[k]).interpolate_with(frames[k],t))
			var obj: Transform3D = Transform3D(c.objeto).interpolate_with(objeto,t)
			var colisores_alvo: Array = []
			for k in frames_colisores.size(): colisores_alvo.append(Transform3D(c.frames_colisores[k]).interpolate_with(frames_colisores[k],t))
			passo(c,alvos,obj,impulso,colisores_alvo)
			c.tempo -= h
			passos += 1
		if quantidade>=int(c.max_passos): c.tempo = 0.0
		c.frames = frames
		c.objeto = objeto
		c.frames_colisores = frames_colisores
		aplicar(sk,c,frames)

func passo(c: Dictionary, frames: Array, objeto: Transform3D, impulso: Vector3, frames_colisores: Array = []) -> void:
	var escala := objeto.basis.x.length()
	var movimento: Vector3 = objeto.origin-Transform3D(c.objeto_passo).origin
	c.objeto_passo = objeto
	var gravidade: Vector3 = c.gravidade
	if c.tipo=="DynamicBone" and gravidade.length_squared()>0:
		var g := gravidade.normalized()
		var local: Vector3 = Transform3D(frames[0]).basis.orthonormalized()*Vector3(c.gravidade_local)
		gravidade -= g*maxf(local.dot(g),0)
	var forca: Vector3 = (gravidade+Vector3(c.forca))*escala
	# Arrasto 2D não desloca o modelo 3D; este acoplamento é próprio da mascote.
	forca += impulso*0.003
	for p in c.particulas:
		if p.pai<0:
			p.prev = p.pos
			p.pos = frames[0].origin
			continue
		var v: Vector3 = (Vector3(p.pos)-Vector3(p.prev))*float(c.reflect)
		var deslocamento := movimento*float(p.inert)
		p.prev = Vector3(p.pos)+deslocamento
		p.pos = Vector3(p.pos)+v*(1-float(p.damping))+forca+deslocamento
	for j in range(1,c.particulas.size()):
		var p: Dictionary = c.particulas[j]
		var pai: Dictionary = c.particulas[p.pai]
		var alvo: Vector3 = Vector3(pai.pos)+(Transform3D(frames[j]).origin-Transform3D(frames[p.pai]).origin)
		var comprimento := (Transform3D(frames[j]).origin-Transform3D(frames[p.pai]).origin).length()
		if c.tipo=="DynamicBone_Ver02":
			alvo = Vector3(pai.pos)+Transform3D(frames[p.pai]).basis*Vector3(p.local)
			if p.terminal: comprimento = Vector3(p.local).length()*escala
		var rigidez := lerpf(1,float(p.stiffness),float(c.peso))
		p.pos = Vector3(p.pos)+(alvo-Vector3(p.pos))*float(p.elasticity)
		var delta: Vector3 = alvo-Vector3(p.pos)
		var limite := comprimento*(1-rigidez)*2
		if rigidez>0 and delta.length()>limite and delta.length()>0: p.pos = Vector3(p.pos)+delta*(1-limite/delta.length())
		for k in c.colisores.size():
			var resultado := colidir(p.pos,float(p.radius)*escala,c.colisores[k],frames_colisores[k])
			if not resultado.is_equal_approx(p.pos): colisoes += 1
			p.pos = resultado
		if int(c.freeze)>0:
			var normal: Vector3 = Transform3D(frames[p.pai]).basis[int(c.freeze)-1].normalized()
			p.pos = Vector3(p.pos)-normal*(Vector3(p.pos)-Vector3(pai.pos)).dot(normal)
		var direcao: Vector3 = Vector3(pai.pos)-Vector3(p.pos)
		if direcao.length()>0:
			var fracao := (direcao.length()-comprimento)/direcao.length()
			var permitida := clampf(fracao,float(p.keep_length_fraction_min),float(p.keep_length_fraction_max)) if c.tipo=="DynamicBone_Ver02" else 0.0
			p.pos = Vector3(p.pos)+direcao*(fracao-permitida)
		if c.tipo=="DynamicBone_Ver02" and p.is_move_limit and p.i>=0:
			var frame: Transform3D = frames[j]
			frame.origin = alvo
			var local: Vector3 = frame.affine_inverse()*Vector3(p.pos)
			var a := vetor_unity(p.move_limit_min_local)
			var b := vetor_unity(p.move_limit_max_local)
			p.pos = frame*local.clamp(a.min(b),a.max(b))

func aplicar(sk: Skeleton3D, c: Dictionary, frames: Array) -> void:
	for j in range(1,c.particulas.size()):
		var p: Dictionary = c.particulas[j]
		var pai: Dictionary = c.particulas[p.pai]
		var i: int = pai.i
		var filhos := 0
		for outro in c.particulas:
			if outro.pai==p.pai: filhos += 1
		if i>=0 and filhos==1 and pai.rotacao:
			var mundo: Transform3D = sk.global_transform*sk.get_bone_global_pose(i)
			var de: Vector3 = (sk.global_transform*sk.get_bone_global_pose(p.i)).origin-mundo.origin if p.i>=0 else mundo.basis*Vector3(p.local)
			if c.tipo=="DynamicBone_Ver02": de = mundo.basis.orthonormalized()*Vector3(p.local)
			var para: Vector3 = Vector3(p.pos)-Vector3(pai.pos)
			if c.tipo=="DynamicBone_Ver02" and Vector3(p.local).length()>0: para -= de*(1-float(pai.next_bone_length_scale))
			if de.length_squared()>0.0000000001 and para.length_squared()>0.0000000001:
				lembrar(sk,i)
				var correção := Quaternion(de.normalized(),para.normalized())
				var avô := sk.get_bone_parent(i)
				var base_pai := sk.global_transform*sk.get_bone_global_pose(avô) if avô>=0 else sk.global_transform
				sk.set_bone_pose_rotation(i,(base_pai.basis.orthonormalized().get_rotation_quaternion().inverse()*correção*mundo.basis.orthonormalized().get_rotation_quaternion()).normalized())
		if p.i>=0:
			lembrar(sk,p.i)
			var avô := sk.get_bone_parent(p.i)
			var base_pai := sk.global_transform*sk.get_bone_global_pose(avô) if avô>=0 else sk.global_transform
			sk.set_bone_pose_position(p.i,base_pai.affine_inverse()*Vector3(p.pos))
	for i in bases: ultimos[i] = sk.get_bone_pose(i)

func lembrar(sk: Skeleton3D, i: int) -> void:
	if not bases.has(i): bases[i] = sk.get_bone_pose(i)

func estado() -> Dictionary:
	var n := 0
	for c in cadeias: n += c.particulas.size()
	var ligados := 0
	for c in cadeias: ligados += c.colisores.size()
	return {"cadeias":cadeias.size(),"particulas":n,"passos":passos,"colisores_vinculados":ligados,"colisoes":colisoes,"avisos":avisos.duplicate(),"motor":"DynamicBone/DynamicBone_Ver02 adaptados"}
