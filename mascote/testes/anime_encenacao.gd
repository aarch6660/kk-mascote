extends SceneTree

var casos := 0
var erros: Array[String] = []
var app

func verificar(ok: bool, descricao: String) -> void:
	casos += 1
	if not ok:
		erros.append(descricao)

func _initialize() -> void:
	call_deferred("provar")

func tick_no_indice(dt: float, indice: int) -> void:
	app.fala_texto.indice = indice
	app._process(dt)

func nova_fala(id: String, cenas: Array, emocao := "Felicidade") -> Dictionary:
	return {
		"id": id,
		"autor": "Codex — teste de encenação",
		"texto": ("Uma explicação de teste em várias partes. ").repeat(8),
		"emocao": emocao,
		"atuacao": cenas,
	}

func escrever_cache(dados: Dictionary) -> void:
	var arquivo := FileAccess.open(app.cache, FileAccess.WRITE)
	assert(arquivo != null)
	arquivo.store_string(JSON.stringify(dados))
	arquivo.close()

func provar() -> void:
	root.size = Vector2i(1920, 1080)
	app = load("res://mascote.gd").new()
	app.roupas.relogio = func(): return {"hour":12,"weekday":1}
	app.cache = "/tmp/kk-anime-encenacao-%d.json" % OS.get_process_id()
	app.runtime = ""
	app.prova = true
	root.add_child(app)
	app.set_process(false)
	for timer in app.find_children("*", "Timer", true, false): timer.stop()
	app.fala_automatica = false
	app.modo_mensagens = false
	app.atuacao_natural = false
	app.estilo_anime = true
	app.olhar.active = false
	app.secundario.active = false
	app.fisica.base = 1080
	app.fisica.largura = 1920
	app.zoom = 0.75
	app.menu.hide()

	# Cache antigo sem estilo_anime: os campos existentes sobrevivem e o novo usa o padrão.
	escrever_cache({
		"versao": 9,
		"modo": "passeio",
		"fixa": true,
		"posicao": [960, 1080],
		"escala": 0.82,
		"modo_mensagens": false,
		"fala_automatica": false,
		"boneca": "chika-haruno",
	})
	app.carregar()
	verificar(app.fisica.fixa and app.zoom == 0.82 and app.modo_mensagens == false, "cache anterior preserva fixação, escala e modo mensagens")
	verificar(app.estilo_anime, "cache anterior sem campo novo mantém estilo anime padrão")
	verificar(app.rosto.PERFIS.size() == 28, "catálogo mantém 28 perfis disponíveis")
	verificar(app.PERFIS_ANIME.get("Felicidade", "") == "Encantada", "estilo anime mapeia Felicidade para Encantada")

	var prefs_anteriores: Dictionary = app.preferencias().duplicate(true)
	app.acao_menu("Estilo anime: ligado")
	verificar(not app.estilo_anime and app.preferencias().estilo_anime == false, "ação de menu desliga estilo e atualiza preferências")
	app.prova = false
	app.salvar()
	app.prova = true
	app.estilo_anime = true
	app.carregar()
	verificar(not app.estilo_anime, "estilo anime alterado pelo menu persiste no cache privado")
	for chave in ["fixa", "escala", "modo_mensagens", "fala_automatica", "boneca"]:
		verificar(app.preferencias()[chave] == prefs_anteriores[chave], "cache preserva preferência anterior: "+chave)
	app.acao_menu("Estilo anime: desligado")
	verificar(app.estilo_anime, "menu permite reativar estilo anime")
	app.fisica.fixa = true
	app.fisica.pos = Vector2(960, 1080)
	app.fisica.apoio = ""

	# Fala em personagem fixada: caminha visualmente sem deslocar a posição física persistida.
	var cenas := [
		{"indice": 0, "deslocamento": {"pixels": 120, "duracao": 1.0}, "enquadramento": "corpo"},
		{"indice": 5, "emocao": "Surpresa"},
		{"indice": 30, "gesto": "stand_joy_04"},
		{"indice": 50, "deslocamento": {"pixels": 0, "duracao": 0.5}, "enquadramento": "normal"},
	]
	var posicao_fisica: Vector2 = app.fisica.pos
	var preferencias_antes_fala: Dictionary = app.preferencias().duplicate(true)
	verificar(app.receber_fala(nova_fala("passeio-fixo", cenas)), "recebe cenas com deslocamento e enquadramento")
	tick_no_indice(0.01, 0)
	verificar(app.encenacao.offset > 0 and app.andando_encenacao, "deslocamento começa durante fala fixa")
	verificar(app.player.current_animation == "caminhar", "clipe caminhar acompanha deslocamento")
	verificar(app.fisica.pos == posicao_fisica, "deslocamento de fala não altera posição física")
	verificar(app.emocao_atual == "Encantada", "fala feliz usa perfil caricatural Encantada")

	# O early return em fullscreen congela o deslocamento e pausa o clipe; reaparecer retoma.
	var offset_oculto: float = app.encenacao.offset
	var tempo_oculto: float = app.encenacao.tempo
	app.escondida = true
	app._process(0.7)
	verificar(app.encenacao.offset == offset_oculto and app.encenacao.tempo == tempo_oculto, "fullscreen congela offset e tempo da encenação")
	verificar(not app.player.is_playing(), "fullscreen pausa AnimationPlayer")
	app.escondida = false
	app._process(0.01)
	verificar(app.player.is_playing(), "voltar de fullscreen retoma AnimationPlayer")

	for _i in 10: tick_no_indice(0.1, 0)
	verificar(is_equal_approx(app.encenacao.offset, 120.0) and not app.andando_encenacao, "deslocamento termina no alvo sem continuar andando")
	tick_no_indice(0.001, 15)
	verificar(app.atuacao.proxima == 2 and app.atuacao.emocao == "Surpresa", "salto de índice aplica cena intermediária")
	tick_no_indice(0.001, 40)
	verificar(app.atuacao.proxima == 3 and app.player.current_animation == "stand_joy_04", "gesto de fala substitui caminhada ao terminar o trecho")
	tick_no_indice(0.001, 55)
	verificar(app.atuacao.proxima == 4 and app.encenacao.enquadramento == "normal" and app.encenacao.direcao == -1, "cena pulada inicia retorno ao zero e restaura enquadramento")
	for _i in 6: tick_no_indice(0.1, 55)
	verificar(is_zero_approx(app.encenacao.offset) and not app.andando_encenacao, "retorno conclui no offset zero")
	verificar(app.player.current_animation == "stand_joy_04", "após caminhar restaura gesto escolhido")
	verificar(app.preferencias() == preferencias_antes_fala, "fala não altera preferências persistentes")

	# Apoio na tela também permite deslocamento limitado.
	app.encerrar_fala()
	app.retrato = false
	app.perfil = false
	app.fisica.fixa = false
	app.fisica.apoio = "tela"
	app.fisica.vel = Vector2.ZERO
	app.fisica.pos = Vector2(960, app.fisica.base)
	verificar(app.receber_fala(nova_fala("apoio-tela", [{"indice": 0, "deslocamento": {"pixels": -60, "duracao": 0.5}}])), "recebe fala apoiada na tela")
	tick_no_indice(0.01, 0)
	verificar(app.encenacao.offset < 0 and app.encenacao.offset >= -180, "apoio tela limita deslocamento à esquerda")
	app.encerrar_fala()

	# Retrato conserva âncora; enquadramento corpo abre a câmera e o segundo acento retorna.
	app.retrato = true
	app.perfil = false
	app.pos_retrato = Vector2(900, 560)
	app.configurar_camera()
	var camera_busto: float = app.camera.size
	var ancora_retrato: Vector2 = app.pos_retrato
	var cenas_retrato := [
		{"indice": 0, "deslocamento": {"pixels": 100, "duracao": 1.0}, "enquadramento": "corpo"},
		{"indice": 25, "deslocamento": {"pixels": 0, "duracao": 0.5}, "enquadramento": "normal"},
	]
	verificar(app.receber_fala(nova_fala("retrato", cenas_retrato)), "recebe fala em retrato")
	tick_no_indice(0.01, 0)
	tick_no_indice(0.1, 0)
	verificar(app.encenacao.offset > 0 and app.pos_retrato == ancora_retrato, "retrato desloca apenas a imagem e mantém âncora")
	verificar(app.camera.size > camera_busto, "enquadramento corpo abre temporariamente a câmera")
	tick_no_indice(0.001, 35)
	verificar(app.encenacao.enquadramento == "normal", "cena retrato restaura enquadramento normal")
	for _i in 6: tick_no_indice(0.1, 35)
	verificar(is_zero_approx(app.encenacao.offset) and app.pos_retrato == ancora_retrato, "retrato volta ao centro transitório sem mover posição salva")
	for _i in 20: tick_no_indice(0.1, 35)
	verificar(app.camera.size < camera_busto + 0.1, "câmera retorna ao busto após encenação")

	# Apoio estreito limita o palco; ao desaparecer, o offset sai da faixa sem passear no ar.
	app.encerrar_fala()
	app.retrato = false
	app.fisica.fixa = false
	app.fisica.pos = Vector2(930, 600)
	app.fisica.pisos = [{"address": "A", "x": 900.0, "y": 600.0, "width": 60.0}]
	app.fisica.apoio = "A"
	verificar(app.receber_fala(nova_fala("apoio-estreito", [{"indice": 0, "deslocamento": {"pixels": 180, "duracao": 1.0}}])), "recebe fala sobre apoio estreito")
	tick_no_indice(0.1, 0)
	for _i in 4: tick_no_indice(0.1, 0)
	verificar(app.encenacao.offset <= 10.0, "apoio estreito limita offset ao topo disponível")
	app.fisica.pisos.clear()
	app.fisica.apoio = ""
	tick_no_indice(0.1, 0)
	verificar(is_zero_approx(app.encenacao.offset) and not app.andando_encenacao, "apoio removido limita e encerra deslocamento visual")

	# Pegar com deslocamento grande cancela a fala sem fazer a personagem saltar
	# para trás; só a posição escolhida pela interação deve mudar nas preferências.
	for em_retrato in [false, true]:
		app.encerrar_fala()
		app.retrato = em_retrato
		app.perfil = false
		app.fisica.fixa = true
		app.fisica.pos = Vector2(960, 800)
		app.pos_retrato = Vector2(900, 560)
		app.configurar_camera()
		var preferencias_esperadas: Dictionary = app.preferencias().duplicate(true)
		verificar(app.receber_fala(nova_fala("clique-cancela", [{"indice": 0, "deslocamento": {"pixels": 80, "duracao": 1.0}, "enquadramento": "corpo"}])), "recebe fala para teste de clique")
		tick_no_indice(0.5, 0)
		app.posicionar() # Headless não gera a silhueta que normalmente chama posicionar.
		var deslocamento_ao_pegar: float = app.encenacao.offset
		verificar(deslocamento_ao_pegar > 30, "teste pega durante deslocamento visual significativo")
		var origem_exibida: Vector2 = (app.pos_retrato if em_retrato else app.fisica.pos) + Vector2(deslocamento_ao_pegar, 0)
		var imagem_ao_pegar: Vector2 = app.sprite.position
		var id_cancelado: String = app.fala_texto.id
		app.poligono = PackedVector2Array([Vector2.ZERO, Vector2(1920, 0), Vector2(1920, 1080), Vector2(0, 1080)])
		var clique := InputEventMouseButton.new()
		clique.button_index = MOUSE_BUTTON_LEFT
		clique.pressed = true
		clique.position = Vector2(960, 540)
		app._input(clique)
		verificar(not app.fala_texto.ativo and app.fala_texto.id == id_cancelado, "clique no mascote cancela a fala atual")
		verificar(is_zero_approx(app.encenacao.offset) and app.encenacao.enquadramento == "normal", "cancelamento limpa offset e enquadramento")
		verificar(app.sprite.position.is_equal_approx(imagem_ao_pegar), "pegar mantém a posição visual sem salto para trás")
		verificar(not app.mensagens.ativo and app.runtime.is_empty(), "cancelamento não inicia mensagem nem runtime")
		var delta_mouse := Vector2(45, -20)
		var movimento := InputEventMouseMotion.new()
		movimento.position = clique.position + delta_mouse
		app._input(movimento)
		var destino: Vector2 = app.pos_retrato if em_retrato else app.fisica.pos
		verificar(destino.is_equal_approx(origem_exibida + delta_mouse), "arraste parte da origem exibida durante a caminhada")
		clique.position = movimento.position
		clique.pressed = false
		app._input(clique)
		preferencias_esperadas["posicao_retrato" if em_retrato else "posicao"] = [destino.x, destino.y]
		preferencias_esperadas.fixa = not em_retrato
		verificar(app.preferencias() == preferencias_esperadas, "arraste conserva preferências além da posição e fixação escolhidas")

	app.encerrar_fala()
	app.player.stop()
	var caminho_cache: String = app.cache
	app.free()
	DirAccess.remove_absolute(caminho_cache)
	var resultado := {"passou": erros.is_empty(), "casos": casos, "erros": erros}
	print(JSON.stringify(resultado))
	quit(0 if erros.is_empty() else 1)
