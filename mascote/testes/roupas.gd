extends SceneTree
var erros: Array = []
var casos := 0
func verificar(ok: bool, texto: String):
 casos += 1
 if not ok: erros.append(texto)
func _initialize():
 call_deferred("provar")
func captura(app, nome):
 if DisplayServer.get_name() == "headless": return
 app.player.play("idle_em_pe")
 app.player.seek(0.6,true)
 app.player.pause()
 for i in 8: await process_frame
 app.atualizar_silhueta()
 app.posicionar()
 for i in 4: await process_frame
 RenderingServer.force_draw()
 root.get_texture().get_image().save_png(OS.get_environment("KK_PROVA_RETRATO").path_join(nome))
func provar():
 root.size = Vector2i(1920,1080)
 var app = load("res://mascote.gd").new()
 app.roupas.relogio = func(): return {"hour":12,"weekday":1}
 app.cache = "/tmp/kk-roupas-%d.json" % OS.get_process_id()
 app.prova = true
 app.runtime = ""
 root.add_child(app)
 app.set_process(false)
 for t in app.get_children():
  if t is Timer: t.stop()
 app.retrato = false
 app.zoom = 2.0
 app.fisica.pos = Vector2(960,1000)
 app.aplicar_render()
 var contagens = {}
 for b in app.bonecas:
  app.trocar_boneca(b.id)
  verificar(app.pecas_roupa.has("roupa_0") and app.pecas_roupa.has("roupa_1"), b.id+": roupas externas disponíveis")
  verificar(app.pecas_roupa.has("roupa_2") and app.pecas_roupa.has("roupa_3"), b.id+": peças íntimas disponíveis individualmente")
  var ids = app.pecas_roupa.keys()
  for tipo in ids:
   app.acao_menu("Ocultar: "+str(app.pecas_roupa[tipo]))
   verificar(tipo in app.roupas_ocultas[b.id], b.id+": ocultar "+str(tipo))
   for m in app.malhas:
    if m.mesh.get_surface_count() > 0 and m.mesh.surface_get_material(0).resource_name.begins_with(str(tipo)+"__"):
     verificar(not m.visible, b.id+": malha oculta "+str(m.name))
   app.acao_menu("Mostrar: "+str(app.pecas_roupa[tipo]))
   verificar(not tipo in app.roupas_ocultas[b.id], b.id+": mostrar "+str(tipo))
  var vertices_por_estado = {}
  for ocultas in [[],["roupa_0"],["roupa_1"],["roupa_0","roupa_1"]]:
   app.roupas_ocultas[b.id] = ocultas
   app.aplicar_roupas()
   var corpos = 0
   var bras = 0
   var indices = 0
   for m in app.malhas:
    if not m.visible: continue
    if str(m.name) == "o_body_a" or str(m.name).begins_with("kk_o_body_a_"):
     corpos += 1
     for si in m.mesh.get_surface_count(): indices += m.mesh.surface_get_array_index_len(si)
    elif m.mesh.get_surface_count() > 0 and m.mesh.surface_get_material(0).resource_name.begins_with("roupa_2__"): bras += 1
   verificar(corpos == 1 and bras >= 1, b.id+": um corpo e cobertura interna em "+str(ocultas))
   vertices_por_estado[str(ocultas)] = indices
  var numeros = vertices_por_estado.values()
  verificar(numeros[3] > numeros[0] and numeros[1] >= numeros[0] and numeros[2] >= numeros[0], b.id+": restaura triângulos sob as peças")
  contagens[b.id] = vertices_por_estado
  for mascara in 16:
   var ocultas: Array = []
   for slot in 4:
    if mascara & (1 << slot): ocultas.append("roupa_%d" % slot)
   app.roupas_ocultas[b.id] = ocultas
   app.aplicar_roupas()
   var corpos_visiveis = 0
   var bras_visiveis = 0
   var calcinhas_visiveis = 0
   for m in app.malhas:
    if not m.visible: continue
    if str(m.name) == "o_body_a" or str(m.name).begins_with("kk_o_body_a_"): corpos_visiveis += 1
    if m.mesh.get_surface_count() == 0: continue
    var tipo = m.mesh.surface_get_material(0).resource_name.get_slice("__",0)
    if tipo == "roupa_2": bras_visiveis += 1
    if tipo == "roupa_3": calcinhas_visiveis += 1
   verificar(corpos_visiveis == 1, b.id+": um corpo em combinação %d" % mascara)
   verificar((bras_visiveis == 0) == ("roupa_2" in ocultas), b.id+": sutiã independente em combinação %d" % mascara)
   verificar((calcinhas_visiveis == 0) == ("roupa_3" in ocultas), b.id+": calcinha independente em combinação %d" % mascara)
  app.acao_menu("Restaurar todas as peças")
  app.acao_menu("Ocultar todas as roupas")
  var corpo_inteiro = 0
  var roupa_visivel = 0
  for m in app.malhas:
   if not m.visible: continue
   if str(m.name) == "kk_o_body_a_11": corpo_inteiro += 1
   if m.mesh.get_surface_count() > 0 and m.mesh.surface_get_material(0).resource_name.begins_with("roupa_"): roupa_visivel += 1
  verificar(corpo_inteiro == 1 and roupa_visivel == 0, b.id+": ocultar todas conserva corpo completo")
  app.acao_menu("Restaurar todas as peças")
 app.trocar_boneca("chika-haruno")
 app.acao_menu("Voltar")
 app.menu.hide()
 await captura(app,"vestida.png")
 app.acao_menu("Ocultar: Blusa")
 app.menu.hide()
 await captura(app,"sem-blusa.png")
 app.acao_menu("Ocultar todas as roupas")
 app.menu.hide()
 await captura(app,"sem-roupas.png")
 app.prova = false
 app.salvar()
 var salvas = app.preferencias().duplicate(true)
 app.roupas_ocultas.clear()
 app.carregar()
 verificar(app.preferencias() == salvas, "Persistência de roupas por boneca")
 app.prova = true
 app.trocar_boneca("sawai-hinata")
 verificar(app.roupas_ocultas.get("sawai-hinata",[]).is_empty(), "Outra boneca conserva roupa própria")
 app.trocar_boneca("chika-haruno")
 verificar("roupa_2" in app.roupas_ocultas.get("chika-haruno",[]) and "roupa_3" in app.roupas_ocultas.get("chika-haruno",[]), "Voltar conserva escolhas íntimas")
 app.acao_menu("Restaurar todas as peças")
 DirAccess.remove_absolute(app.cache)
 var dados = {"passou":erros.is_empty(),"casos":casos,"erros":erros,"indices_corpo":contagens}
 var f = FileAccess.open("res://evidencias/roupas-validacao.json",FileAccess.WRITE)
 f.store_string(JSON.stringify(dados,"  "));f.close()
 print(JSON.stringify(dados))
 quit(0 if erros.is_empty() else 1)
