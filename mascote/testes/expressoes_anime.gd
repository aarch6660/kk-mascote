extends SceneTree

const ROSTO = preload("res://expressoes.gd")
const EFEITOS = preload("res://efeitos.gd")
const BONECAS := ["chika-haruno", "sawai-hinata", "mizuno-ayaka"]
const PERFIS_ANIME := ["Gargalhada", "Espanto", "Encantada", "Pânico cômico", "Birra", "Choro dramático", "Vergonha fofa", "Orgulho"]

var casos := 0
var erros: Array[String] = []
var sub: SubViewport
var palco: Node3D
var app_rosto
var boneca_atual := ""

func verificar(ok: bool, descricao: String) -> void:
 casos += 1
 if not ok: erros.append(descricao)

func _initialize() -> void:
 call_deferred("provar")

func _configurar_captura() -> void:
 var destino := OS.get_environment("KK_PROVA_RETRATO")
 if destino.is_empty(): return
 DirAccess.make_dir_recursive_absolute(destino)
 sub = SubViewport.new()
 sub.name = "ProvaExpressoes"
 sub.size = Vector2i(640,640)
 sub.transparent_bg = true
 sub.render_target_update_mode = SubViewport.UPDATE_ALWAYS
 root.add_child(sub)
 palco = Node3D.new()
 sub.add_child(palco)
 var camera := Camera3D.new()
 camera.projection = Camera3D.PROJECTION_ORTHOGONAL
 camera.size = 1.8
 camera.position = Vector3(0,1.0,3.2)
 camera.look_at(Vector3(0,1.0,0))
 palco.add_child(camera)
 camera.current = true
 var luz := DirectionalLight3D.new()
 luz.rotation_degrees = Vector3(-20,-25,0)
 palco.add_child(luz)

func capturar(nome: String) -> void:
 if sub == null: return
 for i in 4: await process_frame
 RenderingServer.force_draw()
 var destino := OS.get_environment("KK_PROVA_RETRATO").path_join(boneca_atual+"-"+nome+".png")
 sub.get_texture().get_image().save_png(destino)

func canal_da(malhas: Array, nome: String) -> Dictionary:
 for canal in app_rosto.canais:
  if str(canal.malha.name) == nome: return canal
 return {}

func ler_forma(canal: Dictionary, nome: String) -> float:
 if canal.is_empty() or not canal.grupos.olhos.has(nome): return -1.0
 return canal.malha.get_blend_shape_value(canal.grupos.olhos[nome])

func verificar_boca_fechada(canal: Dictionary, contexto: String) -> void:
 var abertos := 0.0
 var fechados := 0.0
 for forma in canal.grupos.boca:
  var peso: float = canal.malha.get_blend_shape_value(canal.grupos.boca[forma])
  if str(forma).ends_with("_op"): abertos += peso
  elif str(forma).ends_with("_cl"): fechados += peso
 verificar(abertos < 0.001 and is_equal_approx(fechados,1.0),contexto+": boca fechada em repouso")

func provar() -> void:
 _configurar_captura()
 var mensagens: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://mensagens.json"))
 for nome in PERFIS_ANIME:
  var perfil: Array = ROSTO.CATALOGO.perfis.get(nome,[])
  var meta: Dictionary = ROSTO.CATALOGO.get("caricatos",{}).get(nome,{})
  verificar(perfil.size()==3,nome+": perfil facial presente")
  verificar(meta.has("efeito") and meta.has("fechamento"),nome+": metadados de efeito e fechamento")
  verificar(meta.get("efeito","") in mensagens.efeitos,nome+": efeito permitido")
  verificar(float(meta.get("fechamento",-1))>=0.0 and float(meta.get("fechamento",2))<=1.0,nome+": fechamento no intervalo 0..1")

 var efeitos = EFEITOS.new()
 root.add_child(efeitos)
 for efeito in mensagens.efeitos:
  if efeito in ["nenhum","espirais","surpresa","alegria","ideia"]: continue
  efeitos.iniciar(efeito)
  verificar(efeitos.tipo==efeito,efeito+": inicia")
  efeitos.passo(2.0)
  verificar(efeitos.tipo=="nenhum",efeito+": limpa após duração")
 efeitos.pode_mostrar = false
 efeitos.iniciar("coracoes")
 verificar(not efeitos.deve_desenhar(), "pode_mostrar false suprime o desenho")
 efeitos.passo(2.0)
 verificar(efeitos.tipo=="nenhum", "efeito oculto também limpa o relógio")

 for boneca_var in BONECAS:
  var boneca_id: String = str(boneca_var)
  boneca_atual = boneca_id
  var caminho: String = "res://bonecas/"+boneca_id+"/saida/personagem.glb"
  var cena := load(caminho) as PackedScene
  verificar(cena != null,boneca_id+": GLB exportado carrega")
  if cena == null: continue
  var modelo = cena.instantiate()
  if sub != null: palco.add_child(modelo)
  var malhas: Array = modelo.find_children("*","MeshInstance3D",true,false)
  app_rosto = ROSTO.new()
  app_rosto.preparar(malhas)
  var face := canal_da(malhas,"cf_O_face")
  var sobrancelha := canal_da(malhas,"cf_O_mayuge")
  verificar(not face.is_empty() and not sobrancelha.is_empty(),boneca_id+": malhas faciais reconhecidas")
  if face.is_empty() or sobrancelha.is_empty():
   modelo.free()
   continue
  var olhos_hitomi: Array = app_rosto.canais.filter(func(c): return str(c.malha.name).begins_with("cf_Ohitomi_") and c.grupos.olhos.size()>0)
  verificar(olhos_hitomi.size()>=2,boneca_id+": morfos das íris disponíveis")

  for nome in PERFIS_ANIME:
   var perfil: Array = ROSTO.CATALOGO.perfis[nome]
   verificar(face.grupos.olhos.has(perfil[0]),boneca_id+"/"+nome+": forma ocular comum")
   verificar(sobrancelha.grupos.sobrancelhas.has(perfil[1]),boneca_id+"/"+nome+": forma de sobrancelha comum")
   verificar(face.grupos.boca.has(perfil[2]),boneca_id+"/"+nome+": forma de boca comum")
   app_rosto.aplicar(nome,0.0,"a",0.0,1.0)
   verificar_boca_fechada(face,boneca_id+"/"+nome)
   if nome=="Gargalhada":
    verificar(is_equal_approx(ler_forma(face,"egao_op"),0.15),boneca_id+": gargalhada preserva 15% da abertura ocular")
    verificar(is_equal_approx(ler_forma(face,"egao_cl"),0.85),boneca_id+": gargalhada fecha 85% dos olhos")
    for canal in olhos_hitomi:
     verificar(canal.malha.visible,boneca_id+": íris permanece visível no fechamento expressivo parcial")
   if sub != null: await capturar(nome)

  app_rosto.aplicar("Gargalhada",0.0,"a",0.0,1.0)
  for canal in olhos_hitomi:
   canal.malha.visible = canal.visibilidade
  app_rosto.aplicar("Gargalhada",0.0,"a",1.0,1.0)
  verificar(is_equal_approx(ler_forma(face,"egao_op"),0.0),boneca_id+": piscada soma com fechamento expressivo até fechar")
  verificar(is_equal_approx(ler_forma(face,"egao_cl"),1.0),boneca_id+": piscada máxima fecha completamente as pálpebras")
  for canal in olhos_hitomi:
   verificar(not canal.malha.visible,boneca_id+": íris oculta somente quando a pálpebra fecha totalmente")
   if canal.piscar>=0: verificar(is_zero_approx(canal.malha.get_blend_shape_value(canal.piscar)),boneca_id+": sem morph sintético de recuo da íris")

  app_rosto.aplicar("Gargalhada",0.0,"a",0.0,1.0)
  app_rosto.aplicar("Gargalhada",0.72,"a",0.0,1.0)
  verificar(face.grupos.boca.has("a_s_op") and face.malha.get_blend_shape_value(face.grupos.boca.get("a_s_op",-1))>0.70,boneca_id+": fala mantém articulação vocal durante expressão")
  verificar(face.malha.get_blend_shape_value(face.grupos.boca.get("egao_op",-1))<0.001,boneca_id+": forma fechada de boca facial não abre durante fala")
  app_rosto.aplicar("Gargalhada",0.0,"a",0.0,1.0)
  verificar_boca_fechada(face,boneca_id+": retorno após fala")
  app_rosto.aplicar("Felicidade",0.0,"a",0.0,1.0)
  verificar(is_equal_approx(ler_forma(face,"bisyou_op"),1.0),boneca_id+": perfis antigos continuam sem fechamento extra")
  app_rosto.aplicar("Felicidade",0.0,"a",0.4,1.0)
  verificar(is_equal_approx(ler_forma(face,"bisyou_op"),0.6),boneca_id+": piscada antiga mantém peso original")
  verificar(is_equal_approx(ler_forma(face,"def_cl"),0.4),boneca_id+": piscada antiga mantém pálpebra original")
  if modelo.get_parent() != null: modelo.get_parent().remove_child(modelo)
  modelo.free()

 var resultado := {"passou":erros.is_empty(),"casos":casos,"erros":erros,"bonecas":BONECAS,"perfis":PERFIS_ANIME,"capturas":not OS.get_environment("KK_PROVA_RETRATO").is_empty()}
 print(JSON.stringify(resultado))
 efeitos.queue_free()
 quit(0 if erros.is_empty() else 1)
