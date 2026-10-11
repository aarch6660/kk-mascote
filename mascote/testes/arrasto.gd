extends SceneTree
var erros: Array = []
var casos := 0
func verificar(ok: bool, mensagem: String):
 casos += 1
 if not ok: erros.append(mensagem)
func _initialize():
 call_deferred("provar")
func provar():
 root.size = Vector2i(1920,1080)
 var app = load("res://mascote.gd").new()
 app.roupas.relogio = func(): return {"hour":12,"weekday":1}
 app.cache = "/tmp/kk-arrasto-%d.json" % OS.get_process_id()
 app.runtime = ""
 root.add_child(app)
 app.set_process(false)
 for t in app.get_children():
  if t is Timer: t.stop()
 app.retrato = false
 app.zoom = 0.75
 app.fisica.pos = Vector2(800,600)
 app.fisica.apoio = "tela"
 app.limites = Rect2(170,70,110,350)
 app.local_poly = PackedVector2Array([Vector2(140,40),Vector2(310,40),Vector2(310,448),Vector2(140,448)])
 app.posicionar()
 app.mudar("andando")
 var ponto = app.sprite.position
 var clique = InputEventMouseButton.new()
 clique.button_index = MOUSE_BUTTON_LEFT
 clique.position = ponto
 clique.pressed = true
 app._input(clique)
 verificar(app.pressionada and app.fisica.arrastando and app.estados.estado == "parada", "Pressionar suspende movimento imediatamente")
 var origem = app.fisica.pos
 app.fisica.atualizar([],1920,1038)
 app.fisica.passo(1,46)
 verificar(app.fisica.pos == origem, "Ponte e física não movem durante captura")
 verificar(app.regiao_entrada.size() == 4 and Geometry2D.is_point_in_polygon(Vector2(15,15),app.regiao_entrada), "Captura abrange tela durante arrasto")
 var movimento = InputEventMouseMotion.new()
 movimento.position = ponto + Vector2(280,-150)
 app._input(movimento)
 verificar(app.arrastando and app.fisica.pos.is_equal_approx(origem + Vector2(280,-150)), "Arrasto preserva deslocamento do ponto pego")
 clique.position = movimento.position
 clique.pressed = false
 app._input(clique)
 var destino = app.fisica.pos
 verificar(not app.pressionada and not app.arrastando and app.fisica.fixa, "Soltar fixa na posição escolhida")
 verificar(not Geometry2D.is_point_in_polygon(Vector2(15,15),app.regiao_entrada), "Soltar devolve região vazia ao desktop")
 app.fisica.atualizar([],1920,1038)
 for i in 600:
  app.fisica.passo(1.0/30,46)
  app.estados.passo(1.0/30,0,true,true,false,true)
  verificar(app.estados.estado != "andando" and app.estados.estado != "sentada", "Fixada não passeia nem desloca para borda")
 verificar(app.fisica.pos == destino, "Permanece por 20 segundos mesmo sem janela de apoio")
 app.salvar()
 app.fisica.fixa = false
 app.fisica.pos = Vector2.ZERO
 app.carregar()
 verificar(app.fisica.fixa and app.fisica.pos == destino, "Reinício conserva posição fixada")
 app.acao_menu("Soltar e passear")
 app.fisica.passo(0.1)
 verificar(not app.fisica.fixa and app.fisica.pos.y > destino.y, "Menu restaura gravidade e passeio")
 DirAccess.remove_absolute(app.cache)
 print(JSON.stringify({"casos":casos,"erros":erros,"passou":erros.is_empty()}))
 quit(0 if erros.is_empty() else 1)
