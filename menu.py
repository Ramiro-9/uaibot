# menu.py
# Pantalla de inicio del juego con fondo ilustrado y botones tipo ribbon.
# Permite seleccionar dificultad, cambiar controles e iniciar partida.
# Soporta navegación por teclado (↑↓ + ENTER) y mouse (hover + click).

import arcade
import guardado
from constantes import *

OPCIONES     = ["Iniciar partida", "Controles", "Dificultad"]
DIFICULTADES = ["facil", "medio", "dificil"]

class Menu(arcade.View):
    def __init__(self):
        super().__init__()
        self.datos               = guardado.cargar()
        self.opcion_seleccionada = 0
        self.submenu             = None   # None | "controles" | "dificultad"
        self.dificultad          = self.datos.get("dificultad", "facil")
        self._cargar_assets()
        self._crear_textos()

    # ── Assets ────────────────────────────────────────────────────────────────
    def _cargar_assets(self):
        """Carga el fondo del menú y los ribbons de botones desde sus spritesheets."""
        self.img_fondo = arcade.load_texture("assets/fondo_menu.png")

        # El spritesheet de botones tiene 5 ribbons apilados verticalmente
        sheet        = arcade.load_spritesheet("assets/botones.png")
        alto_ribbon  = 1563 // 5
        self.img_btn = [
            sheet.get_texture(
                arcade.LRBT(0, 1024,
                            1563 - (i + 1) * alto_ribbon,
                            1563 - i * alto_ribbon)
            )
            for i in range(5)
        ]

    # ── Textos ────────────────────────────────────────────────────────────────
    def _crear_textos(self):
        """Crea todos los objetos Text del menú. Se llama una sola vez en __init__."""
        cx = ANCHO_VENTANA // 2

        self.txt_titulo    = arcade.Text("UAIBOT", cx, ALTO_VENTANA - 120,
                                          arcade.color.GOLD, 64, anchor_x="center", bold=True)
        self.txt_subtitulo = arcade.Text("OFIRCA 2026", cx, ALTO_VENTANA - 170,
                                          (52, 152, 219), 20, anchor_x="center")
        self.txt_highscore = arcade.Text(f"Highscore: {self.datos['highscore']}",
                                          cx, ALTO_VENTANA - 210,
                                          arcade.color.GOLD, 14, anchor_x="center")
        self.txt_opciones  = [
            arcade.Text(op, cx, ALTO_VENTANA - 308 - i * 60,
                        arcade.color.WHITE, 22, anchor_x="center")
            for i, op in enumerate(OPCIONES)
        ]
        self.txt_instruccion   = arcade.Text("↑↓ para navegar   ENTER para seleccionar",
                                              cx, 40, (150, 150, 150), 12, anchor_x="center")
        # Subtextos de controles y dificultad (solo visibles en el submenu)
        self.txt_controles_val = arcade.Text("", cx, ALTO_VENTANA - 300 - 1 * 60 - 22,
                                              (52, 152, 219), 12, anchor_x="center")
        self.txt_dificultad_val = arcade.Text("", cx, ALTO_VENTANA - 300 - 2 * 60 - 22,
                                               (52, 152, 219), 12, anchor_x="center")
        self._actualizar_subtextos()

    def _actualizar_subtextos(self):
        """Refresca los valores mostrados de controles y dificultad."""
        controles = self.datos.get("controles", "flechas")
        self.txt_controles_val.value  = f"actual: {controles}"
        self.txt_dificultad_val.value = f"actual: {self.dificultad}"

    # ── Eventos de teclado ────────────────────────────────────────────────────
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
        """Alterna entre flechas y WASD con ← →. ESC cierra el submenu."""
        if symbol in (arcade.key.LEFT, arcade.key.RIGHT):
            actual = self.datos.get("controles", "flechas")
            nuevo  = "wasd" if actual == "flechas" else "flechas"
            guardado.actualizar_controles(nuevo)
            self.datos = guardado.cargar()
            self._actualizar_subtextos()
        elif symbol == arcade.key.ESCAPE:
            self.submenu = None

    def _manejar_dificultad(self, symbol):
        """Cambia la dificultad con ← →. ESC cierra el submenu."""
        if symbol == arcade.key.LEFT:
            idx             = DIFICULTADES.index(self.dificultad)
            self.dificultad = DIFICULTADES[(idx - 1) % len(DIFICULTADES)]
            self._guardar_dificultad()
        elif symbol == arcade.key.RIGHT:
            idx             = DIFICULTADES.index(self.dificultad)
            self.dificultad = DIFICULTADES[(idx + 1) % len(DIFICULTADES)]
            self._guardar_dificultad()
        elif symbol == arcade.key.ESCAPE:
            self.submenu = None

    def _guardar_dificultad(self):
        datos = guardado.cargar()
        datos["dificultad"] = self.dificultad
        guardado.guardar(datos)
        self._actualizar_subtextos()

    # ── Eventos de mouse ──────────────────────────────────────────────────────
    def on_mouse_motion(self, x, y, dx, dy):
        """Resalta la opción bajo el cursor cuando no hay submenú abierto."""
        if self.submenu is not None:
            return
        cx = ANCHO_VENTANA // 2
        for i in range(len(OPCIONES)):
            y_boton = ALTO_VENTANA - 300 - i * 60
            if (cx - 140 <= x <= cx + 140) and (y_boton - 27 <= y <= y_boton + 27):
                self.opcion_seleccionada = i
                break

    def on_mouse_press(self, x, y, button, modifiers):
        """Selecciona la opción bajo el cursor al hacer click izquierdo."""
        if button != arcade.MOUSE_BUTTON_LEFT or self.submenu is not None:
            return
        cx = ANCHO_VENTANA // 2
        for i in range(len(OPCIONES)):
            y_boton = ALTO_VENTANA - 300 - i * 60
            if (cx - 140 <= x <= cx + 140) and (y_boton - 27 <= y <= y_boton + 27):
                self.opcion_seleccionada = i
                if i == 0:
                    self._iniciar_partida()
                elif i == 1:
                    self.submenu = "controles"
                elif i == 2:
                    self.submenu = "dificultad"
                break

    # ── Inicio de partida ─────────────────────────────────────────────────────
    def _iniciar_partida(self):
        """Crea la vista de juego y la muestra con la dificultad y controles actuales."""
        from juego import Juego
        juego = Juego(
            dificultad=self.dificultad,
            controles=self.datos.get("controles", "flechas")
        )
        juego.setup()
        self.window.show_view(juego)

    # ── Dibujo ────────────────────────────────────────────────────────────────
    def on_draw(self):
        self.window.clear((20, 28, 36))

        # Fondo ilustrado con overlay oscuro para legibilidad del texto
        arcade.draw_texture_rect(
            self.img_fondo,
            arcade.XYWH(ANCHO_VENTANA // 2, ALTO_VENTANA // 2, ANCHO_VENTANA, ALTO_VENTANA)
        )
        arcade.draw_lrbt_rectangle_filled(0, ANCHO_VENTANA, 0, ALTO_VENTANA, (0, 0, 0, 100))

        self.txt_titulo.draw()
        self.txt_subtitulo.draw()
        self.txt_highscore.draw()
        self.txt_instruccion.draw()

        cx = ANCHO_VENTANA // 2
        for i, txt in enumerate(self.txt_opciones):
            y = ALTO_VENTANA - 300 - i * 60
            # La opción seleccionada se agranda ligeramente
            ancho = 280 if i == self.opcion_seleccionada and self.submenu is None else 260
            arcade.draw_texture_rect(self.img_btn[i], arcade.XYWH(cx, y - 5, ancho, 55))
            txt.color = arcade.color.WHITE if (i == self.opcion_seleccionada and self.submenu is None) else (200, 200, 200)
            txt.draw()

        # Submenú flotante para controles o dificultad
        if self.submenu == "controles":
            self._dibujar_submenu("Controles",
                f"actual: {self.datos.get('controles', 'flechas')}\n← → para cambiar\nESC para volver")
        elif self.submenu == "dificultad":
            self._dibujar_submenu("Dificultad",
                f"actual: {self.dificultad}\n← → para cambiar\nESC para volver")

    def _dibujar_submenu(self, titulo, instruccion):
        """Dibuja un cuadro flotante centrado con título e instrucciones."""
        cx = ANCHO_VENTANA // 2
        cy = ALTO_VENTANA // 2
        arcade.draw_lrbt_rectangle_filled(cx - 220, cx + 220, cy - 80, cy + 80, (30, 39, 46))
        arcade.draw_lrbt_rectangle_outline(cx - 220, cx + 220, cy - 80, cy + 80, (52, 152, 219), 2)
        arcade.Text(titulo, cx, cy + 50, arcade.color.GOLD, 18,
                    anchor_x="center", bold=True).draw()
        arcade.Text(instruccion, cx, cy, (200, 200, 200), 13,
                    anchor_x="center", multiline=True, width=400).draw()