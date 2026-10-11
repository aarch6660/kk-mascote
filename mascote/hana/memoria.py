#!/usr/bin/env python3
"""Memória persistente da Hana; CLI também disponível para o usuário e agentes."""
import argparse
from contextlib import contextmanager
from datetime import date, datetime, timedelta
import fcntl
import json
import os
from pathlib import Path
import re
import tempfile
import uuid

VERSAO = 1
MAX_FATOS = 60
MAX_RESUMO = 1500
DADOS = Path(os.environ.get("MASCOTE_HANA_DIR", Path.home() / ".local/share/kk-mascote/hana"))


def agora_local():
    return datetime.now().astimezone()


def dia(agora, virada=5):
    """O dia de convivência começa às 05:00; datas de tarefas são civis."""
    return (agora - timedelta(hours=virada)).date().isoformat()


def texto_valido(valor, limite):
    return (isinstance(valor, str) and 0 < len(valor.strip()) <= limite
            and not any(ord(c) < 32 and c not in "\n\t" for c in valor))


def data_valida(valor):
    if not isinstance(valor, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", valor):
        return False
    try:
        date.fromisoformat(valor)
        return True
    except ValueError:
        return False


def data_tarefa(texto, data, agora):
    if data is not None:
        if not data_valida(data):
            raise ValueError("Data deve ser AAAA-MM-DD válida.")
        return data
    amanha = bool(re.search(r"\bamanh[ãa]\b", texto, re.IGNORECASE))
    return (agora.date() + timedelta(days=int(amanha))).isoformat()


def gravar_atomico(arquivo, dados):
    arquivo = Path(arquivo)
    arquivo.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporario = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=arquivo.parent,
                                         prefix="." + arquivo.name, suffix=".tmp", delete=False) as f:
            temporario = Path(f.name)
            json.dump(dados, f, ensure_ascii=False, indent=2, allow_nan=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporario, arquivo)
        fd = os.open(arquivo.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        if temporario:
            temporario.unlink(missing_ok=True)


def vazia():
    return {"versao": VERSAO, "nome_usuario": None, "fatos": [], "tarefas": [], "resumo": "",
            "dias": {}, "rotina": {}, "operacoes": [], "resumo_ate": ""}


def registro_dia(dados, agora, virada=5):
    return dados["dias"].setdefault(dia(agora, virada),
                                  {"primeiro_login": None, "mensagens": 0, "tarefas_feitas": []})


class Memoria:
    def __init__(self, arquivo=None, virada=5):
        self.arquivo = Path(arquivo) if arquivo else DADOS / "memoria.json"
        self.virada = virada

    def ler(self):
        try:
            dados = json.loads(self.arquivo.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return vazia()
        # Nunca sobrescreve silenciosamente uma memória corrompida/de versão futura.
        if not isinstance(dados, dict) or dados.get("versao") != VERSAO:
            raise ValueError("Versão/formato da memória não suportado.")
        resultado = vazia()
        resultado.update(dados)
        for chave, tipo in [("fatos", list), ("tarefas", list), ("dias", dict),
                            ("rotina", dict), ("operacoes", list), ("resumo", str)]:
            if not isinstance(resultado[chave], tipo):
                raise ValueError("Campo inválido na memória: " + chave)
        return resultado

    @contextmanager
    def transacao(self):
        self.arquivo.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self.arquivo.with_suffix(".lock").open("a+") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            dados = self.ler()
            yield dados
            gravar_atomico(self.arquivo, dados)

    def aplicar(self, operacoes, agora=None, identificador=None, mensagens=0):
        agora = agora or agora_local()
        with self.transacao() as dados:
            if identificador and identificador in dados["operacoes"]:
                return
            for fato in operacoes.get("fatos_novos", []):
                if texto_valido(fato, 400):
                    fato = fato.strip()
                    if fato.casefold() not in [f.casefold() for f in dados["fatos"]]:
                        dados["fatos"].append(fato)
            dados["fatos"] = dados["fatos"][-MAX_FATOS:]
            nome = operacoes.get("nome_usuario")
            if texto_valido(nome, 80):
                dados["nome_usuario"] = nome.strip()
            for tarefa in operacoes.get("tarefas_novas", []):
                if not isinstance(tarefa, dict) or not texto_valido(tarefa.get("texto"), 400):
                    continue
                texto = tarefa["texto"].strip()
                try:
                    data = data_tarefa(texto, tarefa.get("data"), agora)
                except ValueError:
                    continue
                if any(t["texto"].casefold() == texto.casefold() and t["data"] == data
                       and not t["concluida_em"] for t in dados["tarefas"]):
                    continue
                dados["tarefas"].append({"id": uuid.uuid4().hex[:12], "texto": texto, "data": data,
                    "criada_em": agora.isoformat(), "concluida_em": None,
                    "cobrancas": 0, "ultima_cobranca": None})
            concluidas = operacoes.get("tarefas_concluidas", [])
            removidas = operacoes.get("tarefas_removidas", [])
            registro = registro_dia(dados, agora, self.virada)
            for tarefa in dados["tarefas"]:
                if tarefa["id"] in concluidas and not tarefa["concluida_em"]:
                    tarefa["concluida_em"] = agora.isoformat()
                    registro["tarefas_feitas"].append(tarefa["id"])
            dados["tarefas"] = [t for t in dados["tarefas"] if t["id"] not in removidas]
            registro["mensagens"] += mensagens
            if identificador:
                dados["operacoes"] = (dados["operacoes"] + [identificador])[-100:]

    def contexto(self, agora=None):
        agora = agora or agora_local()
        dados = self.ler()
        recentes = (agora - timedelta(days=7)).isoformat()
        tarefas = [dict(t, atrasada=not t["concluida_em"] and t["data"] < agora.date().isoformat())
                   for t in dados["tarefas"] if not t["concluida_em"] or t["concluida_em"] >= recentes]
        return {"nome_usuario": dados["nome_usuario"], "fatos": dados["fatos"],
                "tarefas": tarefas, "resumo": dados["resumo"][:MAX_RESUMO]}

    def resumir(self, texto, ate):
        if not texto_valido(texto, MAX_RESUMO):
            raise ValueError("Resumo inválido.")
        with self.transacao() as dados:
            dados["resumo"] = texto.strip()
            dados["resumo_ate"] = ate


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    grupo = ap.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--listar", action="store_true")
    grupo.add_argument("--tarefa")
    grupo.add_argument("--concluir")
    grupo.add_argument("--esquecer")
    ap.add_argument("--data")
    a = ap.parse_args()
    if a.data and not a.tarefa:
        ap.error("--data exige --tarefa")
    memoria = Memoria()
    try:
        if a.tarefa:
            if not texto_valido(a.tarefa, 400):
                raise ValueError("Tarefa deve ter 1 a 400 caracteres.")
            data = data_tarefa(a.tarefa, a.data, agora_local())
            memoria.aplicar({"tarefas_novas": [{"texto": a.tarefa, "data": data}]})
        elif a.concluir or a.esquecer:
            ident = a.concluir or a.esquecer
            if not any(t["id"] == ident for t in memoria.ler()["tarefas"]):
                raise ValueError("ID de tarefa desconhecido.")
            memoria.aplicar({"tarefas_concluidas" if a.concluir else "tarefas_removidas": [ident]})
        print(json.dumps(memoria.ler(), ensure_ascii=False, indent=2))
    except (OSError, ValueError) as exc:
        ap.exit(1, str(exc) + "\n")


if __name__ == "__main__":
    main()
