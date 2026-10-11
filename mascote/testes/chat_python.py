#!/usr/bin/env python3
"""Histórico do chat, aviso ao Godot e cursor de leitura por agente (chat_dados.py)."""
import json, os, sys, tempfile, threading
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
casos, erros = 0, []
def verificar(ok, nome):
    global casos
    casos += 1
    if not ok: erros.append(nome)
with tempfile.TemporaryDirectory() as t:
    os.environ["MASCOTE_CHAT"] = t + "/hist"
    os.environ["MASCOTE_RUNTIME"] = t + "/rt"
    import chat_dados as c
    a = c.registrar("usuario", "  oi, tudo bem?  ", boneca="chika-haruno", avisar=True)
    verificar((Path(t) / "rt/chat/entrada" / (a + ".json")).exists(), "aviso para o Godot ler no celular")
    b = c.registrar("personagem", "Tudo! E você?", autor="Claude")
    msgs = c.listar()
    verificar([m["origem"] for m in msgs] == ["usuario", "personagem"] and msgs[0]["texto"] == "oi, tudo bem?", "histórico em ordem e sem espaços sobrando")
    for ruim in [("usuario", ""), ("outro", "x"), ("usuario", "x" * 2001)]:
        try: c.registrar(*ruim); verificar(False, "rejeita mensagem inválida")
        except ValueError: verificar(True, "rejeita mensagem inválida")
    verificar([m["id"] for m in c.novas("Claude")] == [a], "agente lê só mensagens do usuário")
    verificar(c.novas("Claude") == [], "cursor avança após ler")
    verificar(len(c.novas("Codex", consumir=False)) == 1 and len(c.novas("Codex")) == 1, "cada agente tem cursor próprio; espiar não consome")
    fios = [threading.Thread(target=c.registrar, args=("usuario", f"m{i}")) for i in range(30)]
    for f in fios: f.start()
    for f in fios: f.join()
    verificar(len(c.listar(500)) == 32, "30 envios simultâneos sem perda")
    verificar(len(c.novas("Claude")) == 30, "agente recebe todas as novas")
    for i in range(c.LIMITE + 20): c.registrar("personagem", f"p{i}")
    verificar(len(list(Path(t, "hist").glob("*.json"))) == c.LIMITE, "histórico é podado no limite")
print(json.dumps({"casos": casos, "passou": not erros, "erros": erros}, ensure_ascii=False))
sys.exit(1 if erros else 0)
