#!/usr/bin/env python3
"""Mede CPU do Godot por 30 s em cada estado, em Xvnc e HOME privados."""
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidencias/hana-etapa2"


def ticks(pid):
    campos = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
    return int(campos[11]) + int(campos[12])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rotulo = sys.argv[1]
    resultados = {}
    with tempfile.TemporaryDirectory(prefix="kk-consumo-") as tmp:
        r, w = os.pipe()
        servidor = subprocess.Popen(["Xvnc", "-displayfd", str(w), "-geometry", "1920x1080",
            "-depth", "24", "-localhost", "-SecurityTypes", "None", "-rfbunixpath", tmp + "/vnc.sock",
            "-rfbport", "0", "-nolisten", "tcp"], pass_fds=(w,), stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        os.close(w)
        processo = None
        try:
            if not select.select([r], [], [], 15)[0]:
                raise RuntimeError("Xvnc não iniciou")
            numero = os.read(r, 64).decode().strip()
            preferencias = json.loads((Path.home() / ".cache/forja/kk-mascote.json").read_text())
            # Mesma boneca/roupas/escala; enquadramento inteiro, sem gravar no cache real.
            preferencias.update(modo="passeio", fixa=True, posicao=[960, 1000])
            cache = Path(tmp) / ".cache/forja/kk-mascote.json"
            cache.parent.mkdir(parents=True)
            cache.write_text(json.dumps(preferencias))
            env = dict(os.environ, DISPLAY=":" + numero, HOME=tmp, MASCOTE_RUNTIME="", MASCOTE_CHAT=tmp + "/chat")
            env.pop("WAYLAND_DISPLAY", None)
            # Mesmo OpenGL/Intel do lançador real.
            env.update(DRI_PRIME="pci-0000_00_02_0", __GLX_VENDOR_LIBRARY_NAME="mesa")
            for chave in ("__NV_PRIME_RENDER_OFFLOAD", "__VK_LAYER_NV_optimus", "VK_LOADER_DRIVERS_SELECT"):
                env.pop(chave, None)
            if rotulo.startswith("antes"):
                env["KK_CONSUMO_BASELINE"] = str(OUT/"antes/mascote__mascote.gd")
            processo = subprocess.Popen([os.environ.get("GODOT", str(Path.home() / ".local/opt/godot/godot")),
                "--display-driver", "x11", "--rendering-method", "gl_compatibility", "--audio-driver", "Dummy",
                "--path", str(ROOT), "--script", "testes/consumo_hana.gd"], env=env,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            limite = threading.Timer(120, processo.terminate)
            limite.start()
            inicio = None
            with (OUT / f"consumo-{rotulo}.log").open("w") as log:
                for linha in processo.stdout:
                    log.write(linha)
                    log.flush()
                    if linha.startswith("MEDIR "):
                        inicio = (time.monotonic(), ticks(processo.pid))
                    if linha.startswith("FIM "):
                        fim = (time.monotonic(), ticks(processo.pid))
                        segundos = fim[0] - inicio[0]
                        resultados[linha.strip().split()[1]] = dict(segundos=segundos,
                            cpu_percent=100 * (fim[1] - inicio[1]) / os.sysconf("SC_CLK_TCK") / segundos)
                    if linha.startswith("ESTAT "):
                        resultados.setdefault("amostras",[]).append(json.loads(linha[len("ESTAT "):]))
            if processo.wait(timeout=5):
                raise RuntimeError("Godot falhou; consulte o log")
            if not {"parada", "falando"} <= set(resultados):
                raise RuntimeError("Medição incompleta")
            if "ERROR:" in (OUT / f"consumo-{rotulo}.log").read_text():
                raise RuntimeError("Medição inválida: erros do Godot")
        finally:
            if processo:
                limite.cancel()
            os.close(r)
            if processo and processo.poll() is None:
                processo.terminate()
                processo.wait(timeout=5)
            servidor.terminate()
            servidor.wait(timeout=5)
    (OUT / f"consumo-{rotulo}.json").write_text(json.dumps(resultados, indent=2) + "\n")
    print(json.dumps(resultados))


if __name__ == "__main__":
    main()
