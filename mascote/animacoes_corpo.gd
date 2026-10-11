extends RefCounted
# Guarda fontes intactas: cada personagem recebe seus próprios offsets de repouso.
var fontes: Dictionary = {}
var repousos: Dictionary = {}
var propriedades: Dictionary = {}
func carregar() -> void:
 for arquivo in DirAccess.open("res://anims").get_files():
  if not arquivo.ends_with(".glb"): continue
  var cena = (load("res://anims/"+arquivo) as PackedScene).instantiate()
  var sk: Skeleton3D = cena.find_children("*","Skeleton3D",true,false)[0]
  var player: AnimationPlayer = cena.find_children("*","AnimationPlayer",true,false)[0]
  var rest := {}
  for i in sk.get_bone_count(): rest[sk.get_bone_name(i)] = sk.get_bone_rest(i)
  for nome in player.get_animation_list():
   if nome == "RESET": continue
   var anim: Animation = player.get_animation(nome)
   fontes[arquivo.get_basename()] = anim.duplicate(true)
   repousos[arquivo.get_basename()] = rest
   for t in anim.get_track_count():
    var osso := str(anim.track_get_path(t)).get_slice(":",1)
    var tipo := anim.track_get_type(t)
    if tipo in [Animation.TYPE_POSITION_3D,Animation.TYPE_ROTATION_3D,Animation.TYPE_SCALE_3D]:
     propriedades[osso+":"+str(tipo)] = [osso,tipo]
   break
  cena.free()
func biblioteca(sk: Skeleton3D, caminho: String) -> AnimationLibrary:
 var lib := AnimationLibrary.new()
 for nome in fontes:
  var anim: Animation = fontes[nome].duplicate(true)
  var usados := {}
  for t in anim.get_track_count():
   var osso := str(anim.track_get_path(t)).get_slice(":",1)
   var i := sk.find_bone(osso)
   if i < 0: continue
   var tipo := anim.track_get_type(t)
   anim.track_set_path(t,NodePath(caminho+":"+osso))
   usados[osso+":"+str(tipo)] = true
   var fonte: Transform3D = repousos[nome].get(osso,sk.get_bone_rest(i))
   var destino := sk.get_bone_rest(i)
   for k in anim.track_get_key_count(t):
    var valor = anim.track_get_key_value(t,k)
    match tipo:
     Animation.TYPE_POSITION_3D: valor = destino.origin+(valor-fonte.origin)
     Animation.TYPE_ROTATION_3D: valor = (destino.basis.get_rotation_quaternion()*fonte.basis.get_rotation_quaternion().inverse()*valor).normalized()
     Animation.TYPE_SCALE_3D: valor = destino.basis.get_scale()*valor/fonte.basis.get_scale()
    anim.track_set_key_value(t,k,valor)
  # Uma pista omitida volta ao repouso, em vez de herdar a pose do último clipe.
  for chave in propriedades:
   if usados.has(chave): continue
   var prop: Array = propriedades[chave]
   var i := sk.find_bone(prop[0])
   if i < 0: continue
   var rest := sk.get_bone_rest(i)
   var valor = rest.origin if prop[1] == Animation.TYPE_POSITION_3D else (rest.basis.get_rotation_quaternion() if prop[1] == Animation.TYPE_ROTATION_3D else rest.basis.get_scale())
   var t := anim.add_track(prop[1])
   anim.track_set_path(t,NodePath(caminho+":"+prop[0]))
   anim.track_insert_key(t,0,valor)
   anim.track_insert_key(t,anim.length,valor)
  var pontuais: Array = JSON.parse_string(FileAccess.get_file_as_string("res://gestos.json")).get("pontuais",[])
  anim.loop_mode = Animation.LOOP_NONE if nome in pontuais else Animation.LOOP_LINEAR
  lib.add_animation(nome,anim)
 # Recortes do gesto original de tocar a tela (f_tachi_00_05): toques do indicador em loop e o "enviar".
 if lib.has_animation("celular_em_pe_transicao"):
  var toque: Animation = lib.get_animation("celular_em_pe_transicao")
  lib.add_animation("celular_digitar",recortar(toque,1.0,2.0,true))
  lib.add_animation("celular_enviar",recortar(toque,2.0,3.4,false))
 return lib

# Reamostra [ini, fim] a 30 fps. Em loop, os últimos 0,2 s convergem para o primeiro quadro (emenda sem salto).
func recortar(origem: Animation, ini: float, fim: float, loop: bool) -> Animation:
 var anim := Animation.new()
 var duracao := fim-ini
 anim.length = duracao
 anim.loop_mode = Animation.LOOP_LINEAR if loop else Animation.LOOP_NONE
 var quadros := int(round(duracao*30.0))
 for t in origem.get_track_count():
  var tipo := origem.track_get_type(t)
  if tipo not in [Animation.TYPE_POSITION_3D,Animation.TYPE_ROTATION_3D,Animation.TYPE_SCALE_3D]: continue
  var nova := anim.add_track(tipo)
  anim.track_set_path(nova,origem.track_get_path(t))
  var primeiro = null
  for k in quadros+1:
   var tempo := ini+duracao*k/float(quadros)
   var valor
   match tipo:
    Animation.TYPE_POSITION_3D: valor = origem.position_track_interpolate(t,tempo)
    Animation.TYPE_ROTATION_3D: valor = origem.rotation_track_interpolate(t,tempo)
    _: valor = origem.scale_track_interpolate(t,tempo)
   if k == 0: primeiro = valor
   var resta := duracao-duracao*k/float(quadros)
   if loop and resta < 0.2:
    var peso := 1.0-resta/0.2
    valor = valor.slerp(primeiro,peso) if tipo == Animation.TYPE_ROTATION_3D else valor.lerp(primeiro,peso)
   anim.track_insert_key(nova,duracao*k/float(quadros),valor)
 return anim
