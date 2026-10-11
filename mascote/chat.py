#!/usr/bin/env python3
"""Janela de chat ao lado da personagem (GTK3 + layer-shell, camada top).

Mostra o histórico (chat_dados), a mensagem que ela está escrevendo (runtime/chat/escrevendo.json,
publicada pelo Godot) e um campo para o usuário escrever. Só aparece com o Modo mensagens ligado
e a personagem visível. Iniciada/encerrada pelo supervisor (executar.py).
"""
import json
import os
import sys
import time

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import GLib, Gtk, Gdk, GtkLayerShell, Pango

import chat_dados as dados

LARGURA, ALTURA = 340, 430
CSS = b"""
window { background: transparent; }
.painel { background: rgba(20,16,13,0.94); border: 1px solid #5a3a12; border-radius: 14px; }
.topo { padding: 8px 12px; border-bottom: 1px solid #3a2a14; }
.nome { color: #FFC24D; font-weight: 700; font-size: 13px; }
.estado { color: #b89a74; font-size: 11px; font-style: italic; }
.lista { background: transparent; padding: 6px 8px; }
.bolha { border-radius: 12px; padding: 7px 10px; font-size: 13px; }
.dela { background: #2b2118; color: #f3e6d6; border: 1px solid #4a3418; }
.minha { background: #F08A0C; color: #1a1006; }
.escrevendo { background: #241c15; color: #e9d8c3; border: 1px dashed #6b4a1c; }
.hora { color: #8a7660; font-size: 9px; }
.entrada { background: #1c1611; color: #f3e6d6; border: 1px solid #4a3418; border-radius: 10px; padding: 6px 8px; caret-color: #FF9E1B; }
.enviar { background: #FF9E1B; color: #1a1006; border-radius: 10px; font-weight: 700; padding: 4px 10px; border: none; }
.min { background: transparent; color: #FFC24D; border: none; padding: 0 6px; }
"""
FASES = {"lendo": "visualizou…", "reagindo": "…", "pensando": "pensando…",
         "digitando": "digitando…", "apagando": "digitando…", "enviando": "digitando…"}


def status():
    try:
        s = json.loads((dados.RUNTIME / "status.json").read_text())
    except (OSError, ValueError):
        return {}
    return s if time.time() - float(s.get("timestamp", 0)) < 8 else {}


def nome_boneca(ident):
    try:
        cat = json.loads((dados.Path(__file__).resolve().parent.parent / "bonecas/catalogo.json").read_text())
        for b in cat if isinstance(cat, list) else cat.get("bonecas", []):
            if b.get("id") == ident:
                return b.get("nome", ident)
    except (OSError, ValueError, AttributeError):
        pass
    return ident.replace("-", " ").title() if ident else "Chika"


class Chat(Gtk.Window):
    def __init__(self, camada=True):
        super().__init__(title="kk-mascote-chat")
        self.camada = camada
        if camada:
            self.iniciar_camada()
        self.montar()

    def iniciar_camada(self):
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_namespace(self, "kk-mascote-chat")
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.TOP)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, True)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.ON_DEMAND)

    def montar(self):
        self.set_app_paintable(True)
        visual = self.get_screen().get_rgba_visual()
        if visual:
            self.set_visual(visual)
        prov = Gtk.CssProvider()
        prov.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        painel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        painel.get_style_context().add_class("painel")
        self.add(painel)
        topo = Gtk.Box(spacing=6)
        topo.get_style_context().add_class("topo")
        textos = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.lbl_nome = Gtk.Label(xalign=0)
        self.lbl_nome.get_style_context().add_class("nome")
        self.lbl_estado = Gtk.Label(xalign=0)
        self.lbl_estado.get_style_context().add_class("estado")
        textos.pack_start(self.lbl_nome, False, False, 0)
        textos.pack_start(self.lbl_estado, False, False, 0)
        topo.pack_start(textos, True, True, 0)
        self.btn_min = Gtk.Button(label="–")
        self.btn_min.get_style_context().add_class("min")
        self.btn_min.connect("clicked", self.alternar)
        topo.pack_end(self.btn_min, False, False, 0)
        painel.pack_start(topo, False, False, 0)

        self.corpo = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.rolagem = Gtk.ScrolledWindow()
        self.rolagem.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.rolagem.set_size_request(LARGURA, ALTURA - 110)
        self.lista = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.lista.get_style_context().add_class("lista")
        self.rolagem.add(self.lista)
        self.corpo.pack_start(self.rolagem, True, True, 0)
        linha = Gtk.Box(spacing=6, margin=8)
        self.entrada = Gtk.Entry(placeholder_text="Escreva para ela…")
        self.entrada.get_style_context().add_class("entrada")
        self.entrada.set_max_length(dados.TAMANHO)
        self.entrada.connect("activate", self.enviar)
        enviar = Gtk.Button(label="Enviar")
        enviar.get_style_context().add_class("enviar")
        enviar.connect("clicked", self.enviar)
        linha.pack_start(self.entrada, True, True, 0)
        linha.pack_start(enviar, False, False, 0)
        self.corpo.pack_start(linha, False, False, 0)
        painel.pack_start(self.corpo, True, True, 0)

        self.minimizado = False
        self.assinatura = None
        self.bolha_viva = None
        self.margem = None
        self.boneca = ""
        self.connect("destroy", Gtk.main_quit)
        self.show_all()
        self.hide()
        GLib.timeout_add(80, self.tique)

    def alternar(self, *_):
        self.minimizado = not self.minimizado
        self.corpo.set_visible(not self.minimizado)
        self.btn_min.set_label("+" if self.minimizado else "–")
        self.resize(LARGURA, 1)

    def enviar(self, *_):
        texto = self.entrada.get_text().strip()
        if not texto:
            return
        self.entrada.set_text("")
        try:
            dados.registrar("usuario", texto, boneca=self.boneca, avisar=True)
        except ValueError:
            return
        self.assinatura = None

    def bolha(self, texto, minha, classe=None):
        caixa = Gtk.Box()
        lbl = Gtk.Label(label=texto, xalign=0)
        lbl.set_line_wrap(True)
        lbl.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        lbl.set_max_width_chars(34)
        lbl.set_selectable(True)
        ctx = lbl.get_style_context()
        ctx.add_class("bolha")
        ctx.add_class(classe or ("minha" if minha else "dela"))
        if minha:
            caixa.pack_end(lbl, False, False, 0)
        else:
            caixa.pack_start(lbl, False, False, 0)
        return caixa, lbl

    def redesenhar(self, msgs):
        for filho in self.lista.get_children():
            self.lista.remove(filho)
        for m in msgs:
            caixa, _ = self.bolha(m.get("texto", ""), m.get("origem") == "usuario")
            self.lista.pack_start(caixa, False, False, 0)
        caixa, self.bolha_viva = self.bolha("", False, "escrevendo")
        self.caixa_viva = caixa
        self.lista.pack_start(caixa, False, False, 0)
        self.lista.show_all()
        caixa.hide()
        GLib.idle_add(self.rolar_fim)

    def rolar_fim(self):
        adj = self.rolagem.get_vadjustment()
        adj.set_value(adj.get_upper())
        return False

    def posicionar(self, st):
        hull = st.get("hull") or []
        if not hull:
            return
        xs = [p[0] for p in hull]
        ys = [p[1] for p in hull]
        mon = self.get_display().get_monitor_at_window(self.get_window()) if self.get_window() else None
        larg = mon.get_geometry().width if mon else 1920
        alt = mon.get_geometry().height if mon else 1080
        x = max(xs) + 14
        if x + LARGURA > larg - 8:
            x = min(xs) - LARGURA - 14
        x = int(min(max(8, x), larg - LARGURA - 8))
        y = int(min(max(8, min(ys) + 30), alt - ALTURA - 8))
        if self.camada and (self.margem is None or abs(self.margem[0] - x) > 6 or abs(self.margem[1] - y) > 6):
            self.margem = (x, y)
            GtkLayerShell.set_margin(self, GtkLayerShell.Edge.LEFT, x)
            GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, y)

    def tique(self):
        st = status()
        prefs = st.get("preferencias", {})
        visivel = bool(st) and prefs.get("modo_mensagens") and not st.get("hidden")
        if not visivel:
            if self.get_visible():
                self.hide()
            return True
        if not self.get_visible():
            self.show()
            self.corpo.set_visible(not self.minimizado)
        self.boneca = prefs.get("boneca", "")
        self.lbl_nome.set_text(nome_boneca(self.boneca))
        self.posicionar(st)
        msgs = dados.listar()
        assinatura = (len(msgs), msgs[-1]["id"] if msgs else "")
        if assinatura != self.assinatura:
            self.assinatura = assinatura
            self.redesenhar(msgs)
        viva = dados.escrevendo()
        fase = viva.get("fase", "") if viva and time.time() - float(viva.get("timestamp", 0)) < 5 else ""
        self.lbl_estado.set_text(FASES.get(fase, "online"))
        texto = viva.get("texto", "") if fase in ("digitando", "apagando", "pensando", "enviando") else ""
        if texto:
            self.bolha_viva.set_text(texto + ("▍" if fase != "pensando" else ""))
            if not self.caixa_viva.get_visible():
                self.caixa_viva.show_all()
                GLib.idle_add(self.rolar_fim)
        elif self.caixa_viva.get_visible():
            self.caixa_viva.hide()
        return True


def main():
    if "--prova" in sys.argv:
        # Janela comum (sem layer-shell) para capturas em tela virtual; usa MASCOTE_CHAT/RUNTIME de teste.
        Chat(camada=False)
        Gtk.main()
        return 0
    if not GtkLayerShell.is_supported():
        print("layer-shell indisponível", file=sys.stderr)
        return 1
    Chat()
    Gtk.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
