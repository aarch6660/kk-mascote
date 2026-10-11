extends AudioStreamPlayer
# Respiração original, alta (bonecas/<id>/vozes/ofegar.json, ver vozes/extrair_ofegar.py).
# Nível escolhido pelo usuário: Idle calmo 「すぅ……はぁ……」, para incomodar; --nivel ofegante troca.
# Gatilhos: toque em região íntima, sem roupa (de tempos em tempos), aleatório e comando/menu.
# Os automáticos só valem com a preferência ligada; o comando explícito sempre toca.
const INTIMAS := ["Mamilo esquerdo","Mamilo direito","Seio esquerdo","Seio direito","Região genital","Nádega esquerda","Nádega direita"]
const ALEATORIO := Vector2(600,2400)   # intervalo entre crises do nada, s
const SEM_ROUPA := Vector2(60,180)     # intervalo enquanto estiver sem roupa, s
const SAIDA := 1.5                     # fade-out, s
var ligado := false
var boneca := ""
var clipes: Array = []
var dados: Dictionary = {}
var restante := 0.0
var saindo := 0.0
var proximo_aleatorio := 0.0
var proximo_sem_roupa := 0.0
var ultimo := ""
var motivo := ""
var rng := RandomNumberGenerator.new()

func _ready() -> void:
 volume_db = 0
 rng.randomize()
 proximo_aleatorio = rng.randf_range(ALEATORIO.x,ALEATORIO.y)
 proximo_sem_roupa = rng.randf_range(SEM_ROUPA.x*0.25,SEM_ROUPA.x)

func carregar() -> void:
 encerrar()
 clipes = []
 var caminho := "res://bonecas/%s/vozes/ofegar.json" % boneca
 if FileAccess.file_exists(caminho):
  var d = JSON.parse_string(FileAccess.get_file_as_string(caminho))
  if d is Dictionary: clipes = d.get("clipes",[])

func ativo() -> bool:
 return restante > 0 or saindo > 0

func disparar(segundos: float, por: String) -> void:
 if clipes.is_empty(): return
 if restante <= 0: motivo = por
 restante = maxf(restante, segundos)
 saindo = 0
 volume_db = 0

func tocar_proximo() -> void:
 var escolha: Dictionary = clipes[rng.randi_range(0,clipes.size()-1)]
 if escolha.arquivo == ultimo and clipes.size() > 1: escolha = clipes[(clipes.find(escolha)+1)%clipes.size()]
 var audio := AudioStreamOggVorbis.load_from_file(ProjectSettings.globalize_path("res://bonecas/%s/vozes/%s" % [boneca,escolha.arquivo]))
 if audio == null: return
 stream = audio
 dados = escolha
 ultimo = escolha.arquivo
 # Começa num ponto qualquer do loop: cada crise soa diferente.
 play(rng.randf_range(0, maxf(0, float(escolha.dur)-4)))

func passo(dt: float, sem_roupa: bool, toque_intimo: bool, pausado: bool) -> void:
 stream_paused = pausado
 if pausado: return
 if ligado and not clipes.is_empty():
  proximo_aleatorio -= dt
  if proximo_aleatorio <= 0:
   disparar(rng.randf_range(20,45),"aleatorio")
   proximo_aleatorio = rng.randf_range(ALEATORIO.x,ALEATORIO.y)
  if sem_roupa:
   proximo_sem_roupa -= dt
   if proximo_sem_roupa <= 0:
    disparar(rng.randf_range(15,30),"sem_roupa")
    proximo_sem_roupa = rng.randf_range(SEM_ROUPA.x,SEM_ROUPA.y)
  if toque_intimo: disparar(8,"toque")
 elif motivo != "comando" and restante > 0:
  restante = 0
  saindo = SAIDA
 if restante > 0:
  restante -= dt
  if not playing: tocar_proximo()
  if restante <= 0: saindo = SAIDA
 elif saindo > 0:
  saindo -= dt
  volume_db = linear_to_db(maxf(saindo/SAIDA,0.001))
  if saindo <= 0: encerrar()

func abertura() -> float:
 if not ativo(): return 0
 var envelope: Array = dados.get("envoltoria",[])
 var i := int(get_playback_position()/float(dados.get("passo",0.02))) if playing else -1
 var e := float(envelope[i]) if i>=0 and i<envelope.size() else 0.0
 # Boca entreaberta o tempo todo, abrindo mais a cada puxada de ar.
 return clampf(0.22+e*0.5,0,0.7)*db_to_linear(volume_db)

func encerrar() -> void:
 stop()
 stream = null
 dados = {}
 restante = 0
 saindo = 0
 motivo = ""
