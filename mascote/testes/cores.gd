extends SceneTree
# Renderiza a cena real do mascote em câmera normalizada para comparar os apps.
# O runner cria Xvnc e cache privados; não usa o lançador nem Hyprland.
func _initialize():
 call_deferred("provar")
func provar():
 root.size = Vector2i(900,1000)
 root.content_scale_size = Vector2i(900,1000)
 var destino = OS.get_environment("KK_PROVA_CORES")
 var catalogo = JSON.parse_string(FileAccess.get_file_as_string("res://bonecas/catalogo.json"))
 for b in catalogo:
  var app = load("res://mascote.gd").new()
  app.roupas.relogio = func(): return {"hour":12,"weekday":1}
  app.boneca = b.id
  app.prova = true
  app.cache = destino.path_join("cache-inexistente.json")
  app.runtime = ""
  root.add_child(app)
  OS.low_processor_usage_mode = false
  app.set_process(false)
  app.set_physics_process(false)
  app.olhar.active = false
  for t in app.get_children():
   if t is Timer: t.stop()
  app.sub.size = Vector2i(900,1000)
  app.sub.screen_space_aa = Viewport.SCREEN_SPACE_AA_FXAA
  app.player.play("idle_em_pe")
  app.player.seek(0.6,true)
  app.player.pause()
  for f in 2: await process_frame
  var eye = app.sk.find_bone("cf_J_Eye_tx_L")
  var altura = app.sk.to_global(app.sk.get_bone_global_pose(eye).origin).y - 0.03
  app.camera.projection = Camera3D.PROJECTION_ORTHOGONAL
  app.camera.size = 0.58
  app.camera.position = Vector3(0,altura+0.02,3)
  app.camera.look_at(Vector3(0,altura,0))
  app.sprite.position = Vector2(450,500)
  app.sprite.scale = Vector2.ONE
  app.menu.hide()
  for f in 8: await process_frame
  RenderingServer.force_draw()
  root.get_texture().get_image().save_png(destino.path_join(b.id+".png"))
  print("Cor do mascote capturada: ",b.id)
  app.free()
 quit()
