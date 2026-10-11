extends SceneTree
# Usa o shader de produção em planos de teste; não renderiza corpos.
var pasta: String
var count := 0
func conferir(ok: bool, texto: String):
 count += 1
 if not ok:
  push_error(texto)
  quit(1)
  assert(ok,texto)

func _initialize():
 call_deferred("provar")

func provar():
 pasta = OS.get_environment("KK_PELE_PROVA")
 var casos = JSON.parse_string(FileAccess.get_file_as_string(pasta.path_join("amostras.json")))
 var mundo = Node3D.new()
 root.add_child(mundo)
 var sub = SubViewport.new()
 sub.size = Vector2i(800,800)
 sub.own_world_3d = true
 sub.render_target_update_mode = SubViewport.UPDATE_ALWAYS
 mundo.add_child(sub)
 var camera = Camera3D.new()
 camera.projection = Camera3D.PROJECTION_ORTHOGONAL
 camera.size = 4.0
 camera.position = Vector3(0,0,3)
 sub.add_child(camera)
 var luz = DirectionalLight3D.new()
 sub.add_child(luz)
 var imagem = Image.new()
 conferir(imagem.load(pasta.path_join("canais.png"))==OK,"Imagem sintética")
 var tex = ImageTexture.create_from_image(imagem)
 var branco = Image.create(2,2,false,Image.FORMAT_RGBA8)
 branco.fill(Color.WHITE)
 var tex_branca = ImageTexture.create_from_image(branco)
 var shader = load("res://shaders/kk_pele.gdshader")
 for i in casos.size():
  var caso=casos[i]
  var material=ShaderMaterial.new()
  material.shader=shader
  material.set_shader_parameter("tem_areola",true)
  material.set_shader_parameter("tem_over1",true)
  material.set_shader_parameter("overtex1",tex)
  material.set_shader_parameter("areola_tex",tex)
  material.set_shader_parameter("areola_srgb",caso.dados.srgb)
  material.set_shader_parameter("ramp_tex",tex_branca)
  material.set_shader_parameter("ambiente_kk",Vector4(1,1,1,0))
  material.set_shader_parameter("rim",0.0)
  var c=caso.cor
  material.set_shader_parameter("cor",Color(caso.base[0],caso.base[1],caso.base[2],1))
  material.set_shader_parameter("overcolor1",Color(c[0],c[1],c[2],c[3]))
  for k in ["tamanho","brilho","mistura","deformar"]:
   material.set_shader_parameter(k+"_areola",caso.dados[k])
  var st=caso.dados.uv_unity
  material.set_shader_parameter("uv_areola",Vector4(st[0],st[1],st[2],st[3]))
  var arrays=[]
  arrays.resize(Mesh.ARRAY_MAX)
  arrays[Mesh.ARRAY_VERTEX]=PackedVector3Array([Vector3(-.48,-.48,0),Vector3(.48,-.48,0),Vector3(.48,.48,0),Vector3(-.48,.48,0)])
  arrays[Mesh.ARRAY_NORMAL]=PackedVector3Array([Vector3.BACK,Vector3.BACK,Vector3.BACK,Vector3.BACK])
  arrays[Mesh.ARRAY_INDEX]=PackedInt32Array([0,1,2,0,2,3])
  arrays[Mesh.ARRAY_COLOR]=PackedColorArray([Color(caso.vermelho,0,0,1),Color(caso.vermelho,0,0,1),Color(caso.vermelho,0,0,1),Color(caso.vermelho,0,0,1)])
  var uv=Vector2(caso.uv[0],caso.uv[1])
  arrays[Mesh.ARRAY_TEX_UV]=PackedVector2Array([Vector2.ZERO,Vector2.RIGHT,Vector2.ONE,Vector2.DOWN])
  arrays[Mesh.ARRAY_TEX_UV2]=PackedVector2Array([uv,uv,uv,uv])
  var malha=ArrayMesh.new()
  malha.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
  var plano=MeshInstance3D.new()
  plano.mesh=malha
  plano.material_override=material
  plano.position=Vector3((i%4)-1.5,1.5-(i/4),0)
  sub.add_child(plano)
 for i in 10: await process_frame
 RenderingServer.force_draw()
 var render=sub.get_texture().get_image()
 conferir(render.save_png(pasta.path_join("planos-"+OS.get_environment("KK_PELE_RENDERER")+".png"))==OK,"Captura dos planos")
 var erros=[]
 for i in casos.size():
  var c=render.get_pixel((i%4)*200+100,(i/4)*200+100)
  var esperado=casos[i].esperado
  var erro=max(abs(c.r-esperado[0]),abs(c.g-esperado[1]),abs(c.b-esperado[2]))
  erros.append(erro)
  conferir(erro<.018,"Plano %d: erro %f; RGB %s; esperado %s" % [i,erro,c,esperado])
 # Conferir os parâmetros e a textura nos GLBs reais de todas as bonecas.
 var catalogo=JSON.parse_string(FileAccess.get_file_as_string("res://bonecas/catalogo.json"))
 for b in catalogo:
  var path="res://bonecas/"+b.id+"/saida/"
  var card=JSON.parse_string(FileAccess.get_file_as_string("res://bonecas/"+b.id+"/card.json")).Custom.corpo
  var personagem=load(path+"personagem_roupas.glb").instantiate()
  root.add_child(personagem)
  var info=load("res://materiais_kk.gd").aplicar(personagem,path)
  conferir(info.faltantes.is_empty(),b.id+": materiais completos")
  var corpos=0
  for malha in personagem.find_children("*","MeshInstance3D",true,false):
   for s in malha.mesh.get_surface_count():
    var mat=malha.get_surface_override_material(s)
    if mat.resource_name!="corpo__cf_m_body":continue
    corpos+=1
    conferir(mat.get_shader_parameter("tem_areola")==true,b.id+": camada corporal")
    conferir(mat.get_shader_parameter("tem_over1")==true,b.id+": textura ligada")
    conferir(mat.get_shader_parameter("overtex1")!=null,b.id+": textura carregada")
    conferir(mat.get_shader_parameter("areola_tex")!=null,b.id+": mapa linear carregado")
    conferir(mat.get_shader_parameter("areola_srgb")==false,b.id+": mapa linear preservado")
    conferir(abs(mat.get_shader_parameter("tamanho_areola")-card.areolaSize)<1e-6,b.id+": tamanho do card")
    conferir(abs(mat.get_shader_parameter("brilho_areola")-card.nipGlossPower)<1e-6,b.id+": brilho do card")
  conferir(corpos>=3,b.id+": variantes de corpo")
  personagem.queue_free()
 mundo.queue_free()
 var f=FileAccess.open(pasta.path_join("godot-"+OS.get_environment("KK_PELE_RENDERER")+".json"),FileAccess.WRITE)
 f.store_string(JSON.stringify({"sucesso":true,"verificacoes":count,"erros_rgb":erros},"  "))
 print("PELE CARD: ",count," verificações; planos sintéticos e materiais das três bonecas.")
 quit()
