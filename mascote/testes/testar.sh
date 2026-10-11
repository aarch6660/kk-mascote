#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
godot_bin="${GODOT:-$HOME/.local/opt/godot/godot}"
"${PYTHON_PERSONAGEM:-$HOME/Games/samabake-mascote/.venv/bin/python}" ../personagem/testar_proporcoes.py
"$godot_bin" --headless --path . --editor --import --quit > evidencias/importacao.log 2>&1
"$godot_bin" --headless --path . --script testes/fisica_estados.gd
"$godot_bin" --headless --path . --script testes/fisica_kk.gd
"$godot_bin" --headless --path . --script testes/rig.gd
"$godot_bin" --headless --path . --script testes/bonecas.gd
"$godot_bin" --headless --path . --script testes/troca_bonecas.gd
"$godot_bin" --headless --path . --script testes/arrasto.gd
"$godot_bin" --headless --path . --script testes/roupas.gd
"$godot_bin" --headless --path . --script testes/perfil_facial.gd
"$godot_bin" --headless --path . --script testes/olhar_mouse.gd
"$godot_bin" --headless --path . --script testes/piscar.gd
"$godot_bin" --headless --path . --script testes/corpo_interacoes.gd
"$godot_bin" --headless --path . --script testes/maos_repouso.gd
"$godot_bin" --headless --path . --script testes/expression_kk.gd
"${PYTHON_PERSONAGEM:-$HOME/Games/samabake-mascote/.venv/bin/python}" testes/expression_kk_python.py
"${PYTHON_PERSONAGEM:-$HOME/Games/samabake-mascote/.venv/bin/python}" ../personagem/auditar_expression.py --verificar
"$godot_bin" --headless --path ../visualizador --script testes/expression_kk.gd
"$godot_bin" --headless --path . --script testes/fala_balao.gd
"$godot_bin" --headless --audio-driver Dummy --path . --script testes/voz.gd
"$godot_bin" --headless --path . --script testes/gestos_expressoes.gd
"$godot_bin" --headless --path . --script testes/eventos_face.gd
"$godot_bin" --headless --path . --script testes/atuacao.gd
"$godot_bin" --headless --audio-driver Dummy --path . --script testes/mensagens.gd
"$godot_bin" --headless --audio-driver Dummy --path . --script testes/escrita.gd
"$godot_bin" --headless --audio-driver Dummy --path . --script testes/ofegar.gd
"$godot_bin" --headless --audio-driver Dummy --path . --script testes/hana.gd
"$godot_bin" --headless --audio-driver Dummy --path . --script testes/hana_etapa2.gd
"$godot_bin" --headless --audio-driver Dummy --path . --script testes/hana_etapa3.gd
"$godot_bin" --headless --path . --script testes/encenacao_unidade.gd
"$godot_bin" --headless --path . --script testes/expressoes_anime.gd
"$godot_bin" --headless --path . --script testes/anims_anime.gd
"$godot_bin" --headless --path . --script testes/anime_encenacao.gd
python3 testes/anime_python.py
python3 testes/mensagens_python.py
python3 testes/chat_python.py
python3 testes/hana_python.py
python3 testes/hana_local_python.py
python3 testes/hana_etapa2_python.py
python3 testes/hana_etapa3_python.py
python3 testes/atuacao_python.py
python3 testes/eventos_python.py
python3 testes/ponte_fala.py
python3 testes/ponte.py
if [[ "${1:-}" == --tela ]]; then
    python3 - <<'PY'
import hypr_bridge, executar
m=hypr_bridge.query('monitors')[0]
assert (m['x'],m['y'],m['width'],m['height'],m['scale'])==(0,0,1920,1080,1), 'Ensaio só para 1920×1080, escala 1, origem 0.'
assert not (executar.RUNTIME/'pids.json').exists(), 'Feche a instância antes do ensaio.'
PY
    teste_dir=$(mktemp -d "${XDG_RUNTIME_DIR:-/tmp}/kk-mascote-prova.XXXXXX")
    trap 'rm -rf -- "$teste_dir"' EXIT
    wayland-scanner client-header testes/virtual-pointer.xml "$teste_dir/mascote-virtual-pointer.h"
    wayland-scanner private-code testes/virtual-pointer.xml "$teste_dir/mascote-virtual-pointer.c"
    cc -I"$teste_dir" testes/ponteiro.c "$teste_dir/mascote-virtual-pointer.c" -lwayland-client -o "$teste_dir/ponteiro"
    export MASCOTE_PONTEIRO="$teste_dir/ponteiro"
    python3 testes/provar_tela.py
    python3 testes/provar_interacoes.py
    python3 testes/provar_menu.py
    python3 testes/provar_capturas.py
fi
