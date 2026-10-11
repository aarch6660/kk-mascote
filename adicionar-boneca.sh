#!/usr/bin/env bash
set -euo pipefail
RAIZ_BONECAS="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec "${PYTHON_PERSONAGEM:-$HOME/Games/samabake-mascote/.venv/bin/python}" "$RAIZ_BONECAS/personagem/adicionar.py" "$@"
