extends SceneTree
func _initialize():
	var personagem = load("res://personagem.glb").instantiate()
	var origem = load("res://clipe_idle.glb").instantiate()
	get_root().add_child(personagem)
	get_root().add_child(origem)
	var esqueleto = personagem.find_children("*", "Skeleton3D", true, false)[0] as Skeleton3D
	var original = origem.find_children("*", "AnimationPlayer", true, false)[0] as AnimationPlayer
	var nome = ""
	for candidato in original.get_animation_list():
		if candidato != "RESET": nome = candidato
	var animacao = original.get_animation(nome).duplicate(true)
	var player = AnimationPlayer.new()
	personagem.add_child(player)
	var lib = AnimationLibrary.new()
	lib.add_animation("idle_original", animacao)
	player.add_animation_library("", lib)
	# Só o caminho até o nó Skeleton3D muda entre as cenas importadas.
	# Mantém nome de osso, tipo, tempos e valores de todas as pistas.
	var caminho_sk = personagem.get_path_to(esqueleto)
	var ajustes = 0
	for i in animacao.get_track_count():
		var antigo = animacao.track_get_path(i)
		assert(antigo.get_subname_count() == 1)
		var novo = NodePath(str(caminho_sk) + ":" + antigo.get_subname(0))
		if antigo != novo: ajustes += 1
		animacao.track_set_path(i, novo)
	var ausentes = []
	for i in animacao.get_track_count():
		var caminho = animacao.track_get_path(i)
		var node = personagem.get_node_or_null(NodePath(caminho.get_concatenated_names()))
		if node == null: ausentes.append(str(caminho))
		elif caminho.get_subname_count() and node is Skeleton3D:
			if node.find_bone(caminho.get_subname(0)) < 0: ausentes.append(str(caminho))
	assert(ausentes.is_empty(), "Pistas do clipe original devem encaixar")
	player.play("idle_original")
	player.advance(0.0)
	var bone = esqueleto.find_bone("cf_j_hand_L")
	var antes = esqueleto.get_bone_pose_rotation(bone)
	player.advance(0.6)
	var variou = not antes.is_equal_approx(esqueleto.get_bone_pose_rotation(bone))
	assert(variou)
	var resultado = {"origem": "animacoes/exportados/idle_em_pe.glb", "pistas": animacao.get_track_count(), "caminhos_ausentes": ausentes, "sem_retarget_ossos": true, "pistas_com_caminho_do_no_ajustado": ajustes, "mao_variou": variou}
	var arquivo = FileAccess.open("res://../saida/reuso_clipe_godot.json", FileAccess.WRITE)
	arquivo.store_string(JSON.stringify(resultado,"\t"))
	print(JSON.stringify(resultado))
	quit(0)
