extends SceneTree
# Ensaio isolado, vestido, coordenada zero e câmera frontal fixa.
var medidas: Array = []
func _initialize() -> void: call_deferred("provar")
func captura(app, clipe: String, modo: String) -> void:
	for f in 4: await process_frame
	await RenderingServer.frame_post_draw
	var destino := OS.get_environment("KK_EXPRESSION_PROVA")
	app.sub.get_texture().get_image().save_png(destino.path_join(clipe+"-"+modo+".png"))
	var maos := {}
	for lado in ["L","R"]:
		var i: int = app.sk.find_bone("cf_j_hand_"+lado)
		var p: Vector3 = app.sk.get_bone_global_pose(i).origin
		var tela: Vector2 = app.camera.unproject_position(p)
		var normal: Vector3 = app.sk.get_bone_global_pose(i).basis.y.normalized()
		var auxiliares := {}
		for nome in ["cf_d_forearm02_","cf_d_wrist_"]:
			var j: int = app.sk.find_bone(nome+lado)
			var q: Quaternion = app.sk.get_bone_pose_rotation(j)
			if app.expression.active and app.expression.rotacoes_ultimas.has(j): q = app.expression.rotacoes_ultimas[j]
			auxiliares[nome+lado] = [q.x,q.y,q.z,q.w]
		maos[lado] = {"tela":[tela.x,tela.y],"auxiliares":auxiliares,"normal_local_y":[normal.x,normal.y,normal.z],"rotacao":[app.sk.get_bone_pose_rotation(i).x,app.sk.get_bone_pose_rotation(i).y,app.sk.get_bone_pose_rotation(i).z,app.sk.get_bone_pose_rotation(i).w]}
	medidas.append({"boneca":app.boneca,"coordenada":app.roupa_coordenada,"clipe":clipe,"modo":modo,"maos":maos})
func provar() -> void:
	root.size = Vector2i(900,1400)
	var app = load("res://mascote.gd").new()
	app.roupas.relogio = func(): return {"hour":12,"weekday":1}
	app.prova = true
	app.cache = "/tmp/kk-expression-visual-%d.json" % OS.get_process_id()
	app.runtime = ""
	root.add_child(app)
	app.set_process(false)
	for t in app.get_children():
		if t is Timer: t.stop()
	app.trocar_boneca("chika-haruno")
	assert(app.roupa_coordenada == 0)
	app.olhar.active = false
	app.secundario.active = false
	app.dedos_mensagem.active = false
	app.secundario.ligado = false
	app.roupas_ocultas[app.boneca] = []
	app.aplicar_roupas()
	app.sub.size = Vector2i(900,1400)
	app.camera.size = 1.95
	app.camera.position = Vector3(0,0.85,4)
	app.camera.rotation = Vector3.ZERO
	var expression = app.get("expression")
	if expression != null: expression.active = false
	var legado_script := GDScript.new()
	legado_script.source_code = FileAccess.get_file_as_string("res://evidencias/expression-kk/antes/movimento_secundario.gd")
	assert(legado_script.reload() == OK)
	var legado = legado_script.new()
	app.sk.add_child(legado)
	legado.active = false
	legado.ligado = false
	legado.configurar_maos(app.player)
	for clipe in ["parada_relaxada","parada_maos_atras","parada_timida","parada_balanco"]:
		app.secundario.maos_suaves = false
		app.secundario.repouso = false
		app.player.play(clipe)
		app.player.seek(0.6,true)
		app.player.pause()
		var originais := {}
		for i in app.sk.get_bone_count(): originais[i] = [app.sk.get_bone_pose_position(i),app.sk.get_bone_pose_rotation(i),app.sk.get_bone_pose_scale(i)]
		await captura(app,clipe,"sem-suavidade")
		legado.maos_suaves = true
		legado.repouso = true
		for f in 180: legado.atualizar(1.0/30)
		await captura(app,clipe,"antes")
		if clipe == "parada_maos_atras":
			app.camera.position.z = -4
			app.camera.rotation.y = PI
			await captura(app,clipe,"antes-traseira")
			app.camera.position.z = 4
			app.camera.rotation = Vector3.ZERO
		if expression != null:
			for i in originais:
				app.sk.set_bone_pose_position(i,originais[i][0])
				app.sk.set_bone_pose_rotation(i,originais[i][1])
				app.sk.set_bone_pose_scale(i,originais[i][2])
			app.secundario.maos_suaves = true
			app.secundario.repouso = true
			for f in 180: app.secundario.atualizar(1.0/30)
			expression.active = true
			await captura(app,clipe,"depois")
			if clipe == "parada_maos_atras":
				app.camera.position.z = -4
				app.camera.rotation.y = PI
				await captura(app,clipe,"depois-traseira")
				app.camera.position.z = 4
				app.camera.rotation = Vector3.ZERO
			expression.active = false
	# Regressão visual vestida das quatro bonecas na mesma pose e câmera.
	if expression != null:
		for b in app.bonecas:
			app.trocar_boneca(b.id)
			app.olhar.active = false
			app.secundario.active = false
			app.dedos_mensagem.active = false
			app.roupas_ocultas[app.boneca] = []
			app.aplicar_roupas()
			app.camera.size = 1.95
			app.camera.position = Vector3(0,0.85,4)
			app.camera.rotation = Vector3.ZERO
			app.player.play("parada_relaxada");app.player.seek(0.6,true);app.player.pause()
			await captura(app,b.id,"corpo")
	var destino := OS.get_environment("KK_EXPRESSION_PROVA")
	FileAccess.open(destino.path_join("capturas.json"),FileAccess.WRITE).store_string(JSON.stringify(medidas,"  "))
	quit()
