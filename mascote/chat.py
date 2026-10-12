#!/usr/bin/env python3
"""Janela de chat da personagem (GTK3 + layer-shell, camada top).

Mostra o histórico (chat_dados), a mensagem que ela está escrevendo (runtime/chat/escrevendo.json,
publicada pelo Godot) e um campo para o usuário escrever. Só aparece com o Modo mensagens ligado.
Iniciada/encerrada pelo supervisor (executar.py).

Formas (menu ⚙, salvas em ~/.local/share/kk-mascote/chat.json):
- personagem: ao lado dela, acompanhando (some quando ela está escondida);
- gaveta: presa numa borda; fechada vira um fio. Duas passadas rápidas do mouse mostram o puxador,
  que se clica ou puxa; arrastá-lo ao longo da borda muda o lugar. Mensagens novas viram um contador;
- solta: janela livre, arrastada pelo topo.
"""
import json
import os
import sys
import time
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import GLib, Gtk, Gdk, GtkLayerShell, Pango

import chat_dados as dados

CONFIG = Path.home() / ".local/share/kk-mascote/chat.json"
LARGURA, ALTURA = 360, 460            # tamanho inicial; o usuário redimensiona pela alça ⤡
MIN_L, MIN_A, MAX_L = 280, 240, 720
MARGEM_TELA = 8
RESERVA_TOPO = 64                     # barra do topo (zona exclusiva) não entra na conta do layer-shell
FIO, PUXADOR_LARG, PUXADOR_COMP = 5, 30, 96
DUPLA_PASSADA = 0.9                   # s entre duas entradas do mouse no fio
DICA_DURA = 3.0                       # s que o puxador fica visível sem o mouse em cima
PADRAO = {"modo": "personagem", "borda": "direita", "desloc": 300, "solta": [200, 200],
          "puxador": "escondido", "fechar_fora": True, "lido_ate": 0.0,
          "largura": LARGURA, "altura": ALTURA}
CSS = b"""
window { background: transparent; }
.painel { background: rgba(20,16,13,0.95); border: 1px solid #5a3a12; border-radius: 14px; }
.topo { padding: 6px 6px 6px 12px; border-bottom: 1px solid #3a2a14; }
.nome { color: #FFC24D; font-weight: 700; font-size: 13px; }
.estado { color: #b89a74; font-size: 11px; font-style: italic; }
.lista { background: transparent; padding: 8px 10px; }
scrolledwindow, viewport { background: transparent; border: none; }
.bolha { border-radius: 12px; padding: 7px 10px; font-size: 13px; }
.bolha selection { background: rgba(255,194,77,0.35); color: inherit; }
.dela { background: #2b2118; color: #f3e6d6; border: 1px solid #4a3418; border-bottom-left-radius: 4px; }
.minha { background: #F08A0C; color: #1a1006; border-bottom-right-radius: 4px; }
.escrevendo { background: #241c15; color: #e9d8c3; border: 1px dashed #6b4a1c; border-bottom-left-radius: 4px; }
.hora { color: #8a7660; font-size: 9px; margin: 1px 4px 0 4px; }
.entrada { background: #1c1611; color: #f3e6d6; border: 1px solid #4a3418; border-radius: 10px; padding: 6px 8px; caret-color: #FF9E1B; }
.enviar { background: #FF9E1B; color: #1a1006; border-radius: 10px; font-weight: 700; padding: 4px 10px; border: none; }
.min, .alca, .engrenagem { background: transparent; color: #FFC24D; border: none; padding: 0 6px; min-height: 0; min-width: 0; }
.alca, .engrenagem { color: #b89a74; }
.alca:hover, .engrenagem:hover, .min:hover { color: #FFE0A0; }
.puxador { background: rgba(32,24,17,0.96); border: 1px solid #6b4a1c; color: #FFC24D; }
.puxador.fio { background: rgba(255,158,27,0.35); border: none; }
.puxador.novas { background: #F08A0C; color: #1a1006; border-color: #FFC24D; }
.puxador.novas.fio { background: #FF9E1B; }
.puxador.pulso { background: #FFC24D; }
.puxador.esquerda { border-left: none; border-radius: 0 10px 10px 0; }
.puxador.direita { border-right: none; border-radius: 10px 0 0 10px; }
.puxador.cima { border-top: none; border-radius: 0 0 10px 10px; }
.puxador.baixo { border-bottom: none; border-radius: 10px 10px 0 0; }
.puxador.fio { border-radius: 3px; }
.painel.g-esquerda { border-left: none; border-radius: 0 14px 14px 0; }
.painel.g-direita { border-right: none; border-radius: 14px 0 0 14px; }
.painel.g-cima { border-top: none; border-radius: 0 0 14px 14px; }
.painel.g-baixo { border-bottom: none; border-radius: 14px 14px 0 0; }
.contador { font-weight: 700; font-size: 12px; }
.icone { font-size: 15px; }
popover { background: #1c1611; border: 1px solid #5a3a12; }
popover label { color: #f3e6d6; }
popover .secao { color: #FFC24D; font-weight: 700; font-size: 11px; margin-top: 6px; }
popover radiobutton, popover checkbutton { color: #f3e6d6; padding: 2px 4px; }
popover button.plano { background: transparent; border: 1px solid #4a3418; color: #f3e6d6; margin-top: 6px; }
"""
FASES = {"lendo": "visualizou…", "reagindo": "visualizou…", "pensando": "digitando…", "visto": "online",
         "digitando": "digitando…", "apagando": "digitando…", "enviando": "digitando…"}
BORDAS = {"esquerda": "Esquerda", "direita": "Direita", "cima": "Em cima", "baixo": "Embaixo"}
MODOS = {"personagem": "Seguir a personagem", "gaveta": "Gaveta na borda", "solta": "Janela solta"}
PUXADORES = {"escondido": "Escondido (2 passadas do mouse)", "sempre": "Sempre visível",
             "abrir": "Abrir direto com 2 passadas"}


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


def ler_config():
    cfg = dict(PADRAO)
    try:
        lido = json.loads(CONFIG.read_text())
        if isinstance(lido, dict):
            cfg.update({k: v for k, v in lido.items() if k in PADRAO and type(v) is type(PADRAO[k])
                        or (k in ("lido_ate", "desloc") and isinstance(v, (int, float)))})
    except (OSError, ValueError):
        pass
    if cfg["modo"] not in MODOS:
        cfg["modo"] = PADRAO["modo"]
    if cfg["borda"] not in BORDAS:
        cfg["borda"] = PADRAO["borda"]
    if cfg["puxador"] not in PUXADORES:
        cfg["puxador"] = PADRAO["puxador"]
    if not cfg["lido_ate"]:
        # Primeira vez: o histórico antigo não conta como "novas".
        cfg["lido_ate"] = max((float(m.get("criado_em", 0)) for m in dados.listar()), default=time.time())
    return cfg


def gravar_config(cfg):
    try:
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        tmp = CONFIG.with_suffix(".tmp")
        tmp.write_text(json.dumps(cfg))
        os.replace(tmp, CONFIG)
    except OSError:
        pass


def suave(t):
    return 1 - (1 - t) ** 3


class Chat(Gtk.Window):
    def __init__(self, camada=True):
        super().__init__(title="kk-mascote-chat")
        self.camada = camada
        self.cfg = ler_config()
        self.largura, self.altura = int(self.cfg["largura"]), int(self.cfg["altura"])
        if camada:
            GtkLayerShell.init_for_window(self)
            GtkLayerShell.set_namespace(self, "kk-mascote-chat")
            GtkLayerShell.set_layer(self, GtkLayerShell.Layer.TOP)
            GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.ON_DEMAND)
        self.ancoras = {}
        self.margens = {}
        self.montar()

    # ================= montagem =================
    def montar(self):
        self.set_app_paintable(True)
        visual = self.get_screen().get_rgba_visual()
        if visual:
            self.set_visual(visual)
        prov = Gtk.CssProvider()
        prov.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.painel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.painel.get_style_context().add_class("painel")
        topo_ev = Gtk.EventBox()   # arrastar o topo move a janela solta / a gaveta ao longo da borda
        topo_ev.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK
                           | Gdk.EventMask.POINTER_MOTION_MASK)
        topo_ev.connect("button-press-event", self.topo_apertar)
        topo_ev.connect("motion-notify-event", self.topo_mover)
        topo_ev.connect("button-release-event", self.topo_soltar)
        topo = Gtk.Box(spacing=2)
        topo.get_style_context().add_class("topo")
        topo_ev.add(topo)
        textos = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.lbl_nome = Gtk.Label(xalign=0)
        self.lbl_nome.get_style_context().add_class("nome")
        self.lbl_nome.set_ellipsize(Pango.EllipsizeMode.END)
        self.lbl_estado = Gtk.Label(xalign=0)
        self.lbl_estado.get_style_context().add_class("estado")
        textos.pack_start(self.lbl_nome, False, False, 0)
        textos.pack_start(self.lbl_estado, False, False, 0)
        topo.pack_start(textos, True, True, 0)
        self.btn_min = Gtk.Button(label="–")
        self.btn_min.get_style_context().add_class("min")
        self.btn_min.connect("clicked", self.alternar)
        topo.pack_end(self.btn_min, False, False, 0)
        # Alça de tamanho: arrastar para longe da âncora aumenta; duplo clique volta ao padrão.
        self.alca = Gtk.EventBox()
        self.alca.add(Gtk.Label(label="⤡"))
        self.alca.get_style_context().add_class("alca")
        self.alca.set_tooltip_text("Arraste para redimensionar (duplo clique: tamanho padrão)")
        self.alca.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK
                             | Gdk.EventMask.POINTER_MOTION_MASK)
        self.alca.connect("button-press-event", self.alca_apertar)
        self.alca.connect("motion-notify-event", self.alca_mover)
        self.alca.connect("button-release-event", self.alca_soltar)
        self.alca.connect("realize", lambda w: w.get_window().set_cursor(
            Gdk.Cursor.new_from_name(w.get_display(), "nwse-resize")))
        topo.pack_end(self.alca, False, False, 0)
        self.btn_cfg = Gtk.MenuButton(label="⚙")
        self.btn_cfg.get_style_context().add_class("engrenagem")
        self.btn_cfg.set_tooltip_text("Forma do chat")
        self.btn_cfg.set_popover(self.montar_menu())
        topo.pack_end(self.btn_cfg, False, False, 0)
        self.painel.pack_start(topo_ev, False, False, 0)

        self.corpo = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.rolagem = Gtk.ScrolledWindow()
        self.rolagem.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.rolagem.set_vexpand(True)
        self.lista = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.lista.get_style_context().add_class("lista")
        self.lista.set_valign(Gtk.Align.END)   # poucas mensagens ficam embaixo, perto do campo
        self.rolagem.add(self.lista)
        self.corpo.pack_start(self.rolagem, True, True, 0)
        adj = self.rolagem.get_vadjustment()
        # Rola sozinho só se o usuário já estava no fim; lendo o histórico, nada pula.
        self.no_fim = True
        adj.connect("value-changed", self.lembrar_fim)
        adj.connect("changed", self.manter_fim)
        linha = Gtk.Box(spacing=6, margin=8)
        self.entrada = Gtk.Entry(placeholder_text="Escreva para ela…")
        self.entrada.get_style_context().add_class("entrada")
        self.entrada.set_max_length(dados.TAMANHO)
        self.entrada.connect("activate", self.enviar)
        self.entrada.connect("key-press-event", self.tecla)
        enviar = Gtk.Button(label="Enviar")
        enviar.get_style_context().add_class("enviar")
        enviar.connect("clicked", self.enviar)
        linha.pack_start(self.entrada, True, True, 0)
        linha.pack_start(enviar, False, False, 0)
        self.corpo.pack_start(linha, False, False, 0)
        self.painel.pack_start(self.corpo, True, True, 0)

        # Recorte da gaveta: o painel tem tamanho fixo e só a parte "puxada" aparece.
        self.recorte = Gtk.ScrolledWindow()
        self.recorte.set_policy(Gtk.PolicyType.EXTERNAL, Gtk.PolicyType.EXTERNAL)
        self.recorte.set_shadow_type(Gtk.ShadowType.NONE)
        self.recorte.add(self.painel)
        self.recorte.connect("scroll-event", lambda *_: True)
        self.recorte.get_hadjustment().connect("changed", self.ajustar_recorte)
        self.recorte.get_vadjustment().connect("changed", self.ajustar_recorte)
        self.chave_gaveta = None

        self.puxador = Gtk.EventBox()
        self.puxador.get_style_context().add_class("puxador")
        self.puxador.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK
                                | Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.ENTER_NOTIFY_MASK
                                | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.puxador.connect("enter-notify-event", self.pux_entrar)
        self.puxador.connect("leave-notify-event", self.pux_sair)
        self.puxador.connect("button-press-event", self.pux_apertar)
        self.puxador.connect("motion-notify-event", self.pux_mover)
        self.puxador.connect("button-release-event", self.pux_soltar)
        self.pux_caixa = Gtk.Box(spacing=2)
        self.pux_caixa.set_halign(Gtk.Align.CENTER)
        self.pux_caixa.set_valign(Gtk.Align.CENTER)
        self.pux_icone = Gtk.Label(label="💬")
        self.pux_icone.get_style_context().add_class("icone")
        self.pux_contador = Gtk.Label()
        self.pux_contador.get_style_context().add_class("contador")
        self.pux_caixa.pack_start(self.pux_icone, False, False, 0)
        self.pux_caixa.pack_start(self.pux_contador, False, False, 0)
        self.puxador.add(self.pux_caixa)

        self.raiz = Gtk.Box()
        self.add(self.raiz)

        self.minimizado = False
        self.ids = []
        self.labels = []
        self.margem_personagem = None
        self.lado_esq = True
        self.arrasto = None          # alça de tamanho
        self.arrasto_topo = None     # mover pela barra do topo
        self.arrasto_pux = None      # puxar/mover o puxador
        self.tela = (1920, 1080)
        self.boneca = ""
        self.abertura = 0.0          # gaveta: quanto do painel aparece (px ao longo do eixo)
        self.anim = None
        self.entradas_fio = []
        self.dica_ate = 0.0
        self.mouse_no_pux = False
        self.nao_lidas = 0
        self.ela_digitando = False
        self.ultimo_pulso = 0.0
        self.ultima_nova = 0.0
        self.caixa_viva, self.bolha_viva, _ = self.bolha("", False, "escrevendo")
        self.lista.pack_end(self.caixa_viva, False, False, 0)
        self.connect("destroy", Gtk.main_quit)
        self.connect("focus-out-event", self.foco_saiu)
        if os.environ.get("KK_CHAT_ABERTA"):   # testes: começa com a gaveta aberta
            self.abertura = self.tamanho_aberto()
        self.aplicar_forma()
        self.show_all()
        self.caixa_viva.hide()
        self.hide()
        GLib.timeout_add(80, self.tique)

    def montar_menu(self):
        pop = Gtk.Popover()
        caixa = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1, margin=10)
        pop.add(caixa)
        self.radios = {}

        def secao(titulo):
            l = Gtk.Label(label=titulo, xalign=0)
            l.get_style_context().add_class("secao")
            caixa.pack_start(l, False, False, 0)

        def grupo(chave, opcoes):
            primeiro = None
            for valor, rotulo in opcoes.items():
                r = Gtk.RadioButton.new_with_label_from_widget(primeiro, rotulo)
                primeiro = primeiro or r
                r.set_active(self.cfg[chave] == valor)
                r.connect("toggled", self.menu_escolher, chave, valor)
                caixa.pack_start(r, False, False, 0)
                self.radios[(chave, valor)] = r

        secao("Onde o chat fica")
        grupo("modo", MODOS)
        secao("Borda da gaveta")
        grupo("borda", BORDAS)
        secao("Puxador da gaveta")
        grupo("puxador", PUXADORES)
        fora = Gtk.CheckButton(label="Fechar a gaveta ao clicar fora")
        fora.set_active(self.cfg["fechar_fora"])
        fora.connect("toggled", lambda b: self.mudar("fechar_fora", b.get_active()))
        caixa.pack_start(fora, False, False, 0)
        padrao = Gtk.Button(label="Tamanho padrão")
        padrao.get_style_context().add_class("plano")
        padrao.connect("clicked", lambda *_: self.redimensionar(LARGURA, ALTURA, salvar=True))
        caixa.pack_start(padrao, False, False, 0)
        caixa.show_all()
        return pop

    def menu_escolher(self, botao, chave, valor):
        if botao.get_active() and self.cfg[chave] != valor:
            self.mudar(chave, valor)

    def mudar(self, chave, valor):
        self.cfg[chave] = valor
        gravar_config(self.cfg)
        if chave in ("modo", "borda"):
            self.btn_cfg.get_popover().popdown()
            self.minimizado = False
            self.corpo.set_visible(True)
            # Ao virar gaveta, já abre para o usuário ver onde ela ficou.
            self.abertura = self.tamanho_aberto() if self.cfg["modo"] == "gaveta" else 0
            self.margem_personagem = None
            self.aplicar_forma()

    # ================= geometria =================
    @property
    def gaveta(self):
        return self.cfg["modo"] == "gaveta"

    def eixo_x(self):
        return self.cfg["borda"] in ("esquerda", "direita")

    def tamanho_aberto(self):
        return self.largura if self.eixo_x() else self.altura

    def limites(self):
        larg, alt = self.tela
        return (max(MIN_L, min(MAX_L, larg - 2 * MARGEM_TELA - PUXADOR_LARG)),
                max(MIN_A, alt - RESERVA_TOPO - 2 * MARGEM_TELA))

    def ancorar(self, **lados):
        """lados: esquerda/direita/cima/baixo = margem (px) ou None (solto)."""
        mapa = {"esquerda": GtkLayerShell.Edge.LEFT, "direita": GtkLayerShell.Edge.RIGHT,
                "cima": GtkLayerShell.Edge.TOP, "baixo": GtkLayerShell.Edge.BOTTOM}
        novas = {k: v for k, v in lados.items() if v is not None}
        if not self.camada:
            self.ancoras, self.margens = set(novas), novas
            return
        if set(novas) != self.ancoras:
            for nome, borda in mapa.items():
                GtkLayerShell.set_anchor(self, borda, nome in novas)
            self.ancoras = set(novas)
        for nome, m in novas.items():
            if self.margens.get(nome) != int(m):
                GtkLayerShell.set_margin(self, mapa[nome], int(m))
        self.margens = {k: int(v) for k, v in novas.items()}

    def origem(self):
        """Canto superior esquerdo da superfície na tela (para arrastos estáveis)."""
        larg, alt = self.tela
        w, h = self.get_allocated_width(), self.get_allocated_height()
        m = self.margens
        x = m["esquerda"] if "esquerda" in m else (larg - w - m["direita"] if "direita" in m else (larg - w) / 2)
        y = m["cima"] if "cima" in m else (alt - h - m["baixo"] if "baixo" in m else (alt - h) / 2)
        return x, y

    def na_tela(self, widget, ev):
        r = widget.translate_coordinates(self, int(ev.x), int(ev.y))
        tx, ty = (r[-2], r[-1]) if r else (ev.x, ev.y)
        ox, oy = self.origem()
        return ox + tx, oy + ty

    def aplicar_forma(self):
        """Reorganiza a janela conforme modo/borda e reaplica tamanho e âncoras."""
        max_l, max_a = self.limites()
        self.largura = int(min(max(self.largura, MIN_L), max_l))
        self.altura = int(min(max(self.altura, MIN_A), max_a))
        chars = max(18, int(self.largura * 0.74 / 7.2))
        for lbl in self.labels + [self.bolha_viva]:
            lbl.set_max_width_chars(chars)
        for filho in self.raiz.get_children():
            self.raiz.remove(filho)
        ctx = self.puxador.get_style_context()
        ctx_p = self.painel.get_style_context()
        for b in BORDAS:
            ctx.remove_class(b)
            ctx_p.remove_class("g-" + b)
        if self.camada:
            # Gaveta/solta usam a tela inteira como referência; "personagem" respeita a barra do topo.
            GtkLayerShell.set_exclusive_zone(self, 0 if self.cfg["modo"] == "personagem" else -1)
        if self.gaveta:
            borda = self.cfg["borda"]
            ctx.add_class(borda)
            ctx_p.add_class("g-" + borda)
            self.raiz.set_orientation(Gtk.Orientation.HORIZONTAL if self.eixo_x() else Gtk.Orientation.VERTICAL)
            self.pux_caixa.set_orientation(Gtk.Orientation.VERTICAL if self.eixo_x() else Gtk.Orientation.HORIZONTAL)
            if borda in ("esquerda", "cima"):
                self.raiz.pack_start(self.recorte, False, False, 0)
                self.raiz.pack_start(self.puxador, False, False, 0)
            else:
                self.raiz.pack_start(self.puxador, False, False, 0)
                self.raiz.pack_start(self.recorte, False, False, 0)
            self.puxador.set_halign(Gtk.Align.START)
            self.puxador.set_valign(Gtk.Align.START)
            self.painel.set_size_request(self.largura, self.altura)
        else:
            self.raiz.pack_start(self.painel_direto(), True, True, 0)
            self.painel.set_size_request(self.largura, -1 if self.minimizado else self.altura)
        self.raiz.show_all()
        self.caixa_viva.set_visible(bool(self.bolha_viva.get_text()))
        self.corpo.set_visible(not self.minimizado)
        self.atualizar_botoes()
        self.desenhar_gaveta()
        self.resize(1, 1)

    def painel_direto(self):
        # Fora da gaveta o painel vai direto na janela (sem recorte).
        if self.painel.get_parent() is not None and self.painel.get_parent() is not self.raiz:
            pai = self.painel.get_parent()
            pai.remove(self.painel)
            if isinstance(pai, Gtk.Viewport):
                self.recorte.remove(pai)
        return self.painel

    def atualizar_botoes(self):
        if self.gaveta:
            self.btn_min.set_label("›" if self.cfg["borda"] == "direita" else "‹" if self.cfg["borda"] == "esquerda"
                                   else "˄" if self.cfg["borda"] == "cima" else "˅")
            self.btn_min.set_tooltip_text("Fechar a gaveta (Esc)")
        else:
            self.btn_min.set_label("+" if self.minimizado else "–")
            self.btn_min.set_tooltip_text("Abrir" if self.minimizado else "Recolher")

    def garantir_recorte(self):
        if self.painel.get_parent() is None:
            self.recorte.add(self.painel)
            self.painel.show_all()
            self.caixa_viva.set_visible(bool(self.bolha_viva.get_text()))

    # ================= gaveta =================
    def estado_puxador(self):
        if self.abertura > 0 or self.arrasto_pux or self.mouse_no_pux or time.time() < self.dica_ate \
                or self.cfg["puxador"] == "sempre":
            return "dica"
        return "novas" if self.nao_lidas or self.ela_digitando else "fio"

    def desenhar_gaveta(self):
        if not self.gaveta:
            return
        self.garantir_recorte()
        larg, alt = self.tela
        cheio = self.tamanho_aberto()
        ab = int(round(min(max(self.abertura, 0), cheio)))
        estado = self.estado_puxador()
        ctx = self.puxador.get_style_context()
        for c in ("fio", "novas"):
            ctx.remove_class(c)
        if estado == "fio":
            ctx.add_class("fio")
            espessura, comp = FIO, PUXADOR_COMP
        elif estado == "novas":
            ctx.add_class("novas")
            espessura, comp = PUXADOR_LARG - 4, 46
        else:
            if self.nao_lidas:
                ctx.add_class("novas")
            espessura, comp = PUXADOR_LARG, PUXADOR_COMP
        self.pux_caixa.set_visible(estado != "fio")
        self.pux_icone.set_visible(estado == "dica")
        self.pux_contador.set_text("…" if self.ela_digitando and not self.nao_lidas
                                   else str(self.nao_lidas) if self.nao_lidas else "")
        self.pux_contador.set_visible(bool(self.pux_contador.get_text()))
        eixo_x = self.eixo_x()
        painel_comp = self.altura if eixo_x else self.largura
        tela_comp = alt if eixo_x else larg
        desloc = int(min(max(self.cfg["desloc"], MARGEM_TELA), tela_comp - PUXADOR_COMP - MARGEM_TELA))
        # Painel aberto alinhado ao puxador, mas sempre dentro da tela.
        inicio = int(min(desloc, tela_comp - painel_comp - MARGEM_TELA)) if ab > 0 else desloc
        inicio = max(0, inicio)
        recuo = desloc - inicio + (PUXADOR_COMP - comp) // 2
        if eixo_x:
            self.puxador.set_size_request(espessura, comp)
            self.puxador.set_margin_top(recuo)
            self.puxador.set_margin_start(0)
            self.recorte.set_size_request(ab, self.altura)
        else:
            self.puxador.set_size_request(comp, espessura)
            self.puxador.set_margin_start(recuo)
            self.puxador.set_margin_top(0)
            self.recorte.set_size_request(self.largura, ab)
        self.recorte.set_visible(ab > 0)
        self.ajustar_recorte()
        borda = self.cfg["borda"]
        lados = {"esquerda": None, "direita": None, "cima": None, "baixo": None}
        lados[borda] = 0
        lados["cima" if eixo_x else "esquerda"] = inicio
        self.ancorar(**lados)
        chave = (ab, espessura, comp, recuo, inicio, self.largura, self.altura, borda)
        if chave != self.chave_gaveta:
            self.chave_gaveta = chave
            self.resize(1, 1)

    def ajustar_recorte(self, *_):
        # O lado do painel que "sai" da borda é o primeiro a aparecer.
        if not self.gaveta:
            return
        ab = int(round(min(max(self.abertura, 0), self.tamanho_aberto())))
        borda = self.cfg["borda"]
        hadj, vadj = self.recorte.get_hadjustment(), self.recorte.get_vadjustment()
        hadj.set_value(hadj.get_upper() - hadj.get_page_size() if borda == "esquerda" else 0)
        vadj.set_value(vadj.get_upper() - vadj.get_page_size() if borda == "cima" else 0)

    def animar(self, alvo):
        inicio, de = time.monotonic(), self.abertura
        dur = 0.18 if alvo > de else 0.14
        self.anim = (inicio, de, alvo, dur)
        if alvo > 0:
            self.no_fim = True
        GLib.timeout_add(15, self.passo_anim)

    def passo_anim(self):
        if not self.anim:
            return False
        inicio, de, alvo, dur = self.anim
        t = min(1.0, (time.monotonic() - inicio) / dur)
        self.abertura = de + (alvo - de) * suave(t)
        self.desenhar_gaveta()
        if t >= 1.0:
            self.anim = None
            if alvo > 0:
                self.marcar_lidas()
                self.entrada.grab_focus()
            else:
                self.dica_ate = time.time() + 1.0
            return False
        return True

    def abrir(self):
        self.animar(self.tamanho_aberto())

    def fechar(self):
        self.animar(0)

    def pux_entrar(self, *_):
        self.mouse_no_pux = True
        if self.abertura > 0:
            return False
        agora = time.monotonic()
        self.entradas_fio = [t for t in self.entradas_fio if agora - t < DUPLA_PASSADA] + [agora]
        if len(self.entradas_fio) >= 2 or self.estado_puxador() != "fio":
            self.entradas_fio = []
            if self.cfg["puxador"] == "abrir" and not self.anim:
                self.abrir()
            else:
                self.dica_ate = time.time() + DICA_DURA
                self.desenhar_gaveta()
        return False

    def pux_sair(self, _w, ev):
        if ev.detail == Gdk.NotifyType.INFERIOR:
            return False
        self.mouse_no_pux = False
        if self.estado_puxador() == "dica" and self.abertura <= 0:
            self.dica_ate = max(self.dica_ate, time.time() + 1.2)
        return False

    def pux_apertar(self, w, ev):
        if ev.button != 1:
            return False
        if self.estado_puxador() == "fio":
            return True     # o fio só reage a passadas; evita abrir com clique acidental na borda
        x, y = self.na_tela(w, ev)
        self.anim = None
        self.arrasto_pux = {"x": x, "y": y, "ab": self.abertura, "desloc": self.cfg["desloc"], "eixo": None}
        return True

    def pux_mover(self, w, ev):
        a = self.arrasto_pux
        if not a:
            return False
        x, y = self.na_tela(w, ev)
        dx, dy = x - a["x"], y - a["y"]
        borda = self.cfg["borda"]
        perp = {"esquerda": dx, "direita": -dx, "cima": dy, "baixo": -dy}[borda]
        par = dy if self.eixo_x() else dx
        if a["eixo"] is None and max(abs(perp), abs(par)) > 6:
            a["eixo"] = "puxar" if abs(perp) >= abs(par) else "mover"
        if a["eixo"] == "puxar":
            self.abertura = min(max(a["ab"] + perp, 0), self.tamanho_aberto())
            self.desenhar_gaveta()
        elif a["eixo"] == "mover":
            self.cfg["desloc"] = int(a["desloc"] + par)
            self.desenhar_gaveta()
        return True

    def pux_soltar(self, *_):
        a, self.arrasto_pux = self.arrasto_pux, None
        if not a:
            return False
        cheio = self.tamanho_aberto()
        if a["eixo"] is None:
            self.fechar() if self.abertura > 0 else self.abrir()
        elif a["eixo"] == "puxar":
            # Abrindo: basta puxar um quarto. Fechando: basta empurrar um quarto.
            limiar = 0.25 if a["ab"] < cheio / 2 else 0.75
            self.abrir() if self.abertura >= cheio * limiar else self.fechar()
        else:
            tela_comp = self.tela[1] if self.eixo_x() else self.tela[0]
            self.cfg["desloc"] = int(min(max(self.cfg["desloc"], MARGEM_TELA), tela_comp - PUXADOR_COMP - MARGEM_TELA))
            gravar_config(self.cfg)
            self.dica_ate = time.time() + DICA_DURA
            self.desenhar_gaveta()
        return True

    def foco_saiu(self, *_):
        if self.gaveta and self.cfg["fechar_fora"] and self.abertura > 0 and not self.anim \
                and not self.btn_cfg.get_active():
            GLib.timeout_add(120, lambda: (self.fechar() if not self.has_toplevel_focus() and self.abertura > 0 else None, False)[1])
        return False

    def tecla(self, _w, ev):
        if ev.keyval == Gdk.KEY_Escape:
            self.alternar()
            return True
        return False

    # ================= tamanho / mover =================
    def redimensionar(self, largura, altura, salvar=False):
        self.largura, self.altura = largura, altura
        if self.gaveta and self.abertura > 0:
            self.abertura = 10 ** 6   # aberta continua totalmente aberta (limitada ao desenhar)
        self.aplicar_forma()
        if self.gaveta and self.abertura > 0:
            self.abertura = self.tamanho_aberto()
        self.cfg["largura"], self.cfg["altura"] = int(self.largura), int(self.altura)
        self.margem_personagem = None
        if salvar:
            gravar_config(self.cfg)

    def sentido_alca(self):
        """Quanto a largura/altura cresce por pixel de arrasto em x/y (depende de onde a janela está presa)."""
        modo, borda = self.cfg["modo"], self.cfg["borda"]
        if modo == "personagem":
            return (-1 if self.lado_esq else 1), -1
        if modo == "gaveta":
            return (-1 if borda == "direita" else 1), (-1 if borda == "baixo" else 1)
        return 1, 1

    def alca_apertar(self, w, ev):
        if ev.type == Gdk.EventType._2BUTTON_PRESS:
            self.redimensionar(LARGURA, ALTURA, salvar=True)
            return True
        if ev.button == 1:
            x, y = self.na_tela(w, ev)
            self.arrasto = (x, y, self.largura, self.altura)
        return True

    def alca_mover(self, w, ev):
        if not self.arrasto:
            return False
        x0, y0, l0, a0 = self.arrasto
        x, y = self.na_tela(w, ev)
        sx, sy = self.sentido_alca()
        self.redimensionar(l0 + sx * (x - x0), a0 + sy * (y - y0))
        return True

    def alca_soltar(self, *_):
        if self.arrasto:
            self.arrasto = None
            gravar_config(self.cfg)
        return True

    def topo_apertar(self, w, ev):
        if ev.button != 1 or self.cfg["modo"] == "personagem":
            return False
        x, y = self.na_tela(w, ev)
        self.arrasto_topo = (x, y, list(self.cfg["solta"]), self.cfg["desloc"])
        return True

    def topo_mover(self, w, ev):
        if not self.arrasto_topo:
            return False
        x0, y0, solta, desloc = self.arrasto_topo
        x, y = self.na_tela(w, ev)
        if self.cfg["modo"] == "solta":
            self.cfg["solta"] = [int(solta[0] + x - x0), int(solta[1] + y - y0)]
            self.posicionar_solta()
        else:
            self.cfg["desloc"] = int(desloc + ((y - y0) if self.eixo_x() else (x - x0)))
            self.desenhar_gaveta()
        return True

    def topo_soltar(self, *_):
        if self.arrasto_topo:
            self.arrasto_topo = None
            gravar_config(self.cfg)
        return False

    def alternar(self, *_):
        if self.gaveta:
            self.fechar()
            return
        self.minimizado = not self.minimizado
        self.aplicar_forma()

    # ================= mensagens =================
    def enviar(self, *_):
        texto = self.entrada.get_text().strip()
        if not texto:
            return
        self.entrada.set_text("")
        try:
            dados.registrar("usuario", texto, boneca=self.boneca, avisar=True)
        except ValueError:
            return
        self.no_fim = True   # quem acabou de escrever quer ver a resposta

    def bolha(self, texto, minha, classe=None, hora=None):
        caixa = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        lbl = Gtk.Label(label=texto, xalign=0)
        lbl.set_line_wrap(True)
        lbl.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        lbl.set_max_width_chars(max(18, int(self.largura * 0.74 / 7.2)))
        lbl.set_selectable(True)
        lbl.set_can_focus(False)   # sem foco, o GTK não seleciona o texto inteiro ao abrir
        lbl.set_halign(Gtk.Align.END if minha else Gtk.Align.START)
        ctx = lbl.get_style_context()
        ctx.add_class("bolha")
        ctx.add_class(classe or ("minha" if minha else "dela"))
        caixa.pack_start(lbl, False, False, 0)
        if hora:
            h = Gtk.Label(label=time.strftime("%H:%M", time.localtime(hora)))
            h.get_style_context().add_class("hora")
            h.set_halign(Gtk.Align.END if minha else Gtk.Align.START)
            caixa.pack_start(h, False, False, 0)
        return caixa, lbl, minha

    def sincronizar(self, msgs):
        ids = [m.get("id", "") for m in msgs]
        if ids == self.ids:
            return
        n = len(self.ids)
        if ids[:n] != self.ids:
            # Histórico podado/reordenado: refaz tudo (raro).
            for filho in self.lista.get_children():
                if filho is not self.caixa_viva:
                    self.lista.remove(filho)
            self.labels = []
            n = 0
        for m in msgs[n:]:
            caixa, lbl, _ = self.bolha(m.get("texto", ""), m.get("origem") == "usuario", hora=m.get("criado_em"))
            self.labels.append(lbl)
            self.lista.pack_start(caixa, False, False, 0)
            caixa.show_all()
        self.ids = ids

    def lendo(self):
        """O usuário está vendo as mensagens agora?"""
        if self.gaveta:
            return self.abertura >= self.tamanho_aberto() - 1
        return not self.minimizado

    def marcar_lidas(self):
        msgs = dados.listar()
        ultimo = max((float(m.get("criado_em", 0)) for m in msgs), default=0.0)
        if ultimo > self.cfg["lido_ate"]:
            self.cfg["lido_ate"] = ultimo
            gravar_config(self.cfg)
        self.nao_lidas = 0

    def contar_novas(self, msgs):
        antes = self.nao_lidas
        self.nao_lidas = sum(1 for m in msgs if m.get("origem") == "personagem"
                             and float(m.get("criado_em", 0)) > self.cfg["lido_ate"])
        if self.nao_lidas > antes:
            self.ultima_nova = time.time()

    def lembrar_fim(self, adj):
        self.no_fim = adj.get_value() >= adj.get_upper() - adj.get_page_size() - 24

    def manter_fim(self, adj):
        if self.no_fim:
            adj.set_value(adj.get_upper() - adj.get_page_size())

    # ================= posição =================
    def medir_tela(self):
        mon = self.get_display().get_monitor_at_window(self.get_window()) if self.get_window() else None
        if mon:
            g = mon.get_geometry()
            if (g.width, g.height) != self.tela:
                self.tela = (g.width, g.height)
                self.aplicar_forma()

    def posicionar_personagem(self, st):
        hull = st.get("hull") or []
        if not hull:
            return
        xs = [p[0] for p in hull]
        ys = [p[1] for p in hull]
        larg, alt = self.tela
        w = self.largura
        # Mantém o lado escolhido enquanto couber: não fica pulando de um lado para o outro.
        cabe_esq = min(xs) - w - 14 >= MARGEM_TELA
        cabe_dir = max(xs) + 14 + w <= larg - MARGEM_TELA
        if self.lado_esq and not cabe_esq and cabe_dir:
            self.lado_esq = False
        elif not self.lado_esq and not cabe_dir and cabe_esq:
            self.lado_esq = True
        x = min(xs) - w - 14 if self.lado_esq else max(xs) + 14
        x = int(min(max(MARGEM_TELA, x), larg - w - MARGEM_TELA))
        # Base alinhada aos pés/borda inferior da personagem, nunca fora da tela.
        baixo = int(min(max(MARGEM_TELA, alt - max(ys)), alt - RESERVA_TOPO - self.altura - MARGEM_TELA))
        baixo = max(MARGEM_TELA, baixo)
        # Histerese: animação da personagem mexe o contorno alguns px; só reposiciona em movimento real.
        m = self.margem_personagem
        if m is None or abs(m[0] - x) > 24 or abs(m[1] - baixo) > 24:
            self.margem_personagem = (x, baixo)
            self.ancorar(esquerda=x, baixo=baixo)

    def posicionar_solta(self):
        larg, alt = self.tela
        w, h = self.get_allocated_width() or self.largura, self.get_allocated_height() or self.altura
        x = int(min(max(0, self.cfg["solta"][0]), larg - min(w, larg)))
        y = int(min(max(RESERVA_TOPO // 2, self.cfg["solta"][1]), alt - min(h, alt)))
        self.ancorar(esquerda=x, cima=y)

    # ================= laço =================
    def tique(self):
        st = status()
        prefs = st.get("preferencias", {})
        modo = self.cfg["modo"]
        visivel = bool(st) and prefs.get("modo_mensagens") and (modo != "personagem" or not st.get("hidden"))
        if not visivel:
            if self.get_visible():
                self.hide()
            return True
        if not self.get_visible():
            self.show()
            self.no_fim = True
            if not self.gaveta:
                self.entrada.grab_focus()
        self.medir_tela()
        self.boneca = prefs.get("boneca", "")
        msgs = dados.listar()
        self.sincronizar(msgs)
        if self.lendo():
            if self.nao_lidas or (msgs and float(msgs[-1].get("criado_em", 0)) > self.cfg["lido_ate"]):
                self.marcar_lidas()
        else:
            self.contar_novas(msgs)
        nome = nome_boneca(self.boneca)
        self.lbl_nome.set_text(f"{nome}  ({self.nao_lidas})" if self.nao_lidas and self.minimizado else nome)
        viva = dados.escrevendo()
        fase = viva.get("fase", "") if viva and time.time() - float(viva.get("timestamp", 0)) < 5 else ""
        self.lbl_estado.set_text(FASES.get(fase, "online"))
        self.ela_digitando = fase in ("pensando", "digitando", "apagando", "enviando")
        texto = viva.get("texto", "") if fase in ("digitando", "apagando", "pensando", "enviando") else ""
        if texto:
            novo = texto + ("▍" if fase != "pensando" else "")
            if self.bolha_viva.get_text() != novo:
                self.bolha_viva.set_text(novo)
            if not self.caixa_viva.get_visible():
                self.caixa_viva.show_all()
        elif self.caixa_viva.get_visible():
            self.caixa_viva.hide()
            self.bolha_viva.set_text("")
        if modo == "personagem":
            if not self.arrasto:
                self.posicionar_personagem(st)
        elif modo == "solta":
            if not self.arrasto:
                self.posicionar_solta()
        elif not (self.anim or self.arrasto_pux or self.arrasto):
            # Pulsa por alguns segundos quando chega mensagem com a gaveta fechada.
            ctx = self.puxador.get_style_context()
            if self.abertura <= 0 and time.time() - self.ultima_nova < 6:
                if time.time() - self.ultimo_pulso > 0.45:
                    self.ultimo_pulso = time.time()
                    (ctx.remove_class if ctx.has_class("pulso") else ctx.add_class)("pulso")
            elif ctx.has_class("pulso"):
                ctx.remove_class("pulso")
            self.desenhar_gaveta()
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
