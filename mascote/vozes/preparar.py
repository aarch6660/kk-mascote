#!/usr/bin/env python3
"""Vozes do jogo de ponta a ponta, sem intervenção: transcrever → classificar → extrair.

    ~/Games/samabake-mascote/.venv/bin/python mascote/vozes/preparar.py [boneca-id ...]
    ... preparar.py --refazer cNN    # descarta categorias e transcrições dessa personalidade

Para cada boneca: se a personalidade ainda não tem categorias_cNN.json, exporta os clipes
cotidianos adm_* (nunca h/), transcreve com Whisper e classifica por regras (classificar.py).
Categorias existentes nunca são sobrescritas: revisar à mão é opcional e fica preservado.
O ambiente Whisper é criado na primeira vez em ~/.local/share/kk-mascote/whisper
(ou KK_WHISPER_VENV); o modelo é baixado pelo Hugging Face se não estiver em cache.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import UnityPy

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import classificar  # noqa: E402
import extrair  # noqa: E402

VENV = Path(os.environ.get("KK_WHISPER_VENV", Path.home() / ".local/share/kk-mascote/whisper"))


def ambiente_whisper():
    python = VENV / "bin/python"
    if python.exists() and subprocess.run([python, "-c", "import faster_whisper"], capture_output=True).returncode == 0:
        return python
    print("Criando ambiente Whisper em", VENV, "(só na primeira vez)...", flush=True)
    VENV.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["python3", "-m", "venv", str(VENV)], check=True)
    subprocess.run([python, "-m", "pip", "install", "-q", "faster-whisper"], check=True)
    # GPU NVIDIA opcional; sem ela o transcritor usa CPU.
    subprocess.run([python, "-m", "pip", "install", "-q", "nvidia-cublas-cu12", "nvidia-cudnn-cu12==9.*"])
    return python


def env_cuda(python):
    # Bibliotecas CUDA instaladas por pip ficam no site-packages do ambiente.
    libs = [str(p) for p in (VENV / "lib").glob("python*/site-packages/nvidia/*/lib")]
    env = dict(os.environ)
    env["LD_LIBRARY_PATH"] = ":".join(libs + [env.get("LD_LIBRARY_PATH", "")])
    return env


def transcrever(cod):
    bundle = extrair.JOGO / f"sound/data/pcm/c{cod}/adm/00.unity3d"
    if not bundle.exists():
        raise FileNotFoundError(f"pacote de vozes ausente: {bundle}")
    python = ambiente_whisper()
    with tempfile.TemporaryDirectory(prefix="kk-vozes-") as tmp:
        n = 0
        for o in UnityPy.load(str(bundle)).objects:
            if o.type.name != "AudioClip" or not o.peek_name().startswith("adm_"):
                continue
            for _, dados in o.read().samples.items():
                (Path(tmp) / (o.peek_name() + ".wav")).write_bytes(dados)
                n += 1
                break
        print(f"c{cod}: transcrevendo {n} clipes...", flush=True)
        saida = AQUI / f"transcricoes_c{cod}.json"
        subprocess.run([python, str(AQUI / "transcrever.py"), tmp, str(saida)], check=True, env=env_cuda(python))
    return json.loads(saida.read_text())


def preparar(boneca):
    pasta = extrair.PROJETO / "bonecas" / boneca
    cod = f"{int(json.loads((pasta / 'card.json').read_text())['Parameter']['personality']):02d}"
    cats = AQUI / f"categorias_c{cod}.json"
    if not cats.exists():
        trans = AQUI / f"transcricoes_c{cod}.json"
        textos = json.loads(trans.read_text()) if trans.exists() else transcrever(cod)
        categorias = classificar.classificar(textos)
        cats.write_text(json.dumps(categorias, ensure_ascii=False, indent=1) + "\n")
        print(f"c{cod}: categorias automáticas em {cats.name} (revisão manual opcional)")
    extrair.extrair(boneca)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--refazer"]:
        for c in args[1:]:
            for nome in (f"categorias_{c}.json", f"transcricoes_{c}.json"):
                (AQUI / nome).unlink(missing_ok=True)
        args = []
    for b in args or [b["id"] for b in json.loads((extrair.PROJETO / "bonecas/catalogo.json").read_text())]:
        preparar(b)
