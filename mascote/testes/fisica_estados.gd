extends SceneTree
var erros: Array = []
var casos := 0
func verificar(ok: bool, mensagem: String) -> void:
	casos += 1
	if not ok: erros.append(mensagem)
func _initialize() -> void:
	var f = load("res://fisica.gd").new()
	var e = load("res://estados.gd").new()
	var janela := {"address":"A","x":300.0,"y":600.0,"width":400.0}
	f.pos = Vector2(450, 300)
	f.atualizar([janela], 1920, 1038)
	for _i in 90: f.passo(1.0/30)
	verificar(f.apoio == "A" and f.pos.y == 600, "Pousar sem atravessar o topo")
	janela.x += 80; janela.y += 35
	f.atualizar([janela], 1920, 1038)
	verificar(f.pos == Vector2(530,635), "Seguir movimento da janela")
	f.atualizar([],1920,1038)
	verificar(f.apoio.is_empty(), "Perder apoio ao fechar/trocar workspace")
	for _i in 90: f.passo(1.0/30)
	verificar(f.apoio == "tela" and f.pos.y == 1038,"Base descontando reserva da barra")
	f.pos = Vector2(520,600); f.apoio="A"
	f.atualizar([{"address":"A","x":300,"y":600,"width":250},{"address":"B","x":650,"y":520,"width":300}],1920,1038)
	verificar(f.pular(Vector2(680,520)), "Salto balístico alcançável")
	for _i in 60: f.passo(1.0/30)
	verificar(f.apoio == "B" and f.pos.y == 520,"Pouso na janela vizinha")
	f.arrastando = true; var antes: Vector2 = f.pos
	f.passo(1.0)
	verificar(f.pos == antes,"Arrasto suspende gravidade")
	f.soltar(); verificar(f.apoio.is_empty(),"Soltar inicia queda")
	e.rng.seed = 4
	e.passo(8,0,true,true,false); verificar(e.estado == "andando","Parada → caminhada")
	e.passo(8,0,true,true,false); verificar(e.estado == "gesto","Caminhada → gesto")
	e.passo(8,0,true,true,false); verificar(e.estado == "sentada","Gesto → sentada")
	e.passo(1,181,true,true,false); verificar(e.estado == "cochilo","Ociosidade na janela → cochilo")
	e.passo(0.1,0,true,true,true); verificar(e.estado == "parada","Mouse próximo acorda")
	e.passo(1,181,true,false,false); verificar(e.estado == "dormindo","Ociosidade na tela → dormir")
	e.mudar("reacao"); var c: String = e.clipe
	e.mudar("reacao"); verificar(c != e.clipe,"Reações alternadas")
	e.sono_manual=true; e.mudar("cochilo")
	e.passo(0.1,0,true,true,true); verificar(e.estado == "cochilo","Sono manual persiste até acordar")
	e.sono_manual=false
	var vistos := {}
	for k in 12:
		var anterior: String = e.ultimo_idle
		e.mudar("gesto"); e.mudar("parada")
		verificar(e.clipe in e.idles,"Parada usa pose original do jogo")
		verificar(e.clipe != anterior,"Parada não repete a pose anterior")
		vistos[e.clipe] = true
	verificar(vistos.size() >= 3,"Parada varia entre as poses")
	var mantida: String = e.clipe
	e.mudar("parada"); verificar(e.clipe == mantida,"Parada repetida mantém a pose")
	var result := {"passou":erros.is_empty(),"erros":erros,"casos":casos}
	var arq := FileAccess.open("res://evidencias/headless-fisica-estados.json",FileAccess.WRITE)
	arq.store_string(JSON.stringify(result,"  "))
	print(JSON.stringify(result))
	quit(0 if erros.is_empty() else 1)
