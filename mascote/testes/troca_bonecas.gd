extends SceneTree
func _initialize():
 call_deferred("provar")
func provar():
 var app = load("res://mascote.gd").new()
 app.roupas.relogio = func(): return {"hour":12,"weekday":1}
 var cache_teste = "/tmp/kk-bonecas-%d.json" % OS.get_process_id()
 app.cache = cache_teste
 app.prova = false
 app.runtime = ""
 root.add_child(app)
 var posicao = app.fisica.pos
 var escala = app.zoom
 var resultados = []
 for b in app.bonecas:
  app.acao_menu("Boneca: "+b.nome)
  assert(app.boneca == b.id)
  assert(app.fisica.pos == posicao and app.zoom == escala)
  assert(app.sk.find_bone("cf_j_head")>=0)
  assert(app.olhar != null and not app.piscadas.is_empty())
  app.player.play("idle_em_pe")
  app.player.advance(0.0)
  var indice = app.sk.find_bone("cf_j_hand_L")
  var antes = app.sk.get_bone_pose_rotation(indice)
  app.player.advance(0.6)
  assert(not antes.is_equal_approx(app.sk.get_bone_pose_rotation(indice)))
  app.salvar()
  var salvo = JSON.parse_string(FileAccess.get_file_as_string(cache_teste))
  assert(salvo.boneca == b.id and salvo.escala == escala)
  resultados.append({"boneca":b.id,"idle_movimenta":true,"cache":true,"posicao_escala_preservadas":true})
 app.boneca = "inexistente"
 app.carregar()
 assert(app.boneca == app.bonecas[-1].id)
 app.queue_free()
 DirAccess.remove_absolute(cache_teste)
 var f = FileAccess.open("res://evidencias/troca-bonecas.json",FileAccess.WRITE)
 f.store_string(JSON.stringify(resultados,"  "))
 print(JSON.stringify(resultados))
 quit(0)
