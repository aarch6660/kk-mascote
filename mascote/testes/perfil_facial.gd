extends SceneTree
var erros: Array = []
var casos := 0
func verificar(ok: bool, mensagem: String):
 casos += 1
 if not ok: erros.append(mensagem)
func _initialize():
 call_deferred("provar")
func captura(app, nome):
 if DisplayServer.get_name() == "headless": return
 app.player.pause()
 for i in 8: await process_frame
 app.atualizar_silhueta()
 app.posicionar()
 for i in 4: await process_frame
 RenderingServer.force_draw()
 var regiao = Rect2i(Vector2i(app.pos_retrato-Vector2.ONE*app.TAM*app.zoom*0.5-Vector2(6,6)),Vector2i(Vector2.ONE*app.TAM*app.zoom+Vector2(12,12)))
 root.get_texture().get_image().get_region(regiao).save_png(OS.get_environment("KK_PROVA_RETRATO").path_join(nome))
func provar():
 root.size = Vector2i(1920,1080)
 var app = load("res://mascote.gd").new()
 app.roupas.relogio = func(): return {"hour":12,"weekday":1}
 app.cache = "/tmp/kk-perfil-%d.json" % OS.get_process_id()
 app.runtime = ""
 app.prova = true
 root.add_child(app)
 app.set_process(false)
 for t in app.get_children():
  if t is Timer: t.stop()
 app.acao_menu("Modo perfil")
 verificar(app.perfil and app.retrato and app.moldura and app.camera.size < 0.48, "Perfil enquadra rosto e ativa moldura")
 app.zoom = 1.2
 app.pos_retrato = Vector2(1000,650)
 app.preparar_retrato()
 app.aplicar_render()
 for b in app.bonecas:
  app.trocar_boneca(b.id)
  var lingua = app.malhas.filter(func(m): return str(m.name) == "o_tang")
  verificar(lingua.size() == 1, b.id+": língua restaurada")
  var face = app.malhas.filter(func(m): return str(m.name) == "cf_O_face")[0]
  var boca = {}
  for canal in app.rosto.canais:
   if canal.malha == face: boca = canal.grupos.boca
  verificar(boca.has("def_cl") and boca.has("a_s_op") and boca.has("i_s_op") and boca.has("u_s_op") and boca.has("e_s_op") and boca.has("o_s_op"), b.id+": boca original com cinco vogais")
  for emocao in app.rosto.PERFIS:
   app.expressao = emocao
   app.emocao_atual = emocao
   app.aplicar_expressao()
   verificar(app.emocao_atual == emocao, b.id+": expressão "+str(emocao))
   var aberta = 0.0
   var fechada = 0.0
   for forma in boca:
    if str(forma).ends_with("_op"): aberta += face.get_blend_shape_value(boca[forma])
    elif str(forma).ends_with("_cl"): fechada += face.get_blend_shape_value(boca[forma])
   verificar(aberta < 0.001 and is_equal_approx(fechada,1), b.id+": boca fechada em repouso em "+str(emocao))
   if b.id == "chika-haruno":
    app.player.play("idle_em_pe")
    app.player.seek(0.6,true)
    app.configurar_camera()
    await captura(app,"perfil-"+str(emocao)+".png")
  app.expressao = "Neutra"
  app.fala_automatica = false
  app.iniciar_fala(6)
  verificar(app.player.current_animation.begins_with("conversa_") and app.fala_restante > 0, b.id+": fala usa clipe original")
  var aberturas = []
  for i in 90:
   app.passo_facial(1.0/30,0)
   aberturas.append(face.get_blend_shape_value(boca.a_s_op))
  var minimo = aberturas.min()
  var maximo = aberturas.max()
  verificar(maximo-minimo > 0.05, b.id+": boca articulada varia no tempo")
  app.fala_restante = 0
  app.passo_facial(1,0)
  verificar(is_equal_approx(face.get_blend_shape_value(boca.def_cl),1), b.id+": boca volta ao repouso")
  app.rosto.aplicar("Raiva",0,"a",1,1)
  verificar(is_equal_approx(face.get_blend_shape_value(boca.def_cl),0) or is_equal_approx(face.get_blend_shape_value(boca.ikari_cl),1), b.id+": grupos faciais não acumulam pesos")
 app.trocar_boneca("chika-haruno")
 app.expressao = "Neutra"
 app.iniciar_fala(6)
 for i in 3:
  app.tempo_fala = 0.11+float(i)*0.24
  app.passo_facial(0.04,0)
  await captura(app,"fala-%d.png" % i)
 app.expressao = "Automática"
 app.fala_automatica = true
 app.indice_emocao = 5
 app.estados.mudar("parada",0)
 app.passo_retrato(0.1,false)
 verificar(app.fala_restante > 0 and app.player.current_animation.begins_with("conversa_"), "Fala automática inicia conversa no perfil")
 verificar(app.emocao_atual == "Raiva", "Ciclo automático preserva a expressão ao começar fala")
 app.prova = false
 app.expressao = "Medo"
 app.fala_automatica = false
 app.salvar()
 var salvo = app.preferencias().duplicate(true)
 app.perfil = false
 app.retrato = false
 app.expressao = "Neutra"
 app.carregar()
 verificar(app.perfil and app.preferencias() == salvo, "Perfil e expressão persistem")
 app.prova = true
 app.acao_menu("Modo passeio")
 verificar(not app.perfil and not app.retrato, "Voltar ao passeio")
 app.acao_menu("Modo retrato")
 verificar(app.retrato and not app.perfil and is_equal_approx(app.camera.size,0.48), "Retrato de busto continua disponível")
 DirAccess.remove_absolute(app.cache)
 var resultado = {"passou":erros.is_empty(),"casos":casos,"erros":erros}
 var f = FileAccess.open("res://evidencias/perfil-facial-validacao.json",FileAccess.WRITE)
 f.store_string(JSON.stringify(resultado,"  "));f.close()
 print(JSON.stringify(resultado))
 quit(0 if erros.is_empty() else 1)
