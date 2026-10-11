extends RefCounted
## Física em pixels lógicos. O apoio guarda o endereço IPC, não o foco.
var pos := Vector2(850, 600)
var vel := Vector2.ZERO
var apoio := ""
var pisos: Array = []
var largura := 1920.0
var base := 1080.0
var altura_minima := 180.0
var arrastando := false
var fixa := false
const GRAVIDADE := 980.0

func atualizar(novos: Array, w: float, b: float) -> void:
	var anterior := piso(apoio)
	pisos = novos.duplicate(true)
	largura = w
	base = b
	if arrastando or fixa: return
	if apoio == "tela":
		pos.y = base
	elif not apoio.is_empty():
		var atual := piso(apoio)
		if atual.is_empty():
			apoio = ""
		else:
			if not anterior.is_empty():
				pos.x += float(atual.x) - float(anterior.x)
			pos.y = float(atual.y)
			if not contem(atual, pos.x) or pos.y < altura_minima:
				apoio = ""

func piso(id: String) -> Dictionary:
	for p in pisos:
		if str(p.address) == id: return p
	return {}

func contem(p: Dictionary, x: float) -> bool:
	return x >= float(p.x) and x <= float(p.x) + float(p.width)

func passo(dt: float, andar := 0.0) -> void:
	if arrastando or fixa: return
	vel.x = andar if not apoio.is_empty() else vel.x
	pos.x = clampf(pos.x + vel.x * dt, 20, largura - 20)
	if not apoio.is_empty():
		if apoio != "tela" and not contem(piso(apoio), pos.x): apoio = ""
		else: return
	var antes := pos.y
	vel.y += GRAVIDADE * dt
	pos.y += vel.y * dt
	if vel.y < 0: return
	var melhor := base
	var id := "tela"
	for p in pisos:
		var y := float(p.y)
		if y >= altura_minima and contem(p, pos.x) and antes <= y + 0.5 and pos.y >= y and y < melhor:
			melhor = y
			id = str(p.address)
	if antes <= melhor + 0.5 and pos.y >= melhor or pos.y >= base:
		pos.y = melhor
		vel = Vector2.ZERO
		apoio = id

func soltar() -> void:
	fixa = false
	arrastando = false
	apoio = ""
	vel = Vector2.ZERO

func pular(alvo: Vector2) -> bool:
	if apoio.is_empty(): return false
	var dy := alvo.y - pos.y
	if absf(alvo.x - pos.x) > 270 or dy < -120: return false
	var vy := -520.0
	var disc := vy * vy + 2 * GRAVIDADE * dy
	if disc <= 0: return false
	var tempo := (-vy + sqrt(disc)) / GRAVIDADE
	var vx := (alvo.x - pos.x) / tempo
	if absf(vx) > 290: return false
	vel = Vector2(vx, vy)
	apoio = ""
	return true
