#!/usr/bin/env python3
"""Gera WAV e tempos de palavras usando a instalação existente de edge-tts."""
import asyncio
import array
import html
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import wave

VOICE = os.environ.get('MASCOTE_TTS_VOICE', 'pt-BR-FranciscaNeural').strip() or 'pt-BR-FranciscaNeural'
STEP = 0.02

def analisar(wav_path):
    with wave.open(str(wav_path), 'rb') as wav:
        assert wav.getnchannels() == 1 and wav.getsampwidth() == 2
        rate = wav.getframerate()
        samples = array.array('h', wav.readframes(wav.getnframes()))
        if sys.byteorder != 'little': samples.byteswap()
    size = round(rate * STEP)
    envelope = []
    for i in range(0, len(samples), size):
        block = samples[i:i+size]
        rms = math.sqrt(sum(x*x for x in block)/len(block))/32768
        envelope.append(round(min(1, max(0, (rms-0.006)*12)), 4))
    return len(samples)/rate, envelope

def mapear(texto, boundaries):
    words = list(re.finditer(r'\w+', texto, re.UNICODE))
    result = []
    cursor = 0
    for boundary in boundaries:
        value = html.unescape(boundary['text'])
        match = re.search(re.escape(value), texto[cursor:], re.IGNORECASE)
        if match:
            start = cursor+match.start()
            end = cursor+match.end()
        else:
            remaining = [w for w in words if w.end() > cursor]
            if not remaining: break
            start, end = remaining[0].span()
        cursor = end
        result.append({'inicio': boundary['offset']/10_000_000,
                       'fim': (boundary['offset']+boundary['duration'])/10_000_000,
                       'de': start, 'ate': end})
    return result

async def sintetizar(texto, arquivo):
    import edge_tts
    boundaries = []
    mp3 = arquivo.with_suffix('.mp3')
    try:
        with mp3.open('wb') as output:
            os.chmod(mp3, 0o600)
            async for chunk in edge_tts.Communicate(texto, VOICE, boundary='WordBoundary',
                rate=os.environ.get('MASCOTE_TTS_RATE', '+0%'),
                pitch=os.environ.get('MASCOTE_TTS_PITCH', '+0Hz')).stream():
                if chunk['type'] == 'audio': output.write(chunk['data'])
                elif chunk['type'] == 'WordBoundary': boundaries.append(chunk)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(mp3), '-ac', '1',
                        '-ar', '24000', '-c:a', 'pcm_s16le', str(arquivo)], check=True, timeout=20)
        os.chmod(arquivo, 0o600)
        duration, envelope = analisar(arquivo)
        words = mapear(texto, boundaries)
        if not words or duration <= 0: raise RuntimeError('Áudio sem tempos de palavras.')
        return {'arquivo': arquivo.name, 'voz': VOICE, 'duracao': duration,
                'passo': STEP, 'envoltoria': envelope, 'palavras': words}
    finally:
        mp3.unlink(missing_ok=True)

if __name__ == '__main__':
    data = json.load(sys.stdin)
    print(json.dumps(asyncio.run(asyncio.wait_for(sintetizar(data['texto'], Path(data['arquivo'])), 45)), ensure_ascii=False))
