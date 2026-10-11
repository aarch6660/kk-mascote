extends SkeletonModifier3D
# Mãos/contato suaves e cadeias físicas com parâmetros do rig original.
var ligado := true
var maos_suaves := true
var repouso := true
var relaxar := false
var poses_maos: Array = []
var dormindo := false
var impulso := Vector3.ZERO
var toque_osso := -1
var pressao := 0.0
var tempo := 0.0
var canais: Array = []
var ultimos: Dictionary = {}
var deltas: Dictionary = {}
var inicializado := false
var pausado := false
var nativa = preload("res://fisica_kk.gd").new()
func configurar_fisica(caminho: String) -> void:
 nativa.configurar(get_skeleton(),caminho)
 canais.clear()
 ultimos.clear()
 deltas.clear()
 inicializado = false
func _process_modification_with_delta(delta: float) -> void:
 atualizar(delta)
func preparar() -> void:
 var sk := get_skeleton()
 for i in sk.get_bone_count():
  var nome := sk.get_bone_name(i)
  var tipo := ""
  if nome.begins_with("cf_J_hair") and not nome.ends_with("top") and not nome.ends_with("_s"): tipo = "cabelo"
  elif nome.begins_with("cf_j_sk_"): tipo = "roupa"
  elif nome in ["cf_j_bust01_L","cf_j_bust01_R","cf_j_bust02_L","cf_j_bust02_R"]: tipo = "corpo"
  elif nome.begins_with("cf_j_") and ("01_" in nome or "02_" in nome or "03_" in nome) and ("index" in nome or "middle" in nome or "ring" in nome or "little" in nome or "thumb" in nome): tipo = "dedo"
  # A torção do punho pertence ao ExpressionBone, que já rodou neste frame.
  # O controle Mãos suaves conserva os dedos; não gira cf_j_hand para o repouso.
  elif nome in ["cf_j_spine02","cf_j_spine03","cf_j_arm00_L","cf_j_arm00_R","cf_j_thigh00_L","cf_j_thigh00_R"]: tipo = "toque"
  if tipo.is_empty(): continue
  if not nativa.dados.is_empty() and tipo in ["cabelo","roupa","corpo"]: continue
  canais.append({"i":i,"tipo":tipo,"angulo":Vector3.ZERO,"velocidade":Vector3.ZERO,"pos":Vector3.ZERO,"vbase":Vector3.ZERO,"primeiro":true})
 inicializado = true
func configurar_maos(player: AnimationPlayer) -> void:
 poses_maos.clear()
 for clipe in ["conversa_03","sentada_idle"]:
  var pose := {}
  var anim := player.get_animation(clipe)
  for t in anim.get_track_count():
   if anim.track_get_type(t) != Animation.TYPE_ROTATION_3D: continue
   var nome := str(anim.track_get_path(t)).get_slice(":",1)
   if any_dedo(nome): pose[nome] = anim.rotation_track_interpolate(t,0.6)
  poses_maos.append(pose)
func any_dedo(nome: String) -> bool:
 return nome.begins_with("cf_j_") and ("thumb" in nome or "index" in nome or "middle" in nome or "ring" in nome or "little" in nome)
func atualizar(dt: float) -> void:
 if pausado or dt <= 0 or not is_finite(dt): return
 dt = minf(dt,0.1)
 if not inicializado: preparar()
 var sk := get_skeleton()
 nativa.restaurar(sk)
 tempo += dt
 var bases := {}
 var pais := {}
 # Retira todas as correções antes de medir a animação; as molas não excitam
 # umas às outras por amostrar uma mistura de poses do quadro anterior/atual.
 for canal in canais:
  var i: int = canal.i
  var base := sk.get_bone_pose_rotation(i)
  if ultimos.has(i) and base.is_equal_approx(ultimos[i]): base = (base*Quaternion(deltas[i]).inverse()).normalized()
  base = base.normalized()
  bases[i] = base
  sk.set_bone_pose_rotation(i,base)
 for canal in canais: pais[canal.i] = sk.get_bone_global_pose(sk.get_bone_parent(canal.i))
 for canal in canais:
  var i: int = canal.i
  var base: Quaternion = bases[i]
  # Posição do pai antes da própria correção evita realimentação da mola.
  var transform_pai: Transform3D = pais[i]
  var pos := transform_pai.origin
  var velocidade := Vector3.ZERO if canal.primeiro else (pos-Vector3(canal.pos))/maxf(dt,0.001)
  var aceleracao := Vector3.ZERO if canal.primeiro else (velocidade-Vector3(canal.vbase))/maxf(dt,0.001)
  canal.pos = pos
  canal.vbase = velocidade
  canal.primeiro = false
  var alvo := Vector3.ZERO
  var limite := 0.45 if canal.tipo == "dedo" else (0.08 if canal.tipo == "cabelo" else (0.055 if canal.tipo == "roupa" else 0.035))
  if maos_suaves and relaxar and not dormindo:
   var nome := sk.get_bone_name(i)
   if canal.tipo == "dedo" and poses_maos.size() == 2 and poses_maos[0].has(nome) and poses_maos[1].has(nome):
    # Referências do próprio jogo: abertura/flexão em conjunto, incluindo polegar.
    var a: Quaternion = poses_maos[0][nome]
    var b: Quaternion = poses_maos[1][nome]
    var pose := a.slerp(b,0.5+sin(tempo*0.35)*0.2)
    alvo += (base.inverse()*base.slerp(pose,0.85)).get_euler().limit_length(limite)
  if ligado and not dormindo and canal.tipo in ["cabelo","roupa","corpo"]:
   var inv := transform_pai.basis.orthonormalized().inverse()
   var forca: Vector3 = inv*(aceleracao.limit_length(10)*-0.006+impulso)
   alvo = Vector3(forca.z,0,-forca.x).limit_length(limite)
  if maos_suaves and repouso and not dormindo:
   if canal.tipo == "dedo":
    # Flexão local Z, sem abrir punhos/gestos fechados dos clipes originais.
    var flexao := absf(base.get_euler().z)
    var forca := clampf(1.0-flexao/0.8,0,1)
    alvo.z += (sin(tempo*1.5+i*0.7)*0.018+sin(tempo*0.7+i)*0.009)*forca
  if i == toque_osso and ligado and not dormindo: alvo.x += pressao*0.035
  var passos := maxi(1,int(ceil(dt*120)))
  var h := dt/passos
  for passo in passos:
   canal.velocidade = Vector3(canal.velocidade)+(alvo-Vector3(canal.angulo))*80*h-Vector3(canal.velocidade)*17*h
   canal.angulo = (Vector3(canal.angulo)+Vector3(canal.velocidade)*h).limit_length(limite)
  var delta := Quaternion.from_euler(canal.angulo)
  deltas[i] = delta
  ultimos[i] = (base*delta).normalized()
  sk.set_bone_pose_rotation(i,ultimos[i])
 if ligado and not dormindo: nativa.atualizar(sk,dt,impulso)
 else: nativa.reiniciar()
 impulso = impulso.move_toward(Vector3.ZERO,dt*0.6)
