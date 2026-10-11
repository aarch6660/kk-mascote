extends RefCounted
## Interpolação transitória do deslocamento de uma cena de fala.
## Bounds são offsets relativos à origem visual da fala, recalculados pelo chamador.
const MIN_PIXELS := -180.0
const MAX_PIXELS := 180.0
const MIN_DURACAO := 0.5
const MAX_DURACAO := 6.0
const EPSILON := 0.0001

var offset := 0.0
var direcao := 1.0
var andando := false
var tempo := 0.0
var duracao := 0.0
var enquadramento := "normal"

var _inicio := 0.0
var _alvo := 0.0
var _ativo := false

func validar_deslocamento(dados: Variant) -> bool:
	if not dados is Dictionary or dados.size() != 2:
		return false
	if not dados.has("pixels") or not dados.has("duracao"):
		return false
	for chave in dados:
		if chave not in ["pixels", "duracao"]:
			return false
	for chave in ["pixels", "duracao"]:
		var valor = dados[chave]
		if typeof(valor) not in [TYPE_INT, TYPE_FLOAT]:
			return false
		if not is_finite(float(valor)):
			return false
	var pixels := float(dados.pixels)
	var segundos := float(dados.duracao)
	return pixels >= MIN_PIXELS and pixels <= MAX_PIXELS and segundos >= MIN_DURACAO and segundos <= MAX_DURACAO

func iniciar(dados: Dictionary) -> void:
	if not validar_deslocamento(dados):
		limpar()
		return
	_inicio = offset
	_alvo = float(dados.pixels)
	duracao = float(dados.duracao)
	tempo = 0.0
	_ativo = absf(_alvo - offset) > EPSILON
	andando = _ativo
	if _ativo:
		direcao = 1.0 if _alvo > offset else -1.0

func passo(dt: float, minimo: float, maximo: float) -> void:
	if not is_finite(minimo) or not is_finite(maximo):
		andando = false
		return
	# Bounds invertidos representam um palco sem espaço: colapsa no ponto médio.
	if minimo > maximo:
		var meio := (minimo + maximo) * 0.5
		minimo = meio
		maximo = meio
	if not _ativo:
		offset = clampf(offset, minimo, maximo)
		andando = false
		return
	if not is_finite(dt) or dt <= 0.0:
		return
	var alvo_limitado := clampf(_alvo, minimo, maximo)
	if alvo_limitado > offset + EPSILON:
		direcao = 1.0
	elif alvo_limitado < offset - EPSILON:
		direcao = -1.0
	tempo = minf(duracao, tempo + dt)
	var fase := clampf(tempo / duracao, 0.0, 1.0)
	var curva := smoothstep(0.0, 1.0, fase)
	var interpolado := lerpf(_inicio, alvo_limitado, curva)
	offset = clampf(interpolado, minimo, maximo)
	if tempo >= duracao:
		offset = alvo_limitado
		_ativo = false
		andando = false
	else:
		# Continua ativo se os bounds mudarem novamente antes do fim da cena.
		andando = absf(alvo_limitado - offset) > EPSILON

func limpar() -> void:
	offset = 0.0
	direcao = 1.0
	andando = false
	tempo = 0.0
	duracao = 0.0
	enquadramento = "normal"
	_inicio = 0.0
	_alvo = 0.0
	_ativo = false
