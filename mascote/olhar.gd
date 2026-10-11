extends SkeletonModifier3D
# Ângulos em relação ao rosto: x = direita, y = baixo na tela.
var alvo := Vector2.ZERO
var expressivo := Vector3.ZERO
var perto := false
var cabeca := -1
var olhos: Array[int] = []
var suavizado := Vector2.ZERO
var ultima_cabeca := Quaternion.IDENTITY
var ultimo_delta := Quaternion.IDENTITY
var base_olhos: Dictionary = {}
var ultimas_posicoes: Dictionary = {}
var deslocamentos_olhos: Dictionary = {}
var eixos_olhos: Dictionary = {}
var suavizado_olhos := Vector2.ZERO

func _process_modification() -> void:
 atualizar(clampf(get_process_delta_time(),0.001,0.1))

func atualizar(dt: float) -> void:
 var sk := get_skeleton()
 if cabeca < 0:
  cabeca = sk.find_bone("cf_j_head")
  for nome in ["cf_J_hitomi_tx_L", "cf_J_hitomi_tx_R"]:
   var i := sk.find_bone(nome)
   if i >= 0:
    olhos.append(i)
    base_olhos[i] = sk.get_bone_pose_rotation(i)
    if cabeca >= 0:
     var pai := sk.get_bone_parent(i)
     eixos_olhos[i] = sk.get_bone_global_rest(pai).basis.orthonormalized().inverse() * sk.get_bone_global_rest(cabeca).basis.orthonormalized()
 var destino := alvo.clamp(Vector2(-0.65,-0.34),Vector2(0.65,0.34)) if perto else Vector2.ZERO
 suavizado = suavizado.lerp(destino,1.0-exp(-5.0*dt))
 suavizado_olhos = suavizado_olhos.lerp(destino,1.0-exp(-14.0*dt))
 var angulo_cabeca := Vector2(clampf(suavizado.x*0.7,-0.42,0.42),clampf(suavizado.y*0.65,-0.20,0.20))
 if cabeca >= 0:
  var q := Quaternion.from_euler(Vector3(angulo_cabeca.y,angulo_cabeca.x,0)+expressivo.clamp(Vector3(-0.09,-0.10,-0.07),Vector3(0.09,0.10,0.07)))
  var base := sk.get_bone_pose_rotation(cabeca)
  # Preserva pistas do clipe; remove só a correção anterior se ela ainda estiver aplicada.
  if base.is_equal_approx(ultima_cabeca): base = base * ultimo_delta.inverse()
  ultima_cabeca = base * q
  ultimo_delta = q
  sk.set_bone_pose_rotation(cabeca,ultima_cabeca)
 var residual := suavizado_olhos-angulo_cabeca
 var horizontal := clampf(residual.x/0.18,-1,1)
 var vertical := clampf(residual.y/0.12,-1,1)
 # A íris do KK é uma camada curva: girá-la faz bordas atravessarem a esclera.
 # Desliza em relação ao rosto, com folga frontal proporcional ao deslocamento.
 var deslocamento := Vector3(horizontal*0.0025,-vertical*0.0015,0.0012*minf(1.0,absf(horizontal)+absf(vertical)))
 for i in olhos:
  var eixos: Basis = eixos_olhos.get(i,Basis.IDENTITY)
  var delta: Vector3 = eixos*deslocamento
  var base := sk.get_bone_pose_position(i)
  if ultimas_posicoes.has(i) and base.is_equal_approx(ultimas_posicoes[i]): base -= deslocamentos_olhos[i]
  ultimas_posicoes[i] = base+delta
  deslocamentos_olhos[i] = delta
  sk.set_bone_pose_position(i,ultimas_posicoes[i])
