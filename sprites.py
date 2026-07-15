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