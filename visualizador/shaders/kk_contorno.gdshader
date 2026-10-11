shader_type spatial;
render_mode unshaded, cull_front;
uniform float espessura = 0.0012;
uniform vec4 cor_contorno : source_color = vec4(0.12,0.09,0.10,1.0);
uniform sampler2D main_tex : source_color, filter_linear_mipmap_anisotropic;
uniform bool tem_main = false;
uniform sampler2D alpha_mask : hint_default_white, filter_linear_mipmap_anisotropic;
void vertex() {
 // Alfa da cor de vértice Unity: fator de espessura, não iluminação.
 VERTEX += NORMAL*espessura*COLOR.a;
}
void fragment() {
 if (tem_main && texture(main_tex,UV).a < 0.5) discard;
 if (texture(alpha_mask,UV).r < 0.5) discard;
 ALBEDO = cor_contorno.rgb;
}
