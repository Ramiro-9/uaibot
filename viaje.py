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

        # Solo se puede jugar con los personajes ya desbloqueados. Se lee
        # el guardado en cada nivel (y no una sola vez al crear la vista)
        # porque un desbloqueo ocurre justo al terminar el nivel anterior.
        desbloqueados = guardado.cargar()["personajes_desbloqueados"]
        self.personajes_disponibles = [
            p for p in PERSONAJES_FAMILIA if p["id"] in desbloqueados
        ]
        self.personaje_activo = 0

        # Pila de estados para el deshacer con Z. Se vacía en cada nivel:
        # no tiene sentido deshacer hacia un nivel que ya quedó atrás.
        self.historial = []

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

    # ── Cambio de personaje (tecla C) ─────────────────────────────────────────
    def _cambiar_personaje(self):
        """Pasa al siguiente personaje desbloqueado. A diferencia de
        Tutorial, acá no hay cupo de pasos: se cambia libremente, y lo que
        limita quiénes están disponibles es cuánto se avanzó en la campaña."""
        if len(self.personajes_disponibles) < 2:
            # Todavía no se desbloqueó nadie más que UAIBOT.
            arcade.play_sound(self.snd_no_mover)
            return

        self._guardar_snapshot()
        self.personaje_activo = (self.personaje_activo + 1) % len(self.personajes_disponibles)
        self._actualizar_texto_personaje()

    def _actualizar_texto_personaje(self):
        personaje = self.personajes_disponibles[self.personaje_activo]
        total     = len(self.personajes_disponibles)
        self.txt_personaje.value = f"{personaje['nombre']}  ({total} en el equipo)"
        self.txt_personaje.color = personaje["color"]

    # ── Deshacer (tecla Z) ────────────────────────────────────────────────────
    def _guardar_snapshot(self):
        """Guarda el estado del nivel antes de una acción reversible.

        Juego llama a este método justo antes de mover, de recoger la
        llave y -acá- de cambiar de personaje. Se copian solo los datos
        que una acción puede modificar; las capas de sprites no se
        guardan, se reconstruyen al restaurar.

        Ojo con lo que muta una sola jugada en este modo: además de la
        posición y el sendero, pisar una placa o recoger la llave sacan
        celdas de self.paredes (la puerta se abre) y arrancan la animación
        de esa puerta, así que todo eso también entra en el snapshot."""
        self.historial.append({
            "col": self.col,
            "fila": self.fila,
            "sendero":     set(self.sendero),
            "direcciones": dict(self.direcciones),
            "pasos":       self.pasos,
            "cajas":       set(self.cajas),
            "paredes":     set(self.paredes),
            "tiene_llave": self.tiene_llave,
            "personaje_activo": self.personaje_activo,
            "puertas_placa":     [dict(p) for p in self.puertas_placa],
            "anim_puertas_llave": {pos: dict(e) for pos, e in self.anim_puertas_llave.items()},
            "anim_puertas_placa": {pos: dict(e) for pos, e in self.anim_puertas_placa.items()},
        })

    def _deshacer(self):
        """Vuelve al estado anterior de la pila y rearma las capas visuales
        para que no queden huellas ni cajas de un estado que ya no existe."""
        if not self.historial:
            arcade.play_sound(self.snd_no_mover)
            return

        s = self.historial.pop()
        self.col          = s["col"]
        self.fila         = s["fila"]
        self.sendero      = s["sendero"]
        self.direcciones  = s["direcciones"]
        self.pasos        = s["pasos"]
        self.cajas        = s["cajas"]
        self.paredes      = s["paredes"]
        self.tiene_llave  = s["tiene_llave"]
        self.personaje_activo   = s["personaje_activo"]
        self.puertas_placa      = s["puertas_placa"]
        self.anim_puertas_llave = s["anim_puertas_llave"]
        self.anim_puertas_placa = s["anim_puertas_placa"]

        self._reconstruir_sendero_sprites()
        self._reconstruir_cajas_sprites()

        # La posición en píxeles se reubica de golpe: al deshacer no
        # corresponde animar el desplazamiento hacia atrás.
        self.px_x, self.px_y = self._celda_a_px(self.col, self.fila)

        self.txt_pasos.value = str(self.pasos)
        self.txt_llave.value = "LLAVE: SI" if self.tiene_llave else "LLAVE: NO"
        self.txt_llave.color = (100, 200, 100) if self.tiene_llave else (200, 100, 100)
        self._actualizar_texto_personaje()

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

        # Personaje activo, con el nombre en su color. Se mete entre el
        # puntaje y los controles, y para eso hay que correr el indicador
        # de llave un poco más abajo del lugar donde lo pone Juego.
        self.txt_personaje_titulo = arcade.Text(
            "PERSONAJE (C)", ANCHO_JUEGO + 16, ALTO_VENTANA - 410,
            arcade.color.GOLD, 11, bold=True
        )
        self.txt_personaje = arcade.Text(
            "", ANCHO_JUEGO + 16, ALTO_VENTANA - 428, (200, 200, 200), 11, bold=True
        )
        self.txt_llave.y = ALTO_VENTANA - 448
        self._actualizar_texto_personaje()

        # Se rehace el bloque de controles para sumar C y Z.
        controles_texto = (
            "WASD: mover\nC: cambiar personaje\nZ: deshacer\nR: reiniciar nivel\nESC: menu"
            if self.controles == "wasd" else
            "Flechas: mover\nC: cambiar personaje\nZ: deshacer\nR: reiniciar nivel\nESC: menu"
        )
        self.txt_controles.value = controles_texto

    def _dibujar_panel(self):
        super()._dibujar_panel()
        self.txt_cronometro.draw()
        self.txt_personaje_titulo.draw()
        self.txt_personaje.draw()
        # Juego solo dibuja el indicador de llave en dificultad difícil;
        # en la campaña se muestra siempre que el nivel tenga una llave.
        if self.pos_llave:
            self.txt_llave.draw()

    def _dibujar_uaibot(self):
        """Igual que en Juego, pero tiñendo el sprite con el color del
        personaje activo: los cuatro comparten el mismo spritesheet.

        El color va envuelto en arcade.types.Color y no como la tupla
        cruda de constantes.py, porque draw_texture_rect necesita el tipo
        propio de Arcade (una tupla suelta rompe al dibujar)."""
        frames = self.frames_walk if self.moviendose else self.frames_idle
        arcade.draw_texture_rect(
            frames[self.frame_actual],
            arcade.XYWH(self.px_x, self.px_y, TAM_CELDA, TAM_CELDA),
            color=arcade.types.Color(*self.personajes_disponibles[self.personaje_activo]["color"])
        )

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

        if not (self.ganado or self.perdido):
            if symbol == arcade.key.C:
                self._cambiar_personaje()
                return
            if symbol == arcade.key.Z:
                self._deshacer()
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
