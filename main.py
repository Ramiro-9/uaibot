import arcade
from constantes import *
from menu import Menu

def main():
    ventana = arcade.Window(ANCHO_VENTANA, ALTO_VENTANA, TITULO)
    ventana.musica_player = None
    menu = Menu()
    ventana.show_view(menu)
    arcade.run()

if __name__ == "__main__":
    main()