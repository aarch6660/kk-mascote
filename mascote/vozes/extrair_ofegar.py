#!/usr/bin/env python3
"""Respiração ofegante original de cada boneca, pela tabela de respiração do próprio jogo.

    $PYTHON_PERSONAGEM mascote/vozes/extrair_ofegar.py [boneca-id ...]

Lê h/list/*.unity3d → personality_breath_cNN_00_00 (somente leitura) e escolhe as linhas cuja
legenda tem 「はぁはぁ」: os loops de respiração ofegante (família h_ko_*). Beijos e demais sons da
mesma família ficam de fora. Grava bonecas/<id>/vozes/ofegar/*.ogg + ofegar.json (envoltória da boca).
"""
import json
import sys
import tempfile
from pathlib import Path

import UnityPy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extrair  # noqa: E402  (JOGO, PROJETO, envoltoria)

MARCA = "はぁはぁ"


def tabela(cod):
    nome = f"personality_breath_c{cod}_00_00"
    for bundle in sorted((extrair.JOGO / "h/list").glob("*.unity3d")):
        for o in UnityPy.load(str(bundle)).objects:
            if o.type.name == "TextAsset" and o.peek_name() == nome:
                t = o.read().m_Script
                return t if isinstance(t, str) else t.decode("utf-8", "replace")
    raise FileNotFoundError(nome)


def escolher(texto):
    clipes = {}
    for linha in texto.splitlines():
        c = linha.split("\t")
        # id, estado, bundle, clipe, legenda, ... (primeira coluna de experiência)
        if len(c) > 4 and c[3].startswith("h_ko_") and MARCA in c[4]:
            clipes.setdefault(c[3], (c[2], c[4]))
    return clipes


def extrair_boneca(boneca):
    pasta = extrair.PROJETO / "bonecas" / boneca
    cod = f"{int(json.loads((pasta / 'card.json').read_text())['Parameter']['personality']):02d}"
    clipes = escolher(tabela(cod))
    if not clipes:
        raise ValueError(f"c{cod}: nenhuma respiração ofegante na tabela")
    saida = pasta / "vozes/ofegar"
    saida.mkdir(parents=True, exist_ok=True)
    feitos = []
    por_bundle = {}
    for nome, (bundle, legenda) in clipes.items():
        por_bundle.setdefault(bundle, {})[nome] = legenda
    with tempfile.TemporaryDirectory() as tmp:
        for bundle, nomes in por_bundle.items():
            for o in UnityPy.load(str(extrair.JOGO / bundle)).objects:
                if o.type.name != "AudioClip" or o.peek_name() not in nomes:
                    continue
                nome = o.peek_name()
                for _, dados in o.read().samples.items():
                    wav = Path(tmp) / (nome + ".wav")
                    wav.write_bytes(dados)
                    ogg = saida / (nome + ".ogg")
                    extrair.subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-i", str(wav), "-ac", "1", "-c:a",
                                            "libvorbis", "-q:a", "4", str(ogg)], check=True)
                    env, dur = extrair.envoltoria(wav)
                    feitos.append({"arquivo": "ofegar/" + ogg.name, "texto": nomes[nome], "dur": round(dur, 3),
                                   "passo": extrair.PASSO, "envoltoria": env})
                    break
    faltando = set(clipes) - {Path(f["arquivo"]).stem for f in feitos}
    if faltando:
        raise ValueError(f"{boneca}: clipes ausentes: {sorted(faltando)}")
    (pasta / "vozes/ofegar.json").write_text(json.dumps(
        {"clipes": sorted(feitos, key=lambda f: f["arquivo"]),
         "_origem": {"personalidade": int(cod), "tabela": f"personality_breath_c{cod}_00_00", "marca": MARCA}},
        ensure_ascii=False) + "\n")
    print(f"{boneca}: c{cod}, {len(feitos)} loops de respiração ofegante")


if __name__ == "__main__":
    ids = sys.argv[1:] or [b["id"] for b in json.loads((extrair.PROJETO / "bonecas/catalogo.json").read_text())]
    for b in ids:
        extrair_boneca(b)
