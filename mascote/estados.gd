extends RefCounted
## Tempos separados da renderização para permitir prova headless.
var estado := "parada"
var tempo := 0.0
var prazo := 7.0
var direcao := 1.0
var alternar := false
var sono_manual := false
var rng := RandomNumberGenerator.new()
var gestos := ["stand_joy_00", "stand_joy_04", "stand_oth_00", "alongar", "conversa_03"]
# Poses de espera originais do jogo (f_tachi_*); idle_em_pe fica só como pose neutra de referência.
var idles := ["parada_relaxada", "parada_maos_atras", "parada_timida", "parada_balanco", "parada_espera_h"]
var clipe := "parada_relaxada"
var ultimo_idle := ""
var gestos_ocasionais := ["gesto_ajeitar_cabelo", "gesto_mao_boca", "gesto_olhar_longe", "gesto_maos_juntas"]
var ultimo_ocasional := ""
var tempo_ocasional := 0.0
var prazo_ocasional := 0.0

func sortear_ocasional() -> String:
	var opcoes := gestos_ocasionais.filter(func(n): return n != ultimo_ocasional)
	ultimo_ocasional = opcoes[rng.randi_range(0,opcoes.size()-1)]
	return ultimo_ocasional

func passo_ocasional(dt: float, disponivel: bool) -> bool:
	if not disponivel or estado != "parada": return false
	if prazo_ocasional <= 0: prazo_ocasional = rng.randf_range(40,120)
	tempo_ocasional += dt
	if tempo_ocasional < prazo_ocasional: return false
	tempo_ocasional = 0
	prazo_ocasional = rng.randf_range(40,120)
	mudar("gesto_ocasional",120)
	clipe = sortear_ocasional()
	return true

func sortear_idle() -> String:
	var opcoes := idles.filter(func(n): return n != ultimo_idle)
	ultimo_idle = opcoes[rng.randi_range(0, opcoes.size()-1)]
	return ultimo_idle

func mudar(novo: String, duracao := 8.0) -> void:
	var continua := novo == "parada" and estado == "parada" and clipe in idles
	estado = novo
	tempo = 0
	prazo = duracao
	match estado:
		"parada": if not continua: clipe = sortear_idle()
		"andando": clipe = "caminhar"
		"gesto": clipe = gestos[rng.randi_range(0, gestos.size()-1)]
		"sentada": clipe = "sentada_idle"
		"cochilo": clipe = "sono_sentada"
		"dormindo": clipe = "dormir_00"
		"reacao":
			alternar = not alternar
			clipe = "reacao_defesa" if alternar else "stand_joy_00"
		"caindo", "arrastando", "pulando": clipe = "idle_postura"

func passo(dt: float, ocioso: float, apoiada: bool, janela: bool, perto: bool, imovel := false) -> bool:
	tempo += dt
	var antigo := estado
	if estado in ["arrastando", "pulando", "caindo"]: return false
	if estado in ["assistindo", "cumprimento"]: return false
	if estado in ["cochilo", "dormindo"]:
		if perto and not sono_manual: mudar("parada")
	elif ocioso > 180 or sono_manual:
		mudar("cochilo" if janela else "dormindo", 60)
	elif estado == "gesto_ocasional": return false
	elif apoiada and tempo >= prazo:
		match estado:
			"parada":
				if imovel: return false
				direcao = -1 if rng.randf() < 0.5 else 1
				mudar("gesto" if imovel else "andando", rng.randf_range(3, 7))
			"andando": mudar("gesto", 5)
			"gesto": mudar("sentada" if janela and not imovel else "parada", 18)
			_: mudar("parada", rng.randf_range(5, 12))
	return antigo != estado
