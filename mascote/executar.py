#!/usr/bin/env python3
"""Alterna uma instância; lock e PIDs com starttime evitam matar PID reutilizado."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import select
import signal
import socket
import subprocess
import sys
import time
import hypr_bridge as bridge

ROOT = Path(__file__).resolve().parent
RUNTIME = Path(os.environ.get("XDG_RUNTIME_DIR", f"/tmp/kk-mascote-{os.getuid()}")) / "kk-mascote"


class FilhoSupervisionado:
    """Reinicia só seu filho, com backoff; nunca procura processos pelo nome."""
    def __init__(self, comando, log, env):
        self.comando, self.log, self.env = comando, log, env
        self.processo = None
        self.proximo = 0
        self.backoff = 1
        self.inicio = 0

    def passo(self, agora):
        if self.processo and self.processo.poll() is not None:
            print("Hana encerrou (%s); reinício em %ss" % (self.processo.returncode, self.backoff), flush=True)
            self.processo = None
            self.proximo = agora + self.backoff
            self.backoff = min(60, self.backoff * 2)
        if self.processo is None and agora >= self.proximo:
            self.processo = subprocess.Popen(self.comando, cwd=ROOT, env=self.env,
                                             stdout=self.log, stderr=self.log, start_new_session=True)
            self.inicio = agora
        elif self.processo and agora - self.inicio > 60:
            self.backoff = 1

    def fechar(self):
        if self.processo and self.processo.poll() is None:
            self.processo.terminate()
            try:
                self.processo.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(self.processo.pid, signal.SIGKILL)
                self.processo.wait()


def identity(pid):
    try:
        return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
    except (OSError, IndexError):
        return None


def own_alive(info):
    return identity(info.get("runner", 0)) == info.get("starttime") and info.get("starttime") is not None


def hypr_lua(source):
    result = subprocess.run(["hyprctl", "eval", source], capture_output=True, text=True, timeout=4)
    if result.returncode or result.stdout.strip() != "ok":
        raise RuntimeError("hyprctl eval: " + result.stdout + result.stderr)


def run(args, lock):
    stopped = False
    def stop(*_):
        nonlocal stopped
        stopped = True
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    rule = f"kk-mascote-temporario-{os.getpid()}"
    godot = None
    chat = None
    hana = None
    hana_log = None
    events = None
    installed = False
    display_alias = None
    listeners = f"{rule}-eventos"
    last_gate = None
    last_activity = time.time()
    def instalar():
        hypr_lua(f'''_G["{rule}"] = (function() {source} end)()
            if _G["{listeners}"] then
                for _,s in ipairs(_G["{listeners}"]) do s:remove() end
            end
            local ultimo = hl.get_active_window()
            _G["{listeners}"] = {{
                hl.on("window.active", function(w)
                    if w and w.class == "kk-mascote" then
                        -- devolver o foco sem o Hyprland teleportar o cursor para o centro da outra janela
                        if ultimo then pcall(function()
                            hl.config({{ cursor = {{ no_warps = true }} }})
                            hl.dispatch(hl.dsp.focus({{window=ultimo}}))
                            hl.config({{ cursor = {{ no_warps = false }} }})
                        end) end
                    elseif w then ultimo = w end
                end),
                hl.on("input.keyboard.key", function() hl.dispatch(hl.dsp.event("kk-mascote-input")) end),
                hl.bind("B", function() hl.dispatch(hl.dsp.event("kk-mascote-boneca")) end, {{non_consuming=true}})
            }}''')
    try:
        data = bridge.snapshot()
        # Só a regra deste processo é criada/desativada; nenhum reload/config editado.
        source = (ROOT / "regras-mascote.lua").read_text().replace('name = "kk-mascote"', f'name = "{rule}"')
        m = data["monitor"]
        source = source.replace('size = "1920 1080"', f'size = "{m["width"]} {m["height"]}"')
        source = source.replace('move = "0 0"', f'move = "{m["x"]} {m["y"]}"')
        installed = True
        instalar()
        bridge.atomic_json(RUNTIME / "desktop.json", data)
        env = os.environ.copy()
        env["MASCOTE_RUNTIME"] = str(RUNTIME)
        env["MASCOTE_RETRATO"] = "1" if args.retrato else "0"
        env["MASCOTE_PERFIL"] = "1" if args.perfil else "0"
        env["MASCOTE_PROVA"] = "1" if args.prova else "0"
        binary = os.environ.get("GODOT", str(Path.home()/".local/opt/godot/godot"))
        # Intel Vulkan evita acordar a NVIDIA; usuário pode optar por --gpu inherit.
        if args.gpu == "intel":
            env["DRI_PRIME"] = "pci-0000_00_02_0"
            env["__GLX_VENDOR_LIBRARY_NAME"] = "mesa"
            env.pop("__NV_PRIME_RENDER_OFFLOAD", None)
            env.pop("__VK_LAYER_NV_optimus", None)
            env.pop("VK_LOADER_DRIVERS_SELECT", None)
        # Esta sessão pode ter o socket X1 removido por ferramentas Xvnc anteriores.
        # Alias exclusivo e temporário para o listener XWayland ainda vivo X1_.
        if args.driver == "x11":
            number = env.get("DISPLAY", ":1").split(":")[-1].split(".")[0]
            normal = Path(f"/tmp/.X11-unix/X{number}")
            alternate = normal.with_name(normal.name + "_")
            if not normal.exists() and alternate.exists():
                for n in range(190, 250):
                    candidate = normal.with_name(f"X{n}")
                    try:
                        candidate.symlink_to(alternate)
                    except FileExistsError:
                        continue
                    display_alias = candidate
                    env["DISPLAY"] = f":{n}"
                    break
        log = open(RUNTIME / "godot.log", "w")
        godot = subprocess.Popen([binary, "--path", str(ROOT), "--display-driver", args.driver,
                                  "--rendering-method", "gl_compatibility" if args.gpu == "intel" else "forward_plus",
                                  "--audio-driver", "PulseAudio", "--position", f'{m["x"]},{m["y"]}'],
                                 env=env, stdout=log, stderr=log)
        info = {"runner": os.getpid(), "starttime": identity(os.getpid()), "godot": godot.pid,
                "godot_starttime": identity(godot.pid), "rule": rule, "driver": args.driver, "display": env.get("DISPLAY")}
        bridge.atomic_json(RUNTIME / "pids.json", info)
        if not args.prova:
            # Janela de chat (layer-shell Wayland); só aparece com o Modo mensagens ligado.
            chat = subprocess.Popen([sys.executable, str(ROOT / "chat.py")], cwd=ROOT,
                                    env=dict(os.environ, GDK_BACKEND="wayland"),
                                    stdout=log, stderr=log)
            hana_log = open(RUNTIME / "hana.log", "a")
            hana = FilhoSupervisionado([sys.executable, str(ROOT / "hana/cerebro.py")], hana_log, env)
        events = socket.socket(socket.AF_UNIX)
        events.connect(str(bridge.socket_dir()/".socket2.sock"))
        events.setblocking(False)
        start = time.monotonic()
        geometry_due = start
        cursor_due = start
        last_cursor = None
        cursor_moved_at = start
        last_error = ""
        while not stopped and godot.poll() is None:
            now = time.monotonic()
            if args.seconds and now - start >= args.seconds:
                break
            if hana:
                hana.passo(now)
                pid_hana = hana.processo.pid if hana.processo else None
                if info.get("hana") != pid_hana:
                    info["hana"] = pid_hana
                    info["hana_starttime"] = identity(pid_hana) if pid_hana else None
                    bridge.atomic_json(RUNTIME / "pids.json", info)
            if now >= geometry_due:
                try:
                    data = bridge.snapshot()
                    data["last_activity"] = last_activity
                    bridge.atomic_json(RUNTIME / "desktop.json", data)
                    last_error = ""
                except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
                    if str(exc) != last_error:
                        print("Ponte IPC:", exc, flush=True)
                        last_error = str(exc)
                    # Falha fechada: invisível e sem região de entrada até reconectar.
                    data["fullscreen"] = True
                    bridge.atomic_json(RUNTIME / "desktop.json", data)
                geometry_due = now + 0.3
            if now >= cursor_due:
                state = {}
                try:
                    data["cursor"] = bridge.query("cursorpos")
                    if data["cursor"] != last_cursor:
                        last_cursor = data["cursor"]
                        cursor_moved_at = now
                    state = json.loads((RUNTIME / "status.json").read_text()) if (RUNTIME / "status.json").exists() else {}
                    if state.get("driver") and state["driver"].lower() != args.driver:
                        raise RuntimeError("Godot trocou o driver solicitado; veja godot.log")
                    enabled = bridge.accepts_mouse(state,
                        data["cursor"]["x"] - data["monitor"]["x"],
                        data["cursor"]["y"] - data["monitor"]["y"], godot.pid)
                    if enabled != last_gate:
                        response = bridge.ipc(f'/eval hl.window_rule({{name="{rule}",no_focus={str(not enabled).lower()}}})')
                        if response.strip() != "ok": raise RuntimeError("Gate: " + response)
                        last_gate = enabled
                    bridge.atomic_json(RUNTIME / "desktop.json", data)
                except (OSError, ValueError):
                    if last_gate is not False:
                        bridge.set_gate(rule, False, True)
                        last_gate = False
                sleeping = state.get("estado") in ("cochilo", "dormindo")
                active_mouse = now - cursor_moved_at < 0.5 or state.get("pressionada") or state.get("menu")
                rate = 60 if active_mouse else (10 if sleeping else 20)
                cursor_due = now + 1 / rate
            ready, _, _ = select.select([events], [], [], max(0, min(geometry_due, cursor_due)-time.monotonic()))
            if ready:
                chunk = events.recv(65536)
                if not chunk:
                    raise ConnectionError("Hyprland encerrou a conexão IPC")
                if b"kk-mascote-input" in chunk:
                    last_activity = time.time()
                if b"kk-mascote-boneca" in chunk and last_gate and not data.get("fullscreen") and not data.get("game_mode"):
                    bridge.atomic_json(RUNTIME / "comando.json", {"boneca_seguinte": True, "nonce": time.time_ns()})
                geometry_due = min(geometry_due, time.monotonic()+0.03)
                # reload (modo jogo desligado) elimina regras temporárias: reaplica só a nossa.
                if b"configreloaded>>" in chunk:
                    instalar()
                    last_gate = None
        if godot.poll() not in (None, 0):
            raise RuntimeError(f"Godot encerrou ({godot.returncode}); consulte {RUNTIME/'godot.log'}")
    finally:
        print(time.strftime("%Y-%m-%d %H:%M:%S"), "ENCERRAMENTO:",
              "sinal SIGTERM/SIGINT" if stopped else ("godot saiu com código %s" % godot.returncode if godot and godot.poll() is not None else "erro/fim do laço"),
              "|", repr(sys.exc_info()[1]) if sys.exc_info()[1] else "", flush=True)
        if not args.prova:
            try:
                state = json.loads((RUNTIME / "status.json").read_text())
                if state.get("pid") == (godot.pid if godot else None):
                    saved = Path.home() / ".cache/forja/kk-mascote.json"
                    saved.parent.mkdir(parents=True, exist_ok=True)
                    bridge.atomic_json(saved, state["preferencias"])
            except (OSError, ValueError, KeyError):
                pass
        if events:
            events.close()
        if hana:
            hana.fechar()
        if hana_log:
            hana_log.close()
        if chat and chat.poll() is None:
            chat.terminate()
            try:
                chat.wait(timeout=3)
            except subprocess.TimeoutExpired:
                chat.kill()
                chat.wait()
        if godot and godot.poll() is None:
            godot.terminate()
            try:
                godot.wait(timeout=5)
            except subprocess.TimeoutExpired:
                godot.kill()
                godot.wait()
        if display_alias:
            display_alias.unlink(missing_ok=True)
        if installed:
            try:
                hypr_lua(f'''if _G["{rule}"] then _G["{rule}"]:set_enabled(false); _G["{rule}"] = nil end
                    if _G["{listeners}"] then for _,s in ipairs(_G["{listeners}"]) do s:remove() end; _G["{listeners}"] = nil end''')
            except Exception as exc:
                print("Falha ao desativar regra:", exc, flush=True)
        (RUNTIME / "pids.json").unlink(missing_ok=True)
        (RUNTIME / "desktop.json").unlink(missing_ok=True)
        (RUNTIME / "comando.json").unlink(missing_ok=True)
        lock.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--driver", choices=["x11", "wayland"], default="x11")
    parser.add_argument("--gpu", choices=["intel", "inherit"], default="intel")
    parser.add_argument("--seconds", type=float, default=0)
    parser.add_argument("--teste-clique", action="store_true")
    parser.add_argument("--prova", action="store_true", help="Poses determinísticas; não altera posição/escala salvas")
    parser.add_argument("--retrato", action="store_true", help="Inicia em modo cabeça e ombros")
    parser.add_argument("--perfil", action="store_true", help="Inicia com o rosto ampliado e moldura")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--parar", action="store_true")
    parser.add_argument("--foreground", action="store_true")
    args = parser.parse_args()
    RUNTIME.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = open(RUNTIME / "instancia.lock", "a+")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        try:
            info = json.loads((RUNTIME/"pids.json").read_text())
        except (OSError, ValueError):
            print("Instância iniciando; repita em um segundo.")
            return
        if own_alive(info):
            if args.status:
                print(json.dumps(info, ensure_ascii=False, indent=2))
            else:
                os.kill(info["runner"], signal.SIGTERM)
                for _ in range(60):
                    if not (RUNTIME/"pids.json").exists() and not own_alive(info): break
                    time.sleep(0.1)
                if own_alive(info):
                    print("Encerramento ainda em andamento; consulte runner.log.")
                    sys.exit(1)
                print("Mascote desligado.")
        return
    if args.status or args.parar:
        print("Mascote desligado.")
        return
    for name in ["status.json", "comando.json"]:
        (RUNTIME / name).unlink(missing_ok=True)
    if args.teste_clique:
        print("Teste de clique: clique no vazio (deve atingir o desktop) e na Chika; arraste/rodinha/menu.\n"
              "Use iniciar.sh novamente para fechar. Logs: " + str(RUNTIME), flush=True)
    if args.foreground:
        run(args, lock)
        return
    child = os.fork()
    if child:
        # A descrição de arquivo compartilhada mantém o flock no supervisor.
        lock.close()
        for _ in range(80):
            try:
                info = json.loads((RUNTIME/"pids.json").read_text())
                state = json.loads((RUNTIME/"status.json").read_text())
                if own_alive(info) and state.get("pid") == info["godot"] and (state.get("hull") or state.get("hidden")):
                    print("Chika ligada; iniciar.sh novamente desliga. Logs: " + str(RUNTIME))
                    return
            except (OSError, ValueError, KeyError):
                pass
            done, _ = os.waitpid(child, os.WNOHANG)
            if done:
                break
            time.sleep(0.1)
        try:
            info = json.loads((RUNTIME/"pids.json").read_text())
            if info.get("runner") == child and own_alive(info):
                os.kill(child, signal.SIGTERM)
        except (OSError, ValueError):
            pass
        print("Falha ao iniciar; consulte " + str(RUNTIME/"runner.log"))
        sys.exit(1)
    os.setsid()
    # Guarda os logs da execução anterior para diagnosticar quedas.
    for nome in ("runner", "godot"):
        if (RUNTIME / f"{nome}.log").exists():
            os.replace(RUNTIME / f"{nome}.log", RUNTIME / f"{nome}.anterior.log")
    with open(RUNTIME / "runner.log", "w") as log:
        os.dup2(log.fileno(), 1)
        os.dup2(log.fileno(), 2)
        null = os.open(os.devnull, os.O_RDONLY)
        os.dup2(null, 0)
        os.close(null)
        try:
            run(args, lock)
        except Exception as exc:
            print(str(exc), flush=True)
            sys.exit(1)


if __name__ == "__main__":
    main()
