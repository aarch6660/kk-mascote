#!/usr/bin/env python3
"""Cérebro local opcional da Hana: servidor Ollama falso, sem rede nem modelo real."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import socket
import sys
import tempfile
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hana import modelo  # noqa: E402

casos = 0


def verificar(ok, nome):
    global casos
    casos += 1
    assert ok, nome


pedidos = []


class Falso(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def responder(self, dados):
        corpo = json.dumps(dados).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        self.responder({"models": [{"name": "falso:7b"}]})

    def do_POST(self):
        pedido = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        pedidos.append(pedido)
        resposta = {"texto": "anotado, pão amanhã", "tom": "neutro", "emocao": "Neutra",
                    "roteiro": "nenhum", "gesto": "nenhum",
                    "memoria": {"fatos_novos": [], "tarefas_novas": [{"texto": "comprar pão", "data": "2026-10-12"}],
                                "tarefas_concluidas": [], "tarefas_removidas": [], "nome_usuario": None}}
        if "resumo" in json.dumps(pedido["format"]):
            resposta = {"resumo": "resumo local"}
        self.responder({"message": {"role": "assistant", "content": json.dumps(resposta)}})


servidor = ThreadingHTTPServer(("127.0.0.1", 0), Falso)
threading.Thread(target=servidor.serve_forever, daemon=True).start()
url = "http://127.0.0.1:%d" % servidor.server_port

with tempfile.TemporaryDirectory(prefix="kk-hana-local-") as tmp:
    base = Path(tmp)
    m = modelo.Modelo(base / "a", binario="/nao/existe")
    verificar(m.backend == "claude", "Claude continua padrão")
    m.usar("qualquer")
    verificar(m.backend == "claude", "backend desconhecido volta ao Claude")
    m.ollama_url = url
    m.usar("local")
    r = m.responder({"motivo": "mensagem", "memoria": {"tarefas": []}})
    verificar(r["texto"] == "anotado, pão amanhã", "resposta local validada")
    verificar(r["memoria"]["tarefas_novas"] == [{"texto": "comprar pão", "data": "2026-10-12"}], "tarefa local")
    verificar(pedidos[-1]["model"] == "falso:7b", "sem modelo configurado usa o primeiro instalado")
    verificar(pedidos[-1]["format"]["type"] == "object" and not pedidos[-1]["stream"], "schema e sem streaming")
    verificar(m.resumir({"resumo": "", "historico": []}) == "resumo local", "resumo local")

    (base / "b").mkdir()
    (base / "b/config.json").write_text(json.dumps({"ollama_url": url, "ollama_modelo": "escolhido:3b"}))
    m = modelo.Modelo(base / "b", binario="/nao/existe")
    m.usar("local")
    m.responder({"motivo": "mensagem", "memoria": {"tarefas": []}})
    verificar(pedidos[-1]["model"] == "escolhido:3b", "config.json escolhe modelo")

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        porta = s.getsockname()[1]
    m = modelo.Modelo(base / "c", binario="/nao/existe")
    m.ollama_url = "http://127.0.0.1:%d" % porta
    m.usar("local")
    r = m.responder({"motivo": "mensagem", "memoria": {"tarefas": []}})
    verificar("ollama" in r["texto"], "Ollama desligado vira aviso claro, sem travar")
    verificar(m.resumir({"resumo": "", "historico": []}) is None, "resumo desiste com Ollama desligado")

    m = modelo.Modelo(base / "d", binario="/nao/existe")
    m.ollama_url = url
    m.usar("local")
    m.parar.set()
    try:
        m.responder({"motivo": "mensagem", "memoria": {"tarefas": []}})
        verificar(False, "cancelamento")
    except modelo.Cancelado:
        verificar(True, "cancelamento respeitado no backend local")

servidor.shutdown()
print(json.dumps({"passou": True, "casos": casos}))
