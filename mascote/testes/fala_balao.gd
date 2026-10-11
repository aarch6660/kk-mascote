extends SceneTree
var casos := 0
var erros: Array = []
func verificar(ok: bool, texto: String):
 casos += 1
 if not ok: erros.append(texto)
func _initialize(): call_deferred("provar")
func mensagem(app,id: String,texto: String,autor: String,emocao: String):
 var f := FileAccess.open(app.runtime.path_join("falas/"+id+".json"),FileAccess.WRITE)
 f.store_string(JSON.stringify({"id":id,"pid_destino":OS.get_process_id(),"criado_em":Time.get_unix_time_from_system(),"texto":texto,"autor":autor,"emocao":emocao}));f.close()
func captura(app,nome):
 if DisplayServer.get_name()=="headless": return
 for i in 8: await process_frame
 app.posicionar()
 for i in 4: await process_frame
 RenderingServer.force_draw()
 root.get_texture().get_image().save_png(OS.get_environment("KK_PROVA_RETRATO").path_join(nome))
func provar():
 root.size = Vector2i(1920,1080)
 var app = load("res://mascote.gd").new()
 app.roupas.relogio = func(): return {"hour":12,"weekday":1}
 app.prova = true
 # Testa a fala falada: modo mensagens (resposta escrita) desligado e voz sintética ligada.
 app.modo_mensagens = false
 app.voz_sintetica = true
 app.cache = "/tmp/kk-fala-cache-inexistente-%d.json" % OS.get_process_id()
 app.runtime = ""
 root.add_child(app)
 app.set_process(false)
 for timer in app.get_children():
  if timer is Timer: timer.stop()
 app.olhar.active = false
 app.secundario.active = false
 app.runtime = "/tmp/kk-fala-godot-%d" % OS.get_process_id()
 DirAccess.make_dir_recursive_absolute(app.runtime.path_join("falas"))
 app.acao_menu("Modo perfil")
 app.pos_retrato = Vector2(960,700)
 app.zoom = 1.1
 app.preparar_retrato()
 app.aplicar_render()
 app.aplicar_expressao()
 app.fala_automatica = false
 app.expressao = "Confiança"
 app.emocao_atual = "Confiança"
 for b in app.bonecas:
  app.trocar_boneca(b.id)
  app.olhar.active = false
  app.secundario.active = false
  verificar(app.receber_fala({"id":"direta-"+b.id,"texto":"a, e, i, o, u.","autor":"Codex — teste","emocao":"Tristeza"}),b.id+": aceita fala")
  app.player.seek(0.6,true)
  app.player.pause()
  verificar(app.player.assigned_animation.begins_with("stand_sad_"),b.id+": fala triste usa corpo original de tristeza")
  var aberturas := []
  var vogais := {}
  var pausas := 0
  for i in 75:
   app._process(1.0/60)
   aberturas.append(app.fala_texto.abertura)
   if app.fala_texto.abertura>0.5: vogais[app.fala_texto.vogal] = true
   if app.fala_texto.abertura == 0: pausas+=1
   verificar(app.emocao_atual == "Tristeza",b.id+": emoção da mensagem prevalece sem alterar preferência")
  verificar(vogais.size() == 5 and aberturas.max()>0.5 and pausas>0,b.id+": boca acompanha cinco vogais e pausas")
  for i in 400: app._process(1.0/60)
  verificar(not app.fala_texto.ativo and not app.balao.visible,b.id+": balão termina")
  verificar(app.expressao == "Confiança" and app.emocao_atual == "Confiança",b.id+": restaura expressão escolhida")
  verificar(is_zero_approx(app.fala_texto.abertura),b.id+": boca em repouso após texto")
 app.trocar_boneca("chika-haruno")
 app.olhar.active = false
 app.secundario.active = false
 app.expressao = "Automática"
 app.emocao_atual = "Neutra"
 mensagem(app,"001-codex","Sinto muito. Estou triste com essa notícia.","Codex — teste","Tristeza")
 mensagem(app,"002-claude","Que ótimo! Conseguimos terminar juntos.","Claude — teste","Felicidade")
 app.ler_falas()
 verificar(app.fala_texto.id=="001-codex","Fila inicia Codex primeiro")
 app.ler_falas()
 verificar(FileAccess.file_exists(app.runtime.path_join("falas/002-claude.json")),"Mensagem de Claude aguarda sem sobrescrever Codex")
 for i in 80: app._process(1.0/60)
 await captura(app,"fala-codex-triste.png")
 for i in 600: app._process(1.0/60)
 app.ler_falas()
 verificar(app.fala_texto.id=="002-claude","Fila inicia canal Claude depois")
 for i in 100: app._process(1.0/60)
 await captura(app,"fala-claude-feliz.png")
 verificar(app.emocao_atual == "Felicidade","Canal Claude controla emoção facial")
 var recibo = JSON.parse_string(FileAccess.get_file_as_string(app.runtime.path_join("recibos-fala/001-codex.json")))
 verificar(recibo.estado=="concluida","Recibo confirma conclusão")
 app.encerrar_fala()
 verificar(not app.fala_texto.ativo,"Pode interromper fala")
 var recibo2 = JSON.parse_string(FileAccess.get_file_as_string(app.runtime.path_join("recibos-fala/002-claude.json")))
 verificar(recibo2.estado=="interrompida","Recibo confirma interrupção")
 app.receber_fala({"id":"longa","texto":("Uma mensagem longa precisa continuar legível. ").repeat(22),"autor":"Codex — teste","emocao":"Neutra"})
 for i in 1200: app._process(1.0/60)
 verificar(app.fala_texto.paginas.size()>1 and app.fala_texto.pagina_visivel().length()<=211,"Texto longo paginado")
 for pos in [Vector2(280,280),Vector2(1640,280),Vector2(1640,790),Vector2(280,790)]:
  app.pos_retrato = pos
  app.preparar_retrato()
  app.posicionar()
  app._process(0.01)
  verificar(Rect2(Vector2.ZERO,Vector2(root.size)).encloses(app.balao.get_global_rect()),"Balão fica dentro da tela")
  verificar(app.balao.mouse_filter==Control.MOUSE_FILTER_IGNORE,"Balão não captura mouse")
 app.encerrar_fala()
 for pasta in ["falas","recibos-fala"]:
  for nome in DirAccess.get_files_at(app.runtime.path_join(pasta)): DirAccess.remove_absolute(app.runtime.path_join(pasta).path_join(nome))
  DirAccess.remove_absolute(app.runtime.path_join(pasta))
 for nome in DirAccess.get_files_at(app.runtime): DirAccess.remove_absolute(app.runtime.path_join(nome))
 DirAccess.remove_absolute(app.runtime)
 app.runtime = ""
 var resultado = {"casos":casos,"passou":erros.is_empty(),"erros":erros}
 var f = FileAccess.open("res://evidencias/fala-balao-validacao.json",FileAccess.WRITE)
 f.store_string(JSON.stringify(resultado,"  "));f.close()
 print(JSON.stringify(resultado))
 quit(0 if erros.is_empty() else 1)
