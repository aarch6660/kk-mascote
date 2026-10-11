extends SceneTree
var resultados := {}
func _initialize():
 call_deferred("provar")
func estabilizar(app):
 app.player.play("idle_em_pe")
 app.player.seek(0.6, true)
 app.player.pause()
 app.configurar_camera()
 for f in 8: await process_frame
 app.atualizar_silhueta()
 app.posicionar()
 for f in 4: await process_frame
 RenderingServer.force_draw()
func provar():
 root.size = Vector2i(1920,1080)
 var destino = OS.get_environment("KK_PROVA_RETRATO")
 var app = load("res://mascote.gd").new()
 app.roupas.relogio = func(): return {"hour":12,"weekday":1}
 app.cache = destino.path_join("cache.json")
 app.runtime = ""
 app.prova = true
 root.add_child(app)
 app.set_process(false)
 for t in app.get_children():
  if t is Timer: t.stop()
 app.olhar.active = false
 app.acao_menu("Modo retrato")
 app.preparar_retrato()
 app.aplicar_render()
 await estabilizar(app)
 assert(app.retrato and app.moldura)
 root.get_texture().get_image().save_png(destino.path_join("retrato-moldura.png"))
 app.acao_menu("Moldura: ligada")
 await estabilizar(app)
 root.get_texture().get_image().save_png(destino.path_join("retrato-sem-moldura.png"))
 app.trocar_boneca("sawai-hinata")
 await estabilizar(app)
 root.get_texture().get_image().save_png(destino.path_join("retrato-hinata.png"))
 # Física inerte e sono/acordar por proximidade.
 var pos = app.fisica.pos
 app.ocioso = 181
 app.passo_retrato(1,false)
 assert(app.estados.estado == "cochilo" and app.fisica.pos == pos)
 app.passo_retrato(1,true)
 assert(app.estados.estado == "parada")
 app.prova = false
 app.salvar()
 var preferencia = app.preferencias()
 app.retrato = false
 app.carregar()
 assert(app.retrato and app.preferencias() == preferencia)
 app.prova = true
 # Entrada ampla, arrasto sem queda, clique e rodinha.
 var clique = InputEventMouseButton.new()
 clique.button_index = MOUSE_BUTTON_LEFT
 clique.position = app.pos_retrato
 clique.pressed = true
 app._input(clique)
 var movimento = InputEventMouseMotion.new()
 movimento.position = clique.position - Vector2(100,80)
 app._input(movimento)
 assert(app.arrastando)
 clique.pressed = false
 clique.position = movimento.position
 app._input(clique)
 assert(not app.arrastando and app.estados.estado == "parada")
 clique.pressed = true
 app._input(clique)
 clique.pressed = false
 app._input(clique)
 assert(app.estados.estado == "reacao")
 assert(app.player.current_animation == "stand_joy_00")
 var tecla = InputEventKey.new()
 tecla.keycode = KEY_B
 tecla.pressed = true
 var boneca_antes = app.boneca
 app._input(tecla)
 assert(app.boneca != boneca_antes and app.retrato)
 app.zoom = 0.75
 app.aplicar_render()
 var tamanho_antes = app.sub.size
 clique.button_index = MOUSE_BUTTON_WHEEL_UP
 clique.pressed = true
 clique.position = app.pos_retrato
 for i in 5: app._input(clique)
 assert(app.sub.size == tamanho_antes and app.render_pendente > 0)
 app.prova = false
 for i in 20: app._process(0.03)
 assert(app.sub.size.x >= ceil(app.zoom * app.TAM))
 assert(app.fisica.pos == pos and app.retrato)
 app.mudar("cochilo")
 app.estados.tempo = 5
 app.contorno_urgente = 0
 app.ocioso = 200
 app._process(0.03)
 assert(not app.renderizando)
 clique.position = app.pos_retrato
 app._input(clique)
 app._process(0.03)
 assert(app.renderizando and app.render_pendente > 0)
 for i in 20: app._process(0.03)
 assert(app.sub.size.x >= ceil(app.zoom * app.TAM))
 app.ocioso = 0
 app.mudar("parada")
 app.prova = true
 # Ocultação usa o mesmo caminho que a ponte fornece em produção.
 app.runtime = destino
 var desktop = {"monitor":{"x":0,"y":0,"width":1920,"height":1080,"reserved":[0,0,0,42]},"floors":[],"fullscreen":true}
 var arq = FileAccess.open(destino.path_join("desktop.json"),FileAccess.WRITE)
 arq.store_string(JSON.stringify(desktop)); arq.close()
 app.ler_desktop()
 assert(app.escondida and not app.sprite.visible)
 desktop.fullscreen = false
 desktop.game_mode = true
 arq = FileAccess.open(destino.path_join("desktop.json"),FileAccess.WRITE)
 arq.store_string(JSON.stringify(desktop)); arq.close()
 app.ler_desktop()
 assert(app.escondida)
 desktop.game_mode = false
 arq = FileAccess.open(destino.path_join("desktop.json"),FileAccess.WRITE)
 arq.store_string(JSON.stringify(desktop)); arq.close()
 app.ler_desktop()
 assert(not app.escondida and app.sprite.visible)
 app.runtime = ""
 DirAccess.remove_absolute(destino.path_join("desktop.json"))
 DirAccess.remove_absolute(destino.path_join("status.json"))
 app.ocioso = 0
 app.acao_menu("Modo passeio")
 app.trocar_boneca("chika-haruno")
 app._input(tecla)
 assert(app.boneca != "chika-haruno" and not app.retrato)
 app.trocar_boneca("chika-haruno")
 app.zoom = 2.5
 app.fisica.pos = Vector2(960,1038)
 app.estados.mudar("parada",60)
 app.aplicar_render()
 await estabilizar(app)
 assert(app.sub.size.x == 1152)
 root.get_texture().get_image().save_png(destino.path_join("passeio-zoom-2_5.png"))
 var novo = app.sub.size.x
 # Reprodução do render antigo fixo, no mesmo instante/pose/zoom.
 app.sub.size = Vector2i(448,448)
 await estabilizar(app)
 root.get_texture().get_image().save_png(destino.path_join("passeio-zoom-2_5-antes.png"))
 resultados = {"retrato_sono_acordar":true,"rodinha_debounce":true,"ampliar_dormindo":true,"B_dois_modos":true,"fullscreen_modo_jogo":true,"persistencia":true,"arrasto_clique":true,"render_zoom_2_5":novo,"render_antes":448}
 var f = FileAccess.open(destino.path_join("validacao.json"),FileAccess.WRITE)
 f.store_string(JSON.stringify(resultados,"  "))
 app.free()
 DirAccess.remove_absolute(destino.path_join("cache.json"))
 quit()
