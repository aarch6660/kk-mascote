#!/usr/bin/env bash
# Primeira execução numa máquina nova: extrai do jogo (somente leitura) tudo o que é comum às bonecas.
# Depois disso, cada personagem entra com ./adicionar-boneca.sh card.png
set -euo pipefail
RAIZ="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON_PERSONAGEM:-$HOME/Games/samabake-mascote/.venv/bin/python}"
export PYTHON_PERSONAGEM="$PY"
mkdir -p "$RAIZ/bonecas"
echo "== Animações"
"$RAIZ/animacoes/montar_biblioteca.sh"
echo "== Graduação de cor e iluminação do editor"
"$PY" "$RAIZ/personagem/extrair_cor_kk.py"
echo "== Celular original"
"$PY" "$RAIZ/mascote/celular_jogo/extrair.py"
for app in mascote visualizador; do
    [[ -e "$RAIZ/$app/bonecas" ]] || ln -s ../bonecas "$RAIZ/$app/bonecas"
done
echo "Pronto. Próximo passo: ./adicionar-boneca.sh caminho/do/card.png"
