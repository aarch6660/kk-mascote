#!/usr/bin/env python3
"""Extrai as vozes curtas originais (pacote cotidiano adm) de cada boneca, por personalidade.

    ~/Games/samabake-mascote/.venv/bin/python mascote/vozes/extrair.py [boneca-id ...]

Lê bonecas/<id>/card.json (Parameter.personality), abre sound/data/pcm/cNN/adm/00.unity3d
em leitura, exporta só os clipes listados em vozes/categorias_cNN.json (nunca a pasta h/,
nem clipes h_*) para bonecas/<id>/vozes/*.ogg e grava bonecas/<id>/vozes/vozes.json:
{categoria: [{arquivo, texto, dur, passo, envoltoria}]}. A envoltória RMS move a boca.
Personalidade sem categorias_cNN.json: a boneca fica sem vozes do jogo (aviso, sem erro).
"""
import os
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import UnityPy

AQUI = Path(__file__).resolve().parent
PROJETO = AQUI.parent.parent
JOGO = Path(os.environ.get("KK_JOGO") or Path.home()/"Downloads/Koikatsu.Party/Koikatsu Party")/"abdata"
PASSO = 0.02


def envoltoria(wav):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", str(wav), "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    janela = int(16000 * PASSO)
    n = max(1, len(a) // janela)
    rms = np.sqrt(np.mean(a[: n * janela].reshape(n, janela) ** 2, axis=1))
    pico = float(rms.max()) or 1.0
    return [round(float(v) / pico, 3) for v in rms], len(a) / 16000


def extrair(boneca):
    pasta = PROJETO / "bonecas" / boneca
    pers = int(json.loads((pasta / "card.json").read_text())["Parameter"]["personality"])
    cod = f"{pers:02d}"
    cats_arq = AQUI / f"categorias_c{cod}.json"
    if not cats_arq.exists():
        print(f"{boneca}: personalidade {cod} sem categorias revisadas; sem vozes do jogo")
        return
    cats = json.loads(cats_arq.read_text())
    textos = json.loads((AQUI / f"transcricoes_c{cod}.json").read_text())
    quero = {c for lista in cats.values() for c in lista}
    if any(c.startswith("h_") or not c.startswith("adm_") for c in quero):
        raise ValueError("só clipes cotidianos adm_* são permitidos")
    bundle = JOGO / f"sound/data/pcm/c{cod}/adm/00.unity3d"
    env = UnityPy.load(str(bundle))
    saida = pasta / "vozes"
    saida.mkdir(exist_ok=True)
    feitos = {}
    with tempfile.TemporaryDirectory() as tmp:
        for o in env.objects:
            if o.type.name != "AudioClip" or o.peek_name() not in quero:
                continue
            nome = o.peek_name()
            for _, dados in o.read().samples.items():
                wav = Path(tmp) / (nome + ".wav")
                wav.write_bytes(dados)
                ogg = saida / (nome + ".ogg")
                subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-i", str(wav), "-ac", "1", "-c:a", "libvorbis", "-q:a", "4", str(ogg)], check=True)
                env_rms, dur = envoltoria(wav)
                feitos[nome] = {"arquivo": ogg.name, "texto": textos.get(nome, {}).get("texto", ""),
                                "dur": round(dur, 3), "passo": PASSO, "envoltoria": env_rms}
                break
    faltando = quero - feitos.keys()
    if faltando:
        raise ValueError(f"{boneca}: clipes ausentes no pacote: {sorted(faltando)}")
    catalogo = {cat: [feitos[c] for c in lista] for cat, lista in cats.items()}
    catalogo["_origem"] = {"personalidade": pers, "pacote": str(bundle.relative_to(JOGO))}
    (saida / "vozes.json").write_text(json.dumps(catalogo, ensure_ascii=False) + "\n")
    print(f"{boneca}: c{cod}, {len(feitos)} vozes em {sum(1 for v in catalogo.values() if isinstance(v, list) and v)} categorias")


if __name__ == "__main__":
    ids = sys.argv[1:] or [b["id"] for b in json.loads((PROJETO / "bonecas/catalogo.json").read_text())]
    for b in ids:
        extrair(b)
