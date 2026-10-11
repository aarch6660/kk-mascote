extends SkeletonModifier3D
# Variação pequena dos dedos sobre a pose nativa de celular, sem acumular rotação.
var ligado := false
var tempo := 0.0
var mistura := 0.0
var ultimos: Dictionary = {}
var deltas: Dictionary = {}
func _process_modification() -> void:
 var dt := minf(get_process_delta_time(),0.1)
 tempo += dt
 mistura = move_toward(mistura,1.0 if ligado else 0.0,dt*5)
 var sk := get_skeleton()
 for nome in ["cf_j_thumb02_R","cf_j_index02_R","cf_j_thumb02_L"]:
  var i := sk.find_bone(nome)
  if i<0: continue
  var base := sk.get_bone_pose_rotation(i)
  if ultimos.has(i) and base.is_equal_approx(ultimos[i]): base = base*deltas[i].inverse()
  var peso := maxf(0,sin(tempo*11+float(i)*0.6))*mistura
  var delta := Quaternion(Vector3.RIGHT,peso*0.13)
  ultimos[i] = (base*delta).normalized()
  deltas[i] = delta
  sk.set_bone_pose_rotation(i,ultimos[i])
