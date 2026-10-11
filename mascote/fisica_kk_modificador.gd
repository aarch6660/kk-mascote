extends SkeletonModifier3D
var simulacao = preload("res://fisica_kk.gd").new()
var pausado := false
func configurar(caminho: String) -> void:
	simulacao.configurar(get_skeleton(),caminho)
func _process_modification_with_delta(delta: float) -> void:
	if pausado or delta<=0: return
	simulacao.restaurar(get_skeleton())
	simulacao.atualizar(get_skeleton(),minf(delta,0.1),Vector3.ZERO)
