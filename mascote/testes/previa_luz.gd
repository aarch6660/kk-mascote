extends SceneTree
# Mesma pose da captura do jogo (parada_espera_h), de frente, variando a luz direcional.
const LUZES := [[-6,0,true],[-8,-5,true],[-12,5,true]]

func _initialize() -> void: call_deferred("provar")

func provar() -> void:
	root.size = Vector2i(560,1000)
	var app = load("res://mascote.gd").new()
	app.roupas.relogio = func(): return {"hour":12,"weekday":1}
	app.prova = true
	app.cache = "/tmp/kk-previa-luz-%d.json" % OS.get_process_id()
	app.runtime = ""
	root.add_child(app)
	app.set_process(false)
	app.olhar.active = false
	for t in app.get_children():
		if t is Timer: t.stop()
	app.roupas_ocultas.clear(); app.registrar_roupas(); app.aplicar_roupas()
	app.sub.size = Vector2i(560,1000)
	app.sprite.position = Vector2(280,500)
	app.sprite.scale = Vector2.ONE
	app.camera.size = 1.8
	app.camera.position = Vector3(0,0.8,4)
	app.chika.rotation.y = 0.0
	var luz: DirectionalLight3D = app.find_children("*","DirectionalLight3D",true,false)[0]
	var anim: Animation = app.player.get_animation("parada_espera_h")
	for i in LUZES.size():
		var l = LUZES[i]
		luz.rotation_degrees = Vector3(l[0], l[1], 0)
		luz.shadow_enabled = l[2]
		app.player.play("parada_espera_h",0); app.player.seek(anim.length*0.5,true); app.player.pause()
		for k in 6: await process_frame
		RenderingServer.force_draw()
		root.get_texture().get_image().save_png(OS.get_environment("KK_PROVA_RETRATO").path_join("luz_%d.png" % i))
		print("LUZ ", i, " ", l)
	quit()
