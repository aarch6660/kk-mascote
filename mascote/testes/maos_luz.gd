extends SceneTree
func _initialize(): call_deferred("provar")
func capturar(app,nome):
 for i in 8: await process_frame
 RenderingServer.force_draw()
 root.get_texture().get_image().save_png(OS.get_environment("KK_PROVA_RETRATO").path_join(nome))
func provar():
 root.size = Vector2i(900,1000)
 var app = load("res://mascote.gd").new()
 app.roupas.relogio = func(): return {"hour":12,"weekday":1}
 app.prova = true
 app.cache = "/tmp/kk-luz-inexistente-%d.json" % OS.get_process_id()
 app.runtime = ""
 root.add_child(app)
 app.set_process(false)
 app.olhar.active = false
 app.secundario.active = false
 for t in app.get_children():
  if t is Timer: t.stop()
 app.sub.size = Vector2i(900,1000)
 app.sprite.position = Vector2(450,500)
 app.sprite.scale = Vector2.ONE
 app.camera.size = 1.75
 app.camera.position = Vector3(0,0.78,4)
 app.player.play("idle_em_pe");app.player.seek(0.6,true);app.player.pause()
 app.roupas_ocultas[app.boneca] = app.pecas_roupa.keys()
 app.aplicar_roupas()
 var pele := []
 for m in app.malhas:
  for s in m.mesh.get_surface_count():
   var mat = m.get_surface_override_material(s)
   if mat is ShaderMaterial and str(mat.resource_name).begins_with("corpo__") and not pele.has(mat): pele.append(mat)
 for mat in pele: mat.shader = load("res://shaders/kk_toon.gdshader")
 await capturar(app,"luz-anterior.png")
 for mat in pele: mat.shader = load("res://shaders/kk_pele.gdshader")
 await capturar(app,"luz-base.png")
 app.secundario.relaxar = true
 app.secundario.repouso = true
 for i in 180: app.secundario.atualizar(1.0/30)
 await capturar(app,"maos-relaxadas.png")
 app.camera.size = 0.65
 var centro = (app.sk.get_bone_global_pose(app.sk.find_bone("cf_j_hand_L")).origin+app.sk.get_bone_global_pose(app.sk.find_bone("cf_j_hand_R")).origin)*0.5
 app.camera.position = Vector3(centro.x,centro.y,4)
 await capturar(app,"maos-detalhe.png")
 app.camera.size = 1.75
 app.camera.position = Vector3(0,0.78,4)
 for m in app.malhas:
  for s in m.mesh.get_surface_count():
   var mat = m.get_surface_override_material(s)
   if mat is ShaderMaterial and str(mat.resource_name).begins_with("corpo__"):
    mat.set_shader_parameter("especular",0.0)
 await capturar(app,"luz-sem-especular.png")
 var luz: DirectionalLight3D = app.camera.get_parent().find_children("*","DirectionalLight3D",true,false)[0]
 luz.shadow_enabled = false
 await capturar(app,"luz-sem-sombras.png")
 for m in app.malhas:
  for s in m.mesh.get_surface_count():
   var mat = m.get_surface_override_material(s)
   if mat is ShaderMaterial and str(mat.resource_name).begins_with("corpo__"):
    mat.set_shader_parameter("tem_normal",false)
 await capturar(app,"luz-sem-normal.png")
 quit()
