#!/usr/bin/env python3
"""Daemon supervisionado: recebe chat, consulta Haiku e responde pela ponte local."""
import fcntl
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
import logging
from pathlib import Path
import signal
import sys
import threading
import time
import uuid

# Também executável diretamente pelo supervisor, sem depender do cwd.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import chat_dados
import encenar
import falar
from hana import desktop
from hana.avisar import enviar as avisar
from hana.gatilhos import Gatilhos
from hana.memoria import DADOS, Memoria, agora_local, gravar_atomico
from hana.modelo import Cancelado, Modelo
from hana.rotina import ATIVO_POR, Rotina

INTERVALO = 0.5
INTERVALO_DESKTOP = 5
JUNTAR_POR = 0.8
JUNTAR_MAX = 2
RESUMIR_APOS = 30
LOG = logging.getLogger("hana")
DIAS_SEMANA = ("segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo")


class Cerebro:
    def __init__(self, pasta=DADOS, runtime=falar.RUNTIME, modelo=None, relogio=agora_local):
        self.pasta = Path(pasta)
        self.pasta.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.runtime = Path(runtime)
        self.relogio = relogio
        self.parar = threading.Event()
        self.modelo = modelo or Modelo(pasta, parar=self.parar)
        self.memoria = Memoria(self.pasta / "memoria.json")
        self.rotina = Rotina(self.memoria, relogio)
        self.pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="hana")
        self.chamada = None
        self.resumo = None
        self.resumo_ate = ""
        self.resumo_tentar = 0
        self.contexto = {}
        self.gatilhos = Gatilhos()
        self.desktop_due = 0
        self.entrada_real = None
        self.cursor_anterior = None
        self.pendencia = self._ler_pendencia()
        if not (chat_dados.HIST / ".cursor-Hana").exists() and not self.pendencia:
            # Primeira execução: conversas antigas (de outros agentes) não viram fila de respostas.
            antigas = [m for m in chat_dados.listar(chat_dados.LIMITE) if m.get("origem") == "usuario"]
            if antigas:
                chat_dados.confirmar("Hana", antigas[-1]["id"])
        self.juntar_ate = 0
        self.juntar_inicio = 0
        self.leitura_ate = 0

    def _ler_pendencia(self):
        try:
            return json.loads((self.pasta / "pendencia.json").read_text())
        except FileNotFoundError:
            return None

    def salvar(self):
        gravar_atomico(self.pasta / "pendencia.json", self.pendencia)

    def sessao(self):
        try:
            info = json.loads((self.runtime / "pids.json").read_text())
            estado = json.loads((self.runtime / "status.json").read_text())
            pid = info["godot"]
            identidade = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
            if (identidade != info.get("godot_starttime") or estado.get("pid") != pid
                    or abs(time.time() - estado.get("timestamp", 0)) > 3):
                return {}, None
            return estado, [pid, identidade]
        except (OSError, ValueError, KeyError, IndexError, TypeError):
            return {}, None

    def entrada(self):
        agora = self.relogio()
        contexto = dict(self.contexto)
        estado, _ = self.sessao()
        contexto["roupa"] = desktop.roupa(estado)
        if self.pendencia.get("evento"):
            contexto["evento"] = self.pendencia["evento"]
        return {"agora": {"data_hora": agora.isoformat(), "dia_semana": DIAS_SEMANA[agora.weekday()]},
                "desktop": contexto, "memoria": self.memoria.contexto(agora),
                "historico": chat_dados.listar(20), "motivo": self.pendencia["motivo"],
                "mensagens_usuario": self.pendencia["mensagens"]}

    def preparar(self, mensagens, motivo):
        self.pendencia = {"id": f"{time.time_ns():020d}-{uuid.uuid4().hex}", "motivo": motivo,
                          "mensagens": mensagens, "resposta": None, "envio": None,
                          "agora": self.relogio().isoformat()}
        if motivo.startswith("evento:"):
            self.pendencia["evento"] = self.rotina.evento(motivo, self.contexto)
        self.salvar()
        self.juntar_inicio = time.monotonic()
        self.juntar_ate = self.juntar_inicio + (JUNTAR_POR if mensagens else 0)
        self.leitura_ate = 0

    def ler(self, estado):
        if time.monotonic() < self.leitura_ate or self.pendencia["motivo"] != "resposta":
            return
        # O Godot continua a leitura existente, sem repetir ler/reagir a cada renovação.
        encenar.enviar(autor="Hana", tom="neutro", duracao=20, runtime=self.runtime)
        self.leitura_ate = time.monotonic() + 18

    def _limpar_atividades(self):
        for arquivo in (self.runtime / "atividades").glob("*.json"):
            try:
                if json.loads(arquivo.read_text()).get("autor") == "Hana":
                    arquivo.unlink(missing_ok=True)
            except (OSError, ValueError, AttributeError):
                continue

    def concluir(self):
        p = self.pendencia
        if p["mensagens"]:
            chat_dados.confirmar("Hana", p["mensagens"][-1]["id"])
        else:
            self.rotina.confirmar(p["motivo"], p["id"], (p.get("evento") or {}).get("id"))
        self._limpar_atividades()
        self.pendencia = None
        self.salvar()

    def acompanhar(self, sessao):
        p = self.pendencia
        envio = p["envio"]
        if not envio:
            return False
        recibo = self.runtime / "recibos-fala" / (p["id"] + ".json")
        try:
            estado = json.loads(recibo.read_text()).get("estado")
        except (OSError, ValueError, AttributeError):
            estado = None
        historico = chat_dados.HIST / (p["id"] + "-personagem.json")
        if estado in ("concluida", "interrompida") or historico.exists():
            # Clique interrompe intencionalmente: nunca reenviar esse texto.
            self.concluir()
            return True
        if estado == "erro" or envio["sessao"] != sessao:
            LOG.info("Entrega aguardará sessão ativa: %s", estado or "sessão encerrada")
            (self.runtime / "falas" / (p["id"] + ".json")).unlink(missing_ok=True)
            recibo.unlink(missing_ok=True)
            p["envio"] = None
            self.salvar()
            return False
        fila = self.runtime / "falas" / (p["id"] + ".json")
        if estado is None and not fila.exists() and time.time() - envio["em"] > 3:
            # Crash entre persistir intenção e publicar arquivo: tenta o mesmo ID.
            p["envio"] = None
            self.salvar()
            return False
        return True

    def _desktop(self, estado=None):
        self.contexto["roupa"] = desktop.roupa(estado or {})
        if time.monotonic() < self.desktop_due:
            return
        self.contexto = desktop.coletar()
        self.contexto["roupa"] = desktop.roupa(estado or {})
        try:
            ponte = json.loads((self.runtime / "desktop.json").read_text())
        except (OSError, ValueError):
            ponte = {}
        teclado = ponte.get("last_activity")
        if isinstance(teclado, (int, float)) and teclado > 0:
            self.entrada_real = max(self.entrada_real or 0, teclado)
        cursor = ponte.get("cursor")
        if self.cursor_anterior is not None and cursor and cursor != self.cursor_anterior:
            self.entrada_real = time.time()
        self.cursor_anterior = cursor
        self.contexto["game_mode"] = bool(ponte.get("game_mode"))
        agora = self.relogio()
        publicado = dict(self.contexto, timestamp=time.time(), hora_local=agora.hour)
        gravar_atomico(self.runtime / "contexto.json", publicado)
        for evento in self.gatilhos.passo(self.contexto.get("janela", {})):
            texto = evento.pop("texto")
            avisar(texto, self.pasta, agora=agora.timestamp(), **evento)
        for arquivo in sorted((self.pasta / "eventos").glob("*.json")):
            try:
                evento = json.loads(arquivo.read_text())
                if (not isinstance(evento, dict) or evento.get("id") != arquivo.stem
                        or evento.get("motivo") not in ("evento:aviso", "evento:crash", "evento:download")
                        or not isinstance(evento.get("expira_em"), (int, float))):
                    raise ValueError("Evento externo inválido")
                self.rotina.enfileirar(evento)
                arquivo.unlink()
            except (ValueError, TypeError) as exc:
                LOG.warning("Aviso ignorado: %s", exc)
                arquivo.rename(arquivo.with_suffix(".invalido"))
        self.rotina.observar(self.contexto, self.entrada_real)
        self.desktop_due = time.monotonic() + INTERVALO_DESKTOP

    def _resumir(self):
        if self.resumo and self.resumo.done():
            texto = self.resumo.result()
            if texto:
                self.memoria.resumir(texto, self.resumo_ate)
            self.resumo = None
            self.resumo_tentar = time.monotonic() + 60
        if self.resumo or time.monotonic() < self.resumo_tentar:
            return
        dados = self.memoria.ler()
        novas = [m for m in chat_dados.listar(chat_dados.LIMITE) if m["id"] > dados["resumo_ate"]]
        if len(novas) > RESUMIR_APOS:
            self.resumo_ate = novas[-1]["id"]
            self.resumo = self.pool.submit(self.modelo.resumir,
                                          {"resumo": dados["resumo"], "historico": novas})

    def passo(self):
        estado, sessao = self.sessao()
        if hasattr(self.modelo, "usar"):
            self.modelo.usar(estado.get("preferencias", {}).get("hana_cerebro", "claude"))
        if self.pendencia and self.pendencia["envio"]:
            if self.acompanhar(sessao):
                return
        if self.chamada and self.chamada.done():
            self.pendencia["resposta"] = self.chamada.result()
            self.chamada = None
            self.salvar()
        if not sessao:
            return
        self._desktop(estado)
        if not estado.get("preferencias", {}).get("hana_auto", True):
            return
        mensagem = estado.get("mensagem", {})
        ident = str(mensagem.get("id", ""))
        outro_preparando = (mensagem.get("ativa") and mensagem.get("autor") != "Hana"
                            and ident and Path(ident).name == ident
                            and (self.runtime / "recibos-fala" / (ident + ".json")).exists())
        ocupado = (estado.get("falando") or estado.get("pressionada") or estado.get("menu")
                   or outro_preparando or mensagem.get("ativa") and mensagem.get("autor") == "Prévia visual")
        if not self.pendencia:
            novas = chat_dados.novas("Hana", consumir=False)
            if novas:
                self.preparar(novas, "resposta")
            elif not ocupado and not estado.get("mensagem", {}).get("ativa"):
                ativo = self.entrada_real is not None and time.time() - self.entrada_real < ATIVO_POR
                motivo = self.rotina.motivo(self.contexto, dict(estado, game_mode=self.contexto["game_mode"]), ativo)
                if motivo:
                    self.preparar([], motivo)
        if self.pendencia and not ocupado:
            p = self.pendencia
            if p["motivo"] != "resposta":
                from hana.rotina import relevante
                evento = p.get("evento")
                # Descarta observações que deixaram de ser verdade durante a chamada/fullscreen.
                if evento and not relevante(evento, self.contexto, self.relogio()) and not self.chamada:
                    self.rotina.descartar(evento["id"])
                    self.pendencia = None
                    self.salvar()
                    return
                if (p["motivo"] == "volta" and not self.chamada and
                        self.relogio().timestamp()-self.memoria.ler()["rotina"].get("retorno_em",0) >= 1800):
                    self.pendencia = None
                    self.salvar()
                    return
                if not self.rotina.pode_entregar(p["motivo"], self.contexto, estado, evento):
                    return
            if not p["resposta"]:
                self.ler(estado)
                if not self.chamada:
                    novas = chat_dados.novas("Hana", consumir=False) if p["mensagens"] else []
                    if novas and novas[-1]["id"] != p["mensagens"][-1]["id"]:
                        lote = {m["id"]: m for m in p["mensagens"] + novas}
                        p["mensagens"] = [lote[i] for i in sorted(lote)]
                        self.salvar()
                        self.juntar_ate = min(time.monotonic() + JUNTAR_POR, self.juntar_inicio + JUNTAR_MAX)
                    if time.monotonic() >= self.juntar_ate:
                        self.chamada = self.pool.submit(self.modelo.responder, self.entrada())
            elif not p["envio"]:
                # Uma proativa calculada antes de entrar em fullscreen espera a saída.
                if p["motivo"] != "resposta" and (estado.get("hidden") or self.contexto["game_mode"]
                        or self.contexto.get("janela", {}).get("fullscreen")):
                    return
                resposta = p["resposta"]
                self.memoria.aplicar(resposta["memoria"], datetime.fromisoformat(p["agora"]),
                                     p["id"], len(p["mensagens"]))
                p["envio"] = {"sessao": sessao, "em": time.time()}
                self.salvar()
                falar.enviar(resposta["texto"], autor="Hana", emocao=resposta["emocao"],
                    gesto="gesto_reverencia" if p["motivo"] in ("bom_dia", "volta") else
                          (resposta["gesto"] if resposta["gesto"] != "nenhum" else "auto"),
                    roteiro=None if p["motivo"] in ("bom_dia", "volta") else
                            (resposta["roteiro"] if resposta["roteiro"] != "nenhum" else None),
                    preparacao={"tom": resposta["tom"]}, runtime=self.runtime, identificador=p["id"])
        self._resumir()

    def fechar(self):
        self.parar.set()
        self.gatilhos.fechar()
        self.modelo.parar.set()
        self.pool.shutdown(wait=True, cancel_futures=True)
        self._limpar_atividades()


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    DADOS.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (DADOS / "cerebro.lock").open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            LOG.error("Já existe um cérebro Hana neste diretório de dados.")
            return 1
        cerebro = Cerebro()
        def parar(*_):
            cerebro.parar.set()
        signal.signal(signal.SIGTERM, parar)
        signal.signal(signal.SIGINT, parar)
        LOG.info("Hana iniciou; aguardando sessão e chat.")
        try:
            while not cerebro.parar.is_set():
                try:
                    cerebro.passo()
                except Cancelado:
                    break
                except (OSError, ValueError, RuntimeError, KeyError) as exc:
                    LOG.exception("Ciclo falhou; pendência preservada: %s", exc)
                    cerebro.parar.wait(2)
                cerebro.parar.wait(INTERVALO)
        finally:
            cerebro.fechar()
            LOG.info("Hana encerrou de forma limpa.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
