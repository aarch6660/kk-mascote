extends RefCounted
# Relógio/aleatoriedade injetáveis; reações locais, sem chamada ao cérebro.
var relogio := func(): return int(Time.get_datetime_dict_from_system().hour)
var rng := RandomNumberGenerator.new()
var tempo := 0.0
var proximo_bocejo := 150.0
var bocejo := 0.0
var palpebras := 0.0
var peso_musica := 0.0
var fase_musica := 0.0

func passo(dt: float, livre: bool, tocando: bool, bpm := 100.0) -> void:
	var madrugada: bool = int(relogio.call()) < 5
	palpebras = lerpf(palpebras,0.12 if madrugada and livre else 0.0,1.0-exp(-3.0*dt))
	if not livre: bocejo = 0.0
	elif bocejo > 0: bocejo = maxf(0,bocejo-dt)
	elif madrugada:
		tempo += dt
		if tempo >= proximo_bocejo:
			bocejo = 3.8
			tempo = 0.0
			proximo_bocejo = rng.randf_range(120,240)
	else: tempo = 0.0
	var alvo := 1.0 if tocando and livre else 0.0
	peso_musica = lerpf(peso_musica,alvo,1.0-exp(-6.0*dt))
	fase_musica = fmod(fase_musica+TAU*clampf(bpm,40,240)/60.0*dt,TAU)

func abertura_bocejo() -> float:
	return 0.8*sin(PI*(3.8-bocejo)/3.8) if bocejo > 0 else 0.0

func cabeca() -> Vector3:
	return Vector3(sin(fase_musica)*0.025,0,sin(fase_musica*0.5)*0.012)*peso_musica

static func assistindo(contexto: Dictionary) -> bool:
	var janela: Dictionary = contexto.get("janela",{})
	return janela.get("categoria","")=="jogo" and not janela.get("fullscreen",false) and not contexto.get("game_mode",false)

static func fps(estado: Dictionary) -> int:
	if estado.get("oculta",false): return 10
	for chave in ["interacao","fala","gesto","movimento","mouse","musica","bocejo"]:
		if estado.get(chave,false): return 60
	if float(estado.get("energia",0)) > 0.04: return 60
	if estado.get("dormindo",false): return 10
	return 20
