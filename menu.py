# menu.py
import arcade
import guardado
from constantes import *

OPCIONES = ["Iniciar partida", "Controles", "Dificultad"]
DIFICULTADES = ["facil", "medio", "dificil"]

class Menu(arcade.View):
    def __init__(self):
        super().__init__()
        self.datos = guardado.cargar()
        self.opcion_seleccionada = 0
        self.submenu = None
        self.dificultad = self.datos.get("dificultad", "facil")
        self._crear_textos()

    def _crear_textos(self):
        cx = ANCHO_VENTANA // 2
        self.txt_titulo = arcade.Text("UAIBOT", cx, ALTO_VENTANA - 120,
                                      arcade.color.GOLD, 64,
                                      anchor_x="center", bold=True)
        self.txt_subtitulo = arcade.Text("OFIRCA 2026", cx, ALTO_VENTANA - 170,
                                          (52, 152, 219), 20, anchor_x="center")
        self.txt_highscore = arcade.Text(f"Highscore: {self.datos['highscore']}",
                                          cx, ALTO_VENTANA - 210,
                                          arcade.color.GOLD, 14, anchor_x="center")
        self.txt_opciones = [
            arcade.Text(op, cx, ALTO_VENTANA - 300 - i * 60,
                        arcade.color.WHITE, 22, anchor_x="center")
            for i, op in enumerate(OPCIONES)
        ]
        self.txt_instruccion = arcade.Text("↑↓ para navegar   ENTER para seleccionar",
                                            cx, 40, (150, 150, 150), 12, anchor_x="center")
        self.txt_controles_val = arcade.Text("", cx, ALTO_VENTANA - 300 - 1 * 60 - 28,
                                              (52, 152, 219), 12, anchor_x="center")
        self.txt_dificultad_val = arcade.Text("", cx, ALTO_VENTANA - 300 - 2 * 60 - 28,
                                               (52, 152, 219), 12, anchor_x="center")
        self._actualizar_subtextos()

    def _actualizar_subtextos(self):
        controles = self.datos.get("controles", "flechas")
        self.txt_controles_val.value = f"actual: {controles}"
        self.txt_dificultad_val.value = f"actual: {self.dificultad}"

    def on_key_press(self, symbol, modifiers):
        if self.submenu == "controles":
            self._manejar_controles(symbol)
        elif self.submenu == "dificultad":
            self._manejar_dificultad(symbol)
        else:
            self._manejar_menu(symbol)

    def _manejar_menu(self, symbol):
        if symbol == arcade.key.UP:
            self.opcion_seleccionada = (self.opcion_seleccionada - 1) % len(OPCIONES)
        elif symbol == arcade.key.DOWN:
            self.opcion_seleccionada = (self.opcion_seleccionada + 1) % len(OPCIONES)
        elif symbol == arcade.key.ENTER:
            if self.opcion_seleccionada == 0:
                self._iniciar_partida()
            elif self.opcion_seleccionada == 1:
                self.submenu = "controles"
            elif self.opcion_seleccionada == 2:
                self.submenu = "dificultad"

    def _manejar_controles(self, symbol):
        if symbol in (arcade.key.LEFT, arcade.key.RIGHT):
            actual = self.datos.get("controles", "flechas")
            nuevo = "wasd" if actual == "flechas" else "flechas"
            guardado.actualizar_controles(nuevo)
            self.datos = guardado.cargar()
            self._actualizar_subtextos()
        elif symbol == arcade.key.ESCAPE:
            self.submenu = None

    def _manejar_dificultad(self, symbol):
        if symbol == arcade.key.LEFT:
            idx = DIFICULTADES.index(self.dificultad)
            self.dificultad = DIFICULTADES[(idx - 1) % len(DIFICULTADES)]
            self._guardar_dificultad()
        elif symbol == arcade.key.RIGHT:
            idx = DIFICULTADES.index(self.dificultad)
            self.dificultad = DIFICULTADES[(idx + 1) % len(DIFICULTADES)]
            self._guardar_dificultad()
        elif symbol == arcade.key.ESCAPE:
            self.submenu = None

    def _guardar_dificultad(self):
        datos = guardado.cargar()
        datos["dificultad"] = self.dificultad
        guardado.guardar(datos)
        self._actualizar_subtextos()

    def _iniciar_partida(self):
        from juego import Juego
        juego = Juego(dificultad=self.dificultad, controles=self.datos.get("controles", "flechas"))
        juego.setup()
        self.window.show_view(juego)

    def on_draw(self):
        self.window.clear((20, 28, 36))
        self.txt_titulo.draw()
        self.txt_subtitulo.draw()
        self.txt_highscore.draw()
        self.txt_instruccion.draw()
        for i, txt in enumerate(self.txt_opciones):
            if i == self.opcion_seleccionada and self.submenu is None:
                txt.color = arcade.color.GOLD
            else:
                txt.color = arcade.color.WHITE
            txt.draw()
        self.txt_controles_val.draw()
        self.txt_dificultad_val.draw()
        if self.submenu == "controles":
            self._dibujar_submenu("Controles", "← → para cambiar entre flechas y WASD\nESC para volver")
        elif self.submenu == "dificultad":
            self._dibujar_submenu("Dificultad", "← → para cambiar\nESC para volver")

    def _dibujar_submenu(self, titulo, instruccion):
        cx = ANCHO_VENTANA // 2
        cy = ALTO_VENTANA // 2
        arcade.draw_lrbt_rectangle_filled(cx - 220, cx + 220, cy - 80, cy + 80, (30, 39, 46))
        arcade.draw_lrbt_rectangle_outline(cx - 220, cx + 220, cy - 80, cy + 80, (52, 152, 219), 2)
        arcade.Text(titulo, cx, cy + 50, arcade.color.GOLD, 18,
                    anchor_x="center", bold=True).draw()
        arcade.Text(instruccion, cx, cy, (200, 200, 200), 13,
                    anchor_x="center", multiline=True, width=400).draw()