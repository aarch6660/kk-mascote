// LUT 32³ da câmera do editor KK. Dados sRGB; não usar source_color.
uniform sampler2D lut_kk : filter_linear, repeat_disable;
vec3 graduar_kk(vec3 rgb) {
 vec3 c = clamp(rgb,0.0,1.0)*31.0;
 float b = floor(c.b);
 vec2 uv = vec2((b*32.0+c.r+0.5)/1024.0,1.0-(c.g+0.5)/32.0);
 vec3 a = texture(lut_kk,uv).rgb;
 vec3 z = texture(lut_kk,uv+vec2(min(1.0,31.0-b)/32.0,0.0)).rgb;
 return mix(a,z,fract(c.b));
}
