# ui.py
# Piezas compartidas de las pantallas de menú: el cuadro de diálogo con su
# marco, los encabezados y el ajuste de línea.
#
# ── Por qué existe ───────────────────────────────────────────────────────
# El submenú de Ajustes era el único armado como interfaz: cuadro con marco
# nine-patch, título y pie de ayuda. El Inventario y la sala del
# Multijugador eran texto suelto sobre el fondo plano, y cada uno repetía a
# mano su encabezado y su pie. Acá están esas piezas una sola vez, para que
# todas las pantallas se vean iguales y una corrección alcance a todas.

import arcade

import sprites as spr
from constantes import ALTO_VENTANA, ANCHO_VENTANA, PANEL_MARCO

FONDO        = (20, 28, 36)      # el mismo que limpia las vistas de menú
FONDO_CUADRO = (30, 39, 46)      # relleno del cuadro cuando no hay marco
BORDE_CUADRO = (52, 152, 219)
COLOR_AYUDA  = (120, 120, 120)
COLOR_TENUE  = (170, 170, 170)


# ── Textos reutilizados ──────────────────────────────────────────────────
# Crear un arcade.Text cuesta unos 14 ms porque arma el layout del texto de
# cero; dibujar uno ya creado cuesta 0,3 ms, y cambiarle el valor 3,7 ms
# -y nada si el texto no cambió-. Como estas pantallas se redibujan 60
# veces por segundo, cada Text creado dentro del dibujo se paga entero en
# cada cuadro. Por eso se guardan por rol y se reusan.
_textos = {}


def etiqueta(clave, valor, x, y, color, tam, **kw):
    """Devuelve el Text de ese rol, creándolo la primera vez y solo
    actualizándolo después.

    La clave es el ROL que cumple el texto en la pantalla, no su contenido:
    "el título del cuadro", "la tercera línea del párrafo". Como se dibuja
    una sola pantalla por vez, dos pantallas pueden compartir un rol sin
    problema; lo único que cuesta es reescribir el valor al cambiar de
    pantalla."""
    t = _textos.get(clave)
    if t is None:
        t = arcade.Text(valor, x, y, color, tam, **kw)
        _textos[clave] = t
        return t
    if t.value != valor:
        t.value = valor
    t.x, t.y = x, y
    if tuple(t.color)[:3] != tuple(color)[:3]:
        t.color = color
    return t


def dialogo(cx, cy, ancho, alto, titulo=None):
    """Dibuja el cuadro de diálogo y devuelve sus bordes (izq, der, abajo,
    arriba), que es lo que necesita quien va a poner contenido adentro.

    Si el arte del marco no está, cae a un rectángulo con borde: el juego
    tiene que seguir siendo jugable sin los PNG (ver sprites.py)."""
    izq, der = cx - ancho // 2, cx + ancho // 2
    aba, arr = cy - alto // 2, cy + alto // 2

    marco = spr.marco(PANEL_MARCO)
    if marco is not None:
        marco.draw_rect(rect=arcade.XYWH(cx, cy, ancho, alto))
    else:
        arcade.draw_lrbt_rectangle_filled(izq, der, aba, arr, FONDO_CUADRO)
        arcade.draw_lrbt_rectangle_outline(izq, der, aba, arr, BORDE_CUADRO, 2)

    if titulo:
        etiqueta("dialogo_titulo", titulo, cx, arr - 30, arcade.color.GOLD, 18,
               anchor_x="center", anchor_y="center", bold=True).draw()
    return izq, der, aba, arr


def encabezado(texto, subtitulo=None):
    """Título de una pantalla completa, arriba de todo."""
    cx = ANCHO_VENTANA // 2
    etiqueta("encabezado", texto, cx, ALTO_VENTANA - 44, arcade.color.GOLD, 26,
           anchor_x="center", anchor_y="center", bold=True).draw()
    if subtitulo:
        etiqueta("encabezado_sub", subtitulo, cx, ALTO_VENTANA - 70, COLOR_TENUE,
               12, anchor_x="center", anchor_y="center").draw()


def ayuda(texto, y=24):
    """Pie con los controles de la pantalla."""
    etiqueta("ayuda", texto, ANCHO_VENTANA // 2, y, COLOR_AYUDA, 11,
           anchor_x="center", anchor_y="center").draw()


def solapas(nombres, activa, cy, separacion=200):
    """Solapas de sección, con la activa subrayada.

    El subrayado va además del color porque el dorado sobre gris no siempre
    se distingue de un vistazo, y son la única pista de que ↑↓ cambia de
    sección."""
    cx = ANCHO_VENTANA // 2
    x0 = cx - separacion * (len(nombres) - 1) / 2
    for i, nombre in enumerate(nombres):
        x = x0 + i * separacion
        es_activa = (i == activa)
        color = arcade.color.GOLD if es_activa else (120, 120, 120)
        t = etiqueta(f"solapa{i}", nombre, x, cy, color, 14, anchor_x="center",
                   anchor_y="center", bold=True)
        t.draw()
        if es_activa:
            medio = t.content_width / 2
            arcade.draw_line(x - medio, cy - 13, x + medio, cy - 13,
                             arcade.color.GOLD, 2)


# ── Ajuste de línea ──────────────────────────────────────────────────────
# Se corta el texto acá en vez de dejárselo a Arcade porque su ajuste
# automático parte palabras al medio: agrupa los glifos por fuente, y
# cuando la fuente del juego no trae una vocal acentuada cae a otra fuente,
# lo que abre un punto de corte justo antes del acento. Así se veían
# "compartimento m / ás seguro" y "la c / ampaña" en el Bestiario.
_cache_ancho = {}


def _ancho(texto, tam, bold):
    """Ancho en píxeles de un texto, cacheado por contenido y estilo."""
    clave = (texto, tam, bold)
    if clave not in _cache_ancho:
        _cache_ancho[clave] = arcade.Text(texto, 0, 0, arcade.color.WHITE,
                                          tam, bold=bold).content_width
    return _cache_ancho[clave]


def envolver(texto, ancho_px, tam, bold=False):
    """Corta el texto en líneas que entren en ancho_px, siempre entre
    palabras. Devuelve el texto con saltos de línea puestos."""
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = f"{actual} {palabra}".strip()
        if actual and _ancho(prueba, tam, bold) > ancho_px:
            lineas.append(actual)
            actual = palabra
        else:
            actual = prueba
    if actual:
        lineas.append(actual)
    return "\n".join(lineas)


def parrafo(texto, cx, y, ancho_px, tam, color, bold=False, interlinea=1.35):
    """Dibuja un texto largo centrado, cortado con envolver(). Devuelve el
    alto que ocupó, para poder seguir apilando abajo."""
    lineas = envolver(texto, ancho_px, tam, bold).split("\n")
    alto_linea = tam * interlinea
    for i, linea in enumerate(lineas):
        etiqueta(f"parrafo{i}", linea, cx, y - i * alto_linea, color, tam,
               anchor_x="center", anchor_y="center", bold=bold).draw()
    return alto_linea * len(lineas)
