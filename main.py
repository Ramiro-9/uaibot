# main.py
# Punto de entrada del juego.
# Crea la ventana principal y muestra el menú de inicio.

import arcade
from constantes import *
from menu import Menu

def main():
    """Abre la ventana del juego y muestra el menú principal."""
    # Crear la ventana con el tamaño definido en constantes
    ventana = arcade.Window(ANCHO_VENTANA, ALTO_VENTANA, TITULO)

    # Player de música global para poder detenerla desde cualquier vista
    ventana.musica_player = None

    # Mostrar el menú principal como primera vista
    # La ventana conserva la vista activa; no retener el menú inicial aquí.
    ventana.show_view(Menu())
    arcade.run()

if __name__ == "__main__":
    main()