extends Node2D
# Desenhos vetoriais breves. Seguem os olhos reais; não substituem assets do jogo.
var tipo := "nenhum"
var tempo := 0.0
var duracao := 1.6
var forca := 1.0
var olhos: Array[Vector2] = []
var raio := 8.0
var ancora := Vector2.ZERO
var fechamento := 0.0
var pode_mostrar := true

func iniciar(nome: String, intensidade := 1.0) -> void:
 tipo = nome
 tempo = 0
 forca = clampf(intensidade,0.0,1.0)
 duracao = 1.6 if nome=="espirais" else 1.2
 queue_redraw()

func passo(dt: float) -> void:
 tempo += dt
 if tempo>=duracao: tipo = "nenhum"
 queue_redraw()

func deve_desenhar() -> bool:
 return tipo!="nenhum" and pode_mostrar

func desenhar_estrela(centro: Vector2, tamanho: float, cor: Color) -> void:
 var pontos := PackedVector2Array()
 for i in 10:
  var angulo := -PI*0.5+TAU*float(i)/10.0
  var r := tamanho if i%2==0 else tamanho*0.38
  pontos.append(centro+Vector2(cos(angulo),sin(angulo))*r)
 pontos.append(pontos[0])
 draw_colored_polygon(pontos,cor)
 draw_polyline(pontos,Color(0.42,0.25,0.14,cor.a),maxf(1.0,tamanho*0.12),true)

func desenhar_coracao(centro: Vector2, tamanho: float, cor: Color) -> void:
 var pontos := PackedVector2Array()
 for i in 41:
  var t := TAU*float(i)/40.0
  var x: float = 16.0*pow(sin(t),3.0)/17.0
  var y: float = (13.0*cos(t)-5.0*cos(2.0*t)-2.0*cos(3.0*t)-cos(4.0*t))/17.0
  pontos.append(centro+Vector2(x,-y)*tamanho)
 draw_colored_polygon(pontos,cor)
 draw_polyline(pontos,Color(0.47,0.18,0.28,cor.a),maxf(1.0,tamanho*0.1),true)

func _draw() -> void:
 if not deve_desenhar(): return
 var alfa := minf(1,tempo/0.15)*minf(1,(duracao-tempo)/0.3)*forca
 var cor := Color(1,0.86,0.52,alfa)
 var brilho := alfa*clampf(1.0-fechamento*1.1,0.0,1.0)
 if tipo=="espirais" and fechamento<0.6:
  for centro in olhos:
   draw_circle(centro,raio,Color(1,0.96,0.91,alfa*0.96))
   var pontos := PackedVector2Array()
   for i in 65:
    var f := float(i)/64
    var angulo := f*TAU*2.4+tempo*2.5
    pontos.append(centro+Vector2(cos(angulo),sin(angulo))*raio*f*0.85)
   draw_polyline(pontos,Color(0.25,0.15,0.25,alfa),maxf(1.2,raio*0.15),true)
 elif tipo=="surpresa":
  for i in 3:
   var a := -PI*0.8+float(i)*0.3
   var v := Vector2(cos(a),sin(a))
   draw_line(ancora+v*raio*2,ancora+v*raio*3.3,cor,maxf(1.5,raio*0.2),true)
 elif tipo=="alegria" or tipo=="ideia":
  for i in 3:
   var centro := ancora+Vector2((i-1)*raio*2.4,-raio*(2.0+sin(tempo*4+i)*0.4))
   var r := raio*(0.35+0.12*sin(tempo*5+i))
   var sparkle := Color(cor.r,cor.g,cor.b,brilho)
   draw_line(centro-Vector2(r,0),centro+Vector2(r,0),sparkle,1.8,true)
   draw_line(centro-Vector2(0,r),centro+Vector2(0,r),sparkle,1.8,true)
 elif tipo=="lagrimas":
  for i in olhos.size():
   var lado := -1.0 if i==0 else 1.0
   # A lágrima nasce abaixo do aro dos óculos e escorre só um trecho da bochecha.
   var fase := fposmod(tempo*1.7+float(i)*0.32,1.0)
   var centro := olhos[i]+Vector2(lado*raio*0.72,raio*(2.1+fase*0.62))
   var gota := Color(0.20,0.63,1.0,alfa)
   var largura := raio*0.34
   var trilha := Color(0.48,0.82,1.0,alfa*0.72)
   draw_line(centro-Vector2(0,raio*0.92),centro-Vector2(0,raio*0.36),trilha,maxf(2.0,raio*0.16),true)
   draw_circle(centro,largura,gota)
   draw_colored_polygon(PackedVector2Array([centro+Vector2(-largura*0.84,-largura*0.12),centro+Vector2(largura*0.84,-largura*0.12),centro+Vector2(0,-largura*1.8)]),gota)
   draw_circle(centro-Vector2(largura*0.25,largura*0.28),largura*0.22,Color(0.87,0.97,1.0,alfa*0.85))
 elif tipo=="raiva":
  var centro := ancora+Vector2(raio*2.75,-raio*2.65)
  var marca := Color(0.92,0.18,0.18,alfa)
  var espessura := maxf(2.4,raio*0.3)
  draw_circle(centro,raio*1.05,Color(1.0,0.96,0.9,alfa*0.94))
  draw_line(centro-Vector2(raio*0.85,raio*0.95),centro+Vector2(raio*0.08,raio*0.08),marca,espessura,true)
  draw_line(centro+Vector2(raio*0.08,raio*0.08),centro+Vector2(raio*0.92,-raio*0.68),marca,espessura,true)
  draw_line(centro+Vector2(raio*0.08,raio*0.08),centro-Vector2(raio*0.72,-raio*0.92),marca,espessura,true)
 elif tipo=="coracoes":
  for i in olhos.size():
   var centro := olhos[i]
   var opacidade := brilho*clampf(1.0-fechamento*1.15,0.0,1.0)
   draw_circle(centro,raio*0.96,Color(1.0,0.98,0.92,opacidade*0.98))
   desenhar_coracao(centro,raio*0.8,Color(1.0,0.25,0.48,opacidade))
  var tamanho := raio*0.38
  desenhar_coracao(ancora+Vector2(-raio*2.2,-raio*2.45+sin(tempo*5)*raio*0.14),tamanho,Color(1.0,0.5,0.67,brilho*0.85))
  desenhar_coracao(ancora+Vector2(raio*2.25,-raio*2.25+sin(tempo*5+1)*raio*0.14),tamanho*0.82,Color(1.0,0.52,0.66,brilho*0.85))
 elif tipo=="estrelas":
  for i in olhos.size():
   var centro := olhos[i]
   var opacidade := brilho*clampf(1.0-fechamento*1.15,0.0,1.0)
   draw_circle(centro,raio*0.96,Color(1.0,0.98,0.9,opacidade*0.98))
   desenhar_estrela(centro,raio*0.8,Color(1.0,0.72,0.08,opacidade))
 elif tipo=="suor":
  var centro := ancora+Vector2(raio*2.85,-raio*2.45)
  var gota := Color(0.25,0.67,1.0,alfa)
  var tamanho := raio*0.64
  draw_circle(centro,raio*0.96,Color(1.0,0.98,0.92,alfa*0.94))
  draw_circle(centro, tamanho*0.72, gota)
  draw_colored_polygon(PackedVector2Array([centro+Vector2(-tamanho*0.56,-tamanho*0.2),centro+Vector2(tamanho*0.56,-tamanho*0.2),centro+Vector2(0,-tamanho*1.55)]),gota)
  draw_circle(centro-Vector2(tamanho*0.2,tamanho*0.45),tamanho*0.16,Color(0.9,0.98,1.0,alfa*0.9))
 elif tipo=="rubor":
  for lado in [-1.0,1.0]:
   if olhos.is_empty(): break
   var olho := olhos[0] if lado<0 else olhos[olhos.size()-1]
   var centro := olho+Vector2(lado*raio*1.55,raio*0.92)
   var cor_rubor := Color(1.0,0.35,0.48,alfa*0.72)
   for i in 3:
    var deslocamento := (float(i)-1.0)*raio*0.34
    draw_line(centro+Vector2(deslocamento,-raio*0.24),centro+Vector2(deslocamento+raio*0.18,raio*0.24),cor_rubor,maxf(1.5,raio*0.12),true)
 elif tipo=="interrogacao":
  var centro := ancora+Vector2(raio*2.0,-raio*2.2)
  var curva := PackedVector2Array()
  for i in 17:
   var t := float(i)/16.0
   var angulo := -PI*0.88+PI*1.38*t
   curva.append(centro+Vector2(cos(angulo)*raio*0.56,-sin(angulo)*raio*0.7))
  draw_polyline(curva,Color(0.5,0.35,0.92,alfa),maxf(1.8,raio*0.2),true)
  draw_line(centro+Vector2(raio*0.45,raio*0.16),centro+Vector2(raio*0.12,raio*0.62),Color(0.5,0.35,0.92,alfa),maxf(1.8,raio*0.2),true)
  draw_circle(centro+Vector2(raio*0.08,raio*1.0),raio*0.13,Color(0.5,0.35,0.92,alfa))
 elif tipo=="desanimo":
  for i in 3:
   var centro := ancora+Vector2((float(i)-1.0)*raio*0.72,-raio*2.2)
   draw_circle(centro,raio*0.13,Color(0.48,0.53,0.68,alfa))
