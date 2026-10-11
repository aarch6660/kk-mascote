shader_type canvas_item;
render_mode unshaded;
#include "res://shaders/kk_lut.gdshaderinc"
void fragment() {
 COLOR = vec4(graduar_kk(COLOR.rgb),COLOR.a);
}
