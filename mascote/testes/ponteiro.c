/* Apenas para o ensaio: ponteiro Wayland virtual, sem root ou uinput.
 * Protocolo oficial: https://github.com/swaywm/wlr-protocols
 * Uso: ponteiro X Y [click|middle|up|down|move|drag X2 Y2]
 * Coordenadas deste teste: 1920x1080, um monitor, escala 1.
 */
#include <wayland-client.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include "mascote-virtual-pointer.h"
static struct zwlr_virtual_pointer_manager_v1 *manager;
static struct wl_display *display;
static struct zwlr_virtual_pointer_v1 *pointer;
static void global(void *d, struct wl_registry *r, uint32_t id, const char *i, uint32_t v) {
    if (!strcmp(i, "zwlr_virtual_pointer_manager_v1"))
        manager = wl_registry_bind(r, id, &zwlr_virtual_pointer_manager_v1_interface, v < 2 ? v : 2);
}
static void removed(void *d, struct wl_registry *r, uint32_t id) {}
static const struct wl_registry_listener listener = {global, removed};
static uint32_t now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec*1000+t.tv_nsec/1000000; }
static void flush(void) { zwlr_virtual_pointer_v1_frame(pointer); wl_display_roundtrip(display); usleep(40000); }
static void move(int x, int y) { zwlr_virtual_pointer_v1_motion_absolute(pointer, now(), x, y, 1920, 1080); flush(); }
static void button(int code, int state) { zwlr_virtual_pointer_v1_button(pointer, now(), code, state); flush(); }
int main(int argc, char **argv) {
    if(argc < 4) return 2;
    display = wl_display_connect(NULL); if(!display) return 3;
    struct wl_registry *registry = wl_display_get_registry(display);
    wl_registry_add_listener(registry, &listener, NULL); wl_display_roundtrip(display);
    if(!manager) { fprintf(stderr,"Protocolo virtual-pointer indisponível\n"); return 4; }
    pointer = zwlr_virtual_pointer_manager_v1_create_virtual_pointer(manager, NULL);
    int x=atoi(argv[1]), y=atoi(argv[2]); move(x,y); usleep(120000);
    if(!strcmp(argv[3],"click") || !strcmp(argv[3],"middle") || !strcmp(argv[3],"right")) {
        int code = !strcmp(argv[3],"right") ? 273 : (!strcmp(argv[3],"middle") ? 274 : 272); button(code,1); button(code,0);
    } else if(!strcmp(argv[3],"drag") && argc==6) {
        int tx=atoi(argv[4]),ty=atoi(argv[5]); button(272,1);
        for(int i=1;i<=20;i++) move(x+(tx-x)*i/20,y+(ty-y)*i/20);
        button(272,0);
    } else if(!strcmp(argv[3],"up") || !strcmp(argv[3],"down")) {
        int dir = !strcmp(argv[3],"up") ? -1 : 1;
        zwlr_virtual_pointer_v1_axis_source(pointer,WL_POINTER_AXIS_SOURCE_WHEEL);
        zwlr_virtual_pointer_v1_axis_discrete(pointer,now(),WL_POINTER_AXIS_VERTICAL_SCROLL,wl_fixed_from_int(dir*10),dir);
        flush();
    }
    zwlr_virtual_pointer_v1_destroy(pointer);
    zwlr_virtual_pointer_manager_v1_destroy(manager);
    wl_registry_destroy(registry); wl_display_flush(display); wl_display_disconnect(display);
    return 0;
}
