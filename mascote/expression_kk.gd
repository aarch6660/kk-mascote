extends SkeletonModifier3D
# ExpressionBone original após animação/olhar e antes do movimento secundário/física.
# Fonte/fórmulas reproduzíveis: personagem/auditar_expression.py e EXPRESSION-KK.md.
var ligado := true
var dados: Dictionary = {}
var ossos: Dictionary = {}
var habilitados: Dictionary = {}
var avisos: Array = []
var bases: Dictionary = {}
var ultimos: Dictionary = {}
var rotacoes_bases: Dictionary = {}
var rotacoes_ultimas: Dictionary = {}
var indices: Array = []
var calculo
var formula = preload("res://expression_kk_formula.gd").new()

class Osso extends RefCounted:
	var sk: Skeleton3D
	var i := -1
	var pai
	var local := Transform3D.IDENTITY
	var posicao_local: Vector3:
		get: return espelho(sk.get_bone_pose_position(i)) if i >= 0 else local.origin
		set(v):
			if i >= 0: sk.set_bone_pose_position(i,espelho(v))
			else: local.origin = v
	var rotacao_local: Quaternion:
		get: return espelho_q(sk.get_bone_pose_rotation(i)) if i >= 0 else local.basis.get_rotation_quaternion()
		set(v):
			if i >= 0: sk.set_bone_pose_rotation(i,espelho_q(v).normalized())
			else: local.basis = Basis(v).scaled_local(escala_local)
	var escala_local: Vector3:
		get: return sk.get_bone_pose_scale(i) if i >= 0 else local.basis.get_scale()
		set(v):
			if i >= 0: sk.set_bone_pose_scale(i,v)
			else: local.basis = Basis(rotacao_local).scaled_local(v)
	var posicao: Vector3:
		get: return frame().origin
		set(v): posicao_local = pai.frame().affine_inverse()*v if pai != null else v
	var rotacao: Quaternion:
		get:
			# Transform.rotation do Unity não herda cisalhamento de escalas desiguais.
			if i >= 0:
				var q := Quaternion.IDENTITY
				var atual := i
				while atual >= 0:
					q = sk.get_bone_pose_rotation(atual)*q
					atual = sk.get_bone_parent(atual)
				return espelho_q(q.normalized())
			return (pai.rotacao*rotacao_local).normalized() if pai != null else rotacao_local
		set(v): rotacao_local = (pai.rotacao.inverse()*v).normalized() if pai != null else v
	static func espelho(v: Vector3) -> Vector3: return Vector3(-v.x,v.y,v.z)
	static func espelho_q(q: Quaternion) -> Quaternion: return Quaternion(q.x,-q.y,-q.z,q.w)
	func frame() -> Transform3D:
		if i >= 0:
			var t := sk.get_bone_global_pose(i)
			var s := Basis(Vector3(-1,0,0),Vector3.UP,Vector3.BACK)
			return Transform3D(s*t.basis*s,espelho(t.origin))
		return pai.frame()*local if pai != null else local
	func inverter_ponto(v: Vector3) -> Vector3: return frame().affine_inverse()*v
	func transladar(v: Vector3) -> void:
		# Translate(Space.Self) usa rotação mundial; não multiplica a distância pela escala.
		posicao += rotacao*v
	func definir_eixo(campo: String, eixo: int, valor: float) -> void:
		var v: Vector3 = get(campo)
		v[eixo] = valor
		set(campo,v)
	func definir_rotacao_x(x: float) -> void:
		# SetLocalRotationX conserva Y/Z de Quaternion.eulerAngles (Unity Y*X*Z).
		var v := Basis(rotacao_local).get_euler(EULER_ORDER_YXZ)*180.0/PI
		rotacao_local = Quaternion(Vector3.UP,deg_to_rad(v.y))*Quaternion(Vector3.RIGHT,deg_to_rad(x))*Quaternion(Vector3.BACK,deg_to_rad(v.z))

func configurar(caminho: String) -> void:
	restaurar()
	dados.clear()
	ossos.clear()
	indices.clear()
	avisos.clear()
	var conteudo = JSON.parse_string(FileAccess.get_file_as_string(caminho))
	if not conteudo is Dictionary or int(conteudo.get("version",0)) != 1:
		avisos.append("Dados Expression ausentes/inválidos: "+caminho)
		return
	dados = conteudo
	var sk := get_skeleton()
	for ref in dados.references:
		if ref.get("virtual",false): continue
		var i := sk.find_bone(str(ref.name))
		if i < 0:
			avisos.append("Osso Expression ausente: "+str(ref.name))
			ossos[ref.name] = null
			continue
		var osso := Osso.new()
		osso.sk = sk
		osso.i = i
		ossos[ref.name] = osso
	for ref in dados.references:
		if not ref.get("virtual",false): continue
		var osso := Osso.new()
		# cf_j_shoulder não está na enum BoneName, mas é pai dos goals criados
		# em Initialize. Resolve o pai no rig, sem acrescentá-lo às 62 referências.
		var indice_pai := sk.find_bone(str(ref.parent))
		if indice_pai >= 0:
			var pai := Osso.new()
			pai.sk = sk
			pai.i = indice_pai
			osso.pai = pai
		var p: Array = ref.local_position_unity
		osso.posicao_local = Vector3(p[0],p[1],p[2])
		ossos[ref.name] = osso if osso.pai != null else null
		if osso.pai == null: avisos.append("Pai do alvo virtual ausente: "+str(ref.parent))
	for nome in dados.targets:
		if ossos.get(nome) != null: indices.append(ossos[nome].i)
	calculo = Osso.new()

func _process_modification_with_delta(_delta: float) -> void: atualizar()

func restaurar() -> void:
	var sk := get_skeleton()
	if sk == null: return
	# O Godot retira os modifiers após skinning; isto também permite ensaios manuais
	# e animações pausadas, sem realimentar nossas próprias correções.
	for i in ultimos:
		if sk.get_bone_pose_position(i).is_equal_approx(ultimos[i].origin): sk.set_bone_pose_position(i,bases[i].origin)
		if sk.get_bone_pose_rotation(i).is_equal_approx(rotacoes_ultimas[i]): sk.set_bone_pose_rotation(i,rotacoes_bases[i])
		if sk.get_bone_pose_scale(i).is_equal_approx(ultimos[i].basis.get_scale()): sk.set_bone_pose_scale(i,bases[i].basis.get_scale())
	ultimos.clear()
	bases.clear()
	rotacoes_bases.clear()
	rotacoes_ultimas.clear()

func atualizar() -> void:
	restaurar()
	if not ligado or dados.is_empty(): return
	var sk := get_skeleton()
	for i in indices:
		bases[i] = sk.get_bone_pose(i)
		rotacoes_bases[i] = sk.get_bone_pose_rotation(i)
	formula.aplicar(self)
	for i in indices:
		ultimos[i] = sk.get_bone_pose(i)
		rotacoes_ultimas[i] = sk.get_bone_pose_rotation(i)

static func sinal(v: float) -> float: return 1.0 if v >= 0 else -1.0
static func angulo(a: Vector3, b: Vector3) -> float:
	var denominador := sqrt(a.length_squared()*b.length_squared())
	return rad_to_deg(acos(clampf(a.dot(b)/denominador,-1,1))) if denominador > 0.000000000000001 else 0.0
static func quaternion(ordem: int, v: Vector3) -> Quaternion:
	var x := Quaternion(Vector3.RIGHT,deg_to_rad(v.x))
	var y := Quaternion(Vector3.UP,deg_to_rad(v.y))
	var z := Quaternion(Vector3.BACK,deg_to_rad(v.z))
	assert(ordem in [3,4,5])
	if ordem == 3: return (y*z*x).normalized()
	if ordem == 4: return (z*x*y).normalized()
	return (z*y*x).normalized()
static func euler(ordem: int, q: Quaternion) -> Vector3:
	# ConvertRadianFromMatrix 0x06004747: limiar assimétrico original (> +0,9999).
	var m := Basis(q)
	var v := Vector3.ZERO
	if ordem == 3:
		v.z = asin(clampf(m.x.y,-1,1))
		if m.x.y > 0.9998999834060669:
			v.y = atan2(m.z.x,m.z.z)
		else:
			v.x = atan2(-m.z.y,m.y.y)
			v.y = atan2(-m.x.z,m.x.x)
	elif ordem == 4:
		v.x = asin(clampf(m.y.z,-1,1))
		if m.y.z > 0.9998999834060669:
			v.z = atan2(m.x.y,m.x.x)
		else:
			v.y = atan2(-m.x.z,m.z.z)
			v.z = atan2(-m.y.x,m.y.y)
	else:
		assert(ordem == 5)
		v.y = asin(clampf(-m.x.z,-1,1))
		if -m.x.z > 0.9998999834060669:
			v.z = atan2(-m.y.x,m.y.y)
		else:
			v.x = atan2(m.y.z,m.z.z)
			v.z = atan2(m.x.y,m.x.x)
	for i in 3:
		if is_nan(v[i]): v[i] = 0.0
	return v*57.295780181884766
