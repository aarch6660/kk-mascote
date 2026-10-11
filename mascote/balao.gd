extends PanelContainer
var cabecalho := Label.new()
var corpo := RichTextLabel.new()
func _ready() -> void:
 mouse_filter = Control.MOUSE_FILTER_IGNORE
 z_index = 10
 var estilo := StyleBoxFlat.new()
 estilo.bg_color = Color("252128")
 estilo.border_color = Color("c99a50")
 estilo.set_border_width_all(2)
 estilo.set_corner_radius_all(14)
 estilo.content_margin_left = 16
 estilo.content_margin_right = 16
 estilo.content_margin_top = 12
 estilo.content_margin_bottom = 14
 add_theme_stylebox_override("panel",estilo)
 var caixa := VBoxContainer.new()
 caixa.mouse_filter = Control.MOUSE_FILTER_IGNORE
 add_child(caixa)
 cabecalho.mouse_filter = Control.MOUSE_FILTER_IGNORE
 cabecalho.clip_text = true
 cabecalho.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
 cabecalho.add_theme_color_override("font_color",Color("e9c384"))
 cabecalho.add_theme_font_size_override("font_size",14)
 caixa.add_child(cabecalho)
 corpo.mouse_filter = Control.MOUSE_FILTER_IGNORE
 corpo.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
 corpo.bbcode_enabled = false
 corpo.scroll_active = false
 corpo.fit_content = false
 corpo.custom_minimum_size = Vector2(300,40)
 corpo.add_theme_color_override("default_color",Color("fff4e3"))
 corpo.add_theme_font_size_override("normal_font_size",18)
 caixa.add_child(corpo)
 hide()
func atualizar(fala, ancora: Vector2, tela: Vector2, escondida: bool, afastamento := 70.0) -> void:
 visible = fala.ativo and not escondida
 if not visible: return
 cabecalho.text = fala.autor
 corpo.text = fala.pagina_visivel()
 var largura := clampf(tela.x-32,180,332)
 var altura := ThemeDB.fallback_font.get_multiline_string_size(corpo.text,HORIZONTAL_ALIGNMENT_LEFT,largura-32,18,-1,TextServer.BREAK_MANDATORY | TextServer.BREAK_WORD_BOUND | TextServer.BREAK_ADAPTIVE).y
 corpo.custom_minimum_size = Vector2(largura-32,maxf(40,altura+8))
 custom_minimum_size = Vector2(largura,0)
 reset_size()
 # Acima do rosto se houver espaço; senão ao lado, sempre dentro do monitor.
 var destino := ancora+Vector2(30,-size.y-25)
 if destino.y<16:
  destino = ancora+Vector2(afastamento,12) if ancora.x+afastamento+size.x<=tela.x-16 else ancora+Vector2(-size.x-afastamento,12)
 position = destino.clamp(Vector2(16,16),(tela-size-Vector2(16,16)).max(Vector2(16,16)))
