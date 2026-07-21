# juego.py
# Vista principal del juego. Maneja toda la lógica de UAIBOT:
# movimiento, colisiones, puntaje, animaciones y renderizado.

import arcade
import random
import guardado
import nivel as nivel_mod
import sprites as spr
from constantes import *

# ── Configuración del spritesheet de UAIBOT ───────────────────────────────────
TOTAL_FRAMES = 6      # cantidad de frames en cada spritesheet
FRAME_WIDTH  = 128    # ancho de cada frame en píxeles
FRAME_HEIGHT = 128    # alto de cada frame en píxeles

# ── Configuración de spritesheets de puertas ──────────────────────────────────
# Las puertas tienen animación de UN SOLO SENTIDO (cerrada → abierta, 5 frames).
# No son loops como llave/portal/teleporte.
ANCHO_TOTAL_PUERTA_LLAVE, ALTO_PUERTA_LLAVE = 937, 150
ANCHO_TOTAL_PUERTA_PLACA, ALTO_PUERTA_PLACA = 907, 155
CANTIDAD_FRAMES_PUERTA = 5


class Particula:
    """Representa un cuadrado de confeti para la animación de victoria."""

    def __init__(self):
        self.x = random.randint(0, ANCHO_JUEGO)
        self.y = ALTO_VENTANA
        self.vy = random.uniform(-3, -1)   # velocidad vertical (cae hacia abajo)
        self.vx = random.uniform(-1, 1)    # velocidad horizontal aleatoria
        self.color = random.choice([
            arcade.color.GOLD, arcade.color.ELECTRIC_BLUE,
            arcade.color.HOT_PINK, arcade.color.LIME_GREEN,
            arcade.color.ORANGE
        ])
        self.tam = random.randint(4, 10)

    def actualizar(self):
        self.x += self.vx
        self.y += self.vy

    def dibujar(self):
        arcade.draw_lrbt_rectangle_filled(
            self.x, self.x + self.tam,
            self.y, self.y + self.tam,
            self.color
        )


class Juego(arcade.View):
    """Vista principal del juego. Hereda de arcade.View para integrarse
    con el sistema de vistas de Arcade (menu → juego → menu)."""

    def __init__(self, dificultad="facil", controles="flechas"):
        super().__init__()
        self.dificultad = dificultad
        self.controles  = controles
        # Los assets se cargan una sola vez en __init__ para evitar
        # congelamientos al reiniciar niveles con setup()
        self._cargar_assets()

    # ── Setup / Reinicio ──────────────────────────────────────────────────────
    def setup(self, numero_nivel=1, puntaje_total=0):
        """Inicializa o reinicia el estado del juego para el nivel indicado.
        Se llama al iniciar partida, al reiniciar (R) y al pasar de nivel."""

        # Detener música anterior antes de reproducir la del nuevo nivel
        if hasattr(self, 'musica_player') and self.musica_player:
            arcade.stop_sound(self.musica_player)
            self.musica_player = None
        self.musica_player = arcade.play_sound(self.musica, volume=0.3, loop=True)

        self.numero_nivel  = numero_nivel
        self.puntaje_total = puntaje_total
        self.pasos         = 0
        self.ganado        = False
        self.perdido       = False
        self.particulas    = []
        self.timer_estado  = 0
        self.caminando     = False
        self.tiene_llave   = False
        self.animacion_portal = 0.0
        self.puntaje_nivel = 0   # puntos obtenidos en este nivel específico

        # Generar o cargar los datos del nivel
        datos = nivel_mod.generar_nivel(self.numero_nivel, self.dificultad)
        self.paredes       = datos["paredes"]
        self.portal        = datos["portal"]
        self.pos_llave     = datos["pos_llave"]
        self.hielo         = datos["hielo"]
        self.teleportes    = datos["teleportes"]
        self.puertas_llave = list(datos["puertas_llave"])
        self.puertas_placa = list(datos["puertas_placa"])
        self.placas        = list(datos["placas"])
        self.mapa_ancho    = datos["ancho"]
        self.mapa_alto     = datos["alto"]

        # Inicializar el estado de animación de cada puerta del nivel
        self._inicializar_estado_puertas()

        # Anuncio de nivel al inicio (se muestra 2 segundos)
        self.mostrar_anuncio = True
        self.timer_anuncio   = 0

        # Si el nivel tiene tilemap de Tiled, activar la cámara con scroll horizontal
        self.tile_map = datos.get("tile_map", None)
        if self.tile_map:
            self.escena = arcade.Scene.from_tilemap(self.tile_map)
            self.camara = arcade.Camera2D()
            self.camara.position = (ANCHO_JUEGO // 2, ALTO_JUEGO // 2)
        else:
            self.escena = None
            self.camara = None

        # Posición inicial de UAIBOT
        self.col, self.fila  = POS_INICIO
        self.sendero         = {POS_INICIO}   # celdas ya visitadas
        self.direcciones     = {}              # dirección con que se entró a cada celda

        self.pasos_minimos = nivel_mod.pasos_minimos(POS_INICIO, self.portal, self.paredes)
        self._crear_textos()

        # Posición en píxeles para el movimiento suave
        self.px_x, self.px_y    = self._celda_a_px(*POS_INICIO)
        self.moviendose         = False
        self.velocidad_movimiento = 8   # píxeles por frame

    def _inicializar_estado_puertas(self):
        """Crea el estado de animación inicial para todas las puertas del nivel.
        Cada puerta arranca en frame 0 (cerrada) y sin animación activa."""
        self.anim_puertas_llave = {
            pos: {"anim_frame": 0, "animando": False, "timer": 0}
            for pos in self.puertas_llave
        }
        self.anim_puertas_placa = {
            puerta["pos"]: {"anim_frame": 0, "animando": False, "timer": 0}
            for puerta in self.puertas_placa
        }

    # ── Carga de assets ───────────────────────────────────────────────────────
    def _cargar_assets(self):
        """Carga todos los sprites, sonidos y música del juego.
        Solo se ejecuta una vez en __init__ para no bloquear entre niveles."""

        # Spritesheet de UAIBOT: 6 frames de 128x128 en una fila
        sheet_idle = arcade.load_spritesheet("assets/Idle.png")
        sheet_walk = arcade.load_spritesheet("assets/Walk.png")
        self.frames_idle = []
        self.frames_walk = []
        for i in range(TOTAL_FRAMES):
            self.frames_idle.append(
                sheet_idle.get_texture(arcade.LRBT(
                    i * FRAME_WIDTH, i * FRAME_WIDTH + FRAME_WIDTH, 0, FRAME_HEIGHT))
            )
            self.frames_walk.append(
                sheet_walk.get_texture(arcade.LRBT(
                    i * FRAME_WIDTH, i * FRAME_WIDTH + FRAME_WIDTH, 0, FRAME_HEIGHT))
            )

        self.frame_actual    = 0
        self.timer_frame     = 0
        self.velocidad_frame = 8   # frames de juego entre cada frame de animación

        # Imagen estática del merendero (nivel 10)
        self.img_merendero = arcade.load_texture("assets/merendero.png")

        # Sonidos de acción
        self.snd_mover    = arcade.load_sound("assets/Moverse.wav")
        self.snd_no_mover = arcade.load_sound("assets/NoMoverse.wav")
        self.snd_victoria = arcade.load_sound("assets/CompletedLevel.wav")
        self.musica       = arcade.load_sound("assets/GameLevelMusic.wav")

        # Spritesheets de elementos animados en loop
        sheet_llave     = arcade.load_spritesheet("assets/llave_anim.png")
        sheet_portal    = arcade.load_spritesheet("assets/portal_anim.png")
        sheet_teleporte = arcade.load_spritesheet("assets/teleporte_anim.png")

        self.frames_llave = [
            sheet_llave.get_texture(arcade.LRBT(i * 20, i * 20 + 20, 0, 20))
            for i in range(7)
        ]
        self.frames_portal = [
            sheet_portal.get_texture(arcade.LRBT(i * 64, i * 64 + 64, 0, 64))
            for i in range(8)
        ]
        self.frames_teleporte = [
            sheet_teleporte.get_texture(arcade.LRBT(i * 32, i * 32 + 32, 0, 32))
            for i in range(6)
        ]

        # Timer compartido para elementos animados en loop
        self.frame_elementos    = 0
        self.timer_elementos    = 0
        self.velocidad_elementos = 10

        # Spritesheets de puertas (animación única de apertura)
        self._cargar_assets_puertas()

    def _cargar_assets_puertas(self):
        """Recorta los frames de apertura de puerta_llave y puerta_placa.
        Cada spritesheet tiene 5 frames horizontales de distinto ancho."""
        frame_w_llave = ANCHO_TOTAL_PUERTA_LLAVE / CANTIDAD_FRAMES_PUERTA
        frame_w_placa = ANCHO_TOTAL_PUERTA_PLACA / CANTIDAD_FRAMES_PUERTA

        sheet_puerta_llave = arcade.load_spritesheet(SPRITE_PUERTA_LLAVE)
        sheet_puerta_placa = arcade.load_spritesheet(SPRITE_PUERTA_PLACA)

        self.frames_puerta_llave = [
            sheet_puerta_llave.get_texture(
                arcade.LRBT(round(i * frame_w_llave), round((i + 1) * frame_w_llave),
                            0, ALTO_PUERTA_LLAVE)
            )
            for i in range(CANTIDAD_FRAMES_PUERTA)
        ]
        self.frames_puerta_placa = [
            sheet_puerta_placa.get_texture(
                arcade.LRBT(round(i * frame_w_placa), round((i + 1) * frame_w_placa),
                            0, ALTO_PUERTA_PLACA)
            )
            for i in range(CANTIDAD_FRAMES_PUERTA)
        ]

        # Velocidad de apertura: frames de juego por frame de sprite
        self.velocidad_apertura_puerta = 4

    # ── Textos del panel ──────────────────────────────────────────────────────
    def _crear_textos(self):
        """Crea los objetos Text del panel lateral y los overlays.
        Se llama en cada setup() porque algunos valores cambian entre niveles."""
        px = ANCHO_JUEGO
        pw = PANEL_ANCHO
        cx = px + pw // 2
        es_ultimo = self.numero_nivel == 10

        self.txt_titulo    = arcade.Text("UAIBOT", cx, ALTO_VENTANA - 35,
                                          arcade.color.GOLD, 26, anchor_x="center", bold=True)
        self.txt_ofirca    = arcade.Text("OFIRCA 2026", cx, ALTO_VENTANA - 58,
                                          (52, 152, 219), 12, anchor_x="center")
        self.txt_nivel     = arcade.Text(f"Nivel {self.numero_nivel}/10", cx, ALTO_VENTANA - 85,
                                          arcade.color.WHITE, 13, anchor_x="center", bold=True)
        self.txt_dificultad = arcade.Text(f"Dificultad: {self.dificultad}", cx, ALTO_VENTANA - 103,
                                           (150, 150, 150), 11, anchor_x="center")

        self.txt_mision_titulo = arcade.Text("MISION", px + 16, ALTO_VENTANA - 128,
                                              arcade.color.GOLD, 11, bold=True)
        mision = "Lleva las donaciones\nal merendero." if es_ultimo else "Llega al portal\npara avanzar."
        if self.dificultad == "dificil" and self.pos_llave:
            mision += "\nRecoge la llave\nprimero con E."
        self.txt_mision = arcade.Text(mision, px + 16, ALTO_VENTANA - 148,
                                       (200, 200, 200), 10, multiline=True, width=pw - 32)

        self.txt_pasos_titulo = arcade.Text("PASOS", px + 16, ALTO_VENTANA - 265,
                                             arcade.color.GOLD, 11, bold=True)
        self.txt_pasos        = arcade.Text("0", px + 16, ALTO_VENTANA - 290,
                                             (200, 200, 200), 22, bold=True)
        self.txt_pasos_min    = arcade.Text(f"Minimo sugerido: {self.pasos_minimos}",
                                             px + 16, ALTO_VENTANA - 318, (100, 180, 100), 10)

        # El límite de pasos solo aplica en medio y difícil
        if self.dificultad in ("medio", "dificil"):
            limite = self.pasos_minimos * 2 if self.pasos_minimos else "-"
            self.txt_limite = arcade.Text(f"Limite maximo: {limite}",
                                           px + 16, ALTO_VENTANA - 334, (220, 100, 100), 10)
        else:
            self.txt_limite = arcade.Text("", px + 16, ALTO_VENTANA - 334, (0, 0, 0), 10)

        self.txt_puntaje_titulo = arcade.Text("PUNTAJE", px + 16, ALTO_VENTANA - 364,
                                               arcade.color.GOLD, 11, bold=True)
        self.txt_puntaje        = arcade.Text(str(self.puntaje_total), px + 16, ALTO_VENTANA - 390,
                                               (200, 200, 200), 22, bold=True)

        # Indicador de llave (solo visible en difícil)
        self.txt_llave = arcade.Text("LLAVE: NO", px + 16, ALTO_VENTANA - 428,
                                      (200, 100, 100), 11, bold=True)

        self.txt_controles_titulo = arcade.Text("CONTROLES", px + 16, ALTO_VENTANA - 468,
                                                 arcade.color.GOLD, 11, bold=True)
        controles_texto = "WASD: mover\nR: reiniciar nivel\nN: reiniciar juego\nESC: menu" \
                          if self.controles == "wasd" else \
                          "Flechas: mover\nR: reiniciar nivel\nN: reiniciar juego\nESC: menu"
        self.txt_controles  = arcade.Text(controles_texto, px + 16, ALTO_VENTANA - 540,
                                           (200, 200, 200), 10, multiline=True, width=pw - 32)
        self.txt_reiniciar  = arcade.Text("R=nivel  N=inicio  ESC=menu",
                                           cx, 16, (120, 120, 120), 9, anchor_x="center")

        # Textos para los overlays de victoria y derrota
        self.txt_victoria = arcade.Text(
            "¡NIVEL COMPLETADO!" if self.numero_nivel < 10 else "¡MISION CUMPLIDA!",
            ANCHO_JUEGO // 2, ALTO_VENTANA // 2 + 30,
            arcade.color.GOLD, 30, anchor_x="center", anchor_y="center", bold=True)
        self.txt_victoria_sub = arcade.Text(
            "Continuando..." if self.numero_nivel < 10 else "Presiona N para jugar de nuevo",
            ANCHO_JUEGO // 2, ALTO_VENTANA // 2 - 20,
            (200, 200, 200), 14, anchor_x="center", anchor_y="center")
        self.txt_perdido = arcade.Text("¡SIN PASOS!",
            ANCHO_JUEGO // 2, ALTO_VENTANA // 2 + 30,
            arcade.color.RED, 32, anchor_x="center", anchor_y="center", bold=True)
        self.txt_perdido_sub = arcade.Text("R=Reiniciar nivel  N=Desde el inicio",
            ANCHO_JUEGO // 2, ALTO_VENTANA // 2 - 20,
            (200, 200, 200), 14, anchor_x="center", anchor_y="center")

    # ── Detección de teclas según esquema de controles ────────────────────────
    def _tecla_arriba(self, symbol):
        return symbol == (arcade.key.W  if self.controles == "wasd" else arcade.key.UP)

    def _tecla_abajo(self, symbol):
        return symbol == (arcade.key.S  if self.controles == "wasd" else arcade.key.DOWN)

    def _tecla_izquierda(self, symbol):
        return symbol == (arcade.key.A  if self.controles == "wasd" else arcade.key.LEFT)

    def _tecla_derecha(self, symbol):
        return symbol == (arcade.key.D  if self.controles == "wasd" else arcade.key.RIGHT)

    # ── Eventos ───────────────────────────────────────────────────────────────
    def on_key_press(self, symbol, modifiers):
        if self._tecla_arriba(symbol):
            self._intentar_mover(0, 1)
        elif self._tecla_abajo(symbol):
            self._intentar_mover(0, -1)
        elif self._tecla_izquierda(symbol):
            self._intentar_mover(-1, 0)
        elif self._tecla_derecha(symbol):
            self._intentar_mover(1, 0)
        elif symbol == arcade.key.E:
            self._intentar_recoger_llave()
        elif symbol == arcade.key.R:
            self.setup(self.numero_nivel, self.puntaje_total)
        elif symbol == arcade.key.N:
            self.setup(1, 0)
        elif symbol == arcade.key.ESCAPE:
            # Detener música al volver al menú
            if hasattr(self, 'musica_player') and self.musica_player:
                arcade.stop_sound(self.musica_player)
                self.musica_player = None
            from menu import Menu
            self.window.show_view(Menu())

    def on_key_release(self, symbol, modifiers):
        """Al soltar una tecla de movimiento, UAIBOT vuelve a animación idle."""
        if symbol in (arcade.key.UP, arcade.key.DOWN, arcade.key.LEFT, arcade.key.RIGHT,
                      arcade.key.W, arcade.key.A, arcade.key.S, arcade.key.D):
            self.caminando    = False
            self.frame_actual = 0

    # ── Lógica de juego ───────────────────────────────────────────────────────
    def _intentar_recoger_llave(self):
        """Recoge la llave si UAIBOT está en la misma celda y aún no la tiene.
        Al recogerla, dispara la animación de apertura de las puertas correspondientes."""
        if self.pos_llave and (self.col, self.fila) == self.pos_llave and not self.tiene_llave:
            self.tiene_llave = True
            self.txt_llave.value = "LLAVE: SI"
            self.txt_llave.color = (100, 200, 100)
            for pos in self.puertas_llave:
                self.paredes.discard(pos)
                if pos in self.anim_puertas_llave:
                    self.anim_puertas_llave[pos]["animando"] = True

    def _intentar_mover(self, dc, df):
        """Intenta mover a UAIBOT en la dirección (dc, df).
        Verifica límites, paredes y sendero antes de confirmar el movimiento.
        También procesa hielo, teleportes, placas y condición de victoria."""
        if self.ganado or self.perdido:
            return

        nc = self.col + dc
        nf = self.fila + df

        # Verificar límites de la grilla
        if not (0 <= nc < self.mapa_ancho and 0 <= nf < self.mapa_alto):
            arcade.play_sound(self.snd_no_mover)
            return

        # Verificar pared
        if (nc, nf) in self.paredes:
            arcade.play_sound(self.snd_no_mover)
            return

        # Verificar sendero ya pisado (no se puede volver por donde pasó)
        if (nc, nf) in self.sendero:
            arcade.play_sound(self.snd_no_mover)
            return

        # Movimiento válido
        self.col, self.fila = nc, nf
        self.direcciones[(nc, nf)] = (dc, df)
        self.sendero.add((nc, nf))
        self.pasos += 1
        self.txt_pasos.value = str(self.pasos)
        self.caminando = True
        arcade.play_sound(self.snd_mover)

        # Hielo: desliza una celda extra en la misma dirección si es posible
        if (self.col, self.fila) in self.hielo:
            nc2 = self.col + dc
            nf2 = self.fila + df
            if (0 <= nc2 < self.mapa_ancho and 0 <= nf2 < self.mapa_alto
                    and (nc2, nf2) not in self.paredes
                    and (nc2, nf2) not in self.sendero):
                self.col, self.fila = nc2, nf2
                self.direcciones[(nc2, nf2)] = (dc, df)
                self.sendero.add((nc2, nf2))
                self.pasos += 1
                self.txt_pasos.value = str(self.pasos)

        # Teleporte: si UAIBOT llega a una celda de teleporte lo mueve al destino
        if (self.col, self.fila) in self.teleportes:
            destino = self.teleportes[(self.col, self.fila)]
            if destino not in self.sendero:
                self.col, self.fila = destino
                self.sendero.add(destino)
                self.pasos += 1
                self.txt_pasos.value = str(self.pasos)

        # Placas de presión: abren la puerta vinculada al pisarlas
        for placa in self.placas:
            if (self.col, self.fila) == placa["pos"]:
                for puerta in self.puertas_placa:
                    if puerta["id"] == placa["id"] and not puerta["abierta"]:
                        puerta["abierta"] = True
                        self.paredes.discard(puerta["pos"])
                        if puerta["pos"] in self.anim_puertas_placa:
                            self.anim_puertas_placa[puerta["pos"]]["animando"] = True

        # Límite de pasos en medio y difícil (doble del mínimo)
        if self.dificultad in ("medio", "dificil") and self.pasos_minimos:
            if self.pasos >= self.pasos_minimos * 2:
                self.perdido = True
                return

        # Verificar si llegó al portal
        if (self.col, self.fila) == self.portal:
            # En difícil necesita la llave antes de entrar al portal
            if self.dificultad == "dificil" and self.pos_llave and not self.tiene_llave:
                arcade.play_sound(self.snd_no_mover)
                self.col -= dc
                self.fila -= df
                self.sendero.discard((nc, nf))
                self.direcciones.pop((nc, nf), None)
                self.pasos -= 1
                self.txt_pasos.value = str(self.pasos)
                return
            self._completar_nivel()

    def _completar_nivel(self):
        """Marca el nivel como ganado, calcula el puntaje y lanza el confeti."""
        self.ganado        = True
        self.puntaje_nivel = self._calcular_puntaje()
        self.puntaje_total += self.puntaje_nivel
        self.txt_puntaje.value = str(self.puntaje_total)
        guardado.actualizar_highscore(self.puntaje_total)
        arcade.play_sound(self.snd_victoria)
        for _ in range(80):
            self.particulas.append(Particula())

    def _calcular_puntaje(self):
        """Calcula el puntaje del nivel (1-10) según la eficiencia del recorrido.
        Si se usó el mínimo de pasos posible, se obtienen 10 puntos."""
        if not self.pasos_minimos:
            return 10
        ratio = self.pasos_minimos / max(self.pasos, 1)
        return max(1, min(10, round(ratio * 10)))

    # ── Actualización ─────────────────────────────────────────────────────────
    def on_update(self, delta_time):
        # Avanzar animación de UAIBOT
        self.animacion_portal += delta_time * 3.0
        self.timer_frame += 1
        if self.timer_frame >= self.velocidad_frame:
            self.timer_frame  = 0
            self.frame_actual = (self.frame_actual + 1) % TOTAL_FRAMES

        # Movimiento suave: interpolar posición en píxeles hacia la celda destino
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

        # Lógica post-victoria: confeti y paso al siguiente nivel
        if self.ganado:
            self.timer_estado += 1
            for p in self.particulas:
                p.actualizar()
            self.particulas = [p for p in self.particulas if p.y > 0]
            if self.timer_estado % 30 == 0:
                for _ in range(30):
                    self.particulas.append(Particula())
            if self.timer_estado == 180:
                if hasattr(self, 'musica_player') and self.musica_player:
                    arcade.stop_sound(self.musica_player)
                    self.musica_player = None
                if self.numero_nivel < 10:
                    self.setup(self.numero_nivel + 1, self.puntaje_total)
                else:
                    from menu import Menu
                    self.window.show_view(Menu())

        # Avanzar animación de elementos del mapa (llave, portal, teleporte)
        self.timer_elementos += 1
        if self.timer_elementos >= self.velocidad_elementos:
            self.timer_elementos  = 0
            self.frame_elementos  = (self.frame_elementos + 1) % 9

        # Avanzar animaciones de apertura de puertas
        self._actualizar_animacion_puertas()

        # Cámara: seguir a UAIBOT horizontalmente en mapas anchos (medio/difícil)
        if self.camara:
            x, y = self._celda_a_px(self.col, self.fila)
            cam_x = max(ANCHO_JUEGO // 2, min(
                self.mapa_ancho * TAM_CELDA - ANCHO_JUEGO // 2 + TAM_CELDA * 2, x
            ))
            self.camara.position = (cam_x, ALTO_JUEGO // 2)

        # Temporizador del anuncio de nivel (2 segundos = 120 frames)
        if self.mostrar_anuncio:
            self.timer_anuncio += 1
        if self.timer_anuncio >= 120:
            self.mostrar_anuncio = False

    def _actualizar_animacion_puertas(self):
        """Avanza un frame la animación de apertura de cada puerta activa.
        Se detiene automáticamente al llegar al último frame (puerta abierta)."""
        for estado in self.anim_puertas_llave.values():
            if estado["animando"]:
                estado["timer"] += 1
                if estado["timer"] >= self.velocidad_apertura_puerta:
                    estado["timer"] = 0
                    if estado["anim_frame"] < 4:
                        estado["anim_frame"] += 1
                    else:
                        estado["animando"] = False

        for estado in self.anim_puertas_placa.values():
            if estado["animando"]:
                estado["timer"] += 1
                if estado["timer"] >= self.velocidad_apertura_puerta:
                    estado["timer"] = 0
                    if estado["anim_frame"] < 4:
                        estado["anim_frame"] += 1
                    else:
                        estado["animando"] = False

    # ── Dibujo ────────────────────────────────────────────────────────────────
    def on_draw(self):
        self.window.clear((20, 28, 36))

        # Modo con cámara (tilemap de Tiled): scroll horizontal
        if self.camara:
            with self.camara.activate():
                if self.escena:
                    self.escena.draw()   # dibuja fondo y obstáculos del tilemap
                self._dibujar_sendero()
                self._dibujar_paredes()
                self._dibujar_hielo()
                self._dibujar_teleportes()
                self._dibujar_placas()
                self._dibujar_puertas_llave()
                self._dibujar_puertas_placa()
                self._dibujar_portal()
                self._dibujar_llave()
                self._dibujar_uaibot()
        else:
            # Modo sin cámara (generación automática, modo fácil)
            self._dibujar_grilla()
            self._dibujar_sendero()
            self._dibujar_paredes()
            self._dibujar_hielo()
            self._dibujar_teleportes()
            self._dibujar_placas()
            self._dibujar_puertas_llave()
            self._dibujar_puertas_placa()
            self._dibujar_portal()
            self._dibujar_llave()
            self._dibujar_uaibot()

        self._dibujar_panel()

        if self.mostrar_anuncio:
            self._dibujar_anuncio_nivel()
        if self.ganado:
            self._dibujar_overlay_victoria()
        elif self.perdido:
            self._dibujar_overlay_perdido()

    def _celda_a_px(self, col, fila):
        """Convierte coordenadas de grilla (col, fila) al centro en píxeles."""
        x = col * TAM_CELDA + TAM_CELDA // 2
        y = fila * TAM_CELDA + TAM_CELDA // 2
        return x, y

    def _dibujar_grilla(self):
        """Dibuja el fondo de la grilla celda por celda.
        El nivel 1 usa colores planos; los demás usan el sprite de césped."""
        for fila in range(self.mapa_alto):
            for col in range(self.mapa_ancho):
                if self.numero_nivel == 1 or not spr.dibujar_celda(SPRITE_CESPED, col, fila, TAM_CELDA):
                    color = (44, 62, 80) if (col + fila) % 2 == 0 else (39, 55, 70)
                    arcade.draw_lrbt_rectangle_filled(
                        col * TAM_CELDA + 1, col * TAM_CELDA + TAM_CELDA - 1,
                        fila * TAM_CELDA + 1, fila * TAM_CELDA + TAM_CELDA - 1,
                        color
                    )

    def _dibujar_sendero(self):
        """Dibuja las huellas direccionales en las celdas ya visitadas por UAIBOT."""
        for (col, fila) in self.sendero:
            if (col, fila) == POS_INICIO:
                continue
            dc, df = self.direcciones.get((col, fila), (0, 0))
            if dc == 0 and df == 1:
                path = SPRITE_HUELLA_ARRIBA
            elif dc == 0 and df == -1:
                path = SPRITE_HUELLA_ABAJO
            elif dc == -1 and df == 0:
                path = SPRITE_HUELLA_IZQUIERDA
            else:
                path = SPRITE_HUELLA_DERECHA
            if not spr.dibujar_celda(path, col, fila, TAM_CELDA):
                arcade.draw_lrbt_rectangle_filled(
                    col * TAM_CELDA + 1, col * TAM_CELDA + TAM_CELDA - 1,
                    fila * TAM_CELDA + 1, fila * TAM_CELDA + TAM_CELDA - 1,
                    (30, 100, 160)
                )

    def _dibujar_paredes(self):
        """Dibuja las paredes con sprite o color marrón de fallback.
        En modo tilemap se omite porque la escena ya las dibuja."""
        if self.tile_map:
            return
        for (col, fila) in self.paredes:
            if self.numero_nivel == 1 or not spr.dibujar_celda(SPRITE_PARED, col, fila, TAM_CELDA):
                arcade.draw_lrbt_rectangle_filled(
                    col * TAM_CELDA + 1, col * TAM_CELDA + TAM_CELDA - 1,
                    fila * TAM_CELDA + 1, fila * TAM_CELDA + TAM_CELDA - 1,
                    (101, 67, 33)
                )

    def _dibujar_hielo(self):
        """Dibuja las celdas de hielo (celeste) que deslizan a UAIBOT."""
        for (col, fila) in self.hielo:
            if not spr.dibujar_celda(SPRITE_HIELO, col, fila, TAM_CELDA):
                arcade.draw_lrbt_rectangle_filled(
                    col * TAM_CELDA + 1, col * TAM_CELDA + TAM_CELDA - 1,
                    fila * TAM_CELDA + 1, fila * TAM_CELDA + TAM_CELDA - 1,
                    (135, 206, 235)
                )

    def _dibujar_teleportes(self):
        """Dibuja los teleportes con su animación en loop."""
        for (col, fila) in self.teleportes:
            x, y  = self._celda_a_px(col, fila)
            frame = self.frames_teleporte[self.frame_elementos % len(self.frames_teleporte)]
            arcade.draw_texture_rect(frame, arcade.XYWH(x, y, TAM_CELDA, TAM_CELDA))

    def _dibujar_placas(self):
        """Dibuja las placas de presión que abren puertas."""
        for placa in self.placas:
            col, fila = placa["pos"]
            if not spr.dibujar_celda(SPRITE_PLACA, col, fila, TAM_CELDA):
                arcade.draw_lrbt_rectangle_filled(
                    col * TAM_CELDA + 4, col * TAM_CELDA + TAM_CELDA - 4,
                    fila * TAM_CELDA + 4, fila * TAM_CELDA + TAM_CELDA - 4,
                    (200, 160, 0)
                )

    def _dibujar_puertas_llave(self):
        """Dibuja cada puerta de llave en el frame actual de su animación."""
        for pos in self.puertas_llave:
            estado = self.anim_puertas_llave.get(pos)
            if estado is None:
                continue
            col, fila = pos
            x, y  = self._celda_a_px(col, fila)
            frame = self.frames_puerta_llave[estado["anim_frame"]]
            arcade.draw_texture_rect(frame, arcade.XYWH(x, y, TAM_CELDA, TAM_CELDA))

    def _dibujar_puertas_placa(self):
        """Dibuja cada puerta de placa en el frame actual de su animación."""
        for puerta in self.puertas_placa:
            estado = self.anim_puertas_placa.get(puerta["pos"])
            if estado is None:
                continue
            col, fila = puerta["pos"]
            x, y  = self._celda_a_px(col, fila)
            frame = self.frames_puerta_placa[estado["anim_frame"]]
            arcade.draw_texture_rect(frame, arcade.XYWH(x, y, TAM_CELDA, TAM_CELDA))

    def _dibujar_portal(self):
        """Dibuja el portal con animación pulsante.
        En el nivel 10 muestra la imagen del merendero en vez del portal."""
        col, fila = self.portal
        x, y      = self._celda_a_px(col, fila)
        es_ultimo = self.numero_nivel == 10

        if es_ultimo:
            arcade.draw_lrbt_rectangle_filled(
                col * TAM_CELDA + 1, col * TAM_CELDA + TAM_CELDA - 1,
                fila * TAM_CELDA + 1, fila * TAM_CELDA + TAM_CELDA - 1,
                (192, 57, 43, 180)
            )
            arcade.draw_texture_rect(self.img_merendero, arcade.XYWH(x, y, TAM_CELDA, TAM_CELDA))
        else:
            frame = self.frames_portal[self.frame_elementos % len(self.frames_portal)]
            arcade.draw_texture_rect(frame, arcade.XYWH(x, y, TAM_CELDA, TAM_CELDA))

    def _dibujar_llave(self):
        """Dibuja la llave animada si UAIBOT todavía no la recogió."""
        if self.pos_llave and not self.tiene_llave:
            col, fila = self.pos_llave
            x, y  = self._celda_a_px(col, fila)
            frame = self.frames_llave[self.frame_elementos % len(self.frames_llave)]
            arcade.draw_texture_rect(frame, arcade.XYWH(x, y, TAM_CELDA, TAM_CELDA))

    def _dibujar_uaibot(self):
        """Dibuja a UAIBOT en su posición interpolada con la animación correcta."""
        frames = self.frames_walk if self.moviendose else self.frames_idle
        arcade.draw_texture_rect(
            frames[self.frame_actual],
            arcade.XYWH(self.px_x, self.px_y, TAM_CELDA, TAM_CELDA)
        )

    def _dibujar_anuncio_nivel(self):
        """Overlay de introducción al nivel con fade-out en los últimos 30 frames."""
        alpha = int(255 * min(1.0, (120 - self.timer_anuncio) / 30))
        arcade.draw_lrbt_rectangle_filled(0, ANCHO_JUEGO, 0, ALTO_VENTANA, (0, 0, 0, 150))
        arcade.Text(f"NIVEL {self.numero_nivel}",
                    ANCHO_JUEGO // 2, ALTO_VENTANA // 2 + 20,
                    (*arcade.color.GOLD[:3], alpha), 48,
                    anchor_x="center", anchor_y="center", bold=True).draw()
        arcade.Text(self.dificultad.upper(),
                    ANCHO_JUEGO // 2, ALTO_VENTANA // 2 - 30,
                    (*COLOR_ACENTO[:3], alpha), 18,
                    anchor_x="center", anchor_y="center").draw()

    def _dibujar_panel(self):
        """Dibuja el panel lateral derecho con toda la información del juego."""
        arcade.draw_lrbt_rectangle_filled(
            ANCHO_JUEGO, ANCHO_VENTANA, 0, ALTO_VENTANA, (30, 39, 46)
        )
        arcade.draw_line(ANCHO_JUEGO, 0, ANCHO_JUEGO, ALTO_VENTANA, (52, 152, 219), 2)
        self.txt_titulo.draw()
        self.txt_ofirca.draw()
        self.txt_nivel.draw()
        self.txt_dificultad.draw()
        self.txt_mision_titulo.draw()
        self.txt_mision.draw()
        self.txt_pasos_titulo.draw()
        self.txt_pasos.draw()
        self.txt_pasos_min.draw()
        self.txt_limite.draw()
        self.txt_puntaje_titulo.draw()
        self.txt_puntaje.draw()
        self.txt_controles_titulo.draw()
        self.txt_controles.draw()
        self.txt_reiniciar.draw()
        if self.dificultad == "dificil" and self.pos_llave:
            self.txt_llave.draw()

    def _dibujar_overlay_victoria(self):
        """Overlay de victoria con confeti, puntaje obtenido y mensaje de continuación."""
        arcade.draw_lrbt_rectangle_filled(0, ANCHO_JUEGO, 0, ALTO_VENTANA, (0, 0, 0, 180))
        for p in self.particulas:
            p.dibujar()
        self.txt_victoria.draw()
        self.txt_victoria_sub.draw()
        arcade.Text(f"+{self.puntaje_nivel} puntos",
                    ANCHO_JUEGO // 2, ALTO_VENTANA // 2 - 60,
                    arcade.color.LIME_GREEN, 24,
                    anchor_x="center", anchor_y="center", bold=True).draw()

    def _dibujar_overlay_perdido(self):
        """Overlay de derrota cuando UAIBOT supera el límite de pasos."""
        arcade.draw_lrbt_rectangle_filled(0, ANCHO_JUEGO, 0, ALTO_VENTANA, (0, 0, 0, 180))
        self.txt_perdido.draw()
        self.txt_perdido_sub.draw()
