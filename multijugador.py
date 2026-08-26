# multijugador.py
# Modo Multijugador cooperativo para dos jugadores en red local.
#
# Contiene dos vistas:
#   - SalaMultijugador: la pantalla previa donde uno crea la partida y el
#     otro se une escribiendo su IP.
#   - Multijugador: la partida en sí, que hereda de Juego para reutilizar
#     la carga de mapas de Tiled, la cámara, el dibujo de puertas,
#     teleportes y placas, y el panel lateral.
#
# ── Quién manda ──────────────────────────────────────────────────────────
# El modelo es HOST AUTORITATIVO: el que creó la partida tiene el estado
# real del nivel. El cliente no simula nada — manda "quiero moverme en esta
# dirección" y dibuja lo que el host le contesta.
#
# Después de cada cambio, el host manda el estado COMPLETO (posiciones,
# sendero, puertas abiertas, pasos) en vez de mandar solo lo que cambió.
# Es más tráfico, pero en una red local con un juego de grilla es
# despreciable, y evita de raíz el bug más difícil de perseguir en un
# multijugador: que las dos pantallas se vayan desincronizando de a poco
# sin que se sepa cuál de las dos tiene razón.
#
# El mapa no viaja por la red: los dos lados tienen los mismos archivos
# .tmx, así que alcanza con que el host diga qué número de nivel es.
#
# ── Por qué la lógica de movimiento está acá y no en Juego ───────────────
# Juego._intentar_mover está escrito sobre un único self.col/self.fila.
# Para dos jugadores hace falta una versión que reciba de quién se trata.
# Se adapta acá en vez de generalizar Juego, porque Juego es la base de
# Infinito y de Viaje -ya verificados y entregados- y su método de
# movimiento es el más delicado de todo el proyecto.

import arcade

import guardado
import nivel as nivel_mod
import red
import sprites as spr
from constantes import *
from habilidades import Habilidades
from juego import Juego

DIFICULTAD_MAPAS = "dificil"   # los 10 mapas reservados para este modo
TOTAL_NIVELES    = 10

# Los dos personajes que se reparten los jugadores. Se toman de la familia
# ya definida en constantes.py, así el color con el que se dibuja cada uno
# es el mismo que usan Tutorial y Viaje.
JUGADORES = [PERSONAJES_FAMILIA[0], PERSONAJES_FAMILIA[1]]   # UAIBOT y UAIBOTA


class SalaMultijugador(arcade.View):
    """Pantalla previa a la partida: crear una o unirse a una existente.

    El descubrimiento automático por UDP está previsto para más adelante;
    por ahora el que se une escribe la IP que le muestra el host. Es la
    parte que nunca falla, ni con firewall ni con redes que aíslan los
    dispositivos entre sí."""

    def __init__(self, controles="flechas"):
        super().__init__()
        self.controles = controles
        self.estado    = "menu"      # menu | esperando | escribiendo_ip | error
        self.opcion    = 0           # 0 = crear, 1 = unirse
        self.ip_escrita = ""
        self.mensaje_error = ""
        self.servidor = None
        self.cliente  = None

    # ── Eventos ───────────────────────────────────────────────────────────
    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.ESCAPE:
            self._volver_al_menu()
            return

        if self.estado == "menu":
            if symbol in (arcade.key.UP, arcade.key.DOWN):
                self.opcion = 1 - self.opcion
            elif symbol == arcade.key.ENTER:
                self._crear_partida() if self.opcion == 0 else self._pedir_ip()

        elif self.estado == "escribiendo_ip":
            if symbol == arcade.key.ENTER:
                self._unirse()
            elif symbol == arcade.key.BACKSPACE:
                self.ip_escrita = self.ip_escrita[:-1]

        elif self.estado == "error":
            self.estado = "menu"

    def on_text(self, text):
        """Solo se aceptan números y puntos: es una dirección IP."""
        if self.estado == "escribiendo_ip" and text in "0123456789." and len(self.ip_escrita) < 15:
            self.ip_escrita += text

    def _volver_al_menu(self):
        if self.servidor:
            self.servidor.cerrar()
        if self.cliente:
            self.cliente.cerrar()
        from menu import Menu
        self.window.show_view(Menu())

    # ── Crear / unirse ────────────────────────────────────────────────────
    def _crear_partida(self):
        self.servidor = red.Servidor()
        if self.servidor.error:
            self.estado = "error"
            self.mensaje_error = self.servidor.error
            return
        self.estado = "esperando"

    def _pedir_ip(self):
        self.estado = "escribiendo_ip"
        self.ip_escrita = ""

    def _unirse(self):
        self.cliente = red.Cliente(self.ip_escrita.strip() or "127.0.0.1")
        if self.cliente.error:
            self.estado = "error"
            self.mensaje_error = self.cliente.error
            return
        self._empezar_partida(self.cliente, es_host=False)

    def _empezar_partida(self, conexion, es_host):
        vista = Multijugador(controles=self.controles, conexion=conexion, es_host=es_host)
        vista.setup()
        self.window.show_view(vista)

    def on_update(self, delta_time):
        # El host espera acá hasta que alguien se conecta. La detección la
        # hace el hilo de red; acá solo se consulta la bandera, que es una
        # operación instantánea y no frena el dibujado.
        if self.estado == "esperando" and self.servidor.hay_jugador:
            self._empezar_partida(self.servidor, es_host=True)

    # ── Dibujo ────────────────────────────────────────────────────────────
    def on_draw(self):
        self.window.clear((20, 28, 36))
        cx, cy = ANCHO_VENTANA // 2, ALTO_VENTANA // 2

        arcade.Text("MULTIJUGADOR", cx, ALTO_VENTANA - 80, arcade.color.GOLD, 34,
                    anchor_x="center", bold=True).draw()

        if self.estado == "menu":
            self._dibujar_menu(cx, cy)
        elif self.estado == "esperando":
            self._dibujar_esperando(cx, cy)
        elif self.estado == "escribiendo_ip":
            self._dibujar_pedir_ip(cx, cy)
        elif self.estado == "error":
            self._dibujar_error(cx, cy)

        arcade.Text("ESC para volver al menu", cx, 30, (120, 120, 120), 11,
                    anchor_x="center").draw()

    def _dibujar_menu(self, cx, cy):
        opciones = ["Crear partida", "Unirse a una partida"]
        for i, texto in enumerate(opciones):
            elegida = (i == self.opcion)
            arcade.Text(("> " if elegida else "   ") + texto,
                        cx, cy + 30 - i * 44,
                        arcade.color.WHITE if elegida else (150, 150, 150),
                        20, anchor_x="center", bold=elegida).draw()
        arcade.Text("Los dos tienen que estar en la misma red",
                    cx, cy - 80, (150, 150, 150), 12, anchor_x="center").draw()
        arcade.Text("Para probar en una sola PC: abri el juego dos veces y usa 127.0.0.1",
                    cx, cy - 102, (110, 110, 110), 11, anchor_x="center").draw()

    def _dibujar_esperando(self, cx, cy):
        arcade.Text("Esperando al otro jugador...", cx, cy + 40, arcade.color.WHITE, 20,
                    anchor_x="center", bold=True).draw()
        arcade.Text("Que se una con esta direccion:", cx, cy - 10, (180, 180, 180), 13,
                    anchor_x="center").draw()
        arcade.Text(red.ip_local(), cx, cy - 50, arcade.color.GOLD, 30,
                    anchor_x="center", bold=True).draw()
        arcade.Text("(en la misma PC: 127.0.0.1)", cx, cy - 84, (120, 120, 120), 11,
                    anchor_x="center").draw()

    def _dibujar_pedir_ip(self, cx, cy):
        arcade.Text("Escribi la IP del que creo la partida:", cx, cy + 40,
                    arcade.color.WHITE, 16, anchor_x="center").draw()
        arcade.Text(self.ip_escrita + "_", cx, cy - 10, arcade.color.GOLD, 28,
                    anchor_x="center", bold=True).draw()
        arcade.Text("ENTER para conectar   (vacio = 127.0.0.1)", cx, cy - 60,
                    (150, 150, 150), 12, anchor_x="center").draw()

    def _dibujar_error(self, cx, cy):
        arcade.Text("No se pudo conectar", cx, cy + 30, arcade.color.RED, 22,
                    anchor_x="center", bold=True).draw()
        arcade.Text(self.mensaje_error, cx, cy - 10, (200, 200, 200), 11,
                    anchor_x="center", multiline=True, width=560).draw()
        arcade.Text("Cualquier tecla para volver", cx, cy - 70, (150, 150, 150), 12,
                    anchor_x="center").draw()


class Multijugador(Habilidades, Juego):
    """La partida cooperativa. Hereda de Juego todo el dibujo del mapa y
    reemplaza el movimiento por una versión de dos jugadores sincronizada
    por red."""

    def __init__(self, controles="flechas", conexion=None, es_host=True):
        super().__init__(controles=controles)
        self.conexion   = conexion
        self.es_host    = es_host
        self.mi_indice  = 0 if es_host else 1
        self.desconectado = False
        # Cuál de los dos jugadores está siendo evaluado en este momento.
        # Normalmente soy yo, pero el host también resuelve los movimientos
        # del invitado, y ahí las habilidades que se aplican son las del
        # invitado, no las suyas (ver _mover_jugador).
        self.indice_en_foco = self.mi_indice
        # Aviso del objeto cooperativo recogido (nombre + tiempo restante)
        self.aviso_objeto       = ""
        self.timer_aviso_objeto = 0.0

    def _personaje_de_habilidad(self):
        """El mixin de habilidades pregunta por acá de quién son las
        habilidades que hay que aplicar."""
        return JUGADORES[self.indice_en_foco]

    # ── Setup ─────────────────────────────────────────────────────────────
    def setup(self, numero_nivel=1, puntaje_total=0):
        # Va antes de super() porque el panel lateral, que se arma dentro
        # de setup(), ya muestra la habilidad y sus usos restantes.
        self.iniciar_habilidades()

        super().setup(numero_nivel, puntaje_total)

        # Las paredes tal como vienen del mapa, antes de que se abra
        # ninguna puerta. El cliente las necesita para poder reconstruir
        # cuáles están abiertas a partir del estado que manda el host.
        self.paredes_originales = set(self.paredes)

        # El jugador 1 arranca donde arrancan todos los modos; el 2, en la
        # primera celda libre pegada a esa (los mapas no traen un objeto
        # de inicio propio para el segundo jugador).
        # "moviendose" es propio de cada jugador: define si se lo dibuja con
        # la animación de caminar o la de quieto. Tiene que ser individual
        # porque los dos se mueven por su cuenta — con una sola bandera
        # compartida, cuando uno caminaba el otro también parecía caminar
        # parado en el lugar.
        inicio2 = self._celda_libre_vecina(POS_INICIO)
        self.jugadores = [
            {"col": POS_INICIO[0], "fila": POS_INICIO[1],
             "px_x": 0.0, "px_y": 0.0, "moviendose": False},
            {"col": inicio2[0],    "fila": inicio2[1],
             "px_x": 0.0, "px_y": 0.0, "moviendose": False},
        ]
        for j in self.jugadores:
            j["px_x"], j["px_y"] = self._celda_a_px(j["col"], j["fila"])

        # Las dos celdas de arranque ya cuentan como recorridas: el sendero
        # es compartido, igual que en Tutorial y Viaje.
        self.sendero.add(inicio2)

        self._sincronizar_mi_jugador(tambien_pixeles=True)

        if self.es_host:
            self._difundir_estado()

    def _celda_libre_vecina(self, celda):
        """Busca una celda transitable pegada a la dada, para ubicar al
        segundo jugador. Si no hubiera ninguna (mapa muy cerrado), se
        devuelve la misma: es preferible que los dos arranquen encimados
        antes que dejar a un jugador dentro de una pared."""
        col, fila = celda
        for dc, df in ((1, 0), (0, -1), (0, 1), (-1, 0)):
            vecina = (col + dc, fila + df)
            if (0 <= vecina[0] < self.mapa_ancho and 0 <= vecina[1] < self.mapa_alto
                    and vecina not in self.paredes):
                return vecina
        return celda

    def _sincronizar_mi_jugador(self, tambien_pixeles=False):
        """Copia la posición de MI jugador a self.col/self.fila, que es lo
        que miran los métodos heredados de Juego: el movimiento suave en
        píxeles y la cámara que sigue al jugador.

        Con tambien_pixeles se reubica además la posición en pantalla sin
        animar. Hace falta al arrancar el nivel, porque Juego deja a todos
        en POS_INICIO y el jugador 2 empieza en otra celda: sin esto, el
        invitado vería su propio sprite deslizándose desde el lugar del
        anfitrión al empezar."""
        yo = self.jugadores[self.mi_indice]
        self.col, self.fila = yo["col"], yo["fila"]
        if tambien_pixeles:
            self.px_x, self.px_y = self._celda_a_px(self.col, self.fila)

    # ── Costuras heredadas de Juego ───────────────────────────────────────
    def _dificultad_del_nivel(self, numero_nivel):
        return DIFICULTAD_MAPAS

    def _obtener_datos_nivel(self):
        return nivel_mod.generar_nivel(self.numero_nivel, DIFICULTAD_MAPAS, usar_tiled=True)

    def _hay_que_perder_por_pasos(self):
        """En cooperativo no hay límite de pasos: la gracia es coordinarse,
        no competir por eficiencia."""
        return False

    def _guardar_progreso(self):
        """El multijugador no persiste nada: no tendría sentido guardar un
        récord que depende de con quién se jugó."""

    def _avanzar_de_nivel(self):
        """Solo el host decide cuándo se pasa de nivel; el cliente espera
        el aviso para que los dos carguen el mismo mapa."""
        if not self.es_host:
            return
        if self.numero_nivel < TOTAL_NIVELES:
            siguiente = self.numero_nivel + 1
            self.conexion.enviar({"t": "nivel", "n": siguiente})
            self.setup(siguiente, self.puntaje_total)
        else:
            self.conexion.enviar({"t": "fin"})
            self.juego_completado = True

    # ── Entrada del jugador ───────────────────────────────────────────────
    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.ESCAPE:
            if self.conexion:
                self.conexion.cerrar()
            if hasattr(self, "musica_player") and self.musica_player:
                arcade.stop_sound(self.musica_player)
                self.musica_player = None
            from menu import Menu
            self.window.show_view(Menu())
            return

        if self.ganado or self.desconectado:
            return

        if self._tecla_arriba(symbol):
            self._pedir_movimiento(0, 1)
        elif self._tecla_abajo(symbol):
            self._pedir_movimiento(0, -1)
        elif self._tecla_izquierda(symbol):
            self._pedir_movimiento(-1, 0)
        elif self._tecla_derecha(symbol):
            self._pedir_movimiento(1, 0)
        elif symbol == arcade.key.E:
            self._pedir_llave()
        elif symbol == arcade.key.SPACE:
            self._pedir_habilidad()

    def _pedir_movimiento(self, dc, df):
        """El host aplica el movimiento directamente; el cliente se lo pide
        al host y espera que le vuelva el estado ya resuelto."""
        if self.es_host:
            if self._mover_jugador(0, dc, df):
                self._difundir_estado()
        else:
            self.conexion.enviar({"t": "mover", "dc": dc, "df": df})

    def _pedir_llave(self):
        if self.es_host:
            if self._recoger_llave(0):
                self._difundir_estado()
        else:
            self.conexion.enviar({"t": "llave"})

    def _pedir_habilidad(self):
        """La Rampa cambia las reglas del movimiento, así que la decide el
        host igual que todo lo demás. La Guía, en cambio, es solo
        información en pantalla: se resuelve localmente y no se manda."""
        personaje = JUGADORES[self.mi_indice]
        if personaje["habilidad"] == "guia":
            self.indice_en_foco = self.mi_indice
            self.usar_habilidad(self._mi_celda())
            return

        if self.es_host:
            self._activar_habilidad(0)
            self._difundir_estado()
        else:
            self.conexion.enviar({"t": "habilidad"})

    def _activar_habilidad(self, indice):
        """Aplica la habilidad activa del jugador indicado. Corre en el
        host, que es quien tiene el estado real."""
        foco_anterior = self.indice_en_foco
        self.indice_en_foco = indice
        try:
            jugador = self.jugadores[indice]
            self.usar_habilidad((jugador["col"], jugador["fila"]))
        finally:
            self.indice_en_foco = foco_anterior

    def _mi_celda(self):
        yo = self.jugadores[self.mi_indice]
        return (yo["col"], yo["fila"])

    # ── Lógica de juego (solo corre en el host) ───────────────────────────
    def _mover_jugador(self, indice, dc, df):
        """Intenta mover al jugador indicado. Devuelve True si el estado
        cambió, para que el host sepa que hay algo que difundir.

        Mismas reglas que el resto del juego -límites, paredes, sendero no
        repetible, hielo, teleportes y placas- más una nueva: los dos
        jugadores no pueden ocupar la misma celda."""
        jugador = self.jugadores[indice]
        nc, nf   = jugador["col"] + dc, jugador["fila"] + df

        # Las habilidades que valen durante este movimiento son las del
        # jugador que se mueve. Importa sobre todo en el host, que también
        # resuelve los movimientos del invitado.
        estaba_pisado = (nc, nf) in self.sendero
        foco_anterior = self.indice_en_foco
        self.indice_en_foco = indice
        try:
            se_movio = self._resolver_movimiento(indice, jugador, dc, df, nc, nf)
            self.consumir_rampa_si_correspondia(estaba_pisado, se_movio)
            return se_movio
        finally:
            self.indice_en_foco = foco_anterior

    def _resolver_movimiento(self, indice, jugador, dc, df, nc, nf):
        if not (0 <= nc < self.mapa_ancho and 0 <= nf < self.mapa_alto):
            return False
        if (nc, nf) in self.paredes:
            return False
        if self._sendero_bloquea(nc, nf):
            return False
        if any(o["col"] == nc and o["fila"] == nf for o in self.jugadores):
            return False   # el otro jugador está parado ahí

        jugador["col"], jugador["fila"] = nc, nf
        self.direcciones[(nc, nf)] = (dc, df)
        self.sendero.add((nc, nf))
        self._sumar_paso()
        self._agregar_huella(nc, nf)

        # Hielo: desliza una celda más en la misma dirección, si se puede.
        if (nc, nf) in self.hielo:
            nc2, nf2 = nc + dc, nf + df
            libre = (0 <= nc2 < self.mapa_ancho and 0 <= nf2 < self.mapa_alto
                     and (nc2, nf2) not in self.paredes
                     and (nc2, nf2) not in self.sendero
                     and not any(o["col"] == nc2 and o["fila"] == nf2 for o in self.jugadores))
            if libre:
                jugador["col"], jugador["fila"] = nc2, nf2
                self.direcciones[(nc2, nf2)] = (dc, df)
                self.sendero.add((nc2, nf2))
                self._sumar_paso()
                self._agregar_huella(nc2, nf2)

        # Teleporte.
        actual = (jugador["col"], jugador["fila"])
        if actual in self.teleportes:
            destino = self.teleportes[actual]
            ocupado = any(o["col"] == destino[0] and o["fila"] == destino[1]
                          for o in self.jugadores)
            if destino not in self.sendero and not ocupado:
                jugador["col"], jugador["fila"] = destino
                self.sendero.add(destino)
                self._sumar_paso()
                self._agregar_huella(*destino)

        self._revisar_placas()
        self._revisar_objetos()

        if (jugador["col"], jugador["fila"]) == self.portal:
            self._completar_nivel()

        return True

    def _sumar_paso(self):
        """Los pasos son del equipo, no de cada jugador: se cuentan juntos
        porque el sendero también es compartido."""
        self.pasos += 1
        self.txt_pasos.value = str(self.pasos)

    def _recoger_llave(self, indice):
        """Recoger la llave es cooperativo: la agarra cualquiera de los dos
        y abre las puertas para ambos."""
        jugador = self.jugadores[indice]
        if not self.pos_llave or self.tiene_llave:
            return False
        if (jugador["col"], jugador["fila"]) != self.pos_llave:
            return False

        self.tiene_llave = True
        for pos in self.puertas_llave:
            self.paredes.discard(pos)
            if pos in self.anim_puertas_llave:
                self.anim_puertas_llave[pos]["animando"] = True
        self._actualizar_texto_llave()
        return True

    def _actualizar_texto_llave(self):
        """Deja el indicador del panel en sintonía con self.tiene_llave.

        Está en un solo lugar porque hay dos caminos que cambian la llave y
        los dos tienen que actualizar el texto Y el color: el jugador local
        que la recoge, y el estado que llega del host cuando la recogió el
        otro. Cuando el color se actualizaba solo en uno de los dos, el
        texto decía "LLAVE: SI" pero seguía en rojo."""
        self.txt_llave.value = "LLAVE: SI" if self.tiene_llave else "LLAVE: NO"
        self.txt_llave.color = (100, 200, 100) if self.tiene_llave else (200, 100, 100)

    def _revisar_placas(self):
        """Una placa se activa si CUALQUIERA de los dos está parado encima."""
        for placa in self.placas:
            pisada = any((j["col"], j["fila"]) == placa["pos"] for j in self.jugadores)
            if not pisada:
                continue
            for puerta in self.puertas_placa:
                if puerta["id"] == placa["id"] and not puerta["abierta"]:
                    puerta["abierta"] = True
                    self.paredes.discard(puerta["pos"])
                    if puerta["pos"] in self.anim_puertas_placa:
                        self.anim_puertas_placa[puerta["pos"]]["animando"] = True

    def _revisar_objetos(self):
        """El objeto cooperativo se consigue si CUALQUIERA de los dos pisa su
        celda: lo agarra uno, pero el logro es del equipo.

        Igual que las placas, se deriva de las posiciones —que el host
        difunde y el cliente aplica— así los dos lados llegan al mismo
        resultado sin agregar nada al protocolo de red. Al conseguirse se
        desbloquea en el guardado (lo lee el Inventario) y se muestra un
        aviso corto en pantalla."""
        for d in self.donaciones:
            if d["recogida"]:
                continue
            if any((j["col"], j["fila"]) == d["pos"] for j in self.jugadores):
                d["recogida"] = True
                guardado.desbloquear_objeto(d["tipo"])
                arcade.play_sound(self.snd_victoria)
                objeto = next((o for o in OBJETOS_MULTIJUGADOR
                               if o["id"] == d["tipo"]), None)
                self.aviso_objeto       = objeto["nombre"] if objeto else d["tipo"]
                self.timer_aviso_objeto = 3.0

    # ── Sincronización por red ────────────────────────────────────────────
    def _difundir_estado(self):
        """El host manda el estado completo del nivel. Las listas se mandan
        como listas de listas porque JSON no tiene tuplas ni conjuntos."""
        if not self.es_host or not self.conexion:
            return
        self.conexion.enviar({
            "t": "estado",
            "jugadores": [[j["col"], j["fila"]] for j in self.jugadores],
            "sendero":   [[c, f] for (c, f) in self.sendero],
            "direcciones": [[c, f, dc, df] for (c, f), (dc, df) in self.direcciones.items()],
            "pasos":     self.pasos,
            "llave":     self.tiene_llave,
            # Solo las puertas que se abrieron: el resto de las paredes son
            # idénticas de los dos lados porque salen del mismo .tmx.
            "abiertas":  [[c, f] for (c, f) in (self.paredes_originales - self.paredes)],
            "ganado":    self.ganado,
            # Estado de las habilidades, para que las dos pantallas muestren
            # lo mismo (si la rampa está lista y cuántos usos quedan).
            "rampa":     self.rampa_armada,
            "usos":      dict(self.usos_gastados),
        })

    def _aplicar_estado(self, msg):
        """El cliente reemplaza su estado por el que mandó el host. No
        intenta fusionar nada: el host es la única fuente de verdad."""
        for jugador, (col, fila) in zip(self.jugadores, msg["jugadores"]):
            jugador["col"], jugador["fila"] = col, fila

        self.sendero     = {(c, f) for c, f in msg["sendero"]}
        self.direcciones = {(c, f): (dc, df) for c, f, dc, df in msg["direcciones"]}
        self.pasos       = msg["pasos"]
        self.tiene_llave = msg["llave"]

        abiertas     = {(c, f) for c, f in msg["abiertas"]}
        self.paredes = self.paredes_originales - abiertas
        for pos in abiertas:
            for anim in (self.anim_puertas_llave, self.anim_puertas_placa):
                if pos in anim and anim[pos]["anim_frame"] == 0 and not anim[pos]["animando"]:
                    anim[pos]["animando"] = True

        self.rampa_armada   = msg.get("rampa", False)
        self.usos_gastados  = msg.get("usos", {})

        if msg["ganado"] and not self.ganado:
            self._completar_nivel()

        self._sincronizar_mi_jugador()
        self._reconstruir_sendero_sprites()
        self.txt_pasos.value = str(self.pasos)
        self._actualizar_texto_llave()
        self._revisar_objetos()

    def _procesar_mensajes(self):
        if not self.conexion:
            return
        for msg in self.conexion.leer_mensajes():
            tipo = msg.get("t")
            if tipo == "mover" and self.es_host:
                if self._mover_jugador(1, msg["dc"], msg["df"]):
                    self._difundir_estado()
            elif tipo == "llave" and self.es_host:
                if self._recoger_llave(1):
                    self._difundir_estado()
            elif tipo == "habilidad" and self.es_host:
                self._activar_habilidad(1)
                self._difundir_estado()
            elif tipo == "estado" and not self.es_host:
                self._aplicar_estado(msg)
            elif tipo == "nivel" and not self.es_host:
                self.setup(msg["n"], self.puntaje_total)
            elif tipo == "fin" and not self.es_host:
                self.juego_completado = True

    # ── Actualización ─────────────────────────────────────────────────────
    def on_update(self, delta_time):
        # Primero se refleja la celda de MI jugador en self.col/self.fila.
        # Es imprescindible y va antes que todo lo demás: Juego interpola el
        # sprite y mueve la cámara mirando esos dos atributos, y quien mueve
        # a los jugadores es _mover_jugador, que solo toca la lista
        # self.jugadores. Sin esta línea, el anfitrión avanzaba de celda en
        # la lógica pero su sprite se quedaba clavado en el lugar.
        self._sincronizar_mi_jugador()

        # Con eso ya puesto, Juego mueve suavemente self.px_x/px_y hacia la
        # celda destino y acomoda la cámara.
        super().on_update(delta_time)

        self._procesar_mensajes()
        self.actualizar_habilidades(delta_time)

        if self.aviso_objeto:
            self.timer_aviso_objeto -= delta_time
            if self.timer_aviso_objeto <= 0:
                self.aviso_objeto = ""

        if self.conexion and not self._sigue_conectado():
            self.desconectado = True

        # Mi posición en píxeles ya la calculó super(), junto con si me
        # estoy moviendo; se copian al jugador que me corresponde.
        yo = self.jugadores[self.mi_indice]
        yo["px_x"], yo["px_y"] = self.px_x, self.px_y
        yo["moviendose"]       = self.moviendose

        # El resto de los jugadores se interpolan acá, con el mismo
        # criterio, y cada uno decide por su cuenta si está caminando.
        for i, jugador in enumerate(self.jugadores):
            if i == self.mi_indice:
                continue
            destino_x, destino_y = self._celda_a_px(jugador["col"], jugador["fila"])
            dx, dy = destino_x - jugador["px_x"], destino_y - jugador["px_y"]
            distancia = (dx**2 + dy**2) ** 0.5
            if distancia > self.velocidad_movimiento:
                jugador["px_x"] += dx / distancia * self.velocidad_movimiento
                jugador["px_y"] += dy / distancia * self.velocidad_movimiento
                jugador["moviendose"] = True
            else:
                jugador["px_x"], jugador["px_y"] = destino_x, destino_y
                jugador["moviendose"] = False

    def _sigue_conectado(self):
        if self.es_host:
            return self.conexion.hay_jugador
        return self.conexion.conectado

    # ── Dibujo ────────────────────────────────────────────────────────────
    def _dibujar_uaibot(self):
        """Dibuja a los dos jugadores, cada uno con su color y con SU
        propia animación: el que se está moviendo va con los frames de
        caminar y el que está quieto con los de idle, sin importar lo que
        haga el otro. Sustituye al método de Juego, que dibuja uno solo."""
        # La ruta de la Guía va debajo de los jugadores.
        self.dibujar_habilidades()
        for i, jugador in enumerate(self.jugadores):
            datos  = self.familia[JUGADORES[i]["id"]]
            frames = datos["walk"] if jugador["moviendose"] else datos["idle"]
            arcade.draw_texture_rect(
                frames[self.frame_actual % len(frames)],
                arcade.XYWH(jugador["px_x"], jugador["px_y"], TAM_CELDA, TAM_CELDA),
                color=arcade.types.Color(*datos["color"])
            )

    def _frames_activos(self):
        """El contador de animación es uno solo para los dos jugadores, así que
        cicla sobre la animación más larga de las dos en curso; cada jugador
        aplica su propio módulo al dibujar. De lo contrario, si un jugador
        tuviera menos frames que el otro, al más largo se le cortarían poses."""
        listas = [
            self.familia[JUGADORES[i]["id"]]["walk" if j["moviendose"] else "idle"]
            for i, j in enumerate(self.jugadores)
        ]
        return max(listas, key=len)

    def _crear_textos(self):
        super()._crear_textos()
        self.txt_nivel.value  = f"Nivel {self.numero_nivel}/{TOTAL_NIVELES}"
        self.txt_limite.value = ""
        self.txt_mision.value = "Lleguen al portal.\nEl camino recorrido\nes de los dos."

        # Van en el hueco que queda entre la misión y el contador de pasos:
        # más abajo chocarían con el puntaje.
        soy = JUGADORES[self.mi_indice]
        self.txt_quien_soy = arcade.Text(
            f"Sos {soy['nombre']}" + ("  (anfitrion)" if self.es_host else "  (invitado)"),
            ANCHO_JUEGO + 16, ALTO_VENTANA - 218,
            arcade.types.Color(*soy["color"]), 11, bold=True
        )
        self.txt_conexion = arcade.Text(
            "", ANCHO_JUEGO + 16, ALTO_VENTANA - 236, (120, 200, 120), 10
        )
        self.txt_habilidad_titulo = arcade.Text(
            "HABILIDAD (ESPACIO)", ANCHO_JUEGO + 16, ALTO_VENTANA - 410,
            arcade.color.GOLD, 11, bold=True
        )
        self.txt_habilidad = arcade.Text(
            self.texto_habilidad(), ANCHO_JUEGO + 16, ALTO_VENTANA - 428,
            (150, 200, 150), 9
        )
        self.txt_llave.y = ALTO_VENTANA - 446

    def _dibujar_iconos_panel(self):
        """Suma el ícono de la habilidad de quien está jugando en esta máquina."""
        super()._dibujar_iconos_panel()
        icono = ICONOS_HABILIDAD.get(JUGADORES[self.mi_indice]["habilidad"])
        if icono:
            spr.dibujar_icono(icono, self.x_iconos,
                              self.txt_habilidad_titulo.y + 3)

    def _dibujar_panel(self):
        super()._dibujar_panel()
        self.txt_quien_soy.draw()
        self.txt_habilidad_titulo.draw()
        self.txt_habilidad.value = self.texto_habilidad()
        self.txt_habilidad.draw()
        self.txt_conexion.value = "Desconectado" if self.desconectado else "Conectado"
        self.txt_conexion.color = (220, 100, 100) if self.desconectado else (120, 200, 120)
        self.txt_conexion.draw()
        if self.pos_llave:
            self.txt_llave.draw()

    def on_draw(self):
        super().on_draw()
        if not (self.ganado or self.desconectado):
            self.dibujar_aviso_habilidad()
        if self.aviso_objeto:
            self._dibujar_aviso_objeto()
        if self.desconectado:
            self._dibujar_aviso_desconexion()

    def _dibujar_aviso_objeto(self):
        """Cartel corto al conseguir el objeto cooperativo del nivel."""
        cx, cy = ANCHO_JUEGO // 2, ALTO_VENTANA - 120
        arcade.draw_lrbt_rectangle_filled(cx - 260, cx + 260, cy - 26, cy + 26,
                                          (0, 0, 0, 160))
        arcade.draw_lrbt_rectangle_outline(cx - 260, cx + 260, cy - 26, cy + 26,
                                           arcade.color.GOLD, 2)
        arcade.Text("¡OBJETO CONSEGUIDO!", cx, cy + 8, arcade.color.GOLD, 13,
                    anchor_x="center", bold=True).draw()
        arcade.Text(self.aviso_objeto, cx, cy - 10, (220, 220, 220), 12,
                    anchor_x="center").draw()

    def _dibujar_aviso_desconexion(self):
        arcade.draw_lrbt_rectangle_filled(0, ANCHO_JUEGO, 0, ALTO_VENTANA, (0, 0, 0, 190))
        cx, cy = ANCHO_JUEGO // 2, ALTO_VENTANA // 2
        arcade.Text("SE CORTO LA CONEXION", cx, cy + 20, arcade.color.RED, 26,
                    anchor_x="center", anchor_y="center", bold=True).draw()
        arcade.Text("El otro jugador se desconecto", cx, cy - 20, (200, 200, 200), 13,
                    anchor_x="center", anchor_y="center").draw()
        arcade.Text("ESC para volver al menu", cx, cy - 55, (150, 150, 150), 12,
                    anchor_x="center", anchor_y="center").draw()
