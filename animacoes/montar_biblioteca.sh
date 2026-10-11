#!/usr/bin/env bash
# Monta a biblioteca de animações do mascote a partir do jogo (somente leitura), do zero.
# selecao.json já lista todos os clipes do mascote: extrair.py exporta os cotidianos e extrair_espera_h.py
# a espera em pé de h/ (só a pose sem toque). Os scripts extrair_idles/gestos_hana/anime serviram para
# escolher e acrescentar clipes à seleção; refazê-los dá a mesma animação (só metadados diferem).
set -euo pipefail
AQUI="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON_PERSONAGEM:-$HOME/Games/samabake-mascote/.venv/bin/python}"
cd -- "$AQUI"
"$PY" extrair.py
"$PY" extrair_espera_h.py
for destino in ../mascote/anims ../visualizador/anims; do
    mkdir -p -- "$destino"
    for glb in exportados/*.glb; do
        case "$(basename -- "$glb")" in parada_espera_h_m.glb|parada_espera_h_l.glb) continue ;; esac
        cp -u -- "$glb" "$destino/"
    done
done
echo "Biblioteca: $(ls ../mascote/anims/*.glb | wc -l) clipes em mascote/anims"
