extends RefCounted
# Atuação visual local. Não simula mensagens de um agente nem chama modelos.
var cenas: Array = []
var proxima := 0
var face_base: Dictionary = {}
var face_atual: Dictionary = {}
var emocao := ""
var tempo := 0.0
var tempo_movimento := 0.0
var movimento := ""
var olhar_alvo := Vector2.ZERO
var olhar_tempo := 0.0
var reacao_tempo := 0.0
var reacao_emocao := ""
var ultima_regiao := ""
var automatico := true
var ultimo_indice := -1
var ultimo_acento := -10.0
var contato := false
var toque_tempo := 0.0
var pede_piscada := false
const MOVIMENTOS := ["concordar","negar","inclinar","nenhum"]

func validar(dados, tamanho: int) -> bool:
 if not dados is Array or dados.size()>16: return false
 var anterior := -1
 for cena in dados:
  if not cena is Dictionary: return false
  for chave in cena:
   if chave not in ["indice","emocao","face","gesto","movimento","olhar","efeito","som","deslocamento","enquadramento"]: return false
  var indice = cena.get("indice",-1)
  if not (indice is int or indice is float) or not is_finite(float(indice)) or float(indice)!=floor(float(indice)): return false
  if int(indice) <= anterior or int(indice)<0 or int(indice)>=tamanho: return false
  anterior = int(indice)
  if cena.has("emocao") and not preload("res://expressoes.gd").PERFIS.has(cena.emocao): return false
  if not preload("res://expressoes.gd").new().validar_ajustes(cena.get("face",{})): return false
  if cena.has("gesto") and not JSON.parse_string(FileAccess.get_file_as_string("res://gestos.json")).clipes.has(cena.gesto): return false
  if cena.has("movimento") and cena.movimento not in MOVIMENTOS: return false
  if cena.has("enquadramento") and cena.enquadramento not in ["normal","corpo"]: return false
  if cena.has("deslocamento") and not preload("res://encenacao.gd").new().validar_deslocamento(cena.deslocamento): return false
  if cena.has("olhar"):
   if not cena.olhar is Array or cena.olhar.size()!=2: return false
   for valor in cena.olhar:
    if not (valor is float or valor is int) or not is_finite(float(valor)) or absf(float(valor))>1: return false
  for chave in ["efeito","som"]:
   var catalogo: Dictionary = preload("res://mensagens.gd").CATALOGO
   if cena.has(chave) and cena[chave] not in catalogo["efeitos" if chave=="efeito" else "sons"]: return false
 return true

func iniciar(dados: Array, face: Dictionary, expressao: String, natural: bool) -> void:
 limpar()
 cenas = dados.duplicate(true)
 face_base = face.duplicate(true)
 face_atual = face.duplicate(true)
 emocao = expressao
 automatico = natural

func limpar() -> void:
 cenas = []
 proxima = 0
 face_base = {}
 face_atual = {}
 emocao = ""
 movimento = ""
 tempo_movimento = 0
 olhar_tempo = 0
 ultimo_indice = -1
 ultimo_acento = -10
 pede_piscada = false

func contato_inicio(regiao: String, carinho: bool) -> void:
 contato = true
 toque_tempo = 0
 ultima_regiao = regiao
 reacao_tempo = 1.8
 # Reações comuns a cabeça/mãos/ombros; outras regiões não recebem atuação específica.
 reacao_emocao = "Felicidade" if carinho and (regiao=="Cabeça" or regiao.begins_with("Mão")) else "Surpresa"

func contato_fim() -> void:
 contato = false
 reacao_tempo = 1.6

func passo(dt: float, indice: int, texto: String, falando: bool) -> Array:
 tempo += dt
 tempo_movimento = maxf(0,tempo_movimento-dt)
 olhar_tempo = maxf(0,olhar_tempo-dt)
 reacao_tempo = maxf(0,reacao_tempo-dt)
 if contato:
  toque_tempo += dt
  reacao_tempo = 1.8
  if ultima_regiao=="Cabeça" and reacao_emocao=="Felicidade" and toque_tempo>1.2: reacao_emocao = "Riso"
 var aplicadas: Array = []
 if not falando: return aplicadas
 while proxima<cenas.size() and int(cenas[proxima].indice)<=indice:
  var cena: Dictionary = cenas[proxima]
  proxima += 1
  if cena.has("emocao"): emocao = cena.emocao
  if cena.has("face"): face_atual = cena.face.duplicate(true)
  if cena.has("movimento"):
   movimento = cena.movimento
   tempo_movimento = 1.2
   ultimo_acento = tempo
  if cena.has("olhar"):
   olhar_alvo = Vector2(float(cena.olhar[0]),float(cena.olhar[1]))*Vector2(0.45,0.20)
   olhar_tempo = 1.5
  aplicadas.append(cena)
 # Acentos discretos na cabeça em limites de frase, sem trocar o gesto corporal.
 if automatico and indice>ultimo_indice and indice>0:
  var de := maxi(0,ultimo_indice+1)
  var trecho := texto.substr(de,maxi(0,mini(indice,texto.length())-de))
  if tempo-ultimo_acento>2.4 and (trecho.contains(".") or trecho.contains("!") or trecho.contains("?")):
   movimento = "inclinar" if trecho.contains("?") else "concordar"
   tempo_movimento = 1.2
   ultimo_acento = tempo
   pede_piscada = true
 ultimo_indice = indice
 return aplicadas

func cabeca() -> Vector3:
 if tempo_movimento<=0 or movimento=="nenhum": return Vector3.ZERO
 var fase := clampf(1.0-tempo_movimento/1.2,0,1)
 var pulso := sin(fase*TAU)*pow(sin(fase*PI),2)
 if movimento=="concordar": return Vector3(pulso*0.07,0,0)
 if movimento=="negar": return Vector3(0,pulso*0.09,0)
 if movimento=="inclinar": return Vector3(0,0,sin(fase*PI)*0.06)
 return Vector3.ZERO

func intensidade_reacao() -> float:
 return smoothstep(0,0.6,reacao_tempo)
