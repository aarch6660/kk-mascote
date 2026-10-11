#!/usr/bin/env bash
# Regera a boneca escolhida a partir do card, com acesso somente leitura ao jogo.
set -euo pipefail
PASTA_PERSONAGEM="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export BONECA_DIR="${BONECA_DIR:-$PASTA_PERSONAGEM/../bonecas/chika-haruno}"
export KK_COORDENADA="${KK_COORDENADA:-0}"
case "$KK_COORDENADA" in [0-6]) ;; *) echo 'KK_COORDENADA precisa ser um inteiro de 0 a 6.' >&2; exit 1 ;; esac
export KK_BONECA_ID="$(basename -- "$BONECA_DIR")"
if [[ "$KK_COORDENADA" != 0 ]]; then
    BONECA_ORIGEM="$BONECA_DIR"
    export BONECA_DIR="$BONECA_ORIGEM/coordenadas/coord_$KK_COORDENADA"
    mkdir -p -- "$BONECA_DIR"
    cp -- "$BONECA_ORIGEM/card.png" "$BONECA_DIR/card.png"
fi
PYTHON_PERSONAGEM="${PYTHON_PERSONAGEM:-$HOME/Games/samabake-mascote/.venv/bin/python}"
BLENDER_PERSONAGEM="${BLENDER_PERSONAGEM:-$HOME/.local/opt/blender-5.2.2-linux-x64/blender}"
"$PYTHON_PERSONAGEM" "$PASTA_PERSONAGEM/preparar_pasta.py"
"$PYTHON_PERSONAGEM" "$PASTA_PERSONAGEM/ler_card.py"
"$PYTHON_PERSONAGEM" "$PASTA_PERSONAGEM/resolver.py"
"$PYTHON_PERSONAGEM" "$PASTA_PERSONAGEM/proporcoes.py"
"$PYTHON_PERSONAGEM" "$PASTA_PERSONAGEM/extrair.py"
"$PYTHON_PERSONAGEM" "$PASTA_PERSONAGEM/auditar_fisica_kk.py" --boneca-dir "$BONECA_DIR"
"$PYTHON_PERSONAGEM" "$PASTA_PERSONAGEM/auditar_expression.py" --boneca-dir "$BONECA_DIR"
"$PYTHON_PERSONAGEM" "$PASTA_PERSONAGEM/preparar_texturas.py"
"$PYTHON_PERSONAGEM" "$PASTA_PERSONAGEM/preparar_visual.py"
"$BLENDER_PERSONAGEM" -b -t 4 --python-exit-code 1 -P "$PASTA_PERSONAGEM/montar_blender.py"
"$BLENDER_PERSONAGEM" -b -t 4 --python-exit-code 1 -P "$PASTA_PERSONAGEM/verificar_blender.py"
KK_GUARDAR_ROUPA=1 "$BLENDER_PERSONAGEM" -b -t 4 --python-exit-code 1 -P "$PASTA_PERSONAGEM/montar_blender.py"
"$PYTHON_PERSONAGEM" "$PASTA_PERSONAGEM/validar_corpo.py" --pasta "$BONECA_DIR"
# Só remove intermediários desta tarefa, depois de gerar todas as saídas.
rm -rf -- "${BONECA_DIR:-$PASTA_PERSONAGEM}/trabalho"
rm -f -- "${BONECA_DIR:-$PASTA_PERSONAGEM}/saida/personagem.blend1" "${BONECA_DIR:-$PASTA_PERSONAGEM}/saida/personagem.blend"
if [[ "${KK_PUBLICAR:-1}" == 1 ]]; then
    "$PYTHON_PERSONAGEM" "$PASTA_PERSONAGEM/catalogo.py"
fi
