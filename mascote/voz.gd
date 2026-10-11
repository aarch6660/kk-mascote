extends AudioStreamPlayer
# O relógio do áudio dirige texto e boca; a pausa do desktop pausa a reprodução.
var dados: Dictionary = {}
var caminho := ""
var terminou := false
func _ready() -> void:
 finished.connect(func(): terminou = true)
func iniciar(valor: Dictionary, runtime: String, id: String) -> bool:
 encerrar()
 if valor.is_empty(): return true
 if runtime.is_empty() or id.get_file()!=id or str(valor.get("arquivo","")) != id+".wav": return false
 if not valor.get("palavras") is Array or not valor.get("envoltoria") is Array or float(valor.get("passo",0)) <= 0: return false
 caminho = runtime.path_join("audio").path_join(id+".wav")
 var audio := AudioStreamWAV.load_from_file(caminho)
 if audio == null:
  encerrar()
  return false
 dados = valor
 stream = audio
 terminou = false
 play()
 return true
func tempo() -> float:
 if terminou: return float(dados.get("duracao",0))
 return maxf(0,get_playback_position()+AudioServer.get_time_since_last_mix()-AudioServer.get_output_latency())
func encerrar() -> void:
 stop()
 stream = null
 stream_paused = false
 if not caminho.is_empty(): DirAccess.remove_absolute(caminho)
 caminho = ""
 dados = {}
 terminou = false
