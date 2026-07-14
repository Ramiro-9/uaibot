# juego.py
import arcade
import random
import guardado
import nivel as nivel_mod
import sprites as spr
from constantes import *

TOTAL_FRAMES = 6
FRAME_WIDTH  = 128
FRAME_HEIGHT = 128

class Particula:
    def __init__(self):
        self.x = random.randint(0, ANCHO_JUEGO)
        self.y = ALTO_VENTANA
        self.vy = random.uniform(-3, -1)
        self.vx = random.uniform(-1, 1)
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
    def __init__(self, dificultad="facil", controles="flechas"):
        super().__init__()
        self.dificultad = dificultad
        self.controles  = controles
        self._cargar_assets()

    def setup(self, numero_nivel=1, puntaje_total=0):
        # al inicio de setup, antes de todo
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
        self.puntaje_nivel = 0

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

        self.mostrar_anuncio = True
        self.timer_anuncio = 0

        self.tile_map = datos.get("tile_map", None)
        if self.tile_map:
            self.escena = arcade.Scene.from_tilemap(self.tile_map)
            self.camara = arcade.Camera2D()
            self.camara.position = (ANCHO_JUEGO // 2, ALTO_JUEGO // 2)
        else:
            self.escena = None
            self.camara = None

        self.col, self.fila = POS_INICIO
        self.sendero     = {POS_INICIO}
        self.direcciones = {}

        self.pasos_minimos = nivel_mod.pasos_minimos(POS_INICIO, self.portal, self.paredes)
        self._crear_textos()

        self.px_x, self.px_y = self._celda_a_px(*POS_INICIO)
        self.moviendose = False
        self.velocidad_movimiento = 8  # pixeles por frame

    def _cargar_assets(self):
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
        self.velocidad_frame = 8

        self.img_merendero = arcade.load_texture("assets/merendero.png")
        self.snd_mover     = arcade.load_sound("assets/Moverse.wav")
        self.snd_no_mover  = arcade.load_sound("assets/NoMoverse.wav")
        self.snd_victoria  = arcade.load_sound("assets/CompletedLevel.wav")
        self.musica = arcade.load_sound("assets/GameLevelMusic.wav")

        # spritesheets de elementos animados
        sheet_llave = arcade.load_spritesheet("assets/llave_anim.png")
        sheet_portal = arcade.load_spritesheet("assets/portal_anim.png")
        sheet_teleporte = arcade.load_spritesheet("assets/teleporte_anim.png")

        self.frames_llave = [
            sheet_llave.get_texture(arcade.LRBT(i * 20, i * 20 + 20, 0, 20))
            for i in range(9)
        ]
        self.frames_portal = [
            sheet_portal.get_texture(arcade.LRBT(i * 64, i * 64 + 64, 0, 64))
            for i in range(8)
        ]
        self.frames_teleporte = [
            sheet_teleporte.get_texture(arcade.LRBT(i * 48, i * 48 + 48, 0, 64))
            for i in range(2)
        ]

        self.frame_elementos = 0
        self.timer_elementos = 0
        self.velocidad_elementos = 10

    def _crear_textos(self):
        px = ANCHO_JUEGO
        pw = PANEL_ANCHO
        cx = px + pw // 2
        es_ultimo = self.numero_nivel == 10

        self.txt_titulo = arcade.Text("UAIBOT", cx, ALTO_VENTANA - 35,
                                      arcade.color.GOLD, 26, anchor_x="center", bold=True)
        self.txt_ofirca = arcade.Text("OFIRCA 2026", cx, ALTO_VENTANA - 58,
                                      (52, 152, 219), 12, anchor_x="center")
        self.txt_nivel = arcade.Text(f"Nivel {self.numero_nivel}/10", cx, ALTO_VENTANA - 85,
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
        self.txt_pasos = arcade.Text("0", px + 16, ALTO_VENTANA - 290,
                                      (200, 200, 200), 22, bold=True)
        self.txt_pasos_min = arcade.Text(f"Minimo sugerido: {self.pasos_minimos}",
                                          px + 16, ALTO_VENTANA - 318,
                                          (100, 180, 100), 10)
        if self.dificultad in ("medio", "dificil"):
            limite = self.pasos_minimos * 2 if self.pasos_minimos else "-"
            self.txt_limite = arcade.Text(f"Limite maximo: {limite}",
                                           px + 16, ALTO_VENTANA - 334,
                                           (220, 100, 100), 10)
        else:
            self.txt_limite = arcade.Text("", px + 16, ALTO_VENTANA - 334, (0, 0, 0), 10)
        self.txt_puntaje_titulo = arcade.Text("PUNTAJE", px + 16, ALTO_VENTANA - 364,
                                               arcade.color.GOLD, 11, bold=True)
        self.txt_puntaje = arcade.Text(str(self.puntaje_total), px + 16, ALTO_VENTANA - 390,
                                        (200, 200, 200), 22, bold=True)
        self.txt_llave = arcade.Text("LLAVE: NO", px + 16, ALTO_VENTANA - 428,
                                      (200, 100, 100), 11, bold=True)
        self.txt_controles_titulo = arcade.Text("CONTROLES", px + 16, ALTO_VENTANA - 468,
                                                 arcade.color.GOLD, 11, bold=True)
        controles_texto = "WASD: mover\nR: reiniciar nivel\nN: reiniciar juego\nESC: menu" \
                          if self.controles == "wasd" else \
                          "Flechas: mover\nR: reiniciar nivel\nN: reiniciar juego\nESC: menu"
        self.txt_controles = arcade.Text(controles_texto, px + 16, ALTO_VENTANA - 540,
                                          (200, 200, 200), 10, multiline=True, width=pw - 32)
        self.txt_reiniciar = arcade.Text("R=nivel  N=inicio  ESC=menu",
                                          cx, 16, (120, 120, 120), 9, anchor_x="center")
        self.txt_victoria = arcade.Text(
            "¡NIVEL COMPLETADO!" if self.numero_nivel < 10 else "¡MISION CUMPLIDA!",
            ANCHO_JUEGO // 2, ALTO_VENTANA // 2 + 30,
            arcade.color.GOLD, 30, anchor_x="center", anchor_y="center", bold=True)
        self.txt_victoria_sub = arcade.Text(
            "Continuando..." if self.numero_nivel < 10 else "Presiona N para jugar de nuevo",
            ANCHO_JUEGO // 2, ALTO_VENTANA // 2 - 20,
            (200, 200, 200), 14, anchor_x="center", anchor_y="center")
        self.txt_perdido = arcade.Text("¡SIN PASOS!", ANCHO_JUEGO // 2, ALTO_VENTANA // 2 + 30,
                                        arcade.color.RED, 32, anchor_x="center", anchor_y="center", bold=True)
        self.txt_perdido_sub = arcade.Text("R=Reiniciar nivel  N=Desde el inicio",
                                            ANCHO_JUEGO // 2, ALTO_VENTANA // 2 - 20,
                                            (200, 200, 200), 14, anchor_x="center", anchor_y="center")

    def _tecla_arriba(self, symbol):
        return symbol == (arcade.key.W if self.controles == "wasd" else arcade.key.UP)

    def _tecla_abajo(self, symbol):
        return symbol == (arcade.key.S if self.controles == "wasd" else arcade.key.DOWN)

    def _tecla_izquierda(self, symbol):
        return symbol == (arcade.key.A if self.controles == "wasd" else arcade.key.LEFT)

    def _tecla_derecha(self, symbol):
        return symbol == (arcade.key.D if self.controles == "wasd" else arcade.key.RIGHT)

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
           if hasattr(self, 'musica_player') and self.musica_player:
               arcade.stop_sound(self.musica_player)
               self.musica_player = None
           from menu import Menu
           self.window.show_view(Menu())

    def on_key_release(self, symbol, modifiers):
        if symbol in (arcade.key.UP, arcade.key.DOWN, arcade.key.LEFT, arcade.key.RIGHT,
                      arcade.key.W, arcade.key.A, arcade.key.S, arcade.key.D):
            self.caminando = False
            self.frame_actual = 0

    def _intentar_recoger_llave(self):
        if self.pos_llave and (self.col, self.fila) == self.pos_llave and not self.tiene_llave:
            self.tiene_llave = True
            self.txt_llave.value = "LLAVE: SI"
            self.txt_llave.color = (100, 200, 100)
            for pos in self.puertas_llave:
                self.paredes.discard(pos)

    def _intentar_mover(self, dc, df):
        if self.ganado or self.perdido:
            return

        nc = self.col + dc
        nf = self.fila + df

        if not (0 <= nc < self.mapa_ancho and 0 <= nf < self.mapa_alto):
            arcade.play_sound(self.snd_no_mover)
            return
        if (nc, nf) in self.paredes:
            arcade.play_sound(self.snd_no_mover)
            return
        if (nc, nf) in self.sendero:
            arcade.play_sound(self.snd_no_mover)
            return

        self.col, self.fila = nc, nf
        self.direcciones[(nc, nf)] = (dc, df)
        self.sendero.add((nc, nf))
        self.pasos += 1
        self.txt_pasos.value = str(self.pasos)
        self.caminando = True
        arcade.play_sound(self.snd_mover)

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

        if (self.col, self.fila) in self.teleportes:
            destino = self.teleportes[(self.col, self.fila)]
            if destino not in self.sendero:
                self.col, self.fila = destino
                self.sendero.add(destino)
                self.pasos += 1
                self.txt_pasos.value = str(self.pasos)

        for placa in self.placas:
            if (self.col, self.fila) == placa["pos"]:
                for puerta in self.puertas_placa:
                    if puerta["id"] == placa["id"] and not puerta["abierta"]:
                        puerta["abierta"] = True
                        self.paredes.discard(puerta["pos"])

        if self.dificultad in ("medio", "dificil") and self.pasos_minimos:
            if self.pasos >= self.pasos_minimos * 2:
                self.perdido = True
                return

        if (self.col, self.fila) == self.portal:
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
        self.ganado = True
        self.puntaje_nivel = self._calcular_puntaje()
        self.puntaje_total += self.puntaje_nivel
        self.txt_puntaje.value = str(self.puntaje_total)
        guardado.actualizar_highscore(self.puntaje_total)
        arcade.play_sound(self.snd_victoria)
        for _ in range(80):
            self.particulas.append(Particula())

    def _calcular_puntaje(self):
        if not self.pasos_minimos:
            return 10
        ratio = self.pasos_minimos / max(self.pasos, 1)
        return max(1, min(10, round(ratio * 10)))

    def on_update(self, delta_time):
        self.animacion_portal += delta_time * 3.0
        self.timer_frame += 1
        if self.timer_frame >= self.velocidad_frame:
            self.timer_frame = 0
            self.frame_actual = (self.frame_actual + 1) % TOTAL_FRAMES
        # mover suavemente hacia la celda destino
        dest_x, dest_y = self._celda_a_px(self.col, self.fila)
        dx = dest_x - self.px_x
        dy = dest_y - self.px_y
        distancia = (dx**2 + dy**2) ** 0.5

        if distancia > self.velocidad_movimiento:
            self.px_x += dx / distancia * self.velocidad_movimiento
            self.px_y += dy / distancia * self.velocidad_movimiento
            self.moviendose = True
        else:
            self.px_x = dest_x
            self.px_y = dest_y
            self.moviendose = False

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

        self.timer_elementos += 1
        if self.timer_elementos >= self.velocidad_elementos:
            self.timer_elementos = 0
            self.frame_elementos = (self.frame_elementos + 1) % 9
        if self.camara:
            x, y = self._celda_a_px(self.col, self.fila)
            cam_x = max(ANCHO_JUEGO // 2, min(
                self.mapa_ancho * TAM_CELDA - ANCHO_JUEGO // 2 + TAM_CELDA *2, x
            ))
            self.camara.position = (cam_x, ALTO_JUEGO // 2)
        if self.mostrar_anuncio:
            self.timer_anuncio += 1
        if self.timer_anuncio >= 120:  # 2 segundos
            self.mostrar_anuncio = False

    def on_draw(self):
        self.window.clear((20, 28, 36))
        if self.camara:
            with self.camara.activate():
                if self.escena:
                    self.escena.draw()
                self._dibujar_sendero()
                self._dibujar_paredes()
                self._dibujar_hielo()
                self._dibujar_teleportes()
                self._dibujar_placas()
                self._dibujar_portal()
                self._dibujar_llave()
                self._dibujar_uaibot()
        else:
            self._dibujar_grilla()
            self._dibujar_sendero()
            self._dibujar_paredes()
            self._dibujar_hielo()
            self._dibujar_teleportes()
            self._dibujar_placas()
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
        x = col * TAM_CELDA + TAM_CELDA // 2
        y = fila * TAM_CELDA + TAM_CELDA // 2
        return x, y

    def _dibujar_grilla(self):
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
        for (col, fila) in self.hielo:
            if not spr.dibujar_celda(SPRITE_HIELO, col, fila, TAM_CELDA):
                arcade.draw_lrbt_rectangle_filled(
                    col * TAM_CELDA + 1, col * TAM_CELDA + TAM_CELDA - 1,
                    fila * TAM_CELDA + 1, fila * TAM_CELDA + TAM_CELDA - 1,
                    (135, 206, 235)
                )

    def _dibujar_teleportes(self):
        for (col, fila) in self.teleportes:
            x, y = self._celda_a_px(col, fila)
            frame = self.frames_teleporte[self.frame_elementos % len(self.frames_teleporte)]
            arcade.draw_texture_rect(
                frame,
                arcade.XYWH(x, y, TAM_CELDA, TAM_CELDA)
            )

    def _dibujar_placas(self):
        for placa in self.placas:
            col, fila = placa["pos"]
            if not spr.dibujar_celda(SPRITE_PLACA, col, fila, TAM_CELDA):
                arcade.draw_lrbt_rectangle_filled(
                    col * TAM_CELDA + 4, col * TAM_CELDA + TAM_CELDA - 4,
                    fila * TAM_CELDA + 4, fila * TAM_CELDA + TAM_CELDA - 4,
                    (200, 160, 0)
                )

    def _dibujar_portal(self):
        import math
        col, fila = self.portal
        x, y = self._celda_a_px(col, fila)
        es_ultimo = self.numero_nivel == 10

        if es_ultimo:
            arcade.draw_lrbt_rectangle_filled(
                col * TAM_CELDA + 1, col * TAM_CELDA + TAM_CELDA - 1,
                fila * TAM_CELDA + 1, fila * TAM_CELDA + TAM_CELDA - 1,
                (192, 57, 43, 180)
            )
            arcade.draw_texture_rect(self.img_merendero, arcade.XYWH(x, y, TAM_CELDA, TAM_CELDA))
        else:
            frame_portal = self.frames_portal[self.frame_elementos % len(self.frames_portal)]
            arcade.draw_texture_rect(
                frame_portal,
                arcade.XYWH(x, y, TAM_CELDA, TAM_CELDA)
            )

    def _dibujar_llave(self):
        if self.pos_llave and not self.tiene_llave:
            col, fila = self.pos_llave
            x, y = self._celda_a_px(col, fila)
            frame = self.frames_llave[self.frame_elementos % len(self.frames_llave)]
            arcade.draw_texture_rect(
                frame,
                arcade.XYWH(x, y, TAM_CELDA, TAM_CELDA)
            )

    def _dibujar_uaibot(self):
        x, y = self._celda_a_px(self.col, self.fila)
        frames = self.frames_walk if self.caminando else self.frames_idle
        arcade.draw_texture_rect(
            frames[self.frame_actual],
            arcade.XYWH(x, y, TAM_CELDA, TAM_CELDA)
        )
    def _dibujar_anuncio_nivel(self):
        import math
        alpha = int(255 * min(1.0, (120 - self.timer_anuncio) / 30))
        arcade.draw_lrbt_rectangle_filled(
            0, ANCHO_JUEGO, 0, ALTO_VENTANA, (0, 0, 0, 150)
        )
        arcade.Text(
            f"NIVEL {self.numero_nivel}",
            ANCHO_JUEGO // 2, ALTO_VENTANA // 2 + 20,
            (*arcade.color.GOLD[:3], alpha), 48,
            anchor_x="center", anchor_y="center", bold=True
        ).draw()
        arcade.Text(
            self.dificultad.upper(),
            ANCHO_JUEGO // 2, ALTO_VENTANA // 2 - 30,
            (*COLOR_ACENTO[:3], alpha), 18,
            anchor_x="center", anchor_y="center"
        ).draw()

    def _dibujar_panel(self):
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
        arcade.draw_lrbt_rectangle_filled(0, ANCHO_JUEGO, 0, ALTO_VENTANA, (0, 0, 0, 180))
        for p in self.particulas:
            p.dibujar()
        self.txt_victoria.draw()
        self.txt_victoria_sub.draw()
        arcade.Text(
             f"+{self.puntaje_nivel} puntos",
             ANCHO_JUEGO // 2, ALTO_VENTANA // 2 - 60,
            arcade.color.LIME_GREEN, 24,
            anchor_x="center", anchor_y="center", bold=True
        ).draw()

    def _dibujar_overlay_perdido(self):
        arcade.draw_lrbt_rectangle_filled(0, ANCHO_JUEGO, 0, ALTO_VENTANA, (0, 0, 0, 180))
        self.txt_perdido.draw()
        self.txt_perdido_sub.draw()