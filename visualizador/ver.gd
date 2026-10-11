extends Node3D
# Visualizador: setas/A-D giram a câmera, rodinha aproxima, espaço/N troca a animação.

var clipes := []          # [nome, Animation]
var atual := 0
var player: AnimationPlayer
var cam: Camera3D
var rotacao := 0.0
var dist := 3.0
var rotulo: Label
var prova := "--prova" in OS.get_cmdline_user_args()
var chika: Node3D
var relatorio: Dictionary
var capturando := false
var catalogo_gestos: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://gestos.json"))
var expressao_card := false
var fisica_secundaria: SkeletonModifier3D
var expression: SkeletonModifier3D
func preparar_fisica(sk: Skeleton3D) -> void:
 expression = preload("res://expression_kk.gd").new()
 sk.add_child(expression)
 expression.configurar(pasta_boneca()+"expression_kk.json")
 fisica_secundaria = preload("res://fisica_kk_modificador.gd").new()
 sk.add_child(fisica_secundaria)
 fisica_secundaria.configurar(pasta_boneca()+"fisica_kk.json")

func _ready():
 ler_bonecas()
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--boneca="): boneca = arg.trim_prefix("--boneca=")
 var env := WorldEnvironment.new()
 var e := Environment.new()
 e.background_mode = Environment.BG_COLOR
 e.background_color = Color(0.45, 0.47, 0.52)
 e.tonemap_mode = Environment.TONE_MAPPER_LINEAR
 e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
 e.ambient_light_color = Color(1, 1, 1)
 e.ambient_light_energy = 0.0
 get_viewport().msaa_3d = Viewport.MSAA_4X
 get_viewport().screen_space_aa = Viewport.SCREEN_SPACE_AA_FXAA
 env.environment = e
 add_child(env)
 # AmplifyColor/Lut_Amount original: aplica depois da conversão linear → sRGB.
 var camada_cor := CanvasLayer.new()
 camada_cor.layer = -1
 var pos_cor := ColorRect.new()
 pos_cor.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
 pos_cor.mouse_filter = Control.MOUSE_FILTER_IGNORE
 var mat_cor := ShaderMaterial.new()
 mat_cor.shader = load("res://shaders/kk_pos.gdshader")
 mat_cor.set_shader_parameter("lut_kk",load("res://bonecas/visual_comum/Lut_Amount.png"))
 pos_cor.material = mat_cor
 camada_cor.add_child(pos_cor)
 add_child(camada_cor)
 var sol := DirectionalLight3D.new()
 sol.rotation_degrees = Vector3(-10, 0, 0) # luz quase frontal, como a do personagem no KK
 sol.light_energy = 1.0
 sol.shadow_enabled = true
 sol.directional_shadow_max_distance = 5.0
 sol.shadow_bias = 0.02
 sol.shadow_normal_bias = 0.25
 add_child(sol)
 var chao := MeshInstance3D.new()
 var p := PlaneMesh.new(); p.size = Vector2(3, 3)
 chao.mesh = p
 var m := StandardMaterial3D.new(); m.albedo_color = Color(0.37, 0.39, 0.44)
 chao.material_override = m
 add_child(chao)

 chika = (load(pasta_boneca()+"personagem.glb") as PackedScene).instantiate()
 add_child(chika)
 relatorio = preload("res://materiais_kk.gd").aplicar(chika,pasta_boneca())
 expressao(false)
 print("Materiais KK: ",relatorio)
 var sk: Skeleton3D = chika.find_children("*", "Skeleton3D", true, false)[0]
 player = AnimationPlayer.new()
 chika.add_child(player)
 var caminho_sk := String(player.get_parent().get_path_to(sk))
 var lib := AnimationLibrary.new()
 var dir := DirAccess.open("res://anims")
 var nomes := []
 for f in dir.get_files():
  if f.ends_with(".glb"): nomes.append(f.get_basename())
 nomes.sort()
 nomes.erase("idle_em_pe"); nomes.push_front("idle_em_pe")
 for nome in nomes:
  var cena: Node = (load("res://anims/%s.glb" % nome) as PackedScene).instantiate()
  var ap: AnimationPlayer = cena.find_children("*", "AnimationPlayer", true, false)[0]
  for an in ap.get_animation_list():
   if an == "RESET": continue
   var anim: Animation = ap.get_animation(an).duplicate(true)
   for t in anim.get_track_count():
    var tp := String(anim.track_get_path(t))
    var osso := tp.get_slice(":", 1)
    anim.track_set_path(t, NodePath(caminho_sk + ":" + osso))
   anim.loop_mode = Animation.LOOP_NONE if nome in catalogo_gestos.get("pontuais",[]) else Animation.LOOP_LINEAR
   lib.add_animation(nome, anim)
   clipes.append(nome)
   break
  cena.free()
 player.add_animation_library("", lib)
 preparar_fisica(sk)

 cam = Camera3D.new()
 cam.fov = 35
 add_child(cam)
 rotulo = Label.new()
 rotulo.position = Vector2(16, 8)
 rotulo.add_theme_font_size_override("font_size", 15)
 rotulo.add_theme_color_override("font_color", Color(1, 0.65, 0.2))
 add_child(rotulo)
 tocar()
 if prova: call_deferred("capturar_provas")

func tocar():
 player.play(clipes[atual], 0.3)
 var categoria := ""
 for grupo in catalogo_gestos.get("categorias",{}):
  if clipes[atual] in catalogo_gestos.categorias[grupo]: categoria = " · "+str(grupo); break
 rotulo.text = "%s%s   (%d/%d)\nespaço: próxima · setas: girar · rodinha: zoom · G: expressão do card · B: boneca %s" % [clipes[atual], categoria, atual + 1, clipes.size(),boneca]

func _unhandled_input(ev):
 if ev is InputEventKey and ev.pressed:
  if ev.keycode in [KEY_SPACE, KEY_N]:
   atual = (atual + 1) % clipes.size(); tocar()
  elif ev.keycode == KEY_B:
   trocar_boneca()
  elif ev.keycode == KEY_G:
   expressao(not expressao_card)
  elif ev.keycode == KEY_ESCAPE:
   get_tree().quit()
 if ev is InputEventMouseButton and ev.pressed:
  if ev.button_index == MOUSE_BUTTON_WHEEL_UP: dist = max(0.8, dist - 0.15)
  if ev.button_index == MOUSE_BUTTON_WHEEL_DOWN: dist = min(5.0, dist + 0.15)
  if ev.button_index == MOUSE_BUTTON_LEFT:
   atual = (atual + 1) % clipes.size(); tocar()

func _process(d):
 if capturando: return
 if Input.is_key_pressed(KEY_LEFT) or Input.is_key_pressed(KEY_A): rotacao -= d * 1.5
 if Input.is_key_pressed(KEY_RIGHT) or Input.is_key_pressed(KEY_D): rotacao += d * 1.5
 var alvo := Vector3(0, 0.75, 0)
 cam.position = alvo + Vector3(sin(rotacao), 0.12, cos(rotacao)) * dist
 cam.look_at(alvo)

# Captura no servidor X virtual: --prova. Não usa renderer dummy/headless.
func capturar_provas():
 capturando = true
 fisica_secundaria.pausado = true
 rotulo.hide()
 player.play("idle_em_pe")
 player.seek(0.6,true)
 player.pause()
 for f in 2: await get_tree().process_frame
 var sk = chika.find_children("*", "Skeleton3D", true, false)[0]
 var eye = sk.find_bone("cf_J_Eye_tx_L")
 var altura_rosto = sk.to_global(sk.get_bone_global_pose(eye).origin).y - 0.03
 cam.projection = Camera3D.PROJECTION_ORTHOGONAL
 var saida = ProjectSettings.globalize_path("res://bonecas/%s/saida/" % boneca)
 for tomada in [{"nome":"render_frente","alvo":Vector3(0,0.86,0),"pos":Vector3(0,0.92,4),"size":1.95},{"nome":"render_tres_quartos","alvo":Vector3(0,0.86,0),"pos":Vector3(2.2,1.0,3.5),"size":1.95},{"nome":"render_rosto","alvo":Vector3(0,altura_rosto,0),"pos":Vector3(0,altura_rosto+0.02,3),"size":0.58}]:
  cam.size = tomada.size
  cam.position = tomada.pos
  cam.look_at(tomada.alvo)
  for f in 8: await get_tree().process_frame
  await RenderingServer.frame_post_draw
  var im = get_viewport().get_texture().get_image()
  im.save_png(saida+tomada.nome+".png")
  print("Captura ",tomada.nome)
 expressao(true)
 for f in 8: await get_tree().process_frame
 await RenderingServer.frame_post_draw
 get_viewport().get_texture().get_image().save_png(saida+"render_card.png")
 var arq = FileAccess.open(saida+"validacao_visual_godot.json",FileAccess.WRITE)
 arq.store_string(JSON.stringify(relatorio,"  "))
 get_tree().quit()

# G alterna o padrão 23, resolvido da tabela cha_eyeset original.
func expressao(usar_card: bool):
 usar_card = usar_card and chika.find_children("*gag_eye*","MeshInstance3D",true,false).size() > 0
 expressao_card = usar_card
 for malha in chika.find_children("*","MeshInstance3D",true,false):
  var nome = malha.name
  if nome == "cf_O_face":
   var mat = malha.get_surface_override_material(0)
   if mat is ShaderMaterial: mat.set_shader_parameter("expressao_gag",usar_card)
  if "gag_eye" in nome: malha.visible = usar_card
  if "hitomi" in nome or "eyeline" in nome: malha.visible = not usar_card
  for i in malha.mesh.get_blend_shape_count():
   var shape = String(malha.mesh.get_blend_shape_name(i))
   if shape.begins_with("eye_"):
    malha.set_blend_shape_value(i,1.0 if shape.ends_with("_gag") and usar_card or shape.ends_with("_def_op") and not usar_card else 0.0)

var bonecas: Array = []
var boneca := "chika-haruno"
func pasta_boneca() -> String:
 return "res://bonecas/"+boneca+"/saida/"
func ler_bonecas():
 var dados = JSON.parse_string(FileAccess.get_file_as_string("res://bonecas/catalogo.json"))
 if dados is Array: bonecas = dados
 if not bonecas.any(func(b): return b.id == boneca) and not bonecas.is_empty(): boneca = bonecas[0].id

func trocar_boneca():
 if bonecas.size() < 2: return
 var indice = 0
 for i in bonecas.size():
  if bonecas[i].id == boneca: indice = i
 boneca = bonecas[(indice+1)%bonecas.size()].id
 var anterior = chika
 anterior.remove_child(player)
 chika = (load(pasta_boneca()+"personagem.glb") as PackedScene).instantiate()
 add_child(chika)
 chika.add_child(player)
 anterior.free()
 relatorio = preload("res://materiais_kk.gd").aplicar(chika,pasta_boneca())
 var sk = chika.find_children("*","Skeleton3D",true,false)[0]
 var caminho = String(chika.get_path_to(sk))
 for nome in player.get_animation_list():
  var anim = player.get_animation(nome)
  for t in anim.get_track_count(): anim.track_set_path(t,NodePath(caminho+":"+String(anim.track_get_path(t)).get_slice(":",1)))
 player.clear_caches()
 preparar_fisica(sk)
 expressao(false)
 tocar()
