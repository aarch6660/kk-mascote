#!/usr/bin/env python3
"""Transcreve WAVs curtos com faster-whisper. Roda no ambiente Whisper criado por preparar.py.

    python transcrever.py <pasta_wav> <saida.json> [modelo]

Saída: {clipe: {texto, dur}}. Tenta GPU (CUDA) e cai para CPU int8 se não houver.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel

MODELO = "deepdml/faster-whisper-large-v3-turbo-ct2"


def audio(wav):
    # Decodifica com ffmpeg: o PyAV recente quebra o decode_audio do faster-whisper.
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", str(wav), "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def carregar(nome):
    try:
        modelo = WhisperModel(nome, device="cuda", compute_type="float16")
        list(modelo.transcribe(audio(WAVS[0]), language="ja")[0])  # falha cedo sem cuBLAS/cuDNN
        print("Whisper: GPU", flush=True)
        return modelo
    except Exception as exc:  # sem CUDA utilizável
        print("Whisper: CPU (" + str(exc).splitlines()[0][:80] + ")", flush=True)
        return WhisperModel(nome, device="cpu", compute_type="int8")


pasta, saida = Path(sys.argv[1]), Path(sys.argv[2])
WAVS = sorted(pasta.glob("*.wav"))
modelo = carregar(sys.argv[3] if len(sys.argv) > 3 else MODELO)
resultado = {}
for i, wav in enumerate(WAVS, 1):
    segmentos, info = modelo.transcribe(audio(wav), language="ja", beam_size=5, vad_filter=False)
    resultado[wav.stem] = {"texto": "".join(s.text for s in segmentos).strip(), "dur": round(info.duration, 2)}
    if i % 20 == 0 or i == len(WAVS):
        print(f"  {i}/{len(WAVS)}", flush=True)
saida.write_text(json.dumps(resultado, ensure_ascii=False, indent=1) + "\n")
