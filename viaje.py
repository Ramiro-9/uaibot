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
import panel as pnl
import sprites as spr
from constantes import *
from habilidades import Habilidades
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


class Viaje(Habilidades, Juego):
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

        # Donaciones de la campaña completa: se acumulan nivel a nivel para
        # la pantalla final (cuántas de las totales se entregaron).
        if numero_nivel == 1 or not hasattr(self, "donaciones_entregadas"):
            self.donaciones_entregadas = 0
            self.donaciones_campania   = 0

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

        # Los usos de las habilidades se recuperan en cada nivel. Va antes
        # de super() porque el movimiento y los textos del panel, que se
        # arman dentro de setup(), ya consultan este estado.
        self.iniciar_habilidades()

        super().setup(numero_nivel, puntaje_total)

    def _personaje_de_habilidad(self):
        """El mixin de habilidades pregunta por acá quién está jugando."""
        return self.personajes_disponibles[self.personaje_activo]

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
        # Contabilizar las donaciones del nivel que termina antes de pasar
        # al siguiente (que reemplaza la lista en setup).
        self.donaciones_entregadas += sum(1 for d in self.donaciones if d["recogida"])
        self.donaciones_campania   += len(self.donaciones)

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
        # El ícono de la sección PERSONAJE es el de la habilidad del que
        # está activo, así que hay que rehacer las secciones.
        self._acomodar_panel()

    def _actualizar_texto_personaje(self):
        """Refresca el bloque del panel: quién está activo y cuál es su habilidad."""
        personaje = self.personajes_disponibles[self.personaje_activo]
        total     = len(self.personajes_disponibles)
        self.txt_personaje.value = f"{personaje['nombre']}  ({total} en el equipo)"
        self.txt_personaje.color = personaje["color"]
        self.txt_habilidad.value = self.texto_habilidad()

    # ── Habilidades ───────────────────────────────────────────────────────────
    def _intentar_mover(self, dc, df):
        """Igual que en Juego, pero descontando el uso de la Rampa cuando
        el paso efectivamente cruzó una celda ya recorrida. Se hace después
        del movimiento y no durante la comprobación, para que el estado que
        guarda el deshacer sea el de ANTES de gastar el uso."""
        destino = (self.col + dc, self.fila + df)
        estaba_pisado = destino in self.sendero
        antes = (self.col, self.fila)

        super()._intentar_mover(dc, df)

        self.consumir_rampa_si_correspondia(estaba_pisado, (self.col, self.fila) != antes)
        self._recoger_donaciones()

    def _recoger_donaciones(self):
        """Suma las donaciones de la celda en la que quedó el personaje.

        Se recogen pisándolas, a diferencia de la llave (que necesita E):
        son varias por nivel y frenar el recorrido para confirmar cada una
        arruinaría el ritmo de exploración de la campaña. Al ir después del
        super(), ya cubre las celdas alcanzadas por hielo o teleporte."""
        recogi = False
        for d in self.donaciones:
            if not d["recogida"] and d["pos"] == (self.col, self.fila):
                d["recogida"] = True
                recogi = True
        if recogi:
            arcade.play_sound(self.snd_mover)
            self._actualizar_texto_donaciones()

    def _intentar_recoger_llave(self):
        """Igual que en Juego, pero contemplando el ALCANCE de UAIBOTINO,
        que puede tomar la llave desde una celda vecina sin pisarla —y así
        no gasta esa celda del sendero."""
        if not self.pos_llave or self.tiene_llave:
            return
        if self.pos_llave not in self.celdas_al_alcance(self.col, self.fila):
            return

        self._guardar_snapshot()
        self.tiene_llave = True
        self.txt_llave.value = "LLAVE: SI"
        self.txt_llave.color = (100, 200, 100)
        for pos in self.puertas_llave:
            self.paredes.discard(pos)
            if pos in self.anim_puertas_llave:
                self.anim_puertas_llave[pos]["animando"] = True

    def _actualizar_texto_donaciones(self):
        """Refresca el contador del panel; vacío si el nivel no tiene."""
        if self.donaciones:
            recogidas = sum(1 for d in self.donaciones if d["recogida"])
            self.txt_donaciones.value = f"Donaciones: {recogidas}/{len(self.donaciones)}"
        else:
            self.txt_donaciones.value = ""

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
            # Deshacer un paso hacia la izquierda tiene que devolver también
            # la orientación anterior, o el personaje queda mirando hacia
            # donde ya no caminó.
            "mirando_derecha": self.mirando_derecha,
            "cajas":       set(self.cajas),
            "paredes":     set(self.paredes),
            "tiene_llave": self.tiene_llave,
            "personaje_activo": self.personaje_activo,
            "puertas_placa":     [dict(p) for p in self.puertas_placa],
            "anim_puertas_llave": {pos: dict(e) for pos, e in self.anim_puertas_llave.items()},
            "anim_puertas_placa": {pos: dict(e) for pos, e in self.anim_puertas_placa.items()},
            # Las habilidades también se deshacen: si Z revierte el paso que
            # cruzó por la rampa, el uso tiene que volver a estar disponible.
            "usos_gastados": dict(self.usos_gastados),
            "rampa_armada":  self.rampa_armada,
            # Una donación se recoge al pisarla; deshacer ese paso tiene que
            # devolverla al mapa.
            "donaciones":   [dict(d) for d in self.donaciones],
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
        self.mirando_derecha = s["mirando_derecha"]
        self.cajas        = s["cajas"]
        self.paredes      = s["paredes"]
        self.tiene_llave  = s["tiene_llave"]
        self.personaje_activo   = s["personaje_activo"]
        self.usos_gastados      = s["usos_gastados"]
        self.rampa_armada       = s["rampa_armada"]
        self.donaciones         = s["donaciones"]
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
        self._actualizar_texto_donaciones()
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
            self.txt_mision.value = "Llega al portal. Recoge la llave con E."
        if self.donaciones:
            self.txt_mision.value += " Recoge las donaciones."

        # Textos propios de la campaña. Ninguno lleva Y: el orden en que
        # aparecen lo decide _secciones_panel.
        x = ANCHO_JUEGO + pnl.MARGEN_X
        self.txt_cronometro = pnl.crear_texto(
            f"Tiempo: {self.tiempo_transcurrido:.1f}s", x, 11, (100, 180, 220))
        self.txt_donaciones = pnl.crear_texto("", x, 10, (220, 180, 120), bold=True)
        self.txt_personaje  = pnl.crear_texto("", x, 11, (200, 200, 200), bold=True)
        self.txt_habilidad  = pnl.crear_texto("", x, 9, (150, 200, 150))
        self._actualizar_texto_personaje()
        self._actualizar_texto_donaciones()

        # Se rehace el bloque de controles para sumar C y Z.
        mover = "WASD" if self.controles == "wasd" else "Flechas"
        controles_texto = (f"{mover}: mover\n"
                           "C: personaje     Z: deshacer\n"
                           "R: reiniciar     ESC: menu")
        self.txt_controles.value = controles_texto

    def _secciones_panel(self):
        """Suma a las de Juego el cronómetro, las donaciones y el personaje
        activo. Insertar en el medio no obliga a mover nada de lo demás."""
        secciones = super()._secciones_panel()
        secciones.insert(2, pnl.Seccion("TIEMPO", [self.txt_cronometro,
                                                   self.txt_donaciones],
                                        icono=ICONO_RELOJ))
        habilidad = ICONOS_HABILIDAD.get(
            self.personajes_disponibles[self.personaje_activo]["habilidad"])
        secciones.insert(4, pnl.Seccion("PERSONAJE (C)",
                                        [self.txt_personaje, self.txt_habilidad],
                                        icono=habilidad))
        return secciones

    def _muestra_llave(self):
        """A diferencia de Infinito, la campaña muestra el indicador siempre
        que el mapa traiga una llave, sin importar la dificultad."""
        return bool(self.pos_llave)

    def _animacion_activa(self):
        """Frames y color del personaje activo.

        El color sale de la familia y no de constantes.py: un personaje con
        arte propio viene con tinte neutro, mientras que los que todavía
        reusan el spritesheet de UAIBOT vienen con su color para distinguirse."""
        return self.familia[self.personajes_disponibles[self.personaje_activo]["id"]]

    def _frames_activos(self):
        """Los frames del personaje activo: caminando o quieto."""
        datos = self._animacion_activa()
        return datos["walk"] if self.moviendose else datos["idle"]

    def _dibujar_uaibot(self):
        """Igual que en Juego, pero con el arte del personaje activo.

        El color va envuelto en arcade.types.Color y no como la tupla
        cruda de constantes.py, porque draw_texture_rect necesita el tipo
        propio de Arcade (una tupla suelta rompe al dibujar).

        La ruta que marca la Guía va primero: así queda sobre el piso y las
        huellas, pero por debajo del personaje."""
        self.dibujar_habilidades()
        frames = self._frames_activos()
        arcade.draw_texture_rect(
            spr.orientar(frames[self.frame_actual % len(frames)],
                         self.mirando_derecha),
            arcade.XYWH(self.px_x, self.px_y, TAM_CELDA, TAM_CELDA),
            color=arcade.types.Color(*self._animacion_activa()["color"])
        )

    # ── Actualización ─────────────────────────────────────────────────────────
    def on_update(self, delta_time):
        """Un cuadro de campaña: además del motor, corre el cronómetro."""
        super().on_update(delta_time)

        # El cronómetro corre mientras se está jugando: se congela al ganar
        # el nivel, al perder y al terminar la campaña.
        if not (self.ganado or self.perdido or self.juego_completado):
            self.tiempo_transcurrido += delta_time
        self.txt_cronometro.value = f"Tiempo: {self.tiempo_transcurrido:.1f}s"

        self.actualizar_habilidades(delta_time)

    # ── Eventos ───────────────────────────────────────────────────────────────
    def on_key_press(self, symbol, modifiers):
        """Suma a las teclas de Juego las propias de la campaña.

        C cambia de personaje entre los desbloqueados y Z deshace. Con la
        campaña terminada, R vuelve a empezar desde el nivel 1."""
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
            if symbol == arcade.key.SPACE:
                self.usar_habilidad((self.col, self.fila))
                return

        super().on_key_press(symbol, modifiers)

    # ── Dibujo ────────────────────────────────────────────────────────────────
    def on_draw(self):
        """Dibuja el nivel y encima el cartel de estado de las habilidades."""
        super().on_draw()
        # El cartel de estado de las habilidades va arriba de todo, para que
        # no lo tape ni el mapa ni el panel.
        if not (self.ganado or self.juego_completado):
            self.dibujar_aviso_habilidad()

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
        # Con donaciones en los mapas, el cierre muestra el real entregado;
        # si la campaña no tiene ninguna (todavía), queda el texto de siempre.
        if self.donaciones_campania:
            arcade.Text(f"Donaciones entregadas: {self.donaciones_entregadas}"
                        f"/{self.donaciones_campania}",
                        cx, cy + 20, (220, 180, 120), 13,
                        anchor_x="center", anchor_y="center").draw()
        else:
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
