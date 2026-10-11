shader_type canvas_item;
render_mode unshaded;
#include "res://shaders/kk_lut.gdshaderinc"
uniform sampler2D tela : hint_screen_texture, filter_nearest, repeat_disable;
void fragment() {
 vec4 c = texture(tela,SCREEN_UV);
 COLOR = vec4(graduar_kk(c.rgb),c.a);
}
