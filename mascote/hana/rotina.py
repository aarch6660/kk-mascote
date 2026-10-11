"""Agenda persistente, com relógio e aleatoriedade injetáveis para testes."""
from datetime import timedelta
import random
from . import desktop
from .memoria import agora_local, dia, registro_dia

VIRADA_DIA = 5
NOITE_INICIO = 21
NOITE_FIM = 2
COBRANCA_MIN = 40 * 60
COBRANCA_MAX = 70 * 60
INTERVALO_PROATIVO = 15 * 60
ATIVO_POR = 5 * 60
RETORNO_OCIOSO = 3 * 60 * 60
CONTEXTO_ESTAVEL = 2 * 60
INTERVALO_COMENTARIO = 30 * 60


def madrugada(agora):
    return 0 <= agora.hour < 5


def relevante(evento, contexto, agora):
    if evento.get("expira_em", 0) <= agora.timestamp():
        return False
    motivo = evento.get("motivo")
    if motivo == "evento:bateria":
        return desktop.bateria_baixa(contexto)
    if motivo == "evento:bateria_cheia":
        return any(b.get("nivel") == 100 and b.get("status") in ("Full", "Not charging")
                   for b in contexto.get("baterias", []))
    if motivo == "evento:janela":
        return desktop.categorizar(contexto.get("janela", {})) == evento.get("categoria")
    if motivo == "evento:musica":
        return contexto.get("musica", {}).get("status") == "Playing"
    if motivo == "evento:download":
        from pathlib import Path
        try:
            stat = Path(evento["arquivo"]).stat()
            return [stat.st_ino, stat.st_size, stat.st_mtime_ns] == evento.get("assinatura")
        except (OSError, KeyError):
            return False
    return motivo in ("evento:aviso", "evento:crash")


def adicionar_evento(estado, evento):
    fila = estado.setdefault("eventos", [])
    if not any(e.get("id") == evento["id"] for e in fila):
        fila.append(evento)
    estado["eventos"] = fila[-64:]


class Rotina:
    def __init__(self, memoria, relogio=agora_local, sorteio=random.uniform):
        self.memoria = memoria
        self.relogio = relogio
        self.sorteio = sorteio
        self.memoria.virada = VIRADA_DIA

    def observar(self, contexto, ultima_entrada=None):
        agora = self.relogio()
        with self.memoria.transacao() as dados:
            estado = dados["rotina"]
            antes = estado.get("desktop", {})
            if "bateria_baixa" in desktop.eventos(antes, contexto):
                estado["bateria_pendente"] = True
            if not desktop.bateria_baixa(contexto):
                estado["bateria_pendente"] = False
            for evento in desktop.eventos(antes, contexto):
                if evento in ("bateria_baixa", "bateria_cheia"):
                    motivo = "evento:bateria" if evento == "bateria_baixa" else "evento:bateria_cheia"
                    adicionar_evento(estado, dict(id=f"{motivo}-{agora.timestamp()}", motivo=motivo,
                        texto="Bateria baixa, descarregando." if evento == "bateria_baixa" else "A bateria terminou de carregar.",
                        criado_em=agora.timestamp(), expira_em=agora.timestamp()+3600))
            categoria = desktop.categorizar(contexto.get("janela", {}))
            anterior_categoria = desktop.categorizar(antes.get("janela", {}))
            if categoria != anterior_categoria:
                estado["janela_candidata"] = dict(categoria=categoria, desde=agora.timestamp(), notificada=False)
            candidata = estado.get("janela_candidata", {})
            if (categoria != "outro" and candidata and not candidata["notificada"]
                    and agora.timestamp() - candidata["desde"] > CONTEXTO_ESTAVEL):
                adicionar_evento(estado, dict(id=f"janela-{candidata['desde']}", motivo="evento:janela",
                    categoria=categoria, texto=f"A janela ativa mudou para a categoria {categoria} há mais de dois minutos.",
                    criado_em=agora.timestamp(), expira_em=agora.timestamp()+3600))
                candidata["notificada"] = True
            toca = contexto.get("musica", {}).get("status") == "Playing"
            tocava = antes.get("musica", {}).get("status") == "Playing"
            if toca and not tocava:
                estado["musica_candidata"] = dict(desde=agora.timestamp(), notificada=False)
            if not toca:
                estado.pop("musica_candidata", None)
            candidata = estado.get("musica_candidata", {})
            if candidata and not candidata["notificada"] and agora.timestamp()-candidata["desde"] > CONTEXTO_ESTAVEL:
                adicionar_evento(estado, dict(id=f"musica-{candidata['desde']}", motivo="evento:musica",
                    texto="Música tocando há mais de dois minutos.", criado_em=agora.timestamp(),
                    expira_em=agora.timestamp()+3600))
                candidata["notificada"] = True
            estado["eventos"] = [e for e in estado.get("eventos", []) if relevante(e, contexto, agora)]
            estado["desktop"] = contexto
            # Só entrada efetiva (mouse/teclado) permite detectar retorno após 3 h.
            anterior = estado.get("ultima_entrada")
            if ultima_entrada is not None and (anterior is None or ultima_entrada > anterior):
                if anterior is not None and ultima_entrada - anterior > RETORNO_OCIOSO:
                    estado["retorno_pendente"] = True
                    estado["retorno_em"] = agora.timestamp()
                estado["ultima_entrada"] = ultima_entrada
            estado.setdefault("proxima_cobranca", agora.timestamp() + self.sorteio(COBRANCA_MIN, COBRANCA_MAX))

    def enfileirar(self, evento):
        with self.memoria.transacao() as dados:
            adicionar_evento(dados["rotina"], evento)

    def descartar(self, evento_id):
        with self.memoria.transacao() as dados:
            estado = dados["rotina"]
            estado["eventos"] = [e for e in estado.get("eventos", []) if e["id"] != evento_id]

    def evento(self, motivo, contexto):
        agora = self.relogio()
        return next((e for e in self.memoria.ler()["rotina"].get("eventos", [])
                     if e["motivo"] == motivo and relevante(e, contexto, agora)), None)

    def pode_entregar(self, motivo, contexto, status, evento=None):
        agora = self.relogio()
        estado = self.memoria.ler()["rotina"]
        if (status.get("hidden") or status.get("game_mode") or contexto.get("game_mode")
                or contexto.get("janela", {}).get("fullscreen")):
            return False
        if agora.timestamp() - estado.get("ultima_proativa", 0) < INTERVALO_PROATIVO:
            return False
        if motivo in ("evento:janela", "evento:musica"):
            if agora.timestamp() - estado.get("ultimo_comentario", 0) < INTERVALO_COMENTARIO:
                return False
        if evento and not relevante(evento, contexto, agora):
            return False
        if motivo == "volta" and agora.timestamp()-estado.get("retorno_em", 0) >= 1800:
            return False
        return True

    def motivo(self, contexto, status, ativo):
        agora = self.relogio()
        dados = self.memoria.ler()
        estado = dados["rotina"]
        # Ocultação vale para TODA proatividade, inclusive bom dia e bateria.
        if not self.pode_entregar("rotina", contexto, status):
            return None
        registro = dados["dias"].get(dia(agora, VIRADA_DIA), {})
        if not registro.get("primeiro_login"):
            return "bom_dia"
        if not ativo:
            return None
        if estado.get("retorno_pendente") and self.pode_entregar("volta", contexto, status):
            return "volta"
        for evento in estado.get("eventos", []):
            if relevante(evento, contexto, agora) and self.pode_entregar(evento["motivo"], contexto, status, evento):
                return evento["motivo"]
        # Depois da meia-noite, "amanhã" ainda é o dia civil seguinte.
        amanha = (agora.date() + timedelta(days=1)).isoformat()
        noite = agora.hour >= NOITE_INICIO or agora.hour < NOITE_FIM
        if (noite and not registro.get("pergunta_noite")
                and not any(t["data"] == amanha for t in dados["tarefas"])):
            return "pergunta_noite"
        hoje = agora.date().isoformat()
        pendentes = any(not t["concluida_em"] and t["data"] <= hoje for t in dados["tarefas"])
        if pendentes and agora.timestamp() >= estado.get("proxima_cobranca", float("inf")):
            return "cobranca"
        return None

    def confirmar(self, motivo, identificador=None, evento_id=None):
        agora = self.relogio()
        with self.memoria.transacao() as dados:
            estado = dados["rotina"]
            if identificador and identificador in estado.get("confirmadas", []):
                return
            if identificador:
                estado["confirmadas"] = (estado.get("confirmadas", []) + [identificador])[-100:]
            estado["ultima_proativa"] = agora.timestamp()
            registro = registro_dia(dados, agora, VIRADA_DIA)
            if motivo == "bom_dia":
                registro["primeiro_login"] = registro["primeiro_login"] or agora.isoformat()
                estado["retorno_pendente"] = False
            elif motivo == "volta":
                estado["retorno_pendente"] = False
            elif motivo == "pergunta_noite":
                registro["pergunta_noite"] = agora.isoformat()
            elif motivo == "evento:bateria":
                estado["bateria_pendente"] = False
            if motivo.startswith("evento:"):
                evento = next((e for e in estado.get("eventos", [])
                    if e["id"] == evento_id or (evento_id is None and e["motivo"] == motivo)), None)
                if evento:
                    estado["eventos"] = [e for e in estado["eventos"] if e["id"] != evento["id"]]
            if motivo in ("evento:janela", "evento:musica"):
                estado["ultimo_comentario"] = agora.timestamp()
            if motivo in ("bom_dia", "cobranca"):
                estado["proxima_cobranca"] = agora.timestamp() + self.sorteio(COBRANCA_MIN, COBRANCA_MAX)
                if motivo == "cobranca":
                    for t in dados["tarefas"]:
                        if not t["concluida_em"] and t["data"] <= agora.date().isoformat():
                            t["cobrancas"] += 1
                            t["ultima_cobranca"] = agora.isoformat()
