extends SceneTree
func _initialize():
 call_deferred("provar")
func provar():
 var app = load("res://ver.gd").new()
 root.add_child(app)
 var visitadas = []
 for _i in app.bonecas.size():
  var ev = InputEventKey.new()
  ev.pressed = true
  ev.keycode = KEY_B
  app._unhandled_input(ev)
  var sk = app.chika.find_children("*","Skeleton3D",true,false)[0]
  assert(app.relatorio.faltantes.is_empty())
  app.player.play("idle_em_pe")
  app.player.advance(0.0)
  var indice = sk.find_bone("cf_j_hand_L")
  var antes = sk.get_bone_pose_rotation(indice)
  app.player.advance(0.6)
  assert(not antes.is_equal_approx(sk.get_bone_pose_rotation(indice)))
  visitadas.append(app.boneca)
 var f = FileAccess.open("res://bonecas/teste_visualizador.json",FileAccess.WRITE)
 f.store_string(JSON.stringify({"tecla":"B","visitadas":visitadas,"idle_movimenta":true},"  "))
 app.queue_free()
 print("Troca B passou: ",visitadas)
 quit(0)
