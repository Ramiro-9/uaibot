# tutorial.py
# Modo Tutorial: nivel único y fijo que reúne, en un solo lugar, las 7
# consignas obligatorias de Ronda 1 (contador de pasos, imagen en el
# merendero, sonido al moverse, sendero no repetible, 4 paredes marrones,
# reinicio con R, animación al ganar) y las 6 mecánicas nuevas de Ronda 2
# (cronómetro, cambio de personaje con cupo de pasos, comida obligatoria,
# sillas de ruedas por adyacencia, nombre+tiempo al ganar, deshacer con Z).
# Ronda final: alto contraste (A), ranking por tiempo y romper paredes
# (X + flecha, dos movimientos), también reversible con Z.
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
import json
from pathlib import Path

import arcade
from recursos_audio import cargar_sonido

import guardado
import panel as pnl
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

FRAME_WIDTH  = 128
FRAME_HEIGHT = 128

COLOR_PARED           = (101, 67, 33)
COLOR_SENDERO         = (30, 100, 160)
COLOR_FONDO_CLARO     = (44, 62, 80)
COLOR_FONDO_OSCURO    = (39, 55, 70)
COLOR_COMIDA          = (241, 196, 15)
COLOR_SILLA           = (52, 152, 219)
COLOR_SILLA_COMPLETA  = (46, 204, 113)   # ya tiene las pasadas justas
COLOR_SILLA_EXCEDIDA  = (192, 57, 43)    # se paso de más: nivel perdido
COLOR_LADO_SILLA      = (52, 152, 219, 170)   # marca de "pasá por acá"

# Paleta exclusiva de la ronda final, sin transparencias ni texturas de arte.
HC_NEGRO = (0, 0, 0)
HC_BLANCO = (255, 255, 255)
HC_AMARILLO = (255, 255, 0)
ARCHIVO_REPLAY = Path(__file__).with_name("replay_tutorial.txt")
INTERVALO_REPLAY = 0.5

MISION_TUTORIAL = (
    "Junta la comida (hexagonos) pisandola. Las sillas (triangulos) "
    "se recogen pasando por su lado las veces justas.")

# Son objetivos de aprendizaje, no condiciones adicionales para ganar.
# Se reconocen en cualquier orden, únicamente tras acciones exitosas.
LECCIONES_GUIA = (
    ("mover", "Usá las flechas para avanzar una celda. No podés volver a pisar el sendero."),
    ("comida", "Pisá un hexágono para recoger comida. Juntá los cuatro antes de ir al merendero."),
    ("silla", "Pasá junto a un triángulo para sumar una pasada. Su contador debe quedar exacto: por ejemplo, 2/2."),
    ("personaje", "Presioná C para cambiar de robot. Cada uno tiene 8 movimientos; comparten el sendero."),
    ("pared", "Junto a una pared, usá X y una flecha. Cuesta 2 movimientos del robot activo. X cancela."),
    ("deshacer", "Presioná Z para deshacer la última acción y recuperar sus movimientos."),
    ("contraste", "Presioná A para probar el alto contraste. A también vuelve a la vista normal."),
)


class Tutorial(arcade.View):
    """Nivel de referencia para las consignas de las tres rondas de OFIRCA.
    Hereda de arcade.View para integrarse al
    sistema de vistas (menu -> tutorial -> menu)."""

    def __init__(self, controles="flechas", acciones_replay=None, origen_replay=None):
        """Crea la vista del Tutorial. El nivel se arma en setup()."""
        super().__init__()
        self._en_replay = acciones_replay is not None
        self._acciones_replay = acciones_replay or []
        self._origen_replay = origen_replay
        self._indice_replay = 0
        self._reloj_replay = 0.0
        self._registro_disponible = False
        # A está reservada por la consigna. La preferencia global de WASD
        # sigue vigente en los otros modos; Tutorial siempre usa flechas.
        self.controles = "flechas"
        self.alto_contraste = False
        self.guia_activa = True
        self._cargar_assets()

    # ── Setup / Reinicio ─────────────────────────────────────────────────────
    def setup(self):
        """Inicializa o reinicia el estado completo del nivel. Se llama al
        entrar a Tutorial y cada vez que se presiona R."""
        if hasattr(self, "musica_player") and self.musica_player:
            arcade.stop_sound(self.musica_player)
            self.musica_player = None
        self.musica_player = None
        if not self._en_replay:
            self.musica_player = arcade.play_sound(
                self.musica, volume=guardado.cargar().get("volumen_musica_nivel", 0.3), loop=True)

        self.paredes         = set(PAREDES_FIJAS)
        self.comida_pendiente = set(COMIDA_FIJA)
        self.sillas = {
            pos: {"requeridas": req, "recolectadas": 0, "excedido": False}
            for pos, req in SILLAS_FIJAS.items()
        }
        # El contador de cada silla, creado una sola vez. Crear un
        # arcade.Text cuesta unos 8 ms —arma el layout del texto de cero—,
        # así que hacerlo en el dibujo era casi todo el costo del cuadro en
        # este modo: dos sillas se llevaban 15 ms de los 24 que tardaba.
        # Acá solo se les cambia el valor cuando cambia el conteo.
        self.txt_sillas_celda = {
            (col, fila): arcade.Text(
                "", *self._celda_a_px(col, fila), arcade.color.WHITE, 9,
                anchor_x="center", anchor_y="center", bold=True)
            for (col, fila) in self.sillas
        }

        self.col, self.fila = POS_INICIO
        self.sendero      = {POS_INICIO}   # compartido entre los 4 personajes
        self.direcciones  = {}
        self.historial    = []             # pila de snapshots para deshacer (Z)
        self.seleccionando_pared = False
        self.mensaje_accion = ""
        self.tiempo_mensaje = 0.0
        self.puesto_ranking = None
        self.total_ranking = 0
        self.error_guardado = ""
        self.lecciones_aprendidas = set()
        self.titulo_mision = "MISION"

        self.personaje_activo = 0
        self.pasos_restantes  = {p["id"]: MAX_PASOS_PERSONAJE for p in PERSONAJES_FAMILIA}
        self.pasos            = 0
        # El arte está de perfil hacia la derecha: True es lo natural.
        self.mirando_derecha  = True

        self.tiempo_transcurrido = 0.0
        self.estado       = "jugando"   # jugando | ingresando_nombre | victoria | perdido
        self.nombre_input = ""
        self.particulas   = []

        self.caminando      = False
        self.frame_actual   = 0
        self.timer_frame    = 0
        self.velocidad_frame = 8

        self.mostrar_anuncio = not self.guia_activa
        self.timer_anuncio   = 0

        self._construir_capas_estaticas()
        self._crear_textos()
        self._actualizar_texto_personajes()
        self._actualizar_texto_recursos()
        # Después de llenar los textos: acomodar salta las secciones cuyo
        # cuerpo está vacío, y la de personajes se llena recién acá.
        self._acomodar_panel()
        self._aplicar_paleta_textos()

        self.px_x, self.px_y      = self._celda_a_px(*POS_INICIO)
        self.moviendose           = False
        self.velocidad_movimiento = 10
        self._actualizar_guia()
        if self._en_replay:
            self.mostrar_anuncio = False
            self.txt_modo.value = "REPLAY 0/" + str(len(self._acciones_replay))
            self.txt_replay.value = "P: VOLVER"
        else:
            self._iniciar_registro_replay()

    # ── Consigna sorpresa: registro en TXT y reproducción desde el archivo ──
    def _iniciar_registro_replay(self):
        """R inicia una partida nueva y, por lo tanto, un registro nuevo."""
        try:
            with ARCHIVO_REPLAY.open("w", encoding="utf-8") as archivo:
                archivo.write(json.dumps({"formato": "UAIBOT_REPLAY", "version": 1}) + "\n")
            self._registro_disponible = True
        except OSError:
            self._registro_disponible = False
            self._avisar_accion("No se pudo crear replay_tutorial.txt · Revisá permisos de escritura")

    def _registrar_accion_replay(self, accion, dc=0, df=0):
        """Registra acciones aceptadas, incluidos los Z; no borra lo deshecho."""
        if self._en_replay or not self._registro_disponible:
            return
        registro = {"accion": accion, "dc": dc, "df": df,
                    "tiempo": round(self.tiempo_transcurrido, 3)}
        try:
            with ARCHIVO_REPLAY.open("a", encoding="utf-8") as archivo:
                archivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
        except OSError:
            # No reproducir un registro incompleto como si fuera la partida.
            self._registro_disponible = False
            self._avisar_accion("No se pudo guardar una acción · Replay no disponible para esta partida")

    def _leer_replay(self):
        """Lee y valida TODO el TXT antes de cambiar de vista; nunca usa eval."""
        with ARCHIVO_REPLAY.open(encoding="utf-8") as archivo:
            cabecera = json.loads(archivo.readline())
            if cabecera != {"formato": "UAIBOT_REPLAY", "version": 1}:
                raise ValueError("Formato de replay no reconocido")
            acciones = []
            for linea in archivo:
                dato = json.loads(linea)
                if not isinstance(dato, dict):
                    raise ValueError("Acción inválida")
                accion, dc, df = dato.get("accion"), dato.get("dc"), dato.get("df")
                tiempo = dato.get("tiempo")
                if accion not in ("MOVER", "CAMBIAR", "ROMPER", "DESHACER"):
                    raise ValueError("Acción desconocida")
                if type(dc) is not int or type(df) is not int:
                    raise ValueError("Dirección inválida")
                if accion in ("MOVER", "ROMPER") and (dc, df) not in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    raise ValueError("Dirección inválida")
                if not isinstance(tiempo, (int, float)) or not math.isfinite(tiempo) or tiempo < 0:
                    raise ValueError("Tiempo inválido")
                acciones.append(dato)
        return acciones

    def _iniciar_replay(self):
        if not self._registro_disponible:
            self._avisar_accion("Replay no disponible: no se pudo guardar el registro completo")
            return
        try:
            acciones = self._leer_replay()
        except (OSError, ValueError, UnicodeError):
            self._avisar_accion("No se pudo leer replay_tutorial.txt o su contenido es inválido")
            return
        if not acciones:
            self._avisar_accion("Todavía no hay acciones para reproducir")
            return
        # Una vista independiente deja intactos el historial, nombre, tiempo
        # y puntaje reales. setup() del replay NO toca el TXT ni la música.
        repeticion = Tutorial(acciones_replay=acciones, origen_replay=self)
        repeticion.alto_contraste = self.alto_contraste
        repeticion.guia_activa = False
        repeticion.setup()
        self.window.show_view(repeticion)

    def _salir_replay(self):
        self.window.show_view(self._origen_replay)

    def _actualizar_replay(self, delta_time):
        if self._indice_replay >= len(self._acciones_replay):
            return
        self._reloj_replay += delta_time
        if self._reloj_replay + 1e-9 < INTERVALO_REPLAY:
            return
        # Una acción por intervalo visible. Tras un cuadro lento no ejecutar
        # varias juntas, porque se perdería la demostración del deshacer.
        self._reloj_replay = max(0.0, self._reloj_replay - INTERVALO_REPLAY) % INTERVALO_REPLAY
        dato = self._acciones_replay[self._indice_replay]
        self.tiempo_transcurrido = dato["tiempo"]
        accion = dato["accion"]
        if accion == "MOVER":
            self._intentar_mover(dato["dc"], dato["df"])
        elif accion == "ROMPER":
            self._intentar_romper_pared(dato["dc"], dato["df"])
        elif accion == "CAMBIAR":
            self._cambiar_personaje()
        elif accion == "DESHACER":
            self._deshacer()
        self._indice_replay += 1
        self.txt_modo.value = f"REPLAY {self._indice_replay}/{len(self._acciones_replay)}"
        self._avisar_accion(f"REPLAY · {accion} · P o ESC: volver a la partida")
        if self._indice_replay == len(self._acciones_replay):
            self.txt_modo.value = "REPLAY COMPLETO"
            self._avisar_accion("Replay completo · P o ESC: volver a la partida")

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT and ANCHO_JUEGO + 16 <= x <= ANCHO_VENTANA - 16 and 4 <= y <= 26:
            if self._en_replay:
                self._salir_replay()
            else:
                self._iniciar_replay()

    # ── Construcción de capas estáticas (mismo patrón de SpriteList que
    # juego.py usa para no dibujar celda por celda en cada frame) ─────────────
    def _crear_sprite_celda(self, path, col, fila, color_fallback, forzar_color=False):
        """Un sprite de fondo ubicado en una celda de la grilla."""
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

        self._reconstruir_paredes_sprites()
        self.sendero_sprites = arcade.SpriteList()

    def _reconstruir_paredes_sprites(self):
        """Actualiza la representación de paredes después de romper/deshacer."""
        self.paredes_sprites = arcade.SpriteList()
        for (col, fila) in self.paredes:
            self.paredes_sprites.append(
                self._crear_sprite_celda(SPRITE_PARED, col, fila, COLOR_PARED, forzar_color=True)
            )

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
        """Carga texturas y sonidos una sola vez por partida."""
        if self._en_replay and self._origen_replay is not None:
            origen = self._origen_replay
            for nombre in ("familia", "img_merendero", "snd_mover", "snd_no_mover", "snd_victoria", "musica"):
                setattr(self, nombre, getattr(origen, nombre))
            self.sprite_personaje = arcade.Sprite(self.familia[PERSONAJES_FAMILIA[0]["id"]]["idle"][0])
            self.sprite_personaje.width = self.sprite_personaje.height = TAM_CELDA
            self.sprites_personaje = arcade.SpriteList()
            self.sprites_personaje.append(self.sprite_personaje)
            return
        # Animaciones de los cuatro personajes: cada uno con su arte propio si
        # lo tiene, o las hojas de UAIBOT teñidas si todavía no. La cantidad de
        # frames sale del ancho de cada hoja, así conviven hojas de distinto
        # largo sin tocar nada acá.
        self.familia = spr.cargar_familia(PERSONAJES_FAMILIA, FRAME_WIDTH, FRAME_HEIGHT)

        # Sprite persistente del personaje activo: se reusa entre frames
        # (textura/tinte/posición se actualizan en _dibujar_personaje) en
        # vez de crear un arcade.Sprite nuevo en cada on_draw. En Arcade 3.x
        # un Sprite suelto no tiene .draw() -hay que dibujarlo dentro de una
        # SpriteList, aunque sea de un solo elemento- así que se envuelve en
        # self.sprites_personaje.
        self.sprite_personaje = arcade.Sprite(
            self.familia[PERSONAJES_FAMILIA[0]["id"]]["idle"][0])
        self.sprite_personaje.width  = TAM_CELDA
        self.sprite_personaje.height = TAM_CELDA
        self.sprites_personaje = arcade.SpriteList()
        self.sprites_personaje.append(self.sprite_personaje)

        self.img_merendero = arcade.load_texture("assets/imagenes/merendero.png")

        self.snd_mover    = cargar_sonido("assets/audio/Moverse.wav")
        self.snd_no_mover = cargar_sonido("assets/audio/NoMoverse.wav")
        self.snd_victoria = cargar_sonido("assets/audio/CompletedLevel.wav")
        self.musica       = cargar_sonido("assets/audio/GameLevelMusic.wav")

    # ── Textos del panel ─────────────────────────────────────────────────────
    def _crear_textos(self):
        """Arma los textos del panel lateral y de los overlays."""
        px = ANCHO_JUEGO
        pw = PANEL_ANCHO
        cx = px + pw // 2

        self.txt_titulo = arcade.Text("UAIBOT", cx, ALTO_VENTANA - 35,
                                       arcade.color.GOLD, 26, anchor_x="center", bold=True)
        self.txt_ofirca = arcade.Text("OFIRCA 2026", cx, ALTO_VENTANA - 58,
                                       (52, 152, 219), 12, anchor_x="center")
        self.txt_modo   = arcade.Text("TUTORIAL", cx, ALTO_VENTANA - 85,
                                       arcade.color.WHITE, 13, anchor_x="center", bold=True)

        # ── Textos del panel ─────────────────────────────────────────
        # Sin posición vertical: la reparte panel.acomodar() según el orden
        # de _secciones_panel. Es el mismo armador que usa Juego, aunque
        # Tutorial no herede de él.
        x = px + pnl.MARGEN_X
        ancho_texto = pw - pnl.MARGEN_X * 2

        # El texto es explícito con las sillas a propósito: "pasa por las
        # sillas" se entendía como "pisalas", que es justo lo que NO hay
        # que hacer.
        self.txt_mision = pnl.crear_texto(
            MISION_TUTORIAL,
            x, 9, (200, 200, 200), ancho=ancho_texto)

        self.txt_pasos      = pnl.crear_texto("0", x, 18, (200, 200, 200), bold=True)
        self.txt_cronometro = pnl.crear_texto("0.0s", x, 16, (200, 200, 200), bold=True)
        self.txt_personajes = pnl.crear_texto("", x, 10, (200, 200, 200),
                                              ancho=ancho_texto)
        self.txt_comida = pnl.crear_texto("Comida: 0/0", x, 11, (200, 200, 200))
        self.txt_sillas = pnl.crear_texto("Sillas de ruedas: 0/0 celdas OK",
                                          x, 11, (200, 200, 200))

        self.txt_controles = pnl.crear_texto(
            "Flechas: mover   C: personaje\nX + flecha: romper (2 pasos)\n"
            "Z: deshacer   R: reiniciar\nESC: menu   G: guía\nA: Alto contraste — "
            + ("ACTIVADO" if self.alto_contraste else "DESACTIVADO"),
            x, 10, (200, 200, 200), ancho=ancho_texto)

        self.txt_victoria = arcade.Text("MISION CUMPLIDA", ANCHO_JUEGO // 2, ALTO_VENTANA // 2 + 50,
                                         arcade.color.GOLD, 30, anchor_x="center", anchor_y="center", bold=True)
        self.txt_victoria_sub = arcade.Text("R: jugar de nuevo   ESC: volver al menu",
                                             ANCHO_JUEGO // 2, ALTO_VENTANA // 2 - 65,
                                             (200, 200, 200), 14, anchor_x="center", anchor_y="center")

        self.txt_perdido = arcade.Text("SIN PASOS", ANCHO_JUEGO // 2, ALTO_VENTANA // 2 + 30,
                                        arcade.color.RED, 32, anchor_x="center", anchor_y="center", bold=True)
        self.txt_perdido_sub = arcade.Text("Los 4 personajes se quedaron sin movimientos",
                                            ANCHO_JUEGO // 2, ALTO_VENTANA // 2 - 10,
                                            (200, 200, 200), 13, anchor_x="center", anchor_y="center")
        self.txt_perdido_sub2 = arcade.Text("Z: deshacer   R: reiniciar   ESC: menu",
                                             ANCHO_JUEGO // 2, ALTO_VENTANA // 2 - 40,
                                             (150, 150, 150), 12, anchor_x="center", anchor_y="center")

        self.txt_ranking = arcade.Text("", ANCHO_JUEGO // 2, ALTO_VENTANA // 2 - 30,
                                      arcade.color.WHITE, 16, anchor_x="center", anchor_y="center")
        self.txt_accion = arcade.Text("", ANCHO_JUEGO // 2, ALTO_VENTANA - 20,
                                     arcade.color.WHITE, 12, anchor_x="center", anchor_y="center")
        self.txt_replay = arcade.Text("P: REPLAY", cx, 15, arcade.color.WHITE, 10,
                                     anchor_x="center", anchor_y="center", bold=True)
        self.txt_robot_celda = arcade.Text("", 0, 0, HC_NEGRO, 7,
                                           anchor_x="center", anchor_y="center", bold=True)
        self.txt_merendero_celda = arcade.Text("MEREN\nDERO", *self._celda_a_px(*POS_MERENDERO),
                                               HC_NEGRO, 8, anchor_x="center", anchor_y="center",
                                               bold=True, multiline=True, width=52, align="center")
        # Guardar la paleta normal una sola vez permite alternar sin perderla.
        self._colores_textos = [(texto, texto.color) for nombre, texto in vars(self).items()
                               if nombre.startswith("txt_") and isinstance(texto, arcade.Text)
                               and nombre not in ("txt_robot_celda", "txt_merendero_celda")]

    def _color(self, normal, contraste=HC_BLANCO):
        return contraste if self.alto_contraste else normal

    def _aplicar_paleta_textos(self):
        for texto, normal in self._colores_textos:
            texto.color = self._color(normal)
        for texto in (self.txt_titulo, self.txt_victoria, self.txt_perdido):
            if self.alto_contraste:
                texto.color = HC_AMARILLO
        for seccion in self.secciones_panel:
            if seccion.txt_titulo:
                seccion.txt_titulo.color = self._color(pnl.COLOR_TITULO, HC_AMARILLO)

    def _alternar_alto_contraste(self):
        self.alto_contraste = not self.alto_contraste
        estado = "ACTIVADO" if self.alto_contraste else "DESACTIVADO"
        self.txt_controles.value = (
            "Flechas: mover   C: personaje\nX + flecha: romper (2 pasos)\n"
            f"Z: deshacer   R: reiniciar\nESC: menu   G: guía\nA: Alto contraste — {estado}")
        self._acomodar_panel()
        self._aplicar_paleta_textos()
        if self.estado == "jugando":
            self._registrar_leccion("contraste")

    # ── Guía opcional por acciones ──────────────────────────────────────────
    def _registrar_leccion(self, accion):
        """Lo aprendido no se deshace con Z; R inicia una nueva práctica.

        También registra acciones con la guía oculta para no pedir de nuevo
        algo que el jugador ya demostró al reactivarla con G.
        """
        if accion not in self.lecciones_aprendidas:
            self.lecciones_aprendidas.add(accion)
            self._actualizar_guia()

    def _actualizar_guia(self):
        """Actualiza textos y layout solo cuando cambia la lección visible."""
        if not self.guia_activa:
            titulo, texto = "MISION · GUIA OCULTA (G)", MISION_TUTORIAL
        else:
            pendientes = [(clave, texto) for clave, texto in LECCIONES_GUIA
                          if clave not in self.lecciones_aprendidas]
            hechas = len(LECCIONES_GUIA) - len(pendientes)
            titulo = f"GUIA · {hechas}/{len(LECCIONES_GUIA)} · G: ocultar"
            texto = pendientes[0][1] if pendientes else (
                "¡Guía completada! Juntá la comida, completá las sillas y llegá al merendero. R reinicia la práctica.")
        if self.titulo_mision != titulo or self.txt_mision.value != texto:
            self.titulo_mision = titulo
            self.txt_mision.value = texto
            self._acomodar_panel()
            self._aplicar_paleta_textos()

    def _alternar_guia(self):
        self.guia_activa = not self.guia_activa
        self.mostrar_anuncio = False
        self._actualizar_guia()

    def _actualizar_texto_personajes(self):
        """Refresca la lista del panel: quién está activo y cuántos pasos le
        quedan a cada uno."""
        lineas = []
        for i, p in enumerate(PERSONAJES_FAMILIA):
            marca      = "» " if i == self.personaje_activo else "  "
            restantes  = self.pasos_restantes[p["id"]]
            lineas.append(f"{marca}{p['nombre']}: {restantes}/{MAX_PASOS_PERSONAJE}")
        self.txt_personajes.value = "\n".join(lineas)
        self.txt_robot_celda.value = PERSONAJES_FAMILIA[self.personaje_activo]["nombre"]
        self.txt_robot_celda.font_size = 7
        while self.txt_robot_celda.content_width > 50 and self.txt_robot_celda.font_size > 5:
            self.txt_robot_celda.font_size -= 0.5

    def _actualizar_texto_recursos(self):
        """Refresca los contadores de comida y de sillas de ruedas."""
        total      = len(COMIDA_FIJA)
        recolectada = total - len(self.comida_pendiente)
        self.txt_comida.value = f"Comida: {recolectada}/{total}"

        completas = sum(1 for info in self.sillas.values() if info["recolectadas"] == info["requeridas"])
        self.txt_sillas.value = f"Sillas de ruedas: {completas}/{len(self.sillas)} celdas OK"

    # ── Flechas: A queda reservada para alto contraste en este modo ────────────
    def _tecla_arriba(self, symbol):
        """Si la tecla apretada es la de subir."""
        return symbol == arcade.key.UP

    def _tecla_abajo(self, symbol):
        """Si la tecla apretada es la de bajar."""
        return symbol == arcade.key.DOWN

    def _tecla_izquierda(self, symbol):
        """Si la tecla apretada es la de ir a la izquierda."""
        return symbol == arcade.key.LEFT

    def _tecla_derecha(self, symbol):
        """Si la tecla apretada es la de ir a la derecha."""
        return symbol == arcade.key.RIGHT

    # ── Eventos de teclado ──────────────────────────────────────────────────
    def on_key_press(self, symbol, modifiers):
        """Reparte cada tecla según el estado del nivel.

        Mientras se juega: mover, cambiar de personaje con C y deshacer
        con Z. Al ganar, el teclado pasa a escribir el nombre."""
        if self._en_replay:
            if symbol in (arcade.key.P, arcade.key.ESCAPE):
                self._salir_replay()
            elif symbol == arcade.key.A:
                self._alternar_alto_contraste()
            return

        if self.estado == "ingresando_nombre":
            if symbol == arcade.key.ENTER:
                self._confirmar_nombre()
            elif symbol == arcade.key.BACKSPACE:
                self.nombre_input = self.nombre_input[:-1]
            return

        if symbol == arcade.key.P:
            self._iniciar_replay()
            return

        if symbol == arcade.key.A:
            self._alternar_alto_contraste()
            return

        if self.estado in ("victoria", "perdido"):
            if symbol == arcade.key.Z and self.estado == "perdido":
                self._deshacer()
            elif symbol == arcade.key.R:
                self.setup()
            elif symbol == arcade.key.ESCAPE:
                self._volver_al_menu()
            return

        # self.estado == "jugando"
        if symbol == arcade.key.G:
            self._alternar_guia()
            return
        if symbol == arcade.key.X:
            self.seleccionando_pared = not self.seleccionando_pared
            self.mostrar_anuncio = False
            self._avisar_accion("Elegí una dirección · Costo: 2 movimientos · X: cancelar"
                               if self.seleccionando_pared else "Selección cancelada")
            return
        if self.seleccionando_pared:
            direcciones = {arcade.key.UP: (0, 1), arcade.key.DOWN: (0, -1),
                           arcade.key.LEFT: (-1, 0), arcade.key.RIGHT: (1, 0)}
            if symbol in direcciones:
                self._intentar_romper_pared(*direcciones[symbol])
                return
            if symbol == arcade.key.ESCAPE:
                self.seleccionando_pared = False
                self._avisar_accion("Selección cancelada")
                return
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
        """Corta el movimiento continuo al soltar la tecla."""
        if symbol in (arcade.key.UP, arcade.key.DOWN, arcade.key.LEFT, arcade.key.RIGHT):
            self.caminando    = False
            self.frame_actual = 0

    def on_text(self, text):
        """Captura texto imprimible mientras se ingresa el nombre al ganar
        (consigna 4 de Ronda 2). Se usa on_text en vez de on_key_press
        porque es el callback pensado para entrada de texto en Arcade."""
        if not self._en_replay and self.estado == "ingresando_nombre" and text.isprintable() and len(self.nombre_input) < 20:
            self.nombre_input += text

    def _volver_al_menu(self):
        """Deja el Tutorial, apagando la música antes de salir."""
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
            self._avisar_accion("No hay otro robot con movimientos disponibles")
            arcade.play_sound(self.snd_no_mover)
            return
        self._guardar_snapshot()
        self.personaje_activo = siguiente
        self._actualizar_texto_personajes()

        self._registrar_leccion("personaje")
        self._registrar_accion_replay("CAMBIAR")

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
            nombre = PERSONAJES_FAMILIA[siguiente]["nombre"]
            self._avisar_accion(f"Robot sin movimientos · Ahora sigue {nombre}")
        self._actualizar_texto_personajes()

    # ── Deshacer (Z) ──────────────────────────────────────────────────────────
    def _guardar_snapshot(self):
        """Copia el estado antes de mover, cambiar personaje o romper pared.
        Se apila en self.historial para poder
        restaurarlo con Z."""
        self.historial.append({
            "col": self.col, "fila": self.fila,
            "paredes": set(self.paredes),
            "mirando_derecha": self.mirando_derecha,
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
        self.paredes           = snap["paredes"]
        self.mirando_derecha   = snap["mirando_derecha"]
        self.fila               = snap["fila"]
        self.sendero            = snap["sendero"]
        self.direcciones        = snap["direcciones"]
        self.personaje_activo   = snap["personaje_activo"]
        self.pasos_restantes    = snap["pasos_restantes"]
        self.pasos               = snap["pasos"]
        self.comida_pendiente   = snap["comida_pendiente"]
        self.sillas              = snap["sillas"]

        self._reconstruir_paredes_sprites()
        self._reconstruir_sendero_sprites()
        self.moviendose = self.caminando = False
        self.px_x, self.px_y = self._celda_a_px(self.col, self.fila)
        self.txt_pasos.value = str(self.pasos)
        self._actualizar_texto_personajes()
        self._actualizar_texto_recursos()

    def _deshacer(self):
        """Restaura movimientos, cambios de personaje o paredes, incluso al perder."""
        if not self.historial:
            self._avisar_accion("Todavía no hay acciones para deshacer")
            arcade.play_sound(self.snd_no_mover)
            return
        self._restaurar_snapshot(self.historial.pop())
        self.seleccionando_pared = False
        self._avisar_accion("Acción deshecha")
        self._registrar_leccion("deshacer")
        if self.estado == "perdido":
            self.estado = "jugando"
            if not self._en_replay:
                self.musica_player = arcade.play_sound(
                    self.musica, volume=guardado.cargar().get("volumen_musica_nivel", 0.3), loop=True)
        self._registrar_accion_replay("DESHACER")

    def _avisar_accion(self, mensaje):
        self.mostrar_anuncio = False
        self.mensaje_accion = mensaje
        self.txt_accion.value = mensaje
        self.tiempo_mensaje = 3.0

    def _intentar_romper_pared(self, dc, df):
        """Rompe una pared ortogonal sin mover el robot ni recolectar recursos."""
        if self.estado != "jugando" or abs(dc) + abs(df) != 1:
            return
        destino = (self.col + dc, self.fila + df)
        personaje_id = PERSONAJES_FAMILIA[self.personaje_activo]["id"]
        if destino not in self.paredes:
            self._avisar_accion("No hay una pared ahí · Elegí otra dirección o cancelá con X")
            arcade.play_sound(self.snd_no_mover)
            return
        if self.pasos_restantes[personaje_id] < 2:
            self._avisar_accion("Necesitás 2 movimientos · C: cambiar robot · X: cancelar")
            arcade.play_sound(self.snd_no_mover)
            return
        self._guardar_snapshot()
        self.paredes.remove(destino)
        self.pasos_restantes[personaje_id] -= 2
        self.pasos += 2
        self.txt_pasos.value = str(self.pasos)
        self.seleccionando_pared = False
        self._reconstruir_paredes_sprites()
        self._actualizar_texto_personajes()
        self._avisar_accion("Pared eliminada · 2 movimientos usados · Z: deshacer")
        arcade.play_sound(self.snd_mover)
        self._verificar_personaje_agotado()
        self._registrar_leccion("pared")
        self._registrar_accion_replay("ROMPER", dc, df)

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
        """Si queda alguna silla sin las pasadas justas que pide."""
        return any(info["recolectadas"] != info["requeridas"] for info in self.sillas.values())

    def _intentar_mover(self, dc, df):
        """Intenta mover al personaje activo en la dirección (dc, df).

        El sendero, los pasos totales y las paredes son compartidos por
        los 4 personajes; solo el cupo de pasos restantes es individual."""
        if self.estado != "jugando":
            return

        nc, nf = self.col + dc, self.fila + df

        if not (0 <= nc < COLUMNAS and 0 <= nf < FILAS):
            self._avisar_accion("Llegaste al borde del mapa · Elegí otra dirección")
            arcade.play_sound(self.snd_no_mover)
            return
        if (nc, nf) in self.paredes:
            self._avisar_accion("Hay una pared · X y una flecha para romperla por 2 movimientos")
            arcade.play_sound(self.snd_no_mover)
            return
        if (nc, nf) in self.sendero:
            self._avisar_accion("Ya pasaste por esa celda · Z deshace la última acción")
            arcade.play_sound(self.snd_no_mover)
            return

        self._guardar_snapshot()

        self.col, self.fila = nc, nf
        self.direcciones[(nc, nf)] = (dc, df)
        self.mirando_derecha = spr.mirada_segun(dc, self.mirando_derecha)
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
                if any(info["excedido"] for info in self.sillas.values()):
                    self._avisar_accion("Te pasaste en una silla · Usá Z hasta corregir su contador")
                else:
                    faltantes = []
                    if self.comida_pendiente:
                        faltantes.append(f"comida pendiente: {len(self.comida_pendiente)}")
                    if self._hay_sillas_incompletas():
                        faltantes.append("sillas sin completar")
                    self._avisar_accion("Falta para entrar: " + " · ".join(faltantes))
                return
            self._ganar_nivel()
            self._registrar_accion_replay("MOVER", dc, df)
            return

        # Solo se enseña a partir de movimientos aceptados, nunca del paso
        # al merendero que se revirtió por faltar recursos.
        anterior = self.historial[-1]
        self._registrar_leccion("mover")
        if len(self.comida_pendiente) < len(anterior["comida_pendiente"]):
            self._registrar_leccion("comida")
        if any(info["recolectadas"] > anterior["sillas"][pos]["recolectadas"]
               for pos, info in self.sillas.items()):
            self._registrar_leccion("silla")
        if any(info["excedido"] and not anterior["sillas"][pos]["excedido"]
               for pos, info in self.sillas.items()):
            self._avisar_accion("Te pasaste en una silla · Z: deshacer y elegir otro recorrido")
        elif (nc, nf) in self.sillas:
            self._avisar_accion("Pisar la silla no la recoge · Tenés que pasar por sus lados")
        self._verificar_personaje_agotado()
        self._registrar_accion_replay("MOVER", dc, df)

    def _ganar_nivel(self):
        """Cierra el nivel y pasa a pedir el nombre del jugador."""
        if self._en_replay:
            self.estado = "victoria"
            return
        self.estado       = "ingresando_nombre"
        self.nombre_input = ""
        arcade.play_sound(self.snd_victoria)
        if hasattr(self, "musica_player") and self.musica_player:
            arcade.stop_sound(self.musica_player)
            self.musica_player = None

    def _confirmar_nombre(self):
        """Guarda nombre y tiempo en el .txt de puntajes (consigna 4) y
        muestra la pantalla de victoria."""
        if self._en_replay or self.estado != "ingresando_nombre":
            return
        try:
            self.puesto_ranking, self.total_ranking = guardado.registrar_puntaje_tutorial(
                self.nombre_input, self.tiempo_transcurrido)
        except (OSError, UnicodeError):
            self.error_guardado = "No se pudo guardar el puntaje. ENTER: reintentar"
            return
        self.error_guardado = ""
        self.txt_ranking.value = f"Puesto {self.puesto_ranking} de {self.total_ranking} participantes"
        self.estado = "victoria"
        for _ in range(80):
            self.particulas.append(Particula())

    # ── Actualización ─────────────────────────────────────────────────────────
    def on_update(self, delta_time):
        """Un cuadro del Tutorial: animación, movimiento y cronómetro."""
        if self._en_replay:
            self._actualizar_replay(delta_time)
        self.timer_frame += 1
        if self.timer_frame >= self.velocidad_frame:
            self.timer_frame  = 0
            self.frame_actual = (self.frame_actual + 1) % len(self._frames_activos())

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

        if self.estado == "jugando" and not self._en_replay:
            self.tiempo_transcurrido += delta_time
        if not self.seleccionando_pared:
            self.tiempo_mensaje = max(0.0, self.tiempo_mensaje - delta_time)
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
        """Dibuja el nivel, el panel y el overlay que corresponda."""
        self.window.clear(self._color((20, 28, 36), HC_NEGRO))

        if self.alto_contraste:
            self._dibujar_grilla_contraste()
        else:
            self.fondo_sprites.draw()
            self.sendero_sprites.draw()
            self.paredes_sprites.draw()
        self._dibujar_comida()
        self._dibujar_sillas()
        self._dibujar_portal()
        self._dibujar_personaje()

        self._dibujar_panel()
        if (self.estado == "jugando" or self._en_replay) and (self.seleccionando_pared or self.tiempo_mensaje > 0 or self._en_replay):
            arcade.draw_lrbt_rectangle_filled(0, ANCHO_JUEGO, ALTO_VENTANA - 40,
                                             ALTO_VENTANA, HC_NEGRO)
            self.txt_accion.draw()

        if self.mostrar_anuncio:
            self._dibujar_anuncio_nivel()
        if self._en_replay:
            return  # Se ve la grilla final; no se pide nombre ni guarda puntaje.
        if self.estado == "ingresando_nombre":
            self._dibujar_overlay_nombre()
        elif self.estado == "victoria":
            self._dibujar_overlay_victoria()
        elif self.estado == "perdido":
            self._dibujar_overlay_perdido()
        if self.estado != "jugando" and self.tiempo_mensaje > 0:
            arcade.draw_lrbt_rectangle_filled(0, ANCHO_JUEGO, ALTO_VENTANA - 40,
                                             ALTO_VENTANA, HC_NEGRO)
            self.txt_accion.draw()

    def _dibujar_grilla_contraste(self):
        """Celdas negras, paredes blancas y sendero punteado; bordes de 3 px."""
        for col, fila in self.paredes:
            arcade.draw_lrbt_rectangle_filled(
                col * TAM_CELDA + 4, (col + 1) * TAM_CELDA - 4,
                fila * TAM_CELDA + 4, (fila + 1) * TAM_CELDA - 4, HC_BLANCO)
        for col, fila in self.sendero:
            x, y = self._celda_a_px(col, fila)
            arcade.draw_circle_filled(x, y, 5, HC_BLANCO)
        for col in range(COLUMNAS + 1):
            arcade.draw_line(col * TAM_CELDA, 0, col * TAM_CELDA, ALTO_JUEGO, HC_BLANCO, 3)
        for fila in range(FILAS + 1):
            arcade.draw_line(0, fila * TAM_CELDA, ANCHO_JUEGO, fila * TAM_CELDA, HC_BLANCO, 3)

    def _celda_a_px(self, col, fila):
        """Convierte coordenadas de grilla al centro de la celda en píxeles."""
        x = col * TAM_CELDA + TAM_CELDA // 2
        y = fila * TAM_CELDA + TAM_CELDA // 2
        return x, y

    def _dibujar_hexagono(self, cx, cy, radio, color):
        """Dibuja un hexágono relleno con su contorno, para la comida."""
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
            self._dibujar_hexagono(x, y, radio, self._color(COLOR_COMIDA, HC_AMARILLO))

    def _dibujar_sillas(self):
        """Ídem para sillas de ruedas, pero como triángulo, con el contador
        de pasadas encima.

        Las sillas NO se recogen pisándolas sino pasando por sus lados, que
        es lo que menos se entiende de todo el nivel. Para enseñarlo sin
        tener que explicarlo con texto, se marcan en el piso las celdas
        vecinas por las que todavía conviene pasar: el jugador ve dónde
        tiene que caminar y deduce la regla solo.

        El color del triángulo dice en qué estado está: azul si falta,
        verde si ya tiene las pasadas justas, y rojo si se pasó de más (en
        ese caso el nivel ya no se puede completar)."""
        radio = TAM_CELDA * 0.32
        for (col, fila), info in self.sillas.items():
            faltan = info["requeridas"] - info["recolectadas"]

            # Marcas en los lados que todavía suman una pasada.
            if faltan > 0 and not info["excedido"]:
                self._marcar_lados_de_silla(col, fila)

            x, y = self._celda_a_px(col, fila)
            if info["excedido"]:
                color = COLOR_SILLA_EXCEDIDA
            elif faltan == 0:
                color = COLOR_SILLA_COMPLETA
            else:
                color = COLOR_SILLA
            if self.alto_contraste:
                color = HC_BLANCO if faltan == 0 else HC_AMARILLO

            puntos = [(x, y + radio), (x - radio, y - radio), (x + radio, y - radio)]
            arcade.draw_polygon_filled(puntos, color)
            arcade.draw_polygon_outline(puntos, (0, 0, 0), 2)

            etiqueta = self.txt_sillas_celda[(col, fila)]
            etiqueta.value = ("de mas!" if info["excedido"]
                              else f"{info['recolectadas']}/{info['requeridas']}")
            etiqueta.y = y - radio - 12
            etiqueta.color = HC_BLANCO
            etiqueta.font_size = 9
            if self.alto_contraste:
                etiqueta.value = f"{info['recolectadas']}/{info['requeridas']}"
                etiqueta.color = HC_NEGRO
                etiqueta.font_size = 8
                etiqueta.y = y - radio + 8
            etiqueta.draw()

    def _marcar_lados_de_silla(self, col, fila):
        """Dibuja un recuadro punteado en cada celda vecina por la que aún
        se puede pasar para tomar una silla. Se saltean las paredes y las
        celdas ya recorridas, porque por ahí ya no se puede volver a
        pasar: así la marca siempre señala opciones reales."""
        for dc, df in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            vecina = (col + dc, fila + df)
            if not (0 <= vecina[0] < COLUMNAS and 0 <= vecina[1] < FILAS):
                continue
            if vecina in self.paredes or vecina in self.sendero:
                continue
            izq = vecina[0] * TAM_CELDA + 6
            der = izq + TAM_CELDA - 12
            aba = vecina[1] * TAM_CELDA + 6
            arr = aba + TAM_CELDA - 12
            arcade.draw_lrbt_rectangle_outline(izq, der, aba, arr,
                                               self._color(COLOR_LADO_SILLA, HC_BLANCO), 2)

    def _dibujar_portal(self):
        """La consigna obligatoria de Ronda 1 pide una imagen fija en la
        celda del merendero -acá siempre se muestra, porque Tutorial no
        tiene "niveles siguientes" donde todavía no corresponda."""
        col, fila = POS_MERENDERO
        x, y = self._celda_a_px(col, fila)
        if self.alto_contraste:
            arcade.draw_lrbt_rectangle_filled(
                col * TAM_CELDA + 4, (col + 1) * TAM_CELDA - 4,
                fila * TAM_CELDA + 4, (fila + 1) * TAM_CELDA - 4, HC_BLANCO)
            self.txt_merendero_celda.draw()
            return
        arcade.draw_lrbt_rectangle_filled(
            col * TAM_CELDA + 1, col * TAM_CELDA + TAM_CELDA - 1,
            fila * TAM_CELDA + 1, fila * TAM_CELDA + TAM_CELDA - 1,
            (192, 57, 43, 180)
        )
        arcade.draw_texture_rect(self.img_merendero, arcade.XYWH(x, y, TAM_CELDA, TAM_CELDA))

    def _animacion_activa(self):
        """Frames y color del personaje activo. El color sale de la familia y
        no de constantes.py: quien tiene arte propio viene con tinte neutro,
        y quien todavía reusa el spritesheet de UAIBOT viene con su color."""
        return self.familia[PERSONAJES_FAMILIA[self.personaje_activo]["id"]]

    def _frames_activos(self):
        """Los frames que toca mostrar: caminando o quieto."""
        datos = self._animacion_activa()
        return datos["walk"] if self.moviendose else datos["idle"]

    def _dibujar_personaje(self):
        """Dibuja al personaje activo en su posición interpolada."""
        if self.alto_contraste:
            # Etiqueta fija dentro de la celda lógica, incluso al interpolar
            # la animación normal: el nombre nunca queda entre dos celdas.
            x, y = self._celda_a_px(self.col, self.fila)
            arcade.draw_lrbt_rectangle_filled(x - 26, x + 26, y - 17, y + 17, HC_AMARILLO)
            self.txt_robot_celda.x, self.txt_robot_celda.y = x, y
            self.txt_robot_celda.draw()
            return
        frames = self._frames_activos()
        self.sprite_personaje.texture  = spr.orientar(
            frames[self.frame_actual % len(frames)], self.mirando_derecha)
        self.sprite_personaje.color    = self._animacion_activa()["color"]
        self.sprite_personaje.center_x = self.px_x
        self.sprite_personaje.center_y = self.px_y
        self.sprites_personaje.draw()

    def _dibujar_anuncio_nivel(self):
        """Cartel de arranque del nivel, que se desvanece solo."""
        alpha = int(255 * min(1.0, (120 - self.timer_anuncio) / 30))
        arcade.draw_lrbt_rectangle_filled(0, ANCHO_JUEGO, 0, ALTO_VENTANA,
                                         self._color((0, 0, 0, 150), HC_NEGRO))
        arcade.Text("TUTORIAL", ANCHO_JUEGO // 2, ALTO_VENTANA // 2,
                    self._color((*arcade.color.GOLD[:3], alpha), HC_AMARILLO), 42,
                    anchor_x="center", anchor_y="center", bold=True).draw()

    # Igual que en Juego: el panel va entre el encabezado fijo y el borde.
    x_iconos      = ANCHO_JUEGO + PANEL_ANCHO - 26
    y_panel_desde = ALTO_VENTANA - 110
    y_panel_hasta = 34

    def _secciones_panel(self):
        """Qué muestra el panel del Tutorial, de arriba hacia abajo."""
        return [
            pnl.Seccion(self.titulo_mision, self.txt_mision),
            pnl.Seccion("PASOS TOTALES", self.txt_pasos, icono=ICONO_PASOS),
            pnl.Seccion("TIEMPO", self.txt_cronometro, icono=ICONO_RELOJ),
            pnl.Seccion("PERSONAJES (C)", self.txt_personajes),
            pnl.Seccion("RECOLECCION", [self.txt_comida, self.txt_sillas]),
            pnl.Seccion("CONTROLES", self.txt_controles),
        ]

    def _acomodar_panel(self):
        """Reparte las secciones del panel lateral (ver panel.py)."""
        self.secciones_panel = pnl.acomodar(
            self._secciones_panel(), self.y_panel_desde, self.y_panel_hasta)

    def _dibujar_panel(self):
        """Dibuja el panel lateral derecho con toda la información."""
        arcade.draw_lrbt_rectangle_filled(ANCHO_JUEGO, ANCHO_VENTANA, 0, ALTO_VENTANA,
                                         self._color((30, 39, 46), HC_NEGRO))
        arcade.draw_line(ANCHO_JUEGO, 0, ANCHO_JUEGO, ALTO_VENTANA,
                         self._color((52, 152, 219)), 2)
        self.txt_titulo.draw()
        self.txt_ofirca.draw()
        self.txt_modo.draw()
        if self.alto_contraste:
            # Sin iconos multicolor ni reglas grises del panel compartido.
            for seccion in self.secciones_panel:
                if seccion.txt_titulo:
                    seccion.txt_titulo.x = ANCHO_JUEGO + pnl.MARGEN_X
                    seccion.txt_titulo.y = seccion.y_titulo
                    seccion.txt_titulo.draw()
                for texto in seccion.cuerpo:
                    if texto.value:
                        texto.draw()
        else:
            pnl.dibujar(self.secciones_panel, ANCHO_JUEGO, ANCHO_VENTANA,
                        self.x_iconos, spr.dibujar_icono)
        arcade.draw_lrbt_rectangle_filled(ANCHO_JUEGO + 16, ANCHO_VENTANA - 16, 4, 26,
                                         self._color((45, 65, 80), HC_NEGRO))
        arcade.draw_lrbt_rectangle_outline(ANCHO_JUEGO + 16, ANCHO_VENTANA - 16, 4, 26,
                                          self._color(arcade.color.GOLD, HC_AMARILLO), 2)
        self.txt_replay.draw()

    def _dibujar_overlay_nombre(self):
        """Pantalla donde el jugador escribe su nombre al ganar."""
        arcade.draw_lrbt_rectangle_filled(0, ANCHO_JUEGO, 0, ALTO_VENTANA,
                                         self._color((0, 0, 0, 200), HC_NEGRO))
        cx, cy = ANCHO_JUEGO // 2, ALTO_VENTANA // 2
        arcade.Text("¡LLEGASTE AL MERENDERO!", cx, cy + 70, self._color(arcade.color.GOLD, HC_AMARILLO), 26,
                    anchor_x="center", anchor_y="center", bold=True).draw()
        arcade.Text(f"Tiempo: {self.tiempo_transcurrido:.1f}s", cx, cy + 30,
                    self._color((200, 200, 200)), 14, anchor_x="center", anchor_y="center").draw()
        arcade.Text("Ingresa tu nombre y presiona ENTER:", cx, cy - 10,
                    self._color((200, 200, 200)), 14, anchor_x="center", anchor_y="center").draw()
        arcade.Text(self.nombre_input + "_", cx, cy - 45,
                    arcade.color.WHITE, 22, anchor_x="center", anchor_y="center", bold=True).draw()
        if self.error_guardado:
            arcade.Text(self.error_guardado, cx, cy - 85, self._color(arcade.color.RED), 12,
                        anchor_x="center", anchor_y="center").draw()

    def _dibujar_overlay_victoria(self):
        """Pantalla de victoria, con el tiempo y el confeti."""
        arcade.draw_lrbt_rectangle_filled(0, ANCHO_JUEGO, 0, ALTO_VENTANA,
                                         self._color((0, 0, 0, 180), HC_NEGRO))
        for p in self.particulas:
            if self.alto_contraste:
                arcade.draw_lrbt_rectangle_filled(p.x, p.x + p.tam, p.y, p.y + p.tam, HC_AMARILLO)
            else:
                p.dibujar()
        self.txt_victoria.draw()
        arcade.Text(f"Tiempo: {self.tiempo_transcurrido:.1f}s", ANCHO_JUEGO // 2, ALTO_VENTANA // 2,
                    self._color(arcade.color.LIME_GREEN, HC_AMARILLO), 16,
                    anchor_x="center", anchor_y="center", bold=True).draw()
        self.txt_ranking.draw()
        self.txt_victoria_sub.draw()

    def _dibujar_overlay_perdido(self):
        """Pantalla de derrota cuando ya no quedan pasos."""
        arcade.draw_lrbt_rectangle_filled(0, ANCHO_JUEGO, 0, ALTO_VENTANA,
                                         self._color((0, 0, 0, 180), HC_NEGRO))
        self.txt_perdido.draw()
        self.txt_perdido_sub.draw()
        self.txt_perdido_sub2.draw()
