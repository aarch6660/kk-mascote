"""Contexto autorizado do desktop; consultas curtas, opcionais e sem captura de tela."""
import json
from fnmatch import fnmatchcase
import math
from pathlib import Path
import re
import shutil
import subprocess

TIMEOUT = 0.7
JANELAS_PROPRIAS = {"kk-mascote", "kk-mascote-chat"}
CATEGORIAS = Path(__file__).with_name("categorias_janela.json")


def categorizar(janela, tabela=None):
    """Regras em ordem; título é usado somente junto com uma classe autorizada."""
    if tabela is None:
        try:
            tabela = json.loads(CATEGORIAS.read_text())
        except (OSError, ValueError):
            tabela = []
    if not isinstance(tabela, list):
        return "outro"
    classe = str(janela.get("class", "")).casefold()
    titulo = str(janela.get("title", "")).casefold()
    for regra in tabela:
        try:
            if (any(fnmatchcase(classe, c.casefold()) for c in regra["classes"])
                    and (not regra.get("titulo") or re.search(regra["titulo"], titulo))):
                return regra["categoria"]
        except (KeyError, TypeError, re.error):
            continue
    return "outro"


def comando(args):
    try:
        r = subprocess.run(args, text=True, capture_output=True, timeout=TIMEOUT, check=True)
        return r.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def coletar(power=Path("/sys/class/power_supply")):
    janela = {}
    if shutil.which("hyprctl"):
        try:
            dados = json.loads(comando(["hyprctl", "-j", "activewindow"]))
            if isinstance(dados, dict) and dados.get("class") not in JANELAS_PROPRIAS:
                janela = {"class": str(dados.get("class", ""))[:200],
                          "title": str(dados.get("title", ""))[:500],
                          "fullscreen": bool(dados.get("fullscreen", False)),
                          "address": str(dados.get("address", "")), "pid": dados.get("pid", 0),
                          "at": dados.get("at", [0, 0]), "size": dados.get("size", [0, 0])}
                janela["categoria"] = categorizar(janela)
        except (ValueError, TypeError):
            pass
    musica = {}
    if shutil.which("playerctl"):
        # Separador de linha evita quebrar faixas/artistas que contenham tabs ou barras.
        linhas = comando(["playerctl", "metadata", "--format",
                          "{{status}}\n{{artist}}\n{{title}}"]).splitlines()
        if linhas and linhas[0] in ("Playing", "Paused", "Stopped"):
            musica = dict(status=linhas[0], artista=linhas[1][:300] if len(linhas)>1 else "",
                          faixa=linhas[2][:300] if len(linhas)>2 else "")
            bpm = comando(["playerctl", "metadata", "xesam:audioBPM"])
            try:
                valor = float(bpm)
                if math.isfinite(valor) and 40 <= valor <= 240:
                    musica["bpm"] = valor
            except ValueError:
                pass
    baterias = []
    for pasta in sorted(Path(power).glob("BAT*")):
        try:
            nivel = int((pasta / "capacity").read_text().strip())
            status = (pasta / "status").read_text().strip()
            if 0 <= nivel <= 100:
                baterias.append(dict(nome=pasta.name, nivel=nivel, status=status))
        except (OSError, ValueError):
            continue
    return dict(janela=janela, musica=musica, baterias=baterias)


def bateria_baixa(contexto):
    return any(b.get("nivel", 100) <= 15 and b.get("status") == "Discharging"
               for b in contexto.get("baterias", []))


def roupa(estado):
    """Roupa efetivamente carregada, sem inferir a coordenada apenas pelo horário."""
    atual = estado.get("roupa", {})
    nomes = {0: "uniforme", 5: "casual", 6: "pijama"}
    if not isinstance(atual, dict):
        return {}
    coordenada = atual.get("coordenada")
    if type(coordenada) is not int or coordenada not in nomes:
        return {}
    return dict(coordenada=coordenada, nome=nomes[coordenada],
                modo=estado.get("preferencias", {}).get("roupa_modo", "automatica"))


def eventos(anterior, atual):
    """Transições observáveis; bateria cheia exige carga anterior, não login."""
    anterior = anterior or {}
    saida = []
    if atual.get("janela") and atual.get("janela") != anterior.get("janela"):
        saida.append("janela")
    tocava = anterior.get("musica", {}).get("status") == "Playing"
    toca = atual.get("musica", {}).get("status") == "Playing"
    if toca != tocava:
        saida.append("musica_comecou" if toca else "musica_parou")
    if bateria_baixa(atual) and not bateria_baixa(anterior):
        saida.append("bateria_baixa")
    antes = {b["nome"]: b for b in anterior.get("baterias", [])}
    if any(b.get("nivel") == 100 and b.get("status") in ("Full", "Not charging")
           and antes.get(b["nome"], {}).get("status") == "Charging" for b in atual.get("baterias", [])):
        saida.append("bateria_cheia")
    return saida
