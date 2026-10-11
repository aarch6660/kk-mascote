#!/usr/bin/env python3
"""Classifica as vozes cotidianas (adm_*) de uma personalidade pelo texto transcrito (Whisper).

Entrada: vozes/transcricoes_cNN.json  {clipe: {texto, dur}}
Saída:   vozes/categorias_cNN.json    {categoria: [clipes]}  — revisar à mão depois.
Exclui alucinações típicas do Whisper em sons sem fala e clipes longos (esforço/choro).
"""
import json, re, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REGRAS = [  # (categoria, regex, duração máxima)
    ("choque",    r"^((えぇ|ええ)(?!ー?い)|えー[!?！？]|うそ|嘘|マジ|びっくり|はぁっ?[!?！？])", 2.6),
    ("surpresa",  r"^(え[!?！？]|えっ|あっ|わっ|ひゃ|うわ|ああ[!！]|おお[!！]|あ[!！])", 1.8),
    ("duvida",    r"^.{1,8}[?？]$", 2.6),
    ("alegria",   r"(ふふ|うふ|んふ|えへ|あはは|はっはっ|くすくす|ぷぷ|へへ|イエ|いえーい|わーい|やった|うれしい|嬉しい)", 2.6),
    ("pensando",  r"(うーん|うーむ|んー|えーと|えっと|なるほど|そうなんだ|そっか|そうなるね|^ふーん)", 2.6),
    ("suspiro",   r"^(ふぅ|ふー|はぁ|はー(?!い))", 2.4),
    ("resmungo",  r"(^う+[。…、]?$|^むう|^むー|もう|困った|難しい|うう|ぶー|ちぇ)", 2.6),
    ("concordar", r"^(はい|うん|オッケー|いいよ|了解|よし)[!。！]*$", 1.6),
]


def classificar(transcricoes):
    saida = {c: [] for c, _, _ in REGRAS}
    for clipe, info in sorted(transcricoes.items()):
        t = re.sub(r"\s+", "", info["texto"])
        # Frases completas que não funcionam como reação genérica.
        if not t or info["dur"] < 0.4 or re.search(r"ご視聴|チャンネル|惜しい|もうちょっと|眠れ|元気|またね", t):
            continue
        for cat, rx, dmax in REGRAS:
            if info["dur"] <= dmax and re.search(rx, t):
                saida[cat].append(clipe)
                break
    return saida


if __name__ == "__main__":
    for c in sys.argv[1:]:
        tr = json.loads((AQUI / f"transcricoes_c{c}.json").read_text())
        cats = classificar(tr)
        (AQUI / f"categorias_c{c}.json").write_text(json.dumps(cats, ensure_ascii=False, indent=1) + "\n")
        print(f"== c{c}")
        for cat, clipes in cats.items():
            print(f"  {cat:10s}", " | ".join(f"{tr[k]['texto']}" for k in clipes))
