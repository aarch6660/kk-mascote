#!/usr/bin/env python3
"""Respiração original de cada boneca, pelo estado Idle da tabela de respiração do próprio jogo.

    $PYTHON_PERSONAGEM mascote/vozes/extrair_ofegar.py [--nivel calma|ofegante] [boneca-id ...]

Lê h/list/*.unity3d (somente leitura): breath_00_00 diz quais linhas o estado Idle usa —
1º grupo = respiração calma 「すぅ……はぁ……」 (escolha do usuário em 2026-10-11, tocada alta);
2º grupo = ofegante 「はひ…はぁはぁ」 (excitação ≥ 90). As linhas vêm de personality_breath_cNN_00_00,
1ª coluna de experiência. Beijos/gemidos da mesma família h_ko_* nunca entram.
Grava bonecas/<id>/vozes/ofegar/*.ogg + ofegar.json (envoltória da boca).
"""
import json
import sys
import tempfile
from pathlib import Path

import UnityPy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extrair  # noqa: E402  (JOGO, PROJETO, envoltoria)

NIVEIS = {"calma": 0, "ofegante": 1}  # grupo do estado Idle em breath_00_00


def tabela(nome):
    for bundle in sorted((extrair.JOGO / "h/list").glob("*.unity3d")):
        for o in UnityPy.load(str(bundle)).objects:
            if o.type.name == "TextAsset" and o.peek_name() == nome:
                t = o.read().m_Script
                return t if isinstance(t, str) else t.decode("utf-8", "replace")
    raise FileNotFoundError(nome)


def linhas_idle(grupo):
    # breath_00_00, linha "Idle": após 4 campos, grupos de 7 [estados, ?, condição, ids, flag, limiar, ?].
    for linha in tabela("breath_00_00").splitlines():
        c = linha.split("\t")
        if len(c) > 1 and c[1] == "Idle":
            return [int(i) for i in c[4 + 7 * grupo + 3].split(",")]
    raise ValueError("breath_00_00 sem estado Idle")


def escolher(texto, ids):
    clipes = {}
    for linha in texto.splitlines():
        c = linha.split("\t")
        # id, estado, bundle, clipe, legenda, ... (primeira coluna de experiência)
        if len(c) > 4 and c[0].isdigit() and int(c[0]) in ids and c[3].startswith("h_ko_"):
            clipes.setdefault(c[3], (c[2], c[4]))
    return clipes


def extrair_boneca(boneca, nivel="calma"):
    pasta = extrair.PROJETO / "bonecas" / boneca
    cod = f"{int(json.loads((pasta / 'card.json').read_text())['Parameter']['personality']):02d}"
    clipes = escolher(tabela(f"personality_breath_c{cod}_00_00"), linhas_idle(NIVEIS[nivel]))
    if not clipes:
        raise ValueError(f"c{cod}: nenhuma respiração '{nivel}' na tabela")
    saida = pasta / "vozes/ofegar"
    if saida.exists():
        for velho in saida.glob("*.ogg"):
            velho.unlink()
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
         "_origem": {"personalidade": int(cod), "tabela": f"personality_breath_c{cod}_00_00",
                     "estado": "Idle", "nivel": nivel}},
        ensure_ascii=False) + "\n")
    print(f"{boneca}: c{cod}, {len(feitos)} loops de respiração ({nivel})")


if __name__ == "__main__":
    args = sys.argv[1:]
    nivel = "calma"
    if args[:1] == ["--nivel"]:
        nivel, args = args[1], args[2:]
    for b in args or [b["id"] for b in json.loads((extrair.PROJETO / "bonecas/catalogo.json").read_text())]:
        extrair_boneca(b, nivel)
