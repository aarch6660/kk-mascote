extends SceneTree
# Prova privada da importação corporal: cada boneca vestida e sem roupas.

func _initialize() -> void: call_deferred("provar")

func foto(app, nome: String) -> void:
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
	root.get_texture().get_image().save_png(OS.get_environment("KK_PROVA_SAIDA").path_join(nome+".png"))

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
	app.fisica.fixa = true
	app.menu.hide()
	for b in app.bonecas:
		var id: String = b.id
		app.roupa_modo = "uniforme"
		if app.boneca == id: app.boneca = ""
		app.trocar_boneca(id)
		app.roupa_coordenada = 0
		app.recarregar_boneca()
		await foto(app, id+"-vestida")
		var todas: Array = []
		for tipo in app.pecas_roupa:
			if str(tipo).begins_with("roupa_"): todas.append(tipo)
		app.roupas_ocultas[id] = todas
		app.aplicar_roupas()
		await foto(app, id+"-sem-roupa")
		app.chika.rotation.y = 0.18
		app.roupas_ocultas[id] = []
		app.aplicar_roupas()
	quit(0)
