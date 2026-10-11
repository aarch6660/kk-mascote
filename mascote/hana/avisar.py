#!/usr/bin/env python3
"""Fila local persistente para scripts; não inicia o mascote nem chama modelos."""
import argparse
from pathlib import Path
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hana.memoria import DADOS, gravar_atomico, texto_valido


def enviar(texto, pasta=DADOS, motivo="evento:aviso", agora=None, **dados):
    if not texto_valido(texto, 1000):
        raise ValueError("O aviso deve ter de 1 a 1000 caracteres.")
    if motivo not in ("evento:aviso", "evento:crash", "evento:download"):
        raise ValueError("Motivo de aviso inválido.")
    instante = time.time() if agora is None else agora
    ident = f"{time.time_ns():020d}-{uuid.uuid4().hex}"
    evento = dict(id=ident, motivo=motivo, texto=texto.strip(), criado_em=instante,
                  expira_em=instante + (1800 if motivo == "evento:crash" else 3600), **dados)
    gravar_atomico(Path(pasta) / "eventos" / (ident + ".json"), evento)
    return evento


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("texto")
    args = parser.parse_args()
    try:
        enviar(args.texto)
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
