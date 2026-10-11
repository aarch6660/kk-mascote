#!/usr/bin/env python3
"""Captura expressões do mascote real em Xvnc privado e compõe pranchas."""
import json
import os
import pathlib
import select
import shutil
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCIAS = ROOT / "evidencias" / "anime-2026-10-09"
CAPTURAS = EVIDENCIAS / "capturas-anime"
PRANCHAS = EVIDENCIAS / "pranchas-anime"
BONECAS = ["chika-haruno", "sawai-hinata", "mizuno-ayaka"]
ROTULOS = [
    ("Gargalhada", "Gargalhada"),
    ("Espanto", "Espanto"),
    ("Encantada", "Encantada"),
    ("Pânico cômico", "Pânico cômico"),
    ("Birra", "Birra"),
    ("Choro dramático", "Choro dramático"),
    ("Vergonha fofa", "Vergonha fofa"),
    ("Orgulho", "Orgulho"),
    ("extra-estrelas", "Extra: estrelas"),
    ("extra-interrogacao", "Extra: interrogação"),
    ("extra-desanimo", "Extra: desânimo"),
]


def executar_godot(destino: pathlib.Path, cache: pathlib.Path) -> str:
    servidor = None
    leitura, escrita = os.pipe()
    try:
        with tempfile.TemporaryDirectory(prefix="kk-anime-xvnc-") as tmp:
            tmp = pathlib.Path(tmp)
            capturas_tmp = tmp / "capturas"
            capturas_tmp.mkdir()
            with (tmp / "xvnc.log").open("w") as log:
                servidor = subprocess.Popen(
                    ["Xvnc", "-displayfd", str(escrita), "-geometry", "1920x1080", "-depth", "24",
                     "-localhost", "-SecurityTypes", "None", "-rfbunixpath", str(tmp / "vnc.sock"),
                     "-rfbport", "0", "-nolisten", "tcp"],
                    pass_fds=(escrita,), stdout=log, stderr=subprocess.STDOUT,
                )
            os.close(escrita)
            escrita = -1
            if not select.select([leitura], [], [], 15)[0]:
                raise RuntimeError("Xvnc não iniciou dentro de 15 s")
            numero = os.read(leitura, 64).decode().strip()
            if not numero.isdigit():
                raise RuntimeError("Xvnc retornou display inválido: " + repr(numero))
            env = dict(os.environ)
            env.update({
                "DISPLAY": ":" + numero,
                "KK_ANIME_VISUAL": str(capturas_tmp),
                "KK_ANIME_CACHE": str(cache),
                "MASCOTE_RETRATO": "0",
                "MASCOTE_PERFIL": "0",
                "MASCOTE_RUNTIME": "",
                "GODOT_SILENCE_ROOT_WARNING": "1",
            })
            env.pop("WAYLAND_DISPLAY", None)
            godot = env.get("GODOT", str(pathlib.Path.home() / ".local/opt/godot/godot"))
            comando = [godot, "--display-driver", "x11", "--rendering-method", "gl_compatibility",
                       "--audio-driver", "Dummy", "--path", str(ROOT), "--script", "testes/expressoes_anime_visual.gd"]
            log_path = EVIDENCIAS / "expressoes-anime-visual-godot.log"
            with log_path.open("w") as log:
                try:
                    subprocess.run(comando, env=env, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
                except subprocess.TimeoutExpired as exc:
                    raise RuntimeError("Godot passou de 180 s; consulte " + str(log_path)) from exc
            texto = log_path.read_text(errors="replace")
            if "SCRIPT ERROR:" in texto or "ERROR:" in texto:
                raise RuntimeError("Godot registrou erro; consulte " + str(log_path))
            linhas = [linha for linha in texto.splitlines() if linha.lstrip().startswith("{") and '"passou"' in linha]
            if not linhas:
                raise RuntimeError("Godot não imprimiu resultado do teste; consulte " + str(log_path))
            resultado = json.loads(linhas[-1])
            if not resultado.get("passou"):
                raise RuntimeError("Falha no ensaio: " + json.dumps(resultado, ensure_ascii=False))
            if resultado.get("capturas") != len(BONECAS) * len(ROTULOS):
                raise RuntimeError("Quantidade de capturas inesperada: " + str(resultado.get("capturas")))
            arquivos = list(capturas_tmp.glob("*.png"))
            if len(arquivos) != len(BONECAS) * len(ROTULOS):
                raise RuntimeError(f"Número de arquivos inesperado: {len(arquivos)}")
            for arquivo in arquivos:
                shutil.copy2(arquivo, destino / arquivo.name)
            return texto
    finally:
        os.close(leitura)
        if escrita >= 0:
            os.close(escrita)
        if servidor is not None:
            servidor.terminate()
            try:
                servidor.wait(timeout=5)
            except subprocess.TimeoutExpired:
                servidor.kill()
                servidor.wait()


def compor_pranchas() -> None:
    PRANCHAS.mkdir(parents=True, exist_ok=True)
    for boneca in BONECAS:
        args = ["montage", "-background", "#151923", "-fill", "white", "-font", "DejaVu-Sans",
                "-pointsize", "22", "-tile", "4x3", "-geometry", "360x360+12+12"]
        for arquivo, rotulo in ROTULOS:
            caminho = CAPTURAS / f"{boneca}-{arquivo}.png"
            if not caminho.is_file():
                raise RuntimeError("Captura ausente: " + str(caminho))
            args.extend(["-label", rotulo, str(caminho)])
        saida = PRANCHAS / f"{boneca}.png"
        args.append(str(saida))
        subprocess.run(args, check=True, timeout=60)
        dimensoes = subprocess.run(["identify", "-format", "%wx%h", str(saida)], check=True,
                                   capture_output=True, text=True).stdout.strip()
        print(f"Prancha {boneca}: {dimensoes} ({saida})")


def main() -> None:
    CAPTURAS.mkdir(parents=True, exist_ok=True)
    EVIDENCIAS.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="kk-anime-cache-") as tmp:
        cache = pathlib.Path(tmp) / "kk-mascote-privado.json"
        executar_godot(CAPTURAS, cache)
    compor_pranchas()
    print((EVIDENCIAS / "expressoes-anime-visual-godot.log").read_text(errors="replace").splitlines()[-1])


if __name__ == "__main__":
    main()
