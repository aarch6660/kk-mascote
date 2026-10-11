extends SceneTree
# Escrita no celular: ritmo (pausas, apagar e reescrever), fluxo vindo do chat e vozes do jogo.
var erros := []
var casos := 0
func verificar(ok: bool, nome: String) -> void:
	casos += 1
	if not ok: erros.append(nome)

func _initialize(): call_deferred("provar")

func linha_do_tempo() -> void:
	var E = preload("res://escrita.gd")
	var curto = E.new()
	curto.iniciar("Oi! Tudo bem?", 7)
	var estados := {}
	for e in curto.eventos: estados[e.estado] = true
	verificar(not estados.has("apagando"), "texto curto não apaga")
	verificar(curto.duracao >= 13*0.055, "texto curto leva tempo de digitar")
	var longo = E.new()
	var texto := "Entendi o que você quis dizer, mas acho que dá para fazer de um jeito mais simples. Primeiro a gente separa as poses, depois testa cada uma na tela e só no fim escolhe as melhores. Se alguma ficar estranha, eu troco sem drama. Combinado? Me avisa quando puder olhar."
	longo.iniciar(texto, 11)
	estados = {}
	for e in longo.eventos: estados[e.estado] = true
	verificar(estados.has("pensando"), "texto longo tem pausa para pensar")
	verificar(estados.has("apagando"), "texto longo apaga e reescreve")
	var anterior := -1.0
	var ordenado := true
	for e in longo.eventos:
		if e.t < anterior: ordenado = false
		anterior = e.t
	verificar(ordenado, "eventos em ordem de tempo")
	var maximo := 0
	var monotono := true
	var visto_apagar := false
	while longo.ativo:
		longo.passo(1.0/30)
		if longo.maximo < maximo: monotono = false
		maximo = longo.maximo
		if longo.estado == "apagando": visto_apagar = true
		verificar(longo.indice <= longo.maximo and longo.indice <= texto.length(), "índice visível nunca passa do escrito")
	verificar(monotono and visto_apagar, "máximo só cresce mesmo quando apaga")
	verificar(longo.visivel() == texto, "termina com a resposta inteira")
	var enorme = E.new()
	enorme.iniciar("a".repeat(1200), 3)
	verificar(enorme.duracao <= 35.0 + E.PAUSA_FINAL + 0.001, "resposta enorme limitada a ~35 s")
	var igual = E.new()
	igual.iniciar(texto, 11)
	verificar(igual.eventos == longo.eventos, "mesma semente, mesmo ritmo")

func provar():
	linha_do_tempo()
	var base := "/tmp/kk-escrita-%d" % OS.get_process_id()
	var runtime := base.path_join("runtime")
	var chat := base.path_join("chat")
	DirAccess.make_dir_recursive_absolute(runtime.path_join("chat/entrada"))
	OS.set_environment("MASCOTE_CHAT", chat)
	root.size = Vector2i(1920,1080)
	var app = load("res://mascote.gd").new()
	app.roupas.relogio = func(): return {"hour":12,"weekday":1}
	app.cache = base.path_join("cache.json")
	app.runtime = ""
	app.prova = true
	root.add_child(app)
	app.set_process(false)
	for t in app.get_children():
		if t is Timer: t.stop()
	app.runtime = runtime
	app.modo_mensagens = true
	app.fala_automatica = false
	# Vozes originais da boneca atual.
	app.sons_reacao.boneca = "chika-haruno"
	app.sons_reacao.carregar_vozes()
	for cat in ["surpresa","choque","duvida","alegria","pensando","suspiro","resmungo","concordar"]:
		verificar(not app.sons_reacao.vozes.get(cat,[]).is_empty(), "Chika tem vozes do jogo: "+cat)
	verificar(app.sons_reacao.voz_do_jogo("pensando") and app.sons_reacao.stream != null, "carrega voz do jogo em tempo de execução")
	verificar(not app.sons_reacao.dados.get("envoltoria",[]).is_empty(), "voz do jogo traz envoltória para a boca")
	app.sons_reacao.stream = null
	# Usuário escreve na janela de chat.
	var f := FileAccess.open(runtime.path_join("chat/entrada/00000000000000000001-teste.json"), FileAccess.WRITE)
	f.store_string("{}"); f.close()
	app.ler_chat()
	verificar(app.mensagens.ativo and app.mensagens.fase=="lendo" and app.mensagens.autor=="Usuário", "mensagem do chat: pega o celular e lê")
	verificar(DirAccess.get_files_at(runtime.path_join("chat/entrada")).is_empty(), "aviso do chat é consumido")
	app._process(2.0)
	app._process(1.2)
	verificar(app.mensagens.fase=="pensando", "sem resposta ainda: fica pensando")
	var escrevendo_json = JSON.parse_string(FileAccess.get_file_as_string(runtime.path_join("chat/escrevendo.json")))
	verificar(escrevendo_json is Dictionary and escrevendo_json.fase=="pensando", "janela de chat vê que ela está pensando")
	# Resposta do agente chega com outro tom: ela reage de novo (chocada) antes de escrever.
	var resposta := {"id":"r1","autor":"Claude","texto":"Sério?! Não acredito que você fez isso. Mas tá, vamos consertar juntos com calma, uma coisa de cada vez, combinado?","emocao":"Confiança","preparacao":{"tom":"chocado"},"atuacao":[{"indice":0,"emocao":"Espanto","som":"choque"},{"indice":40,"emocao":"Sorriso travesso","som":"alegria"}]}
	verificar(app.receber_fala(resposta), "resposta do agente aceita durante a espera do chat")
	verificar(app.mensagens.fase=="reagindo" and app.emocao_atual=="Espanto", "reage chocada ao receber o tom da resposta")
	app._process(1.2)
	verificar(app.mensagens.fase=="pensando", "pensa antes de escrever")
	app._process(2.1)
	app._process(0.01)
	verificar(app.escrevendo and app.player.current_animation=="celular_digitar" and app.celular.visible, "escreve no celular tocando a tela")
	# Pose assentada (sem a mistura de entrada) para medir a orientação da tela.
	app.player.play("celular_digitar", 0.0)
	app.player.seek(0.5, true)
	app.sk.force_update_all_bone_transforms()
	await process_frame
	await process_frame
	var olho: Vector3 = app.sk.to_global(app.sk.get_bone_global_pose(app.sk.find_bone("cf_J_Eye_tx_L")).origin)
	var tela_normal: Vector3 = app.celular.malha.global_basis.y.normalized()
	verificar(tela_normal.dot((olho-app.celular.malha.global_position).normalized()) > 0.5, "tela do celular voltada para os olhos dela")
	var fases := {}
	for i in 1200:
		app._process(0.05)
		if app.escrevendo: fases[app.escrita.estado] = true
		var viva = JSON.parse_string(FileAccess.get_file_as_string(runtime.path_join("chat/escrevendo.json")))
		if app.escrevendo and viva is Dictionary and viva.fase in ["digitando","apagando"]:
			verificar(resposta.texto.begins_with(viva.texto), "chat recebe o texto parcial correto")
		if not app.fala_texto.ativo: break
	verificar(fases.has("digitando") and fases.has("apagando") and fases.has("pensando"), "durante a escrita: digita, apaga e pensa")
	verificar(not app.escrevendo and not app.celular.visible, "envia e guarda o celular")
	var historico := Array(DirAccess.get_files_at(chat)).filter(func(a): return a.ends_with("-personagem.json"))
	verificar(historico.size()==1, "resposta enviada vai para o histórico do chat")
	if historico.size()==1:
		var m = JSON.parse_string(FileAccess.get_file_as_string(chat.path_join(historico[0])))
		verificar(m.texto==resposta.texto and m.autor=="Claude" and m.origem=="personagem", "histórico guarda texto e autor")
	var recibo = JSON.parse_string(FileAccess.get_file_as_string(runtime.path_join("recibos-fala/r1.json")))
	verificar(recibo is Dictionary and recibo.estado=="concluida", "recibo concluído ao enviar")
	# Voz sintética desligada: fala fora do modo mensagens descarta o áudio.
	app.modo_mensagens = false
	app.voz_sintetica = false
	DirAccess.make_dir_recursive_absolute(runtime.path_join("audio"))
	f = FileAccess.open(runtime.path_join("audio/r2.wav"), FileAccess.WRITE)
	f.store_string("x"); f.close()
	verificar(app.receber_fala({"id":"r2","autor":"Claude","texto":"Oi!","audio":{"arquivo":"r2.wav"}}) and app.voz.dados.is_empty(), "voz sintética desligada: só texto")
	verificar(not FileAccess.file_exists(runtime.path_join("audio/r2.wav")), "áudio descartado é apagado")
	app.encerrar_fala()
	var prefs: Dictionary = app.preferencias()
	verificar(prefs.has("voz_sintetica") and prefs.voz_sintetica==false, "preferência de voz sintética salva, desligada por padrão")
	# Libera a cena e deixa o servidor de áudio retirar os playbacks antes de sair.
	app.queue_free()
	for i in 8: await process_frame
	OS.execute("rm", ["-rf", base])
	var resultado := {"passou":erros.is_empty(),"erros":erros,"casos":casos}
	print(JSON.stringify(resultado))
	quit(0 if erros.is_empty() else 1)
