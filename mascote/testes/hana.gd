extends SceneTree
# Integração da Hana: leitura única, recibos, escrita/balão, histórico e preferências.
var casos := 0
var erros := []

func verificar(ok: bool, nome: String) -> void:
	casos += 1
	if not ok: erros.append(nome)

func _initialize(): call_deferred("provar")

func provar():
	var base := "/tmp/kk-hana-godot-%d" % OS.get_process_id()
	var runtime := base.path_join("runtime")
	var chat := base.path_join("chat")
	OS.set_environment("MASCOTE_CHAT", chat)
	DirAccess.make_dir_recursive_absolute(runtime.path_join("atividades"))
	root.size = Vector2i(1920,1080)
	var app = load("res://mascote.gd").new()
	app.roupas.relogio = func(): return {"hour":12,"weekday":1}
	app.runtime = ""
	app.cache = base.path_join("cache.json")
	app.prova = true
	root.add_child(app)
	app.set_process(false)
	for t in app.get_children():
		if t is Timer: t.stop()
	app.runtime = runtime
	app.fala_automatica = false
	app.sons_ligados = false
	app.sons_reacao.ligado = false
	app.voz_sintetica = false
	app.modo_mensagens = true
	verificar(app.hana_auto and app.preferencias().versao==12, "Hana ligada por padrão")
	var preferencias: Dictionary = app.preferencias().duplicate(true)
	app.montar_menu_mensagens()
	verificar(app.menu.find_children("*","Button",true,false).any(func(b): return b.text.begins_with("Hana responde sozinha:")), "menu oferece Hana")
	app.acao_menu("Hana responde sozinha: ligada")
	var mudadas: Dictionary = app.preferencias().duplicate(true)
	verificar(not app.hana_auto, "menu desliga Hana")
	mudadas.hana_auto = preferencias.hana_auto
	verificar(mudadas==preferencias, "toggle preserva demais preferências")
	verificar(not app.receber_fala({"id":"desligada","autor":"Hana","texto":"Oi"}), "Hana desligada rejeita fila")
	app.acao_menu("Hana responde sozinha: desligada")
	app.menu.hide()
	app.mensagens.escrever = true
	app.mensagens.iniciar({"tom":"neutro","duracao":60},"Usuário","u1","Neutra")
	app.mensagens.passo(0.5)
	var fase_antes: String = app.mensagens.fase
	var restante_antes: float = app.mensagens.restante
	var variacao_antes: int = app.mensagens.variacao
	var f := FileAccess.open(runtime.path_join("atividades/a1.json"),FileAccess.WRITE)
	f.store_string(JSON.stringify({"pid_destino":OS.get_process_id(),"criado_em":Time.get_unix_time_from_system(),"autor":"Hana","tipo":"leitura","preparacao":{"tom":"neutro","duracao":20}})); f.close()
	app.ler_atividades()
	verificar(app.mensagens.autor=="Hana" and app.mensagens.fase==fase_antes and app.mensagens.restante==restante_antes, "não duplica leitura iniciada pelo chat")
	verificar(app.mensagens.variacao==variacao_antes, "continua ciclo existente")
	app.mensagens.autor = "Codex"
	f = FileAccess.open(runtime.path_join("atividades/terminal.json"),FileAccess.WRITE)
	f.store_string(JSON.stringify({"pid_destino":OS.get_process_id(),"criado_em":Time.get_unix_time_from_system(),"autor":"Hana","tipo":"leitura","preparacao":{"tom":"neutro","duracao":20}})); f.close()
	app.ler_atividades()
	verificar(app.mensagens.autor=="Hana" and app.mensagens.variacao==variacao_antes, "continua também leitura sinalizada pelo terminal")
	app.mensagens.passo(3)
	verificar(app.mensagens.fase=="pensando", "aguarda modelo segurando celular")
	f = FileAccess.open(runtime.path_join("atividades/a2.json"),FileAccess.WRITE)
	f.store_string(JSON.stringify({"pid_destino":OS.get_process_id(),"criado_em":Time.get_unix_time_from_system(),"autor":"Hana","tipo":"leitura","preparacao":{"tom":"neutro","duracao":20}})); f.close()
	app.ler_atividades()
	verificar(app.mensagens.fase=="pensando" and app.mensagens.restante==20, "modelo lento renova pensamento sem reler")
	var fala := {"id":"hana-resposta","autor":"Hana","texto":"Tá, anotei. Vou cobrar.","emocao":"Birra","gesto":"conversa_03","preparacao":{"tom":"irritado"}}
	verificar(app.receber_fala(fala), "resposta recebe mesma ponte")
	verificar(app.mensagens.fase=="reagindo", "reage ao tom sem reler")
	for i in 700:
		app._process(0.05)
		if not app.mensagens.ativo and not app.fala_texto.ativo: break
	var arquivos := Array(DirAccess.get_files_at(chat)).filter(func(a): return a.ends_with("-personagem.json"))
	verificar(arquivos.size()==1 and arquivos[0]=="hana-resposta-personagem.json", "escrita registra histórico uma vez com ID estável")
	var recibo = JSON.parse_string(FileAccess.get_file_as_string(runtime.path_join("recibos-fala/hana-resposta.json")))
	verificar(recibo is Dictionary and recibo.estado=="concluida", "recibo confirma entrega")
	app.gravar_historico(fala.texto,"Hana")
	verificar(DirAccess.get_files_at(chat).size()==1, "repetição não duplica histórico")
	app.modo_mensagens = false
	verificar(app.receber_fala({"id":"hana-balao","autor":"Hana","texto":"Aff, fez a tarefa?","emocao":"Birra"}), "balão fora do modo mensagens")
	for i in 700:
		app._process(0.05)
		if not app.fala_texto.ativo: break
	verificar(FileAccess.file_exists(chat.path_join("hana-balao-personagem.json")), "balão também entra no histórico")
	app.modo_mensagens = true
	verificar(app.receber_fala({"id":"hana-clique","autor":"Hana","texto":"Não ignora minha cobrança.","preparacao":{"tom":"irritado"}}), "prepara terceira mensagem")
	app.encerrar_fala("interrompida","clique")
	recibo = JSON.parse_string(FileAccess.get_file_as_string(runtime.path_join("recibos-fala/hana-clique.json")))
	verificar(recibo is Dictionary and recibo.estado=="interrompida", "clique produz recibo sem reenviar")
	verificar(not FileAccess.file_exists(chat.path_join("hana-clique-personagem.json")), "interrompida não registra texto que não foi enviado")
	# Cache antigo mantém posições, tamanho e demais escolhas; cache novo salva o toggle.
	f = FileAccess.open(app.cache,FileAccess.WRITE)
	preferencias.erase("hana_auto")
	preferencias.versao = 10
	f.store_string(JSON.stringify(preferencias)); f.close()
	app.hana_auto = false
	app.carregar()
	verificar(app.hana_auto and app.zoom==preferencias.escala, "cache antigo migra Hana sem mudar escala")
	app.hana_auto = false
	app.prova = false
	app.salvar()
	app.hana_auto = true
	app.carregar()
	verificar(not app.hana_auto, "toggle persiste ao reiniciar")
	app.prova = true
	OS.execute("rm",["-rf",base])
	print(JSON.stringify({"casos":casos,"passou":erros.is_empty(),"erros":erros}))
	quit(0 if erros.is_empty() else 1)
