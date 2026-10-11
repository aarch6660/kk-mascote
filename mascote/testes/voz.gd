extends SceneTree
var casos := 0
var erros: Array = []
func verificar(ok: bool, descricao: String) -> void:
 casos += 1
 if not ok: erros.append(descricao)
func _initialize(): call_deferred("provar")
func provar():
 var fala = load("res://fala_texto.gd").new()
 var dados := {"palavras":[{"inicio":0.2,"fim":0.8,"de":0,"ate":3},{"inicio":1.0,"fim":1.6,"de":4,"ate":7}],"passo":0.02,"envoltoria":[]}
 for i in 100: dados.envoltoria.append(0.8 if i < 70 else 0.0)
 fala.iniciar({"texto":"Ola boa!"})
 fala.sincronizar_audio(0.1,dados,false,0.016)
 verificar(fala.abertura==0 and fala.indice==0,"Silêncio antes da primeira palavra")
 fala.sincronizar_audio(0.25,dados,false,0.016)
 verificar(fala.abertura>0.5 and fala.vogal=="o","Áudio abre boca com vogal e intensidade")
 fala.sincronizar_audio(0.9,dados,false,0.016)
 verificar(fala.abertura==0 and fala.indice==3,"Fecha boca entre palavras")
 fala.sincronizar_audio(1.01,dados,false,0.016)
 verificar(fala.abertura==0 and fala.indice==4,"B fecha lábios")
 fala.sincronizar_audio(1.3,dados,false,0.016)
 verificar(fala.abertura>0 and fala.indice==5,"Próxima vogal segue tempo da palavra")
 fala.sincronizar_audio(1.5,dados,false,0.016)
 verificar(fala.abertura==0,"Silêncio do áudio fecha boca dentro da palavra")
 fala.sincronizar_audio(2,dados,true,0.1)
 verificar(fala.ativo and fala.indice==8 and fala.abertura==0,"Fim do áudio mantém leitura e fecha boca")
 fala.sincronizar_audio(2,dados,true,3.0)
 verificar(not fala.ativo,"Conclui após pausa final")
 var pasta := "/tmp/kk-voz-godot-%d" % OS.get_process_id()
 DirAccess.make_dir_recursive_absolute(pasta.path_join("audio"))
 var wav := AudioStreamWAV.new()
 wav.format = AudioStreamWAV.FORMAT_16_BITS
 wav.mix_rate = 24000
 var pcm := PackedByteArray()
 pcm.resize(48000)
 wav.data = pcm
 wav.save_to_wav(pasta.path_join("audio/teste.wav"))
 dados.arquivo = "teste.wav"
 dados.duracao = 1.0
 var voz = load("res://voz.gd").new()
 root.add_child(voz)
 verificar(voz.iniciar(dados,pasta,"teste") and voz.playing,"Carrega WAV e reproduz")
 await create_timer(0.15).timeout
 voz.stream_paused = true
 var antes: float = voz.get_playback_position()
 await create_timer(0.15).timeout
 verificar(absf(voz.get_playback_position()-antes)<0.025,"Pausa mantém relógio de reprodução")
 voz.stream_paused = false
 await create_timer(1.2).timeout
 verificar(voz.terminou and not voz.playing,"Sinal de fim acompanha áudio")
 voz.encerrar()
 verificar(not FileAccess.file_exists(pasta.path_join("audio/teste.wav")) and voz.dados.is_empty(),"Encerrar libera áudio temporário")
 wav.save_to_wav(pasta.path_join("audio/teste.wav"))
 voz.iniciar(dados,pasta,"teste")
 voz.encerrar()
 verificar(not voz.playing and voz.stream==null and not FileAccess.file_exists(pasta.path_join("audio/teste.wav")),"Interromper para áudio e limpa arquivo")
 verificar(not voz.iniciar(dados,pasta,"../teste"),"Rejeita arquivo fora da fila")
 DirAccess.remove_absolute(pasta.path_join("audio"))
 DirAccess.remove_absolute(pasta)
 var resultado := {"casos":casos,"erros":erros,"passou":erros.is_empty()}
 print(JSON.stringify(resultado))
 var f := FileAccess.open("res://evidencias/voz-validacao.json",FileAccess.WRITE)
 f.store_string(JSON.stringify(resultado,"  "))
 voz.free()
 wav = null
 fala = null
 f.close()
 await create_timer(0.2).timeout
 quit(0 if erros.is_empty() else 1)
