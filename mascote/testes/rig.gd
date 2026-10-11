extends SceneTree
func _initialize() -> void:
	call_deferred("provar")
func provar() -> void:
	var chika: Node3D = (load("res://bonecas/chika-haruno/saida/personagem.glb") as PackedScene).instantiate()
	root.add_child(chika)
	var sk: Skeleton3D = chika.find_children("*", "Skeleton3D", true, false)[0]
	var ausentes: Array = []
	var total := 0
	for arquivo in DirAccess.open("res://anims").get_files():
		if not arquivo.ends_with(".glb"): continue
		total += 1
		var cena: Node = (load("res://anims/"+arquivo) as PackedScene).instantiate()
		var ap: AnimationPlayer = cena.find_children("*", "AnimationPlayer", true, false)[0]
		for nome in ap.get_animation_list():
			if nome == "RESET": continue
			var anim := ap.get_animation(nome)
			for t in anim.get_track_count():
				var osso := str(anim.track_get_path(t)).get_slice(":",1)
				if sk.find_bone(osso)<0: ausentes.append([arquivo,osso])
		cena.free()
	var modifier = load("res://olhar.gd").new()
	sk.add_child(modifier)
	await process_frame
	modifier.perto = true
	modifier.alvo = Vector2(2,2)
	var cabeca := sk.find_bone("cf_j_head")
	var base := sk.get_bone_pose_rotation(cabeca)
	for _i in 600: modifier._process_modification()
	var delta := base.inverse() * sk.get_bone_pose_rotation(cabeca)
	var bounded := delta.get_angle()<0.6
	var shapes := 0
	for m in chika.find_children("*","MeshInstance3D",true,false):
		for i in m.mesh.get_blend_shape_count():
			if str(m.mesh.get_blend_shape_name(i))=="piscar": shapes+=1
	var resultado := {"clipes":total,"ossos":sk.get_bone_count(),"pistas_ausentes":ausentes,"piscar_malhas":shapes,"cabeca_limite_600_frames":bounded,"angulo_cabeca":delta.get_angle(),"olhos_encontrados":modifier.olhos.size()}
	var f:=FileAccess.open("res://evidencias/headless-rig.json",FileAccess.WRITE)
	f.store_string(JSON.stringify(resultado,"  "))
	print(JSON.stringify(resultado))
	chika.queue_free()
	quit(0 if ausentes.is_empty() and bounded and shapes>0 and modifier.olhos.size()==2 else 1)
