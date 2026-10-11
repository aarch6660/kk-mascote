extends SceneTree
func _initialize():
 call_deferred("provar")
func provar():
 var catalogo = JSON.parse_string(FileAccess.get_file_as_string("res://bonecas/catalogo.json"))
 var resultados = []
 var erros = []
 var seletor = ""
 var coordenada := 0
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--boneca="): seletor = arg.trim_prefix("--boneca=")
  if arg.begins_with("--coordenada="): coordenada = arg.trim_prefix("--coordenada=").to_int()
 for b in catalogo:
  if seletor != "" and b.id != seletor: continue
  var pasta = "res://bonecas/"+b.id+"/saida/"
  if coordenada != 0: pasta = "res://bonecas/"+b.id+"/coordenadas/coord_%d/saida/" % coordenada
  var cena = load(pasta+"personagem.glb") as PackedScene
  if cena == null: erros.append([b.id,"GLB inválido"]); continue
  var boneca = cena.instantiate()
  root.add_child(boneca)
  var skeletons = boneca.find_children("*","Skeleton3D",true,false)
  if skeletons.size() != 1: erros.append([b.id,"Esqueleto inválido"]);boneca.free();continue
  var sk = skeletons[0]
  var materiais = preload("res://materiais_kk.gd").aplicar(boneca,pasta)
  if not materiais.faltantes.is_empty(): erros.append([b.id,materiais.faltantes])
  var ausentes = []
  var clipes = 0
  for arquivo in DirAccess.open("res://anims").get_files():
   if not arquivo.ends_with(".glb"):continue
   clipes += 1
   var origem = (load("res://anims/"+arquivo) as PackedScene).instantiate()
   var ap = origem.find_children("*","AnimationPlayer",true,false)[0]
   for nome in ap.get_animation_list():
    if nome == "RESET":continue
    var anim = ap.get_animation(nome)
    for t in anim.get_track_count():
     var osso = str(anim.track_get_path(t)).get_slice(":",1)
     if sk.find_bone(osso)<0:ausentes.append([arquivo,osso])
   origem.free()
  if not ausentes.is_empty():erros.append([b.id,ausentes])
  var item = {"boneca":b.id,"ossos":sk.get_bone_count(),"clipes":clipes,"ausentes":ausentes,"materiais":materiais}
  resultados.append(item)
  var f = FileAccess.open(pasta+"validacao_boneca.json",FileAccess.WRITE)
  f.store_string(JSON.stringify(item,"  "))
  boneca.free()
 print(JSON.stringify({"bonecas":resultados,"erros":erros}))
 quit(0 if erros.is_empty() and not resultados.is_empty() else 1)
