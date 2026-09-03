# menu.py
# Pantalla de inicio del juego con fondo ilustrado y botones tipo ribbon.
# Navegación por teclado (↑↓ + ENTER) y mouse (hover + click).
#
# Ronda 2 (Fase 0.4 del plan): el menú pasa de 3 a 6 entradas —
# Viaje, Infinito, Multijugador, Tutorial, Inventario/Bestiario y
# Ajustes — y se elimina la selección manual de dificultad (el Modo
# Infinito la reemplaza escalando solo, ver Fase 1 del plan).
#
# De estas 6 entradas, Tutorial, Infinito, Viaje y Ajustes llevan a una
# pantalla funcional:
#   - Tutorial (tutorial.py) es el nivel único y fijo donde se cumplen
#     las 13 consignas graduadas de OFIRCA (7 de Ronda 1 + 6 de Ronda 2)
#     — vista propia, autocontenida, sin dificultad ni mapas de Tiled.
#   - Infinito (juego.py) genera niveles procedurales sin techo, con la
#     dificultad escalando sola cada 10 niveles hasta tope "dificil".
#   - Viaje (viaje.py) es la campaña: 10 niveles fijos diseñados en Tiled
#     (los de dificultad media), con cronómetro y desbloqueo de los
#     personajes de la familia de UAIBOT.
#   - Multijugador (multijugador.py) es el cooperativo para dos jugadores
#     en red local, sobre los 10 mapas de dificultad difícil.
#   - Inventario/Bestiario (clase Inventario, en este archivo) muestra la
#     familia y los objetos coleccionables del Multijugador.
#
# El fondo es una ilustración fija: la familia y el merendero ya están
# pintados dentro de ella. Hubo una versión con capas animadas encima
# -nubes, pájaros, luciérnagas y la familia caminando- que se quitó porque
# los sprites de juego sobre una ilustración pintada nunca terminaron de
# integrarse, por más luz y sombra que se les aplicara.

import arcade

import guardado
import sprites as spr
import ui
from constantes import *

OPCIONES = ["Viaje", "Infinito", "Multijugador", "Tutorial", "Inventario", "Ajustes"]

# Filas del submenu de Ajustes: la primera es el selector de controles que
# antes era su propia entrada del menú; las otras dos, el volumen de la
# música del menú y el de la música de niveles, en pasos de 10%.
FILAS_AJUSTES = ["Controles", "Volumen menú", "Volumen niveles"]
PASO_VOLUMEN  = 0.1

# Modos que todavía no tienen pantalla propia: al seleccionarlos se
# muestra el Placeholder en vez de iniciar algo. Se van sacando de esta
# lista a medida que cada modo se implementa en las fases siguientes.
MODOS_PENDIENTES: set = set()

class Menu(arcade.View):
    # Player de música a nivel de clase: el menú se reconstruye cada vez que
    # se vuelve de un modo (show_view(Menu())), y así el nuevo Menú puede
    # detener la música del anterior en vez de montarle una encima.
    musica_player = None

    def __init__(self):
        """Arma el menú principal: assets, textos y estado de navegación."""
        super().__init__()
        self.datos               = guardado.cargar()
        self.opcion_seleccionada = 0
        self.submenu             = None   # None | "ajustes"
        self.ajuste_seleccionado = 0      # fila activa dentro del submenu de Ajustes
        self._cargar_assets()
        self._crear_textos()

    # ── Assets ────────────────────────────────────────────────────────────────
    def _cargar_assets(self):
        """Carga el fondo ilustrado del menú y los ribbons de botones."""
        self.img_fondo = arcade.load_texture("assets/imagenes/fondo_menu.png")

        # Los ribbons vienen apilados verticalmente, uno por opción del menú.
        # El alto de cada uno sale de la altura REAL del archivo dividida por
        # la cantidad de ribbons: antes estaba escrito a mano como 1563, que
        # no es la altura del PNG (1536), y eso corría todos los cortes 27px
        # y hacía que el primer ribbon leyera fuera de la imagen.
        sheet        = arcade.load_spritesheet("assets/imagenes/botones.png")
        alto_hoja    = sheet.image.height
        cantidad     = len(OPCIONES)
        alto_ribbon  = alto_hoja // cantidad
        self.img_btn = [
            sheet.get_texture(
                arcade.LRBT(0, sheet.image.width,
                            alto_hoja - (i + 1) * alto_ribbon,
                            alto_hoja - i * alto_ribbon)
            )
            for i in range(cantidad)
        ]

        self.musica = arcade.load_sound("assets/audio/MenuMusic.wav")

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

        DESPLAZAMIENTO_TEXTO_Y = 10

        self.txt_opciones  = [
            arcade.Text(op, cx, self.y_primera_opcion - i * self.espaciado_opciones - DESPLAZAMIENTO_TEXTO_Y,
                        arcade.color.BLACK, 20, anchor_x="center")
            for i, op in enumerate(OPCIONES)
        ]
        self.txt_instruccion = arcade.Text("↑↓ para navegar   ENTER para seleccionar",
                                            cx, 34, (150, 150, 150), 11, anchor_x="center")

        # Subtexto de Ajustes (solo visible en el submenu): un resumen de la
        # configuración actual, refrescado por _actualizar_subtextos.
        idx_ajustes = OPCIONES.index("Ajustes")
        y_ajustes   = self.y_primera_opcion - idx_ajustes * self.espaciado_opciones - 18
        self.txt_controles_val = arcade.Text("", cx, y_ajustes,
                                              (52, 152, 219), 11, anchor_x="center")
        self._actualizar_subtextos()

    def _actualizar_subtextos(self):
        """Refresca el resumen de configuración que se ve bajo el botón."""
        controles = self.datos.get("controles", "flechas")
        vol_menu  = int(self.datos.get("volumen_musica_menu", 0.3) * 100)
        vol_nivel = int(self.datos.get("volumen_musica_nivel", 0.3) * 100)
        self.txt_controles_val.value = f"{controles} · música {vol_menu}% / {vol_nivel}%"

    # ── Animación del fondo ───────────────────────────────────────────────────
    def on_show_view(self):
        """Arranca la música del menú. Se usa on_show_view y no __init__ porque
        __init__ también corre antes de que la ventana muestre esta vista; acá
        se garantiza que suena cada vez que el menú aparece en pantalla."""
        self.detener_musica()
        Menu.musica_player = arcade.play_sound(
            self.musica, volume=self.datos.get("volumen_musica_menu", 0.3), loop=True)

    @classmethod
    def detener_musica(cls):
        """Detiene la música del menú si estaba sonando."""
        if cls.musica_player:
            arcade.stop_sound(cls.musica_player)
            cls.musica_player = None

    def on_key_press(self, symbol, modifiers):
        """Reparte las teclas entre el menú y el submenú de Ajustes."""
        if self.submenu == "ajustes":
            self._manejar_ajustes(symbol)
        else:
            self._manejar_menu(symbol)

    def _manejar_menu(self, symbol):
        """Mueve la selección del menú y entra en la opción elegida."""
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
        elif opcion == "Viaje":
            self._iniciar_viaje()
        elif opcion == "Multijugador":
            self._iniciar_multijugador()
        elif opcion == "Ajustes":
            self.submenu = "ajustes"
        elif opcion == "Inventario":
            self._iniciar_inventario()
        elif opcion in MODOS_PENDIENTES:
            self.window.show_view(Placeholder(opcion))

    def _manejar_ajustes(self, symbol):
        """Navega el submenu de Ajustes: ↑↓ elige fila, ← → cambia el valor
        de esa fila (controles o volumen), ESC cierra el submenu."""
        if symbol == arcade.key.UP:
            self.ajuste_seleccionado = (self.ajuste_seleccionado - 1) % len(FILAS_AJUSTES)
        elif symbol == arcade.key.DOWN:
            self.ajuste_seleccionado = (self.ajuste_seleccionado + 1) % len(FILAS_AJUSTES)
        elif symbol in (arcade.key.LEFT, arcade.key.RIGHT):
            direccion = 1 if symbol == arcade.key.RIGHT else -1
            self._cambiar_ajuste(self.ajuste_seleccionado, direccion)
        elif symbol == arcade.key.ESCAPE:
            self.submenu = None
            self.ajuste_seleccionado = 0

    def _cambiar_ajuste(self, fila, direccion):
        """Aplica y persiste el cambio de la fila indicada.

        El volumen del menú se aplica EN VIVO sobre el player que ya está
        sonando (el player de pyglet acepta .volume a mitad de reproducción),
        así el jugador escucha el efecto sin cortar la música; el de niveles
        solo se guarda y rige desde la próxima partida que arranque."""
        if fila == 0:  # Controles: flechas <-> wasd
            actual = self.datos.get("controles", "flechas")
            guardado.actualizar_controles("wasd" if actual == "flechas" else "flechas")
        elif fila == 1:  # Volumen de la música del menú
            actual = self.datos.get("volumen_musica_menu", 0.3)
            nuevo   = min(1.0, max(0.0, round(actual + direccion * PASO_VOLUMEN, 2)))
            if Menu.musica_player:
                Menu.musica_player.volume = nuevo
            guardado.actualizar_volumenes(menu=nuevo)
        elif fila == 2:  # Volumen de la música de los niveles
            actual = self.datos.get("volumen_musica_nivel", 0.3)
            nuevo   = min(1.0, max(0.0, round(actual + direccion * PASO_VOLUMEN, 2)))
            guardado.actualizar_volumenes(nivel=nuevo)

        self.datos = guardado.cargar()
        self._actualizar_subtextos()

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
        self.detener_musica()
        from tutorial import Tutorial
        vista = Tutorial(controles=self.datos.get("controles", "flechas"))
        vista.setup()
        self.window.show_view(vista)

    def _iniciar_infinito(self):
        """Arranca Juego (juego.py) sin selección manual de dificultad:

        escala sola cada 10 niveles y no tiene techo de nivel."""
        self.detener_musica()
        from juego import Juego
        juego = Juego(controles=self.datos.get("controles", "flechas"))
        juego.setup()
        self.window.show_view(juego)

    def _iniciar_viaje(self):
        """Arranca la campaña (viaje.py): 10 niveles fijos diseñados en
        Tiled, con cronómetro y desbloqueo de personajes."""
        self.detener_musica()
        from viaje import Viaje
        vista = Viaje(controles=self.datos.get("controles", "flechas"))
        vista.setup()
        self.window.show_view(vista)

    def _iniciar_multijugador(self):
        """Abre la sala de multijugador (multijugador.py), donde se crea
        una partida o se entra a una existente por la red local."""
        self.detener_musica()
        from multijugador import SalaMultijugador
        self.window.show_view(SalaMultijugador(
            controles=self.datos.get("controles", "flechas")
        ))

    def _iniciar_inventario(self):
        """Abre el Inventario: la familia con sus habilidades y
        los objetos coleccionables del Multijugador con su descripción.
        La música del menú sigue sonando (como en el Placeholder)."""
        self.window.show_view(Inventario())

    # ── Dibujo ────────────────────────────────────────────────────────────────
    def on_draw(self):
        """Dibuja el fondo ilustrado, los botones y el submenú si está abierto."""
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
            ribbon = self.img_btn[i]
            arcade.draw_texture_rect(ribbon, arcade.XYWH(cx, y - 4, ancho, 40))
            txt.color = arcade.color.WHITE if seleccionada else (200, 200, 200)
            txt.draw()

        if self.submenu == "ajustes":
            self._dibujar_submenu_ajustes()

    def _dibujar_submenu_ajustes(self):
        """Dibuja el cuadro de Ajustes: una fila por ajuste con su valor,
        la activa resaltada. Usa el mismo cuadro que el resto de las
        pantallas de menú (ver ui.dialogo)."""
        cx = ANCHO_VENTANA // 2
        cy = ALTO_VENTANA // 2
        ancho, alto = 460, 240
        izq, der, aba, arr = ui.dialogo(cx, cy, ancho, alto, "Ajustes")

        # El valor de cada fila al lado de su etiqueta: el control actual y
        # los volúmenes como porcentaje. La fila activa lleva además una
        # banda de fondo, porque solo el color dorado no alcanzaba para
        # ubicarla de un vistazo.
        valores = [
            self.datos.get("controles", "flechas"),
            f"{int(self.datos.get('volumen_musica_menu', 0.3) * 100)}%",
            f"{int(self.datos.get('volumen_musica_nivel', 0.3) * 100)}%",
        ]
        for i, fila in enumerate(FILAS_AJUSTES):
            y      = arr - 76 - i * 38
            activa = (i == self.ajuste_seleccionado)
            color  = arcade.color.GOLD if activa else (170, 170, 170)
            if activa:
                arcade.draw_lrbt_rectangle_filled(izq + 26, der - 26, y - 16, y + 16,
                                                  (52, 152, 219, 45))
            arcade.Text(fila, izq + 40, y, color, 14, anchor_y="center").draw()
            arcade.Text(f"< {valores[i]} >", der - 90, y, color, 14,
                        anchor_x="center", anchor_y="center").draw()

        arcade.Text("↑↓ para elegir   ← → para cambiar   ESC para volver",
                    cx, aba + 26, (120, 120, 120), 11,
                    anchor_x="center", anchor_y="center").draw()


class Inventario(arcade.View):
    """Inventario(Fase 5 del plan): dos secciones.

    - PERSONAJES: la familia completa con su habilidad. Los aún no
      desbloqueados en Modo Viaje se ven oscurecidos y sin datos — es el
      "bestiario" que se completa jugando la campaña.
    - OBJETOS: los 10 coleccionables cooperativos del Multijugador, cada
      uno con su descripción. El que todavía no se consiguió se ve
      desvanecido; conseguirlo es parte de la Fase 4.

    Navegación: ←→ mueve la selección dentro de la sección, ↑↓ cambia de
    sección, ESC vuelve al menú. La música del menú sigue sonando, como en
    el Placeholder."""

    def __init__(self):
        """Carga los retratos de la familia y las imágenes de los objetos."""
        super().__init__()
        self.seccion       = 0    # 0 = personajes, 1 = objetos
        self.sel_personaje = 0
        self.sel_objeto    = 0

        # Texturas: la familia reusa las mismas hojas que el fondo del menú
        # (frame 0 de Idle, el "retrato"), y los objetos ya son PNG chicos.
        self.familia     = spr.cargar_familia(PERSONAJES_FAMILIA, 128, 128)
        self.img_objetos = [spr.cargar(o["archivo"]) for o in OBJETOS_MULTIJUGADOR]

    def on_show_view(self):
        """Se releen los desbloqueos cada vez que se entra, así lo conseguido
        en otra partida aparece sin reiniciar el juego."""
        self.datos = guardado.cargar()

    # ── Eventos ───────────────────────────────────────────────────────────
    def on_key_press(self, symbol, modifiers):
        """Cambia de sección con arriba/abajo y de ítem con izquierda/derecha."""
        if symbol == arcade.key.ESCAPE:
            self.window.show_view(Menu())
        elif symbol == arcade.key.UP:
            self.seccion = (self.seccion - 1) % 2
        elif symbol == arcade.key.DOWN:
            self.seccion = (self.seccion + 1) % 2
        elif self.seccion == 0:
            if symbol in (arcade.key.LEFT, arcade.key.RIGHT):
                paso = -1 if symbol == arcade.key.LEFT else 1
                self.sel_personaje = (self.sel_personaje + paso) % len(PERSONAJES_FAMILIA)
        elif self.seccion == 1:
            if symbol in (arcade.key.LEFT, arcade.key.RIGHT):
                paso = -1 if symbol == arcade.key.LEFT else 1
                self.sel_objeto = (self.sel_objeto + paso) % len(OBJETOS_MULTIJUGADOR)
            elif symbol in (arcade.key.UP, arcade.key.DOWN):
                # En la grilla de 5 columnas, subir/bajar es saltar de fila.
                fila = -5 if symbol == arcade.key.UP else 5
                self.sel_objeto = (self.sel_objeto + fila) % len(OBJETOS_MULTIJUGADOR)

    # ── Dibujo ────────────────────────────────────────────────────────────
    def on_draw(self):
        """Dibuja la sección activa dentro del cuadro del Bestiario."""
        self.window.clear(ui.FONDO)
        ui.encabezado("INVENTARIO")
        ui.solapas(("PERSONAJES", "OBJETOS"), self.seccion, ALTO_VENTANA - 96,
                   separacion=220)

        if self.seccion == 0:
            self._dibujar_personajes()
        else:
            self._dibujar_objetos()

        ui.ayuda("←→ moverse   ↑↓ cambiar seccion   ESC para volver")

    # Medidas del cuadro de contenido, compartidas por las dos secciones para
    # que al cambiar de solapa no salte el marco.
    CUADRO_ANCHO = 860
    CUADRO_ALTO  = 380

    def _cuadro(self):
        """Dibuja el cuadro y devuelve lo que necesitan las dos secciones
        para ubicar su contenido: el centro horizontal y tres bordes."""
        cx = ANCHO_VENTANA // 2
        cy = ALTO_VENTANA // 2 - 26
        izq, der, _, arr = ui.dialogo(cx, cy, self.CUADRO_ANCHO, self.CUADRO_ALTO)
        return cx, izq, der, arr

    def _dibujar_personajes(self):
        """La familia en fila: retrato (Idle frame 0), nombre en su color y,
        abajo, la ficha del seleccionado. Bloqueado = oscurecido."""
        cx, izq, der, arr = self._cuadro()
        desbloqueados = self.datos["personajes_desbloqueados"]

        # El nombre va bien abajo del retrato: el robot llega hasta el borde
        # inferior de su recuadro, así que con menos separación el texto le
        # queda encima de los pies.
        y_retrato = arr - 108
        for i, personaje in enumerate(PERSONAJES_FAMILIA):
            x       = cx + (i - 1.5) * 180
            activo  = (i == self.sel_personaje)
            abierto = personaje["id"] in desbloqueados

            if activo:
                arcade.draw_lrbt_rectangle_outline(
                    x - 80, x + 80, y_retrato - 104, y_retrato + 78,
                    arcade.color.GOLD, 2)

            frame = self.familia[personaje["id"]]["idle"][0]
            # Sin desbloquear se dibuja casi negro: se ve la silueta, no el
            # detalle — el incentivo a jugar la campaña es conocerlos.
            tinte = (60, 60, 60) if not abierto else personaje["color"]
            arcade.draw_texture_rect(frame, arcade.XYWH(x, y_retrato, 150, 150),
                                     color=arcade.types.Color(*tinte))
            nombre = personaje["nombre"] if abierto else "??????"
            ui.etiqueta(f"bes_nombre{i}", nombre, x, y_retrato - 90,
                     personaje["color"] if abierto else (110, 110, 110),
                     13, anchor_x="center", anchor_y="center", bold=True).draw()

        # Línea que separa la fila de la ficha del seleccionado.
        y_regla = y_retrato - 116
        arcade.draw_line(izq + 40, y_regla, der - 40, y_regla, (58, 72, 82), 1)

        personaje = PERSONAJES_FAMILIA[self.sel_personaje]
        y = y_regla - 26
        if personaje["id"] in desbloqueados:
            ui.etiqueta("bes_ficha", f"{personaje['nombre']} — {personaje['habilidad_nombre']}",
                     cx, y, arcade.color.WHITE, 15,
                     anchor_x="center", anchor_y="center", bold=True).draw()
            extra = (f"{personaje['habilidad_desc']}. "
                     "Disponible desde el inicio en Tutorial y Multijugador; "
                     "en Modo Viaje se suma al equipo al avanzar la campaña.")
            ui.parrafo(extra, cx, y - 28, self.CUADRO_ANCHO - 140, 12,
                       (200, 200, 200))
        else:
            ui.etiqueta("bes_ficha", "Aún no se sumó al equipo.", cx, y,
                     (200, 120, 120), 14,
                     anchor_x="center", anchor_y="center", bold=True).draw()
            ui.etiqueta("bes_bloqueado", "Se desbloquea avanzando el Modo Viaje.",
                     cx, y - 26, (200, 200, 200), 12,
                     anchor_x="center", anchor_y="center").draw()

    def _dibujar_objetos(self):
        """Los 10 coleccionables en grilla de 5×2 con su ficha debajo.

        Sin conseguir = desvanecido; la selección se marca en dorado."""
        cx, izq, der, arr = self._cuadro()
        conseguidos = self.datos["objetos_multijugador"]

        y_grilla = arr - 68
        for i, objeto in enumerate(OBJETOS_MULTIJUGADOR):
            col, fila = i % 5, i // 5
            x = cx + (col - 2) * 130
            y = y_grilla - fila * 96
            if i == self.sel_objeto:
                arcade.draw_lrbt_rectangle_outline(
                    x - 46, x + 46, y - 44, y + 44, arcade.color.GOLD, 2)

            # Sin conseguir se ve la silueta desvanecida: alcanza para
            # reconocerlo, pero invita a ir a buscarlo.
            alpha = 255 if objeto["id"] in conseguidos else 90
            arcade.draw_texture_rect(
                self.img_objetos[i], arcade.XYWH(x, y, 72, 72),
                color=arcade.types.Color(255, 255, 255, alpha))

        y_regla = y_grilla - 96 - 60
        arcade.draw_line(izq + 40, y_regla, der - 40, y_regla, (58, 72, 82), 1)

        objeto = OBJETOS_MULTIJUGADOR[self.sel_objeto]
        tiene  = objeto["id"] in conseguidos
        y = y_regla - 24
        ui.etiqueta("bes_ficha", objeto["nombre"], cx, y, arcade.color.WHITE, 15,
                 anchor_x="center", anchor_y="center", bold=True).draw()
        alto = ui.parrafo(objeto["descripcion"], cx, y - 26,
                          self.CUADRO_ANCHO - 140, 12, (200, 200, 200))
        estado = "Conseguido" if tiene \
                 else "Aún no conseguido — se encuentra en el Modo Multijugador"
        ui.etiqueta("bes_estado", estado, cx, y - 34 - alto,
                 (100, 200, 100) if tiene else (200, 120, 120), 12,
                 anchor_x="center", anchor_y="center", bold=True).draw()


class Placeholder(arcade.View):
    """Pantalla temporal para los modos que todavía no tienen contenido
    propio. Queda sin uso desde que Inventario/Bestiario pasó a tener su
    pantalla (Fase 5), pero se mantiene: es el destino natural de cualquier
    entrada futura del menú que todavía no exista."""

    def __init__(self, titulo):
        """Guarda el título que va a mostrar la pantalla."""
        super().__init__()
        self.titulo = titulo

    def on_draw(self):
        """Dibuja el cartel de 'próximamente' centrado en la pantalla."""
        self.window.clear((20, 28, 36))
        cx, cy = ANCHO_VENTANA // 2, ALTO_VENTANA // 2
        arcade.Text(self.titulo, cx, cy + 30, arcade.color.GOLD, 32,
                    anchor_x="center", anchor_y="center", bold=True).draw()
        arcade.Text("Proximamente", cx, cy - 10, (200, 200, 200), 16,
                    anchor_x="center", anchor_y="center").draw()
        arcade.Text("ESC para volver al menu", cx, cy - 50, (120, 120, 120), 12,
                    anchor_x="center", anchor_y="center").draw()

    def on_key_press(self, symbol, modifiers):
        """ESC vuelve al menú principal."""
        if symbol == arcade.key.ESCAPE:
            self.window.show_view(Menu())