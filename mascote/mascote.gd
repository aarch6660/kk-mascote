extends Node2D
const TAM := 448
const Fisica = preload("res://fisica.gd")
const Estados = preload("res://estados.gd")
var fisica = Fisica.new()
var estados = Estados.new()
var runtime := OS.get_environment("MASCOTE_RUNTIME")
var cache := OS.get_environment("HOME").path_join(".cache/forja/kk-mascote.json")
var sub := SubViewport.new()
var camera := Camera3D.new()
var sprite := Sprite2D.new()
var chika: Node3D
var sk: Skeleton3D
var olhar: SkeletonModifier3D
var player := AnimationPlayer.new()
var animacoes_corpo = preload("res://animacoes_corpo.gd").new()
var secundario: SkeletonModifier3D
var expression: SkeletonModifier3D
var fisicas_ligadas := true
var maos_suaves := true
var modo_toque := "Pegar e mover"
var toque_ativo := false
var regiao_toque := ""
var osso_toque := -1
var ultimo_toque := Vector2.ZERO
var feedback_toque := 0.0
var sessao_eventos := str(Time.get_unix_time_from_system())+"-"+str(Time.get_ticks_usec())
var sequencia_evento := 0
var ultimo_evento: Dictionary = {}
var tempo_toque_evento := 0
var inicio_contato := 0
var regiao_contato := ""
var malhas: Array = []
var roupas_ocultas: Dictionary = {}
var roupa_modo := "automatica"
var roupa_coordenada := 0
var roupas = preload("res://roupas_contexto.gd").new()
var transicao_roupa := 0.0
var consultar_roupa := 0.0
var pecas_roupa: Dictionary = {}
var menu_roupas := false
var caixa_menu: VBoxContainer
var piscadas: Array = []
var poligono := PackedVector2Array()
var regiao_entrada := PackedVector2Array()
var local_poly := PackedVector2Array()
var limites := Rect2()
var retrato := false
var perfil := false
var rosto = preload("res://expressoes.gd").new()
var atuacao = preload("res://atuacao.gd").new()
var encenacao = preload("res://encenacao.gd").new()
var clipe_apos_caminhada := "conversa_00"
var andando_encenacao := false
var player_pausado_ocultacao := false
var estilo_anime := false
var ultimo_efeito_facial := ""
const PERFIS_ANIME := {"Felicidade":"Encantada","Riso":"Gargalhada","Raiva":"Birra","Tristeza":"Choro dramático","Choro":"Choro dramático","Surpresa":"Espanto","Timidez":"Vergonha fofa","Confiança":"Orgulho","Medo":"Pânico cômico"}
var mensagens = preload("res://mensagens.gd").new()
var efeitos = preload("res://efeitos.gd").new()
var celular = preload("res://celular.gd").new()
var sons_reacao = preload("res://sons_reacao.gd").new()
var ofegar = preload("res://ofegar.gd").new()
var dedos_mensagem: SkeletonModifier3D
var modo_mensagens := true
var hana_auto := true
var hana_cerebro := "claude"
var sons_ligados := true
var ofegar_ligado := false
var rosto_ofegante := false
# Resposta escrita no celular (chat) em vez de falada; voz sintética só quando ligada no menu.
var escrita = preload("res://escrita.gd").new()
var escrevendo := false
var escrita_estado_anterior := ""
var voz_sintetica := false
var chat_assinatura := ""
var ultima_conversa := -1000.0   # última troca no chat (para o tempo até ela "ver")
var chat_pasta := OS.get_environment("MASCOTE_CHAT") if not OS.get_environment("MASCOTE_CHAT").is_empty() else OS.get_environment("HOME").path_join(".cache/forja/kk-mascote-chat")
var indicador_mensagem := PanelContainer.new()
var legenda_mensagem := Label.new()
var atuacao_natural := true
var expressoes_extra := false
var pagina_expressoes := 0
var tempo_gesto_fala := 0.0
var proximo_gesto_fala := 3.0
var gesto_fala_fixado := false
var emocao_antes_fala := "Neutra"
var fala_texto = preload("res://fala_texto.gd").new()
var balao = preload("res://balao.gd").new()
var voz = preload("res://voz.gd").new()
var expressao := "Automática"
var emocao_atual := "Neutra"
var fala_automatica := true
var fala_restante := 0.0
var tempo_fala := 0.0
var indice_conversa := 0
var indices_gestos: Dictionary = {}
var catalogo_gestos: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://gestos.json"))
var indice_emocao := 0
var ultimo_clipe_facial := ""
var moldura := true
var pos_retrato := Vector2.ZERO
var render_pendente := 0.0
var zoom := 0.75
var origem := Vector2.ZERO
var cursor := Vector2.ZERO
var ultimo_cursor := Vector2.ZERO
var ocioso := 0.0
var escondida := false
var pressionada := false
var arrastando := false
var press := Vector2.ZERO
var offset := Vector2.ZERO
var clique_total := 0
var cliques_fora := 0
var frame := 0
var piscar_tempo := 0.0
var proxima_piscada := 3.5
var desktop: Dictionary = {}
var contexto_hana: Dictionary = {}
var vida = preload("res://vida_propria.gd").new()
var cumprimento_dados: Dictionary = {}
var tempo_contorno := 0.0
var repouso_fps := 0.0
var menu := PanelContainer.new()
var menu_itens: Array[Button] = []
var menu_tempo := 0.0
var prova := OS.get_environment("MASCOTE_PROVA") == "1"
var tempo_prova := 0.0
var etapa_prova := -1
var alvo_evento := Vector2.ZERO
var tempo_evento := 0.0
var ultimo_comando := ""
var ultima_atividade := 0.0
var ultimo_piscar := -1.0
var ultima_regiao := PackedVector2Array()
var renderizando := true
var ultima_posicao := Vector2.ZERO
var contorno_urgente := 0.5

func _ready() -> void:
	acelerar()
	Engine.physics_ticks_per_second = 60
	OS.low_processor_usage_mode_sleep_usec = 10000
	get_window().title = "Chika — mascote"
	get_window().transparent_bg = true
	get_window().transparent = true
	get_window().borderless = true
	get_window().always_on_top = true
	get_window().unfocusable = true
	get_viewport().transparent_bg = true
	# Região vazia NÃO significa liberar mouse: protege durante a carga.
	DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_MOUSE_PASSTHROUGH, true)
	carregar()
	if OS.get_environment("MASCOTE_RETRATO") == "1": retrato = true
	if OS.get_environment("MASCOTE_PERFIL") == "1":
		perfil = true
		retrato = true
		moldura = true
	ler_bonecas()
	roupa_coordenada = coordenada_disponivel(roupas.coordenada(roupa_modo))
	sub.size = Vector2i(TAM, TAM)
	sub.transparent_bg = true
	sub.own_world_3d = true
	sub.msaa_3d = Viewport.MSAA_4X
	sub.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(sub)
	var mundo := Node3D.new()
	sub.add_child(mundo)
	chika = (load(modelo_boneca()) as PackedScene).instantiate()
	mundo.add_child(chika)
	print("MATERIAIS ", preload("res://materiais_kk.gd").aplicar(chika,pasta_boneca()))
	malhas = chika.find_children("*", "MeshInstance3D", true, false)
	for m in malhas:
		if "gag_eye" in str(m.name): m.hide()
		for i in m.mesh.get_blend_shape_count():
			if str(m.mesh.get_blend_shape_name(i)) == "piscar": piscadas.append([m, i])
	registrar_roupas()
	rosto.preparar(malhas)
	sk = chika.find_children("*", "Skeleton3D", true, false)[0]
	chika.add_child(player)
	animacoes_corpo.carregar()
	var lib: AnimationLibrary = animacoes_corpo.biblioteca(sk,str(chika.get_path_to(sk)))
	player.add_animation_library("",lib)
	player.animation_finished.connect(animacao_concluida)
	# Alguns clipes de exportação têm sufixos diferentes; falhar explicitamente.
	print("CLIPES ", lib.get_animation_list())
	olhar = preload("res://olhar.gd").new()
	sk.add_child(olhar)
	preparar_expression()
	secundario = preload("res://movimento_secundario.gd").new()
	sk.add_child(secundario)
	secundario.configurar_maos(player)
	secundario.configurar_fisica(pasta_boneca()+"fisica_kk.json")
	dedos_mensagem = preload("res://digitar.gd").new()
	sk.add_child(dedos_mensagem)
	mundo.add_child(celular)
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 2.4
	camera.position = Vector3(0, 0.85, 4)
	mundo.add_child(camera)
	camera.current = true
	configurar_camera()
	var luz := DirectionalLight3D.new()
	# KK: a luz do personagem acompanha a câmera (quase frontal). Medido contra captura do jogo na mesma pose:
	# fração da coxa em sombra 16–20% no jogo; -25,-25 dava 31–37%, -10,0 dá 20–21%.
	luz.rotation_degrees = Vector3(-10, 0, 0)
	luz.light_energy = 1.0
	luz.shadow_enabled = true
	luz.directional_shadow_max_distance = 5.0
	luz.shadow_bias = 0.02
	luz.shadow_normal_bias = 0.25
	mundo.add_child(luz)
	var env := WorldEnvironment.new()
	env.environment = Environment.new()
	env.environment.background_mode = Environment.BG_CLEAR_COLOR
	env.environment.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.environment.ambient_light_energy = 0
	mundo.add_child(env)
	var mat_cor := ShaderMaterial.new()
	mat_cor.shader = load("res://shaders/kk_sprite.gdshader")
	mat_cor.set_shader_parameter("lut_kk",load("res://bonecas/visual_comum/Lut_Amount.png"))
	sprite.material = mat_cor
	sprite.texture = sub.get_texture()
	add_child(sprite)
	add_child(efeitos)
	add_child(sons_reacao)
	add_child(ofegar)
	mensagens.fase_mudou.connect(atualizar_fase_mensagem)
	mensagens.mensagem_rapida.connect(enviar_rapida)
	criar_indicador_mensagem()
	add_child(balao)
	add_child(voz)
	criar_menu()
	agendar_render()
	var timer := Timer.new()
	timer.wait_time = 0.1
	timer.timeout.connect(ler_desktop)
	add_child(timer)
	timer.start()
	ler_desktop()
	estados.rng.randomize()
	tocar()
	get_window().close_requested.connect(sair)
	print("START driver=", DisplayServer.get_name(), " pid=", OS.get_process_id())

func tocar() -> void:
	var nome: String = "parada_relaxada" if retrato and estados.estado in ["cochilo", "dormindo", "arrastando"] else ("stand_joy_00" if retrato and estados.estado == "reacao" else estados.clipe)
	if not player.has_animation(nome):
		push_error("Clipe ausente: " + nome)
		nome = "parada_relaxada" if player.has_animation("parada_relaxada") else "idle_em_pe"
	if player.current_animation != nome: player.play(nome, 0.35)
	if estados.estado != "parada": acelerar()
	aplicar_expressao()
	print("ESTADO ", estados.estado, " clipe=", nome)

func mudar(estado: String, prazo := 8.0) -> void:
	estados.mudar(estado, prazo)
	tocar()
	contorno_urgente = 0.5

func acelerar() -> void:
	Engine.max_fps = 60
	OS.low_processor_usage_mode = false
	repouso_fps = 0

func ler_contexto_hana() -> void:
	var caminho := runtime.path_join("contexto.json")
	if not FileAccess.file_exists(caminho):
		contexto_hana = {}
		return
	var dados = JSON.parse_string(FileAccess.get_file_as_string(caminho))
	if dados is Dictionary and absf(Time.get_unix_time_from_system()-float(dados.get("timestamp",0))) < 15:
		contexto_hana = dados
	else: contexto_hana = {}

func atualizar_vida(dt: float, livre: bool) -> void:
	var toca: bool = contexto_hana.get("musica",{}).get("status","")=="Playing"
	var acordada: bool = not estados.estado in ["cochilo","dormindo","arrastando","caindo","pulando"]
	vida.passo(dt,livre and acordada and not menu.visible,toca,float(contexto_hana.get("musica",{}).get("bpm",100)))
	if not livre or menu.visible or estados.sono_manual: return
	var jogo: bool = vida.assistindo(contexto_hana)
	if jogo and estados.estado in ["parada","andando","sentada","assistindo"] and (retrato or fisica.fixa or not fisica.apoio.is_empty()):
		if estados.estado != "assistindo": estados.mudar("assistindo",600)
		var clipe := "sentada_musica" if toca else "sentada_idle"
		if estados.clipe != clipe:
			estados.clipe = clipe
			tocar()
	elif not jogo and estados.estado == "assistindo": mudar("parada",8)
	elif estados.estado == "sentada":
		var clipe := "sentada_musica" if toca else "sentada_idle"
		if estados.clipe != clipe:
			estados.clipe = clipe
			tocar()

func atualizar_fps(dt: float) -> void:
	var mouse: bool = (not poligono.is_empty() and Geometry2D.is_point_in_polygon(cursor,poligono)) or (retrato and Rect2(pos_retrato-Vector2.ONE*TAM*zoom*0.5,Vector2.ONE*TAM*zoom).has_point(cursor))
	var energia: float = secundario.nativa.energia() if fisicas_ligadas and not secundario.dormindo else 0.0
	var alvo: int = vida.fps({"oculta":escondida,"interacao":pressionada or arrastando or toque_ativo or menu.visible or contorno_urgente>0 or render_pendente>0,
		"fala":fala_texto.ativo or mensagens.ativo or fala_restante>0,"gesto":estados.estado in ["gesto","gesto_ocasional","cumprimento","reacao"],
		"movimento":estados.estado in ["andando","caindo","pulando"] or fisica.vel.length()>1 or andando_encenacao,
		"mouse":mouse,"musica":vida.peso_musica>0.05,"bocejo":vida.bocejo>0,"energia":energia,"dormindo":estados.estado in ["cochilo","dormindo"] and not renderizando})
	if alvo == 60: acelerar()
	else:
		repouso_fps += dt
		if repouso_fps >= 1:
			Engine.max_fps = alvo
			OS.low_processor_usage_mode = true

func ler_desktop() -> void:
	if runtime.is_empty(): return
	ler_contexto_hana()
	ler_atividades()
	ler_falas()
	ler_chat()
	var dados = JSON.parse_string(FileAccess.get_file_as_string(runtime.path_join("desktop.json"))) if FileAccess.file_exists(runtime.path_join("desktop.json")) else null
	if not dados is Dictionary or not dados.has("monitor"): return
	var antigos: Array = desktop.get("floors", [])
	var foco_antigo: String = str(desktop.get("focused", {}).get("address", ""))
	desktop = dados
	# A ponte registra atividade do teclado sem guardar teclas.
	if float(dados.get("last_activity", 0)) > ultima_atividade:
		ultima_atividade = float(dados.get("last_activity", 0))
		ocioso = 0
	var m: Dictionary = dados.monitor
	origem = Vector2(m.x, m.y)
	var tamanho := Vector2i(m.width, m.height)
	if get_window().size != tamanho:
		get_window().size = tamanho
		agendar_render()
	if DisplayServer.get_name() == "X11": get_window().position = Vector2i(origem)
	fisica.altura_minima = 320 * zoom + 5
	if retrato:
		fisica.largura = tamanho.x
		fisica.base = tamanho.y - float(m.get("reserved", [0,0,0,0])[3])
		preparar_retrato()
	else:
		fisica.atualizar(dados.floors, tamanho.x, tamanho.y - float(m.get("reserved", [0,0,0,0])[3]))
	if dados.has("cursor"): cursor = Vector2(dados.cursor.x, dados.cursor.y) - origem
	var ocultar: bool = dados.get("fullscreen", false) or dados.get("game_mode", false)
	if ocultar != escondida:
		RenderingServer.set_render_loop_enabled(true)
		renderizando = true
		acelerar()
		escondida = ocultar
		sprite.visible = not escondida
		queue_redraw()
		sub.render_target_update_mode = SubViewport.UPDATE_DISABLED if escondida else SubViewport.UPDATE_ALWAYS
		if escondida:
			toque_ativo = false
			atuacao.contato = false
			atuacao.reacao_tempo = 0
			pressionada = false
			arrastando = false
			fisica.arrastando = false
			fisica.vel = Vector2.ZERO
			menu.hide()
		DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_MOUSE_PASSTHROUGH, true)
		print("OCULTA ", escondida)
		gravar_status()
	var foco: Dictionary = dados.get("focused", {})
	if str(foco.get("address", "")) != foco_antigo and not foco.is_empty():
		alvo_evento = Vector2(foco.at[0] + foco.size[0] * 0.5, foco.at[1]) - origem
		tempo_evento = 2
	for p in dados.floors:
		var existe := false
		for a in antigos:
			if a.address == p.address: existe = true
		if not existe and absf(float(p.x) + float(p.width)*0.5 - fisica.pos.x) < 450:
			alvo_evento = Vector2(p.x + p.width * 0.5, p.y)
			tempo_evento = 3
	if FileAccess.file_exists(runtime.path_join("comando.json")):
		var texto := FileAccess.get_file_as_string(runtime.path_join("comando.json"))
		if texto != ultimo_comando:
			ultimo_comando = texto
			var cmd = JSON.parse_string(texto)
			if cmd is Dictionary:
				if cmd.has("boneca_seguinte"): boneca_seguinte()
				if cmd.has("estado"): mudar(cmd.estado, 60)
				if cmd.has("ofegar"): ofegar.disparar(clampf(float(cmd.ofegar),3,120),"comando")
				if cmd.get("fala") is Dictionary: receber_fala(cmd.fala)
				if cmd.has("pos"):
					fisica.pos = Vector2(cmd.pos[0], cmd.pos[1])
					fisica.apoio = cmd.get("apoio", "")

func _process(dt: float) -> void:
	atualizar_roupa(dt)
	voz.stream_paused = escondida
	secundario.pausado = escondida
	if escondida and player.is_playing():
		player.pause()
		player_pausado_ocultacao = true
	elif not escondida and player_pausado_ocultacao:
		player_pausado_ocultacao = false
		player.play()
	sons_reacao.ligado = sons_ligados
	if sons_reacao.boneca != boneca:
		sons_reacao.boneca = boneca
		sons_reacao.carregar_vozes()
	mensagens.escrever = modo_mensagens
	sons_reacao.passo(dt,mensagens.esta_teclando() or (escrevendo and escrita.batendo()),escondida)
	ofegar.ligado = ofegar_ligado
	if ofegar.boneca != boneca:
		ofegar.boneca = boneca
		ofegar.carregar()
	ofegar.passo(dt,sem_roupa(),toque_ativo and regiao_toque in ofegar.INTIMAS,escondida)
	efeitos.visible = not escondida
	var legenda_agora: String = mensagens.legenda()
	if mensagens.autor=="Prévia visual" and not legenda_agora.is_empty(): legenda_agora = "Prévia · "+legenda_agora
	if legenda_mensagem.text != legenda_agora:
		legenda_mensagem.text = legenda_agora
		indicador_mensagem.reset_size()
	indicador_mensagem.visible = mensagens.ativo and not escondida and not legenda_agora.is_empty()
	dedos_mensagem.ligado = (mensagens.esta_teclando() or (escrevendo and escrita.batendo())) and not escondida
	if escondida:
		balao.hide()
		if frame % 15 == 0 and renderizando:
			RenderingServer.set_render_loop_enabled(false)
			renderizando = false
			Engine.max_fps = 10
		if frame % 15 == 0: gravar_status()
		frame += 1
		return
	frame += 1
	passo_mensagens(dt)
	efeitos.passo(dt)
	var estava_falando: bool = fala_texto.ativo
	if escrevendo:
		passo_escrita(dt)
	elif voz.dados.is_empty():
		fala_texto.passo(dt)
	else:
		fala_texto.sincronizar_audio(voz.tempo(),voz.dados,voz.terminou,dt)
	if estava_falando and not fala_texto.ativo:
		if escrevendo: concluir_escrita()
		elif fala_texto.autor == "Hana": gravar_historico(fala_texto.texto, fala_texto.autor)
		recibo_fala(fala_texto.id,"concluida")
		registrar_evento("fala_concluida", {"fala_id":fala_texto.id,"autor":fala_texto.autor})
		rosto.ajustes = {}
		atuacao.limpar()
		encenacao.limpar()
		andando_encenacao = false
		voz.encerrar()
		emocao_atual = emocao_antes_fala
		mudar("parada",4)
	var cenas_aplicadas: Array = atuacao.passo(dt,fala_texto.indice,fala_texto.texto,fala_texto.ativo)
	for cena in cenas_aplicadas:
		if escrevendo:
			# Escrevendo no celular: só rosto, olhar, efeitos e sons; corpo segura o aparelho.
			cena = cena.duplicate()
			for chave in ["enquadramento","deslocamento","gesto"]: cena.erase(chave)
		if cena.has("enquadramento"): encenacao.enquadramento = cena.enquadramento
		if cena.has("deslocamento"):
			if not andando_encenacao: clipe_apos_caminhada = estados.clipe
			encenacao.iniciar(cena.deslocamento)
		if cena.has("gesto") and player.has_animation(cena.gesto):
			clipe_apos_caminhada = cena.gesto
			tempo_gesto_fala = 0
			proximo_gesto_fala = 5
			estados.clipe = cena.gesto
			tocar()
		registrar_evento("atuacao", {"fala_id":fala_texto.id,"indice":cena.indice,"emocao":atuacao.emocao,"gesto":cena.get("gesto",""),"deslocamento":cena.get("deslocamento",{}),"enquadramento":encenacao.enquadramento})
		if cena.has("efeito"): efeitos.iniciar(cena.efeito)
		if cena.has("som") and not voz.playing: sons_reacao.reagir(cena.som)
	if fala_texto.ativo:
		ocioso = 0
		estados.tempo = 0
		tempo_gesto_fala += dt
		if atuacao_natural and not gesto_fala_fixado and not encenacao.andando and tempo_gesto_fala>=proximo_gesto_fala and not pressionada:
			tempo_gesto_fala = 0
			proximo_gesto_fala = 5.0+float(indice_conversa%3)*0.7
			estados.clipe = "conversa_%02d" % indice_conversa
			indice_conversa = (indice_conversa+1)%14
			tocar()
			registrar_evento("gesto_conversa", {"fala_id":fala_texto.id,"gesto":estados.clipe})
	if render_pendente > 0:
		render_pendente -= dt
		if render_pendente <= 0: aplicar_render()
	if retrato:
		preparar_retrato()
		var olho := sk.find_bone("cf_J_Eye_tx_L")
		if olho >= 0:
			var cabeca_pos := sk.to_global(sk.get_bone_global_pose(olho).origin)
			var cabeca_x := sk.to_global(sk.get_bone_global_pose(sk.find_bone("cf_j_head")).origin).x
			var enquadrar_celular: bool = mensagens.celular() or escrevendo
			var corpo_encenacao: bool = fala_texto.ativo and encenacao.enquadramento=="corpo"
			var tamanho_camera := 2.4 if corpo_encenacao else (0.85 if enquadrar_celular else (0.24 if perfil else 0.48))
			camera.size = lerpf(camera.size,tamanho_camera,minf(1,dt*6))
			var altura_camera := 0.85 if corpo_encenacao else cabeca_pos.y + (-0.19 if enquadrar_celular else (-0.003 if perfil else 0.01))
			camera.position.y = lerpf(camera.position.y, altura_camera, minf(1, dt * 8))
			camera.position.x = lerpf(camera.position.x, 0.0 if corpo_encenacao else cabeca_x, minf(1, dt * 8))
	if prova: estados.tempo += dt
	if cursor.distance_to(ultimo_cursor) > 1:
		ocioso = 0
		ultimo_cursor = cursor
	else: ocioso += dt
	var centro: Vector2 = pos_retrato if retrato else fisica.pos - Vector2(0, 120 * zoom)
	var perto := cursor.distance_to(centro) < 230 * zoom
	var movimento_perto := perto and ocioso < 0.3
	# Mouse se aproximando: ela para de andar para dar para pegar.
	if not retrato and not arrastando and not fisica.fixa and (perto or pressionada) and estados.estado in ["parada", "andando"]:
		if estados.estado == "andando": mudar("parada", 4.0)
		estados.tempo = 0
	var antes: String = fisica.apoio
	var andar: float = estados.direcao * 46 if estados.estado == "andando" else 0.0
	if not retrato: fisica.passo(dt, andar)
	atualizar_encenacao(dt)
	var livre: bool = not pressionada and not arrastando and not toque_ativo and not fala_texto.ativo and not mensagens.ativo and cumprimento_dados.is_empty()
	atualizar_vida(dt,livre)
	if not prova and estados.passo_ocasional(dt,livre and not menu.visible): tocar()
	if retrato and livre and not prova:
		passo_retrato(dt, movimento_perto)
	if not retrato and livre and not prova:
		if not fisica.fixa and fisica.apoio.is_empty() and not estados.estado in ["caindo", "pulando"]: mudar("caindo")
		elif (fisica.fixa or not fisica.apoio.is_empty()) and estados.estado in ["caindo", "pulando"]: mudar("parada")
		if estados.passo(dt, ocioso, fisica.fixa or not fisica.apoio.is_empty(), fisica.apoio != "tela", movimento_perto, fisica.fixa):
			if estados.estado == "sentada":
				var piso: Dictionary = fisica.piso(fisica.apoio)
				if not piso.is_empty(): fisica.pos.x = float(piso.x) + (float(piso.width) - 12 if estados.direcao > 0 else 12)
			tocar()
		if estados.estado == "andando" and not fisica.apoio.is_empty():
			var p: Dictionary = fisica.piso(fisica.apoio)
			if fisica.pos.x < 30 or fisica.pos.x > fisica.largura - 30: estados.direcao *= -1
			if not p.is_empty() and (fisica.pos.x < float(p.x)+24 or fisica.pos.x > float(p.x)+float(p.width)-24):
				var pulou := false
				for destino in fisica.pisos:
					var x := clampf(fisica.pos.x, float(destino.x)+15, float(destino.x)+float(destino.width)-15)
					if destino.address != p.address and float(destino.y) >= fisica.altura_minima and (x - fisica.pos.x) * estados.direcao > 0 and fisica.pular(Vector2(x, destino.y)):
						mudar("pulando")
						pulou = true
						break
				if not pulou: estados.direcao *= -1
	if antes != fisica.apoio: print("APOIO ", fisica.apoio)
	# Perfil lateral durante caminhada; sentado/frontal conserva leitura do rosto.
	var giro: float = estados.direcao * 0.85 if estados.estado == "andando" else 0.0
	if andando_encenacao: giro = encenacao.direcao*0.85
	if absf(chika.rotation.y - giro) > 0.001: chika.rotation.y = lerp_angle(chika.rotation.y, giro, dt * 4)
	tempo_evento = maxf(0, tempo_evento - dt)
	atualizar_olhar()
	feedback_toque = maxf(0,feedback_toque-dt)
	secundario.ligado = fisicas_ligadas
	secundario.maos_suaves = maos_suaves
	secundario.relaxar = player.current_animation in ["idle_em_pe","idle_postura"]
	secundario.repouso = player.current_animation in ["idle_em_pe","idle_postura","sentada_idle"] or player.current_animation.begins_with("conversa_") or player.current_animation.begins_with("parada_")
	secundario.dormindo = estados.estado in ["cochilo","dormindo"]
	secundario.toque_osso = osso_toque if toque_ativo else -1
	secundario.pressao = 1.0 if toque_ativo and modo_toque == "Apalpar" else 0.0
	if toque_ativo:
		ocioso = 0
		estados.tempo = 0
		feedback_toque = 0.6
	if atuacao_natural and atuacao.pede_piscada:
		atuacao.pede_piscada = false
		if piscar_tempo < proxima_piscada: proxima_piscada = piscar_tempo+0.08
	piscar_tempo += dt
	var dorme: bool = estados.estado in ["cochilo", "dormindo"]
	olhar.active = not dorme
	var fechamento := 1.0 if dorme else 0.0
	if not dorme and piscar_tempo > proxima_piscada:
		fechamento = fechamento_piscada(piscar_tempo - proxima_piscada)
		if piscar_tempo > proxima_piscada + 0.23:
			piscar_tempo = 0
			proxima_piscada = randf_range(2.5, 6)
	if not dorme: fechamento = 1.0-(1.0-fechamento)*(1.0-vida.palpebras)
	passo_facial(dt, fechamento)
	if not local_poly.is_empty(): posicionar()
	atualizar_efeitos(fechamento)
	var ancora_balao: Vector2 = ponto_osso("cf_J_Eye_tx_L")
	ancora_balao.y = sprite.position.y+(limites.position.y-TAM*0.5)*zoom
	var afastamento_balao: float = maxf(70,(TAM if retrato else limites.size.x)*zoom*0.5+20)
	balao.atualizar(fala_texto,ancora_balao,Vector2(get_window().size),escondida or escrevendo,afastamento_balao)
	publicar_chat()
	if not local_poly.is_empty(): posicionar()
	contorno_urgente = maxf(0, contorno_urgente - dt)
	tempo_contorno += dt
	if (tempo_contorno >= 0.1 or contorno_urgente > 0) and (not dorme or estados.tempo < 4):
		atualizar_silhueta()
		tempo_contorno = 0
	atualizar_mouse()
	gravar_status()
	if frame % 150 == 0 and not prova: salvar()
	if menu.visible:
		menu_tempo += dt
		if menu_tempo > 8: menu.hide()
	# Dormindo a pose é congelada; overlay também pode renderizar só mudanças.
	if dorme and estados.tempo > 4 and render_pendente <= 0 and contorno_urgente <= 0:
		player.pause()
		sub.render_target_update_mode = SubViewport.UPDATE_ONCE if frame % 30 == 0 else SubViewport.UPDATE_DISABLED
	else:
		if not player.is_playing(): player.play()
		sub.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	var renderizar: bool = render_pendente > 0 or contorno_urgente > 0 or not dorme or estados.tempo < 4 or menu.visible or fisica.pos.distance_to(ultima_posicao) > 0.1
	if renderizar != renderizando:
		RenderingServer.set_render_loop_enabled(renderizar)
		renderizando = renderizar
		Engine.max_fps = 60 if renderizar else 10
		if renderizar: sub.render_target_update_mode = SubViewport.UPDATE_ONCE
	ultima_posicao = fisica.pos
	atualizar_fps(dt)
	if prova and ultimo_comando.is_empty(): prova_passo(dt)

func atualizar_silhueta() -> void:
	if DisplayServer.get_name() == "headless": return
	# Contorno do alfa renderizado acompanha ossos, cabelo e shape keys; 10 Hz.
	if retrato:
		limites = Rect2(0, 0, TAM, TAM)
		local_poly = PackedVector2Array([Vector2.ZERO, Vector2(TAM,0), Vector2(TAM,TAM), Vector2(0,TAM)])
		posicionar()
		return
	var imagem := sub.get_texture().get_image()
	if imagem == null or imagem.is_empty(): return
	# Amostragem barata em coordenadas lógicas; render mantém resolução nativa.
	imagem.resize(TAM, TAM, Image.INTERPOLATE_BILINEAR)
	var bitmap := BitMap.new()
	bitmap.create_from_image_alpha(imagem, 0.12)
	var polys := bitmap.opaque_to_polygons(Rect2i(0, 0, TAM, TAM), 0.75)
	var maior := PackedVector2Array()
	var maior_area := 0.0
	for poly in polys:
		var area := 0.0
		for i in poly.size(): area += poly[i].cross(poly[(i + 1) % poly.size()])
		if absf(area) > maior_area:
			maior_area = absf(area)
			maior = poly
	if maior.size() < 3: return
	limites = Rect2(maior[0], Vector2.ZERO)
	for p in maior: limites = limites.expand(p)
	# Área de pegar: casco retangular com folga de 24 px na tela, senão braços/pernas finos e o movimento tornam o clique quase impossível.
	var margem := 24.0 / maxf(zoom, 0.1)
	var pegar := limites.grow(margem)
	local_poly = PackedVector2Array([pegar.position, pegar.position + Vector2(pegar.size.x, 0), pegar.end, pegar.position + Vector2(0, pegar.size.y)])
	posicionar()

func posicionar() -> void:
	sprite.scale = Vector2.ONE * zoom * TAM / float(sub.size.x)
	var ancora_y := limites.end.y
	var ancora_x := TAM / 2.0
	if estados.estado in ["sentada", "cochilo"]:
		var quadril := sk.find_bone("cf_j_hips")
		if quadril >= 0:
			var proj := camera.unproject_position(sk.global_transform * sk.get_bone_global_pose(quadril).origin)
			ancora_y = proj.y + 8
	elif estados.estado == "dormindo": ancora_x = limites.get_center().x
	sprite.position = fisica.pos - Vector2(ancora_x - TAM/2.0, ancora_y - TAM/2.0) * zoom
	if retrato: sprite.position = pos_retrato
	sprite.position.x += encenacao.offset
	queue_redraw()
	poligono.clear()
	for p in local_poly: poligono.append(sprite.position + (p - Vector2.ONE * TAM/2.0) * zoom)

func limites_encenacao() -> Vector2:
	var margem := TAM*zoom*0.5 if retrato else maxf(24,limites.size.x*zoom*0.5)
	var centro_x: float = pos_retrato.x if retrato else fisica.pos.x
	var minimo := maxf(-180,16+margem-centro_x)
	var maximo := minf(180,fisica.largura-16-margem-centro_x)
	if not retrato and not fisica.fixa:
		if fisica.apoio.is_empty(): return Vector2.ZERO
		if fisica.apoio!="tela":
			var piso: Dictionary = fisica.piso(fisica.apoio)
			if piso.is_empty(): return Vector2.ZERO
			minimo = maxf(minimo,float(piso.x)+20-centro_x)
			maximo = minf(maximo,float(piso.x)+float(piso.width)-20-centro_x)
	if minimo>maximo: return Vector2.ZERO
	return Vector2(minimo,maximo)

func atualizar_encenacao(dt: float) -> void:
	if not fala_texto.ativo: return
	var faixa := limites_encenacao()
	encenacao.passo(dt,faixa.x,faixa.y)
	var andar_agora: bool = encenacao.andando and not pressionada and not toque_ativo
	if andar_agora:
		var clipe := "caminhar_zangada" if atuacao.emocao in ["Raiva","Birra"] else "caminhar"
		if clipe_apos_caminhada.begins_with("correr_"): clipe = clipe_apos_caminhada
		if estados.clipe!=clipe:
			estados.clipe = clipe
			tocar()
	elif andando_encenacao:
		estados.clipe = clipe_apos_caminhada if player.has_animation(clipe_apos_caminhada) else "conversa_00"
		tocar()
	andando_encenacao = andar_agora

func atualizar_mouse() -> void:
	if escondida or poligono.size() < 3:
		DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_MOUSE_PASSTHROUGH, true)
		return
	var regiao := poligono
	if pressionada:
		var tamanho := Vector2(get_window().size)
		regiao = PackedVector2Array([Vector2.ZERO, Vector2(tamanho.x, 0), tamanho, Vector2(0, tamanho.y)])
	elif menu.visible:
		var r := menu.get_global_rect()
		regiao = Geometry2D.convex_hull(poligono + PackedVector2Array([r.position, r.position+Vector2(r.size.x,0), r.end, r.position+Vector2(0,r.size.y)]))
	regiao_entrada = regiao
	if regiao != ultima_regiao:
		DisplayServer.window_set_mouse_passthrough(regiao)
		ultima_regiao = regiao
	DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_MOUSE_PASSTHROUGH, false)

func _input(ev: InputEvent) -> void:
	if escondida: return
	if ev is InputEventMouse and (menu.visible or Geometry2D.is_point_in_polygon(ev.position,poligono)): acelerar()
	if ev is InputEventKey and ev.pressed and not ev.echo and ev.keycode == KEY_B and runtime.is_empty():
		boneca_seguinte()
	if ev is InputEventMouseButton:
		var dentro := Geometry2D.is_point_in_polygon(ev.position, poligono)
		if ev.pressed: print("BOTAO ", ev.button_index, " pos=", ev.position, " dentro=", dentro, " menu=", menu.visible)
		if ev.pressed and menu.visible and menu.get_global_rect().has_point(ev.position):
			if ev.button_index == MOUSE_BUTTON_LEFT:
				for botao in menu_itens:
					if botao.get_global_rect().has_point(ev.position): acao_menu(botao.text); break
			return
		if ev.pressed and not dentro:
			cliques_fora += 1
			print("CLIQUE_FORA ", ev.position)
			menu.hide()
			return
		if ev.button_index == MOUSE_BUTTON_LEFT:
			if ev.pressed:
				var contato := localizar_toque(ev.position)
				regiao_contato = str(contato.get("regiao", "Área da janela"))
				inicio_contato = Time.get_ticks_msec()
				registrar_evento("clique", {"regiao":regiao_contato,"ponto":[ev.position.x,ev.position.y],"shift":ev.shift_pressed})
				encerrar_fala("interrompida", "clique")
				clique_total += 1
				ocioso = 0
				pressionada = true
				fisica.arrastando = true
				estados.sono_manual = false
				mudar("parada", 4)
				press = ev.position
				ultimo_toque = ev.position
				offset = (pos_retrato if retrato else fisica.pos) - ev.position
				menu.hide()
				print("CLIQUE_CHIKA ", ev.position)
				if modo_toque != "Pegar e mover" and not ev.shift_pressed: iniciar_toque(ev.position)
			elif pressionada:
				registrar_evento("contato_fim", {"regiao":regiao_toque if toque_ativo else regiao_contato,"duracao":(Time.get_ticks_msec()-inicio_contato)/1000.0,"arrastando":arrastando,"ponto":[ev.position.x,ev.position.y]})
				pressionada = false
				if toque_ativo:
					atuacao.contato_fim()
					toque_ativo = false
					fisica.arrastando = false
					secundario.pressao = 0
					estados.prazo = 3
				elif arrastando:
					arrastando = false
					fisica.soltar()
					fisica.fixa = not retrato
					mudar("parada")
				else:
					fisica.arrastando = false
					estados.sono_manual = false
					mudar("reacao", 3)
				salvar()
		elif ev.pressed and ev.button_index in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN]:
			zoom = clampf(zoom * (1.1 if ev.button_index == MOUSE_BUTTON_WHEEL_UP else 1/1.1), 0.3, 3.0)
			agendar_render()
			print("ESCALA ", zoom)
			posicionar()
			atualizar_mouse()
			salvar()
		elif ev.pressed and ev.button_index == MOUSE_BUTTON_RIGHT:
			if menu_roupas: montar_menu_principal()
			for botao in menu_itens:
				if botao.text in ["Fixar aqui", "Soltar e passear"]: botao.text = "Soltar e passear" if fisica.fixa else "Fixar aqui"
			menu.position = ev.position.clamp(Vector2.ZERO, Vector2(get_window().size) - menu.size)
			menu.show()
			menu_tempo = 0
			atualizar_mouse()
	elif ev is InputEventMouseMotion and pressionada:
		if toque_ativo:
			atualizar_toque(ev.position)
			atualizar_mouse()
			gravar_status()
			return
		if ev.position.distance_to(press) > 5 and not arrastando:
			registrar_evento("arrasto_inicio", {"regiao":regiao_contato})
			arrastando = true
			fisica.arrastando = true
			fisica.apoio = ""
			mudar("arrastando")
		if arrastando:
			var movimento: Vector2 = (ev.position-ultimo_toque).limit_length(30)
			secundario.impulso = (secundario.impulso+Vector3(-movimento.x,0,movimento.y)*0.001).limit_length(0.12)
			ultimo_toque = ev.position
			if retrato:
				pos_retrato = ev.position + offset
				preparar_retrato()
			else:
				fisica.pos = (ev.position + offset).clamp(Vector2(20, minf(fisica.altura_minima, fisica.base)), Vector2(fisica.largura-20, fisica.base))
			posicionar()
			atualizar_mouse()

	if ev is InputEventMouseButton or (ev is InputEventMouseMotion and pressionada):
		atualizar_mouse()
		gravar_status()

func criar_menu() -> void:
	menu.z_index = 20
	add_child(menu)
	menu.hide()
	caixa_menu = VBoxContainer.new()
	menu.add_child(caixa_menu)
	montar_menu_principal()

func preencher_menu(textos: Array) -> void:
	for botao in menu_itens: botao.free()
	menu_itens.clear()
	for texto in textos:
		var botao := Button.new()
		botao.text = texto
		botao.custom_minimum_size = Vector2(200, 32)
		botao.focus_mode = Control.FOCUS_NONE
		caixa_menu.add_child(botao)
		menu_itens.append(botao)
	menu.reset_size()
	ajustar_menu.call_deferred()

func ajustar_menu() -> void:
	menu.position = menu.position.clamp(Vector2.ZERO, (Vector2(get_window().size) - menu.size).max(Vector2.ZERO))
	atualizar_mouse()
	gravar_status()

func montar_menu_principal() -> void:
	menu_roupas = false
	var textos: Array = ["Dormir / acordar", "Modo passeio" if retrato else "Modo retrato", "Moldura: ligada" if moldura else "Moldura: desligada", "Tamanho P", "Tamanho M", "Tamanho G", "Tamanho padrão", "Soltar e passear" if fisica.fixa else "Fixar aqui", "Roupas e acessórios", "Expressões e fala", "Gestos", "Atuação por mensagens", "Interações e física"]
	textos.append("Modo retrato" if perfil else "Modo perfil")
	for b in bonecas: textos.append("Boneca: "+b.nome)
	textos.append("Sair")
	preencher_menu(textos)

func montar_menu_roupas() -> void:
	menu_roupas = true
	var textos: Array = ["Voltar"]
	for modo in roupas.MODOS: textos.append("Roupa: "+roupas.MODOS[modo]+(" ✓" if roupa_modo == modo else ""))
	var ocultas: Array = roupas_ocultas.get(boneca, [])
	for tipo in pecas_roupa:
		textos.append(("Mostrar: " if tipo in ocultas else "Ocultar: ")+str(pecas_roupa[tipo]))
	textos.append("Ocultar todas as roupas")
	textos.append("Restaurar todas as peças")
	preencher_menu(textos)

func acao_menu(texto: String) -> void:
	contorno_urgente = 0.5
	RenderingServer.set_render_loop_enabled(true)
	renderizando = true
	acelerar()
	print("MENU_ACAO ", texto)
	if texto.begins_with("Roupa: "):
		var nome := texto.trim_prefix("Roupa: ").trim_suffix(" ✓")
		for modo in roupas.MODOS:
			if nome == roupas.MODOS[modo]: roupa_modo = modo
		consultar_roupa = 0
		montar_menu_roupas()
		menu.hide()
		salvar()
		gravar_status()
		return
	if texto=="Atuação por mensagens":
		montar_menu_mensagens()
		menu_tempo = 0
		return
	if texto.begins_with("Modo mensagens:"):
		modo_mensagens = not modo_mensagens
		if not modo_mensagens: cancelar_mensagem("modo desligado")
		montar_menu_mensagens()
		salvar()
		return
	if texto.begins_with("Hana responde sozinha:"):
		hana_auto = not hana_auto
		if not hana_auto and (mensagens.autor=="Hana" or fala_texto.autor=="Hana" or cumprimento_dados.get("autor","")=="Hana"):
			encerrar_fala("interrompida","Hana desligada")
		montar_menu_mensagens()
		salvar()
		gravar_status()
		return
	if texto.begins_with("Cérebro da Hana:"):
		hana_cerebro = "claude" if hana_cerebro == "local" else "local"
		montar_menu_mensagens()
		salvar()
		gravar_status()
		return
	if texto.begins_with("Voz sintética:"):
		voz_sintetica = not voz_sintetica
		montar_menu_mensagens()
		salvar()
		return
	if texto.begins_with("Respiração ofegante:"):
		ofegar_ligado = not ofegar_ligado
		montar_menu_mensagens()
		salvar()
		return
	if texto == "Ofegar agora":
		ofegar.disparar(30,"comando")
		menu.hide()
		return
	if texto.begins_with("Sons de reação:"):
		sons_ligados = not sons_ligados
		if not sons_ligados: sons_reacao.encerrar()
		montar_menu_mensagens()
		salvar()
		return
	if texto.begins_with("Prévia: "):
		encerrar_fala()
		var tom_preview: String = {"leitura":"curioso","surpresa":"surpreso","confusão":"confuso","alegria":"alegre","ousadia":"ousado"}.get(texto.trim_prefix("Prévia: "),"neutro")
		mensagens.iniciar({"tom":tom_preview,"duracao":8},"Prévia visual","preview",emocao_atual)
		menu.hide()
		return
	if texto == "Interações e física":
		montar_menu_interacoes()
		menu_tempo = 0
		return
	if texto.begins_with("Interação: "):
		modo_toque = texto.trim_prefix("Interação: ")
		menu.hide()
		salvar()
		return
	if texto.begins_with("Física secundária:") or texto.begins_with("Mãos suaves:"):
		if texto.begins_with("Física"): fisicas_ligadas = not fisicas_ligadas
		else: maos_suaves = not maos_suaves
		montar_menu_interacoes()
		menu_tempo = 0
		salvar()
		return
	if texto == "Gestos":
		montar_menu_gestos()
		menu_tempo = 0
		return
	if texto.begins_with("Gestos: "):
		montar_menu_gestos(texto.trim_prefix("Gestos: "))
		menu_tempo = 0
		return
	if texto.begins_with("Gesto: "):
		for nome in catalogo_gestos.clipes:
			if str(catalogo_gestos.clipes[nome]) != texto.trim_prefix("Gesto: "): continue
			encerrar_fala()
			estados.sono_manual = false
			ocioso = 0
			estados.mudar("gesto",6)
			estados.clipe = nome
			emocao_atual = emocao_gesto(nome)
			tocar()
			rosto.aplicar(expressao if expressao != "Automática" else emocao_atual,0,"a",0,1)
			break
		menu.hide()
		return
	if texto == "Mais expressões" or texto == "Expressões principais":
		expressoes_extra = texto=="Mais expressões"
		pagina_expressoes = 1 if expressoes_extra else 0
		montar_menu_expressoes()
		return
	if texto in ["Próximas expressões","Expressões anteriores"]:
		pagina_expressoes += 1 if texto=="Próximas expressões" else -1
		montar_menu_expressoes()
		return
	if texto == "Expressões e fala":
		expressoes_extra = false
		pagina_expressoes = 0
		montar_menu_expressoes()
		menu_tempo = 0
		return
	if texto == "Falar agora":
		iniciar_fala(7.0)
		menu.hide()
		gravar_status()
		return
	if texto.begins_with("Fala automática:"):
		fala_automatica = not fala_automatica
		if not fala_automatica: fala_restante = 0
		montar_menu_expressoes()
		menu_tempo = 0
		salvar()
		return
	if texto.begins_with("Expressão: "):
		estados.sono_manual = false
		ocioso = 0
		if estados.estado in ["cochilo", "dormindo"]: mudar("parada")
		expressao = texto.trim_prefix("Expressão: ")
		if expressao != "Automática": emocao_atual = expressao
		if perfil and expressao in ["Raiva", "Tristeza"]:
			estados.mudar("gesto", 6)
			estados.clipe = "stand_ang_00" if expressao == "Raiva" else "stand_sad_00"
			tocar()
		aplicar_expressao()
		montar_menu_expressoes()
		menu_tempo = 0
		salvar()
		return
	if texto == "Roupas e acessórios":
		montar_menu_roupas()
		menu_tempo = 0
		return
	if texto.begins_with("Atuação natural:"):
		atuacao_natural = not atuacao_natural
		atuacao.automatico = atuacao_natural
		atuacao.contato = false
		atuacao.reacao_tempo = 0
		montar_menu_interacoes()
		salvar()
		return
	if texto.begins_with("Estilo anime:"):
		estilo_anime = not estilo_anime
		ultimo_efeito_facial = ""
		efeitos.iniciar("nenhum")
		montar_menu_interacoes()
		salvar()
		return
	if texto == "Voltar":
		montar_menu_principal()
		menu_tempo = 0
		return
	if texto.begins_with("Ocultar: ") or texto.begins_with("Mostrar: ") or texto in ["Restaurar todas as peças", "Ocultar todas as roupas"]:
		var ocultas: Array = roupas_ocultas.get(boneca, []).duplicate()
		if texto == "Restaurar todas as peças": ocultas.clear()
		elif texto == "Ocultar todas as roupas":
			for tipo in pecas_roupa:
				if str(tipo).begins_with("roupa_") and not tipo in ocultas: ocultas.append(tipo)
		else:
			for tipo in pecas_roupa:
				if texto.get_slice(": ", 1) == str(pecas_roupa[tipo]):
					if tipo in ocultas: ocultas.erase(tipo)
					else: ocultas.append(tipo)
		roupas_ocultas[boneca] = ocultas
		aplicar_roupas()
		montar_menu_roupas()
		menu_tempo = 0
		sub.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		atualizar_silhueta()
		salvar()
		gravar_status()
		return
	if texto.begins_with("Boneca: "):
		for b in bonecas:
			if texto == "Boneca: "+b.nome: trocar_boneca(b.id); break
	match texto:
		"Modo retrato", "Modo passeio", "Modo perfil":
			perfil = texto == "Modo perfil"
			retrato = texto != "Modo passeio"
			if perfil: moldura = true
			fisica.soltar()
			estados.sono_manual = false
			mudar("parada")
			estados.gestos = ["stand_joy_00", "stand_joy_04", "stand_oth_00", "alongar", "conversa_03"]
			configurar_camera()
			agendar_render()
		"Fixar aqui", "Soltar e passear":
			var fixar: bool = not fisica.fixa
			fisica.soltar()
			fisica.fixa = fixar
			estados.sono_manual = false
			mudar("parada" if fixar or retrato else "caindo")
		"Moldura: ligada", "Moldura: desligada": moldura = not moldura
		"Tamanho P": zoom = 0.5; agendar_render()
		"Tamanho M", "Tamanho padrão": zoom = 0.75; agendar_render()
		"Tamanho G": zoom = 1.5; agendar_render()
		"Dormir / acordar":
			encerrar_fala("interrompida")
			estados.sono_manual = not estados.sono_manual
			mudar(("cochilo" if retrato or fisica.apoio != "tela" else "dormindo") if estados.sono_manual else "parada")
		"Sair": sair()
	if texto.begins_with("Modo "): montar_menu_principal()
	for botao in menu_itens:
		if botao.text in ["Fixar aqui", "Soltar e passear"]: botao.text = "Soltar e passear" if fisica.fixa else "Fixar aqui"
		if botao.text.begins_with("Moldura: "): botao.text = "Moldura: ligada" if moldura else "Moldura: desligada"
	menu.hide()
	atualizar_silhueta()
	posicionar()
	atualizar_mouse()
	salvar()
	gravar_status()

func carregar() -> void:
	if not FileAccess.file_exists(cache): return
	var dados = JSON.parse_string(FileAccess.get_file_as_string(cache))
	if dados is Dictionary:
		var salvas = dados.get("roupas_ocultas", {})
		roupas_ocultas = salvas if salvas is Dictionary else {}
		roupa_modo = str(dados.get("roupa_modo", "automatica"))
		if not roupas.MODOS.has(roupa_modo): roupa_modo = "automatica"
		fisica.fixa = bool(dados.get("fixa", false))
		boneca = str(dados.get("boneca", "chika-haruno"))
		perfil = dados.get("modo", "passeio") == "perfil"
		retrato = dados.get("modo", "passeio") in ["retrato", "perfil"]
		expressao = str(dados.get("expressao", "Automática"))
		if expressao != "Automática" and not rosto.PERFIS.has(expressao): expressao = "Automática"
		fala_automatica = bool(dados.get("fala_automatica", true))
		fisicas_ligadas = bool(dados.get("fisicas_ligadas",true))
		maos_suaves = bool(dados.get("maos_suaves",true))
		atuacao_natural = bool(dados.get("atuacao_natural",true))
		estilo_anime = bool(dados.get("estilo_anime",true))
		modo_mensagens = bool(dados.get("modo_mensagens",true))
		hana_auto = bool(dados.get("hana_auto",true))
		hana_cerebro = "local" if str(dados.get("hana_cerebro","claude")) == "local" else "claude"
		sons_ligados = bool(dados.get("sons_reacao",true))
		ofegar_ligado = bool(dados.get("ofegar",false))
		voz_sintetica = bool(dados.get("voz_sintetica",false))
		modo_toque = str(dados.get("modo_toque","Pegar e mover"))
		if modo_toque not in ["Pegar e mover","Acariciar","Apalpar"]: modo_toque = "Pegar e mover"
		moldura = bool(dados.get("moldura", true))
		var pr: Array = dados.get("posicao_retrato", [0,0])
		pos_retrato = Vector2(pr[0],pr[1])
		zoom = clampf(float(dados.get("escala", 0.75)), 0.3, 3.0)
		var p: Array = dados.get("posicao", [850,600])
		fisica.pos = Vector2(p[0], p[1])

func salvar() -> void:
	if prova: return
	DirAccess.make_dir_recursive_absolute(cache.get_base_dir())
	var f := FileAccess.open(cache + ".tmp", FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(preferencias()))
		f.close()
		DirAccess.rename_absolute(cache + ".tmp", cache)

func gravar_status() -> void:
	if runtime.is_empty(): return
	var poly: Array = []
	for p in poligono: poly.append([p.x, p.y])
	var entrada: Array = []
	for p in regiao_entrada: entrada.append([p.x, p.y])
	var botoes: Array = []
	for botao in menu_itens:
		var r := botao.get_global_rect()
		botoes.append([r.position.x,r.position.y,r.size.x,r.size.y])
	var f := FileAccess.open(runtime.path_join("status.tmp"), FileAccess.WRITE)
	if f:
		var xid := DisplayServer.window_get_native_handle(DisplayServer.WINDOW_HANDLE) if DisplayServer.get_name() == "X11" else 0
		var r := menu.get_global_rect()
		f.store_string(JSON.stringify({"pid":OS.get_process_id(),"xid":xid,"driver":DisplayServer.get_name(),"fps":Engine.get_frames_per_second(),"estado":estados.estado,"clipe":player.current_animation,"expressao":emocao_atual,"falando":fala_restante > 0 or fala_texto.ativo,"voz":{"ativa":voz.playing,"pausada":voz.stream_paused,"tempo":voz.tempo() if not voz.dados.is_empty() else 0,"nome":voz.dados.get("voz","")},"balao":{"ativo":fala_texto.ativo,"id":fala_texto.id,"autor":fala_texto.autor,"emocao":fala_texto.emocao,"texto_visivel":fala_texto.pagina_visivel(),"indice":fala_texto.indice,"abertura":fala_texto.abertura},"olhar_alvo":[olhar.alvo.x,olhar.alvo.y],"olhar_ativo":olhar.perto,"interacao":modo_toque,"toque_ativo":toque_ativo,"regiao_toque":regiao_toque,"ultimo_evento":ultimo_evento,"sequencia_evento":sequencia_evento,"sessao_eventos":sessao_eventos,"ajuste_facial":rosto.ajustes,"atuacao":{"natural":atuacao_natural,"emocao":atuacao.emocao,"cena":atuacao.proxima,"deslocamento":encenacao.offset,"andando":andando_encenacao,"enquadramento":encenacao.enquadramento,"estilo_anime":estilo_anime,"movimento":atuacao.movimento if atuacao.tempo_movimento>0 else "","reacao":atuacao.reacao_emocao if atuacao.reacao_tempo>0 else ""},"escrita":{"ativa":escrevendo,"estado":escrita.estado if escrevendo else "","indice":escrita.indice,"maximo":escrita.maximo},"mensagem":{"ativa":mensagens.ativo,"fase":mensagens.fase,"tom":mensagens.tom,"autor":mensagens.autor,"id":mensagens.id,"celular":celular.visible,"efeito":efeitos.tipo,"sons":sons_ligados},"fisicas_ligadas":fisicas_ligadas,"apoio":fisica.apoio,"posicao":[fisica.pos.x,fisica.pos.y],"escala":zoom,"roupa":roupa_atual(),"preferencias":preferencias(),"render_size":sub.size.x,"modo":"perfil" if perfil else ("retrato" if retrato else "passeio"),"hull":poly,"input_poly":entrada,"hidden":escondida,"cliques":clique_total,"cliques_fora":cliques_fora,"arrastando":arrastando,"pressionada":pressionada,"menu":menu.visible,"menu_pos":[menu.position.x,menu.position.y],"menu_rect":[r.position.x,r.position.y,r.size.x,r.size.y],"botoes":botoes,"timestamp":Time.get_unix_time_from_system()}))
		f.close()
		DirAccess.rename_absolute(runtime.path_join("status.tmp"), runtime.path_join("status.json"))

func prova_passo(dt: float) -> void:
	tempo_prova += dt
	var etapa := mini(2, int(tempo_prova / 5))
	if etapa == etapa_prova: return
	etapa_prova = etapa
	var pisos: Array = desktop.get("floors", [])
	if pisos.is_empty(): return
	var piso: Dictionary = pisos[0]
	for p in pisos:
		if p.get("class", "") == "kk.mascote.receptor" and float(p.y) >= 260: piso = p
	fisica.pos = Vector2(float(piso.x)+float(piso.width)*0.5, maxf(260, piso.y))
	fisica.apoio = str(piso.address) if float(piso.y) >= fisica.altura_minima else "tela"
	if etapa == 0: mudar("parada", 60)
	if etapa == 1: mudar("sentada", 60)
	if etapa == 2:
		fisica.pos.y = fisica.base
		fisica.apoio = "tela"
		mudar("dormindo", 60)

func sair() -> void:
	encerrar_fala("interrompida","encerramento")
	salvar()
	get_tree().quit()


var bonecas: Array = []
var boneca := "chika-haruno"
func modelo_boneca() -> String:
	var arquivo := pasta_boneca()+"personagem_roupas.glb"
	return arquivo if ResourceLoader.exists(arquivo) else pasta_boneca()+"personagem.glb"

func registrar_roupas() -> void:
	pecas_roupa.clear()
	var nomes := {"roupa_0":"Blusa", "roupa_1":"Parte de baixo", "roupa_2":"Sutiã", "roupa_3":"Calcinha", "roupa_4":"Luvas", "roupa_5":"Meia-calça", "roupa_6":"Meias", "roupa_8":"Sapatos"}
	var presentes := {}
	for m in malhas:
		if m.mesh.get_surface_count() == 0: continue
		var tipo: String = m.mesh.surface_get_material(0).resource_name.get_slice("__", 0)
		presentes[tipo] = true
	for tipo in nomes:
		if not presentes.has(tipo): continue
		if tipo in ["roupa_0", "roupa_1"]:
			# Peças externas precisam de geometria corporal restaurável.
			if not ResourceLoader.exists(pasta_boneca()+"personagem_roupas.glb"): continue
		pecas_roupa[tipo] = nomes[tipo]
	for tipo in presentes:
		if str(tipo).begins_with("acessorio_"):
			pecas_roupa[tipo] = "Acessório %d" % (str(tipo).get_slice("_",1).to_int()+1)
	aplicar_roupas()

func sem_roupa() -> bool:
	var ocultas: Array = roupas_ocultas.get(boneca, [])
	var pecas := 0
	for tipo in pecas_roupa:
		if not str(tipo).begins_with("roupa_"): continue
		pecas += 1
		if not tipo in ocultas: return false
	return pecas > 0

func aplicar_roupas() -> void:
	var ocultas: Array = roupas_ocultas.get(boneca, [])
	var variante := ("1" if "roupa_0" in ocultas and pecas_roupa.has("roupa_0") else "0") + ("1" if "roupa_1" in ocultas and pecas_roupa.has("roupa_1") else "0")
	for m in malhas:
		var nome := str(m.name)
		if nome == "o_body_a": m.visible = variante == "00"
		elif nome.begins_with("kk_o_body_a_"): m.visible = nome == "kk_o_body_a_"+variante
		elif m.mesh.get_surface_count() > 0:
			var tipo: String = m.mesh.surface_get_material(0).resource_name.get_slice("__", 0)
			if tipo == "roupa_2": m.visible = not tipo in ocultas and (nome.begins_with("kk_") == (variante[0] == "1"))
			elif pecas_roupa.has(tipo): m.visible = not tipo in ocultas

func preparar_expression() -> void:
	expression = preload("res://expression_kk.gd").new()
	sk.add_child(expression)
	expression.configurar(pasta_boneca()+"expression_kk.json")

func pasta_boneca() -> String:
	if roupa_coordenada != 0: return "res://bonecas/"+boneca+"/coordenadas/coord_%d/saida/" % roupa_coordenada
	return "res://bonecas/"+boneca+"/saida/"

func coordenada_disponivel(coordenada: int) -> int:
	var pasta := "res://bonecas/"+boneca+"/coordenadas/coord_%d/saida/" % coordenada
	return coordenada if coordenada == 0 or ResourceLoader.exists(pasta+"personagem_roupas.glb") else 0

func roupa_atual() -> Dictionary:
	return {"modo":roupa_modo,"coordenada":roupa_coordenada,"nome":roupas.NOMES[roupa_coordenada]}

func pode_trocar_roupa() -> bool:
	return estados.estado == "parada" and not (escondida or arrastando or pressionada or toque_ativo or menu.visible or fala_texto.ativo or fala_restante > 0 or escrevendo or mensagens.ativo or not cumprimento_dados.is_empty() or andando_encenacao or encenacao.andando or vida.bocejo > 0)

func atualizar_roupa(dt: float) -> void:
	if transicao_roupa > 0:
		transicao_roupa = maxf(0,transicao_roupa-dt)
		sprite.modulate.a = 1.0-transicao_roupa/0.18
		return
	consultar_roupa -= dt
	if consultar_roupa > 0 or not pode_trocar_roupa(): return
	consultar_roupa = 1.0
	var desejada: int = coordenada_disponivel(roupas.coordenada(roupa_modo))
	if desejada == roupa_coordenada: return
	var anterior := roupa_coordenada
	roupa_coordenada = desejada
	if not recarregar_boneca():
		roupa_coordenada = anterior
		return
	# Um reaparecimento breve evita encenar uma animação longa inexistente.
	transicao_roupa = 0.18
	sprite.modulate.a = 0
	contorno_urgente = 0.5
	atualizar_silhueta()
	posicionar()
	gravar_status()
func ler_bonecas():
	var dados = JSON.parse_string(FileAccess.get_file_as_string("res://bonecas/catalogo.json"))
	if dados is Array: bonecas = dados
	if not bonecas.any(func(b): return b.id == boneca) and not bonecas.is_empty(): boneca = bonecas[0].id

func trocar_boneca(id: String) -> void:
	if id == boneca: return
	encerrar_fala("interrompida")
	var boneca_anterior := boneca
	var coordenada_anterior := roupa_coordenada
	boneca = id
	roupa_coordenada = coordenada_disponivel(roupas.coordenada(roupa_modo))
	if not recarregar_boneca():
		boneca = boneca_anterior
		roupa_coordenada = coordenada_anterior
		return
	salvar()

func recarregar_boneca() -> bool:
	var recurso = load(modelo_boneca())
	if not recurso is PackedScene: return false
	var nova = recurso.instantiate()
	var anterior = chika
	var mundo = anterior.get_parent()
	anterior.remove_child(player)
	chika = nova
	mundo.add_child(chika)
	chika.add_child(player)
	anterior.free()
	print("MATERIAIS ", preload("res://materiais_kk.gd").aplicar(chika,pasta_boneca()))
	malhas = chika.find_children("*", "MeshInstance3D", true, false)
	piscadas.clear()
	for m in malhas:
		if "gag_eye" in str(m.name): m.hide()
		for i in m.mesh.get_blend_shape_count():
			if str(m.mesh.get_blend_shape_name(i)) == "piscar": piscadas.append([m,i])
	registrar_roupas()
	rosto.preparar(malhas)
	sk = chika.find_children("*", "Skeleton3D", true, false)[0]
	player.stop()
	player.remove_animation_library("")
	player.add_animation_library("",animacoes_corpo.biblioteca(sk,str(chika.get_path_to(sk))))
	toque_ativo = false
	atuacao.contato = false
	atuacao.reacao_tempo = 0
	pressionada = false
	fisica.arrastando = false
	player.clear_caches()
	olhar = preload("res://olhar.gd").new()
	sk.add_child(olhar)
	preparar_expression()
	secundario = preload("res://movimento_secundario.gd").new()
	sk.add_child(secundario)
	secundario.configurar_maos(player)
	secundario.configurar_fisica(pasta_boneca()+"fisica_kk.json")
	dedos_mensagem = preload("res://digitar.gd").new()
	sk.add_child(dedos_mensagem)
	piscar_tempo = 0
	ultimo_piscar = -1
	configurar_camera()
	tocar()
	sub.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	return true

func preferencias() -> Dictionary:
	return {"versao":12,"roupa_modo":roupa_modo,"hana_auto":hana_auto,"hana_cerebro":hana_cerebro,"estilo_anime":estilo_anime,"modo_mensagens":modo_mensagens,"sons_reacao":sons_ligados,"ofegar":ofegar_ligado,"voz_sintetica":voz_sintetica,"atuacao_natural":atuacao_natural,"fisicas_ligadas":fisicas_ligadas,"maos_suaves":maos_suaves,"modo_toque":modo_toque,"expressao":expressao,"fala_automatica":fala_automatica,"roupas_ocultas":roupas_ocultas,"fixa":fisica.fixa,"boneca":boneca,"posicao":[fisica.pos.x,fisica.pos.y],"escala":zoom,"modo":"perfil" if perfil else ("retrato" if retrato else "passeio"),"moldura":moldura,"posicao_retrato":[pos_retrato.x,pos_retrato.y]}

func preparar_retrato() -> void:
	var metade := TAM * zoom * 0.5
	if pos_retrato == Vector2.ZERO:
		pos_retrato = Vector2(fisica.largura - metade - 24, fisica.base - metade - 24)
	pos_retrato = pos_retrato.clamp(Vector2.ONE * (metade + 16), Vector2(fisica.largura - metade - 16, fisica.base - metade - 16))

func configurar_camera() -> void:
	camera.size = 0.24 if perfil else (0.48 if retrato else 2.4)
	camera.position = Vector3(0, 0.85, 4)
	if retrato:
		var olho := sk.find_bone("cf_J_Eye_tx_L")
		if olho >= 0:
			var altura: float = sk.to_global(sk.get_bone_global_rest(olho).origin).y
			camera.position.y = altura + (-0.003 if perfil else 0.01)

func passo_retrato(dt: float, perto: bool) -> void:
	estados.tempo += dt
	if estados.estado == "cochilo":
		if perto and not estados.sono_manual: mudar("parada")
	elif ocioso > 180 or estados.sono_manual: mudar("cochilo", 60)
	elif estados.estado in ["parada","gesto_ocasional","assistindo","cumprimento"] and not perfil: return
	elif estados.tempo >= estados.prazo:
		estados.gestos = ["stand_joy_00", "stand_joy_04", "conversa_03"]
		if perfil and estados.estado == "parada":
			if expressao == "Automática":
				var opcoes := ["Neutra", "Felicidade", "Surpresa", "Preocupação", "Tristeza", "Medo", "Raiva", "Confiança", "Timidez", "Pensativa", "Seriedade", "Tédio"]
				indice_emocao = (indice_emocao + 1) % opcoes.size()
				emocao_atual = opcoes[indice_emocao]
			if fala_automatica: iniciar_fala(randf_range(4,7))
			else: mudar("gesto", 6)
		else: mudar("gesto" if estados.estado == "parada" else "parada", randf_range(5, 12))

func agendar_render() -> void:
	# Limita altura visível à tela e mantém proporção e densidade de pixels.
	var altura: float = float(get_window().size.y) if not desktop.is_empty() else fisica.base
	zoom = minf(zoom, maxf(0.3, (altura - 64) / (TAM if retrato else 320.0)))
	render_pendente = 0.25
	contorno_urgente = 0.5
	RenderingServer.set_render_loop_enabled(true)
	renderizando = true
	acelerar()

func aplicar_render() -> void:
	var densidade := float(desktop.get("monitor", {}).get("scale", 1.0))
	var tamanho := clampi(int(ceil(TAM * zoom * densidade / 64.0)) * 64, 256, 1536)
	if sub.size.x != tamanho:
		sub.size = Vector2i(tamanho, tamanho)
		contorno_urgente = 0.5
	posicionar()

func _draw() -> void:
	if retrato and moldura and not escondida:
		var lado := TAM * zoom
		draw_rect(Rect2(sprite.position - Vector2.ONE * lado * 0.5, Vector2.ONE * lado), Color("c99a50"), false, 2.0)
	if feedback_toque > 0 and not escondida:
		var cor := Color(1.0,0.72,0.48,minf(1,feedback_toque*3))
		draw_arc(ultimo_toque,12,0,TAU,24,cor,2,true)
		draw_string(ThemeDB.fallback_font,ultimo_toque+Vector2(16,-14),("Carinho: " if modo_toque == "Acariciar" else "Toque: ")+regiao_toque,HORIZONTAL_ALIGNMENT_LEFT,-1,16,cor)

func montar_menu_expressoes() -> void:
	menu_roupas = true
	var textos: Array = ["Voltar", "Falar agora", "Fala automática: ligada" if fala_automatica else "Fala automática: desligada", "Expressão: Automática"]
	var nomes: Array = rosto.PERFIS.keys()
	var paginas := int(ceil(nomes.size()/8.0))
	pagina_expressoes = clampi(pagina_expressoes,0,paginas-1)
	for nome in nomes.slice(pagina_expressoes*8,mini(nomes.size(),(pagina_expressoes+1)*8)): textos.append("Expressão: "+str(nome))
	if pagina_expressoes>0: textos.append("Expressões anteriores")
	if pagina_expressoes<paginas-1: textos.append("Próximas expressões")
	preencher_menu(textos)

func iniciar_fala(duracao := 6.0) -> void:
	encerrar_fala("interrompida")
	estados.sono_manual = false
	ocioso = 0
	fala_restante = duracao
	tempo_fala = 0
	estados.mudar("gesto", duracao)
	var conversa := "conversa_%02d" % indice_conversa
	indice_conversa = (indice_conversa + 1) % 14
	estados.clipe = conversa if player.has_animation(conversa) else "conversa_00"
	tocar()
	ultimo_clipe_facial = player.current_animation

# Fecha rápido, permanece fechado por um quadro mesmo a 30 FPS e reabre suave.
func fechamento_piscada(tempo: float) -> float:
	if tempo < 0 or tempo >= 0.23: return 0.0
	if tempo < 0.065: return smoothstep(0.0,0.065,tempo)
	if tempo < 0.10: return 1.0
	return 1.0-smoothstep(0.10,0.23,tempo)

func passo_facial(dt: float, fechamento: float) -> void:
	var nome := player.current_animation
	if not fala_texto.ativo and fala_automatica and nome != ultimo_clipe_facial and nome.begins_with("conversa_"):
		fala_restante = minf(7.0, maxf(3.0, player.current_animation_length))
		tempo_fala = 0
	ultimo_clipe_facial = nome
	if expressao != "Automática": emocao_atual = expressao
	elif not perfil:
		if estados.estado == "reacao": emocao_atual = "Medo" if nome == "reacao_defesa" else "Felicidade"
		elif nome.begins_with("stand_ang") or nome == "caminhar_zangada": emocao_atual = "Raiva"
		elif nome.begins_with("stand_sad"): emocao_atual = "Tristeza"
		elif estados.estado == "gesto" and nome.begins_with("stand_joy"): emocao_atual = "Felicidade"
		elif nome in catalogo_gestos.emocoes.Timidez: emocao_atual = "Timidez"
		elif nome in catalogo_gestos.emocoes.Surpresa: emocao_atual = "Surpresa"
		else: emocao_atual = "Neutra"
	var dorme: bool = estados.estado in ["cochilo", "dormindo"]
	if estados.estado in ["arrastando", "caindo", "pulando"] or dorme: fala_restante = 0
	var abertura := 0.0
	var vogal := "a"
	fala_restante = maxf(0,fala_restante-dt)
	if fala_restante > 0:
		tempo_fala += dt
		var fase := fmod(tempo_fala, 1.35)
		# Sílabas com pausas e cinco formas originais; temporização visual, sem áudio.
		if fase < 1.05: abertura = 0.25 + 0.65*pow(absf(sin(tempo_fala*10.5)),0.75)
		var vogais := ["a","i","u","e","o","a","e","i"]
		vogal = vogais[int(tempo_fala*4.5) % vogais.size()]
	if fala_texto.ativo:
		emocao_atual = atuacao.emocao if not atuacao.emocao.is_empty() else fala_texto.emocao
		rosto.ajustes = atuacao.face_atual
		abertura = fala_texto.abertura
		vogal = fala_texto.vogal
		if escrevendo:
			# Boca só se mexe com as vozes curtas do jogo; nas pausas, cara de quem pensa.
			if escrita.estado == "pensando" and atuacao.olhar_tempo <= 0: emocao_atual = "Pensativa"
			abertura = sons_reacao.abertura()
	elif mensagens.visivel():
		emocao_atual = mensagens.emocao()
		rosto.ajustes = {"intensidade":mensagens.intensidade}
		abertura = sons_reacao.abertura()
	if toque_ativo and not fala_texto.ativo and expressao == "Automática": emocao_atual = "Felicidade" if modo_toque == "Acariciar" else "Surpresa"
	rosto.dinamica = 1.0
	rosto.vogais_amplas = atuacao_natural and fala_texto.ativo and abertura>0.72
	if atuacao_natural and not fala_texto.ativo and not mensagens.ativo and expressao=="Automática" and atuacao.reacao_tempo>0 and not dorme:
		emocao_atual = atuacao.reacao_emocao
		rosto.dinamica = atuacao.intensidade_reacao()
	if atuacao_natural and fala_texto.ativo and not atuacao.face_atual.has("intensidade"):
		rosto.dinamica = 0.86+0.06*sin(atuacao.tempo*1.4)
	if ofegar.ativo() and not fala_texto.ativo and not mensagens.ativo and expressao == "Automática" and not dorme:
		# Corada (Timidez → Vergonha fofa no estilo anime) e boca acompanhando a respiração.
		emocao_atual = "Timidez"
		abertura = maxf(abertura, ofegar.abertura())
		vogal = "a"
		rosto_ofegante = true
	elif rosto_ofegante:
		# Fim da crise: devolve o rosto em vez de deixá-la corada para sempre.
		rosto_ofegante = false
		if emocao_atual in ["Timidez","Vergonha fofa"]: emocao_atual = "Neutra"
	if estilo_anime and not dorme:
		emocao_atual = PERFIS_ANIME.get(emocao_atual,emocao_atual)
		rosto.dinamica = 1.0
		rosto.vogais_amplas = fala_texto.ativo
		if ultimo_efeito_facial!=emocao_atual:
			ultimo_efeito_facial = emocao_atual
			var caricatos: Dictionary = rosto.CATALOGO.get("caricatos",{})
			if caricatos.has(emocao_atual) and efeitos.tipo=="nenhum":
				efeitos.iniciar(str(caricatos[emocao_atual].get("efeito","nenhum")))
	if vida.bocejo > 0 and not fala_texto.ativo and not mensagens.ativo and expressao=="Automática":
		abertura = vida.abertura_bocejo()
		vogal = "a"
		fechamento = maxf(fechamento,0.5*abertura)
	rosto.aplicar("Neutra" if dorme else emocao_atual, abertura, vogal, fechamento, dt)

func aplicar_expressao() -> void:
	if expressao != "Automática": emocao_atual = expressao
	elif retrato and not perfil and estados.estado in ["reacao", "gesto"]: emocao_atual = "Felicidade"
	rosto.aplicar(emocao_atual, 0.0, "a", 0.0, 1.0)

func atualizar_olhar() -> void:
	var centro: Vector2 = pos_retrato if retrato else fisica.pos-Vector2(0,180*zoom)
	var esquerdo := sk.find_bone("cf_J_hitomi_tx_L")
	var direito := sk.find_bone("cf_J_hitomi_tx_R")
	if esquerdo >= 0 and direito >= 0:
		var ponto := (sk.to_global(sk.get_bone_global_pose(esquerdo).origin)+sk.to_global(sk.get_bone_global_pose(direito).origin))*0.5
		var projetado := camera.unproject_position(ponto)
		centro = sprite.position + (projetado-Vector2(sub.size)*0.5)*sprite.scale
	var distancia := maxf(220.0,TAM*zoom*0.75) if retrato else 500.0
	var diferenca := cursor-centro
	if estados.estado == "assistindo":
		var janela: Dictionary = contexto_hana.get("janela",{})
		var pos: Array = janela.get("at",[0,0])
		var tamanho: Array = janela.get("size",[0,0])
		diferenca = Vector2(float(pos[0])+float(tamanho[0])*0.5,float(pos[1])+float(tamanho[1])*0.5)-origem-centro
	olhar.alvo = Vector2(atan2(diferenca.x,distancia),atan2(diferenca.y,distancia))
	if fala_texto.ativo and atuacao.olhar_tempo>0: olhar.alvo = atuacao.olhar_alvo
	elif escrevendo and escrita.estado=="pensando": olhar.alvo = Vector2(-0.18,-0.1)
	elif mensagens.ativo and mensagens.olhando_voce(): olhar.alvo = mensagens.olhar()
	elif celular.visible and celular.is_inside_tree():
		# Olha para a tela do celular: diferença no plano da tela em metros, a ~30 cm do rosto.
		var tela := sprite.position + (camera.unproject_position(celular.tela_global())-Vector2(sub.size)*0.5)*sprite.scale
		var metros := (tela-centro)/maxf(1.0,float(sub.size.y)/camera.size*sprite.scale.y)
		olhar.alvo = Vector2(atan2(metros.x,0.3),atan2(metros.y,0.3))
	elif mensagens.visivel(): olhar.alvo = mensagens.olhar()
	olhar.expressivo = atuacao.cabeca() if atuacao_natural and not estados.estado in ["cochilo","dormindo","arrastando","caindo","pulando"] else Vector3.ZERO
	if not player.current_animation.begins_with("sentada_"): olhar.expressivo += vida.cabeca()
	olhar.perto = not estados.estado in ["cochilo","dormindo"]

func boneca_seguinte() -> void:
	var indice := 0
	for i in bonecas.size():
		if bonecas[i].id == boneca: indice = i
	trocar_boneca(bonecas[(indice + 1) % bonecas.size()].id)

func montar_menu_interacoes() -> void:
	menu_roupas = true
	preencher_menu(["Voltar","Interação: Pegar e mover","Interação: Acariciar","Interação: Apalpar","Atuação natural: ligada" if atuacao_natural else "Atuação natural: desligada","Estilo anime: ligado" if estilo_anime else "Estilo anime: desligado","Física secundária: ligada" if fisicas_ligadas else "Física secundária: desligada","Mãos suaves: ligadas" if maos_suaves else "Mãos suaves: desligadas"])
	for botao in menu_itens:
		if botao.text.begins_with("Interação: "):
			botao.toggle_mode = true
			botao.button_pressed = botao.text == "Interação: "+modo_toque
			botao.tooltip_text = "Segure o botão esquerdo e mova sobre a personagem. Shift + arrastar permite pegá-la em qualquer modo."

func ponto_osso(nome: String) -> Vector2:
	var i := sk.find_bone(nome)
	if i < 0: return Vector2(-100000,-100000)
	var proj := camera.unproject_position(sk.to_global(sk.get_bone_global_pose(i).origin))
	return sprite.position+(proj-Vector2(sub.size)*0.5)*sprite.scale

func localizar_toque(ponto: Vector2) -> Dictionary:
	# Cápsulas projetadas acompanham a pose e o zoom, sem caixas fixas no retrato.
	var regioes := [
		["Cabeça","cf_j_head","cf_J_Eye_tx_L",0.145,"cf_j_spine02"],
		["Mão esquerda","cf_j_hand_L","cf_j_middle03_L",0.045,"cf_j_hand_L"],
		["Mão direita","cf_j_hand_R","cf_j_middle03_R",0.045,"cf_j_hand_R"],
		["Braço esquerdo","cf_j_arm00_L","cf_j_forearm01_L",0.045,"cf_j_arm00_L"],
		["Braço direito","cf_j_arm00_R","cf_j_forearm01_R",0.045,"cf_j_arm00_R"],
		["Ombros","cf_j_shoulder_L","cf_j_shoulder_R",0.05,"cf_j_spine03"],
		["Tronco","cf_j_spine03","cf_j_hips",0.10,"cf_j_spine03"],
		["Perna esquerda","cf_j_thigh00_L","cf_j_leg01_L",0.06,"cf_j_thigh00_L"],
		["Perna direita","cf_j_thigh00_R","cf_j_leg01_R",0.06,"cf_j_thigh00_R"]]
	var melhor := 1.0
	var resultado := {}
	var escala_tela: float = sub.size.y/camera.size*sprite.scale.y
	var frente := chika.global_basis.z.dot((camera.global_position-chika.global_position).normalized()) >= 0
	var detalhes := [
		["Mamilo esquerdo","cf_j_bnip02_L",0.018,true],
		["Mamilo direito","cf_j_bnip02_R",0.018,true],
		["Seio esquerdo","cf_j_bust03_L",0.065,true],
		["Seio direito","cf_j_bust03_R",0.065,true],
		["Região genital","cf_j_kokan",0.045,true],
		["Nádega esquerda","cf_j_siri_L",0.065,false],
		["Nádega direita","cf_j_siri_R",0.065,false],
		["Região anal","cf_j_ana",0.025,false]]
	for detalhe in detalhes:
		var indice := sk.find_bone(detalhe[1])
		if indice < 0 or frente != detalhe[3]: continue
		var distancia := ponto.distance_to(ponto_osso(detalhe[1]))/maxf(3,detalhe[2]*escala_tela)
		if distancia < melhor:
			melhor = distancia
			resultado = {"regiao":detalhe[0],"osso":indice}
	# Regiões específicas têm precedência sobre o tronco; são aproximações por ossos.
	if not resultado.is_empty(): return resultado
	for regiao in regioes:
		if sk.find_bone(regiao[1]) < 0 or sk.find_bone(regiao[2]) < 0: continue
		var a := ponto_osso(regiao[1])
		var b := ponto_osso(regiao[2])
		var proximo := Geometry2D.get_closest_point_to_segment(ponto,a,b)
		var distancia: float = ponto.distance_to(proximo)/maxf(6,regiao[3]*escala_tela)
		if distancia < melhor:
			melhor = distancia
			resultado = {"regiao":regiao[0],"osso":sk.find_bone(regiao[4])}
	return resultado

func iniciar_toque(ponto: Vector2) -> void:
	var regiao := localizar_toque(ponto)
	if regiao.is_empty():
		pressionada = false
		fisica.arrastando = false
		return
	toque_ativo = true
	regiao_toque = regiao.regiao
	osso_toque = regiao.osso
	ultimo_toque = ponto
	feedback_toque = 0.6
	atuacao.contato_inicio(regiao_toque,modo_toque=="Acariciar")
	tempo_toque_evento = Time.get_ticks_msec()
	registrar_evento("toque_inicio", {"regiao":regiao_toque,"ponto":[ponto.x,ponto.y]})
	fala_restante = 0
	estados.mudar("gesto",4)
	estados.clipe = "stand_joy_00" if modo_toque == "Acariciar" and regiao_toque == "Cabeça" else ("conversa_03" if regiao_toque.begins_with("Mão") else "stand_oth_00")
	tocar()
	secundario.impulso = Vector3(0,0,0.025)
	queue_redraw()

func atualizar_toque(ponto: Vector2) -> void:
	var movimento := (ponto-ultimo_toque).limit_length(25)
	var regiao := localizar_toque(ponto)
	# Sair do corpo interrompe a pressão, mas conserva captura até soltar o botão.
	var anterior := regiao_toque
	if not regiao.is_empty():
		regiao_toque = regiao.regiao
		osso_toque = regiao.osso
		secundario.impulso = (secundario.impulso+Vector3(movimento.x,0,-movimento.y)*0.001).limit_length(0.12)
	else:
		osso_toque = -1
		regiao_toque = "Fora do corpo"
	var agora := Time.get_ticks_msec()
	if regiao_toque != anterior or agora-tempo_toque_evento >= 250:
		tempo_toque_evento = agora
		registrar_evento("toque_movimento", {"regiao":regiao_toque,"anterior":anterior,"ponto":[ponto.x,ponto.y]})
	if regiao_toque != anterior:
		if osso_toque>=0: atuacao.contato_inicio(regiao_toque,modo_toque=="Acariciar")
		else: atuacao.contato_fim()
	ultimo_toque = ponto
	feedback_toque = 0.6
	queue_redraw()

func recibo_fala(id: String, estado: String, detalhe := "", meta: Dictionary = {}) -> void:
	if runtime.is_empty() or id.is_empty() or id.get_file()!=id: return
	var pasta := runtime.path_join("recibos-fala")
	DirAccess.make_dir_recursive_absolute(pasta)
	var arquivo := pasta.path_join(id+".json")
	var f := FileAccess.open(arquivo+".tmp",FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify({"id":id,"estado":estado,"autor":meta.get("autor",fala_texto.autor),"emocao":meta.get("emocao",fala_texto.emocao),"detalhe":detalhe,"timestamp":Time.get_unix_time_from_system()}))
		f.close()
		DirAccess.rename_absolute(arquivo+".tmp",arquivo)
	# Retém os últimos 100 recibos; não cresce indefinidamente.
	var nomes := DirAccess.get_files_at(pasta)
	nomes.sort()
	for i in maxi(0,nomes.size()-100): DirAccess.remove_absolute(pasta.path_join(nomes[i]))

func ler_falas() -> void:
	if runtime.is_empty() or escondida or fala_texto.ativo or pressionada or not cumprimento_dados.is_empty() or not mensagens.resposta.is_empty(): return
	var pasta := runtime.path_join("falas")
	if not DirAccess.dir_exists_absolute(pasta): return
	var arquivos := DirAccess.get_files_at(pasta)
	arquivos.sort()
	for arquivo in arquivos:
		if not arquivo.ends_with(".json"): continue
		var caminho := pasta.path_join(arquivo)
		var dados = JSON.parse_string(FileAccess.get_file_as_string(caminho))
		DirAccess.remove_absolute(caminho)
		var id := arquivo.get_basename()
		if not dados is Dictionary or int(dados.get("pid_destino",-1))!=OS.get_process_id():
			recibo_fala(id,"erro","Mensagem inválida ou de outra sessão")
			continue
		if Time.get_unix_time_from_system()-float(dados.get("criado_em",0)) > 600:
			recibo_fala(id,"erro","Mensagem expirou")
			continue
		dados.id = id
		if receber_fala(dados): return

func receber_fala(dados: Dictionary, direta := false, escrever := false) -> bool:
	if fala_texto.ativo or not cumprimento_dados.is_empty() or (not direta and not mensagens.resposta.is_empty()): return false
	if dados.get("autor","")=="Hana" and not hana_auto:
		recibo_fala(str(dados.get("id","")),"erro","Hana desligada",dados)
		return false
	if not mensagens.validar(dados.get("preparacao",{})):
		recibo_fala(str(dados.get("id","")),"erro","Preparação inválida",dados)
		return false
	if not atuacao.validar(dados.get("atuacao",[]),str(dados.get("texto","")).strip_edges().length()):
		recibo_fala(str(dados.get("id","")),"erro","Atuação inválida")
		return false
	if not rosto.validar_ajustes(dados.get("face",{})):
		recibo_fala(str(dados.get("id","")),"erro","Ajuste facial inválido")
		return false
	var pedido := str(dados.get("gesto","auto"))
	if pedido != "auto" and (not catalogo_gestos.clipes.has(pedido) or not player.has_animation(pedido)):
		recibo_fala(str(dados.get("id","")),"erro","Gesto inválido")
		return false
	if not preload("res://fala_texto.gd").new().iniciar(dados):
		recibo_fala(str(dados.get("id","")),"erro","Texto inválido",dados)
		return false
	# Modo mensagens: toda resposta passa pelo celular (lê, reage, pensa e escreve).
	if not direta and modo_mensagens:
		if pedido == "gesto_reverencia":
			cumprimento_dados = dados.duplicate(true)
			estados.mudar("cumprimento",120)
			estados.clipe = pedido
			tocar()
			recibo_fala(str(dados.get("id","")),"preparando","",dados)
			registrar_evento("cumprimento",{"fala_id":dados.get("id",""),"autor":dados.get("autor",""),"gesto":pedido})
			return true
		mensagens.escrever = true
		mensagens.preparar(dados,emocao_atual)
		recibo_fala(str(dados.get("id","")),"preparando","",dados)
		return true
	if (escrever or not voz_sintetica) and dados.has("audio"):
		# Sem voz sintética: descarta o áudio já gerado e mostra só o texto.
		var arquivo := str(dados.get("id",""))
		if not runtime.is_empty() and not arquivo.is_empty() and arquivo.get_file()==arquivo:
			DirAccess.remove_absolute(runtime.path_join("audio").path_join(arquivo+".wav"))
		dados = dados.duplicate()
		dados.erase("audio")
	sons_reacao.encerrar()
	emocao_antes_fala = emocao_atual
	if not fala_texto.iniciar(dados):
		recibo_fala(str(dados.get("id","")),"erro","Texto inválido")
		return false
	if not voz.iniciar(dados.get("audio",{}),runtime,fala_texto.id):
		recibo_fala(fala_texto.id,"erro","Áudio inválido ou ausente")
		fala_texto.cancelar()
		return false
	rosto.ajustes = dados.get("face",{}).duplicate(true)
	atuacao.iniciar(dados.get("atuacao",[]),rosto.ajustes,fala_texto.emocao,atuacao_natural)
	encenacao.limpar()
	andando_encenacao = false
	ultimo_efeito_facial = ""
	tempo_gesto_fala = 0
	proximo_gesto_fala = 3
	gesto_fala_fixado = dados.get("gesto","auto")!="auto"
	for cena in dados.get("atuacao",[]):
		if cena.has("gesto"): gesto_fala_fixado = true
	estados.sono_manual = false
	ocioso = 0
	fala_restante = 0
	estados.mudar("gesto",600)
	var clipe := "celular_digitar" if escrever else escolher_gesto(fala_texto.emocao,str(dados.get("gesto","auto")))
	estados.clipe = clipe
	tocar()
	escrevendo = escrever
	if escrever:
		gesto_fala_fixado = true
		escrita.iniciar(fala_texto.texto)
		escrita_estado_anterior = ""
		celular.visible = true
	ultimo_clipe_facial = player.current_animation
	emocao_atual = fala_texto.emocao
	rosto.aplicar(emocao_atual,0,"a",0,1)
	RenderingServer.set_render_loop_enabled(true)
	renderizando = true
	acelerar()
	sub.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	contorno_urgente = 0.5
	registrar_evento("fala_inicio", {"fala_id":fala_texto.id,"autor":fala_texto.autor,"gesto":clipe,"emocao":fala_texto.emocao})
	recibo_fala(fala_texto.id,"exibindo")
	return true

func encerrar_fala(estado := "interrompida", motivo := "") -> void:
	if not cumprimento_dados.is_empty():
		recibo_fala(str(cumprimento_dados.get("id","")),estado,motivo,cumprimento_dados)
		cumprimento_dados.clear()
		mudar("parada",4)
	# Pegar durante a caminhada conserva o ponto exibido como origem do arraste.
	# A conclusão normal continua restaurando a origem sem gravar o deslocamento.
	var conservar_posicao := motivo == "clique" and not is_zero_approx(encenacao.offset)
	if conservar_posicao:
		if retrato: pos_retrato.x += encenacao.offset
		else: fisica.pos.x += encenacao.offset
	cancelar_mensagem(motivo)
	encenacao.limpar()
	andando_encenacao = false
	if conservar_posicao: posicionar()
	ultimo_efeito_facial = ""
	efeitos.iniciar("nenhum")
	sons_reacao.encerrar()
	if not fala_texto.ativo: return
	registrar_evento("fala_"+estado, {"fala_id":fala_texto.id,"autor":fala_texto.autor,"regiao":regiao_contato if motivo == "clique" else "","motivo":motivo,"indice":fala_texto.indice})
	recibo_fala(fala_texto.id,estado)
	rosto.ajustes = {}
	atuacao.limpar()
	fala_texto.cancelar()
	voz.encerrar()
	if escrevendo:
		escrevendo = false
		escrita.ativo = false
		celular.hide()
	emocao_atual = emocao_antes_fala
	estados.mudar("parada",4)
	balao.hide()
	fala_restante = 0
	aplicar_expressao()

func escolher_gesto(emocao: String, pedido := "auto") -> String:
	if pedido != "auto" and catalogo_gestos.clipes.has(pedido) and player.has_animation(pedido): return pedido
	var opcoes: Array = catalogo_gestos.emocoes.get(emocao,[])
	if not opcoes.is_empty():
		var indice := int(indices_gestos.get(emocao,0))
		indices_gestos[emocao] = indice+1
		var nome := str(opcoes[indice%opcoes.size()])
		if player.has_animation(nome): return nome
	var conversa := "conversa_%02d" % indice_conversa
	indice_conversa = (indice_conversa+1)%14
	return conversa if player.has_animation(conversa) else "conversa_00"

func montar_menu_gestos(grupo := "") -> void:
	menu_roupas = true
	var textos: Array = ["Voltar"]
	if grupo.is_empty():
		for emocao in ["Neutra","Felicidade","Raiva","Tristeza","Timidez","Surpresa","Medo"]: textos.append("Gestos: "+emocao)
		for categoria in catalogo_gestos.get("categorias",{}): textos.append("Gestos: "+str(categoria))
	else:
		var nomes: Array = catalogo_gestos.get("categorias",{}).get(grupo,catalogo_gestos.emocoes.get(grupo,[])).duplicate()
		if grupo == "Neutra":
			for i in 14: nomes.append("conversa_%02d" % i)
		for nome in nomes: textos.append("Gesto: "+str(catalogo_gestos.clipes[nome]))
	preencher_menu(textos)

func animacao_concluida(nome: StringName) -> void:
	if str(nome)=="gesto_reverencia" and not cumprimento_dados.is_empty():
		var dados := cumprimento_dados.duplicate(true)
		cumprimento_dados.clear()
		mudar("parada",4)
		mensagens.escrever = true
		mensagens.preparar(dados,emocao_atual)
		return
	if estados.estado == "gesto_ocasional" and str(nome)==estados.clipe:
		mudar("parada",8)
		return
	if fala_texto.ativo and not andando_encenacao and str(nome) in catalogo_gestos.get("pontuais",[]):
		estados.clipe = "conversa_%02d" % indice_conversa
		indice_conversa = (indice_conversa+1)%14
		clipe_apos_caminhada = estados.clipe
		tocar()

func emocao_gesto(nome: String) -> String:
	for emocao in ["Felicidade","Raiva","Tristeza","Timidez","Surpresa","Medo"]:
		if nome in catalogo_gestos.emocoes[emocao]: return emocao
	return "Neutra"

func criar_indicador_mensagem() -> void:
	indicador_mensagem.mouse_filter = Control.MOUSE_FILTER_IGNORE
	indicador_mensagem.z_index = 9
	legenda_mensagem.mouse_filter = Control.MOUSE_FILTER_IGNORE
	legenda_mensagem.add_theme_color_override("font_color",Color("f2dec3"))
	legenda_mensagem.add_theme_font_size_override("font_size",15)
	var estilo := StyleBoxFlat.new()
	estilo.bg_color = Color(0.12,0.10,0.16,0.9)
	estilo.set_corner_radius_all(9)
	estilo.content_margin_left = 12
	estilo.content_margin_right = 12
	estilo.content_margin_top = 7
	estilo.content_margin_bottom = 7
	indicador_mensagem.add_theme_stylebox_override("panel",estilo)
	indicador_mensagem.add_child(legenda_mensagem)
	add_child(indicador_mensagem)
	indicador_mensagem.hide()

func montar_menu_mensagens() -> void:
	menu_roupas = true
	preencher_menu(["Voltar","Modo mensagens: ligado" if modo_mensagens else "Modo mensagens: desligado","Hana responde sozinha: ligada" if hana_auto else "Hana responde sozinha: desligada","Cérebro da Hana: local (Ollama)" if hana_cerebro == "local" else "Cérebro da Hana: Claude","Sons de reação: ligados" if sons_ligados else "Sons de reação: desligados","Respiração ofegante: ligada" if ofegar_ligado else "Respiração ofegante: desligada","Ofegar agora","Voz sintética: ligada" if voz_sintetica else "Voz sintética: desligada","Prévia: leitura","Prévia: surpresa","Prévia: confusão","Prévia: alegria","Prévia: ousadia"])

func atualizar_fase_mensagem() -> void:
	if mensagens.fase=="distraida":
		# Ainda não viu a mensagem: continua o que estava fazendo.
		registrar_evento("fase_mensagem",{"atividade_id":mensagens.id,"autor":mensagens.autor,"fase":mensagens.fase,"tom":mensagens.tom})
		return
	ocioso = 0
	fala_restante = 0
	estados.sono_manual = false
	estados.mudar("sentada" if mensagens.fase=="digitando" and not retrato else "gesto",65)
	var nome := ("celular_jogando" if mensagens.fase=="digitando" else "celular_em_pe") if mensagens.celular() else escolher_gesto(mensagens.emocao())
	# Vai responder escrevendo: não larga o celular; a reação fica no rosto, na voz e nos efeitos.
	var segura: bool = mensagens.escrever and mensagens.autor != "Prévia visual"
	if segura:
		estados.mudar("gesto",65)
		nome = "celular_em_pe"
	estados.clipe = nome
	tocar()
	emocao_atual = mensagens.emocao()
	celular.visible = segura or mensagens.celular()
	legenda_mensagem.text = mensagens.legenda()
	if mensagens.autor=="Prévia visual" and not legenda_mensagem.text.is_empty(): legenda_mensagem.text = "Prévia · "+legenda_mensagem.text
	indicador_mensagem.reset_size()
	if mensagens.fase=="reagindo":
		var perfil: Dictionary = mensagens.CATALOGO.tons[mensagens.tom]
		efeitos.iniciar(perfil.efeito,mensagens.intensidade)
		sons_reacao.ligado = sons_ligados
		if mensagens.intensidade>0: sons_reacao.reagir(perfil.som)
	registrar_evento("fase_mensagem",{"atividade_id":mensagens.id,"autor":mensagens.autor,"fase":mensagens.fase,"tom":mensagens.tom})
	RenderingServer.set_render_loop_enabled(true)
	renderizando = true
	acelerar()
	sub.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	contorno_urgente = 0.5

func passo_mensagens(dt: float) -> void:
	var estava: bool = mensagens.ativo
	if mensagens.passo(dt):
		var anterior: String = mensagens.emocao_anterior
		var dados: Dictionary = mensagens.retirar_resposta()
		celular.hide()
		indicador_mensagem.hide()
		rosto.ajustes = {}
		emocao_atual = anterior
		if not receber_fala(dados,true,modo_mensagens): mudar("parada",4)
	elif estava and not mensagens.ativo:
		registrar_evento("atividade_concluida",{"atividade_id":mensagens.id,"autor":mensagens.autor})
		celular.hide()
		indicador_mensagem.hide()
		rosto.ajustes = {}
		emocao_atual = mensagens.emocao_anterior
		mudar("parada",4)
	if mensagens.visivel():
		ocioso = 0
		estados.tempo = 0
		if celular.visible: celular.alinhar(sk,mensagens.esta_teclando(),mensagens.tempo)

func atualizar_efeitos(fechamento: float) -> void:
	efeitos.olhos.clear()
	for nome in ["cf_J_hitomi_tx_L","cf_J_hitomi_tx_R"]:
		if sk.find_bone(nome)>=0: efeitos.olhos.append(ponto_osso(nome))
	if efeitos.olhos.size()==2:
		efeitos.raio = clampf(efeitos.olhos[0].distance_to(efeitos.olhos[1])*0.18,2,22)
		efeitos.ancora = (efeitos.olhos[0]+efeitos.olhos[1])*0.5
		var meta: Dictionary = rosto.CATALOGO.get("caricatos",{}).get(emocao_atual,{})
		efeitos.fechamento = 1.0-(1.0-fechamento)*(1.0-float(meta.get("fechamento",0)))
		efeitos.pode_mostrar = not escondida and absf(chika.rotation.y)<0.65 and absf(olhar.suavizado.x)<0.55
	if mensagens.ativo:
		var alto: float = sprite.position.y+((limites.position.y-TAM*0.5)*zoom if not retrato else -TAM*zoom*0.5)
		var destino := Vector2(sprite.position.x+28,alto-indicador_mensagem.size.y-12)
		indicador_mensagem.position = destino.clamp(Vector2(16,16),(Vector2(get_window().size)-indicador_mensagem.size-Vector2(16,16)).max(Vector2(16,16)))

func cancelar_mensagem(motivo := "") -> void:
	if not mensagens.ativo and mensagens.resposta.is_empty(): return
	var anterior: String = mensagens.emocao_anterior
	var dados: Dictionary = mensagens.cancelar()
	if not dados.is_empty():
		var id := str(dados.get("id",""))
		recibo_fala(id,"interrompida",motivo,dados)
		if not runtime.is_empty() and not id.is_empty() and id.get_file()==id:
			DirAccess.remove_absolute(runtime.path_join("audio").path_join(id+".wav"))
	registrar_evento("atividade_interrompida",{"atividade_id":mensagens.id,"autor":mensagens.autor,"fase":"cancelada","motivo":motivo})
	celular.hide()
	indicador_mensagem.hide()
	dedos_mensagem.ligado = false
	efeitos.iniciar("nenhum")
	sons_reacao.encerrar()
	rosto.ajustes = {}
	emocao_atual = anterior
	mudar("parada",4)

func ler_atividades() -> void:
	if runtime.is_empty() or escondida or fala_texto.ativo or pressionada or not cumprimento_dados.is_empty() or not mensagens.resposta.is_empty(): return
	var pasta := runtime.path_join("atividades")
	if not DirAccess.dir_exists_absolute(pasta): return
	var arquivos := DirAccess.get_files_at(pasta)
	arquivos.sort()
	for arquivo in arquivos:
		if not arquivo.ends_with(".json"): continue
		var caminho := pasta.path_join(arquivo)
		var dados = JSON.parse_string(FileAccess.get_file_as_string(caminho))
		DirAccess.remove_absolute(caminho)
		if not dados is Dictionary or int(dados.get("pid_destino",-1))!=OS.get_process_id(): continue
		var idade := Time.get_unix_time_from_system()-float(dados.get("criado_em",0))
		if not is_finite(idade) or idade>60 or idade< -5 or dados.get("tipo","")!="leitura" or not mensagens.validar(dados.get("preparacao",{})): continue
		if not dados.get("autor") is String or str(dados.autor).strip_edges().is_empty() or str(dados.autor).length()>48: continue
		if dados.autor=="Hana" and not hana_auto: continue
		if not modo_mensagens:
			registrar_evento("atividade_ignorada",{"atividade_id":arquivo.get_basename(),"autor":dados.autor,"motivo":"modo desligado"})
			continue
		if dados.autor=="Hana" and mensagens.ativo and mensagens.autor!="Prévia visual":
			# A janela de chat pode ter começado a leitura antes do daemon. Renova só a espera.
			mensagens.autor = "Hana"
			if mensagens.fase=="esperando": mensagens.restante = maxf(mensagens.restante,float(dados.preparacao.get("duracao",20)))
			return
		cancelar_mensagem("nova leitura")
		mensagens.iniciar(dados.get("preparacao",{}),dados.autor,arquivo.get_basename(),emocao_atual)
		return

func registrar_evento(tipo: String, dados: Dictionary = {}) -> void:
	sequencia_evento += 1
	ultimo_evento = dados.duplicate(true)
	ultimo_evento.merge({"tipo":tipo,"sessao":sessao_eventos,"sequencia":sequencia_evento,"pid":OS.get_process_id(),"timestamp":Time.get_unix_time_from_system(),"boneca":boneca,"interacao":modo_toque},true)
	if runtime.is_empty(): return
	var pasta := runtime.path_join("eventos")
	DirAccess.make_dir_recursive_absolute(pasta)
	var caminho := pasta.path_join("%020d-%010d-%010d.json" % [int(Time.get_unix_time_from_system()*1000000),OS.get_process_id(),sequencia_evento])
	var f := FileAccess.open(caminho+".tmp",FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(ultimo_evento))
		f.close()
		DirAccess.rename_absolute(caminho+".tmp",caminho)
	var arquivos := DirAccess.get_files_at(pasta)
	arquivos.sort()
	for i in maxi(0,arquivos.size()-256): DirAccess.remove_absolute(pasta.path_join(arquivos[i]))

# --- Resposta escrita no celular (modo mensagens) ---
func passo_escrita(dt: float) -> void:
	escrita.passo(dt)
	fala_texto.indice = escrita.maximo
	fala_texto.abertura = 0
	celular.visible = true
	celular.alinhar(sk,escrita.batendo(),escrita.tempo)
	ocioso = 0
	estados.tempo = 0
	if escrita.estado != escrita_estado_anterior:
		# Pausa para pensar: às vezes resmunga baixinho (voz original do jogo).
		if escrita.estado == "pensando" and randf() < 0.6: sons_reacao.reagir("pensando")
		# Gestos originais: toca a tela com o indicador, só segura para pensar, tira o dedo ao enviar.
		var pose: String = {"pensando":"celular_em_pe","enviando":"celular_enviar"}.get(escrita.estado,"celular_digitar")
		if pose != "celular_digitar" or escrita_estado_anterior in ["","pensando","enviando"]:
			estados.clipe = pose
			tocar()
		escrita_estado_anterior = escrita.estado
	if not escrita.ativo: fala_texto.ativo = false

func concluir_escrita() -> void:
	ultima_conversa = Time.get_unix_time_from_system()
	gravar_historico(fala_texto.texto, fala_texto.autor)
	escrevendo = false
	celular.hide()
	publicar_chat()

func enviar_rapida(texto: String) -> void:
	# Bolha curta durante uma espera longa; id próprio para não colidir com a resposta.
	if not hana_auto or not modo_mensagens: return
	gravar_historico(texto, "Hana", true)
	registrar_evento("mensagem_rapida",{"atividade_id":mensagens.id,"texto":texto})

func gravar_historico(texto: String, autor: String, id_novo := false) -> void:
	if prova and OS.get_environment("MASCOTE_CHAT").is_empty(): return
	DirAccess.make_dir_recursive_absolute(chat_pasta)
	var agora := Time.get_unix_time_from_system()
	var ident := "%020d-%08x" % [int(agora*1000000.0)*1000, randi()]
	if not id_novo and autor=="Hana" and not fala_texto.id.is_empty() and fala_texto.id.get_file()==fala_texto.id:
		ident = fala_texto.id
		if FileAccess.file_exists(chat_pasta.path_join(ident+"-personagem.json")): return
	var f := FileAccess.open(chat_pasta.path_join(ident+"-personagem.tmp"), FileAccess.WRITE)
	if f == null: return
	f.store_string(JSON.stringify({"id":ident,"origem":"personagem","autor":autor,"boneca":boneca,"texto":texto,"criado_em":agora}))
	f.close()
	DirAccess.rename_absolute(chat_pasta.path_join(ident+"-personagem.tmp"), chat_pasta.path_join(ident+"-personagem.json"))

func publicar_chat() -> void:
	if runtime.is_empty(): return
	var fase := ""
	var texto := ""
	if escrevendo:
		fase = escrita.estado
		texto = escrita.visivel()
	elif mensagens.ativo and mensagens.autor != "Prévia visual": fase = mensagens.fase_publica()
	# O carimbo de 2 s mantém o arquivo "vivo" para a janela de chat.
	var assinatura := "%s|%d|%d" % [fase, texto.length(), int(Time.get_unix_time_from_system()/2.0)]
	if assinatura == chat_assinatura: return
	chat_assinatura = assinatura
	var pasta := runtime.path_join("chat")
	DirAccess.make_dir_recursive_absolute(pasta)
	var f := FileAccess.open(pasta.path_join("escrevendo.tmp"), FileAccess.WRITE)
	if f == null: return
	f.store_string(JSON.stringify({"fase":fase,"texto":texto,"autor":fala_texto.autor if escrevendo else mensagens.autor,"timestamp":Time.get_unix_time_from_system()}))
	f.close()
	DirAccess.rename_absolute(pasta.path_join("escrevendo.tmp"), pasta.path_join("escrevendo.json"))

func ler_chat() -> void:
	# Mensagem escrita pelo usuário na janela de chat: ela pega o celular e lê.
	if not modo_mensagens or escondida or fala_texto.ativo or mensagens.ativo or pressionada: return
	var pasta := runtime.path_join("chat").path_join("entrada")
	if not DirAccess.dir_exists_absolute(pasta): return
	var arquivos := Array(DirAccess.get_files_at(pasta)).filter(func(a): return a.ends_with(".json"))
	if arquivos.is_empty(): return
	arquivos.sort()
	# Várias mensagens juntas: lê todas (o tempo de leitura soma o texto).
	var caracteres := 0
	for a in arquivos:
		var lido = JSON.parse_string(FileAccess.get_file_as_string(pasta.path_join(a)))
		if lido is Dictionary: caracteres += str(lido.get("texto","")).length()
		DirAccess.remove_absolute(pasta.path_join(a))
	var id: String = arquivos[-1].get_basename()
	# Tempo até "ver": no meio da conversa vê quase na hora; depois de um silêncio, termina o que fazia.
	var agora := Time.get_unix_time_from_system()
	var distracao := randf_range(0.3,1.0) if agora-ultima_conversa < 45.0 else randf_range(1.8,4.5)
	if Time.get_datetime_dict_from_system().hour < 6: distracao += randf_range(0.5,2.0)
	if estados.estado in ["cochilo","dormindo"]: distracao += randf_range(2.0,4.0)
	ultima_conversa = agora
	mensagens.permitir_rapida = hana_auto
	mensagens.iniciar({"tom":"neutro","caracteres":caracteres,"distracao":distracao,"duracao":60},"Usuário",id,emocao_atual)
	registrar_evento("mensagem_chat",{"mensagem_id":id,"distracao":distracao})
