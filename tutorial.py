# tutorial.py
# Modo Tutorial: nivel único y fijo que reúne, en un solo lugar, las 7
# consignas obligatorias de Ronda 1 (contador de pasos, imagen en el
# merendero, sonido al moverse, sendero no repetible, 4 paredes marrones,
# reinicio con R, animación al ganar) y las 6 mecánicas nuevas de Ronda 2
# (cronómetro, cambio de personaje con cupo de pasos, comida obligatoria,
# sillas de ruedas por adyacencia, nombre+tiempo al ganar, deshacer con Z).
#
# A diferencia de Juego (juego.py), acá no hay dificultad, no se cargan
# mapas de Tiled y no se progresa a un "nivel siguiente": la partida
# termina al ganar o al quedarse sin personajes con pasos, con pantalla de
# reiniciar (R) o volver al menú (ESC). Es un archivo separado a propósito
# — las reglas son bastante distintas a la progresión de Juego (sendero
# compartido entre 4 personajes, cupos de pasos, recolección obligatoria,
# deshacer), y mezclar todo en una sola clase con flags perjudicaría la
# legibilidad que el jurado evalúa explícitamente.

import math

import arcade

import guardado
import sprites as spr
from constantes import *
from juego import Particula  # se reutiliza el confeti de victoria tal cual

# ── Layout fijo del nivel ───────────────────────────────────────────────────
# Mismo criterio que nivel.py usa para el nivel 1 de Ronda 1: posiciones
# hardcodeadas (no generación procedural), para que las 13 consignas se
# vean cumplidas de forma clara y reproducible.
PAREDES_FIJAS = {(3, 5), (7, 3), (10, 7), (5, 1)}

# Comida (hexágono): recolección obligatoria antes de poder ganar.
COMIDA_FIJA = {(2, 7), (6, 6), (9, 4), (11, 2)}

# Sillas de ruedas (triángulo): cada celda pide una cantidad EXACTA de
# pasadas por uno de sus lados (no se pisan, se bordean). El máximo real
# es 4 -uno por cada vecino ortogonal- porque el sendero compartido no
# permite repisar la misma celda dos veces.
SILLAS_FIJAS = {
    (4, 6): 2,
    (9, 2): 1,
}

TOTAL_FRAMES = 6
FRAME_WIDTH  = 128
FRAME_HEIGHT = 128

COLOR_PARED           = (101, 67, 33)
COLOR_SENDERO         = (30, 100, 160)
COLOR_FONDO_CLARO     = (44, 62, 80)
COLOR_FONDO_OSCURO    = (39, 55, 70)
COLOR_COMIDA          = (241, 196, 15)
COLOR_SILLA           = (52, 152, 219)
COLOR_SILLA_EXCEDIDA  = (192, 57, 43)


class Tutorial(arcade.View):
    """Nivel único de referencia para las 13 consignas graduadas de OFIRCA
    (7 de Ronda 1 + 6 de Ronda 2). Hereda de arcade.View para integrarse al
    sistema de vistas (menu -> tutorial -> menu)."""

    def __init__(self, controles="flechas"):
        super().__init__()
        self.controles = controles
        self._cargar_assets()

    # ── Setup / Reinicio ─────────────────────────────────────────────────────
    def setup(self):
        """Inicializa o reinicia el estado completo del nivel. Se llama al
        entrar a Tutorial y cada vez que se presiona R."""
        if hasattr(self, "musica_player") and self.musica_player:
            arcade.stop_sound(self.musica_player)
            self.musica_player = None
        self.musica_player = arcade.play_sound(self.musica, volume=0.3, loop=True)

        self.paredes         = set(PAREDES_FIJAS)
        self.comida_pendiente = set(COMIDA_FIJA)
        self.sillas = {
            pos: {"requeridas": req, "recolectadas": 0, "excedido": False}
            for pos, req in SILLAS_FIJAS.items()
        }

        self.col, self.fila = POS_INICIO
        self.sendero      = {POS_INICIO}   # compartido entre los 4 personajes
        self.direcciones  = {}
        self.historial    = []             # pila de snapshots para deshacer (Z)

        self.personaje_activo = 0
        self.pasos_restantes  = {p["id"]: MAX_PASOS_PERSONAJE for p in PERSONAJES_FAMILIA}
        self.pasos            = 0

        self.tiempo_transcurrido = 0.0
        self.estado       = "jugando"   # jugando | ingresando_nombre | victoria | perdido
        self.nombre_input = ""
        self.particulas   = []

        self.caminando      = False
        self.frame_actual   = 0
        self.timer_frame    = 0
        self.velocidad_frame = 8

        self.mostrar_anuncio = True
        self.timer_anuncio   = 0

        self._construir_capas_estaticas()
        self._crear_textos()
        self._actualizar_texto_personajes()
        self._actualizar_texto_recursos()

        self.px_x, self.px_y      = self._celda_a_px(*POS_INICIO)
        self.moviendose           = False
        self.velocidad_movimiento = 10

    # ── Construcción de capas estáticas (mismo patrón de SpriteList que
    # juego.py usa para no dibujar celda por celda en cada frame) ─────────────
    def _crear_sprite_celda(self, path, col, fila, color_fallback, forzar_color=False):
        x, y = self._celda_a_px(col, fila)
        tex = None if forzar_color else spr.cargar(path)
        if tex:
            sprite = arcade.Sprite(tex)
            sprite.width  = TAM_CELDA
            sprite.height = TAM_CELDA
        else:
            sprite = arcade.SpriteSolidColor(TAM_CELDA - 2, TAM_CELDA - 2, color=color_fallback)
        sprite.center_x = x
        sprite.center_y = y
        return sprite

    def _construir_capas_estaticas(self):
        """Fondo y paredes van SIEMPRE en color plano, no con los sprites
        de arte -esos quedan reservados para Modo Infinito-. Es el mismo
        criterio que ya usaba el nivel 1 fijo de Ronda 1 (forzar_color_nivel_1
        en juego.py): Tutorial es la referencia limpia de las consignas, y
        un fondo/paredes lisos hacen que UAIBOT, el merendero, la comida y
        las sillas de ruedas se destaquen con claridad."""
        self.fondo_sprites = arcade.SpriteList()
        for fila in range(FILAS):
            for col in range(COLUMNAS):
                color = COLOR_FONDO_CLARO if (col + fila) % 2 == 0 else COLOR_FONDO_OSCURO
                self.fondo_sprites.append(
                    self._crear_sprite_celda(SPRITE_CESPED, col, fila, color, forzar_color=True)
                )

        self.paredes_sprites = arcade.SpriteList()
        for (col, fila) in self.paredes:
            self.paredes_sprites.append(
                self._crear_sprite_celda(SPRITE_PARED, col, fila, COLOR_PARED, forzar_color=True)
            )

        self.sendero_sprites = arcade.SpriteList()

    def _agregar_huella(self, col, fila):
        """Agrega el sprite de huella de (col, fila) al sendero visual,
        eligiendo el sprite direccional según self.direcciones. Mismo
        patrón que juego.py."""
        if (col, fila) == POS_INICIO:
            return

        dc, df = self.direcciones.get((col, fila), (0, 0))
        if dc == 0 and df == 1:
            path = SPRITE_HUELLA_ARRIBA
        elif dc == 0 and df == -1:
            path = SPRITE_HUELLA_ABAJO
        elif dc == -1 and df == 0:
            path = SPRITE_HUELLA_IZQUIERDA
        else:
            path = SPRITE_HUELLA_DERECHA

        self.sendero_sprites.append(self._crear_sprite_celda(path, col, fila, COLOR_SENDERO))

    def _reconstruir_sendero_sprites(self):
        """Rearma la SpriteList del sendero desde self.sendero/direcciones.
        Se usa al deshacer (Z), en vez de tratar de revertir sprite por
        sprite — mismo criterio que _reconstruir_cajas_sprites en juego.py."""
        self.sendero_sprites = arcade.SpriteList()
        for (col, fila) in self.sendero:
            self._agregar_huella(col, fila)

    # ── Carga de assets ──────────────────────────────────────────────────────
    def _cargar_assets(self):
        sheet_idle = arcade.load_spritesheet("assets/Idle.png")
        sheet_walk = arcade.load_spritesheet("assets/Walk.png")
        self.frames_idle = [
            sheet_idle.get_texture(arcade.LRBT(i * FRAME_WIDTH, i * FRAME_WIDTH + FRAME_WIDTH, 0, FRAME_HEIGHT))
            for i in range(TOTAL_FRAMES)
        ]
        self.frames_walk = [
            sheet_walk.get_texture(arcade.LRBT(i * FRAME_WIDTH, i * FRAME_WIDTH + FRAME_WIDTH, 0, FRAME_HEIGHT))
            for i in range(TOTAL_FRAMES)
        ]

        # Sprite persistente del personaje activo: se reusa entre frames
        # (textura/tinte/posición se actualizan en _dibujar_personaje) en
        # vez de crear un arcade.Sprite nuevo en cada on_draw. En Arcade 3.x
        # un Sprite suelto no tiene .draw() -hay que dibujarlo dentro de una
        # SpriteList, aunque sea de un solo elemento- así que se envuelve en
        # self.sprites_personaje.
        self.sprite_personaje = arcade.Sprite(self.frames_idle[0])
        self.sprite_personaje.width  = TAM_CELDA
        self.sprite_personaje.height = TAM_CELDA
        self.sprites_personaje = arcade.SpriteList()
        self.sprites_personaje.append(self.sprite_personaje)

        self.img_merendero = arcade.load_texture("assets/merendero.png")

        self.snd_mover    = arcade.load_sound("assets/Moverse.wav")
        self.snd_no_mover = arcade.load_sound("assets/NoMoverse.wav")
        self.snd_victoria = arcade.load_sound("assets/CompletedLevel.wav")
        self.musica       = arcade.load_sound("assets/GameLevelMusic.wav")

    # ── Textos del panel ─────────────────────────────────────────────────────
    def _crear_textos(self):
        px = ANCHO_JUEGO
        pw = PANEL_ANCHO
        cx = px + pw // 2

        self.txt_titulo = arcade.Text("UAIBOT", cx, ALTO_VENTANA - 35,
                                       arcade.color.GOLD, 26, anchor_x="center", bold=True)
        self.txt_ofirca = arcade.Text("OFIRCA 2026", cx, ALTO_VENTANA - 58,
                                       (52, 152, 219), 12, anchor_x="center")
        self.txt_modo   = arcade.Text("TUTORIAL", cx, ALTO_VENTANA - 85,
                                       arcade.color.WHITE, 13, anchor_x="center", bold=True)

        self.txt_mision_titulo = arcade.Text("MISION", px + 16, ALTO_VENTANA - 115,
                                              arcade.color.GOLD, 11, bold=True)
        self.txt_mision = arcade.Text(
            "Recolecta toda la comida\ny pasa por las sillas de\n"
            "ruedas antes de llegar\nal merendero.",
            px + 16, ALTO_VENTANA - 135, (200, 200, 200), 10, multiline=True, width=pw - 32)

        self.txt_pasos_titulo = arcade.Text("PASOS TOTALES", px + 16, ALTO_VENTANA - 220,
                                             arcade.color.GOLD, 11, bold=True)
        self.txt_pasos        = arcade.Text("0", px + 16, ALTO_VENTANA - 244,
                                             (200, 200, 200), 22, bold=True)

        self.txt_cronometro_titulo = arcade.Text("TIEMPO", px + 16, ALTO_VENTANA - 278,
                                                   arcade.color.GOLD, 11, bold=True)
        self.txt_cronometro        = arcade.Text("0.0s", px + 16, ALTO_VENTANA - 302,
                                                   (200, 200, 200), 18, bold=True)

        self.txt_personajes_titulo = arcade.Text("PERSONAJES (C)", px + 16, ALTO_VENTANA - 336,
                                                   arcade.color.GOLD, 11, bold=True)
        self.txt_personajes        = arcade.Text("", px + 16, ALTO_VENTANA - 358,
                                                   (200, 200, 200), 11, multiline=True, width=pw - 32)

        self.txt_recursos_titulo = arcade.Text("RECOLECCION", px + 16, ALTO_VENTANA - 440,
                                                 arcade.color.GOLD, 11, bold=True)
        self.txt_comida = arcade.Text("Comida: 0/0", px + 16, ALTO_VENTANA - 460,
                                       (200, 200, 200), 11)
        self.txt_sillas = arcade.Text("Sillas de ruedas: 0/0 celdas OK", px + 16, ALTO_VENTANA - 478,
                                       (200, 200, 200), 11)

        self.txt_controles_titulo = arcade.Text("CONTROLES", px + 16, ALTO_VENTANA - 510,
                                                  arcade.color.GOLD, 11, bold=True)
        controles_texto = (
            "WASD: mover\nC: cambiar personaje\nZ: deshacer\nR: reiniciar\nESC: menu"
            if self.controles == "wasd" else
            "Flechas: mover\nC: cambiar personaje\nZ: deshacer\nR: reiniciar\nESC: menu"
        )
        self.txt_controles = arcade.Text(controles_texto, px + 16, ALTO_VENTANA - 534,
                                          (200, 200, 200), 10, multiline=True, width=pw - 32)

        self.txt_victoria = arcade.Text("MISION CUMPLIDA", ANCHO_JUEGO // 2, ALTO_VENTANA // 2 + 50,
                                         arcade.color.GOLD, 30, anchor_x="center", anchor_y="center", bold=True)
        self.txt_victoria_sub = arcade.Text("R: jugar de nuevo   ESC: volver al menu",
                                             ANCHO_JUEGO // 2, ALTO_VENTANA // 2 - 40,
                                             (200, 200, 200), 14, anchor_x="center", anchor_y="center")

        self.txt_perdido = arcade.Text("SIN PASOS", ANCHO_JUEGO // 2, ALTO_VENTANA // 2 + 30,
                                        arcade.color.RED, 32, anchor_x="center", anchor_y="center", bold=True)
        self.txt_perdido_sub = arcade.Text("Los 4 personajes se quedaron sin movimientos",
                                            ANCHO_JUEGO // 2, ALTO_VENTANA // 2 - 10,
                                            (200, 200, 200), 13, anchor_x="center", anchor_y="center")
        self.txt_perdido_sub2 = arcade.Text("R: reiniciar   ESC: volver al menu",
                                             ANCHO_JUEGO // 2, ALTO_VENTANA // 2 - 40,
                                             (150, 150, 150), 12, anchor_x="center", anchor_y="center")

    def _actualizar_texto_personajes(self):
        lineas = []
        for i, p in enumerate(PERSONAJES_FAMILIA):
            marca      = "» " if i == self.personaje_activo else "  "
            restantes  = self.pasos_restantes[p["id"]]
            lineas.append(f"{marca}{p['nombre']}: {restantes}/{MAX_PASOS_PERSONAJE}")
        self.txt_personajes.value = "\n".join(lineas)

    def _actualizar_texto_recursos(self):
        total      = len(COMIDA_FIJA)
        recolectada = total - len(self.comida_pendiente)
        self.txt_comida.value = f"Comida: {recolectada}/{total}"

        completas = sum(1 for info in self.sillas.values() if info["recolectadas"] == info["requeridas"])
        self.txt_sillas.value = f"Sillas de ruedas: {completas}/{len(self.sillas)} celdas OK"

    # ── Detección de teclas según esquema de controles ─────────────────────────
    def _tecla_arriba(self, symbol):
        return symbol == (arcade.key.W if self.controles == "wasd" else arcade.key.UP)

    def _tecla_abajo(self, symbol):
        return symbol == (arcade.key.S if self.controles == "wasd" else arcade.key.DOWN)

    def _tecla_izquierda(self, symbol):
        return symbol == (arcade.key.A if self.controles == "wasd" else arcade.key.LEFT)

    def _tecla_derecha(self, symbol):
        return symbol == (arcade.key.D if self.controles == "wasd" else arcade.key.RIGHT)

    # ── Eventos de teclado ──────────────────────────────────────────────────
    def on_key_press(self, symbol, modifiers):
        if self.estado == "ingresando_nombre":
            if symbol == arcade.key.ENTER:
                self._confirmar_nombre()
            elif symbol == arcade.key.BACKSPACE:
                self.nombre_input = self.nombre_input[:-1]
            return

        if self.estado in ("victoria", "perdido"):
            if symbol == arcade.key.R:
                self.setup()
            elif symbol == arcade.key.ESCAPE:
                self._volver_al_menu()
            return

        # self.estado == "jugando"
        if self._tecla_arriba(symbol):
            self._intentar_mover(0, 1)
        elif self._tecla_abajo(symbol):
            self._intentar_mover(0, -1)
        elif self._tecla_izquierda(symbol):
            self._intentar_mover(-1, 0)
        elif self._tecla_derecha(symbol):
            self._intentar_mover(1, 0)
        elif symbol == arcade.key.C:
            self._cambiar_personaje()
        elif symbol == arcade.key.Z:
            self._deshacer()
        elif symbol == arcade.key.R:
            self.setup()
        elif symbol == arcade.key.ESCAPE:
            self._volver_al_menu()

    def on_key_release(self, symbol, modifiers):
        if symbol in (arcade.key.UP, arcade.key.DOWN, arcade.key.LEFT, arcade.key.RIGHT,
                      arcade.key.W, arcade.key.A, arcade.key.S, arcade.key.D):
            self.caminando    = False
            self.frame_actual = 0

    def on_text(self, text):
        """Captura texto imprimible mientras se ingresa el nombre al ganar
        (consigna 4 de Ronda 2). Se usa on_text en vez de on_key_press
        porque es el callback pensado para entrada de texto en Arcade."""
        if self.estado == "ingresando_nombre" and text.isprintable() and len(self.nombre_input) < 20:
            self.nombre_input += text

    def _volver_al_menu(self):
        if hasattr(self, "musica_player") and self.musica_player:
            arcade.stop_sound(self.musica_player)
            self.musica_player = None
        from menu import Menu
        self.window.show_view(Menu())

    # ── Personajes ────────────────────────────────────────────────────────────
    def _siguiente_personaje_disponible(self, desde):
        """Busca, ciclando desde el índice siguiente a `desde`, el primer
        personaje con pasos disponibles. Devuelve `desde` si es el único
        que todavía tiene, o None si ninguno tiene pasos."""
        n = len(PERSONAJES_FAMILIA)
        for offset in range(1, n + 1):
            i = (desde + offset) % n
            if self.pasos_restantes[PERSONAJES_FAMILIA[i]["id"]] > 0:
                return i
        return None

    def _cambiar_personaje(self):
        """Tecla C: cambia manualmente al siguiente personaje con pasos
        disponibles. No hace nada (más allá del sonido) si nadie más tiene
        pasos para ceder el turno."""
        siguiente = self._siguiente_personaje_disponible(self.personaje_activo)
        if siguiente is None or siguiente == self.personaje_activo:
            arcade.play_sound(self.snd_no_mover)
            return
        self._guardar_snapshot()
        self.personaje_activo = siguiente
        self._actualizar_texto_personajes()

    def _verificar_personaje_agotado(self):
        """Se llama después de cada movimiento: si el personaje activo se
        quedó sin pasos, cambia solo al siguiente disponible. Si ninguno
        de los 4 tiene pasos y todavía no se ganó, el nivel se pierde."""
        personaje_id = PERSONAJES_FAMILIA[self.personaje_activo]["id"]
        if self.pasos_restantes[personaje_id] > 0:
            return

        siguiente = self._siguiente_personaje_disponible(self.personaje_activo)
        if siguiente is None or siguiente == self.personaje_activo:
            self.estado = "perdido"
            if hasattr(self, "musica_player") and self.musica_player:
                arcade.stop_sound(self.musica_player)
                self.musica_player = None
        else:
            self.personaje_activo = siguiente
        self._actualizar_texto_personajes()

    # ── Deshacer (Z) ──────────────────────────────────────────────────────────
    def _guardar_snapshot(self):
        """Copia el estado mutable relevante antes de una acción (mover o
        cambiar de personaje). Se apila en self.historial para poder
        restaurarlo con Z."""
        self.historial.append({
            "col": self.col, "fila": self.fila,
            "sendero":     set(self.sendero),
            "direcciones": dict(self.direcciones),
            "personaje_activo": self.personaje_activo,
            "pasos_restantes":  dict(self.pasos_restantes),
            "pasos": self.pasos,
            "comida_pendiente": set(self.comida_pendiente),
            "sillas": {pos: dict(info) for pos, info in self.sillas.items()},
        })

    def _restaurar_snapshot(self, snap):
        """Restaura un snapshot ya sacado de self.historial. No hace el
        pop ni valida que self.historial no esté vacío -eso lo resuelve
        quien llama- para poder reusarse tanto desde _deshacer (Z) como
        desde el gate de victoria en el portal (ver _intentar_mover)."""
        self.col               = snap["col"]
        self.fila               = snap["fila"]
        self.sendero            = snap["sendero"]
        self.direcciones        = snap["direcciones"]
        self.personaje_activo   = snap["personaje_activo"]
        self.pasos_restantes    = snap["pasos_restantes"]
        self.pasos               = snap["pasos"]
        self.comida_pendiente   = snap["comida_pendiente"]
        self.sillas              = snap["sillas"]

        self._reconstruir_sendero_sprites()
        self.px_x, self.px_y = self._celda_a_px(self.col, self.fila)
        self.txt_pasos.value = str(self.pasos)
        self._actualizar_texto_personajes()
        self._actualizar_texto_recursos()

    def _deshacer(self):
        """Tecla Z: deshace el último movimiento o cambio de personaje."""
        if not self.historial:
            arcade.play_sound(self.snd_no_mover)
            return
        self._restaurar_snapshot(self.historial.pop())

    # ── Lógica de juego ───────────────────────────────────────────────────────
    def _procesar_sillas_adyacentes(self, col, fila):
        """Cada vez que UAIBOT llega a una celda nueva, cuenta como
        "pasada" cada vecino ortogonal que sea una celda de sillas de
        ruedas. Como el sendero es compartido y no se puede repisar una
        celda, cada vecino solo puede generar una pasada en total -no
        hace falta llevar un registro aparte de "lados ya contados"."""
        for dc, df in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            vecino = (col + dc, fila + df)
            if vecino in self.sillas:
                info = self.sillas[vecino]
                info["recolectadas"] += 1
                if info["recolectadas"] > info["requeridas"]:
                    info["excedido"] = True

    def _hay_sillas_incompletas(self):
        return any(info["recolectadas"] != info["requeridas"] for info in self.sillas.values())

    def _intentar_mover(self, dc, df):
        """Intenta mover al personaje activo en la dirección (dc, df).
        El sendero, los pasos totales y las paredes son compartidos por
        los 4 personajes; solo el cupo de pasos restantes es individual."""
        if self.estado != "jugando":
            return

        nc, nf = self.col + dc, self.fila + df

        if not (0 <= nc < COLUMNAS and 0 <= nf < FILAS):
            arcade.play_sound(self.snd_no_mover)
            return
        if (nc, nf) in self.paredes:
            arcade.play_sound(self.snd_no_mover)
            return
        if (nc, nf) in self.sendero:
            arcade.play_sound(self.snd_no_mover)
            return

        self._guardar_snapshot()

        self.col, self.fila = nc, nf
        self.direcciones[(nc, nf)] = (dc, df)
        self.sendero.add((nc, nf))
        self._agregar_huella(nc, nf)
        self.pasos += 1
        self.txt_pasos.value = str(self.pasos)
        self.caminando = True
        arcade.play_sound(self.snd_mover)

        personaje_id = PERSONAJES_FAMILIA[self.personaje_activo]["id"]
        self.pasos_restantes[personaje_id] -= 1
        self._actualizar_texto_personajes()

        if (nc, nf) in self.comida_pendiente:
            self.comida_pendiente.discard((nc, nf))

        self._procesar_sillas_adyacentes(nc, nf)
        self._actualizar_texto_recursos()

        if (self.col, self.fila) == POS_MERENDERO:
            if self.comida_pendiente or self._hay_sillas_incompletas():
                # Todavía falta recolectar algo: se revierte el
                # movimiento entero (reusa el mismo mecanismo del
                # deshacer, así queda perfectamente consistente incluida
                # la comida/silla que se hubiera contado en esta celda).
                arcade.play_sound(self.snd_no_mover)
                self._restaurar_snapshot(self.historial.pop())
                return
            self._ganar_nivel()
            return

        self._verificar_personaje_agotado()

    def _ganar_nivel(self):
        self.estado       = "ingresando_nombre"
        self.nombre_input = ""
        arcade.play_sound(self.snd_victoria)
        if hasattr(self, "musica_player") and self.musica_player:
            arcade.stop_sound(self.musica_player)
            self.musica_player = None

    def _confirmar_nombre(self):
        guardado.registrar_puntaje_tutorial(self.nombre_input, self.tiempo_transcurrido)
        self.estado = "victoria"
        for _ in range(80):
            self.particulas.append(Particula())

    # ── Actualización ─────────────────────────────────────────────────────────
    def on_update(self, delta_time):
        self.timer_frame += 1
        if self.timer_frame >= self.velocidad_frame:
            self.timer_frame  = 0
            self.frame_actual = (self.frame_actual + 1) % TOTAL_FRAMES

        dest_x, dest_y = self._celda_a_px(self.col, self.fila)
        dx = dest_x - self.px_x
        dy = dest_y - self.px_y
        distancia = (dx**2 + dy**2) ** 0.5
        if distancia > self.velocidad_movimiento:
            self.px_x += dx / distancia * self.velocidad_movimiento
            self.px_y += dy / distancia * self.velocidad_movimiento
            self.moviendose = True
        else:
            self.px_x, self.px_y = dest_x, dest_y
            self.moviendose = False

        if self.estado == "jugando":
            self.tiempo_transcurrido += delta_time
        self.txt_cronometro.value = f"{self.tiempo_transcurrido:.1f}s"

        if self.estado == "victoria":
            for p in self.particulas:
                p.actualizar()
            self.particulas = [p for p in self.particulas if p.y > 0]

        if self.mostrar_anuncio:
            self.timer_anuncio += 1
            if self.timer_anuncio >= 120:
                self.mostrar_anuncio = False

    # ── Dibujo ────────────────────────────────────────────────────────────────
    def on_draw(self):
        self.window.clear((20, 28, 36))

        self.fondo_sprites.draw()
        self.sendero_sprites.draw()
        self.paredes_sprites.draw()
        self._dibujar_comida()
        self._dibujar_sillas()
        self._dibujar_portal()
        self._dibujar_personaje()

        self._dibujar_panel()

        if self.mostrar_anuncio:
            self._dibujar_anuncio_nivel()
        if self.estado == "ingresando_nombre":
            self._dibujar_overlay_nombre()
        elif self.estado == "victoria":
            self._dibujar_overlay_victoria()
        elif self.estado == "perdido":
            self._dibujar_overlay_perdido()

    def _celda_a_px(self, col, fila):
        x = col * TAM_CELDA + TAM_CELDA // 2
        y = fila * TAM_CELDA + TAM_CELDA // 2
        return x, y

    def _dibujar_hexagono(self, cx, cy, radio, color):
        puntos = [
            (cx + radio * math.cos(math.radians(60 * i - 30)),
             cy + radio * math.sin(math.radians(60 * i - 30)))
            for i in range(6)
        ]
        arcade.draw_polygon_filled(puntos, color)
        arcade.draw_polygon_outline(puntos, (0, 0, 0), 2)

    def _dibujar_comida(self):
        """La consigna pide representar la comida como un hexágono: se
        dibuja como polígono directo (sin sprite nuevo) para no depender
        de que el diseñador entregue arte a tiempo."""
        radio = TAM_CELDA * 0.32
        for (col, fila) in self.comida_pendiente:
            x, y = self._celda_a_px(col, fila)
            self._dibujar_hexagono(x, y, radio, COLOR_COMIDA)

    def _dibujar_sillas(self):
        """Ídem para sillas de ruedas, pero como triángulo, con el
        contador de pasadas recolectadas/requeridas sobre la celda."""
        radio = TAM_CELDA * 0.32
        for (col, fila), info in self.sillas.items():
            x, y  = self._celda_a_px(col, fila)
            color = COLOR_SILLA_EXCEDIDA if info["excedido"] else COLOR_SILLA
            puntos = [(x, y + radio), (x - radio, y - radio), (x + radio, y - radio)]
            arcade.draw_polygon_filled(puntos, color)
            arcade.draw_polygon_outline(puntos, (0, 0, 0), 2)
            arcade.Text(f"{info['recolectadas']}/{info['requeridas']}", x, y - radio - 12,
                        arcade.color.WHITE, 9, anchor_x="center", bold=True).draw()

    def _dibujar_portal(self):
        """La consigna obligatoria de Ronda 1 pide una imagen fija en la
        celda del merendero -acá siempre se muestra, porque Tutorial no
        tiene "niveles siguientes" donde todavía no corresponda."""
        col, fila = POS_MERENDERO
        x, y = self._celda_a_px(col, fila)
        arcade.draw_lrbt_rectangle_filled(
            col * TAM_CELDA + 1, col * TAM_CELDA + TAM_CELDA - 1,
            fila * TAM_CELDA + 1, fila * TAM_CELDA + TAM_CELDA - 1,
            (192, 57, 43, 180)
        )
        arcade.draw_texture_rect(self.img_merendero, arcade.XYWH(x, y, TAM_CELDA, TAM_CELDA))

    def _dibujar_personaje(self):
        frames    = self.frames_walk if self.moviendose else self.frames_idle
        personaje = PERSONAJES_FAMILIA[self.personaje_activo]
        self.sprite_personaje.texture  = frames[self.frame_actual]
        self.sprite_personaje.color    = personaje["color"]
        self.sprite_personaje.center_x = self.px_x
        self.sprite_personaje.center_y = self.px_y
        self.sprites_personaje.draw()

    def _dibujar_anuncio_nivel(self):
        alpha = int(255 * min(1.0, (120 - self.timer_anuncio) / 30))
        arcade.draw_lrbt_rectangle_filled(0, ANCHO_JUEGO, 0, ALTO_VENTANA, (0, 0, 0, 150))
        arcade.Text("TUTORIAL", ANCHO_JUEGO // 2, ALTO_VENTANA // 2,
                    (*arcade.color.GOLD[:3], alpha), 42,
                    anchor_x="center", anchor_y="center", bold=True).draw()

    def _dibujar_panel(self):
        arcade.draw_lrbt_rectangle_filled(ANCHO_JUEGO, ANCHO_VENTANA, 0, ALTO_VENTANA, (30, 39, 46))
        arcade.draw_line(ANCHO_JUEGO, 0, ANCHO_JUEGO, ALTO_VENTANA, (52, 152, 219), 2)
        self.txt_titulo.draw()
        self.txt_ofirca.draw()
        self.txt_modo.draw()
        self.txt_mision_titulo.draw()
        self.txt_mision.draw()
        self.txt_pasos_titulo.draw()
        self.txt_pasos.draw()
        self.txt_cronometro_titulo.draw()
        self.txt_cronometro.draw()
        self.txt_personajes_titulo.draw()
        self.txt_personajes.draw()
        self.txt_recursos_titulo.draw()
        self.txt_comida.draw()
        self.txt_sillas.draw()
        self.txt_controles_titulo.draw()
        self.txt_controles.draw()

    def _dibujar_overlay_nombre(self):
        arcade.draw_lrbt_rectangle_filled(0, ANCHO_JUEGO, 0, ALTO_VENTANA, (0, 0, 0, 200))
        cx, cy = ANCHO_JUEGO // 2, ALTO_VENTANA // 2
        arcade.Text("¡LLEGASTE AL MERENDERO!", cx, cy + 70, arcade.color.GOLD, 26,
                    anchor_x="center", anchor_y="center", bold=True).draw()
        arcade.Text(f"Tiempo: {self.tiempo_transcurrido:.1f}s", cx, cy + 30,
                    (200, 200, 200), 14, anchor_x="center", anchor_y="center").draw()
        arcade.Text("Ingresa tu nombre y presiona ENTER:", cx, cy - 10,
                    (200, 200, 200), 14, anchor_x="center", anchor_y="center").draw()
        arcade.Text(self.nombre_input + "_", cx, cy - 45,
                    arcade.color.WHITE, 22, anchor_x="center", anchor_y="center", bold=True).draw()

    def _dibujar_overlay_victoria(self):
        arcade.draw_lrbt_rectangle_filled(0, ANCHO_JUEGO, 0, ALTO_VENTANA, (0, 0, 0, 180))
        for p in self.particulas:
            p.dibujar()
        self.txt_victoria.draw()
        arcade.Text(f"Tiempo: {self.tiempo_transcurrido:.1f}s", ANCHO_JUEGO // 2, ALTO_VENTANA // 2,
                    arcade.color.LIME_GREEN, 16, anchor_x="center", anchor_y="center", bold=True).draw()
        self.txt_victoria_sub.draw()

    def _dibujar_overlay_perdido(self):
        arcade.draw_lrbt_rectangle_filled(0, ANCHO_JUEGO, 0, ALTO_VENTANA, (0, 0, 0, 180))
        self.txt_perdido.draw()
        self.txt_perdido_sub.draw()
        self.txt_perdido_sub2.draw()
