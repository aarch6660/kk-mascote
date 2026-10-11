extends RefCounted
# Formas originais do Koikatsu; grupos independentes de olhos, sobrancelha e boca.
static var CATALOGO: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://expressoes.json"))
static var PERFIS: Dictionary = CATALOGO.perfis
var canais: Array = []
var ajustes: Dictionary = {}
var dinamica := 1.0
var vogais_amplas := false
func validar_ajustes(dados) -> bool:
 if not dados is Dictionary: return false
 for chave in dados:
  if chave == "intensidade":
   if not (dados[chave] is float or dados[chave] is int): return false
   if not is_finite(float(dados[chave])) or float(dados[chave]) < 0 or float(dados[chave]) > 1: return false
  elif chave in ["olhos","sobrancelhas","boca"]:
   var valor = dados[chave]
   if valor is String:
    if not PERFIS.has(valor): return false
   elif valor is Dictionary:
    var soma := 0.0
    if valor.is_empty() or valor.size()>4: return false
    for forma in valor:
     if forma not in CATALOGO.formas[chave]: return false
     if not (valor[forma] is int or valor[forma] is float): return false
     var peso := float(valor[forma])
     if not is_finite(peso) or peso < 0 or peso > 1: return false
     soma += peso
    if soma > 1.000001: return false
   else: return false
  elif chave == "vogais_amplas":
   if not dados[chave] is bool: return false
  else: return false
 return true
func mistura(grupo: String, emocao: String, indice: int) -> Dictionary:
 var intensidade := float(ajustes.get("intensidade",1.0))*dinamica
 var valor = ajustes.get(grupo,emocao)
 var nomes := {}
 if valor is Dictionary:
  var soma := 0.0
  for nome in valor:
   nomes[nome] = float(valor[nome])*intensidade
   soma += float(nomes[nome])
  nomes[str(PERFIS.Neutra[indice])] = float(nomes.get(str(PERFIS.Neutra[indice]),0))+1.0-soma
 else:
  var perfil: Array = PERFIS.get(valor,PERFIS.Neutra)
  nomes[str(PERFIS.Neutra[indice])] = 1.0-intensidade
  nomes[str(perfil[indice])] = float(nomes.get(str(perfil[indice]),0))+intensidade
 return nomes
func preparar(malhas: Array) -> void:
 canais.clear()
 for malha in malhas:
  var grupos := {"olhos": {}, "sobrancelhas": {}, "boca": {}}
  var piscar := -1
  for i in malha.mesh.get_blend_shape_count():
   var nome := str(malha.mesh.get_blend_shape_name(i))
   if nome == "piscar": piscar = i; continue
   var grupo := "boca" if nome.begins_with("kuti_") else ("olhos" if nome.begins_with("eye_") else ("sobrancelhas" if nome.begins_with("mayuge.") else ""))
   if grupo.is_empty(): continue
   var inicio := nome.find("_", nome.find(".") + 1) + 1
   grupos[grupo][nome.substr(inicio)] = i
  if piscar >= 0 or not grupos.boca.is_empty() or not grupos.olhos.is_empty() or not grupos.sobrancelhas.is_empty():
   canais.append({"malha":malha, "grupos":grupos, "piscar":piscar, "olhos_abertos":{}, "visibilidade":malha.visible})
func adicionar(alvos: Dictionary, grupo: Dictionary, nome: String, peso: float, padrao: String) -> void:
 if not grupo.has(nome): nome = padrao
 if grupo.has(nome): alvos[grupo[nome]] = float(alvos.get(grupo[nome],0)) + peso
func aplicar(emocao: String, abertura: float, vogal: String, piscar: float, dt: float) -> void:
 # O fechamento extra é opcional. Perfis antigos mantêm exatamente o pulso
 # de piscada que já recebiam; a gargalhada combina os dois fechamentos.
 var metadados: Dictionary = CATALOGO.get("caricatos", {}).get(emocao, {})
 var fechamento_expressivo := clampf(float(metadados.get("fechamento", 0.0)), 0.0, 1.0)
 var fechamento_total := 1.0 - (1.0 - clampf(piscar, 0.0, 1.0)) * (1.0 - fechamento_expressivo)
 var olhos := mistura("olhos",emocao,0)
 var sobrancelhas := mistura("sobrancelhas",emocao,1)
 var boca := mistura("boca",emocao,2)
 for canal in canais:
  var alvos := {}
  var grupos: Dictionary = canal.grupos
  for grupo in grupos.values():
   for indice in grupo.values(): alvos[indice] = 0.0
  # Suaviza a emoção antes de compor o piscar. A pálpebra acompanha o
  # fechamento diretamente: filtrar o pulso curto impedia fechar por completo.
  var abertos: Dictionary = canal.olhos_abertos
  var alvo_olhos := {}
  for nome in olhos:
   var existente: String = nome if grupos.olhos.has(nome) else "def_op"
   alvo_olhos[existente] = float(alvo_olhos.get(existente,0))+float(olhos[nome])
  if abertos.is_empty(): abertos.merge(alvo_olhos)
  for nome in grupos.olhos:
   if not str(nome).ends_with("_op"): continue
   var peso := lerpf(float(abertos.get(nome,0)),float(alvo_olhos.get(nome,0)),minf(1.0,dt*16.0))
   abertos[nome] = peso
   adicionar(alvos,grupos.olhos,nome,peso*(1.0-fechamento_total),"def_op")
   var fechado: String = str(nome).trim_suffix("_op")+"_cl"
   adicionar(alvos,grupos.olhos,fechado,peso*fechamento_total,"def_cl")
  for nome in sobrancelhas: adicionar(alvos,grupos.sobrancelhas,nome,sobrancelhas[nome],"def_op")
  for nome in boca: adicionar(alvos,grupos.boca,nome,boca[nome]*(1.0-abertura),"def_cl")
  var ampla: bool = bool(ajustes.get("vogais_amplas",false)) or vogais_amplas
  var forma_vogal := vogal+("_l_op" if ampla and abertura>0.55 else "_s_op")
  if not grupos.boca.has(forma_vogal): forma_vogal = vogal+"_s_op"
  adicionar(alvos,grupos.boca,forma_vogal,abertura,"def_op")
  # Evita uma fresta de íris em poses extremas: oculta somente quando a
  # pálpebra já está totalmente fechada, mantendo o olho nas fases intermediárias.
  if str(canal.malha.name).begins_with("cf_Ohitomi"):
   canal.malha.visible = canal.visibilidade and fechamento_total < 0.999
  # As formas nativas já cobrem íris e esclera pela profundidade da face.
  # O morph sintético de recuo da íris (-7 cm) apagava a pupila antes da hora.
  if canal.piscar >= 0:
   alvos[canal.piscar] = piscar if grupos.olhos.is_empty() and not str(canal.malha.name).begins_with("cf_Ohitomi") else 0.0
  for indice in alvos:
   var atual: float = canal.malha.get_blend_shape_value(indice)
   var ocular: bool = indice in grupos.olhos.values() or indice == canal.piscar
   var valor := float(alvos[indice]) if ocular else lerpf(atual,float(alvos[indice]),minf(1.0,dt*16.0))
   if absf(valor-float(alvos[indice])) < 0.001: valor = alvos[indice]
   if not is_equal_approx(atual,valor): canal.malha.set_blend_shape_value(indice,valor)
