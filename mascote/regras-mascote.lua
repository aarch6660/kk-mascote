-- Proposta definitiva. NÃO instalada. Uso temporário: hyprctl eval.
-- Geometria inicial para eDP-1; o app recalcula a área lógica do monitor.
-- No Hyprland, no_focus=true também pode impedir os eventos de mouse.
return hl.window_rule({
    name = "kk-mascote",
    match = { class = "^(kk-mascote)$" },
    float = true,
    pin = true,
    size = "1920 1080",
    move = "0 0",
    border_size = 0,
    decorate = false,
    no_shadow = true,
    no_blur = true,
    no_anim = true,
    no_dim = true,
    no_focus = true, -- O supervisor libera somente sobre o contorno; restaura foco com hl.on.
    no_initial_focus = true,
    no_follow_mouse = true,
    focus_on_activate = false,
    no_shortcuts_inhibit = true,
    opacity = "1.0 override 1.0 override",
    idle_inhibit = "none",
})
