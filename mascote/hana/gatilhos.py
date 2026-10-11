"""Observadores opcionais e leves: arquivos estáveis, coredumps e saída por sinal."""
import json
import os
from pathlib import Path
import selectors
import shutil
import subprocess
import time

from .desktop import categorizar

TEMPORARIOS = (".part", ".crdownload", ".tmp", ".download")
JOGOS = {"minecraft", "lutris", "gamescope", "wine", "wine64"}


class Downloads:
    def __init__(self, pasta=None, relogio=time.time):
        self.pasta = Path(pasta) if pasta is not None else Path.home() / "Downloads"
        self.relogio = relogio
        self.arquivos = {}
        self.passo(inicial=True)

    def passo(self, inicial=False):
        agora = self.relogio()
        presentes = set()
        eventos = []
        try:
            arquivos = list(self.pasta.iterdir())
        except OSError:
            return []
        for p in arquivos:
            if p.name.startswith(".") or p.name.casefold().endswith(TEMPORARIOS):
                continue
            try:
                if not p.is_file() or p.is_symlink():
                    continue
                stat = p.stat()
            except OSError:
                continue
            chave = str(p)
            presentes.add(chave)
            assinatura = (stat.st_ino, stat.st_size, stat.st_mtime_ns)
            anterior = self.arquivos.get(chave)
            if anterior is None or anterior[0] != assinatura:
                self.arquivos[chave] = [assinatura, agora, inicial]
            elif not anterior[2] and agora - anterior[1] > 3:
                anterior[2] = True
                eventos.append(dict(motivo="evento:download", texto=f"Download concluído: {p.name}",
                                    arquivo=chave, assinatura=list(assinatura)))
        self.arquivos = {p: v for p, v in self.arquivos.items() if p in presentes}
        return eventos


def processo_jogo(nome, linha=""):
    nome = nome.casefold()
    return (nome in JOGOS or nome.startswith("steam_app_")
            or (nome.startswith("java") and "minecraft" in linha.casefold()))


class Gatilhos:
    def __init__(self, downloads=None, proc=Path("/proc")):
        self.downloads = downloads or Downloads()
        self.proc = Path(proc)
        self.conhecidos = {}
        self.reportados = set()
        self.journal = None
        self.seletor = selectors.DefaultSelector()
        self.buffer = b""
        self.tentar_journal = 0

    def _journal(self):
        if self.journal and self.journal.poll() is not None:
            self.seletor.unregister(self.journal.stdout)
            self.journal.stdout.close()
            self.journal = None
            self.tentar_journal = time.monotonic() + 300
        if not self.journal and time.monotonic() >= self.tentar_journal:
            self.tentar_journal = time.monotonic() + 300
            if shutil.which("journalctl"):
                try:
                    self.journal = subprocess.Popen(["journalctl", "-f", "-n", "0", "-o", "json",
                        "-t", "systemd-coredump"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                    os.set_blocking(self.journal.stdout.fileno(), False)
                    self.seletor.register(self.journal.stdout, selectors.EVENT_READ)
                except OSError:
                    self.journal = None
        saida = []
        if not self.journal:
            return saida
        for key, _ in self.seletor.select(0):
            bloco = os.read(key.fd, 65536)
            self.buffer = (self.buffer + bloco)[-262144:]
            while b"\n" in self.buffer:
                linha, self.buffer = self.buffer.split(b"\n", 1)
                try:
                    d = json.loads(linha)
                    nome = d.get("COREDUMP_COMM", "")
                    pid = str(d.get("COREDUMP_PID", ""))
                    conhecido = self.conhecidos.get(pid, {})
                    if ((conhecido and conhecido["nome"] == nome)
                            or processo_jogo(nome, d.get("COREDUMP_CMDLINE", ""))):
                        evento = self._crash(pid, nome, d.get("COREDUMP_SIGNAL", "?"))
                        if evento:
                            saida.append(evento)
                except (ValueError, TypeError):
                    continue
        return saida

    def _crash(self, pid, nome, sinal):
        chave = (pid, self.conhecidos.get(pid, {}).get("inicio", "journal"))
        if chave in self.reportados:
            return None
        self.reportados.add(chave)
        if len(self.reportados) > 256:
            self.reportados = {chave}
        return dict(motivo="evento:crash", texto=f"O jogo {nome} terminou com sinal {sinal}.", pid=pid)

    def passo(self, janela):
        eventos = self.downloads.passo()
        # A classe de uma janela de jogo é também uma evidência para seu PID.
        pid_janela = str(janela.get("pid", "")) if categorizar(janela) == "jogo" else ""
        try:
            pastas = list(self.proc.iterdir())
        except OSError:
            pastas = []
        for p in pastas:
            if not p.name.isdigit():
                continue
            try:
                stat = (p / "stat").read_text()
                nome = stat.split("(", 1)[1].rsplit(")", 1)[0]
                campos = stat.rsplit(")", 1)[1].split()
                conhecido = self.conhecidos.get(p.name, {})
                jogo = p.name == pid_janela or processo_jogo(nome)
                if nome.startswith("java") and not jogo:
                    jogo = processo_jogo(nome, (p / "cmdline").read_text().replace("\0", " "))
                if not jogo and conhecido.get("inicio") != campos[19]:
                    continue
                self.conhecidos[p.name] = dict(inicio=campos[19], nome=nome, visto=time.monotonic())
                if campos[0] == "Z" and len(campos) > 49:
                    sinal = int(campos[49]) & 127
                    if sinal not in (0, 127):
                        evento = self._crash(p.name, nome, sinal)
                        if evento:
                            eventos.append(evento)
            except (OSError, ValueError, IndexError):
                continue
        eventos.extend(self._journal())
        # O coredump pode chegar depois de o processo desaparecer do /proc.
        recentes = sorted(self.conhecidos.items(), key=lambda item:item[1]["visto"])
        self.conhecidos = {p:v for p,v in recentes[-512:] if time.monotonic()-v["visto"] < 1800}
        return eventos

    def fechar(self):
        self.seletor.close()
        if self.journal:
            if self.journal.poll() is None:
                self.journal.terminate()
                try:
                    self.journal.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.journal.kill()
                    self.journal.wait(timeout=2)
            self.journal.stdout.close()
