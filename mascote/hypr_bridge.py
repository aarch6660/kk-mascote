#!/usr/bin/env python3
"""Snapshot Hyprland: hyprctl --once; IPC + socket2 no modo contínuo."""
import argparse
import json
import os
from pathlib import Path
import select
import signal
import socket
import subprocess
import time


def socket_dir():
    return Path(os.environ["XDG_RUNTIME_DIR"]) / "hypr" / os.environ["HYPRLAND_INSTANCE_SIGNATURE"]


def query(command, cli=False):
    if cli:
        return json.loads(subprocess.check_output(["hyprctl", "-j", command], timeout=2))
    return json.loads(ipc("j/" + command))


def ipc(command):
    with socket.socket(socket.AF_UNIX) as connection:
        connection.settimeout(2)
        connection.connect(str(socket_dir() / ".socket.sock"))
        connection.sendall(command.encode())
        chunks = []
        while chunk := connection.recv(65536):
            chunks.append(chunk)
    return b"".join(chunks).decode()


def inside_polygon(x, y, polygon):
    inside = False
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        if (a[1] > y) != (b[1] > y) and x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]:
            inside = not inside
    return inside


def accepts_mouse(state, x, y, pid=None):
    """Falha libera o desktop; menu não captura o vazio do casco convexo."""
    if state.get("hidden", True) or (pid is not None and state.get("pid") != pid):
        return False
    if time.time() - state.get("timestamp", 0) > 2:
        return False
    if state.get("pressionada", False) or state.get("arrastando", False):
        return True  # Mantém o grab até soltar, inclusive ao sair do contorno.
    if inside_polygon(x, y, state.get("hull", [])):
        return True
    if state.get("menu"):
        rx, ry, rw, rh = state.get("menu_rect", [0, 0, 0, 0])
        return rx <= x < rx + rw and ry <= y < ry + rh
    return False


def set_gate(rule, enabled, lua):
    # Altera só a regra temporária pertencente a esta execução.
    value = "false" if enabled else "true"
    if lua:
        response = ipc(f'/eval hl.window_rule({{name="{rule}", no_focus={value}}})')
    else:
        response = ipc(f'/keyword windowrule[{rule}]:no_focus {value}')
    if response.strip() != "ok":
        raise RuntimeError("Não foi possível alterar gate: " + response)


def snapshot(cli=False):
    clients = query("clients", cli)
    monitors = query("monitors", cli)
    monitor = next((m for m in monitors if m.get("focused")), monitors[0])
    workspace = monitor["activeWorkspace"]["id"]
    special = monitor.get("specialWorkspace", {}).get("id", 0)
    active = query("activewindow", cli)
    scale = monitor["scale"]
    width, height = monitor["width"], monitor["height"]
    if monitor.get("transform", 0) in (1, 3, 5, 7):
        width, height = height, width
    width, height = round(width / scale), round(height / scale)
    keys = ("address", "at", "size", "workspace", "monitor", "floating", "pinned",
            "fullscreen", "fullscreenClient", "mapped", "hidden", "class", "pid", "xwayland")
    clients = [{k: c.get(k) for k in keys} for c in clients if c.get("class") != "kk-mascote"]
    visible = [c for c in clients if c["mapped"] and not c["hidden"] and
               c["monitor"] == monitor["id"] and
               (c["workspace"]["id"] == (special or workspace) or c["pinned"])]
    focused = next((c for c in visible if c["address"] == active.get("address")), {})
    option = query("getoption animations:enabled", cli)
    game_mode = not bool(option.get("bool", option.get("int", 1)))
    cursor = query("cursorpos", cli)
    return {"timestamp": time.time(), "workspace": workspace, "special": special,
            "monitor": {"id": monitor["id"], "x": monitor["x"], "y": monitor["y"],
                        "width": width, "height": height, "scale": scale,
                        "reserved": monitor.get("reserved", [0,0,0,0])},
            "cursor": cursor, "game_mode": game_mode, "focused": focused,
            "floors": [{"address": c["address"], "x": c["at"][0] - monitor["x"],
                        "y": c["at"][1] - monitor["y"], "width": c["size"][0], "class": c["class"]}
                       for c in visible],
            "fullscreen": any((c.get("fullscreen") or 0) & 2 for c in visible)}


def atomic_json(path, data):
    path = Path(path)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False))
    tmp.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="Consulta usando hyprctl e imprime JSON")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--gate-rule")
    parser.add_argument("--lua", action="store_true")
    args = parser.parse_args()
    if args.once:
        print(json.dumps(snapshot(cli=True), indent=2, ensure_ascii=False))
        return
    if not args.output:
        parser.error("use --once ou --output CAMINHO")
    signal.signal(signal.SIGTERM, lambda *_: exit(0))
    events = None
    try:
        events = socket.socket(socket.AF_UNIX)
        events.connect(str(socket_dir() / ".socket2.sock"))
        events.setblocking(False)
        next_poll = 0.0
        next_gate = 0.0
        last_gate = None
        while True:
            now = time.monotonic()
            if args.gate_rule and now >= next_gate:
                enabled = False
                try:
                    state = json.loads(args.output.with_name("input.json").read_text())
                    cursor = query("cursorpos")
                    enabled = not state["hidden"] and (state["dragging"] or inside_polygon(cursor["x"], cursor["y"], state["hull"]))
                except (OSError, ValueError, KeyError):
                    pass  # Falha fechada para o mascote: libera o desktop.
                if enabled != last_gate:
                    set_gate(args.gate_rule, enabled, args.lua)
                    last_gate = enabled
                next_gate = time.monotonic() + 1 / 60
            if now >= next_poll:
                try:
                    atomic_json(args.output, snapshot())
                except (OSError, ValueError, KeyError) as exc:
                    atomic_json(args.output, {"error": str(exc), "timestamp": time.time()})
                next_poll = time.monotonic() + 0.5
            deadline = min(next_poll, next_gate) if args.gate_rule else next_poll
            ready, _, _ = select.select([events], [], [], max(0, deadline - time.monotonic()))
            if ready:
                data = events.recv(65536)
                if not data:
                    raise ConnectionError("socket2 desconectou")
                # Coalesce eventos; geometria é também consultada a cada 500 ms.
                next_poll = min(next_poll, time.monotonic() + 0.05)
    finally:
        if events:
            events.close()


if __name__ == "__main__":
    main()
