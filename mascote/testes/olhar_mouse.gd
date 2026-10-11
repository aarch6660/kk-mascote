extends SceneTree
var erros: Array = []
var casos := 0
func verificar(ok: bool, texto: String):
 casos += 1
 if not ok: erros.append(texto)
func _initialize():
 call_deferred("provar")
func captura(app,nome):
 if DisplayServer.get_name() == "headless": return
 for i in 5: await process_frame
 app.atualizar_silhueta()
 app.posicionar()
 for i in 3: await process_frame
 RenderingServer.force_draw()
 var lado = int(app.TAM*app.zoom)
 var regiao = Rect2i(Vector2i(app.pos_retrato-Vector2.ONE*lado*0.5-Vector2(6,6)),Vector2i(lado+12,lado+12))
 root.get_texture().get_image().get_region(regiao).save_png(OS.get_environment("KK_PROVA_RETRATO").path_join(nome))
func provar():
 root.size = Vector2i(1920,1080)
 var app = load("res://mascote.gd").new()
 app.roupas.relogio = func(): return {"hour":12,"weekday":1}
 app.cache = "/tmp/kk-olhar-%d.json" % OS.get_process_id()
 app.runtime = ""
 app.prova = true
 root.add_child(app)
 app.set_process(false)
 for t in app.get_children():
  if t is Timer: t.stop()
 app.acao_menu("Modo perfil")
 app.expressao = "Neutra"
 app.fala_automatica = false
 app.zoom = 1.2
 app.pos_retrato = Vector2(960,650)
 app.preparar_retrato()
 app.aplicar_render()
 for b in app.bonecas:
  app.trocar_boneca(b.id)
  app.olhar.active = false
  app.player.play("idle_em_pe")
  app.player.seek(0.6,true)
  app.player.pause()
  app.configurar_camera()
  app.aplicar_expressao()
  app.posicionar()
  var base = app.sk.get_bone_pose_rotation(app.sk.find_bone("cf_j_head"))
  app.olhar.perto = false
  for i in 180: app.olhar.atualizar(1.0/30)
  verificar(app.olhar.olhos.size() == 2, b.id+": controla duas pupilas")
  verificar(app.sk.get_bone_name(app.olhar.olhos[0]).begins_with("cf_J_hitomi_tx"), b.id+": não move pálpebras com a pupila")
  for direcao in {"direita":Vector2(500,0),"esquerda":Vector2(-500,0),"baixo":Vector2(0,500),"cima":Vector2(0,-500)}:
   var deslocamento = {"direita":Vector2(500,0),"esquerda":Vector2(-500,0),"baixo":Vector2(0,500),"cima":Vector2(0,-500)}[direcao]
   app.olhar.perto = false
   for i in 180: app.olhar.atualizar(1.0/30)
   app.cursor = app.pos_retrato+deslocamento
   app.atualizar_olhar()
   verificar(app.olhar.perto and app.olhar.alvo.dot(deslocamento)>0, b.id+": cursor e alvo no mesmo sentido "+str(direcao))
   for i in 600: app.olhar.atualizar(1.0/30)
   var delta = base.inverse()*app.sk.get_bone_pose_rotation(app.olhar.cabeca)
   var euler = delta.get_euler()
   verificar(delta.get_angle()<0.6, b.id+": cabeça limitada após 600 passos "+str(direcao))
   verificar((euler.y*deslocamento.x > 0) if deslocamento.x != 0 else (euler.x*deslocamento.y > 0), b.id+": cabeça acompanha "+str(direcao))
   verificar(app.olhar.deslocamentos_olhos[app.olhar.olhos[0]].length()>0.0001 and app.olhar.deslocamentos_olhos[app.olhar.olhos[0]].length()<0.0036, b.id+": pupila acompanha com limite "+str(direcao))
   for olho in app.olhar.olhos:
    verificar(app.sk.get_bone_pose_rotation(olho).is_equal_approx(app.olhar.base_olhos[olho]), b.id+": movimento não inclina camada da pupila "+str(direcao))
   if b.id == "chika-haruno": await captura(app,"olhar-"+str(direcao)+".png")
  app.olhar.perto = false
  for i in 600: app.olhar.atualizar(1.0/30)
  verificar((base.inverse()*app.sk.get_bone_pose_rotation(app.olhar.cabeca)).get_angle()<0.01, b.id+": cabeça volta ao centro")
  verificar(app.olhar.deslocamentos_olhos[app.olhar.olhos[0]].length()<0.00001,b.id+": pupila volta ao centro")
  if b.id == "chika-haruno": await captura(app,"olhar-centro.png")
  for modo in ["Modo passeio","Modo retrato","Modo perfil"]:
   app.acao_menu(modo)
   app.fisica.pos = Vector2(960,1000)
   app.posicionar()
   app.cursor = Vector2(0,100)
   app.atualizar_olhar()
   verificar(app.olhar.perto and app.olhar.alvo.x<0,b.id+": acompanha mouse longe em "+str(modo))
  app.estados.mudar("cochilo")
  app.atualizar_olhar()
  verificar(not app.olhar.perto,b.id+": dormindo não acompanha")
  app.estados.mudar("parada")
 var resultado = {"passou":erros.is_empty(),"casos":casos,"erros":erros}
 var f = FileAccess.open("res://evidencias/olhar-mouse-validacao.json",FileAccess.WRITE)
 f.store_string(JSON.stringify(resultado,"  "));f.close()
 print(JSON.stringify(resultado))
 quit(0 if erros.is_empty() else 1)
