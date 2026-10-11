extends SceneTree

func _initialize():
	var relatorio = []
	for caminho in ["res://personagem.glb", "res://personagem_idle.glb"]:
		var cena = load(caminho) as PackedScene
		assert(cena != null, "GLB não importado")
		var raiz = cena.instantiate()
		get_root().add_child(raiz)
		var skeletons = raiz.find_children("*", "Skeleton3D", true, false)
		assert(skeletons.size() == 1, "Esqueleto deve ser único")
		var sk = skeletons[0] as Skeleton3D
		var meshes = raiz.find_children("*", "MeshInstance3D", true, false)
		var shapes = 0
		var materiais = 0
		for mesh in meshes:
			shapes += mesh.mesh.get_blend_shape_count()
			materiais += mesh.mesh.get_surface_count()
		assert(sk.find_bone("cf_j_hips") >= 0)
		assert(sk.find_bone("cf_J_FaceBase") >= 0)
		assert(shapes > 200, "Expressões devem estar preservadas")
		var item = {"arquivo": caminho, "ossos": sk.get_bone_count(), "malhas": meshes.size(), "shape_keys": shapes, "superficies": materiais}
		if caminho.contains("idle"):
			var players = raiz.find_children("*", "AnimationPlayer", true, false)
			assert(players.size() == 1)
			var player = players[0] as AnimationPlayer
			var nome = ""
			for candidato in player.get_animation_list():
				if candidato != "RESET": nome = candidato
			assert(nome != "")
			player.play(nome)
			player.advance(0.0)
			var osso = sk.find_bone("cf_j_hand_L")
			var inicio = sk.get_bone_pose_rotation(osso)
			player.advance(0.6)
			var depois = sk.get_bone_pose_rotation(osso)
			item["animacao"] = nome
			item["pistas"] = player.get_animation(nome).get_track_count()
			item["mao_variou"] = not inicio.is_equal_approx(depois)
			assert(item["mao_variou"], "O idle deve movimentar os ossos")
		relatorio.append(item)
		raiz.queue_free()
	var arquivo = FileAccess.open("res://../saida/validacao_godot.json", FileAccess.WRITE)
	arquivo.store_string(JSON.stringify(relatorio, "\t"))
	print(JSON.stringify(relatorio))
	quit(0)
