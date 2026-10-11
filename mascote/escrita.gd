extends RefCounted
# Ritmo de escrita no celular: digita, para para pensar, apaga e reescreve.
# Gera uma linha do tempo determinística (semente) e expõe o índice visível.
var texto := ""
var eventos: Array = []   # [{t, n, estado}] — a partir de t, n caracteres visíveis e estado
var duracao := 0.0
var tempo := 0.0
var indice := 0
var maximo := 0           # maior índice já escrito (atuação não reage a texto apagado)
var estado := ""
var ativo := false
var rng := RandomNumberGenerator.new()
const PAUSA_FINAL := 1.4  # cobre o gesto original de "enviar" (celular_enviar)

func iniciar(valor: String, semente := 0) -> void:
	texto = valor
	rng.seed = semente if semente != 0 else hash(valor)
	eventos = []
	var t := 0.0
	var n := 0
	var desde_pausa := 0
	var proxima_pausa := rng.randi_range(55, 120)
	var apagamentos := 0 if texto.length() < 30 else (1 if texto.length() < 220 else 2)
	var pontos_apagar := []
	for k in apagamentos: pontos_apagar.append(rng.randi_range(int(texto.length()*0.2), int(texto.length()*0.85)))
	eventos.append({"t":0.0,"n":0,"estado":"digitando"})
	while n < texto.length():
		var c := texto[n]
		t += _tempo_letra(c)
		n += 1
		desde_pausa += 1
		eventos.append({"t":t,"n":n,"estado":"digitando"})
		var fim_palavra := c == " " or n == texto.length()
		if not pontos_apagar.is_empty() and n >= pontos_apagar[0] and fim_palavra and n < texto.length():
			pontos_apagar.pop_front()
			# Hesita, apaga a última palavra e a reescreve.
			t += rng.randf_range(0.35, 0.7)
			var volta := mini(rng.randi_range(4, 9), n)
			for k in volta:
				t += 0.07
				eventos.append({"t":t,"n":n-k-1,"estado":"apagando"})
			t += rng.randf_range(0.3, 0.6)
			var alvo := n
			n -= volta
			eventos.append({"t":t,"n":n,"estado":"digitando"})
			while n < alvo:
				t += _tempo_letra(texto[n])
				n += 1
				eventos.append({"t":t,"n":n,"estado":"digitando"})
		elif desde_pausa >= proxima_pausa and fim_palavra and n < texto.length():
			desde_pausa = 0
			proxima_pausa = rng.randi_range(60, 140)
			eventos.append({"t":t+0.05,"n":n,"estado":"pensando"})
			t += rng.randf_range(1.0, 2.0)
			eventos.append({"t":t,"n":n,"estado":"digitando"})
	# Textos longos aceleram para não passar de ~35 s.
	var limite := clampf(texto.length()/11.0, 3.0, 35.0)
	if t > limite:
		var escala := limite/t
		for e in eventos: e.t *= escala
		t = limite
	duracao = t + PAUSA_FINAL
	eventos.append({"t":t,"n":texto.length(),"estado":"enviando"})
	tempo = 0
	indice = 0
	maximo = 0
	estado = "digitando"
	ativo = true

func _tempo_letra(c: String) -> float:
	if c in [".","!","?"]: return rng.randf_range(0.30, 0.55)
	if c in [",",";",":"]: return rng.randf_range(0.14, 0.24)
	if c == "\n": return 0.4
	if c == " ": return rng.randf_range(0.05, 0.10)
	return rng.randf_range(0.055, 0.11)

func passo(dt: float) -> void:
	if not ativo: return
	tempo += dt
	var i := 0
	# Busca linear a partir do fim é suficiente para algumas centenas de eventos por mensagem.
	for k in range(eventos.size()-1, -1, -1):
		if eventos[k].t <= tempo:
			i = k
			break
	indice = int(eventos[i].n)
	estado = str(eventos[i].estado)
	maximo = maxi(maximo, indice)
	if tempo >= duracao:
		indice = texto.length()
		maximo = indice
		ativo = false

func visivel() -> String:
	return texto.left(indice)

func batendo() -> bool:
	return ativo and estado in ["digitando","apagando"]
