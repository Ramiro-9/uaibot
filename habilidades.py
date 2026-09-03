# habilidades.py
# Las habilidades propias de cada integrante de la familia de UAIBOT.
#
# Están planteadas como TECNOLOGÍA ASISTIVA: cosas que quitan barreras y
# hacen accesible lo que no lo era, que es el eje del certamen (inclusión
# social con tecnología). Ninguna representa una limitación del personaje.
#
# Las cuatro, definidas en constantes.PERSONAJES_FAMILIA:
#
#   UAIBOT     Carga    empuja cajas para mover las donaciones   (pasiva)
#   UAIBOTA    Rampa    cruza una celda ya recorrida, 1 vez/nivel (ESPACIO)
#   UAIBOTINA  Guia     señaliza la ruta que queda al merendero   (ESPACIO)
#   UAIBOTINO  Alcance  recoge desde una celda vecina             (pasiva)
#
# Las pasivas no tienen tecla: con ese personaje activo simplemente
# funcionan. Las activas van con ESPACIO, porque C ya cambia de personaje.
#
# ── Por qué esto es un mixin y no parte de Juego ─────────────────────────
# Las habilidades las usan Modo Viaje y Multijugador, pero NO Modo
# Infinito, y esos tres comparten la clase Juego. Meterlas ahí obligaría a
# tocar la clase más delicada del proyecto -ya verificada y entregada- para
# algo que uno de sus modos no usa. Como mixin, los dos modos que las
# necesitan hacen:
#
#     class Viaje(Habilidades, Juego)
#     class Multijugador(Habilidades, Juego)
#
# y el modo Infinito queda exactamente como estaba.

import arcade

import nivel as nivel_mod
from constantes import ALTO_VENTANA, ANCHO_JUEGO, TAM_CELDA

# Cuántos segundos queda dibujada la ruta que muestra la Guía.
DURACION_GUIA = 6.0

COLOR_RUTA_GUIA = (241, 196, 15, 130)   # amarillo translúcido sobre el piso
COLOR_RAMPA     = (255, 170, 210)       # el rosa de UAIBOTA


class Habilidades:
    """Mixin con las habilidades de los personajes.

    Pide una sola cosa al modo que lo use: `_personaje_de_habilidad()`,
    que devuelve el diccionario del personaje activo (el mismo formato de
    constantes.PERSONAJES_FAMILIA). El resto lo resuelve acá."""

    # ── Ciclo de vida ─────────────────────────────────────────────────────
    def iniciar_habilidades(self):
        """Reinicia el estado de las habilidades. Se llama al preparar cada
        nivel: los usos se recuperan al cambiar de nivel, no se arrastran."""
        self.usos_gastados   = {}      # id de personaje -> usos ya hechos
        self.rampa_armada    = False   # el próximo paso cruza el sendero
        self.ruta_guia       = []      # celdas que la Guía está mostrando
        self.timer_guia      = 0.0
        self.aviso_habilidad = ""      # mensaje corto en pantalla
        self.timer_aviso     = 0.0

    def _personaje_de_habilidad(self):
        """Lo implementa cada modo: en Viaje es el personaje seleccionado
        con C, en Multijugador es el que le tocó a este jugador."""
        raise NotImplementedError

    # ── Consultas ─────────────────────────────────────────────────────────
    def _usos_restantes(self):
        """Cuántos usos le quedan a la habilidad del personaje actual.

        None significa que no tiene límite."""
        personaje = self._personaje_de_habilidad()
        tope = personaje.get("usos_por_nivel")
        if tope is None:
            return None
        return tope - self.usos_gastados.get(personaje["id"], 0)

    def _gastar_uso(self):
        """Anota un uso más de la habilidad del personaje activo."""
        personaje = self._personaje_de_habilidad()
        self.usos_gastados[personaje["id"]] = self.usos_gastados.get(personaje["id"], 0) + 1

    def _mostrar_aviso(self, texto):
        """Muestra un cartelito al pie durante unos segundos."""
        self.aviso_habilidad = texto
        self.timer_aviso     = 2.5

    # ── Habilidades pasivas ───────────────────────────────────────────────
    def _puede_empujar_cajas(self):
        """CARGA (UAIBOT). Sobrescribe la costura de Juego: solo UAIBOT
        tiene la fuerza para mover las cajas de donaciones."""
        return self._personaje_de_habilidad()["habilidad"] == "carga"

    def _tiene_alcance(self):
        """ALCANCE (UAIBOTINO): puede recoger cosas de una celda vecina sin
        pisarla, así no gasta esa celda del sendero."""
        return self._personaje_de_habilidad()["habilidad"] == "alcance"

    def celdas_al_alcance(self, col, fila):
        """Las celdas desde las que el personaje actual puede recoger algo:

        la propia siempre, y las cuatro vecinas si tiene Alcance."""
        celdas = [(col, fila)]
        if self._tiene_alcance():
            celdas += [(col + dc, fila + df) for dc, df in ((0, 1), (0, -1), (1, 0), (-1, 0))]
        return celdas

    # ── Rampa (activa) ────────────────────────────────────────────────────
    def _sendero_bloquea(self, nc, nf):
        """Sobrescribe la regla central del juego: con la Rampa armada se
        puede cruzar una celda ya recorrida. Es el único punto de todo el
        proyecto donde esa regla cede, y por eso la Rampa está limitada.

        A propósito NO gasta el uso acá: esto es una consulta, y el juego
        la hace antes de guardar el estado para el deshacer. Si el uso se
        descontara en este punto, el snapshot ya lo tomaría gastado y la
        tecla Z no podría devolverlo. Se consume después del movimiento,
        con consumir_rampa_si_correspondia()."""
        return (nc, nf) in self.sendero and not self.rampa_armada

    def consumir_rampa_si_correspondia(self, destino_estaba_pisado, se_movio):
        """La llama el modo justo después de un movimiento. Si el paso
        entró a una celda ya recorrida y la Rampa estaba armada, es que se
        usó: recién ahí se descuenta."""
        if not (self.rampa_armada and destino_estaba_pisado and se_movio):
            return
        self.rampa_armada = False
        self._gastar_uso()
        self._mostrar_aviso("Rampa usada")

    def _usar_rampa(self):
        """Arma la Rampa: deja que el próximo paso cruce una celda ya recorrida.

        No se gasta el uso acá sino al cruzar de verdad (ver
        consumir_rampa_si_correspondia), para no cobrarle al jugador un
        uso si arma la rampa y después se arrepiente."""
        if self.rampa_armada:
            self.rampa_armada = False
            self._mostrar_aviso("Rampa cancelada")
            return
        if self._usos_restantes() == 0:
            self._mostrar_aviso("Rampa ya usada en este nivel")
            return
        self.rampa_armada = True
        self._mostrar_aviso("Rampa lista: cruza el camino recorrido")

    # ── Guía (activa) ─────────────────────────────────────────────────────
    def _usar_guia(self, desde):
        """Calcula la ruta que todavía queda hasta el merendero SIN volver a
        pisar el camino recorrido, y la deja marcada unos segundos.

        Como respeta el sendero, cuando no encuentra ninguna ruta significa
        que el jugador quedó realmente trabado: se lo avisa, que es más útil
        que dejarlo dando vueltas sin saber que ya no puede ganar."""
        # Las puertas arrancan cerradas y por eso figuran como pared, pero
        # el jugador las va a abrir con la llave o la placa: si no se las
        # descontara, la Guía diría "no hay camino" en todo nivel que tenga
        # una puerta, que son casi todos.
        puertas  = set(self.puertas_llave) | {p["pos"] for p in self.puertas_placa}
        gastadas = set(self.sendero) - {desde}
        ruta = nivel_mod._camino_mas_corto(
            desde, self.portal, (self.paredes - puertas) | gastadas,
            self.mapa_ancho, self.mapa_alto
        )
        if ruta is None:
            self.ruta_guia = []
            self._mostrar_aviso("No queda camino: reinicia con R")
            return
        self.ruta_guia  = ruta
        self.timer_guia = DURACION_GUIA
        self._mostrar_aviso(f"Faltan {len(ruta) - 1} pasos")

    # ── Punto de entrada de las activas ───────────────────────────────────
    def usar_habilidad(self, desde):
        """La llama el modo cuando se aprieta ESPACIO. `desde` es la celda
        donde está parado el jugador."""
        habilidad = self._personaje_de_habilidad()["habilidad"]
        if habilidad == "rampa":
            self._usar_rampa()
        elif habilidad == "guia":
            self._usar_guia(desde)
        else:
            # Carga y Alcance son pasivas: no hay nada que activar.
            self._mostrar_aviso("Esta habilidad funciona sola")

    # ── Actualización y dibujo ────────────────────────────────────────────
    def actualizar_habilidades(self, delta_time):
        """Descuenta el tiempo que le queda a los avisos en pantalla."""
        if self.timer_guia > 0:
            self.timer_guia -= delta_time
            if self.timer_guia <= 0:
                self.ruta_guia = []
        if self.timer_aviso > 0:
            self.timer_aviso -= delta_time
            if self.timer_aviso <= 0:
                self.aviso_habilidad = ""

    def dibujar_habilidades(self):
        """Marca la ruta de la Guía y el borde de la celda cuando la Rampa
        está armada. Va después del mapa y antes de los personajes."""
        for (col, fila) in self.ruta_guia:
            arcade.draw_lrbt_rectangle_filled(
                col * TAM_CELDA + 18, col * TAM_CELDA + TAM_CELDA - 18,
                fila * TAM_CELDA + 18, fila * TAM_CELDA + TAM_CELDA - 18,
                COLOR_RUTA_GUIA
            )

    def dibujar_aviso_habilidad(self):
        """El cartelito de estado, sobre el área de juego. Se dibuja al
        final, junto con el resto de la interfaz."""
        if self.rampa_armada:
            arcade.Text("RAMPA LISTA", ANCHO_JUEGO // 2, ALTO_VENTANA - 28,
                        arcade.types.Color(*COLOR_RAMPA), 14,
                        anchor_x="center", bold=True).draw()
        if self.aviso_habilidad:
            arcade.Text(self.aviso_habilidad, ANCHO_JUEGO // 2, 20,
                        arcade.color.WHITE, 12, anchor_x="center", bold=True).draw()

    def texto_habilidad(self):
        """Una sola línea para el panel lateral: qué habilidad tiene, qué
        hace y -si tiene tope- cuántos usos le quedan. Va en una línea
        porque el panel ya está bastante cargado."""
        personaje = self._personaje_de_habilidad()
        restantes = self._usos_restantes()
        sufijo = "" if restantes is None else f" [{restantes}]"
        return f"{personaje['habilidad_nombre']}{sufijo}: {personaje['habilidad_desc']}"
