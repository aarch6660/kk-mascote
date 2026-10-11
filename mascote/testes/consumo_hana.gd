extends SceneTree
var app: Node2D

func _initialize() -> void:
	call_deferred("rodar")

func rodar() -> void:
	var fonte := OS.get_environment("KK_CONSUMO_BASELINE")
	app = load(fonte if not fonte.is_empty() else "res://mascote.gd").new()
	app.prova = true
	app.ultimo_comando = "consumo"
	root.add_child(app)
	app.fisica.fixa = true
	app.modo_mensagens = false
	app.voz_sintetica = false
	app.cursor = Vector2(-1000,-1000)
	app.mudar("parada",600)
	await create_timer(5).timeout
	print("ESTAT ",JSON.stringify({"fps":Engine.max_fps,"real":Engine.get_frames_per_second(),"energia":app.secundario.nativa.energia(),"vel":str(app.fisica.vel),"render":app.render_pendente,"contorno":app.contorno_urgente,"estado":app.estados.estado}))
	print("MEDIR parada")
	await create_timer(30).timeout
	print("FIM parada")
	print("ESTAT ",JSON.stringify({"fps":Engine.max_fps,"real":Engine.get_frames_per_second(),"energia":app.secundario.nativa.energia(),"estado":app.estados.estado}))
	app.receber_fala({"id":"consumo-codex","autor":"Codex","texto":"Esta é uma medição local de consumo enquanto a personagem apresenta uma explicação. ".repeat(10),"emocao":"Neutra"},true)
	print("MEDIR falando")
	await create_timer(30).timeout
	print("FIM falando")
	print("ESTAT ",JSON.stringify({"fps":Engine.max_fps,"real":Engine.get_frames_per_second(),"energia":app.secundario.nativa.energia(),"estado":app.estados.estado}))
	quit()
