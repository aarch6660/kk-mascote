#!/usr/bin/env python3
"""Roda previa_celular.gd em Xvnc privado e monta prancha em evidencias/celular-jogo/."""
import os, pathlib, select, subprocess, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "evidencias/celular-jogo"
OUT.mkdir(parents=True, exist_ok=True)
r, w = os.pipe()
x = subprocess.Popen(["Xvnc", "-displayfd", str(w), "-geometry", "1280x800", "-depth", "24", "-localhost", "-SecurityTypes", "None", "-rfbport", "0", "-nolisten", "tcp"], pass_fds=(w,), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
os.close(w); select.select([r], [], [], 15); n = os.read(r, 64).decode().strip()
env = dict(os.environ, DISPLAY=":" + n, KK_PROVA_RETRATO=str(OUT), MASCOTE_RUNTIME=""); env.pop("WAYLAND_DISPLAY", None)
try:
    with (OUT / "godot.log").open("w") as log:
        subprocess.run([str(pathlib.Path.home() / ".local/opt/godot/godot"), "--display-driver", "x11", "--rendering-method", "gl_compatibility", "--audio-driver", "Dummy", "--path", str(ROOT), "--script", "testes/" + os.environ.get("PREVIA", "previa_celular.gd")], env=env, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=240)
finally:
    x.terminate()
