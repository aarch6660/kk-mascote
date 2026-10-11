shader_type spatial;
render_mode cull_disabled, specular_disabled, ambient_light_disabled, depth_prepass_alpha;
// Reconstrução dos shaders Shader Forge do KK. Máscaras são dados lineares.
uniform sampler2D main_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D color_mask : hint_default_black, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D detail_mask : hint_default_black, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D line_mask : hint_default_black, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D alpha_mask : hint_default_white, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D ramp_tex : filter_linear, repeat_disable;
uniform sampler2D view_ramp_tex : hint_default_white, filter_linear, repeat_disable;
uniform sampler2D hair_gloss : source_color, hint_default_black, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D overtex1 : source_color, hint_default_black, filter_linear_mipmap_anisotropic, repeat_disable;
uniform sampler2D overtex2 : source_color, hint_default_black, filter_linear_mipmap_anisotropic, repeat_disable;
uniform sampler2D overtex3 : source_color, hint_default_black, filter_linear_mipmap_anisotropic, repeat_disable;
uniform vec4 overcolor1 : source_color = vec4(1.0);
uniform vec4 overcolor2 : source_color = vec4(1.0);
uniform vec4 overcolor3 : source_color = vec4(1.0);
uniform bool tem_over1 = false;
uniform bool tem_over2 = false;
uniform bool tem_over3 = false;
uniform bool expressao_gag = false;
uniform vec4 uv_maquiagem = vec4(1.0,1.0,0.0,0.0);
uniform vec4 cor : source_color = vec4(1.0);
uniform vec4 cor2 : source_color = vec4(1.0);
uniform vec4 cor3 : source_color = vec4(1.0);
uniform vec4 sombra : source_color = vec4(0.7,0.75,0.85,1.0);
uniform vec4 linha : source_color = vec4(0.5);
uniform bool tem_main = false;
uniform bool tem_mask = false;
uniform bool tem_normal = false;
uniform bool normal_dxt5 = false;
uniform bool cabelo = false;
uniform bool rosto = false;
uniform bool olhos = false;
uniform float linha_r = 0.0;
uniform float linha_g = 0.0;
uniform float normal_forca = 0.35;
uniform float sombra_extensao = 0.5;
uniform float rim = 0.05;
uniform float rim_potencia = 4.0;
uniform float especular = 0.0;
uniform float especular_altura = 0.985;
// RGB global linear do KK; força de sombra reconstruída em cores_kk.json.
uniform vec4 ambiente_kk = vec4(0.019,0.027,0.039,0.74);
// Compatibility trabalha em sRGB; Forward+ trabalha em linear.
// Fazer a composição do KK em linear nas duas rotas e converter só na saída.
vec3 decodificar_srgb(vec3 c) {
 return mix(c/12.92,pow((c+0.055)/1.055,vec3(2.4)),step(vec3(0.04045),c));
}
vec3 codificar_srgb(vec3 c) {
 c = max(c,vec3(0.0));
 return mix(c*12.92,1.055*pow(c,vec3(1.0/2.4))-0.055,step(vec3(0.0031308),c));
}
vec3 cor_linear(vec3 c) { return OUTPUT_IS_SRGB ? decodificar_srgb(c) : c; }
vec3 cor_saida(vec3 c) { return OUTPUT_IS_SRGB ? codificar_srgb(c) : c; }
vec3 rgb_hsv(vec3 c) {
 vec4 k = vec4(0.0,-1.0/3.0,2.0/3.0,-1.0);
 vec4 p = mix(vec4(c.bg,k.wz),vec4(c.gb,k.xy),step(c.b,c.g));
 vec4 q = mix(vec4(p.xyw,c.r),vec4(c.r,p.yzx),step(p.x,c.r));
 float d = q.x-min(q.w,q.y);
 return vec3(abs(q.z+(q.w-q.y)/(6.0*d+0.000001)),d/(q.x+0.000001),q.x);
}
vec3 hsv_rgb(vec3 c) {
 vec3 p = abs(fract(c.xxx+vec3(0.0,2.0/3.0,1.0/3.0))*6.0-3.0);
 return c.z*mix(vec3(1.0),clamp(p-1.0,0.0,1.0),c.y);
}
varying vec3 detalhe_cabelo;
varying vec3 detalhes_linha;
varying float sombra_pintada;
vec3 overlay(vec3 a, vec3 b) {
 return mix(2.0*a*b, 1.0-2.0*(1.0-a)*(1.0-b), step(vec3(0.5),b));
}
varying vec2 gloss_uv;
varying vec3 n_face;
varying vec3 binormal_eye;
void vertex() {
 gloss_uv = UV2;
 binormal_eye = normalize((MODELVIEW_MATRIX*vec4(BINORMAL,0.0)).xyz);
 n_face = normalize((MODELVIEW_MATRIX * vec4(0.0,0.0,1.0,0.0)).xyz);
}
void fragment() {
 vec4 base = tem_main ? texture(main_tex,UV) : vec4(1.0);
 vec3 cm = texture(color_mask,UV).rgb;
 base.rgb = cor_linear(base.rgb);
 vec3 tinta = cor_linear(cor.rgb);
 if (tem_mask) {
  // Canais de cor do KK: vermelho base, verde raiz/região 2, azul ponta/região 3.
  tinta = mix(vec3(1.0),tinta,cm.r);
  tinta = mix(tinta,cor_linear(cor2.rgb),cm.g);
  tinta = mix(tinta,cor_linear(cor3.rgb),cm.b);
 }
 vec3 det = texture(detail_mask,UV).rgb;
 detalhe_cabelo = det;
 vec3 lin = texture(line_mask,UV).rgb;
 detalhes_linha = lin;
 float linhas = max(lin.r, max(det.r*linha_r,det.g*linha_g));
 if (rosto) linhas = max(linhas, det.g); // Canal original da linha dos lábios.
 if (cabelo) linhas = 0.0; // Detail.g controla sombra, não uma linha cinza sobreposta.

 base.rgb *= tinta;
 if (tem_over1) {
  vec4 o = texture(overtex1,UV);
  base.rgb = mix(base.rgb,cor_linear(o.rgb)*cor_linear(overcolor1.rgb),o.a*overcolor1.a);
 }
 if (tem_over2) {
  vec4 o = texture(overtex2,UV);
  base.rgb = mix(base.rgb,cor_linear(o.rgb)*cor_linear(overcolor2.rgb),o.a*overcolor2.a);
 }
 if (tem_over3 && !expressao_gag) {
  vec4 o = texture(overtex3,UV*uv_maquiagem.xy+uv_maquiagem.zw);
  base.rgb = mix(base.rgb,cor_linear(o.rgb)*cor_linear(overcolor3.rgb),o.a*overcolor3.a);
 }
 // Sombras da face são calculadas pela rampa, sem tingir a textura duas vezes.
 base.rgb = mix(base.rgb,base.rgb*cor_linear(linha.rgb),clamp(linhas*linha.a,0.0,1.0));
 sombra_pintada = rosto ? (1.0-det.b)*0.12 : (cabelo ? 0.0 : (1.0-det.b)*0.10);
 ALBEDO = cor_saida(base.rgb);
 ROUGHNESS = 1.0;
 if (tem_normal && !rosto) {
  vec4 n = texture(normal_tex,UV);
  vec2 xy = (normal_dxt5 ? n.ag : n.rg)*2.0-1.0;
  vec3 nn = vec3(xy,sqrt(max(1.0-dot(xy,xy),0.0)));
  NORMAL_MAP = nn*0.5+0.5;
  NORMAL_MAP_DEPTH = normal_forca;
 }
 float borda = pow(1.0-clamp(dot(normalize(NORMAL),normalize(VIEW)),0.0,1.0),rim_potencia);
 EMISSION = ALBEDO * (olhos ? 1.0 : 0.0) + ALBEDO*borda*rim;
 if (base.a * texture(alpha_mask,UV).r < 0.5) discard;
 ALPHA = base.a * cor.a;
}
void light() {
 if (!olhos) {
  vec3 albedo = cor_linear(ALBEDO);
  vec3 n = rosto ? normalize(mix(NORMAL,n_face,0.82)) : NORMAL;
  float ndl = dot(n,LIGHT)*0.5+0.5;
  float x = clamp(ndl - sombra_pintada + (sombra_extensao-0.5)*0.15,0.0,1.0);
  float r = texture(ramp_tex,vec2(x,0.5)).r;
  if (cabelo) {
   // Composição recuperada do DXBC main_hair; intensidade global reconstruída.
   // _AnotherRamp e _RampG recebem N·V e N·L assinados, não half-Lambert.
   float vr = texture(view_ramp_tex,vec2(dot(NORMAL,VIEW),0.5)).r;
   float lr = texture(ramp_tex,vec2(dot(NORMAL,LIGHT),0.5)).r;
   float r_kk = clamp(min(vr,lr),0.0,1.0);
   vec3 ambiente = mix(ambiente_kk.rgb,vec3(1.0),1.0-ambiente_kk.a);
   vec3 tom = clamp(overlay(ambiente,cor_linear(sombra.rgb)),0.0,1.0);
   vec2 uv = gloss_uv + vec2(dot(NORMAL,LIGHT)*0.005,
                            (especular_altura-1.0)*dot(normalize(binormal_eye),VIEW));
   float g = cor_linear(texture(hair_gloss,uv).rgb).r;
   float dg = (cor_linear(texture(hair_gloss,uv+vec2(0.0,0.008)).rgb).r-g)*0.5;
   vec3 b = albedo*mix(vec3(1.0),tom,dg);
   vec3 resultado = mix(b*tom,b,r_kk*(1.0-detalhe_cabelo.g)*ATTENUATION);
   resultado += vec3(g*(lr*0.5+0.5));
   resultado *= mix(tom,vec3(1.0),max(max(r_kk,1.0-detalhe_cabelo.g),1.0-sombra_extensao));
   // LIGHT_COLOR contém PI no Godot; shader KK não usa Lambert/pi.
   SPECULAR_LIGHT += cor_saida(resultado*max(LIGHT_COLOR/3.14159265*0.6+0.4,ambiente_kk.rgb));
  } else {
   // main_skin/main_opaque: sombra cromática HSV + overlay do ambiente.
   // O alpha histórico é 1-shadowDepth; recuperar a profundidade nativa.
   vec3 ambiente = mix(ambiente_kk.rgb,vec3(1.0),1.0-ambiente_kk.a);
   vec3 hsv = rgb_hsv(albedo*cor_linear(sombra.rgb));
   hsv.y *= 0.5;
   hsv.z = 1.0;
   vec3 tom = clamp(overlay(ambiente,hsv_rgb(hsv)*0.9),0.0,1.0);
   float luz = texture(ramp_tex,vec2(max(dot(n,LIGHT),0.0),0.5)).r;
   float detalhe = min(1.0-detalhe_cabelo.g,1.0-detalhes_linha.b);
   float extensao = clamp(sombra_extensao*1.2,0.0,1.0);
   float fator = clamp(luz*mix(1.0,detalhe,extensao)*ATTENUATION,0.0,1.0);
   vec3 resultado = albedo*mix(tom,vec3(1.0),fator);
   // SPECULAR_LIGHT recebe a composição pronta, sem multiplicar ALBEDO novamente.
   SPECULAR_LIGHT += cor_saida(resultado*max(LIGHT_COLOR/3.14159265*0.6+0.4,ambiente_kk.rgb));

  }
 }
}
