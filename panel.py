# panel.py
# Armado del panel lateral derecho, el que muestra misión, pasos, puntaje y
# controles mientras se juega.
#
# ── Por qué existe este archivo ──────────────────────────────────────────
# Antes cada texto del panel llevaba su posición vertical escrita a mano
# (`ALTO_VENTANA - 404`, `- 420`, `- 452`...), y cada modo que quería sumar
# un bloque tenía que saber en qué píxel había dejado las cosas el modo del
# que heredaba, y correr los de abajo uno por uno. De ahí salieron dos bugs
# ya arreglados —el indicador de llave encima del bloque de personaje, y los
# controles encima del recordatorio del pie— y quedaban huecos de hasta 88
# píxeles mientras los títulos rozaban sus números.
#
# Acá el modo declara QUÉ secciones tiene y en qué orden; las posiciones se
# calculan solas. Sumar un bloque en el medio no obliga a tocar ningún otro.
#
# El mismo armador lo usan Juego (y por herencia Viaje y Multijugador) y
# Tutorial, que no comparte la clase base pero sí el panel.

import arcade

# Ritmo vertical. Son las únicas medidas del panel que se eligen a mano.
MARGEN_X          = 16   # sangría del texto respecto del borde del panel
ESPACIO_TITULO    = 20   # entre el título de una sección y su primera línea
ESPACIO_LINEA     = 4    # entre dos líneas de una misma sección
ESPACIO_SECCION   = 18   # entre el final de una sección y el título de la
                         # siguiente, cuando hay lugar de sobra
ESPACIO_SECCION_MINIMO = 8   # hasta dónde se puede apretar si no entra
ESPACIO_EXTRA_TOPE = 22  # cuánto se puede estirar ese mínimo al repartir el
                         # espacio sobrante (ver acomodar)

COLOR_TITULO   = arcade.color.GOLD
COLOR_REGLA    = (58, 72, 82)   # hairline: apenas más claro que el fondo


class Seccion:
    """Un bloque del panel: un título y las líneas que van abajo.

    `visible` permite declarar una sección que este nivel no usa —la llave
    en un mapa que no tiene llave— sin sacarla de la lista: así el orden de
    las secciones es siempre el mismo y se lee de un vistazo.

    `icono` es la ruta del PNG que se dibuja pegado al borde derecho, a la
    altura del título."""

    def __init__(self, titulo, cuerpo, icono=None, visible=True):
        """Arma una sección del panel con su título y sus líneas."""
        self.titulo  = titulo
        self.cuerpo  = cuerpo if isinstance(cuerpo, (list, tuple)) else [cuerpo]
        self.icono   = icono
        self.visible = visible
        self.y_titulo = 0     # lo completa acomodar()
        # El Text del título lo arma acomodar() y se reusa en cada cuadro.
        # Crearlo dentro de dibujar() costaba un layout de texto nuevo por
        # sección por cuadro, y el panel pasaba a ser casi todo el costo de
        # dibujar el juego.
        self.txt_titulo = None


def crear_texto(valor, x, tam, color, bold=False, ancho=None):
    """Un Text del panel, anclado por arriba.

    Todos los textos que administra este archivo se anclan en su borde
    superior, que es lo que permite apilarlos sin cuentas: se les da el
    techo y Arcade acomoda las líneas hacia abajo."""
    return arcade.Text(valor, x, 0, color, tam, bold=bold, anchor_y="top",
                       multiline=ancho is not None, width=ancho or 0)


def _alto(texto):
    """Alto que ocupa un Text, contando todas sus líneas si es multilínea."""
    return texto.content_height


def _alto_seccion(seccion, con_titulo=True):
    """Alto que ocupa una sección: su título más todas sus líneas."""
    alto = 0
    if con_titulo and seccion.titulo:
        alto += ESPACIO_TITULO
    lineas = [t for t in seccion.cuerpo if t.value]
    for i, texto in enumerate(lineas):
        alto += _alto(texto)
        if i < len(lineas) - 1:
            alto += ESPACIO_LINEA
    return alto


def acomodar(secciones, y_desde, y_hasta):
    """Reparte las secciones entre y_desde (arriba) e y_hasta (abajo) y deja
    cada Text con su posición vertical puesta.

    El sobrante se reparte en partes iguales entre las separaciones, con un
    tope: sin repartir, un modo con pocas secciones dejaba más de un cuarto
    del panel vacío abajo; sin tope, un modo con dos secciones las mandaba a
    los extremos y quedaban flotando."""
    visibles = [s for s in secciones if s.visible and any(t.value for t in s.cuerpo)]
    if not visibles:
        return visibles

    alto_contenido = sum(_alto_seccion(s) for s in visibles)
    separaciones   = max(len(visibles) - 1, 1)
    disponible     = y_desde - y_hasta
    sobrante       = disponible - alto_contenido - ESPACIO_SECCION * separaciones

    if sobrante >= 0:
        # Sobra lugar: se reparte entre las separaciones, con tope.
        separacion = ESPACIO_SECCION + min(ESPACIO_EXTRA_TOPE, sobrante // separaciones)
    else:
        # No entra: se aprietan las separaciones antes que dejar que un
        # bloque se salga del panel. Con el piso puesto puede seguir sin
        # entrar, y en ese caso se prefiere avisar por consola a dibujar
        # texto cortado por abajo, que es lo que pasaba antes.
        separacion = max(ESPACIO_SECCION_MINIMO,
                         (disponible - alto_contenido) // separaciones)
        falta = alto_contenido + separacion * separaciones - disponible
        if falta > 0:
            print(f"Panel: el contenido excede el alto disponible por {falta}px")

    y = y_desde
    for i, seccion in enumerate(visibles):
        if seccion.titulo:
            seccion.y_titulo = y
            if seccion.txt_titulo is None:
                seccion.txt_titulo = arcade.Text(
                    seccion.titulo, 0, 0, COLOR_TITULO, 11, bold=True,
                    anchor_y="top")
            y -= ESPACIO_TITULO
        lineas = [t for t in seccion.cuerpo if t.value]
        for j, texto in enumerate(lineas):
            # Los textos del panel se crean con anchor_y="top" (ver
            # crear_texto), así que alcanza con darles el borde de arriba:
            # Arcade acomoda las líneas hacia abajo, multilínea incluido.
            texto.y = y
            y -= _alto(texto)
            if j < len(lineas) - 1:
                y -= ESPACIO_LINEA
        if i < len(visibles) - 1:
            y -= separacion
    return visibles


def dibujar(secciones, x_izq, x_der, x_iconos, dibujar_icono):
    """Dibuja las secciones ya acomodadas: título, regla, líneas e ícono.

    Recibe dibujar_icono en vez de importar sprites para no atar este
    archivo al sistema de texturas: al panel solo le importa dónde va."""
    for seccion in secciones:
        titulo = seccion.txt_titulo
        if titulo is not None:
            titulo.x = x_izq + MARGEN_X
            titulo.y = seccion.y_titulo
            titulo.draw()
            # Regla fina desde donde termina el título hasta el margen
            # derecho: separa los bloques sin agregar ni un texto más.
            inicio = x_izq + MARGEN_X + titulo.content_width + 8
            fin    = x_der - MARGEN_X
            medio  = seccion.y_titulo - titulo.content_height // 2
            if fin > inicio:
                arcade.draw_line(inicio, medio, fin, medio, COLOR_REGLA, 1)
        for texto in seccion.cuerpo:
            if texto.value:
                texto.draw()

        # El ícono va a la altura del título; en una sección sin título, a
        # la de su primera línea, que es lo único que tiene.
        if seccion.icono:
            primera = next((t for t in seccion.cuerpo if t.value), None)
            if titulo is not None:
                y_icono = seccion.y_titulo - 7
            elif primera is not None:
                y_icono = primera.y - primera.content_height // 2
            else:
                continue
            dibujar_icono(seccion.icono, x_iconos, y_icono)
