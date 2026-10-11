extends SceneTree
var casos := 0
var erros: Array = []
func verificar(ok: bool, texto: String):
 casos += 1
 if not ok: erros.append(texto)
func _initialize(): call_deferred("provar")
func provar():
 var app = load("res://mascote.gd").new()
 app.roupas.relogio = func(): return {"hour":12,"weekday":1}
 app.prova = true
 app.cache = "/tmp/kk-maos-inexistente-%d.json" % OS.get_process_id()
 app.runtime = ""
 root.add_child(app)
 app.set_process(false)
 for timer in app.get_children():
  if timer is Timer: timer.stop()
 for b in app.bonecas:
  app.trocar_boneca(b.id)
  app.olhar.active = false
  app.secundario.active = false
  app.player.play("idle_em_pe");app.player.seek(0.6,true);app.player.pause()
  var bases := {}
  var posicoes := {}
  for lado in ["L","R"]:
   for nome in ["cf_j_hand_","cf_j_index01_","cf_j_index02_","cf_j_thumb01_","cf_j_thumb02_"]:
    var i: int = app.sk.find_bone(nome+lado)
    bases[i] = app.sk.get_bone_pose_rotation(i)
    posicoes[i] = app.sk.get_bone_pose_position(i)
  verificar(app.secundario.poses_maos.size() == 2,b.id+": referências originais preparadas")
  app.secundario.relaxar = true
  app.secundario.repouso = true
  app.secundario.maos_suaves = true
  for passo in 180: app.secundario.atualizar(1.0/30)
  for lado in ["L","R"]:
   var i: int = app.sk.find_bone("cf_j_hand_"+lado)
   verificar(app.sk.get_bone_pose_rotation(i).is_equal_approx(bases[i]),b.id+": suavidade preserva punho animado para Expression "+lado)
   i = app.sk.find_bone("cf_j_index02_"+lado)
   verificar(Quaternion(bases[i]).angle_to(app.sk.get_bone_pose_rotation(i))>0.05,b.id+": índice flexiona em repouso "+lado)
   i = app.sk.find_bone("cf_j_thumb02_"+lado)
   verificar(Quaternion(bases[i]).angle_to(app.sk.get_bone_pose_rotation(i))>0.05,b.id+": polegar acompanha pose "+lado)
  for i in bases:
   verificar(app.sk.get_bone_pose_position(i).is_equal_approx(posicoes[i]),b.id+": comprimento preservado "+str(i))
   verificar(Quaternion(bases[i]).angle_to(app.sk.get_bone_pose_rotation(i))<0.46,b.id+": ajuste limitado "+str(i))
  app.secundario.maos_suaves = false
  app.secundario.relaxar = false
  for passo in 180: app.secundario.atualizar(1.0/30)
  for i in bases:
   var antes: Quaternion = Quaternion(bases[i]).normalized()
   var depois: Quaternion = app.sk.get_bone_pose_rotation(i).normalized()
   verificar(antes.is_equal_approx(depois),b.id+": desligar restaura clipe "+str(i))
  app.player.play("stand_joy_04");app.player.seek(0.8,true);app.player.pause()
  var indicador: int = app.sk.find_bone("cf_j_index02_L")
  var fechado: Quaternion = app.sk.get_bone_pose_rotation(indicador)
  app.secundario.maos_suaves = true
  app.secundario.repouso = false
  for passo in 180: app.secundario.atualizar(1.0/30)
  verificar(fechado.angle_to(app.sk.get_bone_pose_rotation(indicador))<0.001,b.id+": punho do gesto original preservado")
 var resultado = {"casos":casos,"passou":erros.is_empty(),"erros":erros}
 var f = FileAccess.open("res://evidencias/maos-repouso-validacao.json",FileAccess.WRITE)
 f.store_string(JSON.stringify(resultado,"  "));f.close()
 print(JSON.stringify(resultado))
 quit(0 if erros.is_empty() else 1)
