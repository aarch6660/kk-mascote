extends SceneTree
var erros: Array = []
var casos := 0
func verificar(ok: bool, texto: String):
 casos += 1
 if not ok: erros.append(texto)
func _initialize():
 call_deferred("provar")
func captura(app, nome):
 if DisplayServer.get_name() == "headless": return
 for i in 8: await process_frame
 app.configurar_camera()
 app.atualizar_silhueta()
 app.posicionar()
 for i in 4: await process_frame
 RenderingServer.force_draw()
 var lado = int(app.TAM*app.zoom)
 var regiao = Rect2i(Vector2i(app.pos_retrato-Vector2.ONE*lado*0.5-Vector2(6,6)),Vector2i(lado+12,lado+12))
 root.get_texture().get_image().get_region(regiao).save_png(OS.get_environment("KK_PROVA_RETRATO").path_join(nome))
func provar():
 root.size = Vector2i(1920,1080)
 var app = load("res://mascote.gd").new()
 app.roupas.relogio = func(): return {"hour":12,"weekday":1}
 app.cache = "/tmp/kk-piscar-%d.json" % OS.get_process_id()
 app.runtime = ""
 app.prova = true
 root.add_child(app)
 app.set_process(false)
 for t in app.get_children():
  if t is Timer: t.stop()
 app.acao_menu("Modo perfil")
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
  var face = app.malhas.filter(func(m): return str(m.name) == "cf_O_face")[0]
  var olhos = {}
  for canal in app.rosto.canais:
   if canal.malha == face: olhos = canal.grupos.olhos
  verificar(olhos.has("def_op") and olhos.has("def_cl"),b.id+": pálpebras originais do Koikatsu")
  for emocao in app.rosto.PERFIS:
   var meta: Dictionary = app.rosto.CATALOGO.get("caricatos", {}).get(emocao, {})
   var fechamento_expressivo: float = clampf(float(meta.get("fechamento", 0.0)), 0.0, 1.0)
   app.rosto.aplicar(emocao,0,"a",0,1)
   for fps in [30,60]:
    var pico := 0.0
    for frame in range(int(ceil(0.23*fps))+2):
     var fechamento: float = app.fechamento_piscada(float(frame)/fps)
     var fechamento_total: float = 1.0-(1.0-fechamento)*(1.0-fechamento_expressivo)
     pico = maxf(pico,fechamento)
     app.rosto.aplicar(emocao,0,"a",fechamento,1.0/fps)
     var fechadas := 0.0
     for nome in olhos:
      if str(nome).ends_with("_cl"): fechadas += face.get_blend_shape_value(olhos[nome])
     verificar(absf(fechadas-fechamento_total)<0.001,b.id+": pálpebra combina piscada e fechamento expressivo sem atraso em "+str(emocao)+" a "+str(fps)+" FPS")
     for canal in app.rosto.canais:
      if str(canal.malha.name).begins_with("cf_Ohitomi") and canal.piscar >= 0:
       verificar(is_zero_approx(canal.malha.get_blend_shape_value(canal.piscar)),b.id+": íris não recua durante piscar")
       verificar(canal.malha.visible == (fechamento_total < 0.999),b.id+": olho oculto somente no fechamento total")
    verificar(is_equal_approx(pico,1),b.id+": fecha completamente a "+str(fps)+" FPS em "+str(emocao))
    var fechadas_depois := 0.0
    for nome in olhos:
     if str(nome).ends_with("_cl"): fechadas_depois += face.get_blend_shape_value(olhos[nome])
    verificar(absf(fechadas_depois-fechamento_expressivo)<0.001,b.id+": volta ao fechamento expressivo após piscar")
  app.olhar.perto = true
  app.olhar.alvo = Vector2(0.65,-0.34)
  for i in 180: app.olhar.atualizar(1.0/30)
  for fechamento in [0.0,0.25,0.5,0.75,1.0]:
   app.rosto.aplicar("Neutra",0,"a",fechamento,1)
   await captura(app,b.id+"-piscar-%.2f.png" % fechamento)
  if b.id == "chika-haruno":
   app.olhar.perto = false
   for i in 180: app.olhar.atualizar(1.0/30)
   for fechamento in [0.0,0.25,0.5,0.75,1.0]:
    app.rosto.aplicar("Neutra",0,"a",fechamento,1)
    await captura(app,"piscar-%.2f.png" % fechamento)
 var resultado = {"passou":erros.is_empty(),"casos":casos,"erros":erros}
 var f = FileAccess.open("res://evidencias/piscar-validacao.json",FileAccess.WRITE)
 f.store_string(JSON.stringify(resultado,"  "));f.close()
 print(JSON.stringify(resultado))
 quit(0 if erros.is_empty() else 1)
