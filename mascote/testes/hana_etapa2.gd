extends SceneTree
const GESTOS := ["gesto_ajeitar_cabelo","gesto_mao_boca","gesto_olhar_longe","gesto_maos_juntas","gesto_reverencia"]
var casos := 0
var erros := []

func verificar(ok: bool, nome: String) -> void:
	casos += 1
	if not ok: erros.append(nome)

func _initialize() -> void: call_deferred("provar")

func provar() -> void:
	var e = preload("res://estados.gd").new()
	e.rng.seed = 2
	for i in 100:
		var anterior: String = e.ultimo_ocasional
		var gesto: String = e.sortear_ocasional()
		verificar(gesto!=anterior and gesto in GESTOS and gesto!="gesto_reverencia","gesto ocasional sem repetição/reverência")
	e.prazo_ocasional = 40
	verificar(not e.passo_ocasional(39.9,true),"gesto não toca antes do intervalo")
	verificar(not e.passo_ocasional(100,false),"interação suspende relógio de gestos")
	verificar(e.passo_ocasional(0.2,true) and e.estado=="gesto_ocasional","parada toca gesto ao alcançar prazo")
	verificar(e.prazo_ocasional>=40 and e.prazo_ocasional<=120,"intervalo aleatório quarenta a cento e vinte")
	var vida = preload("res://vida_propria.gd").new()
	vida.relogio = func(): return 2
	vida.proximo_bocejo = 120
	vida.passo(119,true,false)
	verificar(vida.bocejo==0,"bocejo ocasional, não imediato")
	vida.passo(2,true,false)
	vida.passo(1.9,true,false)
	verificar(vida.abertura_bocejo()>0.79 and vida.palpebras>0.1,"madrugada boca aberta e pálpebras pesadas")
	vida.passo(4,true,false)
	verificar(vida.bocejo==0,"bocejo termina")
	vida.relogio = func(): return 5
	vida.passo(5,true,false)
	verificar(vida.palpebras<0.001,"às cinco pálpebras voltam ao normal suavemente")
	vida.passo(1,true,true,100)
	verificar(vida.cabeca().length()>0.001 and vida.cabeca().length()<0.04,"música balança cabeça discretamente")
	vida.passo(2,true,false)
	verificar(vida.cabeca().length()<0.0001,"pausa para balanço sem salto")
	vida.relogio = func(): return 1
	vida.passo(300,false,true)
	verificar(vida.bocejo==0 and vida.cabeca().length()<0.0001,"interação/fala tem prioridade sobre reações locais")
	verificar(vida.fps({})==20,"parada usa vinte FPS")
	for motivo in ["interacao","fala","gesto","movimento","mouse","musica","bocejo"]:
		verificar(vida.fps({motivo:true})==60,"sessenta FPS em "+motivo)
	verificar(vida.fps({"energia":0.041})==60 and vida.fps({"energia":0.039})==20,"limiar de energia física")
	verificar(vida.fps({"oculta":true,"fala":true})==10,"ocultação suspende render mesmo falando")
	var base := "/tmp/kk-hana-vida-%d" % OS.get_process_id()
	var app = load("res://mascote.gd").new()
	app.roupas.relogio = func(): return {"hour":12,"weekday":1}
	app.cache = base.path_join("cache.json")
	app.runtime = ""
	app.prova = true
	root.add_child(app)
	app.set_process(false)
	for t in app.get_children():
		if t is Timer: t.stop()
	app.fisica.fixa = true
	app.olhar.active = false
	app.secundario.active = false
	app.sons_ligados = false
	app.fala_automatica = false
	app.modo_mensagens = true
	var preferencias: Dictionary = app.preferencias().duplicate(true)
	for boneca in app.bonecas:
		app.trocar_boneca(boneca.id)
		for nome in GESTOS:
			var anim: Animation = app.player.get_animation(nome)
			verificar(anim!=null and anim.loop_mode==Animation.LOOP_NONE,boneca.id+"/"+nome+" original toca uma vez")
			app.player.play(nome,0)
			for fracao in [0.0,0.33,0.66,0.99]:
				app.player.seek(anim.length*fracao,true)
				app.player.advance(0)
				for osso in ["cf_j_head","cf_j_hand_L","cf_j_hand_R","cf_j_hips"]:
					verificar(app.sk.get_bone_global_pose(app.sk.find_bone(osso)).is_finite(),boneca.id+"/"+nome+" pose finita")
	app.trocar_boneca(preferencias.boneca)
	app.mudar("parada",60)
	app.contexto_hana = {"janela":{"categoria":"jogo","fullscreen":false,"at":[100,100],"size":[800,600]},"musica":{}}
	app.atualizar_vida(0.1,true)
	verificar(app.estados.estado=="assistindo" and app.player.current_animation=="sentada_idle","jogo em janela usa pose sentada original")
	app.atualizar_olhar()
	verificar(app.olhar.alvo!=Vector2.ZERO,"assistindo olha para centro da janela")
	app.contexto_hana.musica = {"status":"Playing"}
	app.atualizar_vida(0.1,true)
	verificar(app.player.current_animation=="sentada_musica","sentada usa clipe original de música")
	app.contexto_hana.musica = {"status":"Paused"}
	app.atualizar_vida(0.1,true)
	verificar(app.player.current_animation=="sentada_idle","pausa restaura pose sentada")
	app.contexto_hana.janela.categoria = "codigo"
	app.atualizar_vida(0.1,true)
	verificar(app.estados.estado=="parada","troca de janela volta ao normal")
	app.contexto_hana.janela.categoria = "jogo"
	app.contexto_hana.janela.fullscreen = true
	app.atualizar_vida(0.1,true)
	verificar(app.estados.estado=="parada","fullscreen não ativa assistir")
	app.contexto_hana.janela.fullscreen = false
	app.atualizar_vida(0.1,false)
	verificar(app.estados.estado=="parada","interação tem prioridade sobre assistir")
	app.estados.mudar("gesto_ocasional",120)
	app.estados.clipe = GESTOS[0]
	app.tocar()
	app.player.advance(app.player.current_animation_length+0.1)
	verificar(app.estados.estado=="parada","gesto ocasional termina e volta à parada")
	app.modo_mensagens = true
	verificar(app.receber_fala({"id":"cumprimento","autor":"Hana","texto":"Ah, lembrou que eu existo?","gesto":"gesto_reverencia"}),"recebe cumprimento")
	verificar(app.estados.estado=="cumprimento" and not app.mensagens.ativo,"reverência acontece antes do celular")
	app.player.advance(app.player.current_animation_length+0.1)
	verificar(app.cumprimento_dados.is_empty() and app.mensagens.ativo,"depois da reverência começa ciclo de escrever")
	app.encerrar_fala("interrompida","clique")
	app.receber_fala({"id":"interromper","autor":"Hana","texto":"Bom dia.","gesto":"gesto_reverencia"})
	app.encerrar_fala("interrompida","clique")
	verificar(app.cumprimento_dados.is_empty() and not app.mensagens.ativo,"clique cancela reverência sem reenviar")
	app.fisicas_ligadas = false
	app.contexto_hana = {}
	app.vida.peso_musica = 0
	app.vida.bocejo = 0
	app.cursor = Vector2(-10000,-10000)
	app.contorno_urgente = 0
	app.render_pendente = 0
	app.fisica.vel = Vector2.ZERO
	app.fala_restante = 0
	app.mudar("parada",60)
	app.contorno_urgente = 0
	var head: int = app.sk.find_bone("cf_j_head")
	var antes: Transform3D = app.sk.get_bone_pose(head)
	app.atualizar_fps(1.1)
	verificar(Engine.max_fps==20 and OS.low_processor_usage_mode,"parada baixa FPS após estabilizar")
	verificar(app.sk.get_bone_pose(head).is_equal_approx(antes),"troca de FPS conserva a pose sem salto")
	app.pressionada = true
	app.atualizar_fps(0.001)
	verificar(Engine.max_fps==60 and not OS.low_processor_usage_mode,"interação restaura sessenta imediatamente")
	verificar(Engine.physics_ticks_per_second==60,"tick de física permanece sessenta")
	var depois: Dictionary = app.preferencias().duplicate(true)
	depois.fixa = preferencias.fixa
	depois.fisicas_ligadas = preferencias.fisicas_ligadas
	verificar(depois==preferencias,"vida própria preserva preferências")
	var resultado := {"casos":casos,"passou":erros.is_empty(),"erros":erros}
	DirAccess.make_dir_recursive_absolute("res://evidencias/hana-etapa2")
	var arquivo := FileAccess.open("res://evidencias/hana-etapa2/headless.json",FileAccess.WRITE)
	arquivo.store_string(JSON.stringify(resultado,"  ")); arquivo.close()
	print(JSON.stringify(resultado))
	quit(0 if erros.is_empty() else 1)
