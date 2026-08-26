# sprites.py
# Carga y cachea texturas de sprites con sistema de fallback.
# Si una imagen no existe, las funciones retornan False y el código
# principal dibuja un color de reemplazo en su lugar.

import os
import arcade

# Caché de texturas para no recargar el mismo archivo varias veces
_cache = {}

def cargar(path):
    """Carga una textura si el archivo existe, sino retorna None.
    Usa caché para evitar lecturas repetidas del disco."""
    if path in _cache:
        return _cache[path]
    if os.path.exists(path):
        tex = arcade.load_texture(path)
        _cache[path] = tex
        return tex
    _cache[path] = None
    return None

def dibujar_celda(path, col, fila, tam):
    """Intenta dibujar una celda con su imagen correspondiente.
    Retorna True si pudo dibujar la imagen, False si no existe
    (en ese caso el código principal dibuja el color de fallback)."""
    tex = cargar(path)
    if tex:
        x = col * tam + tam // 2
        y = fila * tam + tam // 2
        arcade.draw_texture_rect(tex, arcade.XYWH(x, y, tam, tam))
        return True
    return False


# Hojas de UAIBOT: son también el respaldo de los personajes que todavía no
# tienen arte propio.
HOJA_IDLE = "assets/Idle.png"
HOJA_WALK = "assets/Walk.png"

_cache_hojas = {}


def cortar_hoja(path, ancho, alto):
    """Corta una hoja horizontal en tantos frames de ancho x alto como entren.

    La cantidad de frames se deduce del ancho del archivo en vez de fijarse en
    una constante: así cada personaje puede traer su propia hoja con más o
    menos poses sin tocar el código que la consume."""
    clave = (path, ancho, alto)
    if clave in _cache_hojas:
        return _cache_hojas[clave]
    hoja = arcade.load_spritesheet(path)
    frames = [
        hoja.get_texture(arcade.LRBT(i * ancho, i * ancho + ancho, 0, alto))
        for i in range(hoja.image.width // ancho)
    ]
    _cache_hojas[clave] = frames
    return frames


def cargar_familia(personajes, ancho, alto):
    """Arma las animaciones de cada personaje de la familia.

    Devuelve {id: {"idle": [...], "walk": [...], "color": (r, g, b)}}.

    Un personaje con hojas propias -assets/<id>_Idle.png y <id>_Walk.png- se
    dibuja con su arte y SIN tinte, porque teñir arte propio lo desteñiría. Los
    que todavía no tienen arte siguen reusando las hojas de UAIBOT teñidas con
    su color, exactamente como antes. Así se puede ir dibujando un personaje
    por vez sin romper a los demás.

    Cada personaje puede traer distinta cantidad de frames: quien consuma esto
    debe sacar el módulo de len() en vez de asumir un número fijo."""
    familia = {}
    for p in personajes:
        propia_idle = f"assets/{p['id']}_Idle.png"
        propia_walk = f"assets/{p['id']}_Walk.png"
        tiene_arte  = os.path.exists(propia_idle) and os.path.exists(propia_walk)
        if not tiene_arte:
            propia_idle, propia_walk = HOJA_IDLE, HOJA_WALK
        familia[p["id"]] = {
            "idle":  cortar_hoja(propia_idle, ancho, alto),
            "walk":  cortar_hoja(propia_walk, ancho, alto),
            "color": (255, 255, 255) if tiene_arte else p["color"],
        }
    return familia


# ── Elementos de interfaz ─────────────────────────────────────────────────────

_cache_marcos = {}


def dibujar_icono(path, x, y, tam=20):
    """Dibuja un ícono de UI centrado en (x, y).

    Si el archivo no está no dibuja nada y devuelve False, igual que
    dibujar_celda: los íconos acompañan texto que ya se explica solo, así que
    faltando el arte la interfaz sigue siendo legible."""
    tex = cargar(path)
    if tex is None:
        return False
    arcade.draw_texture_rect(tex, arcade.XYWH(x, y, tam, tam))
    return True


def marco(path, borde=(30, 30, 26, 26)):
    """NinePatchTexture cacheada para dibujar marcos ornamentados.

    El nine-patch estira solo los bordes y el centro, dejando las esquinas
    intactas: un marco de 160x120 se puede dibujar a 440x160 sin que se
    deformen los remates dorados. `borde` es (izquierda, derecha, abajo,
    arriba) en píxeles de la textura original.

    Devuelve None si el archivo no está, y quien llama dibuja el rectángulo
    plano de siempre."""
    clave = (path, borde)
    if clave in _cache_marcos:
        return _cache_marcos[clave]

    tex = cargar(path)
    resultado = None
    if tex is not None:
        # import diferido: arcade.gui solo se carga si realmente hay un marco
        from arcade.gui import NinePatchTexture

        izq, der, aba, arr = borde
        resultado = NinePatchTexture(left=izq, right=der, bottom=aba, top=arr,
                                     texture=tex)
    _cache_marcos[clave] = resultado
    return resultado
