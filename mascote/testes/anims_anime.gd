extends SceneTree

const BONECAS := ["chika-haruno", "sawai-hinata", "mizuno-ayaka"]
const CLIPES := [
	"conversa_gesto_00", "conversa_gesto_03", "conversa_gesto_07", "conversa_gesto_11",
	"correr_normal", "correr_zangada", "postura_pensativa", "comemorar_02", "comemorar_03",
	"sentada_estudo", "sentada_leitura", "sentada_musica",
]
const FRACOES := [0.0, 0.25, 0.5, 0.75, 0.99]
const OSSOS := ["cf_j_head", "cf_j_hips", "cf_j_hand_L", "cf_j_hand_R", "cf_j_foot_L", "cf_j_foot_R"]

var casos := 0
var erros: Array[String] = []
var registros: Array[Dictionary] = []

func verificar(ok: bool, descricao: String) -> void:
	casos += 1
	if not ok:
		erros.append(descricao)

func _initialize() -> void:
	call_deferred("provar")

func salvar_captura(app, nome: String) -> void:
	var destino := OS.get_environment("KK_PROVA_RETRATO")
	if destino.is_empty() or DisplayServer.get_name() == "headless":
		return
	app.player.pause()
	for i in 5:
		await process_frame
	RenderingServer.force_draw()
	var caminho := destino.path_join(nome + ".png")
	var erro: Error = app.sub.get_texture().get_image().save_png(caminho)
	verificar(erro == OK, "captura gravada: " + caminho)

func pose_valida(app, nome_osso: String, clipe: String, fracao: float, boneca: String) -> void:
	var indice: int = app.sk.find_bone(nome_osso)
	verificar(indice >= 0, boneca + "/" + clipe + ": osso presente " + nome_osso)
	if indice < 0:
		return
	var pose: Transform3D = app.sk.get_bone_global_pose(indice)
	var quat: Quaternion = pose.basis.get_rotation_quaternion()
	verificar(pose.origin.is_finite() and pose.basis.is_finite() and quat.is_finite(),
		boneca + "/" + clipe + " @" + str(fracao) + ": posição/quaternion finitos em " + nome_osso)

func provar() -> void:
	var app: Variant = load("res://mascote.gd").new()
	app.roupas.relogio = func(): return {"hour":12,"weekday":1}
	app.cache = OS.get_environment("KK_PROVA_CACHE")
	app.runtime = ""
	app.prova = true
	app.fala_automatica = false
	app.expressao = "Automática"
	app.retrato = false
	app.perfil = false
	root.add_child(app)
	await process_frame
	app.set_process(false)
	app.set_physics_process(false)
	for filho in app.get_children():
		if filho is Timer:
			filho.stop()
	app.olhar.active = false
	app.secundario.active = false
	app.fisica.fixa = true
	app.fisica.pos = Vector2(960, 900)
	app.zoom = 1.0
	app.aplicar_render()

	for boneca_valor in BONECAS:
		var boneca: String = str(boneca_valor)
		if app.boneca != boneca:
			app.trocar_boneca(boneca)
			await process_frame
		app.olhar.active = false
		app.secundario.active = false
		var capturar: bool = boneca == "chika-haruno" and not OS.get_environment("KK_PROVA_RETRATO").is_empty()
		if capturar:
			# Vista de três quartos; mantém o corpo inteiro no SubViewport do aplicativo.
			app.chika.rotation.y = deg_to_rad(25.0)
		else:
			app.chika.rotation.y = 0.0

		for nome_valor in CLIPES:
			var nome: String = str(nome_valor)
			var contexto: String = boneca + "/" + nome
			var disponivel: bool = app.player.has_animation(nome)
			verificar(disponivel, contexto + ": clipe presente")
			if not disponivel:
				registros.append({"boneca": boneca, "clipe": nome, "presente": false})
				continue

			var anim: Animation = app.player.get_animation(nome)
			var raiz_indice: int = app.sk.find_bone("cf_j_root")
			verificar(raiz_indice >= 0, contexto + ": cf_j_root presente")
			var raiz_inicio := Vector3.ZERO
			var raiz_inicio_definida := false
			var medidas: Array[Dictionary] = []
			for fracao_valor in FRACOES:
				var fracao: float = float(fracao_valor)
				app.player.stop()
				app.player.play(nome, 0.0)
				app.player.seek(anim.length * fracao, true)
				app.player.advance(0.0)
				app.sk.force_update_all_bone_transforms()
				for osso_valor in OSSOS:
					pose_valida(app, str(osso_valor), nome, fracao, boneca)
				var raiz_pos: Vector3 = Vector3.ZERO
				if raiz_indice >= 0:
					raiz_pos = app.sk.get_bone_pose_position(raiz_indice)
					verificar(raiz_pos.is_finite(), contexto + " @" + str(fracao) + ": cf_j_root finito")
					if not raiz_inicio_definida:
						raiz_inicio = raiz_pos
						raiz_inicio_definida = true
					else:
						verificar(raiz_pos.distance_to(raiz_inicio) <= 0.00001,
							contexto + " @" + str(fracao) + ": cf_j_root sem translação")
				medidas.append({"fracao": fracao, "root_local": [raiz_pos.x, raiz_pos.y, raiz_pos.z]})

			if capturar:
				app.player.stop()
				app.player.play(nome, 0.0)
				app.player.seek(anim.length * 0.5, true)
				app.player.advance(0.0)
				app.sk.force_update_all_bone_transforms()
				await salvar_captura(app, nome)
			registros.append({"boneca": boneca, "clipe": nome, "presente": true,
				"duracao": anim.length, "amostras": medidas})

		app.chika.rotation.y = 0.0

	var resultado := {
		"passou": erros.is_empty(), "casos": casos, "erros": erros,
		"bonecas": BONECAS, "clipes": CLIPES, "fracoes": FRACOES,
		"ossos_verificados": OSSOS, "registros": registros,
		"capturas_3_4_chika": not OS.get_environment("KK_PROVA_RETRATO").is_empty(),
		"runtime_vazio": app.runtime.is_empty(), "prova_ativada": app.prova,
	}
	var saida: String = OS.get_environment("KK_PROVA_RETRATO")
	if not saida.is_empty():
		var arquivo: FileAccess = FileAccess.open(saida.path_join("resultado_godot.json"), FileAccess.WRITE)
		if arquivo:
			arquivo.store_string(JSON.stringify(resultado, "  "))
			arquivo.close()
	print(JSON.stringify(resultado))
	app.free()
	quit(0 if erros.is_empty() else 1)
