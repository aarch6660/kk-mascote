extends Node3D
# Smartphone original do jogo (action/mapitem p_o_koi_ei_smaho00), preso ao osso-âncora
# k_f_handL_00 como o jogo faz com os itens de ação: transformação identidade, segue o clipe.
const OSSO := "k_f_handL_00"
var anexo: BoneAttachment3D
var malha: MeshInstance3D
var material := StandardMaterial3D.new()
var brilho := 0.0

func _ready() -> void:
	material.albedo_texture = load("res://celular_jogo/mt_koi_ei_kagami00.png")
	material.emission_enabled = true
	material.emission_texture = load("res://celular_jogo/mt_koi_ei_kagami00_em.png")
	material.emission_energy_multiplier = 0.9
	visibility_changed.connect(_sincronizar)
	hide()

func _nova_malha() -> MeshInstance3D:
	var m := MeshInstance3D.new()
	m.mesh = load("res://celular_jogo/p_o_koi_ei_smaho00.obj")
	m.material_override = material
	m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# A tela é a face +Y da malha. O espelhamento de X (Unity → glTF) no esqueleto vira o item
	# preso ao osso: sem este giro de 180° no eixo comprido, ela olharia para a traseira.
	m.rotation = Vector3(0, 0, PI)
	return m

func _sincronizar() -> void:
	if is_instance_valid(anexo): anexo.visible = visible

func alinhar(sk: Skeleton3D, digitando: bool, tempo: float) -> void:
	# Troca de boneca libera o esqueleto antigo (e o anexo com a malha): refaz no novo.
	if not is_instance_valid(anexo) or anexo.get_parent() != sk:
		if sk.find_bone(OSSO) < 0:
			hide()
			return
		if is_instance_valid(anexo): anexo.queue_free()
		anexo = BoneAttachment3D.new()
		anexo.bone_name = OSSO
		malha = _nova_malha()
		anexo.add_child(malha)
		sk.add_child(anexo)
	anexo.visible = visible
	# Tela pisca de leve a cada toque enquanto ela digita.
	brilho = 0.9 + (0.25*maxf(0.0, sin(tempo*11.0)) if digitando else 0.0)
	material.emission_energy_multiplier = brilho

func tela_global() -> Vector3:
	return malha.global_position if is_instance_valid(malha) and malha.is_inside_tree() else global_position
