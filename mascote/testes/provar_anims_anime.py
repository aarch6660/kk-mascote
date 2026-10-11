#!/usr/bin/env python3
"""Prova de poses anime do app real em Xvnc/cache privados; não importa recursos."""
import hashlib
import json
import os
import pathlib
import select
import struct
import subprocess
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent
EVIDENCIAS = PROJECT / "animacoes" / "evidencias"
CAPTURAS = EVIDENCIAS / "anims-anime"
METADADOS = EVIDENCIAS / "extrair_anime_resultado.json"
RELATORIO = EVIDENCIAS / "anims_anime_validacao.json"
GODOT = os.environ.get("GODOT", str(pathlib.Path.home() / ".local/opt/godot/godot"))


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            digest.update(bloco)
    return digest.hexdigest()


def registrar(relatorio):
    RELATORIO.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n")


def dimensoes_png(path):
    dados = path.read_bytes()[:24]
    if len(dados) < 24 or dados[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"PNG inválido: {path}")
    return struct.unpack(">II", dados[16:24])


def main():
    EVIDENCIAS.mkdir(parents=True, exist_ok=True)
    CAPTURAS.mkdir(parents=True, exist_ok=True)
    fontes = json.loads(METADADOS.read_text())
    nomes_esperados = [item["name"] for item in fontes["clips"]]
    relatorio = {
        "status": "iniciando",
        "capturas_3_4_fullbody": [],
        "fonte_extracao": str(METADADOS.relative_to(PROJECT)),
        "clips": fontes["clips"],
        "grade": {"bonecas": ["chika-haruno", "sawai-hinata", "mizuno-ayaka"],
                  "fracoes": [0.0, 0.25, 0.5, 0.75, 0.99],
                  "ossos": ["cf_j_head", "cf_j_hips", "cf_j_hand_L", "cf_j_hand_R", "cf_j_foot_L", "cf_j_foot_R"],
                  "capturas": "12 poses da Chika, vista de três quartos, SubViewport do app"},
        "importacao": "não executada por este runner; usar os recursos já importados pelo responsável",
    }
    servidor = None
    r, w = os.pipe()
    tmp = None
    try:
        tmp = tempfile.TemporaryDirectory(prefix="kk-anims-anime-")
        temp = pathlib.Path(tmp.name)
        home = temp / "home"
        home.mkdir()
        for nome in ("config", "cache", "data", "runtime"):
            (temp / nome).mkdir()
        with (temp / "xvnc.log").open("w") as xvnc_log:
            servidor = subprocess.Popen(
                ["Xvnc", "-displayfd", str(w), "-geometry", "1920x1080", "-depth", "24",
                 "-localhost", "-SecurityTypes", "None", "-rfbunixpath", str(temp / "vnc.sock"),
                 "-rfbport", "0", "-nolisten", "tcp"],
                pass_fds=(w,), stdout=xvnc_log, stderr=subprocess.STDOUT)
            os.close(w)
            w = -1
            if not select.select([r], [], [], 15)[0]:
                raise RuntimeError("Xvnc privado não iniciou")
            display = os.read(r, 64).decode().strip()
            if not display.isdigit():
                raise RuntimeError(f"Xvnc retornou display inválido: {display!r}")

        env = dict(os.environ)
        env.update({
            "DISPLAY": ":" + display,
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(temp / "config"),
            "XDG_CACHE_HOME": str(temp / "cache"),
            "XDG_DATA_HOME": str(temp / "data"),
            "KK_PROVA_RETRATO": str(CAPTURAS),
            "KK_PROVA_CACHE": str(temp / "cache.json"),
            "MASCOTE_PROVA": "1",
            "MASCOTE_RETRATO": "0",
            "MASCOTE_RUNTIME": "",
        })
        env.pop("WAYLAND_DISPLAY", None)
        log_path = CAPTURAS / "godot.log"
        with log_path.open("w") as log:
            processo = subprocess.run(
                [GODOT, "--display-driver", "x11", "--rendering-method", "gl_compatibility",
                 "--audio-driver", "Dummy", "--path", str(ROOT), "--script", "testes/anims_anime.gd"],
                env=env, stdout=log, stderr=subprocess.STDOUT, check=False, timeout=240)
        resultado_path = CAPTURAS / "resultado_godot.json"
        if resultado_path.exists():
            resultado_godot = json.loads(resultado_path.read_text())
        else:
            resultado_godot = None
        if resultado_godot is not None:
            relatorio["resultado_godot"] = resultado_godot
        capturas = []
        for nome in nomes_esperados:
            imagem = CAPTURAS / f"{nome}.png"
            if not imagem.is_file():
                continue
            largura, altura = dimensoes_png(imagem)
            capturas.append({"arquivo": str(imagem.relative_to(PROJECT)), "largura": largura,
                             "altura": altura, "sha256": sha256(imagem)})
        relatorio["capturas_3_4_fullbody"] = capturas
        relatorio["godot_exit_code"] = processo.returncode
        relatorio["godot_log"] = str(log_path.relative_to(PROJECT))
        pares_esperados = {(boneca, nome) for boneca in ("chika-haruno", "sawai-hinata", "mizuno-ayaka")
                           for nome in nomes_esperados}
        pares_resultado = set()
        grade_completa = False
        if resultado_godot:
            registros = resultado_godot.get("registros", [])
            pares_resultado = {(item.get("boneca"), item.get("clipe")) for item in registros if item.get("presente")}
            grade_completa = (
                pares_resultado == pares_esperados
                and all(len(item.get("amostras", [])) == 5 for item in registros if item.get("presente"))
                and resultado_godot.get("fracoes") == [0.0, 0.25, 0.5, 0.75, 0.99]
                and resultado_godot.get("ossos_verificados") == ["cf_j_head", "cf_j_hips", "cf_j_hand_L", "cf_j_hand_R", "cf_j_foot_L", "cf_j_foot_R"]
            )
        relatorio["grade_completa"] = grade_completa
        relatorio["passou"] = bool(
            processo.returncode == 0 and resultado_godot and resultado_godot.get("passou")
            and resultado_godot.get("runtime_vazio") is True
            and resultado_godot.get("prova_ativada") is True
            and grade_completa
            and len(capturas) == len(nomes_esperados)
            and {item["clipe"] for item in resultado_godot.get("registros", []) if item.get("boneca") == "chika-haruno"}
                == set(nomes_esperados)
        )
        relatorio["status"] = "concluida" if relatorio["passou"] else "falhou"
        registrar(relatorio)
        print(json.dumps({"status": relatorio["status"], "passou": relatorio["passou"],
                          "bonecas": 3, "clips": len(nomes_esperados), "capturas": len(capturas),
                          "relatorio": str(RELATORIO)}, ensure_ascii=False, indent=2))
        if not relatorio["passou"]:
            raise SystemExit(1)
    except (OSError, RuntimeError, subprocess.SubprocessError, ValueError, json.JSONDecodeError) as exc:
        relatorio["status"] = "falhou"
        relatorio["passou"] = False
        relatorio["erro_runner"] = str(exc)
        registrar(relatorio)
        raise
    finally:
        os.close(r)
        if w >= 0:
            os.close(w)
        if servidor is not None:
            servidor.terminate()
            try:
                servidor.wait(timeout=5)
            except subprocess.TimeoutExpired:
                servidor.kill()
                servidor.wait()
        if tmp is not None:
            tmp.cleanup()


if __name__ == "__main__":
    main()
