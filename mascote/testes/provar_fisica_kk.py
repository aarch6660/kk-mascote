#!/usr/bin/env python3
"""Prova vestida em Xvnc privado, sem IPC ou preferências da instância real."""
import os
import pathlib
import select
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "evidencias/corpo-fisica-2026-10-09/visual"

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    server = None
    read_fd, write_fd = os.pipe()
    try:
        with tempfile.TemporaryDirectory(prefix="kk-fisica-visual-") as temp:
            with (OUT / "xvnc.log").open("w") as log:
                server = subprocess.Popen(
                    ["Xvnc", "-displayfd", str(write_fd), "-geometry", "1920x1080", "-depth", "24",
                     "-localhost", "-SecurityTypes", "None", "-rfbunixpath", temp + "/vnc.sock",
                     "-rfbport", "0", "-nolisten", "tcp"], pass_fds=(write_fd,), stdout=log, stderr=subprocess.STDOUT)
            os.close(write_fd)
            write_fd = None
            if not select.select([read_fd], [], [], 15)[0]:
                raise RuntimeError("Xvnc não iniciou")
            number = os.read(read_fd, 64).decode().strip()
            if not number.isdigit():
                raise RuntimeError("Display inválido")
            env = dict(os.environ, DISPLAY=":" + number, KK_FISICA_VISUAL=str(OUT),
                       KK_FISICA_CACHE=temp + "/cache.json", MASCOTE_RUNTIME="", MASCOTE_RETRATO="0", MASCOTE_PERFIL="0")
            env.pop("WAYLAND_DISPLAY", None)
            godot = env.get("GODOT", str(pathlib.Path.home() / ".local/opt/godot/godot"))
            with (OUT / "godot.log").open("w") as log:
                subprocess.run([godot, "--display-driver", "x11", "--rendering-method", "gl_compatibility",
                                "--audio-driver", "Dummy", "--path", str(ROOT), "--script", "testes/fisica_kk_visual.gd"],
                               env=env, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=120)
            text = (OUT / "godot.log").read_text()
            if "ERROR:" in text:
                raise RuntimeError("Erro no Godot; consulte " + str(OUT / "godot.log"))
            for char in ("chika-haruno", "mizuno-ayaka", "sawai-hinata"):
                args = ["montage", "-background", "#18202a", "-fill", "white", "-font", "DejaVu-Sans", "-pointsize", "20",
                        "-tile", "3x1", "-geometry", "400x480+8+8"]
                for state, label in (("base", "Pose original"), ("movimento", "Conversa e giro"), ("repouso", "Depois do movimento")):
                    args += ["-label", label, str(OUT / (char + "-" + state + ".png"))]
                subprocess.run(args + [str(OUT / (char + "-prancha.png"))], check=True)
            print("9 capturas vestidas; " + str(OUT / "visual.json"))
    finally:
        os.close(read_fd)
        if write_fd is not None:
            os.close(write_fd)
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()

if __name__ == "__main__":
    main()
