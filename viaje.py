# viaje.py
# Modo Viaje: la campaña del juego. A diferencia del Modo Infinito, son 10
# niveles fijos diseñados a mano en Tiled, con final, y a medida que se
# avanza se van desbloqueando los personajes de la familia de UAIBOT.
#
# Hereda de Juego (juego.py) porque comparte casi todo con el Modo Infinito:
# el movimiento en grilla, las colisiones, el sendero que no se puede
# repisar, el hielo, los teleportes, la llave, las puertas con placa, la
# cámara para mapas más anchos que la pantalla, las animaciones y el panel
# lateral. Solo cambia lo que está sobrescrito acá abajo, que son las
# "costuras" marcadas como tales en juego.py.

import arcade

import guardado
import nivel as nivel_mod
from constantes import *
from juego import Juego

# Los 20 mapas de Tiled se reparten entre dos modos: los 10 de dificultad
# media son la campaña de Viaje, y los 10 de dificultad difícil quedan
# reservados para el Modo Multijugador.
DIFICULTAD_MAPAS = "medio"
TOTAL_NIVELES    = 10

# En qué nivel se desbloquea cada integrante de la familia. UAIBOT no está
# en la tabla porque es el personaje inicial, siempre disponible.
PERSONAJES_POR_NIVEL = {
    2: "uaibotino",
    5: "uaibota",
    8: "uaibotina",
}


class Viaje(Juego):
    """Campaña de 10 niveles fijos con desbloqueo de personajes."""

    # ── Setup ─────────────────────────────────────────────────────────────────
    def setup(self, numero_nivel=1, puntaje_total=0):
        """Prepara un nivel de la campaña.

        El cronómetro mide la partida COMPLETA, no cada nivel por separado:
        por eso solo se pone en cero al empezar desde el nivel 1, y se
        mantiene al pasar de un nivel al siguiente. Se inicializa antes de
        llamar a super() porque _crear_textos() -que corre dentro de
        setup()- ya lo necesita para armar el texto del panel."""
        if numero_nivel == 1 or not hasattr(self, "tiempo_transcurrido"):
            self.tiempo_transcurrido = 0.0

        self.juego_completado      = False
        self.personaje_desbloqueado = None   # se muestra al ganar el nivel

        super().setup(numero_nivel, puntaje_total)

    # ── Costuras: en qué se aparta Viaje del Modo Infinito ────────────────────
    def _dificultad_del_nivel(self, numero_nivel):
        """Viaje no escala la dificultad: los 10 niveles son los mapas de
        dificultad media, y la progresión la da el diseño de cada mapa."""
        return DIFICULTAD_MAPAS

    def _obtener_datos_nivel(self):
        """Carga el mapa .tmx dibujado a mano que le corresponde al nivel."""
        return nivel_mod.generar_nivel(self.numero_nivel, DIFICULTAD_MAPAS, usar_tiled=True)

    def _hay_que_perder_por_pasos(self):
        """Viaje no tiene límite de pasos: es una campaña para recorrer y
        explorar, no una prueba de eficiencia como el Modo Infinito."""
        return False

    def _avanzar_de_nivel(self):
        """A diferencia de Infinito, la campaña termina: al completar el
        último nivel no se genera uno nuevo, se marca el juego como
        terminado y se muestra la pantalla final."""
        if self.numero_nivel < TOTAL_NIVELES:
            self.setup(self.numero_nivel + 1, self.puntaje_total)
        else:
            self.juego_completado = True

    def _guardar_progreso(self):
        """Guarda hasta dónde llegó la campaña y desbloquea el personaje
        que corresponda a este nivel, si es que hay uno."""
        guardado.actualizar_progreso_viaje(
            self.numero_nivel,
            completado=(self.numero_nivel >= TOTAL_NIVELES)
        )

        id_personaje = PERSONAJES_POR_NIVEL.get(self.numero_nivel)
        if id_personaje:
            guardado.desbloquear_personaje(id_personaje)
            self.personaje_desbloqueado = id_personaje.upper()

    # ── Panel lateral ─────────────────────────────────────────────────────────
    def _crear_textos(self):
        """Reutiliza todos los textos del panel que arma Juego y ajusta solo
        lo que Viaje muestra distinto, en vez de duplicar el método entero."""
        super()._crear_textos()

        # La campaña sí tiene un total de niveles conocido.
        self.txt_nivel.value = f"Nivel {self.numero_nivel}/{TOTAL_NIVELES}"

        # Sin límite de pasos: se vacía el texto que Juego arma para las
        # dificultades media y difícil del Modo Infinito.
        self.txt_limite.value = ""

        # Los mapas de la campaña tienen llave y puertas con llave, así que
        # conviene avisarlo aunque no sea dificultad "difícil".
        if self.pos_llave:
            self.txt_mision.value = "Llega al portal\npara avanzar.\nRecoge la llave\ncon E."

        # Cronómetro (consigna de la Ronda 2), en el hueco que dejó el
        # texto del límite de pasos.
        self.txt_cronometro = arcade.Text(
            f"Tiempo: {self.tiempo_transcurrido:.1f}s",
            ANCHO_JUEGO + 16, ALTO_VENTANA - 334, (100, 180, 220), 11
        )

    def _dibujar_panel(self):
        super()._dibujar_panel()
        self.txt_cronometro.draw()
        # Juego solo dibuja el indicador de llave en dificultad difícil;
        # en la campaña se muestra siempre que el nivel tenga una llave.
        if self.pos_llave:
            self.txt_llave.draw()

    # ── Actualización ─────────────────────────────────────────────────────────
    def on_update(self, delta_time):
        super().on_update(delta_time)

        # El cronómetro corre mientras se está jugando: se congela al ganar
        # el nivel, al perder y al terminar la campaña.
        if not (self.ganado or self.perdido or self.juego_completado):
            self.tiempo_transcurrido += delta_time
        self.txt_cronometro.value = f"Tiempo: {self.tiempo_transcurrido:.1f}s"

    # ── Eventos ───────────────────────────────────────────────────────────────
    def on_key_press(self, symbol, modifiers):
        # Terminada la campaña, R y N vuelven a empezar desde el nivel 1
        # (en Juego, R reiniciaría el último nivel).
        if self.juego_completado and symbol in (arcade.key.R, arcade.key.N):
            self.setup(1, 0)
            return
        super().on_key_press(symbol, modifiers)

    # ── Dibujo ────────────────────────────────────────────────────────────────
    def _dibujar_overlay_victoria(self):
        """Al completar el último nivel muestra la pantalla de fin de
        campaña; en los demás, el overlay normal de Juego más el aviso de
        personaje desbloqueado si hubo uno."""
        if self.juego_completado:
            self._dibujar_overlay_final()
            return

        super()._dibujar_overlay_victoria()
        if self.personaje_desbloqueado:
            arcade.Text(
                f"¡{self.personaje_desbloqueado} se suma al equipo!",
                ANCHO_JUEGO // 2, ALTO_VENTANA // 2 - 100,
                arcade.color.GOLD, 16,
                anchor_x="center", anchor_y="center", bold=True
            ).draw()

    def _dibujar_overlay_final(self):
        """Pantalla de fin de campaña, con el tiempo total y el puntaje."""
        arcade.draw_lrbt_rectangle_filled(0, ANCHO_JUEGO, 0, ALTO_VENTANA, (0, 0, 0, 200))
        for p in self.particulas:
            p.dibujar()

        cx, cy = ANCHO_JUEGO // 2, ALTO_VENTANA // 2
        arcade.Text("¡VIAJE COMPLETADO!", cx, cy + 60, arcade.color.GOLD, 32,
                    anchor_x="center", anchor_y="center", bold=True).draw()
        arcade.Text("UAIBOT y su familia entregaron todas las donaciones",
                    cx, cy + 20, (200, 200, 200), 13,
                    anchor_x="center", anchor_y="center").draw()
        arcade.Text(f"Tiempo total: {self.tiempo_transcurrido:.1f}s", cx, cy - 20,
                    arcade.color.LIME_GREEN, 16,
                    anchor_x="center", anchor_y="center", bold=True).draw()
        arcade.Text(f"Puntaje: {self.puntaje_total}", cx, cy - 48,
                    arcade.color.LIME_GREEN, 16,
                    anchor_x="center", anchor_y="center", bold=True).draw()
        arcade.Text("R: jugar de nuevo   ESC: volver al menu", cx, cy - 90,
                    (150, 150, 150), 12, anchor_x="center", anchor_y="center").draw()
