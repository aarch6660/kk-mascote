extends SceneTree
# Prévia do ciclo de mensagem com o celular original: capturas em cada fase.
func _initialize(): call_deferred("provar")
func capturar(app, nome):
 app.renderizando = true
 RenderingServer.set_render_loop_enabled(true)
 app.sub.render_target_update_mode = SubViewport.UPDATE_ALWAYS
 app.sub.size = Vector2i(500,560)
 app.sprite.position = Vector2(250,280)
 app.sprite.scale = Vector2.ONE
 app.camera.size = 0.62
 app.camera.position = Vector3(0,1.08,4)
 app.sk.force_update_all_bone_transforms()
 for i in 6: await process_frame
 RenderingServer.force_draw()
 root.get_texture().get_image().save_png(OS.get_environment("KK_PROVA_RETRATO").path_join(nome))
func provar():
 root.size = Vector2i(500,560)
 var app = load("res://mascote.gd").new()
 app.roupas.relogio = func(): return {"hour":12,"weekday":1}
 app.prova = true
 app.cache = "/tmp/kk-previa-ciclo-%d.json" % OS.get_process_id()
 app.runtime = ""
 root.add_child(app)
 app.set_process(false)
 for t in app.get_children():
  if t is Timer: t.stop()
 app.modo_mensagens = true
 app.sons_ligados = false
 app.fala_automatica = false
 var r := {"id":"p","autor":"Claude","texto":"Hmm... deixa eu ver. Acho que dá sim, mas vou precisar testar com calma antes de te dizer que funciona, tá bom? Te mando assim que terminar!","emocao":"Felicidade","preparacao":{"tom":"surpreso","leitura":1.2}}
 app.receber_fala(r)
 var marcos := {"lendo":false,"reagindo":false,"pensando_msg":false,"digitando":false,"pensando":false,"enviando":false}
 for i in 900:
  app._process(1.0/30)
  app.sub.size = Vector2i(500,560)
  app.sprite.position = Vector2(250,280)
  app.sprite.scale = Vector2.ONE
  app.camera.size = 0.62
  app.camera.position = Vector3(0,1.08,4)
  var fase: String = ("pensando_msg" if app.mensagens.fase=="pensando" else app.mensagens.fase) if app.mensagens.ativo else (app.escrita.estado if app.escrevendo else "")
  if marcos.has(fase) and not marcos[fase]:
   # espera o blend da pose assentar antes de capturar
   for k in 12:
    app._process(1.0/30)
   marcos[fase] = true
   await capturar(app, "ciclo_%s.png" % fase)
   if fase == "digitando":
    # Vista por cima do ombro direito: a tela deve aparecer para ela (e para nós daqui).
    var giro: float = app.chika.rotation.y
    app.chika.rotation.y = PI*0.78
    await capturar(app, "ciclo_ombro.png")
    app.chika.rotation.y = giro
   print("FASE ", fase, " clipe=", app.player.current_animation, " celular=", app.celular.visible, " olhar=", app.olhar.alvo)
  if not app.fala_texto.ativo and not app.mensagens.ativo and i > 30: break
 quit()
