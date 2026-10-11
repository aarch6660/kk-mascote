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
 var regiao = Rect2i(Vector2i(app.sprite.position-Vector2.ONE*app.TAM*app.zoom*0.5-Vector2(6,6)),Vector2i(Vector2.ONE*app.TAM*app.zoom+Vector2(12,12)))
 root.get_texture().get_image().get_region(regiao).save_png(OS.get_environment("KK_PROVA_RETRATO").path_join(nome))
func evento(ponto: Vector2,pressionado: bool,shift := false):
 var e := InputEventMouseButton.new()
 e.button_index = MOUSE_BUTTON_LEFT
 e.position = ponto
 e.pressed = pressionado
 e.shift_pressed = shift
 return e
func provar():
 root.size = Vector2i(1920,1080)
 var app = load("res://mascote.gd").new()
 app.roupas.relogio = func(): return {"hour":12,"weekday":1}
 app.cache = "/tmp/kk-corpo-%d.json" % OS.get_process_id()
 app.runtime = ""
 app.prova = true
 root.add_child(app)
 app.set_process(false)
 for t in app.get_children():
  if t is Timer: t.stop()
 app.acao_menu("Modo passeio")
 app.zoom = 1.8
 app.fisica.pos = Vector2(960,980)
 app.fisica.fixa = true
 app.expressao = "Automática"
 app.fala_automatica = false
 app.aplicar_render()
 for b in app.bonecas:
  app.trocar_boneca(b.id)
  app.olhar.active = false
  app.secundario.active = false
  var indice: int = app.sk.find_bone("cf_j_index02_L")
  var lib = app.player.get_animation_library("")
  var numero := -1
  for nome in app.player.get_animation_list():
   var anim = app.player.get_animation(nome)
   if numero < 0: numero = anim.get_track_count()
   verificar(anim.get_track_count() == numero,b.id+": todas as pistas têm destino em "+str(nome))
   var t = anim.find_track(NodePath(str(app.chika.get_path_to(app.sk))+":cf_j_index02_L"),Animation.TYPE_ROTATION_3D)
   verificar(t >= 0,b.id+": dedos presentes em "+str(nome))
  var fonte: Animation = app.animacoes_corpo.fontes.conversa_03
  var rest_fonte: Transform3D = app.animacoes_corpo.repousos.conversa_03.cf_j_index02_L
  var tfonte := -1
  for t in fonte.get_track_count():
   if str(fonte.track_get_path(t)).ends_with(":cf_j_index02_L") and fonte.track_get_type(t) == Animation.TYPE_ROTATION_3D: tfonte = t
  var destino: Animation = lib.get_animation("conversa_03")
  var tdestino = destino.find_track(NodePath(str(app.chika.get_path_to(app.sk))+":cf_j_index02_L"),Animation.TYPE_ROTATION_3D)
  var esperado: Quaternion = app.sk.get_bone_rest(indice).basis.get_rotation_quaternion()*rest_fonte.basis.get_rotation_quaternion().inverse()*fonte.track_get_key_value(tfonte,0)
  verificar(esperado.is_equal_approx(destino.track_get_key_value(tdestino,0)),b.id+": rotação de dedo preserva delta original e repouso da boneca")
  app.player.play("conversa_03")
  app.player.seek(0,true)
  var antes: Quaternion = app.sk.get_bone_pose_rotation(indice)
  app.player.seek(1.5,true)
  verificar(antes.angle_to(app.sk.get_bone_pose_rotation(indice)) > 0.005,b.id+": dedos da conversa animam")
  app.player.play("idle_em_pe")
  app.player.seek(0.6,true)
  app.player.pause()
  app.configurar_camera()
  app.posicionar()
  app.secundario.repouso = true
  app.secundario.relaxar = true
  for i in 120: app.secundario.atualizar(1.0/30)
  var dedo_antes: Quaternion = app.sk.get_bone_pose_rotation(indice)
  for i in 45: app.secundario.atualizar(1.0/30)
  verificar(dedo_antes.angle_to(app.sk.get_bone_pose_rotation(indice))>0.003,b.id+": variação suave dos dedos em repouso")
  app.secundario.maos_suaves = false
  var cabelo_antes := []
  var comprimento_cabelo := 0.0
  for cadeia in app.secundario.nativa.cadeias:
   if cadeia.slot.begins_with("cabelo"):
    for p in cadeia.particulas:
     cabelo_antes.append(Vector3(p.pos))
     comprimento_cabelo = maxf(comprimento_cabelo,Vector3(p.pos).distance_to(cadeia.particulas[0].pos))
  app.secundario.impulso = Vector3(0.12,0,0.06)
  for i in 10: app.secundario.atualizar(1.0/30)
  var maximo := 0.0
  for canal in app.secundario.canais:
   if canal.tipo == "cabelo": maximo = maxf(maximo,Vector3(canal.angulo).length())
  var n := 0
  for cadeia in app.secundario.nativa.cadeias:
   if cadeia.slot.begins_with("cabelo"):
    for p in cadeia.particulas:
     maximo = maxf(maximo,Vector3(p.pos).distance_to(cabelo_antes[n]))
     n += 1
  # Franja curta tem movimento menor que o limite de 1 mm dos cabelos longos.
  var limiar_cabelo := maxf(0.000001,minf(0.001,comprimento_cabelo*0.001))
  verificar(maximo>limiar_cabelo,b.id+": cabelo reage à força")
  for i in 600: app.secundario.atualizar(1.0/30)
  var residual := 0.0
  for canal in app.secundario.canais:
   verificar(Vector3(canal.angulo).is_finite() and Vector3(canal.angulo).length()<0.081,b.id+": física limitada "+str(canal.i))
   residual = maxf(residual,Vector3(canal.angulo).length())
  verificar(residual<0.005,b.id+": molas voltam ao repouso sem acumular")
  app.secundario.ligado = false
  app.secundario.dormindo = true
  for i in 90: app.secundario.atualizar(1.0/30)
  var dormindo := 0.0
  for canal in app.secundario.canais: dormindo = maxf(dormindo,Vector3(canal.angulo).length())
  verificar(dormindo < 0.001,b.id+": desligado ou dormindo volta ao repouso")
  app.secundario.ligado = true
  app.secundario.dormindo = false
  app.secundario.maos_suaves = true
  for i in 180: app.secundario.atualizar(1.0/30)
  await captura(app,b.id+"-corpo.png")
  app.modo_toque = "Acariciar"
  app.local_poly = PackedVector2Array([Vector2.ZERO,Vector2(448,0),Vector2(448,448),Vector2(0,448)])
  app.posicionar()
  var pos = app.fisica.pos
  var ponto = app.ponto_osso("cf_j_head")
  verificar(app.localizar_toque(ponto).get("regiao") == "Cabeça",b.id+": encontra cabeça na pose projetada")
  app._input(evento(ponto,true))
  verificar(app.toque_ativo and app.fisica.arrastando,b.id+": carinho captura sem deslocar")
  var m := InputEventMouseMotion.new()
  m.position = ponto+Vector2(8,2)
  app._input(m)
  app.fisica.passo(1,46)
  verificar(app.fisica.pos == pos and not app.arrastando,b.id+": carinho não arrasta personagem")
  app.passo_facial(1.0/30,0)
  verificar(app.emocao_atual == "Felicidade",b.id+": carinho provoca reação facial")
  app._input(evento(m.position,false))
  verificar(not app.toque_ativo and not app.pressionada and not app.fisica.arrastando,b.id+": soltar termina carinho")
  app.modo_toque = "Apalpar"
  app.player.play("idle_em_pe"); app.player.seek(0.6,true); app.player.pause()
  var mao = app.ponto_osso("cf_j_hand_L")
  app._input(evento(mao,true))
  verificar(app.toque_ativo and app.regiao_toque.begins_with("Mão"),b.id+": toque detecta mão")
  app._process(1.0/30)
  verificar(app.secundario.pressao == 1 and app.secundario.toque_osso>=0,b.id+": toque ativa pressão suave")
  app._input(evento(mao,false))
  app._input(evento(ponto,true,true))
  m.position = ponto+Vector2(50,20)
  app._input(m)
  verificar(app.arrastando and not app.toque_ativo,b.id+": Shift mantém arrasto em modo toque")
  app._input(evento(m.position,false,true))
  app.modo_toque = "Pegar e mover"
  app.zoom = 1.8
  app.fisica.pos = Vector2(960,980)
  app.secundario.maos_suaves = true
  app.feedback_toque = 0
  if b.id == "chika-haruno":
   for clipe in ["alongar","stand_joy_04","caminhar"]:
    app.player.play(clipe);app.player.seek(0.8,true);app.player.pause()
    for i in 8: app.secundario.atualizar(1.0/30)
    await captura(app,"gesto-"+clipe+".png")
  app.player.play("conversa_03");app.player.seek(1.5,true);app.player.pause()
  var centro = (app.sk.get_bone_global_pose(app.sk.find_bone("cf_j_hand_L")).origin+app.sk.get_bone_global_pose(app.sk.find_bone("cf_j_hand_R")).origin)*0.5
  app.camera.size = 0.65
  app.camera.position = Vector3(centro.x,centro.y,4)
  app.retrato = true
  app.pos_retrato = Vector2(960,600)
  await captura(app,b.id+"-maos.png")
  app.retrato = false
  app.configurar_camera()
 app.acao_menu("Modo perfil")
 app.player.play("idle_em_pe");app.player.seek(0.6,true);app.player.pause()
 app.configurar_camera()
 app.posicionar()
 verificar(app.localizar_toque(app.ponto_osso("cf_J_Eye_tx_L")).get("regiao") == "Cabeça","Carinho detecta rosto no perfil")
 app.prova = false
 app.modo_toque = "Acariciar"
 app.fisicas_ligadas = false
 app.maos_suaves = false
 app.salvar()
 app.modo_toque = "Pegar e mover"
 app.fisicas_ligadas = true
 app.maos_suaves = true
 app.carregar()
 verificar(app.modo_toque == "Acariciar" and not app.fisicas_ligadas and not app.maos_suaves,"Interação e física persistem")
 DirAccess.remove_absolute(app.cache)
 var resultado = {"passou":erros.is_empty(),"casos":casos,"erros":erros}
 var f = FileAccess.open("res://evidencias/corpo-interacoes-validacao.json",FileAccess.WRITE)
 f.store_string(JSON.stringify(resultado,"  "));f.close()
 print(JSON.stringify(resultado))
 quit(0 if erros.is_empty() else 1)
