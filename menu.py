# menu.py
# Pantalla de inicio del juego con fondo ilustrado y botones tipo ribbon.
# Navegación por teclado (↑↓ + ENTER) y mouse (hover + click).
#
# Ronda 2 (Fase 0.4 del plan): el menú pasa de 3 a 6 entradas —
# Viaje, Infinito, Multijugador, Tutorial, Inventario/Bestiario y
# Controles — y se elimina la selección manual de dificultad (el Modo
# Infinito la reemplaza escalando solo, ver Fase 1 del plan).
#
# De estas 6 entradas, Tutorial, Infinito y Controles llevan a una
# pantalla funcional:
#   - Tutorial (tutorial.py) es el nivel único y fijo donde se cumplen
#     las 13 consignas graduadas de OFIRCA (7 de Ronda 1 + 6 de Ronda 2)
#     — vista propia, autocontenida, sin dificultad ni mapas de Tiled.
#   - Infinito (juego.py) es el motor de Juego de Ronda 1 (dificultad,
#     Tiled, progresión) pero sin selección manual de dificultad ni
#     techo de nivel: escala sola cada 10 niveles hasta tope "dificil"
#     y sigue indefinidamente hasta que el jugador pierde o sale.
# Las otras tres entradas (Viaje, Multijugador, Inventario/Bestiario)
# muestran una pantalla "Próximamente" (clase Placeholder, al final del
# archivo) hasta que se implementen en sus fases correspondientes.

import arcade

import guardado
from constantes import *

OPCIONES = ["Viaje", "Infinito", "Multijugador", "Tutorial", "Inventario / Bestiario", "Controles"]

# Modos que todavía no tienen pantalla propia: al seleccionarlos se
# muestra el Placeholder en vez de iniciar algo. Se van sacando de esta
# lista a medida que cada modo se implementa en las fases siguientes.
MODOS_PENDIENTES = {"Viaje", "Multijugador", "Inventario / Bestiario"}


class Menu(arcade.View):
    def __init__(self):
        super().__init__()
        self.datos               = guardado.cargar()
        self.opcion_seleccionada = 0
        self.submenu             = None   # None | "controles"
        self._cargar_assets()
        self._crear_textos()

    # ── Assets ────────────────────────────────────────────────────────────────
    def _cargar_assets(self):
        """Carga el fondo del menú y los ribbons de botones desde sus spritesheets."""
        self.img_fondo = arcade.load_texture("assets/fondo_menu.png")

        # El spritesheet de botones tiene 5 ribbons apilados verticalmente.
        # Con 6 opciones en el menú, el sexto botón reutiliza uno de los
        # ribbons existentes (índice % 5) para no romper si todavía no se
        # agregó un sexto diseño — ver README, sección "Para el diseñador
        # de sprites", para sumar un ribbon más cuando haya tiempo de arte.
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

        self.txt_titulo    = arcade.Text("UAIBOT", cx, ALTO_VENTANA - 90,
                                          arcade.color.GOLD, 56, anchor_x="center", bold=True)
        self.txt_subtitulo = arcade.Text("OFIRCA 2026", cx, ALTO_VENTANA - 132,
                                          (52, 152, 219), 18, anchor_x="center")
        self.txt_highscore = arcade.Text(f"Highscore: {self.datos['highscore']}",
                                          cx, ALTO_VENTANA - 164,
                                          arcade.color.GOLD, 13, anchor_x="center")

        # Con 6 opciones el espaciado se achica respecto a la versión de 3
        # (Ronda 1 usaba 60px entre botones; acá 46px para que las 6 entren
        # en la ventana sin superponerse con las instrucciones de abajo).
        self.espaciado_opciones = 46
        self.y_primera_opcion   = ALTO_VENTANA - 210

        self.txt_opciones  = [
            arcade.Text(op, cx, self.y_primera_opcion - i * self.espaciado_opciones,
                        arcade.color.WHITE, 17, anchor_x="center")
            for i, op in enumerate(OPCIONES)
        ]
        self.txt_instruccion = arcade.Text("↑↓ para navegar   ENTER para seleccionar",
                                            cx, 34, (150, 150, 150), 11, anchor_x="center")

        # Subtexto de controles (solo visible en el submenu de Controles)
        idx_controles = OPCIONES.index("Controles")
        y_controles   = self.y_primera_opcion - idx_controles * self.espaciado_opciones - 18
        self.txt_controles_val = arcade.Text("", cx, y_controles,
                                              (52, 152, 219), 11, anchor_x="center")
        self._actualizar_subtextos()

    def _actualizar_subtextos(self):
        """Refresca el valor mostrado de controles."""
        controles = self.datos.get("controles", "flechas")
        self.txt_controles_val.value = f"actual: {controles}"

    # ── Eventos de teclado ────────────────────────────────────────────────────
    def on_key_press(self, symbol, modifiers):
        if self.submenu == "controles":
            self._manejar_controles(symbol)
        else:
            self._manejar_menu(symbol)

    def _manejar_menu(self, symbol):
        if symbol == arcade.key.UP:
            self.opcion_seleccionada = (self.opcion_seleccionada - 1) % len(OPCIONES)
        elif symbol == arcade.key.DOWN:
            self.opcion_seleccionada = (self.opcion_seleccionada + 1) % len(OPCIONES)
        elif symbol == arcade.key.ENTER:
            self._elegir_opcion(OPCIONES[self.opcion_seleccionada])

    def _elegir_opcion(self, opcion):
        """Punto único de entrada para resolver qué hacer al elegir una
        opción del menú, sea por teclado o por mouse."""
        if opcion == "Tutorial":
            self._iniciar_tutorial()
        elif opcion == "Infinito":
            self._iniciar_infinito()
        elif opcion == "Controles":
            self.submenu = "controles"
        elif opcion in MODOS_PENDIENTES:
            self.window.show_view(Placeholder(opcion))

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

    # ── Eventos de mouse ──────────────────────────────────────────────────────
    def _opcion_bajo_cursor(self, x, y):
        """Devuelve el índice de la opción bajo (x, y), o None si no hay
        ninguna. Centraliza el cálculo del hitbox para que on_mouse_motion
        y on_mouse_press usen siempre el mismo criterio."""
        cx = ANCHO_VENTANA // 2
        for i in range(len(OPCIONES)):
            y_boton = self.y_primera_opcion - i * self.espaciado_opciones
            if (cx - 140 <= x <= cx + 140) and (y_boton - 20 <= y <= y_boton + 20):
                return i
        return None

    def on_mouse_motion(self, x, y, dx, dy):
        """Resalta la opción bajo el cursor cuando no hay submenú abierto."""
        if self.submenu is not None:
            return
        indice = self._opcion_bajo_cursor(x, y)
        if indice is not None:
            self.opcion_seleccionada = indice

    def on_mouse_press(self, x, y, button, modifiers):
        """Selecciona la opción bajo el cursor al hacer click izquierdo."""
        if button != arcade.MOUSE_BUTTON_LEFT or self.submenu is not None:
            return
        indice = self._opcion_bajo_cursor(x, y)
        if indice is not None:
            self.opcion_seleccionada = indice
            self._elegir_opcion(OPCIONES[indice])

    # ── Inicio de partida ─────────────────────────────────────────────────────
    def _iniciar_tutorial(self):
        """Arranca el nivel único de Tutorial (tutorial.py), donde se
        cumplen las 13 consignas graduadas de OFIRCA — separado de la
        progresión de 10 niveles con dificultad que usa Juego."""
        from tutorial import Tutorial
        vista = Tutorial(controles=self.datos.get("controles", "flechas"))
        vista.setup()
        self.window.show_view(vista)

    def _iniciar_infinito(self):
        """Arranca Juego (juego.py) sin selección manual de dificultad:
        escala sola cada 10 niveles y no tiene techo de nivel."""
        from juego import Juego
        juego = Juego(controles=self.datos.get("controles", "flechas"))
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
            y = self.y_primera_opcion - i * self.espaciado_opciones
            seleccionada = (i == self.opcion_seleccionada and self.submenu is None)
            ancho = 260 if seleccionada else 240
            ribbon = self.img_btn[i % len(self.img_btn)]
            arcade.draw_texture_rect(ribbon, arcade.XYWH(cx, y - 4, ancho, 40))
            txt.color = arcade.color.WHITE if seleccionada else (200, 200, 200)
            txt.draw()

        if self.submenu == "controles":
            self._dibujar_submenu("Controles",
                f"actual: {self.datos.get('controles', 'flechas')}\n← → para cambiar\nESC para volver")

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


class Placeholder(arcade.View):
    """Pantalla temporal para los modos que todavía no tienen contenido
    propio (Viaje, Multijugador, Inventario/Bestiario).

    Existe solo para que la navegación del menú funcione de punta a
    punta desde ya (objetivo de la Fase 0.4); cada entrada de
    MODOS_PENDIENTES se va sacando de esa lista, y este Placeholder deja
    de usarse para ese modo, a medida que se implementa en su fase
    correspondiente del plan de Ronda 2."""

    def __init__(self, titulo):
        super().__init__()
        self.titulo = titulo

    def on_draw(self):
        self.window.clear((20, 28, 36))
        cx, cy = ANCHO_VENTANA // 2, ALTO_VENTANA // 2
        arcade.Text(self.titulo, cx, cy + 30, arcade.color.GOLD, 32,
                    anchor_x="center", anchor_y="center", bold=True).draw()
        arcade.Text("Proximamente", cx, cy - 10, (200, 200, 200), 16,
                    anchor_x="center", anchor_y="center").draw()
        arcade.Text("ESC para volver al menu", cx, cy - 50, (120, 120, 120), 12,
                    anchor_x="center", anchor_y="center").draw()

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.ESCAPE:
            self.window.show_view(Menu())