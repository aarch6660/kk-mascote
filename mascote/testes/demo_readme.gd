extends SceneTree
# Mídia do README (Xvnc privado, --fixed-fps 30): expressões, quadros de animação e roupas. Sempre vestidas.

var saida := ""

func _initialize() -> void: call_deferred("gravar")

func preparar(app, boneca: String, modo: String) -> void:
	app.roupa_modo = modo
	if app.boneca != boneca: app.trocar_boneca(boneca)
	app.roupa_coordenada = {"uniforme":0,"casual":5,"pijama":6}[modo]
	app.recarregar_boneca()
	app.sprite.position = Vector2(280,500)
	app.sprite.scale = Vector2.ONE
	app.olhar.active = false

func corpo(app) -> void:
	app.camera.size = 1.85
	app.camera.position = Vector3(0,0.82,4)

func rosto(app) -> void:
	app.camera.size = 0.36
	app.camera.position = Vector3(0,1.27,4)

func foto(nome: String) -> void:
	RenderingServer.force_draw()
	root.get_texture().get_image().save_png(saida.path_join(nome+".png"))

func gravar() -> void:
	saida = OS.get_environment("KK_DEMO_SAIDA")
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
	# Expressões: retrato da Chika de uniforme.
	preparar(app,"chika-haruno","uniforme")
	rosto(app)
	app.chika.rotation.y = 0.0
	app.player.play("parada_relaxada",0)
	app.player.seek(0.6,true)
	app.player.pause()
	var ordem := 0
	for e in ["Neutra","Encantada","Espanto","Gargalhada","Birra","Choro dramático","Pânico cômico","Vergonha fofa","Orgulho","Pensativa","Sorriso travesso","Piscadela direita"]:
		app.rosto.dinamica = 1.0
		var caricatos: Dictionary = app.rosto.CATALOGO.get("caricatos",{})
		app.efeitos.iniciar(str(caricatos.get(e,{}).get("efeito","nenhum")))
		for i in 30:
			app.rosto.aplicar(e,0.35 if e=="Gargalhada" else 0.0,"a",0,1.0/30)
			app.emocao_atual = e
			app.atualizar_efeitos(0.0)
			if i < 24: app.efeitos.passo(1.0/30)
			await process_frame
		foto("expr_%02d" % ordem)
		ordem += 1
	app.rosto.aplicar("Neutra",0,"",0,1)
	# Animações com física: corpo inteiro, 30 fps fixos.
	# README: só a Chika como modelo de demonstração (pedido do usuário).
	var clipes := {"chika-haruno":["gesto_ajeitar_cabelo","comemorar_02","conversa_gesto_03","gesto_olhar_longe","celular_em_pe"]}
	for b in clipes:
		preparar(app,b,"uniforme")
		corpo(app)
		app.chika.rotation.y = 0.25
		app.secundario.active = true
		for clipe in clipes[b]:
			if not app.player.has_animation(clipe): continue
			app.player.play(clipe,0)
			for i in 15: await process_frame
			app.player.seek(0,true)
			var n := mini(int(app.player.current_animation_length*30),150)
			for i in n:
				await process_frame
				foto("anim_%s_%s_%03d" % [b,clipe,i])
	quit(0)
