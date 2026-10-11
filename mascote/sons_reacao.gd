extends AudioStreamPlayer
# Reações curtas: vozes originais do jogo da boneca atual (bonecas/<id>/vozes, ver vozes/extrair.py).
# Boneca sem vozes extraídas cai nas interjeições pt-BR sintetizadas antigas (res://sons).
var catalogo: Dictionary = {}
var boneca := ""
var vozes: Dictionary = {}
var ultimo_clipe := ""
var rng := RandomNumberGenerator.new()
# Categoria pedida → alternativas, para personalidades com poucas falas de algum tipo.
const ALTERNATIVAS := {"pensando":["pensando","suspiro","resmungo"],"resmungo":["resmungo","suspiro"],"suspiro":["suspiro","resmungo"],"choque":["choque","surpresa"],"surpresa":["surpresa","choque"],"duvida":["duvida","pensando"],"alegria":["alegria"],"concordar":["concordar"]}
var dados: Dictionary = {}
var ligado := true
var relogio := 0.0
var ultimo := -100.0
var ultimo_nome := ""
var teclas := AudioStreamPlayer.new()

func _ready() -> void:
 volume_db = -18
 if FileAccess.file_exists("res://sons/catalogo.json"):
  catalogo = JSON.parse_string(FileAccess.get_file_as_string("res://sons/catalogo.json"))
 teclas.volume_db = -32
 add_child(teclas)

func carregar_vozes() -> void:
 vozes = {}
 var caminho := "res://bonecas/%s/vozes/vozes.json" % boneca
 if FileAccess.file_exists(caminho):
  var dados = JSON.parse_string(FileAccess.get_file_as_string(caminho))
  if dados is Dictionary: vozes = dados

func voz_do_jogo(nome: String) -> bool:
 for categoria in ALTERNATIVAS.get(nome,[nome]):
  var opcoes: Array = vozes.get(categoria,[])
  if opcoes.is_empty(): continue
  var escolha: Dictionary = opcoes[rng.randi_range(0,opcoes.size()-1)]
  if escolha.arquivo == ultimo_clipe and opcoes.size()>1: escolha = opcoes[(opcoes.find(escolha)+1)%opcoes.size()]
  var audio := AudioStreamOggVorbis.load_from_file(ProjectSettings.globalize_path("res://bonecas/%s/vozes/%s" % [boneca,escolha.arquivo]))
  if audio == null: return false
  stream = audio
  dados = escolha
  ultimo_clipe = escolha.arquivo
  volume_db = -8
  return true
 return false

func reagir(nome: String) -> bool:
 if nome=="nenhum" or not ligado or playing or relogio-ultimo<4: return false
 if not vozes.is_empty():
  if nome==ultimo_nome and relogio-ultimo<12: return false
  if not voz_do_jogo(nome): return false
  ultimo = relogio
  ultimo_nome = nome
  play()
  return true
 if not catalogo.has(nome): return false
 # Não repetir a mesma interjeição em mensagens consecutivas próximas.
 if nome==ultimo_nome and relogio-ultimo<20: return false
 dados = catalogo[nome]
 volume_db = -18
 stream = load("res://sons/"+nome+".wav")
 if stream==null: return false
 ultimo = relogio
 ultimo_nome = nome
 play()
 return true

func passo(dt: float, digitando: bool, pausada: bool) -> void:
 stream_paused = pausada
 teclas.stream_paused = pausada
 if pausada: return
 relogio += dt
 if ligado and digitando and not teclas.playing:
  teclas.stream = load("res://sons/digitacao.wav")
  if teclas.stream: teclas.play()
 if not ligado or not digitando: teclas.stop()
 if not ligado: encerrar()

func abertura() -> float:
 if not playing or stream_paused or dados.is_empty(): return 0
 var envelope: Array = dados.get("envoltoria",[])
 var i := int(get_playback_position()/float(dados.get("passo",0.02)))
 return clampf(float(envelope[i])*0.6,0,0.65) if i>=0 and i<envelope.size() else 0.0

func encerrar() -> void:
 stop()
 teclas.stop()
 stream = null
 teclas.stream = null
 dados = {}
