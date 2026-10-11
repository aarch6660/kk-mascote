extends RefCounted
# Horário local; relógio injetável nos ensaios, sem gravar a roupa transitória nas prefs.
const MODOS := {"automatica":"Automática", "uniforme":"Uniforme", "casual":"Casual", "pijama":"Pijama"}
const NOMES := {0:"uniforme", 5:"casual", 6:"pijama"}
var relogio := func(): return Time.get_datetime_dict_from_system()

func coordenada(modo: String) -> int:
	if modo == "uniforme": return 0
	if modo == "casual": return 5
	if modo == "pijama": return 6
	var agora: Dictionary = relogio.call()
	if int(agora.hour) >= 22 or int(agora.hour) < 7: return 6
	return 5 if int(agora.weekday) in [0, 6] else 0
