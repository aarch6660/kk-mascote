extends SceneTree
# Prancha dos cinco clipes novos e da pose assistindo no mascote real.
const NOMES := ["gesto_ajeitar_cabelo","gesto_mao_boca","gesto_olhar_longe","gesto_maos_juntas","gesto_reverencia","assistindo"]
var app: Node2D

func _initialize() -> void: call_deferred("provar")

func capturar(nome: String) -> void:
	for i in 6: await process_frame
	RenderingServer.force_draw()
	var erro := root.get_texture().get_image().save_png(OS.get_environment("KK_PROVA_RETRATO").path_join(nome))
	if erro != OK:
		push_error("Captura falhou: "+nome)
		quit(1)

func provar() -> void:
	root.size = Vector2i(560,1000)
	app = load("res://mascote.gd").new()
	app.roupas.relogio = func(): return {"hour":12,"weekday":1}
	app.prova = true
	app.cache = OS.get_environment("KK_PROVA_CACHE")
	app.runtime = ""
	root.add_child(app)
	app.set_process(false)
	app.olhar.active = false
	app.secundario.active = false
	for t in app.get_children():
		if t is Timer: t.stop()
	app.roupas_ocultas.clear()
	app.registrar_roupas()
	app.aplicar_roupas()
	app.sub.size = Vector2i(560,1000)
	app.sprite.position = Vector2(280,500)
	app.sprite.scale = Vector2.ONE
	app.camera.size = 1.9
	app.camera.position = Vector3(0,0.8,4)
	app.chika.rotation.y = 0.35
	for nome in NOMES:
		var clipe: String = nome
		if nome == "assistindo":
			app.estados.mudar("parada")
			app.fisica.fixa = true
			app.contexto_hana = {"janela":{"categoria":"jogo","fullscreen":false,"at":[1100,100],"size":[700,600]},"musica":{}}
			app.atualizar_vida(0.1,true)
			app.atualizar_olhar()
			app.olhar.active = true
			clipe = app.estados.clipe
		var anim: Animation = app.player.get_animation(clipe)
		for k in 3:
			app.player.play(clipe,0)
			app.player.seek(anim.length*[0.12,0.4,0.72][k],true)
			app.player.pause()
			await capturar("%s_%d.png" % [nome,k])
		print("CAPTURA ",nome," ",clipe)
	quit()
