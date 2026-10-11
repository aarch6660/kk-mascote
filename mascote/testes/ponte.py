#!/usr/bin/env python3
"""Contrato de entrada: vazio/menu, grab, estado vencido e PID reaproveitado."""
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import hypr_bridge as bridge

state = {"pid": 123, "timestamp": time.time(), "hidden": False,
         "hull": [[100,100],[140,100],[140,200],[100,200]],
         "menu": True, "menu_rect": [200,100,180,104]}
cases = {
    "silhueta": bridge.accepts_mouse(state,120,150,123),
    "vazio": not bridge.accepts_mouse(state,50,150,123),
    "menu": bridge.accepts_mouse(state,220,150,123),
    "vazio_entre_menu_personagem": not bridge.accepts_mouse(state,170,150,123),
    "menu_fechado": not bridge.accepts_mouse(dict(state,menu=False),220,150,123),
    "oculta": not bridge.accepts_mouse(dict(state,hidden=True),120,150,123),
    "vencido": not bridge.accepts_mouse(dict(state,timestamp=time.time()-3),120,150,123),
    "outro_pid": not bridge.accepts_mouse(state,120,150,456),
    "grab_ate_soltar": bridge.accepts_mouse(dict(state,pressionada=True),50,150,123),
    "sem_status": not bridge.accepts_mouse({},120,150,123),
}
result = {"passou": all(cases.values()), "casos": cases}
(ROOT/'evidencias/headless-ponte.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,ensure_ascii=False))
sys.exit(0 if result['passou'] else 1)
