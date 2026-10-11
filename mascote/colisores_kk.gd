extends RefCounted
# Projeção geométrica usada pelos DynamicBoneCollider cotidianos: esfera/cápsula.
# Raio do colisor e da partícula já chegam convertidos para espaço de mundo.
static func esfera(pos: Vector3, centro: Vector3, raio: float, dentro := false) -> Vector3:
	var delta := pos-centro
	var distancia := delta.length()
	var limite := maxf(0,raio)
	if (dentro and distancia <= limite) or (not dentro and distancia >= limite): return pos
	var direcao := delta/distancia if distancia > 0.00000001 else Vector3.UP
	return centro+direcao*limite

static func capsula(pos: Vector3, a: Vector3, b: Vector3, raio: float, dentro := false) -> Vector3:
	var eixo := b-a
	var u := clampf((pos-a).dot(eixo)/eixo.length_squared(),0,1) if eixo.length_squared()>0.0000000001 else 0.0
	var centro := a+eixo*u
	if not dentro and pos.distance_squared_to(centro)<0.0000000001 and eixo.length_squared()>0.0000000001:
		var normal := eixo.normalized().cross(Vector3.RIGHT)
		if normal.length_squared()<0.0000000001: normal = eixo.normalized().cross(Vector3.UP)
		return centro+normal.normalized()*maxf(0,raio)
	return esfera(pos,centro,raio,dentro)
