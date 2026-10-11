extends SceneTree
var casos := 0
var erros: Array = []
func verificar(ok: bool, texto: String) -> void:
	casos += 1
	if not ok: erros.append(texto)
func _initialize() -> void: call_deferred("provar")
func provar() -> void:
	var app = load("res://ver.gd").new()
	root.add_child(app)
	app.set_process(false)
	for b in app.bonecas.size():
		if b > 0: app.trocar_boneca()
		var e = app.expression
		var sk: Skeleton3D = e.get_skeleton()
		verificar(e.avisos.is_empty() and e.ossos.size()==62,app.boneca+": Expression reconectado")
		verificar(e.get_index()<app.fisica_secundaria.get_index(),"Expression antes da física")
		app.fisica_secundaria.active = false
		e.active = false
		for nome in ["parada_relaxada","parada_maos_atras","parada_timida","parada_balanco","gesto_mao_boca","caminhar"]:
			verificar(app.player.has_animation(nome),"clipe presente no visualizador: "+nome)
			if not app.player.has_animation(nome): continue
			app.player.play(nome);app.player.seek(0.6,true);app.player.pause()
			e.atualizar()
			var esperado: Dictionary = e.ultimos.duplicate()
			e.restaurar()
			e.active = true
			for f in 2: await process_frame
			for i in e.indices: verificar(e.ultimos[i].is_equal_approx(esperado[i]),app.boneca+"/"+nome+": callback antes do skinning "+sk.get_bone_name(i))
			e.active = false
			e.restaurar()
	var resultado := {"passou":erros.is_empty(),"casos":casos,"erros":erros}
	FileAccess.open("res://bonecas/expression-visualizador.json",FileAccess.WRITE).store_string(JSON.stringify(resultado,"  "))
	print(JSON.stringify(resultado))
	quit(0 if erros.is_empty() else 1)
