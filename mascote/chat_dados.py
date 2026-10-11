#!/usr/bin/env python3
"""Histórico do chat por mensagens (usuário ↔ personagem) e leitura pelos agentes.

Histórico persistente: ~/.cache/forja/kk-mascote-chat/<ns>-<origem>.json, um arquivo por mensagem
(gravação atômica; vários escritores sem disputa). Origem "usuario" ou "personagem".
A janela também avisa o Godot em <runtime>/chat/entrada/<id>.json para ele "ler" no celular.

Agentes (Claude/Codex) leem o que o usuário escreveu na janela:
    python3 mascote/chat_dados.py --autor Claude            # novas desde a última leitura
    python3 mascote/chat_dados.py --autor Claude --esperar 60
Não existe despertar automático: o agente precisa consultar durante o turno.
"""
import argparse
import json
import os
from pathlib import Path
import time
import uuid

HIST = Path(os.environ.get("MASCOTE_CHAT", Path.home() / ".cache/forja/kk-mascote-chat"))
RUNTIME = Path(os.environ.get("MASCOTE_RUNTIME") or Path(os.environ.get("XDG_RUNTIME_DIR", f"/tmp/kk-mascote-{os.getuid()}")) / "kk-mascote")
LIMITE = 300
TAMANHO = 2000


def _gravar(pasta, nome, dados):
    pasta.mkdir(parents=True, exist_ok=True)
    tmp = pasta / (nome + ".tmp")
    tmp.write_text(json.dumps(dados, ensure_ascii=False))
    os.replace(tmp, pasta / (nome + ".json"))


def registrar(origem, texto, autor="", boneca="", avisar=False):
    texto = str(texto).strip()
    if origem not in ("usuario", "personagem") or not texto or len(texto) > TAMANHO:
        raise ValueError("mensagem de chat inválida")
    ident = f"{time.time_ns():020d}-{uuid.uuid4().hex[:8]}"
    dados = {"id": ident, "origem": origem, "autor": autor, "boneca": boneca, "texto": texto, "criado_em": time.time()}
    _gravar(HIST, f"{ident}-{origem}", dados)
    if origem == "usuario":
        # Fila durável da companheira: podar o chat visual não perde pedidos ainda sem resposta.
        _gravar(HIST / ".pendentes-hana", ident, dados)
    if avisar:
        _gravar(RUNTIME / "chat" / "entrada", ident, dados)
    _podar()
    return ident


def _podar():
    arquivos = sorted(HIST.glob("*.json"))
    for velho in arquivos[:-LIMITE]:
        velho.unlink(missing_ok=True)


def listar(n=80):
    saida = []
    for p in sorted(HIST.glob("*.json")):
        try:
            saida.append(json.loads(p.read_text()))
        except (OSError, ValueError):
            continue
    # IDs estáveis de entrega podem ser anteriores ao término da escrita.
    saida.sort(key=lambda m: (m.get("criado_em", 0), m.get("id", "")))
    return saida[-n:]


def escrevendo():
    try:
        return json.loads((RUNTIME / "chat" / "escrevendo.json").read_text())
    except (OSError, ValueError):
        return {}


def novas(autor, consumir=True):
    """Mensagens do usuário ainda não lidas por este agente (cursor próprio)."""
    cursor = HIST / f".cursor-{autor}"
    ultimo = cursor.read_text().strip() if cursor.exists() else ""
    pendentes = [m for m in listar(LIMITE) if m.get("origem") == "usuario" and m.get("id", "") > ultimo]
    if autor == "Hana":
        lote = {m["id"]: m for m in pendentes}
        for arquivo in (HIST / ".pendentes-hana").glob("*.json"):
            try:
                m = json.loads(arquivo.read_text())
                if m.get("origem") == "usuario" and m.get("id", "") > ultimo:
                    lote[m["id"]] = m
            except (OSError, ValueError, AttributeError):
                continue
        pendentes = [lote[i] for i in sorted(lote)]
    if consumir and pendentes:
        confirmar(autor, pendentes[-1]["id"])
    return pendentes


def confirmar(autor, ultimo):
    """Confirma somente o lote respondido, preservando mensagens que chegaram depois."""
    if not autor or Path(autor).name != autor or not isinstance(ultimo, str):
        raise ValueError("Cursor inválido")
    HIST.mkdir(parents=True, exist_ok=True)
    cursor = HIST / f".cursor-{autor}"
    atual = cursor.read_text().strip() if cursor.exists() else ""
    if ultimo > atual:
        tmp = HIST / f".cursor-{autor}-{uuid.uuid4().hex}.tmp"
        try:
            tmp.write_text(ultimo)
            os.replace(tmp, cursor)
        finally:
            tmp.unlink(missing_ok=True)
    if autor == "Hana":
        for arquivo in (HIST / ".pendentes-hana").glob("*.json"):
            if arquivo.stem <= max(ultimo, atual):
                arquivo.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--autor", required=True, help="Agente que lê (cursor próprio): Claude, Codex…")
    ap.add_argument("--esperar", type=float, default=0, help="Aguarda até N s (máx. 600) por mensagem nova")
    ap.add_argument("--espiar", action="store_true", help="Não avança o cursor")
    a = ap.parse_args()
    fim = time.time() + min(max(a.esperar, 0), 600)
    while True:
        msgs = novas(a.autor, consumir=not a.espiar)
        if msgs or time.time() >= fim:
            break
        time.sleep(0.5)
    print(json.dumps(msgs, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
