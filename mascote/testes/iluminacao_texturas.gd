extends SceneTree
func _initialize(): call_deferred("provar")
func provar():
 root.size = Vector2i(700,950)
 var app = load("res://mascote.gd").new()
 app.roupas.relogio = func(): return {"hour":12,"weekday":1}
 app.prova = true
 app.cache = "/tmp/kk-visual-cache-%d.json" % OS.get_process_id()
 app.runtime = ""
 root.add_child(app)
 app.set_process(false)
 for t in app.get_children():
  if t is Timer: t.stop()
 var pasta := OS.get_environment("KK_PROVA_RETRATO")
 for b in app.bonecas:
  app.trocar_boneca(b.id)
  app.olhar.active = false
  app.secundario.active = false
  app.sub.size = Vector2i(700,950)
  app.sprite.position = Vector2(350,475)
  app.sprite.scale = Vector2.ONE
  app.roupas_ocultas[b.id] = []
  app.aplicar_roupas()
  app.player.play("idle_em_pe")
  app.player.seek(0.6,true)
  app.player.advance(0)
  app.player.pause()
  app.rosto.aplicar("Neutra",0,"a",0,1)
  var shader_antes = OS.get_environment("KK_PROVA_SHADER_PELE")
  if not shader_antes.is_empty():
   var antigo := Shader.new()
   antigo.code = FileAccess.get_file_as_string(shader_antes)
   for mesh in app.find_children("*","MeshInstance3D",true,false):
    for superficie in mesh.mesh.get_surface_count():
     var m = mesh.get_surface_override_material(superficie)
     if m is ShaderMaterial and m.shader.resource_path.ends_with("kk_pele.gdshader"):
      m.shader = antigo
  var vistas = ["busto","rosto"]
  if OS.get_environment("KK_PROVA_LUZ_SERIE")=="1":
   vistas = ["rosto","rosto-esquerda","rosto-direita"]
  for vista in vistas:
   for lamp in app.find_children("*","DirectionalLight3D",true,false):
    if lamp is DirectionalLight3D:
     lamp.rotation_degrees = Vector3(-25,-25,0)
     if vista=="rosto-esquerda": lamp.rotation_degrees.y = -75
     if vista=="rosto-direita": lamp.rotation_degrees.y = 75
   app.camera.size = 1.05 if vista=="busto" else 0.33
   var olho: int = app.sk.find_bone("cf_J_Eye_tx_L")
   var altura: float = app.sk.get_bone_global_pose(olho).origin.y
   app.camera.position = Vector3(0,altura-(0.32 if vista=="busto" else 0.018),4)
   for i in 8: await process_frame
   RenderingServer.force_draw()
   root.get_texture().get_image().save_png(pasta.path_join(b.id+"-"+vista+".png"))
 app.free()
 quit()
