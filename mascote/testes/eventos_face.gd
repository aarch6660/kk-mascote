extends SceneTree
var erros: Array = []
var casos := 0
func verificar(ok: bool, texto: String) -> void:
 casos += 1
 if not ok: erros.append(texto)
func _initialize(): call_deferred("provar")
func botao(ponto: Vector2, pressed: bool) -> InputEventMouseButton:
 var e := InputEventMouseButton.new()
 e.button_index = MOUSE_BUTTON_LEFT
 e.position = ponto
 e.pressed = pressed
 return e
func provar():
 root.size = Vector2i(1920,1080)
 var app = load("res://mascote.gd").new()
 app.roupas.relogio = func(): return {"hour":12,"weekday":1}
 app.cache = "/tmp/kk-eventos-cache-%d.json" % OS.get_process_id()
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
 app.acao_menu("Modo passeio")
 app.zoom = 1.8
 app.fisica.pos = Vector2(960,980)
 app.fisica.fixa = true
 app.aplicar_render()
 for b in app.bonecas:
  app.trocar_boneca(b.id)
  app.olhar.active = false
  app.secundario.active = false
  app.player.play("idle_em_pe")
  app.player.seek(0.6,true)
  app.player.pause()
  app.sk.force_update_all_bone_transforms()
  app.chika.rotation.y = 0
  app.configurar_camera()
  app.posicionar()
  for detalhe in [["cf_j_bnip02_L","Mamilo esquerdo"],["cf_j_bnip02_R","Mamilo direito"],["cf_j_kokan","Região genital"],["cf_j_head","Cabeça"]]:
   verificar(app.localizar_toque(app.ponto_osso(detalhe[0])).get("regiao")==detalhe[1],b.id+": região frontal "+detalhe[1])
  app.chika.rotation.y = PI
  for detalhe in [["cf_j_siri_L","Nádega esquerda"],["cf_j_siri_R","Nádega direita"],["cf_j_ana","Região anal"]]:
   verificar(app.localizar_toque(app.ponto_osso(detalhe[0])).get("regiao")==detalhe[1],b.id+": região posterior "+detalhe[1])
  app.chika.rotation.y = 0
  app.local_poly = PackedVector2Array([Vector2.ZERO,Vector2(448,0),Vector2(448,448),Vector2(0,448)])
  app.posicionar()
  app.modo_toque = "Pegar e mover"
  verificar(app.receber_fala({"id":"teste-evento","texto":"Teste.","emocao":"Felicidade","autor":"Codex — teste","face":{"intensidade":0.4,"sobrancelhas":"Neutra"}}),"aceita ajuste facial")
  var ponto: Vector2 = app.ponto_osso("cf_j_head")
  app._input(botao(ponto,true))
  verificar(app.ultimo_evento.tipo=="fala_interrompida" and app.ultimo_evento.regiao=="Cabeça","clique informa região da interrupção em modo arrasto")
  verificar(app.rosto.ajustes.is_empty(),"interromper restaura ajustes anteriores")
  app._input(botao(ponto,false))
  verificar(app.ultimo_evento.tipo=="contato_fim" and app.ultimo_evento.regiao=="Cabeça","soltar registra contato")
  app.modo_toque = "Acariciar"
  app._input(botao(ponto,true))
  verificar(app.ultimo_evento.tipo=="toque_inicio","início de carinho registrado")
  app.atualizar_toque(Vector2(-9000,-9000))
  verificar(app.ultimo_evento.regiao=="Fora do corpo" and app.osso_toque==-1,"saída do corpo registrada sem pressão")
  app._input(botao(ponto,false))
  for intensidade in [0.0,0.4,1.0]:
   app.rosto.ajustes = {"intensidade":intensidade,"olhos":"Felicidade","sobrancelhas":"Neutra","boca":"Timidez"}
   for piscada in [0.0,0.5,1.0]:
    app.rosto.aplicar("Confiança",0,"a",piscada,1)
    for canal in app.rosto.canais:
     for grupo in ["boca","olhos","sobrancelhas"]:
      var soma := 0.0
      for indice in canal.grupos[grupo].values():
       var peso: float = canal.malha.get_blend_shape_value(indice)
       verificar(is_finite(peso) and peso>=0 and peso<=1,"peso facial limitado")
       soma += peso
      if not canal.grupos[grupo].is_empty(): verificar(absf(soma-1)<0.005,"mistura normalizada "+grupo)
     for nome in canal.grupos.boca:
      if str(nome).ends_with("_op"): verificar(is_zero_approx(canal.malha.get_blend_shape_value(canal.grupos.boca[nome])),"boca fechada em repouso")
   app.rosto.aplicar("Felicidade",0.7,"a",0,1)
   for canal in app.rosto.canais:
    if canal.grupos.boca.has("a_s_op"): verificar(absf(canal.malha.get_blend_shape_value(canal.grupos.boca["a_s_op"])-0.7)<0.005,"lip sync preservado")
  app.rosto.ajustes = {}
 app.acao_menu("Modo retrato")
 app.zoom = 1.7
 app.pos_retrato = Vector2(563,553)
 app.aplicar_render()
 app.configurar_camera()
 app.posicionar()
 verificar(app.localizar_toque(app.ponto_osso("cf_J_Eye_tx_L")).get("regiao")=="Cabeça","cabeça no enquadramento de busto")
 verificar(app.localizar_toque(Vector2(929,615)).is_empty(),"clique real na margem do retrato não inventa região corporal")
 verificar(not app.receber_fala({"texto":"Teste","face":{"intensidade":2}}),"rejeita intensidade inválida")
 verificar(not app.rosto.validar_ajustes({"olhos":"inventado"}),"rejeita perfil inválido")
 app.runtime = "/tmp/kk-eventos-godot-%d" % OS.get_process_id()
 for i in 300: app.registrar_evento("teste",{"regiao":"Cabeça"})
 var pasta: String = app.runtime.path_join("eventos")
 var arquivos := DirAccess.get_files_at(pasta)
 verificar(arquivos.size()==256,"histórico limitado a 256 eventos")
 arquivos.sort()
 var dados = JSON.parse_string(FileAccess.get_file_as_string(pasta.path_join(arquivos[-1])))
 verificar(dados.sequencia==app.sequencia_evento and dados.sessao==app.sessao_eventos,"evento atômico e identificado por sessão")
 for arquivo in arquivos: DirAccess.remove_absolute(pasta.path_join(arquivo))
 DirAccess.remove_absolute(pasta)
 DirAccess.remove_absolute(app.runtime)
 var resultado := {"passou":erros.is_empty(),"casos":casos,"erros":erros}
 var f := FileAccess.open("res://evidencias/ponte-eventos/validacao.json",FileAccess.WRITE)
 f.store_string(JSON.stringify(resultado,"  "));f.close()
 print(JSON.stringify(resultado))
 app.free()
 quit(0 if erros.is_empty() else 1)
