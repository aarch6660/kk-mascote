extends SceneTree
func _initialize(): call_deferred("provar")
func provar():
 root.size = Vector2i(1920,1080)
 var app = load("res://mascote.gd").new()
 app.roupas.relogio = func(): return {"hour":12,"weekday":1}
 app.cache = "/tmp/kk-face-previa-%d.json" % OS.get_process_id()
 app.runtime = ""
 app.prova = true
 root.add_child(app)
 app.set_process(false)
 for t in app.get_children():
  if t is Timer: t.stop()
 app.olhar.active = false
 app.secundario.active = false
 app.acao_menu("Modo perfil")
 app.zoom = 1
 app.pos_retrato = Vector2(960,600)
 app.aplicar_render()
 app.player.play("idle_em_pe")
 app.player.seek(0.6,true)
 app.player.pause()
 app.preparar_retrato()
 for intensidade in [0.0,0.5,1.0]:
  app.rosto.ajustes = {"intensidade":intensidade,"sobrancelhas":"Neutra","boca":"Felicidade"}
  app.rosto.aplicar("Felicidade",0,"a",0,1)
  for i in 4: await process_frame
  RenderingServer.force_draw()
  app.sub.get_texture().get_image().save_png(OS.get_environment("KK_PROVA_RETRATO").path_join("face-%d.png" % int(intensidade*100)))
 app.free()
 quit()
