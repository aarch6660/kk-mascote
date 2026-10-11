extends SceneTree
# Prévia: caixa atual × celular original do jogo nos ossos-âncora k_f_hand{L,R}_00.
func _initialize(): call_deferred("provar")
func capturar(nome):
 for i in 6: await process_frame
 RenderingServer.force_draw()
 root.get_texture().get_image().save_png(OS.get_environment("KK_PROVA_RETRATO").path_join(nome))
func provar():
 root.size = Vector2i(500,560)
 var app = load("res://mascote.gd").new()
 app.roupas.relogio = func(): return {"hour":12,"weekday":1}
 app.prova = true
 app.cache = "/tmp/kk-previa-cel-%d.json" % OS.get_process_id()
 app.runtime = ""
 root.add_child(app)
 app.set_process(false)
 app.olhar.active = false
 app.secundario.active = false
 for t in app.get_children():
  if t is Timer: t.stop()
 app.sub.size = Vector2i(500,560)
 app.sprite.position = Vector2(250,280)
 app.sprite.scale = Vector2.ONE
 app.camera.size = 0.62
 app.camera.position = Vector3(0,1.08,4)
 app.chika.rotation.y = 0.45
 var malha: Mesh = load("res://celular_jogo/p_o_koi_ei_smaho00.obj")
 var mat := StandardMaterial3D.new()
 mat.albedo_texture = load("res://celular_jogo/mt_koi_ei_kagami00.png")
 mat.emission_enabled = true
 mat.emission_texture = load("res://celular_jogo/mt_koi_ei_kagami00_em.png")
 var fones := {}
 for lado in ["L","R"]:
  var anexo := BoneAttachment3D.new()
  anexo.bone_name = "k_f_hand%s_00" % lado
  app.sk.add_child(anexo)
  var m := MeshInstance3D.new()
  m.mesh = malha
  m.material_override = mat
  anexo.add_child(m)
  fones[lado] = anexo
  print("ANCORA ", lado, " ", app.sk.find_bone(anexo.bone_name))
 for clipe in ["celular_em_pe","celular_em_pe_transicao"]:
  var anim: Animation = app.player.get_animation(clipe)
  var n := 6 if clipe.ends_with("transicao") else 3
  for k in n:
   app.player.play(clipe); app.player.seek(anim.length*k/float(n), true); app.player.pause()
   app.sk.force_update_all_bone_transforms()
   for lado in ["L","R"]:
    app.celular.hide()
    for o in fones: fones[o].visible = o == lado
    await capturar("%s_%d_%s.png" % [clipe,k,lado])
   for o in fones: fones[o].visible = false
   app.celular.visible = true
   app.celular.alinhar(app.sk,false,0.0)
   await capturar("%s_%d_caixa.png" % [clipe,k])
 quit()
