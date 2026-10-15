"""Sonidos compartidos entre las vistas del juego.

Carga diferida: cada archivo se lee la primera vez que se necesita.
La caché guarda Sound, nunca reproductores ni vistas. Cada reproducción
mantiene sus controles de volumen, detención y repetición habituales.
"""
from functools import lru_cache

import arcade


@lru_cache(maxsize=16)
def cargar_sonido(ruta: str) -> arcade.Sound:
    """Reutiliza audio estático; las cinco rutas actuales caben en la caché.

    Se conserva una copia decodificada por ruta mientras siga en la caché.
    No usar para streaming: una fuente streaming tiene otro ciclo de vida.
    """
    return arcade.load_sound(ruta)
