extends RefCounted
# Fases visuais publicadas pelo agente. Não lê a conversa nem interpreta o pedido.
signal fase_mudou
# Resposta curta enviada sozinha durante uma espera longa ("pera", "calma aí").
signal mensagem_rapida(texto: String)
const RAPIDAS := ["pera", "calma aí", "hm", "peraí", "tô escrevendo, calma", "1 seg", "hmmm"]
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
# Fases: distraida (ainda não viu) → lendo → reagindo → esperando (celular na mão; "digitando…" liga e desliga).
var leitura_dur := 1.5
var origem_chat := false     # leitura começou por mensagem escrita na janela de chat
var permitir_rapida := false # o mascote liga quando a Hana responde sozinha
var teclando := false
var ciclo_restante := 0.0
var espera_total := 0.0
var rapida_em := -1.0

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

static func tempo_leitura(caracteres: int) -> float:
 # Mensagem de chat se lê rápido: "oi" é instantâneo, um parágrafo leva uns segundos.
 return clampf(0.5+float(caracteres)/35.0,0.7,4.0)

func iniciar(dados: Dictionary, dono: String, identificador: String, anterior: String, emitir := true) -> void:
 cancelar()
 ativo = true
 autor = dono
 id = identificador
 tom = str(dados.get("tom","neutro"))
 intensidade = float(dados.get("intensidade",0.65))
 emocao_anterior = anterior
 variacao += 1
 origem_chat = dados.has("caracteres")
 var limite := float(dados.get("duracao",30))
 var distracao := clampf(float(dados.get("distracao",0)),0,12)
 var leitura := tempo_leitura(int(dados.caracteres)) if origem_chat else float(dados.get("leitura",1.5))+float(variacao%3)*0.12
 leitura = minf(leitura,maxf(0.3,limite-1.2))
 leitura_dur = leitura
 fila = []
 if distracao>0: fila.append({"fase":"distraida","duracao":distracao})
 fila.append({"fase":"lendo","duracao":leitura})
 # Mensagem ainda sem tom conhecido não ganha uma reação vazia de 1 s.
 if tom!="neutro": fila.append({"fase":"reagindo","duracao":1.1})
 fila.append({"fase":"esperando","duracao":maxf(0.1,limite-leitura-distracao)})
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
  # Resposta chegou antes de ela ver: termina a distração, lê e só então reage.
  if fase=="distraida": fila.append({"fase":"lendo","duracao":leitura_dur})
  if fase in ["distraida","lendo"] or (fase=="esperando" and tom!=tom_antes and tom!="neutro"):
   fila.append({"fase":"reagindo","duracao":1.1 if fase!="esperando" else 0.8})
  if escrever: fila.append({"fase":"digitando","duracao":clampf(digitar*0.3,0.3,0.7)})
  elif digitar>0: fila.append({"fase":"digitando","duracao":digitar})
  # Uma resposta rápida ainda aguarda a fase já iniciada, sem reiniciá-la.
  if fase in ["distraida","lendo","reagindo"]: return
  # Na espera: segue para a nova fila (reação ao tom e escrever).
 else:
  var leitura := float(ajustes.get("leitura",1.5))
  fila = []
  if leitura>0: fila.append({"fase":"lendo","duracao":leitura})
  fila.append({"fase":"reagindo","duracao":1.1})
  if escrever: fila.append({"fase":"digitando","duracao":clampf(digitar*0.3,0.3,0.7)})
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
 if fase=="esperando":
  # Começa olhando a mensagem um instante, depois "digitando…" liga e desliga como gente de verdade.
  teclando = false
  ciclo_restante = randf_range(0.6,1.4)
  espera_total = 0
  rapida_em = randf_range(9.0,14.0) if origem_chat and permitir_rapida else -1.0
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
  if fase=="esperando": passo_espera(dt)
 return not ativo and not resposta.is_empty()

func passo_espera(dt: float) -> void:
 espera_total += dt
 ciclo_restante -= dt
 if ciclo_restante > 0: return
 if teclando:
  teclando = false
  ciclo_restante = randf_range(1.2,2.6)
  # Demorou: às vezes manda uma bolha curta antes da resposta (uma vez só).
  if rapida_em>0 and espera_total>=rapida_em:
   rapida_em = -1.0
   if randf()<0.7: mensagem_rapida.emit(RAPIDAS[randi()%RAPIDAS.size()])
 else:
  teclando = true
  ciclo_restante = randf_range(2.5,5.5)

func esta_teclando() -> bool:
 return ativo and (fase=="digitando" or (fase=="esperando" and teclando))

func visivel() -> bool:
 # Distraída: ainda não viu; o mascote segue como estava.
 return ativo and fase!="distraida"

func fase_publica() -> String:
 # O que a janela de chat mostra no status.
 if fase=="distraida": return ""
 if fase=="esperando": return "digitando" if teclando else "visto"
 return fase

func olhando_voce() -> bool:
 # Nas pausas longas da espera, dá uma olhada para fora do celular.
 return fase=="esperando" and not teclando and ciclo_restante>0.5 and int(espera_total/7.0)%2==1

func cancelar() -> Dictionary:
 var pendente := resposta
 resposta = {}
 ativo = false
 fase = ""
 fila = []
 tempo = 0
 som_emitido = false
 teclando = false
 return pendente

func retirar_resposta() -> Dictionary:
 return cancelar()

func emocao() -> String:
 if fase=="reagindo": return CATALOGO.tons[tom].emocao
 if fase=="distraida": return emocao_anterior
 return "Curiosidade" if fase=="lendo" else "Neutra"

func celular() -> bool:
 return ativo and fase in ["lendo","digitando","esperando"]

func legenda() -> String:
 if fase=="esperando": return "Digitando…" if teclando else ""
 return {"lendo":"Lendo sua mensagem…","digitando":"Digitando…"}.get(fase,"")

func olhar() -> Vector2:
 if olhando_voce(): return Vector2.ZERO
 if celular(): return Vector2(0.035*sin(tempo*3.2),0.17)
 return Vector2.ZERO
