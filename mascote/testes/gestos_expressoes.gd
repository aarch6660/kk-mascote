extends SceneTree
var casos := 0
var erros: Array = []
func verificar(ok: bool, descricao: String) -> void:
 casos += 1
 if not ok: erros.append(descricao)
func _initialize(): call_deferred("provar")
func captura(app,nome: String) -> void:
 if DisplayServer.get_name()=="headless": return
 app.player.pause()
 for i in 4: await process_frame
 RenderingServer.force_draw()
 app.sub.get_texture().get_image().save_png(OS.get_environment("KK_PROVA_RETRATO").path_join(nome))
func provar():
 root.size = Vector2i(1920,1080)
 var app = load("res://mascote.gd").new()
 app.roupas.relogio = func(): return {"hour":12,"weekday":1}
 app.cache = "/tmp/kk-gestos-%d.json" % OS.get_process_id()
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
 for b in app.bonecas:
  app.trocar_boneca(b.id)
  app.olhar.active = false
  app.secundario.active = false
  app.acao_menu("Modo passeio")
  app.zoom = 1
  app.fisica.pos = Vector2(960,900)
  app.fisica.fixa = true
  app.aplicar_render()
  for nome in app.catalogo_gestos.novos:
   verificar(app.player.has_animation(nome),b.id+": clipe disponível "+nome)
   var anim: Animation = app.player.get_animation(nome)
   for fracao in [0.0,0.5,0.95]:
    app.player.play(nome)
    app.player.seek(anim.length*fracao,true)
    app.player.advance(0)
    app.sk.force_update_all_bone_transforms()
    for osso in ["cf_j_hand_L","cf_j_hand_R","cf_j_index02_L","cf_j_head","cf_j_foot_L"]:
     var pose: Transform3D = app.sk.get_bone_global_pose(app.sk.find_bone(osso))
     verificar(pose.origin.is_finite() and pose.basis.is_finite(),b.id+": pose finita "+nome+" "+osso)
   app.player.seek(anim.length*0.5,true)
   app.rosto.aplicar(app.emocao_gesto(nome),0,"a",0,1)
   await captura(app,b.id+"-"+nome+".png")
  for emocao in ["Felicidade","Raiva","Tristeza","Timidez","Surpresa"]:
   app.indices_gestos.clear()
   var vistos := {}
   var opcoes: Array = app.catalogo_gestos.emocoes[emocao]
   for i in opcoes.size():
    var nome: String = app.escolher_gesto(emocao)
    verificar(nome in opcoes and app.player.has_animation(nome),b.id+": gesto original corresponde à emoção "+emocao)
    vistos[nome] = true
   verificar(vistos.size()==opcoes.size(),b.id+": alterna todas as variações de "+emocao)
  app.acao_menu("Modo perfil")
  app.zoom = 1
  app.pos_retrato = Vector2(960,600)
  app.aplicar_render()
  var face = app.malhas.filter(func(m): return str(m.name)=="cf_O_face")[0]
  for emocao in ["Timidez","Pensativa","Seriedade","Tédio"]:
   var perfil: Array = app.rosto.PERFIS[emocao]
   for canal in app.rosto.canais:
    if canal.malha == face:
     verificar(canal.grupos.olhos.has(perfil[0]) and canal.grupos.boca.has(perfil[2]),b.id+": formas faciais nativas "+emocao)
    if str(canal.malha.name).contains("mayuge"):
     verificar(canal.grupos.sobrancelhas.has(perfil[1]),b.id+": sobrancelhas nativas "+emocao)
   app.player.play("idle_em_pe")
   app.player.seek(0.6,true)
   app.preparar_retrato()
   app.rosto.aplicar(emocao,0,"a",0,1)
   await captura(app,b.id+"-face-"+emocao+".png")
   verificar(app.receber_fala({"id":"teste","texto":"Olá, tudo bem?","autor":"Codex — teste","emocao":emocao}),b.id+": ponte aceita "+emocao)
   app.passo_facial(0.02,0)
   verificar(app.emocao_atual==emocao,b.id+": emoção acompanha mensagem")
   app.encerrar_fala()
  app.receber_fala({"id":"gesto","texto":"Uma resposta alegre.","autor":"Codex — teste","emocao":"Felicidade","gesto":"stand_joy_02"})
  verificar(app.player.assigned_animation=="stand_joy_02",b.id+": gesto escolhido pela ponte")
  app.encerrar_fala()
  verificar(not app.receber_fala({"texto":"Teste","gesto":"dormir_00"}),b.id+": rejeita gesto fora da lista de conversas")
 app.acao_menu("Gestos")
 verificar(app.menu_itens.size()==8+app.catalogo_gestos.get("categorias",{}).size(),"Menu de categorias de gestos inclui novas atividades")
 app.acao_menu("Gestos: Timidez")
 verificar(app.menu_itens.size()==6,"Menu com cinco gestos de timidez")
 app.acao_menu("Gesto: Timidez 02")
 verificar(app.player.assigned_animation=="stand_oth_02","Menu executa gesto escolhido")
 app.acao_menu("Gestos: Neutra")
 app.acao_menu("Gestos: Neutra")
 verificar(app.menu_itens.size()==15,"Menu não acumula clipes")
 var resultado := {"casos":casos,"passou":erros.is_empty(),"erros":erros,"novos_clipes":app.catalogo_gestos.novos.size(),"expressoes":app.rosto.PERFIS.size()}
 var f := FileAccess.open("res://evidencias/gestos-expressoes-validacao.json",FileAccess.WRITE)
 f.store_string(JSON.stringify(resultado,"  "))
 f.close()
 print(JSON.stringify(resultado))
 app.free()
 quit(0 if erros.is_empty() else 1)
