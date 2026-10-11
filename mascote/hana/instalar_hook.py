#!/usr/bin/env python3
"""Instala uma única linha autorizada no bashrc, preservando o backup inicial."""
from pathlib import Path
import shutil

LINHA = "source ~/Games/kk-mascote/mascote/hana/shell-hook.bash"


def instalar(pasta=None):
    pasta = Path(pasta) if pasta is not None else Path.home()
    rc = pasta / ".bashrc"
    antes = rc.read_text() if rc.exists() else ""
    if LINHA in [linha.strip() for linha in antes.splitlines()]:
        return False
    backup = pasta / ".bashrc.antes-hana"
    if not backup.exists():
        if rc.exists():
            shutil.copy2(rc, backup)
        else:
            backup.write_text("")
    with rc.open("a") as f:
        f.write(("\n" if antes and not antes.endswith("\n") else "") + LINHA + "\n")
    return True


if __name__ == "__main__":
    print("Hook instalado." if instalar() else "Hook já instalado; nenhuma duplicação.")
