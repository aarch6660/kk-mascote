extends RefCounted
# Fases visuais publicadas pelo agente. Não lê a conversa nem interpreta o pedido.
signal fase_mudou
static var CATALOGO: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://mensagens.json"))
var ativo := false
var fase := ""
var tom := "neutro"
var intensidade := 0.65
var autor := ""
var id := ""
var tempo := 0.0
var restante := 0.0
var fila: Array = []
var resposta: Dictionary = {}
var variacao := 0
var emocao_anterior := "Neutra"
var som_emitido := false
# Modo escrita: a resposta é escrita no celular depois; aqui só lê, reage e pensa.
var escrever := false

func validar(dados) -> bool:
 if not dados is Dictionary: return false
 for chave in dados:
  if chave not in ["tom","intensidade","leitura","digitacao","duracao"]: return false
  if chave == "tom":
   if not dados[chave] is String or not CATALOGO.tons.has(dados[chave]): return false
  else:
   var v = dados[chave]
   if not (v is int or v is float) or not is_finite(float(v)): return false
   if chave=="intensidade" and (v<0 or v>1): return false
   if chave in ["leitura","digitacao"] and (v<0 or v>5): return false
   if chave=="duracao" and (v<3 or v>60): return false
 return true

func iniciar(dados: Dictionary, dono: String, identificador: String, anterior: String, emitir := true) -> void:
 cancelar()
 ativo = true
 autor = dono
 id = identificador
 tom = str(dados.get("tom","neutro"))
 intensidade = float(dados.get("intensidade",0.65))
 emocao_anterior = anterior
 variacao += 1
 var limite := float(dados.get("duracao",30))
 var leitura := minf(float(dados.get("leitura",1.5))+float(variacao%3)*0.12,limite-1.2)
 fila = [{"fase":"lendo","duracao":leitura},{"fase":"reagindo","duracao":1.1},{"fase":"pensando","duracao":maxf(0.1,limite-leitura-1.1)}]
 if emitir: avancar()

func preparar(dados: Dictionary, anterior: String) -> void:
 var ajustes: Dictionary = dados.get("preparacao",{})
 # Leitura iniciada pelo chat ("Usuário") aceita a resposta de qualquer agente.
 var ja_lendo := ativo and (autor==str(dados.get("autor","Agente")) or autor=="Usuário")
 var tom_antes := tom
 if not ja_lendo: iniciar(ajustes,str(dados.get("autor","Agente")),str(dados.get("id","")),anterior,false)
 if ajustes.has("tom"): tom = ajustes.tom
 if ajustes.has("intensidade"): intensidade = float(ajustes.intensidade)
 resposta = dados.duplicate(true)
 autor = str(dados.get("autor","Agente"))
 id = str(dados.get("id",""))
 var base_digitar := float(ajustes.get("digitacao",1.3))
 var digitar := base_digitar+float(variacao%3)*0.1 if base_digitar>0 else 0.0
 if ja_lendo:
  fila = []
  if fase=="lendo" or (fase=="pensando" and tom!=tom_antes): fila.append({"fase":"reagindo","duracao":1.1})
  if escrever: fila.append({"fase":"pensando","duracao":clampf(digitar,0.6,2.0)})
  elif digitar>0: fila.append({"fase":"digitando","duracao":digitar})
  # Uma resposta rápida ainda aguarda a reação já iniciada, sem reiniciá-la.
  if fase in ["lendo","reagindo"]: return
  # Esperando no "pensando" longo: segue para a nova fila (reação ao tom / pensar e escrever).
 else:
  var leitura := float(ajustes.get("leitura",1.5))
  fila = []
  if leitura>0: fila.append({"fase":"lendo","duracao":leitura})
  fila.append({"fase":"reagindo","duracao":1.1})
  if escrever: fila.append({"fase":"pensando","duracao":clampf(digitar,0.6,2.0)})
  elif digitar>0: fila.append({"fase":"digitando","duracao":digitar})
 avancar()

func avancar() -> void:
 if fila.is_empty():
  fase = ""
  ativo = false
  return
 var etapa: Dictionary = fila.pop_front()
 fase = etapa.fase
 restante = float(etapa.duracao)
 tempo = 0
 fase_mudou.emit()

func passo(dt: float) -> bool:
 if not ativo: return not resposta.is_empty()
 # Usa o tempo excedente; uma queda de FPS não prolonga a sequência.
 var saldo := dt
 while ativo and saldo>=restante:
  saldo -= restante
  avancar()
 if ativo:
  tempo += saldo
  restante -= saldo
 return not ativo and not resposta.is_empty()

func cancelar() -> Dictionary:
 var pendente := resposta
 resposta = {}
 ativo = false
 fase = ""
 fila = []
 tempo = 0
 som_emitido = false
 return pendente

func retirar_resposta() -> Dictionary:
 return cancelar()

func emocao() -> String:
 if fase=="reagindo": return CATALOGO.tons[tom].emocao
 return "Pensativa" if fase=="pensando" else "Curiosidade"

func celular() -> bool:
 return ativo and fase in ["lendo","digitando"]

func legenda() -> String:
 return {"lendo":"Lendo sua mensagem…","reagindo":"","pensando":"Pensando…","digitando":"Digitando…"}.get(fase,"")

func olhar() -> Vector2:
 if celular(): return Vector2(0.035*sin(tempo*3.2),0.17)
 return Vector2(-0.15, -0.06) if fase=="pensando" else Vector2.ZERO
