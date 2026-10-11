extends SceneTree
var erros: Array = []
var casos := 0
const Solver = preload("res://fisica_kk.gd")
const Colisores = preload("res://colisores_kk.gd")
func verificar(ok: bool, texto: String) -> void:
	casos += 1
	if not ok: erros.append(texto)
func _initialize() -> void:
	call_deferred("provar")

func ensaio(fps: int) -> Dictionary:
	var sk := Skeleton3D.new()
	root.add_child(sk)
	for j in 3:
		sk.add_bone("teste"+str(j))
		if j>0: sk.set_bone_parent(j,j-1)
		sk.set_bone_rest(j,Transform3D(Basis.IDENTITY,Vector3(0,-0.15,0) if j>0 else Vector3(0,1,0)))
	sk.reset_bone_poses()
	var s = Solver.new()
	var fonte := {"root_transform":{"name":"teste0"},"component_game_object":"teste0","component_path_id":1,"serialized_parameters":{"UpdateRate":60,"Damping":0.2,"Elasticity":0.2,"Stiffness":0.1,"Inert":0.7,"Radius":0,"Exclusions":[],"EndLength":0,"EndOffset":{},"Force":{},"Gravity":{},"FreezeAxis":0}}
	s.adicionar_classico(sk,fonte,"cabelo_teste")
	var comprimento_max := 0.0
	for f in range(1,fps*3+1):
		s.restaurar(sk)
		var t := float(f)/fps
		sk.position.x = sin(t*TAU)*0.025
		sk.rotation.z = sin(t*2)*0.12
		s.atualizar(sk,1.0/fps,Vector3.ZERO)
		var c: Dictionary = s.cadeias[0]
		for j in range(1,c.particulas.size()):
			var p: Dictionary = c.particulas[j]
			var d: float = Vector3(p.pos).distance_to(c.particulas[p.pai].pos)
			var ref: float = Transform3D(c.frames[j]).origin.distance_to(c.frames[p.pai].origin)
			comprimento_max = maxf(comprimento_max,absf(d-ref))
	var fim: Vector3 = s.cadeias[0].particulas[-1].pos
	var r := {"posicao":fim,"comprimento_erro":comprimento_max,"passos":s.passos}
	sk.free()
	return r

func provar() -> void:
	verificar(Colisores.esfera(Vector3(0.1,0,0),Vector3.ZERO,0.5).is_equal_approx(Vector3(0.5,0,0)),"Esfera projeta partícula para fora")
	verificar(Colisores.esfera(Vector3(1,0,0),Vector3.ZERO,0.5,true).is_equal_approx(Vector3(0.5,0,0)),"Esfera interna mantém contenção")
	verificar(Colisores.capsula(Vector3(0.1,0.5,0),Vector3.ZERO,Vector3.UP,0.5).is_equal_approx(Vector3(0.5,0.5,0)),"Cápsula usa segmento central")
	verificar(Colisores.capsula(Vector3.ZERO,Vector3.ZERO,Vector3.ZERO,0.5).is_finite(),"Colisor degenerado tem resultado finito")
	verificar(is_equal_approx(Colisores.capsula(Vector3(0,0.5,0),Vector3.ZERO,Vector3.UP,0.5).distance_to(Vector3(0,0.5,0)),0.5),"Partícula sobre eixo da cápsula recebe direção perpendicular")
	var a := ensaio(30)
	var b := ensaio(60)
	var c := ensaio(120)
	var lento := ensaio(20)
	verificar(Vector3(lento.posicao).distance_to(b.posicao)<0.001,"20/60fps convergem em até 1mm")
	verificar(Vector3(a.posicao).distance_to(b.posicao)<0.001,"30/60fps convergem em até 1mm")
	verificar(Vector3(b.posicao).distance_to(c.posicao)<0.001,"60/120fps convergem em até 1mm")
	for r in [lento,a,b,c]:
		verificar(float(r.comprimento_erro)<0.00001,"Comprimentos preservados na cadeia clássica")
		verificar(int(r.passos)==180,"Mesma quantidade de passos físicos em 3 segundos")
	var app = load("res://mascote.gd").new()
	app.roupas.relogio = func(): return {"hour":12,"weekday":1}
	app.cache = "/tmp/kk-fisica-nativa-%d.json" % OS.get_process_id()
	app.runtime = ""
	app.prova = true
	root.add_child(app)
	app.set_process(false)
	for n in app.get_children():
		if n is Timer: n.stop()
	var medidas: Array = []
	for boneca in app.bonecas:
		app.trocar_boneca(boneca.id)
		app.olhar.active = false
		app.secundario.active = false
		app.secundario.maos_suaves = false
		app.secundario.dormindo = false
		app.secundario.ligado = true
		var sim = app.secundario.nativa
		# +12 cadeias cf_J_Vagina_Pivot_* do corpo UncensorSelector (BP Innie).
		var esperado := {"chika-haruno":28,"sawai-hinata":29,"mizuno-ayaka":25,"aihara-rena":27}
		verificar(sim.cadeias.size()==esperado[boneca.id],boneca.id+": todas as cadeias de fonte carregadas")
		verificar(sim.avisos.is_empty(),boneca.id+": ossos e parâmetros resolvidos")
		var referencias := {"chika-haruno":[0.1961797383,0.1980898691,0.9656176447,0.0],"sawai-hinata":[0.1126846402,0.1563423201,0.2141617618,-0.000684586752],"mizuno-ayaka":[0.1584837984,0.1792418992,0.6263541855,-0.00024697626],"aihara-rena":[0.1525556335,0.1762778167,0.5730007011,-0.0003646542821]}
		for cadeia in sim.cadeias:
			if cadeia.tipo=="DynamicBone_Ver02" and str(cadeia.fonte.bone_transforms[0].name).begins_with("cf_j_bust"):
				var ref: Array = referencias[boneca.id]
				for p in cadeia.particulas:
					verificar(absf(float(p.damping)-float(ref[0]))<0.00001 and absf(float(p.elasticity)-float(ref[1]))<0.00001 and absf(float(p.stiffness)-float(ref[2]))<0.00001,boneca.id+": parâmetros do card conferem com IL auditado, incluindo terminal")
				verificar(absf(Vector3(cadeia.gravidade).y-float(ref[3]))<0.00000001,boneca.id+": gravidade do card confere com IL")
		for clipe in ["idle_em_pe","conversa_03","stand_joy_08","caminhar"]:
			sim.restaurar(app.sk)
			app.player.play(clipe)
			app.player.seek(0.6,true)
			app.player.pause()
			sim.restaurar(app.sk)
			sim.reiniciar()
			var antes := {}
			var originais := {}
			for i in app.sk.get_bone_count(): originais[i] = app.sk.get_bone_pose_scale(i)
			for i in sim.ossos: antes[i] = app.sk.get_bone_pose(i)
			for f in 90: app.secundario.atualizar(1.0/30)
			for i in app.sk.get_bone_count():
				verificar(app.sk.get_bone_pose(i).is_finite(),boneca.id+": pose finita em "+clipe+"/"+app.sk.get_bone_name(i))
				verificar(app.sk.get_bone_pose_scale(i).is_equal_approx(originais[i]),boneca.id+": escala original em "+clipe+"/"+app.sk.get_bone_name(i))
			var passos_antes: int = sim.passos
			var snapshot := {}
			for i in sim.ossos: snapshot[i] = app.sk.get_bone_pose(i)
			app.secundario.atualizar(0)
			app.secundario.pausado = true
			app.secundario.atualizar(0.1)
			verificar(sim.passos==passos_antes,boneca.id+": zero delta e pausa não avançam física")
			for i in snapshot: verificar(app.sk.get_bone_pose(i).is_equal_approx(snapshot[i]),boneca.id+": pausa preserva pose")
			app.secundario.pausado = false
			app.secundario.ligado = false
			app.secundario.atualizar(1.0/30)
			for i in antes: verificar(app.sk.get_bone_pose(i).is_equal_approx(antes[i]),boneca.id+": desligar restaura animação sem deriva")
			app.secundario.ligado = true
		medidas.append({"boneca":boneca.id,"estado":sim.estado(),"overrides":sim.dados.get("runtime_overrides",{})})
	DirAccess.remove_absolute(app.cache)
	var resultado := {"passou":erros.is_empty(),"casos":casos,"erros":erros,"fps":{"20":lento,"30":a,"60":b,"120":c},"bonecas":medidas}
	FileAccess.open("res://evidencias/corpo-fisica-2026-10-09/teste-fisica-nativa.json",FileAccess.WRITE).store_string(JSON.stringify(resultado,"  "))
	print(JSON.stringify({"passou":erros.is_empty(),"casos":casos,"erros":erros.slice(0,25)}))
	quit(0 if erros.is_empty() else 1)
