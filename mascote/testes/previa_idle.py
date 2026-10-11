#!/usr/bin/env python3
"""Roda previa_idle.gd em Xvnc privado e monta pranchas em animacoes/candidatas/previa/."""
import os, pathlib, select, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
CAND = ROOT.parent / "animacoes" / "candidatas"
OUT = CAND / "previa"


def prancha():
    from PIL import Image, ImageDraw, ImageFont
    fonte = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans.ttf", 18) if pathlib.Path("/usr/share/fonts/TTF/DejaVuSans.ttf").exists() else ImageFont.load_default()
    nomes = sorted({p.name.rsplit("_", 1)[0] for p in OUT.glob("*_[0-9].png")}, key=lambda n: (n != "idle_em_pe", n))
    porfolha = 6
    for f in range(0, len(nomes), porfolha):
        parte = nomes[f:f + porfolha]
        w, h = 280, 500
        folha = Image.new("RGB", (w * 3 * 2, (h + 30) * ((len(parte) + 1) // 2)), (20, 22, 30))
        d = ImageDraw.Draw(folha)
        for i, nome in enumerate(parte):
            x0, y0 = (i % 2) * w * 3, (i // 2) * (h + 30)
            d.text((x0 + 8, y0 + 5), nome, font=fonte, fill="white")
            for k in range(3):
                p = OUT / f"{nome}_{k}.png"
                if p.exists():
                    folha.paste(Image.open(p).convert("RGB").resize((w, h)), (x0 + k * w, y0 + 30))
        folha.save(OUT / f"prancha_{f // porfolha + 1:02d}.jpg", quality=88)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    r, w = os.pipe()
    servidor = None
    try:
        with tempfile.TemporaryDirectory(prefix="kk-previa-idle-") as t:
            servidor = subprocess.Popen(["Xvnc", "-displayfd", str(w), "-geometry", "1920x1080", "-depth", "24", "-localhost",
                                         "-SecurityTypes", "None", "-rfbunixpath", t + "/vnc.sock", "-rfbport", "0", "-nolisten", "tcp"],
                                        pass_fds=(w,), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.close(w); w = None
            if not select.select([r], [], [], 15)[0]:
                raise RuntimeError("Xvnc não iniciou")
            numero = os.read(r, 64).decode().strip()
            env = dict(os.environ, DISPLAY=":" + numero, KK_PROVA_RETRATO=str(OUT), KK_CANDIDATAS=str(CAND),
                       MASCOTE_RETRATO="0", MASCOTE_RUNTIME="")
            env.pop("WAYLAND_DISPLAY", None)
            with (OUT / "godot.log").open("w") as log:
                subprocess.run([os.environ.get("GODOT", str(pathlib.Path.home() / ".local/opt/godot/godot")),
                                "--display-driver", "x11", "--rendering-method", "gl_compatibility", "--audio-driver", "Dummy",
                                "--path", str(ROOT), "--script", "testes/previa_idle.gd"],
                               env=env, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=300)
    finally:
        os.close(r)
        if w is not None:
            os.close(w)
        if servidor is not None:
            servidor.terminate()
            servidor.wait(timeout=5)
    prancha()


if __name__ == "__main__":
    main()
