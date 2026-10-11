#!/usr/bin/env python3
"""Faz a boneca ativa ofegar agora, por N segundos (padrão 30): python3 mascote/ofegar.py [segundos]."""
import sys
import time

import hypr_bridge as bridge
import falar

segundos = float(sys.argv[1]) if len(sys.argv) > 1 else 30.0
bridge.atomic_json(falar.RUNTIME / "comando.json", {"ofegar": segundos, "nonce": time.time_ns()})
print("ofegar:", segundos, "s")
