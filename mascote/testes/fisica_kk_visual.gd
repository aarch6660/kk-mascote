extends SceneTree
var app
var destino := ""
func _initialize() -> void:
	call_deferred("provar")
func capturar(nome: String) -> void:
	app.sk.force_update_all_bone_transforms()
	app.configurar_camera()
	app.posicionar()
	for f in 4: await process_frame
	app.atualizar_silhueta()
	app.posicionar()
	for f in 3: await process_frame
	RenderingServer.force_draw()
	var imagem := root.get_texture().get_image().get_region(Rect2i(480,40,960,1000))
	var preenchidos := 0
	for x in range(0,imagem.get_width(),8):
		for y in range(0,imagem.get_height(),8):
			if imagem.get_pixel(x,y).a>0.1: preenchidos += 1
	assert(preenchidos>20,"Captura sem mascote visível")
	imagem.save_png(destino.path_join(app.boneca+"-"+nome+".png"))
func provar() -> void:
	destino = OS.get_environment("KK_FISICA_VISUAL")
	assert(not destino.is_empty())
	root.size = Vector2i(1920,1080)
	app = load("res://mascote.gd").new()
	app.roupas.relogio = func(): return {"hour":12,"weekday":1}
	app.cache = OS.get_environment("KK_FISICA_CACHE")
	app.runtime = ""
	app.prova = true
	root.add_child(app)
	app.set_process(false)
	for n in app.get_children():
		if n is Timer: n.stop()
	app.retrato = false
	app.perfil = false
	app.zoom = 1.9
	app.fisica.fixa = true
	app.fisica.pos = Vector2(960,1000)
	app.roupas_ocultas = {} # Cache privado: capturas sempre com todas as peças.
	app.expressao = "Neutra"
	app.aplicar_render()
	var medidas: Array = []
	for b in app.bonecas:
		app.trocar_boneca(b.id)
		app.aplicar_roupas()
		app.olhar.active = false
		app.secundario.active = false
		app.dedos_mensagem.active = false
		app.secundario.maos_suaves = false
		app.secundario.dormindo = false
		app.secundario.pausado = false
		app.chika.rotation = Vector3.ZERO
		app.player.play("conversa_03")
		app.player.seek(0.6,true)
		app.player.pause()
		app.secundario.ligado = false
		app.secundario.atualizar(1.0/30)
		await capturar("base")
		app.secundario.ligado = true
		app.secundario.active = true
		app.player.play("conversa_03")
		var passos_antes: int = app.secundario.nativa.passos
		for f in 23:
			app.chika.rotation.y = sin(float(f)/45*PI)*0.4
			await process_frame
		await capturar("movimento")
		assert(app.secundario.nativa.passos>passos_antes,"Callback físico não executou no renderer")
		app.player.pause()
		app.chika.rotation.y = 0
		for f in 90: await process_frame
		await capturar("repouso")
		medidas.append({"boneca":b.id,"fisica":app.secundario.nativa.estado(),"roupas_ocultas":app.roupas_ocultas.get(b.id,[])})
	FileAccess.open(destino.path_join("visual.json"),FileAccess.WRITE).store_string(JSON.stringify({"passou":true,"capturas":9,"bonecas":medidas},"  "))
	print(JSON.stringify({"passou":true,"capturas":9}))
	quit()
