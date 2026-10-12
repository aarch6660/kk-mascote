extends SceneTree
var erros: Array = []
var casos := 0
var fases: Array = []
func verificar(ok: bool, nome: String) -> void:
 casos += 1
 if not ok: erros.append(nome)
func _initialize(): call_deferred("provar")
func captura(app,nome: String) -> void:
 if DisplayServer.get_name()=="headless": return
 for i in 8: await process_frame
 RenderingServer.force_draw()
 root.get_texture().get_image().save_png(OS.get_environment("KK_PROVA_RETRATO").path_join(nome))
func provar():
 root.size = Vector2i(1920,1080)
 var app = load("res://mascote.gd").new()
 app.roupas.relogio = func(): return {"hour":12,"weekday":1}
 app.cache = "/tmp/kk-mensagens-%d.json" % OS.get_process_id()
 app.runtime = ""
 app.prova = true
 root.add_child(app)
 app.set_process(false)
 for t in app.get_children():
  if t is Timer: t.stop()
 app.fala_automatica = false
 app.acao_menu("Modo retrato")
 app.pos_retrato = Vector2(1100,600)
 app.zoom = 1.6
 app.aplicar_render()
 app.sons_ligados = false
 for b in app.bonecas:
  app.trocar_boneca(b.id)
  app.olhar.active = false
  app.secundario.active = false
  for clipe in ["celular_em_pe","celular_sentada","celular_jogando","celular_sentada_2"]:
   verificar(app.player.has_animation(clipe),b.id+": clipe existe "+clipe)
   for pista in app.player.get_animation(clipe).get_track_count():
    var nome := str(app.player.get_animation(clipe).track_get_path(pista)).get_slice(":",1)
    verificar(app.sk.find_bone(nome)>=0,b.id+": pista de celular encontra osso")
  if DisplayServer.get_name()!="headless":
   for clipe in ["celular_em_pe","celular_sentada","celular_sentada_2","celular_jogando"]:
    app.player.play(clipe)
    app.player.seek(2,true)
    app.player.pause()
    app.camera.size = 2.1
    app.camera.position = Vector3(0,0.9,4)
    app.sk.force_update_all_bone_transforms()
    app.celular.show()
    app.celular.alinhar(app.sk,false,0)
    await captura(app,b.id+"-"+clipe+".png")
  app.configurar_camera()
  app.mensagens.iniciar({"tom":"confuso","duracao":8},"Codex — teste","leitura","Felicidade")
  verificar(app.mensagens.fase=="lendo" and app.celular.visible,"leitura mostra celular")
  app.mensagens.passo(2)
  verificar(app.mensagens.fase=="reagindo" and app.efeitos.tipo=="espirais","confusão tem espirais breves")
  app.player.play("idle_em_pe")
  app.player.seek(0.6,true)
  app.player.pause()
  app.rosto.ajustes = {}
  app.rosto.aplicar("Dúvida",0,"a",0,1)
  app.efeitos.tempo = 0.25
  app.atualizar_efeitos(0)
  await captura(app,b.id+"-espirais.png")
  var restante: float = app.mensagens.restante
  app.escondida = true
  app._process(3)
  verificar(app.mensagens.restante==restante,"tela cheia pausa leitura")
  verificar(not app.efeitos.visible and not app.indicador_mensagem.visible,"tela cheia oculta efeitos e legenda")
  app.escondida = false
  app.encerrar_fala("interrompida","clique")
  verificar(not app.mensagens.ativo and not app.celular.visible and app.rosto.ajustes.is_empty(),"clique cancela leitura sem fala fantasma")
  var msg := {"id":"resposta","autor":"Codex — teste","texto":"Agora vamos testar!","emocao":"Felicidade","preparacao":{"tom":"surpreso","leitura":0.8,"digitacao":2.2},"atuacao":[{"indice":0,"efeito":"ideia"}]}
  verificar(app.receber_fala(msg),"aceita ciclo completo")
  verificar(not app.fala_texto.ativo and app.mensagens.fase=="lendo","áudio e texto não começam antes da leitura")
  app._process(0.9)
  verificar(app.mensagens.fase=="reagindo" and app.emocao_atual=="Surpresa","reage ao tom recebido")
  app._process(1.2)
  verificar(app.mensagens.fase=="digitando","começa a digitar logo depois de reagir (sem pose de pensar)")
  if DisplayServer.get_name()!="headless":
   app.player.seek(2,true)
   app.player.pause()
   for i in 20:
    await process_frame
    app.sk.force_update_all_bone_transforms()
    app._process(0.02)
   await captura(app,b.id+"-digitando.png")
  app.passo_mensagens(3)
  app._process(0.001)
  verificar(app.fala_texto.ativo and app.escrevendo and not app.mensagens.ativo and app.celular.visible,"resposta é escrita no celular depois de pensar")
  verificar(app.voz.dados.is_empty() and not app.balao.visible,"escrita não usa voz sintética nem balão")
  verificar(app.player.current_animation=="celular_digitar","escreve tocando a tela (gesto original)")
  verificar(app.efeitos.tipo=="ideia","efeito por trecho funciona na escrita")
  var visto := 0
  for i in 400:
   app._process(0.05)
   verificar(app.escrita.indice<=app.escrita.texto.length() and app.escrita.visivel()==app.escrita.texto.left(app.escrita.indice),"texto visível é prefixo da resposta")
   visto = maxi(visto,app.escrita.indice)
   if not app.fala_texto.ativo: break
  verificar(not app.fala_texto.ativo and not app.escrevendo and not app.celular.visible and visto==msg.texto.length(),"escreve a resposta inteira, envia e guarda o celular")
  app.encerrar_fala()
  verificar(app.efeitos.tipo=="nenhum" and not app.sons_reacao.playing,"interrupção limpa som e efeito")
  verificar(not app.receber_fala({"texto":"teste","preparacao":{"tom":"inventado"}}),"preparação desconhecida rejeitada")
  app.modo_mensagens = false
  verificar(app.receber_fala(msg) and app.fala_texto.ativo,"modo desligado mantém fala imediata")
  app.encerrar_fala()
  app.modo_mensagens = true
  app.mensagens.iniciar({"tom":"surpreso","duracao":8},"Codex — teste","rapida","Neutra")
  verificar(app.receber_fala(msg) and app.mensagens.fase=="lendo","resposta rápida preserva leitura em andamento")
  app.mensagens.passo(2)
  verificar(app.mensagens.fase=="reagindo","resposta rápida não salta reação ao pedido")
  app.encerrar_fala("interrompida","clique")
 verificar(app.mensagens.validar({"leitura":0,"digitacao":0,"intensidade":0}),"aceita limites mínimos")
 for invalido in [{"duracao":0},{"leitura":-1},{"digitacao":10},{"intensidade":true},{"tom":[]},{"tom":"furiosa"},{"comando":"shell"}]:
  verificar(not app.mensagens.validar(invalido),"preparação inválida rejeitada")
 verificar(not app.atuacao.validar([{"indice":0,"efeito":"qualquer"}],10),"efeito desconhecido rejeitado")
 verificar(not app.atuacao.validar([{"indice":0,"som":"qualquer"}],10),"som desconhecido rejeitado")
 app.mensagens.iniciar({"duracao":3},"Codex","fim","Neutra")
 app._process(10)
 verificar(not app.mensagens.ativo and not app.celular.visible,"leitura expira e restaura repouso")
 app.montar_menu_mensagens()
 verificar(app.menu.size.y<1080,"menu cabe no monitor")
 verificar(app.indicador_mensagem.mouse_filter==Control.MOUSE_FILTER_IGNORE,"legenda não captura cliques")
 var prefs: Dictionary = app.preferencias()
 verificar(prefs.versao==12 and prefs.has("modo_mensagens") and prefs.has("sons_reacao") and prefs.has("hana_auto"),"preferências preservam modo e Hana")
 # Fronteira do protocolo: fila não executa pacotes de outra sessão/expirados.
 var runtime := "/tmp/kk-mensagens-runtime-%d" % OS.get_process_id()
 for pasta in ["atividades","audio"]: DirAccess.make_dir_recursive_absolute(runtime.path_join(pasta))
 app.runtime = runtime
 for i in 3:
  var d := {"pid_destino":OS.get_process_id(),"autor":"Codex — teste","tipo":"leitura","criado_em":Time.get_unix_time_from_system(),"preparacao":{"tom":"curioso"}}
  if i==0: d.pid_destino = OS.get_process_id()+1
  if i==1: d.criado_em -= 120
  if i==2: d.preparacao = {"comando":"ignorar"}
  var f := FileAccess.open(runtime.path_join("atividades/%d.json" % i),FileAccess.WRITE)
  f.store_string(JSON.stringify(d));f.close()
 app.ler_atividades()
 verificar(not app.mensagens.ativo,"fila rejeita sessão errada, expiração e comandos desconhecidos")
 var leitura := {"pid_destino":OS.get_process_id(),"autor":"Codex — teste","tipo":"leitura","criado_em":Time.get_unix_time_from_system(),"preparacao":{"tom":"ousado"}}
 var f := FileAccess.open(runtime.path_join("atividades/valida.json"),FileAccess.WRITE)
 f.store_string(JSON.stringify(leitura));f.close()
 app.ler_atividades()
 verificar(app.mensagens.ativo and app.mensagens.tom=="ousado","leitura válida inicia atuação")
 app.mensagens.passo(2)
 verificar(app.mensagens.emocao()=="Surpresa","pedido ousado pode começar com surpresa")
 app.mensagens.passo(1)
 var pendente := {"id":"pendente","autor":"Codex — teste","texto":"Resposta que será interrompida.","emocao":"Confiança","audio":{"arquivo":"pendente.wav"},"preparacao":{"digitacao":3}}
 f = FileAccess.open(runtime.path_join("audio/pendente.wav"),FileAccess.WRITE)
 f.store_string("audio de teste");f.close()
 verificar(app.receber_fala(pendente) and app.mensagens.fase=="digitando","resposta após leitura pula preparação duplicada")
 app.encerrar_fala("interrompida","clique")
 verificar(not FileAccess.file_exists(runtime.path_join("audio/pendente.wav")),"interromper preparação remove áudio pendente")
 var recibo = JSON.parse_string(FileAccess.get_file_as_string(runtime.path_join("recibos-fala/pendente.json")))
 verificar(recibo.estado=="interrompida" and recibo.autor=="Codex — teste","recibo de preparação informa autor e interrupção")
 for pasta in ["atividades","audio","recibos-fala","eventos","chat"]:
  var caminho := runtime.path_join(pasta)
  if DirAccess.dir_exists_absolute(caminho):
   for arquivo in DirAccess.get_files_at(caminho): DirAccess.remove_absolute(caminho.path_join(arquivo))
   DirAccess.remove_absolute(caminho)
 DirAccess.remove_absolute(runtime)
 app.runtime = ""
 app.sons_reacao.ligado = true
 app.sons_reacao.relogio = 100
 verificar(app.sons_reacao.reagir("surpresa"),"interjeição disponível toca")
 verificar(not app.sons_reacao.reagir("duvida"),"sons não se sobrepõem")
 # Aguarda o mixer registrar o playback antes de testar sua interrupção.
 await create_timer(0.08).timeout
 app.sons_reacao.encerrar()
 verificar(not app.sons_reacao.reagir("surpresa"),"intervalo evita som repetido")
 app.sons_reacao.ligado = false
 app.sons_reacao.passo(0.1,true,false)
 verificar(not app.sons_reacao.playing and not app.sons_reacao.teclas.playing,"mute também silencia digitação")
 var resultado := {"casos":casos,"erros":erros}
 var destino := OS.get_environment("KK_PROVA_RETRATO")
 if destino.is_empty(): destino = "res://evidencias/modo-mensagens"
 var arquivo_resultado := FileAccess.open(destino.path_join("validacao.json"),FileAccess.WRITE)
 arquivo_resultado.store_string(JSON.stringify(resultado," "))
 arquivo_resultado.close()
 print(JSON.stringify(resultado))
 app.queue_free()
 await process_frame
 # O mixer libera playbacks parados em seu próximo ciclo, após o nó ser removido.
 await create_timer(0.2).timeout
 quit(0 if erros.is_empty() else 1)
