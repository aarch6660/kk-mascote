extends SceneTree
var casos := 0
var erros := []

func verificar(ok: bool, nome: String) -> void:
	casos += 1
	if not ok: erros.append(nome)

func _initialize() -> void: call_deferred("provar")

func provar() -> void:
	var politica = preload("res://roupas_contexto.gd").new()
	for dia in 7:
		for hora in 24:
			politica.relogio = func(): return {"hour":hora,"weekday":dia}
			var esperada := 6 if hora >= 22 or hora < 7 else (5 if dia in [0,6] else 0)
			verificar(politica.coordenada("automatica")==esperada,"horário %d/%d" % [dia,hora])
			for modo in ["uniforme","casual","pijama"]:
				verificar(politica.coordenada(modo)=={"uniforme":0,"casual":5,"pijama":6}[modo],"escolha manual independe do relógio")
	var app = load("res://mascote.gd").new()
	app.cache = "/tmp/kk-hana-roupa-%d.json" % OS.get_process_id()
	app.runtime = ""
	app.prova = true
	app.roupas.relogio = func(): return {"hour":12,"weekday":1}
	root.add_child(app)
	app.set_process(false)
	for t in app.get_children():
		if t is Timer: t.stop()
	verificar(app.roupa_modo=="automatica" and app.roupa_coordenada==0,"padrão automático inicia uniforme em dia útil")
	app.modo_mensagens = true
	app.fala_automatica = false
	app.sons_ligados = false
	app.fisica.fixa = true
	app.retrato = true
	app.perfil = true
	app.zoom = 1.3
	app.pos_retrato = Vector2(800,500)
	app.fisica.pos = Vector2(900,600)
	app.menu.hide()
	app.mudar("parada",60)
	app.roupa_modo = "casual"
	for bloqueio in ["arrastando","pressionada","toque_ativo","escondida","escrevendo"]:
		app.set(bloqueio,true)
		app.atualizar_roupa(2)
		verificar(app.roupa_coordenada==0,"adia troca durante "+bloqueio)
		app.set(bloqueio,false)
	for estado in ["gesto","gesto_ocasional","cumprimento","reacao","andando","assistindo","dormindo"]:
		app.estados.estado = estado
		app.atualizar_roupa(2)
		verificar(app.roupa_coordenada==0,"adia troca em "+estado)
	app.mudar("parada",60)
	app.menu.show()
	app.atualizar_roupa(2)
	verificar(app.roupa_coordenada==0,"menu aberto adia troca")
	app.menu.hide()
	app.fala_restante = 2
	app.atualizar_roupa(2)
	verificar(app.roupa_coordenada==0,"fala automática adia troca")
	app.fala_restante = 0
	app.receber_fala({"id":"teste-roupa","autor":"Codex","texto":"Ensaio local da troca de roupa."})
	app.atualizar_roupa(2)
	verificar(app.roupa_coordenada==0 and app.mensagens.ativo,"ciclo do celular não é interrompido")
	app.encerrar_fala("interrompida","ensaio")
	app.mudar("parada",60)
	app.roupa_modo = "uniforme"
	for boneca in app.bonecas:
		app.trocar_boneca(boneca.id)
		app.roupas_ocultas[boneca.id] = ["roupa_0","roupa_1","roupa_6","acessorio_19"]
		for modo in ["casual","pijama","uniforme"]:
			app.roupa_modo = modo
			app.mudar("parada",60)
			app.transicao_roupa = 0
			var antes: Dictionary = app.preferencias().duplicate(true)
			app.atualizar_roupa(2)
			var n: int = {"uniforme":0,"casual":5,"pijama":6}[modo]
			verificar(app.roupa_coordenada==n,boneca.id+" carrega "+modo)
			verificar(app.preferencias()==antes,"troca preserva todas as preferências")
			verificar(app.sk.find_bone("cf_j_head")>=0 and app.player.has_animation("celular_digitar"),"rig e celular reconectados")
			verificar(not app.piscadas.is_empty() and app.olhar.get_parent()==app.sk and app.secundario.get_parent()==app.sk,"modifiers no novo esqueleto")
			verificar(int(app.secundario.nativa.dados.get("coordenada",0))==n,"solver recebe física da coordenada carregada")
			app.player.seek(0.6,true)
			for i in 12: app.secundario.nativa.atualizar(app.sk,1.0/60.0,Vector3.ZERO)
			for osso in ["cf_j_head","cf_j_hips","cf_j_hand_L","cf_j_hand_R"]:
				verificar(app.sk.get_bone_global_pose(app.sk.find_bone(osso)).is_finite(),"pose física finita depois da troca")
			app.secundario.nativa.restaurar(app.sk)
			verificar(app.roupa_atual().nome==modo and app.roupa_atual().coordenada==n,"estado informa roupa efetiva")
			for m in app.malhas:
				if m.mesh.get_surface_count()==0: continue
				var tipo: String = m.mesh.surface_get_material(0).resource_name.get_slice("__",0)
				if tipo in antes.roupas_ocultas[boneca.id]: verificar(not m.visible,"ocultação aplicada por tipo presente")
			var corpos := 0
			for m in app.malhas:
				if m.visible and (str(m.name)=="o_body_a" or str(m.name).begins_with("kk_o_body_a_")): corpos += 1
			verificar(corpos==1,"somente uma variante corporal visível")
			app.atualizar_roupa(0.2)
			verificar(app.sprite.modulate.a==1,"transição breve termina")
			app.celular.alinhar(app.sk,false,0)
			verificar(is_instance_valid(app.celular.anexo) and app.celular.anexo.get_parent()==app.sk,"celular volta ao esqueleto atual")
	app.roupa_modo = "automatica"
	app.roupas.relogio = func(): return {"hour":22,"weekday":1}
	app.transicao_roupa = 0
	app.atualizar_roupa(2)
	verificar(app.roupa_coordenada==6,"virada às 22 troca para pijama")
	app.atualizar_roupa(0.2)
	app.roupas.relogio = func(): return {"hour":7,"weekday":0}
	app.atualizar_roupa(2)
	verificar(app.roupa_coordenada==5,"domingo às sete troca para casual")
	app.atualizar_roupa(0.2)
	app.prova = false
	app.salvar()
	var salvas: Dictionary = app.preferencias().duplicate(true)
	app.roupas_ocultas.clear()
	app.roupa_modo = "uniforme"
	app.carregar()
	verificar(app.preferencias()==salvas and not salvas.has("roupa_coordenada"),"cache salva modo e ocultas sem coordenada transitória")
	salvas.erase("roupa_modo")
	salvas.versao = 11
	var arquivo := FileAccess.open(app.cache,FileAccess.WRITE)
	arquivo.store_string(JSON.stringify(salvas)); arquivo.close()
	app.carregar()
	verificar(app.roupa_modo=="automatica" and app.roupas_ocultas==salvas.roupas_ocultas,"migração v11 preserva escolhas e habilita automático")
	app.acao_menu("Roupa: Pijama")
	verificar(app.roupa_modo=="pijama" and not app.menu.visible,"menu seleciona modo e fecha para permitir troca")
	verificar(JSON.parse_string(FileAccess.get_file_as_string(app.cache)).roupa_modo=="pijama","escolha do menu é persistida")
	app.acao_menu("Roupa: Automática")
	verificar(app.roupa_modo=="automatica","menu volta ao automático")
	app.prova = true
	DirAccess.remove_absolute(app.cache)
	var resultado := {"casos":casos,"passou":erros.is_empty(),"erros":erros}
	arquivo = FileAccess.open("res://evidencias/hana-etapa3/headless.json",FileAccess.WRITE)
	arquivo.store_string(JSON.stringify(resultado,"  ")); arquivo.close()
	print(JSON.stringify(resultado))
	quit(0 if erros.is_empty() else 1)
