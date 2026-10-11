#!/usr/bin/env python3
"""Prova visual em Xvnc privado, sem tocar no cache do usuário."""
import json
import os
from pathlib import Path
import select
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/"evidencias/hana-etapa2/previa"
NOMES = ["gesto_ajeitar_cabelo","gesto_mao_boca","gesto_olhar_longe","gesto_maos_juntas","gesto_reverencia","assistindo"]


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    r,w = os.pipe()
    with tempfile.TemporaryDirectory(prefix="kk-previa-hana-") as tmp:
        servidor = subprocess.Popen(["Xvnc","-displayfd",str(w),"-geometry","1920x1080","-depth","24","-localhost",
            "-SecurityTypes","None","-rfbunixpath",tmp+"/vnc.sock","-rfbport","0","-nolisten","tcp"],
            pass_fds=(w,),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        os.close(w)
        try:
            if not select.select([r],[],[],15)[0]: raise RuntimeError("Xvnc não iniciou")
            numero = os.read(r,64).decode().strip()
            env = dict(os.environ, DISPLAY=":"+numero, KK_PROVA_RETRATO=str(OUT), KK_PROVA_CACHE=tmp+"/cache.json",
                MASCOTE_RUNTIME="", MASCOTE_CHAT=tmp+"/chat", MASCOTE_RETRATO="0", MASCOTE_PERFIL="0")
            env.pop("WAYLAND_DISPLAY",None)
            with (OUT/"godot.log").open("w") as log:
                subprocess.run([os.environ.get("GODOT",str(Path.home()/".local/opt/godot/godot")),"--display-driver","x11",
                    "--rendering-method","gl_compatibility","--audio-driver","Dummy","--path",str(ROOT),
                    "--script","testes/previa_hana.gd"],env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
            if "ERROR:" in (OUT/"godot.log").read_text(): raise RuntimeError("Godot apresentou erro; consulte o log")
        finally:
            os.close(r)
            servidor.terminate(); servidor.wait(timeout=5)
    fonte = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans.ttf",18)
    folha = Image.new("RGB",(1680,1590),(22,24,31))
    d = ImageDraw.Draw(folha)
    for i,nome in enumerate(NOMES):
        x,y = (i%2)*840,(i//2)*530
        d.text((x+8,y+6),nome,font=fonte,fill="white")
        for k in range(3):
            imagem = Image.open(OUT/f"{nome}_{k}.png").convert("RGBA")
            # Fundo neutro por trás da transparência da janela.
            fundo = Image.new("RGBA",imagem.size,(28,31,39,255)); fundo.alpha_composite(imagem)
            folha.paste(fundo.convert("RGB").resize((280,500)),(x+k*280,y+30))
    folha.save(OUT/"prancha.jpg",quality=92)
    (OUT/"resultado.json").write_text(json.dumps(dict(passou=True,clipes=NOMES,capturas=18),indent=2)+"\n")


if __name__ == "__main__": main()
