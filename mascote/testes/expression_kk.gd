extends SceneTree
var casos := 0
var erros: Array = []
var amostras: Array = []
const Correcao = preload("res://expression_kk.gd")
func verificar(ok: bool, texto: String) -> void:
	casos += 1
	if not ok: erros.append(texto)
func _initialize() -> void: call_deferred("provar")
func vetor(v: Vector3) -> Array: return [v.x,v.y,v.z]
func pose(sk: Skeleton3D, i: int) -> Dictionary:
	var q := sk.get_bone_pose_rotation(i)
	return {"p":vetor(sk.get_bone_pose_position(i)),"q":[q.x,q.y,q.z,q.w],"s":vetor(sk.get_bone_pose_scale(i))}
func entrada(app) -> Dictionary:
	var usados := {}
	for ref in app.expression.dados.references:
		if ref.get("virtual",false): continue
		var i: int = app.sk.find_bone(ref.name)
		while i >= 0:
			usados[i] = true
			i = app.sk.get_bone_parent(i)
	var r := {}
	for i in usados:
		var p: int = app.sk.get_bone_parent(i)
		var v := pose(app.sk,i)
		v["parent"] = app.sk.get_bone_name(p) if p >= 0 else ""
		r[app.sk.get_bone_name(i)] = v
	return r
func provar() -> void:
	for ordem in [3,4,5]:
		for x in [-70,0,40,125]:
			for y in [-65,0,60]:
				for z in [-75,0,50]:
					var q := Correcao.quaternion(ordem,Vector3(x,y,z))
					var volta := Correcao.quaternion(ordem,Correcao.euler(ordem,q))
					verificar(Basis(q).is_equal_approx(Basis(volta)),"conversão de rotação original "+str([ordem,x,y,z]))
	var app = load("res://mascote.gd").new()
	app.roupas.relogio = func(): return {"hour":12,"weekday":1}
	app.cache = "/tmp/kk-expression-%d.json" % OS.get_process_id()
	app.runtime = ""
	app.prova = true
	root.add_child(app)
	app.set_process(false)
	for n in app.get_children():
		if n is Timer: n.stop()
	for b in app.bonecas:
		app.trocar_boneca(b.id)
		for coordenada in [0,5,6]:
			if coordenada != app.roupa_coordenada:
				app.roupa_coordenada = coordenada
				verificar(app.recarregar_boneca(),"recarga da coordenada "+str(coordenada))
			app.olhar.active = false
			app.secundario.active = false
			app.dedos_mensagem.active = false
			app.expression.active = false
			var e = app.expression
			verificar(e.avisos.is_empty(),b.id+": todas as referências resolvidas em "+str(coordenada))
			verificar(e.ossos.size()==62 and e.indices.size()==38,b.id+": Expression inteiro reconectado")
			verificar(e.get_index()<app.secundario.get_index(),"Expression precede física e mãos suaves")
			for clipe in app.player.get_animation_list():
				e.restaurar()
				app.player.play(clipe)
				app.player.seek(minf(0.6,app.player.get_animation(clipe).length*0.5),true)
				app.player.pause()
				var origem := entrada(app)
				var bases := {}
				for i in app.sk.get_bone_count(): bases[i] = app.sk.get_bone_pose(i)
				e.atualizar()
				var resultado := {}
				for nome in e.dados.targets: resultado[nome] = pose(app.sk,app.sk.find_bone(nome))
				amostras.append({"boneca":b.id,"coordenada":coordenada,"clipe":clipe,"entrada":origem,"saida":resultado})
				for i in app.sk.get_bone_count():
					verificar(app.sk.get_bone_pose(i).is_finite(),b.id+"/"+clipe+": pose finita "+app.sk.get_bone_name(i))
					if not e.indices.has(i): verificar(app.sk.get_bone_pose(i).is_equal_approx(bases[i]),"preserva osso animado "+app.sk.get_bone_name(i))
				var anterior := {}
				for i in e.indices: anterior[i] = app.sk.get_bone_pose(i)
				for passo in 3: e.atualizar()
				for i in e.indices: verificar(app.sk.get_bone_pose(i).is_equal_approx(anterior[i]),b.id+"/"+clipe+": sem deriva "+app.sk.get_bone_name(i))
				e.ligado = false
				e.atualizar()
				for i in e.indices: verificar(app.sk.get_bone_pose(i).is_equal_approx(bases[i]),"desligar restaura animação "+app.sk.get_bone_name(i))
				e.ligado = true
			# A mão de repouso não deve girar a pista j_hand usada pelo Expression.
			app.player.play("idle_em_pe"); app.player.seek(0.6,true); app.player.pause()
			var punhos := {}
			for lado in ["L","R"]:
				var i: int = app.sk.find_bone("cf_j_hand_"+lado)
				punhos[i] = app.sk.get_bone_pose_rotation(i)
			app.secundario.maos_suaves = true
			app.secundario.relaxar = true
			app.secundario.repouso = true
			for passo in 180: app.secundario.atualizar(1.0/30)
			for i in punhos: verificar(app.sk.get_bone_pose_rotation(i).is_equal_approx(punhos[i]),"relaxamento não disputa torção do punho")
			# Callback real, inclusive com AnimationPlayer pausado (sem depender de delta).
			e.restaurar()
			e.atualizar()
			var manual: Dictionary = e.ultimos.duplicate()
			e.restaurar()
			e.active = true
			for f in 3: await process_frame
			for i in manual: verificar(e.ultimos[i].is_equal_approx(manual[i]),"callback SkeletonModifier aplica fórmula da mesma pose")
			e.active = false
	DirAccess.remove_absolute(app.cache)
	var resultado := {"passou":erros.is_empty(),"casos":casos,"erros":erros.slice(0,40),"amostras":amostras.size()}
	FileAccess.open("res://evidencias/expression-kk/godot.json",FileAccess.WRITE).store_string(JSON.stringify(resultado,"  "))
	FileAccess.open("res://evidencias/expression-kk/amostras.json",FileAccess.WRITE).store_string(JSON.stringify(amostras))
	print(JSON.stringify(resultado))
	quit(0 if erros.is_empty() else 1)
