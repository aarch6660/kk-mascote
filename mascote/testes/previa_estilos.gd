extends SceneTree
# Retrato da Chika (uniforme) com fundo transparente: 1 quadro parado + sequência de 36 quadros (12 fps, piscada).
var app: Node2D
const T := 768

func _initialize() -> void: call_deferred("provar")

func salvar(nome: String) -> void:
	RenderingServer.force_draw()
	var img := root.get_texture().get_image()
	img.save_png(OS.get_environment("KK_PROVA_RETRATO").path_join(nome))

func provar() -> void:
	root.size = Vector2i(T,T)
	root.transparent_bg = true
	app = load("res://mascote.gd").new()
	app.roupas.relogio = func(): return {"hour":12,"weekday":1}
	app.prova = true
	app.cache = OS.get_environment("KK_PROVA_CACHE")
	app.runtime = ""
	root.add_child(app)
	app.set_process(false)
	app.olhar.active = false
	for t in app.get_children():
		if t is Timer: t.stop()
	app.roupas_ocultas.clear()
	app.registrar_roupas()
	app.aplicar_roupas()
	app.retrato = true
	app.moldura = false
	app.configurar_camera()
	app.camera.size = 0.56
	app.camera.position.y -= 0.06
	app.sub.size = Vector2i(T,T)
	app.sprite.position = Vector2(T/2,T/2)
	app.sprite.scale = Vector2.ONE
	var anim: Animation = app.player.get_animation("parada_relaxada")
	app.player.play("parada_relaxada",0)
	app.player.seek(anim.length*0.3,true)
	for i in 8: await process_frame
	salvar("base.png")
	# Sequência viva: clipe avançado à mão a 12 fps + piscada nos blend shapes (quadros 15–19).
	app.sub.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	var fecha := {15:0.5,16:1.0,17:1.0,18:0.6,19:0.2}
	for i in 36:
		app.player.seek(anim.length*0.3 + i/12.0, true)
		for p in app.piscadas: p[0].set_blend_shape_value(p[1], fecha.get(i, 0.0))
		for k in 3: await process_frame
		salvar("quadro_%02d.png" % i)
	quit()
