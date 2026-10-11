extends SceneTree
var erros: Array = []
var casos := 0
func verificar(ok: bool, nome: String) -> void:
 casos += 1
 if not ok: erros.append(nome)
func _initialize(): call_deferred("provar")
func captura(app,nome: String) -> void:
 if DisplayServer.get_name()=="headless": return
 for i in 5: await process_frame
 RenderingServer.force_draw()
 app.sub.get_texture().get_image().save_png(OS.get_environment("KK_PROVA_RETRATO").path_join(nome))
func provar():
 root.size = Vector2i(1920,1080)
 var app = load("res://mascote.gd").new()
 app.roupas.relogio = func(): return {"hour":12,"weekday":1}
 app.cache = "/tmp/kk-atuacao-%d.json" % OS.get_process_id()
 app.runtime = ""
 app.prova = true
 # Testa a fala falada: modo mensagens (resposta escrita) desligado e voz sintética ligada.
 app.modo_mensagens = false
 app.voz_sintetica = true
 root.add_child(app)
 app.set_process(false)
 for t in app.get_children():
  if t is Timer: t.stop()
 app.fala_automatica = false
 app.expressao = "Automática"
 app.acao_menu("Modo perfil")
 app.pos_retrato = Vector2(960,600)
 app.zoom = 1
 app.aplicar_render()
 for b in app.bonecas:
  app.trocar_boneca(b.id)
  app.olhar.active = false
  app.secundario.active = false
  app.player.play("idle_em_pe")
  app.player.seek(0.6,true)
  app.player.pause()
  app.configurar_camera()
  for perfil in ["Riso","Curiosidade","Dúvida","Desânimo","Choro","Sorriso travesso","Piscadela esquerda","Piscadela direita"]:
   app.rosto.ajustes = {}
   app.rosto.dinamica = 1
   app.rosto.aplicar(perfil,0,"a",0,1)
   var face = app.malhas.filter(func(m): return str(m.name)=="cf_O_face")[0]
   var alvo: String = app.rosto.PERFIS[perfil][0]
   var encontrado := false
   for canal in app.rosto.canais:
    if canal.malha==face:
     encontrado = canal.grupos.olhos.has(alvo)
     var soma := 0.0
     for i in canal.grupos.olhos.values(): soma += face.get_blend_shape_value(i)
     verificar(absf(soma-1)<0.001,b.id+": olhos normalizados "+perfil)
   verificar(encontrado,b.id+": forma ocular existe "+perfil)
   await captura(app,b.id+"-"+perfil+".png")
  app.rosto.ajustes = {"olhos":{"bisyou_op":0.65,"def_op":0.15},"sobrancelhas":{"gimoL_op":0.4},"boca":{"neko_cl":0.6},"vogais_amplas":true}
  verificar(app.rosto.validar_ajustes(app.rosto.ajustes),"aceita mistura de formas")
  app.rosto.aplicar("Felicidade",0,"a",0.5,1)
  for canal in app.rosto.canais:
   for grupo in ["olhos","sobrancelhas","boca"]:
    if canal.grupos[grupo].is_empty(): continue
    var soma := 0.0
    for i in canal.grupos[grupo].values(): soma += canal.malha.get_blend_shape_value(i)
    verificar(absf(soma-1)<0.001,"piscar preserva normalização da mistura")
  app.rosto.aplicar("Felicidade",0.8,"a",0,1)
  var face = app.malhas.filter(func(m): return str(m.name)=="cf_O_face")[0]
  for canal in app.rosto.canais:
   if canal.malha==face: verificar(absf(face.get_blend_shape_value(canal.grupos.boca.a_l_op)-0.8)<0.001,"articulação usa forma ampla")
  await captura(app,b.id+"-mistura-fala.png")
  app.rosto.ajustes = {}
  var msg := {"id":"atuacao","autor":"Codex — teste","texto":"Olá! Vamos testar agora.","emocao":"Felicidade","atuacao":[{"indice":0,"emocao":"Curiosidade","movimento":"inclinar","face":{"sobrancelhas":"Neutra"}},{"indice":6,"emocao":"Piscadela esquerda","gesto":"conversa_03"},{"indice":12,"emocao":"Felicidade","movimento":"concordar","olhar":[0.2,0]}]}
  verificar(app.receber_fala(msg),"aceita cenas de atuação")
  app._process(0.01)
  verificar(app.atuacao.proxima==1 and app.emocao_atual=="Curiosidade","aplica cena inicial")
  app.fala_texto.indice = 14
  app._process(0.001)
  verificar(app.atuacao.proxima==3 and app.emocao_atual=="Felicidade","não perde cenas ao saltar índice de palavra")
  verificar(app.player.assigned_animation=="conversa_03","cena troca gesto corporal")
  verificar(app.atuacao.olhar_tempo>0,"cena desvia olhar brevemente")
  var restante: float = app.atuacao.olhar_tempo
  app.escondida = true
  app._process(1)
  verificar(app.atuacao.olhar_tempo==restante,"tela cheia pausa atuação junto da fala")
  app.escondida = false
  app.encerrar_fala()
  verificar(app.atuacao.cenas.is_empty() and app.rosto.ajustes.is_empty(),"interromper limpa atuação")
  app.atuacao.contato_inicio("Cabeça",true)
  app.atuacao.passo(1.4,0,"",false)
  verificar(app.atuacao.reacao_emocao=="Riso","carinho prolongado na cabeça varia expressão")
  app.atuacao.contato_fim()
  app.atuacao.passo(2,0,"",false)
  verificar(app.atuacao.reacao_tempo==0 and not app.atuacao.contato,"soltar deixa reação acabar")
  app.olhar.active = false
  var indice: int = app.sk.find_bone("cf_j_head")
  app.olhar.perto = false
  app.olhar.alvo = Vector2.ZERO
  app.olhar.expressivo = Vector3.ZERO
  for i in 180: app.olhar.atualizar(1.0/60)
  var base: Quaternion = app.sk.get_bone_pose_rotation(indice)
  for i in 240:
   app.olhar.expressivo = Vector3(sin(i*0.1)*0.05,0,0.04)
   app.olhar.atualizar(1.0/60)
  app.olhar.expressivo = Vector3.ZERO
  app.olhar.atualizar(1.0/60)
  verificar(base.angle_to(app.sk.get_bone_pose_rotation(indice))<0.001,"movimento de cabeça retorna sem deriva")
 app.receber_fala({"id":"auto-corpo","autor":"Codex — teste","texto":("Uma conversa mais longa. ").repeat(20),"emocao":"Felicidade"})
 app._process(3.2)
 verificar(app.player.assigned_animation.begins_with("conversa_"),"fala longa alterna para conversa automaticamente")
 app.encerrar_fala()
 app.receber_fala({"id":"gesto-fixo","autor":"Codex — teste","texto":("Uma conversa mais longa. ").repeat(20),"emocao":"Felicidade","gesto":"stand_joy_04"})
 app._process(6)
 verificar(app.player.assigned_animation=="stand_joy_04","gesto explícito preservado durante fala longa")
 app.encerrar_fala()
 for invalido in [{"olhos":{"def_op":0.8,"bisyou_op":0.8}},{"boca":{"a_l_op":1}},{"olhos":{"inventado":1}}]:
  verificar(not app.rosto.validar_ajustes(invalido),"rejeita mistura inválida")
 verificar(not app.atuacao.validar([{"indice":2},{"indice":1}],10),"rejeita cenas fora de ordem")
 verificar(not app.atuacao.validar([{"indice":0,"olhar":[2,0]}],10),"rejeita olhar sem limite")
 app.acao_menu("Atuação natural: ligada")
 verificar(not app.atuacao_natural,"menu permite desativar atuação automática")
 app.prova = false
 app.salvar()
 app.atuacao_natural = true
 app.carregar()
 verificar(not app.atuacao_natural,"preferência persiste")
 DirAccess.remove_absolute(app.cache)
 var resultado := {"passou":erros.is_empty(),"casos":casos,"erros":erros}
 var f := FileAccess.open("res://evidencias/interacao-avancada/validacao.json",FileAccess.WRITE)
 f.store_string(JSON.stringify(resultado,"  "));f.close()
 print(JSON.stringify(resultado))
 app.free()
 quit(0 if erros.is_empty() else 1)
