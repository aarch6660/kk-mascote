extends SceneTree

const PERFIS: Array[String] = ["Gargalhada", "Espanto", "Encantada", "Pânico cômico", "Birra", "Choro dramático", "Vergonha fofa", "Orgulho"]
const EXTRAS: Array[Dictionary] = [
 {"arquivo":"extra-estrelas", "emocao":"Encantada", "efeito":"estrelas"},
 {"arquivo":"extra-interrogacao", "emocao":"Dúvida", "efeito":"interrogacao"},
 {"arquivo":"extra-desanimo", "emocao":"Desânimo", "efeito":"desanimo"}
]
const BONECAS: Array[String] = ["chika-haruno", "sawai-hinata", "mizuno-ayaka"]

var erros: Array[String] = []
var app
var destino := ""

func _initialize() -> void:
 call_deferred("provar")

func capturar(nome: String) -> void:
 app.efeitos.queue_redraw()
 for i in 5: await process_frame
 RenderingServer.force_draw()
 var lado := 720
 var origem := Vector2i(app.sprite.position-Vector2.ONE*float(lado)*0.5)
 var regiao := Rect2i(origem,Vector2i(lado,lado))
 var imagem := root.get_texture().get_image()
 if regiao.position.x<0 or regiao.position.y<0 or regiao.end.x>imagem.get_width() or regiao.end.y>imagem.get_height():
  erros.append(nome+": recorte de 720x720 fora da janela")
  return
 var arquivo := destino.path_join(app.boneca+"-"+nome+".png")
 var erro := imagem.get_region(regiao).save_png(arquivo)
 if erro != OK: erros.append(nome+": falha ao salvar captura ("+str(erro)+")")

func preparar_app() -> void:
 root.size = Vector2i(1920,1080)
 root.content_scale_size = Vector2i(1920,1080)
 app = load("res://mascote.gd").new()
 app.roupas.relogio = func(): return {"hour":12,"weekday":1}
 app.cache = OS.get_environment("KK_ANIME_CACHE")
 app.runtime = ""
 app.prova = true
 app.boneca = BONECAS[0]
 app.perfil = true
 app.retrato = true
 app.moldura = false
 app.estilo_anime = false
 root.add_child(app)
 app.set_process(false)
 app.set_physics_process(false)
 for filho in app.get_children():
  if filho is Timer: filho.stop()
 app.olhar.active = false
 app.secundario.active = false
 app.dedos_mensagem.active = false
 app.zoom = 1.2
 app.pos_retrato = Vector2(960,600)
 app.fisica.pos = app.pos_retrato
 app.fisica.fixa = true
 app.encenacao.offset = 0
 app.chika.rotation = Vector3.ZERO
 app.player.play("idle_em_pe")
 app.player.seek(0.6,true)
 app.player.advance(0.0)
 app.player.pause()
 app.sk.force_update_all_bone_transforms()
 app.configurar_camera()
 app.camera.size = 0.26
 app.preparar_retrato()
 app.aplicar_render()
 app.posicionar()

func preparar_cena(emocao: String, efeito: String, fechamento: float) -> void:
 app.expressao = emocao
 app.emocao_atual = emocao
 app.ultimo_efeito_facial = emocao
 app.rosto.ajustes = {}
 app.rosto.dinamica = 1.0
 app.rosto.vogais_amplas = false
 app.rosto.aplicar(emocao,0.0,"a",0.0,1.0)
 app.sk.force_update_all_bone_transforms()
 app.efeitos.iniciar(efeito)
 app.efeitos.tempo = 0.4
 # Atualiza âncoras projetadas no nó vetorial da janela real.
 app.atualizar_efeitos(fechamento)
 app.efeitos.tempo = 0.4
 app.efeitos.pode_mostrar = true

func provar() -> void:
 destino = OS.get_environment("KK_ANIME_VISUAL")
 if destino.is_empty():
  erros.append("KK_ANIME_VISUAL não definido")
  print(JSON.stringify({"passou":false,"erros":erros}))
  quit(1)
  return
 DirAccess.make_dir_recursive_absolute(destino)
 preparar_app()
 for boneca_id in BONECAS:
  if app.boneca != boneca_id: app.trocar_boneca(boneca_id)
  app.olhar.active = false
  app.secundario.active = false
  app.dedos_mensagem.active = false
  app.player.play("idle_em_pe")
  app.player.seek(0.6,true)
  app.player.advance(0.0)
  app.player.pause()
  app.sk.force_update_all_bone_transforms()
  app.camera.size = 0.26
  app.configurar_camera()
  app.camera.size = 0.26
  app.posicionar()
  for emocao in PERFIS:
   var meta: Dictionary = app.rosto.CATALOGO.get("caricatos",{}).get(emocao,{})
   preparar_cena(emocao,str(meta.get("efeito","nenhum")),float(meta.get("fechamento",0.0)))
   await capturar(emocao)
  for extra in EXTRAS:
   preparar_cena(str(extra.emocao),str(extra.efeito),0.0)
   await capturar(str(extra.arquivo))
 var resultado := {"passou":erros.is_empty(),"bonecas":BONECAS,"perfis":PERFIS,"extras":EXTRAS,"capturas":BONECAS.size()*(PERFIS.size()+EXTRAS.size()),"erros":erros,"cache_privado":app.cache,"runtime":app.runtime,"prova":app.prova}
 print(JSON.stringify(resultado))
 app.free()
 quit(0 if erros.is_empty() else 1)
