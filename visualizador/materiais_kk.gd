extends RefCounted
# O manifesto é gerado a partir de pecas.json + materiais Unity + card.
static func aplicar(raiz: Node, pasta: String = "res://") -> Dictionary:
 var dados = JSON.parse_string(FileAccess.get_file_as_string(pasta+"materiais_kk.json"))
 var ambiente = JSON.parse_string(FileAccess.get_file_as_string("res://bonecas/visual_comum/cores_kk.json")).ambiente_kk
 var opaco = load("res://shaders/kk_toon.gdshader")
 var pele = load("res://shaders/kk_pele.gdshader")
 var alpha = load("res://shaders/kk_alpha.gdshader")
 var casco = load("res://shaders/kk_contorno.gdshader")
 var cache = {}
 var total = 0
 var faltantes = []
 for malha in raiz.find_children("*", "MeshInstance3D", true, false):
  for s in malha.mesh.get_surface_count():
   var original = malha.mesh.surface_get_material(s)
   var chave = original.resource_name
   if not dados.has(chave):
    faltantes.append(chave)
    continue
   if not cache.has(chave):
    var c = dados[chave]
    var m = ShaderMaterial.new()
    m.shader = pele if chave.begins_with("corpo__") or c.rosto else (alpha if c.alpha else opaco)
    m.resource_name = chave
    m.set_shader_parameter("ambiente_kk",Vector4(ambiente[0],ambiente[1],ambiente[2],ambiente[3]))
    for k in ["cor","cor2","cor3","sombra","linha"]:
     var v = c[k]
     m.set_shader_parameter(k,Color(v[0],v[1],v[2],v[3]))
    for k in ["cabelo","rosto","olhos","rim","rim_potencia","normal_forca","sombra_extensao","especular","especular_altura","linha_r","linha_g"]:
     m.set_shader_parameter(k,c[k])
    var slots = {"_MainTex":"main_tex","_ColorMask":"color_mask","_DetailMask":"detail_mask","_NormalMask":"normal_mask","_LineMask":"line_mask","_NormalMap":"normal_tex","_BumpMap":"normal_tex","_AlphaMask":"alpha_mask","_AnotherRamp":"view_ramp_tex","_RampG":"ramp_tex","_HairGloss":"hair_gloss"}
    for k in slots:
     if c.texturas.has(k):
      m.set_shader_parameter(slots[k],load((pasta+"visual/" if pasta != "res://" else "res://texturas/")+c.texturas[k]))
    if c.cabelo and c.texturas.has("_AnotherRamp"):
     m.set_shader_parameter("view_ramp_tex",load(pasta+"visual/"+c.texturas._AnotherRamp))
    if not c.texturas.has("_RampG"):
     m.set_shader_parameter("ramp_tex",load(pasta+"visual/gt_ramp_01.png"))
    m.set_shader_parameter("tem_main",c.texturas.has("_MainTex"))
    m.set_shader_parameter("tem_mask",c.texturas.has("_ColorMask"))
    m.set_shader_parameter("tem_normal",c.texturas.has("_NormalMap") or c.texturas.has("_BumpMap"))
    if c.has("uv_maquiagem"):
     var u=c.uv_maquiagem
     m.set_shader_parameter("uv_maquiagem",Vector4(u[0],u[1],u[2],u[3]))
    if c.has("pelos_srgb"):
     m.set_shader_parameter("tem_pelos",true)
     m.set_shader_parameter("pelos_srgb",c.pelos_srgb)
     m.set_shader_parameter("pelos_tex",load((pasta+"visual/" if pasta != "res://" else "res://texturas/")+c.texturas._overtex2))
    if c.has("uv_pelos_unity"):
     var u=c.uv_pelos_unity
     m.set_shader_parameter("uv_pelos_unity",Vector4(u[0],u[1],u[2],u[3]))
    if c.has("areola"):
     var a=c.areola
     m.set_shader_parameter("tem_areola",true)
     m.set_shader_parameter("areola_srgb",a.srgb)
     m.set_shader_parameter("areola_tex",load((pasta+"visual/" if pasta != "res://" else "res://texturas/")+c.texturas._overtex1))
     for k in ["tamanho","brilho","mistura","deformar"]:
      m.set_shader_parameter(k+"_areola",a[k])
     var u=a.uv_unity
     m.set_shader_parameter("uv_areola",Vector4(u[0],u[1],u[2],u[3]))
    for i in range(1,4):
     var slot="_overtex%d" % i
     # hohoAkaRate=0 no card: overlay de rubor transitório fica desativado.
     var usar = c.has("sobre_cores") and c.sobre_cores.has(slot) and c.texturas.has(slot)
     m.set_shader_parameter("tem_over%d" % i,usar)
     if usar:
      m.set_shader_parameter("overtex%d" % i,load((pasta+"visual/" if pasta != "res://" else "res://texturas/")+c.texturas[slot]))
      var v=c.sobre_cores[slot]
      m.set_shader_parameter("overcolor%d" % i,Color(v[0],v[1],v[2],v[3]))
    m.set_shader_parameter("normal_dxt5",true)
    if c.contorno > 0.0:
     var o = ShaderMaterial.new()
     o.shader = casco
     o.set_shader_parameter("espessura",c.contorno)
     var v = c.cor_contorno
     o.set_shader_parameter("cor_contorno",Color(v[0],v[1],v[2],v[3]))
     if c.texturas.has("_AlphaMask"): o.set_shader_parameter("alpha_mask",load((pasta+"visual/" if pasta != "res://" else "res://texturas/")+c.texturas._AlphaMask))
     if c.texturas.has("_MainTex"):
      o.set_shader_parameter("tem_main",true)
      o.set_shader_parameter("main_tex",load((pasta+"visual/" if pasta != "res://" else "res://texturas/")+c.texturas._MainTex))
     m.next_pass = o
    cache[chave]=m
   malha.set_surface_override_material(s,cache[chave])
   malha.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
   total += 1
 return {"superficies":total,"materiais":cache.size(),"faltantes":faltantes}
