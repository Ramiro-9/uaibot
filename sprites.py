import os
import arcade

_cache = {}

def cargar(path):
    """Carga una textura si existe, sino retorna None"""
    if path in _cache:
        return _cache[path]
    if os.path.exists(path):
        tex = arcade.load_texture(path)
        _cache[path] = tex
        return tex
    _cache[path] = None
    return None

def dibujar_celda(path, col, fila, tam):
    """Dibuja una celda con imagen si existe, sino con el color de fallback dado, ojo con esto juan"""
    tex = cargar(path)
    if tex:
        x = col * tam + tam // 2
        y = fila * tam + tam // 2
        arcade.draw_texture_rect(tex, arcade.XYWH(x, y, tam, tam))
        return True
    return False