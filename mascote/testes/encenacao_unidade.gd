extends SceneTree

const Encencao = preload("res://encenacao.gd")
var erros: Array[String] = []
var casos := 0

func verificar(ok: bool, nome: String) -> void:
	casos += 1
	if not ok:
		erros.append(nome)

func _initialize() -> void:
	var e = Encencao.new()
	var validos := [
		{"pixels": -180, "duracao": 0.5},
		{"pixels": 180.0, "duracao": 6},
		{"pixels": 0, "duracao": 3.25},
	]
	for dados in validos:
		verificar(e.validar_deslocamento(dados), "aceita deslocamento válido %s" % str(dados))
	var invalidos: Array = [
		null,
		[],
		{"pixels": true, "duracao": 1},
		{"pixels": 1, "duracao": false},
		{"pixels": NAN, "duracao": 1},
		{"pixels": INF, "duracao": 1},
		{"pixels": 181, "duracao": 1},
		{"pixels": -181, "duracao": 1},
		{"pixels": 0, "duracao": 0.49},
		{"pixels": 0, "duracao": 6.01},
		{"pixels": 0, "duracao": 1, "extra": 2},
		{"pixels": 0},
		{"duracao": 1},
		{"pixels": "4", "duracao": 1},
	]
	for dados in invalidos:
		verificar(not e.validar_deslocamento(dados), "rejeita entrada inválida %s" % str(dados))

	e.iniciar({"pixels": -100, "duracao": 2})
	verificar(e.offset == 0 and e.direcao == -1 and e.andando, "inicia deslocamento à esquerda")
	e.passo(0.5, -180, 180)
	verificar(e.offset < 0 and e.offset > -100, "ease move em direção à esquerda")
	e.passo(9, -180, 180)
	verificar(e.offset == -100 and e.tempo == 2 and not e.andando, "termina exatamente no alvo esquerdo")
	e.passo(1, -180, 180)
	verificar(e.offset == -100, "não deriva após terminar")

	e.iniciar({"pixels": 120, "duracao": 2})
	e.passo(0.5, -180, 180)
	verificar(e.offset > -100 and e.direcao == 1, "inicia deslocamento à direita a partir do offset atual")
	var antes_reversao: float = e.offset
	e.iniciar({"pixels": -120, "duracao": 2})
	verificar(e.offset == antes_reversao and e.direcao == -1 and e.andando, "nova cena preserva offset e inverte direção")
	e.passo(0.5, -180, 180)
	verificar(e.offset < antes_reversao, "reversão move na direção nova")

	e.limpar()
	e.iniciar({"pixels": 180, "duracao": 2})
	for _i in 10:
		e.passo(0.2, -8, 12)
		verificar(e.offset >= -8 and e.offset <= 12, "palco estreito limita offset")
	verificar(e.offset == 12 and not e.andando, "alvo é limitado à plataforma estreita")
	e.passo(0.2, -4, 8)
	verificar(e.offset == 8, "limite dinâmico reduz offset após a cena")
	e.limpar()
	e.iniciar({"pixels": 180, "duracao": 2})
	e.passo(0.8, -180, 180)
	var offset_antes_limite: float = e.offset
	e.passo(0.2, -180, offset_antes_limite - 2)
	verificar(e.offset <= offset_antes_limite - 2 and e.direcao == -1, "reduzir limite durante caminhada reverte direção")

	e.limpar()
	e.iniciar({"pixels": -100, "duracao": 1})
	e.passo(0.25, 5, 5)
	verificar(e.offset == 5 and not e.andando, "bounds sem espaço prendem no único ponto permitido")
	e.passo(0.25, 10, -10)
	verificar(e.offset == 0 and not e.andando, "bounds invertidos colapsam sem erro")
	e.passo(0.5, -180, 180)
	verificar(e.offset == -100 and not e.andando, "trajetória termina após os bounds reabrirem")

	e.limpar()
	e.iniciar({"pixels": 100, "duracao": 2})
	e.passo(0.5, -180, 180)
	var offset_pausado: float = e.offset
	var tempo_pausado: float = e.tempo
	# Pausa do consumidor: sem chamar passo, estado e interpolação ficam congelados.
	verificar(e.offset == offset_pausado and e.tempo == tempo_pausado and e.andando, "pausa simulada sem avançar passo")
	e.passo(0.5, -180, 180)
	e.enquadramento = "corpo"
	e.limpar()
	verificar(e.offset == 0 and e.tempo == 0 and not e.andando and e.enquadramento == "normal", "limpar restaura estado transitório")

	var resultado := {"passou": erros.is_empty(), "casos": casos, "erros": erros}
	print(JSON.stringify(resultado))
	quit(0 if erros.is_empty() else 1)
