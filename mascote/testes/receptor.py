#!/usr/bin/env python3
"""Duas janelas temporárias: receptor atrás da Chika e plataforma de apoio."""
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, Gdk

def activate(app):
    for titulo, texto in [("KK teste receptor", "RECEPTOR DE CLIQUES\n\nClique no vazio: deve chegar aqui.\nClique na Chika: deve reagir e não tirar o foco."),
                          ("KK teste plataforma", "PLATAFORMA TEMPORÁRIA\nChika fica sobre esta borda.")]:
        janela = Gtk.ApplicationWindow(application=app, title=titulo)
        janela.set_child(Gtk.Label(label=texto))
        click = Gtk.GestureClick()
        click.set_button(0)
        click.connect("pressed", lambda _, n, x, y, t=titulo: print(f"RECEIVER_CLICK {t} {x:.1f} {y:.1f}", flush=True))
        janela.add_controller(click)
        janela.present()
    css = Gtk.CssProvider()
    css.load_from_string("window { background: #163c50; color: #fff; font-size: 22px; }")
    Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

app = Gtk.Application(application_id="kk.mascote.receptor", flags=Gio.ApplicationFlags.NON_UNIQUE)
app.connect("activate", activate)
app.run(None)
