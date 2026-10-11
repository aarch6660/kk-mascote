extends RefCounted
# Animação visual ligada aos caracteres; sem áudio ou reconhecimento de fala.
var texto := ""
var autor := ""
var emocao := "Neutra"
var id := ""
var indice := 0
var tempo_letra := 0.0
var pausa_final := 0.0
var ativo := false
var vogal := "a"
var abertura := 0.0
var paginas: Array[int] = [0]
func iniciar(dados: Dictionary) -> bool:
 var valor = dados.get("texto","")
 if not valor is String or valor.strip_edges().is_empty() or valor.length()>1200: return false
 texto = valor.strip_edges()
 autor = str(dados.get("autor","Agente")).left(48)
 emocao = str(dados.get("emocao","Neutra"))
 if not preload("res://expressoes.gd").PERFIS.has(emocao): emocao = "Neutra"
 id = str(dados.get("id","local"))
 indice = 0
 tempo_letra = 0
 pausa_final = 0
 abertura = 0
 ativo = true
 paginas = [0]
 var inicio := 0
 while texto.length()-inicio > 210:
  var corte := inicio+210
  while corte>inicio+100 and texto[corte] != " " and texto[corte] != "\n": corte -= 1
  if corte<=inicio+100: corte = inicio+210
  paginas.append(corte)
  inicio = corte
 return true
func letra_base(letra: String) -> String:
 return letra.to_lower().replace("á","a").replace("à","a").replace("â","a").replace("ã","a").replace("é","e").replace("ê","e").replace("í","i").replace("ó","o").replace("ô","o").replace("õ","o").replace("ú","u").replace("ü","u")
func duracao(letra: String) -> float:
 if letra in [".","!","?",";",":","\n"]: return 0.24
 if letra == ",": return 0.14
 if letra in [" ","\t"]: return 0.055
 return 0.055 if letra_base(letra) in ["a","e","i","o","u"] else 0.03
func passo(dt: float) -> void:
 abertura = 0
 if not ativo: return
 tempo_letra += dt
 while indice < texto.length() and tempo_letra >= duracao(texto[indice]):
  tempo_letra -= duracao(texto[indice])
  indice += 1
 if indice >= texto.length():
  pausa_final += dt
  if pausa_final >= 3.0: ativo = false
  return
 var letra := letra_base(texto[indice])
 if letra in ["a","e","i","o","u"]:
  vogal = letra
  abertura = 0.65+0.20*sin(clampf(tempo_letra/duracao(texto[indice]),0,1)*PI)
 elif "abcdefghijklmnopqrstuvwxyzç0123456789".contains(letra) and letra not in ["m","b","p"]: abertura = 0.22
func pagina_visivel() -> String:
 var inicio := 0
 for pagina in paginas:
  if pagina<=indice: inicio = pagina
 return texto.substr(inicio,maxi(0,mini(texto.length(),indice+1)-inicio))
func cancelar() -> void:
 ativo = false
 abertura = 0

func sincronizar_audio(tempo: float, dados: Dictionary, terminou: bool, dt: float) -> void:
 abertura = 0
 if not ativo: return
 if terminou:
  indice = texto.length()
  pausa_final += dt
  if pausa_final >= 3.0: ativo = false
  return
 var palavras: Array = dados.get("palavras",[])
 for palavra in palavras:
  var inicio := float(palavra.inicio)
  var fim := float(palavra.fim)
  var de := int(palavra.de)
  var ate := int(palavra.ate)
  if tempo >= fim:
   indice = clampi(ate,0,texto.length())
   continue
  if tempo < inicio: return
  var fracao := clampf((tempo-inicio)/maxf(0.001,fim-inicio),0,0.999)
  indice = clampi(de+int(fracao*(ate-de)),0,texto.length()-1)
  var letra := letra_base(texto[indice])
  # Formas vocálicas são aproximadas dentro da palavra; tempos vêm da síntese.
  if letra in ["a","e","i","o","u"]: vogal = letra
  var envelope: Array = dados.get("envoltoria",[])
  var amostra := int(tempo/float(dados.get("passo",0.02)))
  var energia := float(envelope[amostra]) if amostra>=0 and amostra<envelope.size() else 0.0
  if letra not in ["m","b","p"]: abertura = clampf(energia,0,1)*0.85
  return
