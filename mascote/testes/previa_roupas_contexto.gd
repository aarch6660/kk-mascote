extends SceneTree

func _initialize() -> void: call_deferred("provar")

func provar() -> void:
	root.size = Vector2i(560,1000)
	var app = load("res://mascote.gd").new()
	app.roupas.relogio = func(): return {"hour":12,"weekday":1}
	app.prova = true
	app.cache = OS.get_environment("KK_PROVA_CACHE")
	app.runtime = ""
	root.add_child(app)
	app.set_process(false)
	for t in app.get_children():
		if t is Timer: t.stop()
	app.roupas_ocultas = {}
	app.sub.size = Vector2i(560,1000)
	app.sprite.position = Vector2(280,500)
	app.sprite.scale = Vector2.ONE
	app.fisica.fixa = true
	app.menu.hide()
	for b in app.bonecas:
		app.roupa_modo = "uniforme"
		app.trocar_boneca(b.id)
		for modo in ["uniforme","casual","pijama"]:
			app.roupa_modo = modo
			app.mudar("parada",60)
			app.transicao_roupa = 0
			app.atualizar_roupa(2)
			app.atualizar_roupa(0.2)
			assert(app.roupa_atual().nome==modo)
			# A troca reposiciona no desktop; esta prova usa uma janela estreita própria.
			app.sprite.position = Vector2(280,500)
			app.sprite.scale = Vector2.ONE
			app.olhar.active = false
			app.secundario.active = false
			app.camera.size = 1.85
			app.camera.position = Vector3(0,0.82,4)
			app.chika.rotation.y = 0.18
			app.player.play("parada_relaxada",0)
			app.player.seek(0.6,true)
			app.player.pause()
			app.rosto.aplicar("Neutra",0,"",0,1)
			for i in 8: await process_frame
			RenderingServer.force_draw()
			root.get_texture().get_image().save_png(OS.get_environment("KK_PROVA_RETRATO").path_join(b.id+"-"+modo+".png"))
	quit(0)
