extends SceneTree
# Vídeo de prova (Xvnc privado, --fixed-fps 30): toque íntimo, "Ofegar agora" e crise aleatória.
# Sempre vestida. Grava quadros + log de áudio por quadro; testes/video_ofegar.py monta o MP4.

var saida := ""
var quadro := 0
var log_quadros: Array = []
var legenda := ""
var app

func _initialize() -> void: call_deferred("gravar")

func evento(ponto: Vector2, pressionado: bool) -> InputEventMouseButton:
	var e := InputEventMouseButton.new()
	e.button_index = MOUSE_BUTTON_LEFT
	e.position = ponto
	e.pressed = pressionado
	return e

func som(p) -> Dictionary:
	if not p.playing or p.stream == null: return {}
	var arquivo := str(p.dados.get("arquivo","")) if not p.dados.is_empty() else ""
	return {"arquivo":arquivo,"pos":p.get_playback_position(),"db":p.volume_db}

func passo() -> void:
	app._process(1.0/30)
	await process_frame
	RenderingServer.force_draw()
	var r := Rect2i(Vector2i(app.sprite.position-Vector2.ONE*app.TAM*app.zoom*0.5),Vector2i(Vector2.ONE*app.TAM*app.zoom))
	root.get_texture().get_image().get_region(r).save_png(saida.path_join("q%05d.png" % quadro))
	log_quadros.append({"q":quadro,"legenda":legenda,"boneca":app.boneca,"ofegar":som(app.ofegar),"reacao":som(app.sons_reacao),
		"emocao":app.emocao_atual,"ativo":app.ofegar.ativo(),"motivo":app.ofegar.motivo,
		"cabeca":[app.ponto_osso("cf_j_head").x-r.position.x, app.ponto_osso("cf_j_head").y-r.position.y,r.size.x]})
	quadro += 1

func esperar(segundos: float) -> void:
	for i in int(segundos*30): await passo()

func gravar() -> void:
	saida = OS.get_environment("KK_VIDEO_SAIDA")
	root.size = Vector2i(1920,1080)
	app = load("res://mascote.gd").new()
	app.roupas.relogio = func(): return {"hour":12,"weekday":1}
	app.cache = "/tmp/kk-video-ofegar-%d.json" % OS.get_process_id()
	app.runtime = ""
	app.prova = true
	root.add_child(app)
	app.set_process(false)
	for t in app.get_children():
		if t is Timer: t.stop()
	app.acao_menu("Modo retrato")
	app.zoom = 1.6
	app.fisica.pos = Vector2(960,1000)
	app.fisica.fixa = true
	app.expressao = "Automática"
	app.fala_automatica = false
	app.sons_ligados = true
	app.estilo_anime = true
	app.aplicar_render()
	app.roupas_ocultas = {}
	app.trocar_boneca("chika-haruno")
	app.ofegar_ligado = true
	app.ofegar.proximo_aleatorio = 9999
	app.ofegar.proximo_sem_roupa = 9999
	app.local_poly = PackedVector2Array([Vector2.ZERO,Vector2(448,0),Vector2(448,448),Vector2(0,448)])
	legenda = "Parada (respiração ofegante: ligada)"
	await esperar(2.5)
	# 1. Toque íntimo (apalpar o seio) por 4 s, depois solta: continua ~8 s e sai em fade.
	app.modo_toque = "Apalpar"
	var ponto: Vector2 = app.ponto_osso("cf_j_bust03_L")
	legenda = "Toque: " + str(app.localizar_toque(ponto).get("regiao","?"))
	app._input(evento(ponto,true))
	for i in 120:
		var m := InputEventMouseMotion.new()
		m.position = ponto + Vector2(6*sin(i*0.25), 4*cos(i*0.2))
		app._input(m)
		await passo()
	app._input(evento(ponto,false))
	legenda = "Soltou: continua ofegando e para sozinha"
	while app.ofegar.ativo(): await passo()
	legenda = "Calma de novo"
	await esperar(2.0)
	# 2. Comando do menu.
	legenda = "Menu: Ofegar agora"
	app.acao_menu("Ofegar agora")
	await esperar(9.0)
	app.ofegar.restante = minf(app.ofegar.restante, 0.1)
	while app.ofegar.ativo(): await passo()
	await esperar(1.5)
	# 3. Outra boneca: crise aleatória "do nada".
	app.trocar_boneca("mizuno-ayaka")
	app.ofegar.proximo_aleatorio = 1.0
	app.ofegar.proximo_sem_roupa = 9999
	legenda = "Ayaka: parada..."
	await esperar(1.2)
	legenda = "Crise aleatória (do nada)"
	await esperar(8.0)
	legenda = "Menu: Respiração ofegante → desligada (corta na hora)"
	app.acao_menu("Respiração ofegante: ligada")
	while app.ofegar.ativo(): await passo()
	await esperar(1.5)
	var f := FileAccess.open(saida.path_join("audio.json"), FileAccess.WRITE)
	f.store_string(JSON.stringify(log_quadros))
	f.close()
	quit(0)
