extends SceneTree
# Renderiza poses candidatas (GLB fora do projeto, carregadas em tempo de execução) na boneca real.
# KK_CANDIDATAS: pasta com os GLBs; KK_PROVA_RETRATO: pasta de saída.
const AMOSTRAS := [0.0, 0.33, 0.66]
func _initialize(): call_deferred("provar")
func capturar(nome):
 for i in 6: await process_frame
 RenderingServer.force_draw()
 root.get_texture().get_image().save_png(OS.get_environment("KK_PROVA_RETRATO").path_join(nome))
func carregar_glb(caminho: String) -> Array:
 var doc := GLTFDocument.new()
 var estado := GLTFState.new()
 if doc.append_from_file(caminho, estado) != OK: return []
 var cena := doc.generate_scene(estado)
 var sk: Skeleton3D = cena.find_children("*","Skeleton3D",true,false)[0]
 var player: AnimationPlayer = cena.find_children("*","AnimationPlayer",true,false)[0]
 var rest := {}
 for i in sk.get_bone_count(): rest[sk.get_bone_name(i)] = sk.get_bone_rest(i)
 var anim: Animation
 for n in player.get_animation_list():
  if n != "RESET": anim = player.get_animation(n).duplicate(true); break
 cena.free()
 return [anim, rest]
func provar():
 root.size = Vector2i(560,1000)
 var app = load("res://mascote.gd").new()
 app.roupas.relogio = func(): return {"hour":12,"weekday":1}
 app.prova = true
 app.cache = "/tmp/kk-previa-idle-%d.json" % OS.get_process_id()
 app.runtime = ""
 root.add_child(app)
 app.set_process(false)
 app.olhar.active = false
 app.secundario.active = false
 for t in app.get_children():
  if t is Timer: t.stop()
 app.sub.size = Vector2i(560,1000)
 app.sprite.position = Vector2(280,500)
 app.sprite.scale = Vector2.ONE
 app.camera.size = 1.8
 app.camera.position = Vector3(0,0.8,4)
 app.chika.rotation.y = 0.35
 var pasta := OS.get_environment("KK_CANDIDATAS")
 var corpo = app.animacoes_corpo
 var nomes := []
 for arquivo in DirAccess.open(pasta).get_files():
  if not arquivo.ends_with(".glb"): continue
  var r := carregar_glb(pasta.path_join(arquivo))
  if r.is_empty(): push_error("falhou "+arquivo); continue
  corpo.fontes[arquivo.get_basename()] = r[0]
  corpo.repousos[arquivo.get_basename()] = r[1]
  nomes.append(arquivo.get_basename())
 # Referência atual, para comparar lado a lado.
 nomes.push_front("idle_em_pe")
 var lib: AnimationLibrary = corpo.biblioteca(app.sk, str(app.chika.get_path_to(app.sk)))
 app.player.add_animation_library("prev", lib)
 for nome in nomes:
  var anim: Animation = lib.get_animation(nome)
  for k in AMOSTRAS.size():
   app.player.play("prev/"+nome); app.player.seek(anim.length*AMOSTRAS[k], true); app.player.pause()
   await capturar("%s_%d.png" % [nome, k])
  print("PREVIA ", nome, " ", anim.length)
 quit()
