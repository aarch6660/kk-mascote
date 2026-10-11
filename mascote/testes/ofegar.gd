extends SceneTree
# Respiração ofegante: gatilhos, preferência, comando, boca e integração com roupas/menu.

var casos := 0
var erros: Array = []

func verificar(ok: bool, nome: String) -> void:
	casos += 1
	if not ok: erros.append(nome)

func _initialize() -> void: call_deferred("testar")

func avancar(o, segundos: float, sem_roupa := false, toque := false) -> void:
	var t := 0.0
	while t < segundos:
		o.passo(0.1, sem_roupa, toque, false)
		t += 0.1

func testar() -> void:
	var app = load("res://mascote.gd").new()
	app.roupas.relogio = func(): return {"hour":12,"weekday":1}
	app.cache = "/tmp/kk-ofegar-%d.json" % OS.get_process_id()
	app.runtime = ""
	app.prova = true
	root.add_child(app)
	app.set_process(false)
	for n in app.get_children():
		if n is Timer: n.stop()
	verificar(app.ofegar_ligado == false, "preferência desligada por padrão")
	for b in app.bonecas:
		app.trocar_boneca(b.id)
		app.ofegar.boneca = b.id
		app.ofegar.carregar()
		verificar(app.ofegar.clipes.size() == 4, b.id+": quatro loops originais")
		for c in app.ofegar.clipes:
			verificar(str(c.texto).contains("はぁはぁ") and str(c.arquivo).begins_with("ofegar/h_ko_"), b.id+": só respiração ofegante h_ko")
			verificar(FileAccess.file_exists("res://bonecas/%s/vozes/%s" % [b.id,c.arquivo]), b.id+": arquivo existe")
	var o = app.ofegar
	# Desligado: nenhum gatilho automático.
	o.ligado = false
	o.proximo_aleatorio = 0.05
	o.proximo_sem_roupa = 0.05
	avancar(o, 2.0, true, true)
	verificar(not o.ativo(), "desligado ignora aleatório, sem roupa e toque")
	# Comando funciona mesmo desligado, e termina com fade.
	o.disparar(3, "comando")
	avancar(o, 0.5)
	verificar(o.ativo() and o.playing, "comando toca na hora")
	verificar(o.abertura() >= 0.2, "boca entreaberta enquanto ofega")
	avancar(o, 3.0)
	verificar(o.saindo > 0 or not o.ativo(), "fade-out ao terminar")
	avancar(o, 2.0)
	verificar(not o.ativo() and not o.playing, "silêncio depois do fade")
	verificar(o.abertura() == 0.0, "boca fecha depois")
	# Ligado: cada gatilho.
	o.ligado = true
	o.proximo_aleatorio = 9999
	o.proximo_sem_roupa = 9999
	avancar(o, 0.3, false, true)
	verificar(o.ativo() and o.motivo == "toque", "toque íntimo dispara")
	avancar(o, 12.0)
	verificar(not o.ativo(), "para alguns segundos depois do toque")
	o.proximo_sem_roupa = 0.05
	avancar(o, 0.3, true)
	verificar(o.ativo() and o.motivo == "sem_roupa", "sem roupa dispara")
	verificar(o.proximo_sem_roupa >= 60, "próxima crise sem roupa reagendada")
	o.encerrar()
	o.proximo_aleatorio = 0.05
	avancar(o, 0.3)
	verificar(o.ativo() and o.motivo == "aleatorio", "aleatório dispara")
	verificar(o.proximo_aleatorio >= 600, "próxima crise aleatória em 10–40 min")
	o.ligado = false
	avancar(o, 2.0)
	verificar(not o.ativo(), "desligar no menu interrompe a crise automática")
	verificar("Mamilo esquerdo" in o.INTIMAS and "Região genital" in o.INTIMAS and not "Cabeça" in o.INTIMAS, "regiões íntimas")
	# sem_roupa() segue as peças ocultas da boneca atual.
	app.roupas_ocultas = {}
	verificar(not app.sem_roupa(), "vestida não conta como sem roupa")
	var todas: Array = []
	for tipo in app.pecas_roupa:
		if str(tipo).begins_with("roupa_"): todas.append(tipo)
	app.roupas_ocultas[app.boneca] = todas
	verificar(app.sem_roupa(), "todas as peças ocultas = sem roupa")
	app.roupas_ocultas[app.boneca] = todas.slice(1)
	verificar(not app.sem_roupa(), "uma peça ainda vestida")
	# Preferência salva.
	app.ofegar_ligado = true
	verificar(app.preferencias().get("ofegar") == true, "preferência gravada")
	o.encerrar()
	print(JSON.stringify({"casos":casos,"erros":erros,"passou":erros.is_empty()}))
	quit(0 if erros.is_empty() else 1)
