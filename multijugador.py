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

from typing import ClassVar

import arcade

import guardado
import nivel as nivel_mod
import panel as pnl
import red
import sprites as spr
import ui
from constantes import *
from habilidades import Habilidades
from juego import Juego

DIFICULTAD_MAPAS = "dificil"   # los 10 mapas reservados para este modo
TOTAL_NIVELES    = 10

# Con quién arranca cada jugador si nadie eligió: el anfitrión con UAIBOT y
# el invitado con UAIBOTA. Se toman de la familia ya definida en
# constantes.py, así el color con el que se dibuja cada uno es el mismo que
# usan Tutorial y Viaje.
PERSONAJES_POR_DEFECTO = ["uaibot", "uaibota"]


def personaje_por_id(id_personaje):
    """Busca un integrante de la familia por su id. Si no existe -un mensaje
    de red con un id inventado- devuelve UAIBOT, para que una partida no se
    caiga por un dato mal formado."""
    for p in PERSONAJES_FAMILIA:
        if p["id"] == id_personaje:
            return p
    return PERSONAJES_FAMILIA[0]


class SalaMultijugador(arcade.View):
    """Pantalla previa a la partida: crear una o unirse a una existente.

    El descubrimiento automático por UDP está previsto para más adelante;
    por ahora el que se une escribe la IP que le muestra el host. Es la
    parte que nunca falla, ni con firewall ni con redes que aíslan los
    dispositivos entre sí."""

    def __init__(self, controles="flechas"):
        """Arranca la sala en el menú, sin conexión todavía."""
        super().__init__()
        self.controles = controles
        # menu | eligiendo | esperando | escribiendo_ip | error
        self.estado    = "menu"
        self.opcion    = 0           # 0 = crear, 1 = unirse
        self.accion    = None        # qué se hace al terminar de elegir
        self.personaje = 0           # índice en PERSONAJES_FAMILIA
        # Retratos de la familia: el frame 0 de Idle, igual que el Bestiario.
        self.familia   = spr.cargar_familia(PERSONAJES_FAMILIA, 128, 128)
        self.ip_escrita = ""
        self.mensaje_error = ""
        self.servidor = None
        self.cliente  = None

    # ── Eventos ───────────────────────────────────────────────────────────
    def on_key_press(self, symbol, modifiers):
        """Navega la sala. Cada estado atiende sus propias teclas."""
        if symbol == arcade.key.ESCAPE:
            # Desde la elección se vuelve un paso atrás, no directo al menú
            # principal: es fácil entrar sin querer y perder la partida que
            # se estaba por crear.
            if self.estado == "eligiendo":
                self.estado = "menu"
            else:
                self._volver_al_menu()
            return

        if self.estado == "menu":
            if symbol in (arcade.key.UP, arcade.key.DOWN):
                self.opcion = 1 - self.opcion
            elif symbol == arcade.key.ENTER:
                self.accion = "crear" if self.opcion == 0 else "unirse"
                self.estado = "eligiendo"

        elif self.estado == "eligiendo":
            if symbol in (arcade.key.LEFT, arcade.key.UP):
                self.personaje = (self.personaje - 1) % len(PERSONAJES_FAMILIA)
            elif symbol in (arcade.key.RIGHT, arcade.key.DOWN):
                self.personaje = (self.personaje + 1) % len(PERSONAJES_FAMILIA)
            elif symbol == arcade.key.ENTER:
                self._crear_partida() if self.accion == "crear" else self._pedir_ip()

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
        """Cierra lo que haya quedado abierto y vuelve al menú principal."""
        if self.servidor:
            self.servidor.cerrar()
        if self.cliente:
            self.cliente.cerrar()
        from menu import Menu
        self.window.show_view(Menu())

    # ── Crear / unirse ────────────────────────────────────────────────────
    def _crear_partida(self):
        """Abre el puerto y pasa a esperar al otro jugador."""
        self.servidor = red.Servidor()
        if self.servidor.error:
            self.estado = "error"
            self.mensaje_error = self.servidor.error
            return
        self.estado = "esperando"

    def _pedir_ip(self):
        """Pasa a la pantalla donde se escribe la IP del anfitrión."""
        self.estado = "escribiendo_ip"
        self.ip_escrita = ""

    def _unirse(self):
        """Se conecta a la IP escrita y, si sale bien, arranca la partida."""
        self.cliente = red.Cliente(self.ip_escrita.strip() or "127.0.0.1")
        if self.cliente.error:
            self.estado = "error"
            self.mensaje_error = self.cliente.error
            return
        self._empezar_partida(self.cliente, es_host=False)

    def _empezar_partida(self, conexion, es_host):
        """Deja la sala y muestra la partida ya conectada."""
        vista = Multijugador(controles=self.controles, conexion=conexion,
                             es_host=es_host,
                             personaje=PERSONAJES_FAMILIA[self.personaje]["id"])
        vista.setup()
        self.window.show_view(vista)

    def on_update(self, delta_time):
        # El host espera acá hasta que alguien se conecta. La detección la
        # hace el hilo de red; acá solo se consulta la bandera, que es una
        # operación instantánea y no frena el dibujado.
        """El anfitrión espera acá hasta que alguien se conecta.

        La detección la hace el hilo de red; acá solo se consulta la
        bandera, que es instantáneo y no frena el dibujado."""
        if self.estado == "esperando" and self.servidor.hay_jugador:
            self._empezar_partida(self.servidor, es_host=True)

    # ── Dibujo ────────────────────────────────────────────────────────────
    # Cada pantalla de la sala trae el tamaño de su cuadro y el pie que le
    # corresponde. Tenerlo en un solo lugar evita que cada una repita el
    # encabezado y termine con márgenes distintos, que es como estaban.
    # ancho, alto, título del cuadro y pie de ayuda de cada pantalla.
    PANTALLAS: ClassVar[dict] = {
        "menu":           (540, 250, None, "ESC para volver al menu"),
        "eligiendo":      (840, 340, "¿Con quien jugas?", "ESC para volver atras"),
        "esperando":      (520, 250, None, "ESC para cancelar"),
        "escribiendo_ip": (520, 220, None, "ESC para volver atras"),
        "error":          (620, 230, None, "ESC para volver al menu"),
    }

    def on_draw(self):
        """Dibuja el cuadro de la pantalla en la que esté la sala."""
        self.window.clear(ui.FONDO)
        ui.encabezado("MULTIJUGADOR", "Cooperativo para dos en red local")

        ancho, alto, titulo, pie = self.PANTALLAS[self.estado]
        cx = ANCHO_VENTANA // 2
        cy = ALTO_VENTANA // 2 - 20
        ui.dialogo(cx, cy, ancho, alto, titulo)

        dibujar = {
            "menu":           self._dibujar_menu,
            "eligiendo":      self._dibujar_eleccion,
            "esperando":      self._dibujar_esperando,
            "escribiendo_ip": self._dibujar_pedir_ip,
            "error":          self._dibujar_error,
        }[self.estado]
        dibujar(cx, cy)

        ui.ayuda(pie)

    def _dibujar_menu(self, cx, cy):
        """Elegir entre crear una partida o unirse a una existente."""
        for i, texto in enumerate(("Crear partida", "Unirse a una partida")):
            elegida = (i == self.opcion)
            y = cy + 58 - i * 46
            if elegida:
                arcade.draw_lrbt_rectangle_filled(cx - 170, cx + 170, y - 17, y + 17,
                                                  (52, 152, 219, 45))
            ui.etiqueta(f"sala_op{i}", texto, cx, y,
                     arcade.color.WHITE if elegida else (150, 150, 150), 19,
                     anchor_x="center", anchor_y="center", bold=elegida).draw()

        ui.etiqueta("sala_red", "Los dos tienen que estar en la misma red", cx,
                 cy - 46, (170, 170, 170), 12,
                 anchor_x="center", anchor_y="center").draw()
        ui.parrafo("Para probar en una sola PC: abri el juego dos veces y usa 127.0.0.1",
                   cx, cy - 74, 400, 11, (120, 120, 120))

    def _dibujar_eleccion(self, cx, cy):
        """Elección de personaje. Se muestran los cuatro con su habilidad,
        porque en cooperativo la habilidad es lo que define qué aporta cada
        uno al equipo: es la información con la que conviene elegir."""
        for i, personaje in enumerate(PERSONAJES_FAMILIA):
            x       = cx + (i - 1.5) * 186
            elegido = (i == self.personaje)
            color   = arcade.types.Color(*personaje["color"])

            if elegido:
                arcade.draw_lrbt_rectangle_outline(
                    x - 86, x + 86, cy - 86, cy + 96, arcade.color.GOLD, 2)

            datos = self.familia[personaje["id"]]
            # El tinte sale de cargar_familia: los que tienen arte propio
            # vuelven en blanco, para no desteñirlos pintándolos encima.
            # El retrato va bien arriba del nombre: el robot llega hasta el
            # borde de abajo de su recuadro y si no le tapa el texto.
            arcade.draw_texture_rect(datos["idle"][0],
                                     arcade.XYWH(x, cy + 34, 130, 130),
                                     color=arcade.types.Color(*datos["color"]))
            ui.etiqueta(f"ele_nom{i}", personaje["nombre"], x, cy - 34,
                     color if elegido else (120, 120, 120), 14,
                     anchor_x="center", anchor_y="center", bold=elegido).draw()
            ui.etiqueta(f"ele_hab{i}", personaje["habilidad_nombre"], x, cy - 54,
                     arcade.color.GOLD if elegido else (105, 105, 105), 11,
                     anchor_x="center", anchor_y="center", bold=elegido).draw()
            ui.etiqueta(f"ele_desc{i}", personaje["habilidad_desc"], x, cy - 72,
                     (185, 185, 185) if elegido else (90, 90, 90), 10,
                     anchor_x="center", anchor_y="center").draw()

        ui.etiqueta("ele_ayuda", "<-  ->  para elegir      ENTER para seguir", cx,
                 cy - 112, (150, 150, 150), 12,
                 anchor_x="center", anchor_y="center").draw()
        ui.etiqueta("ele_choque",
                 "Si los dos eligen el mismo, el que se une juega con otro",
                 cx, cy - 136, (110, 110, 110), 11,
                 anchor_x="center", anchor_y="center").draw()

    def _dibujar_esperando(self, cx, cy):
        """La IP que hay que dictarle al otro jugador, bien a la vista."""
        ui.etiqueta("esp_titulo", "Esperando al otro jugador...", cx, cy + 76,
                 arcade.color.WHITE, 19,
                 anchor_x="center", anchor_y="center", bold=True).draw()
        ui.etiqueta("esp_sub", "Que se una con esta direccion:", cx, cy + 34,
                 (170, 170, 170), 13, anchor_x="center", anchor_y="center").draw()

        # La IP en un recuadro propio: es el dato que hay que dictarle al
        # otro jugador, y con el resto del texto alrededor se perdía.
        ip = red.ip_local()
        arcade.draw_lrbt_rectangle_filled(cx - 130, cx + 130, cy - 24, cy + 18,
                                          (0, 0, 0, 90))
        arcade.draw_lrbt_rectangle_outline(cx - 130, cx + 130, cy - 24, cy + 18,
                                           arcade.color.GOLD, 1)
        ui.etiqueta("esp_ip", ip, cx, cy - 3, arcade.color.GOLD, 28,
                 anchor_x="center", anchor_y="center", bold=True).draw()
        ui.etiqueta("esp_pc", "(en la misma PC: 127.0.0.1)", cx, cy - 52,
                 (120, 120, 120), 11, anchor_x="center", anchor_y="center").draw()

    def _dibujar_pedir_ip(self, cx, cy):
        """El campo donde se escribe la IP del anfitrión."""
        ui.etiqueta("ip_titulo", "Escribi la IP del que creo la partida", cx,
                 cy + 62, arcade.color.WHITE, 16, anchor_x="center",
                 anchor_y="center").draw()
        arcade.draw_lrbt_rectangle_filled(cx - 130, cx + 130, cy - 8, cy + 34,
                                          (0, 0, 0, 90))
        arcade.draw_lrbt_rectangle_outline(cx - 130, cx + 130, cy - 8, cy + 34,
                                           arcade.color.GOLD, 1)
        ui.etiqueta("ip_valor", self.ip_escrita + "_", cx, cy + 13,
                 arcade.color.GOLD, 24,
                 anchor_x="center", anchor_y="center", bold=True).draw()
        ui.etiqueta("ip_ayuda", "ENTER para conectar   (vacio = 127.0.0.1)", cx,
                 cy - 40, (150, 150, 150), 12,
                 anchor_x="center", anchor_y="center").draw()

    def _dibujar_error(self, cx, cy):
        """El motivo por el que no se pudo conectar."""
        ui.etiqueta("err_titulo", "No se pudo conectar", cx, cy + 62,
                 arcade.color.RED, 22,
                 anchor_x="center", anchor_y="center", bold=True).draw()
        ui.parrafo(self.mensaje_error, cx, cy + 14, 520, 11, (200, 200, 200))
        ui.etiqueta("err_ayuda", "Cualquier tecla para volver", cx, cy - 62,
                 (150, 150, 150), 12, anchor_x="center", anchor_y="center").draw()


class Multijugador(Habilidades, Juego):
    """La partida cooperativa. Hereda de Juego todo el dibujo del mapa y
    reemplaza el movimiento por una versión de dos jugadores sincronizada
    por red."""

    def __init__(self, controles="flechas", conexion=None, es_host=True,
                 personaje=None):
        """Arma la partida: quién es cada uno y con qué personaje juega."""
        super().__init__(controles=controles)
        self.conexion   = conexion
        self.es_host    = es_host
        self.mi_indice  = 0 if es_host else 1

        # Con quién juega cada uno. El anfitrión es la autoridad también
        # acá: arranca con su elección y con una provisoria para el
        # invitado, y la corrige cuando le llega la que el invitado eligió
        # de verdad. El invitado se dibuja enseguida con la suya, sin
        # esperar la confirmación, y si hubiera choque el anfitrión se la
        # cambia en el estado siguiente.
        self.personajes = [personaje_por_id(i) for i in PERSONAJES_POR_DEFECTO]
        if personaje:
            self.personajes[self.mi_indice] = personaje_por_id(personaje)
        if not es_host and conexion:
            # El anfitrión todavía no sabe con quién quiere jugar el
            # invitado: es lo primero que se le dice.
            conexion.enviar({"t": "personaje", "id": self.personajes[1]["id"]})
        self.desconectado = False
        # Cuál de los dos jugadores está siendo evaluado en este momento.
        # Normalmente soy yo, pero el host también resuelve los movimientos
        # del invitado, y ahí las habilidades que se aplican son las del
        # invitado, no las suyas (ver _mover_jugador).
        self.indice_en_foco = self.mi_indice
        # Aviso del objeto cooperativo recogido (nombre + tiempo restante)
        self.aviso_objeto       = ""
        self.timer_aviso_objeto = 0.0

        # Totales de la partida entera, para la pantalla de cierre. Se
        # acumulan por nivel porque self.pasos y self.donaciones los pisa
        # cada setup(), y al terminar el nivel 10 ya no quedaria nada que
        # mostrar.
        self.juego_completado    = False
        self.tiempo_total        = 0.0
        self.pasos_equipo        = 0
        self.objetos_conseguidos = 0
        self.objetos_campania    = 0

    def _personaje_de_habilidad(self):
        """El mixin de habilidades pregunta por acá de quién son las
        habilidades que hay que aplicar."""
        return self.personajes[self.indice_en_foco]

    # ── Setup ─────────────────────────────────────────────────────────────
    def setup(self, numero_nivel=1, puntaje_total=0):
        """Carga un nivel y ubica a los dos jugadores.

        Corre en los dos lados: el mapa no viaja por la red, cada
        computadora carga su propio .tmx a partir del número de nivel."""
        # Antes de que super() cargue el nivel nuevo y pise los datos, se
        # anota lo que dejo el que termina. Va aca y no en
        # _avanzar_de_nivel porque el invitado no pasa por ese metodo: el
        # llega al nivel siguiente por el mensaje "nivel" del anfitrion,
        # que lo manda derecho a setup().
        if hasattr(self, "donaciones"):
            self._contabilizar_nivel()

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
        # "mirando_derecha" es de cada jugador por el mismo motivo que
        # "moviendose": cada uno camina por su lado y tiene que quedar
        # mirando hacia donde fue él, no hacia donde fue el otro. Arrancan
        # mirando a la derecha, que es como está dibujado el arte.
        self.jugadores = [
            {"col": POS_INICIO[0], "fila": POS_INICIO[1],
             "px_x": 0.0, "px_y": 0.0, "moviendose": False,
             "mirando_derecha": True},
            {"col": inicio2[0],    "fila": inicio2[1],
             "px_x": 0.0, "px_y": 0.0, "moviendose": False,
             "mirando_derecha": True},
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
        """El cooperativo usa siempre los mapas de dificultad difícil."""
        return DIFICULTAD_MAPAS

    def _obtener_datos_nivel(self):
        """Carga el mapa de Tiled que le toca a este número de nivel."""
        return nivel_mod.generar_nivel(self.numero_nivel, DIFICULTAD_MAPAS, usar_tiled=True)

    def _hay_que_perder_por_pasos(self):
        """En cooperativo no hay límite de pasos: la gracia es coordinarse,
        no competir por eficiencia."""
        return False

    def _guardar_progreso(self):
        """El multijugador no persiste progreso: no tendría sentido guardar
        un récord que depende de con quién se jugó."""

    def _persiste_highscore(self):
        """Por el mismo motivo, el puntaje cooperativo tampoco entra al
        highscore general del menú: se consigue entre dos y no se puede
        comparar con el de una partida en solitario. Lo único que el
        multijugador sí deja guardado son los objetos conseguidos, que son
        una colección y no un récord."""
        return False

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
            self._terminar_campania()

    # ── Totales de la partida ─────────────────────────────────────────────
    def _contabilizar_nivel(self):
        """Suma a los totales del equipo lo que dejo el nivel que termina."""
        self.objetos_conseguidos += sum(1 for d in self.donaciones if d["recogida"])
        self.objetos_campania    += len(self.donaciones)
        self.pasos_equipo        += self.pasos

    def _terminar_campania(self):
        """Cierra la partida: anota el ultimo nivel -que no pasa por
        setup(), porque no hay nivel siguiente- y prende la pantalla de
        cierre. Lo corren los dos lados, cada uno por su camino: el
        anfitrion cuando lo decide, el invitado al recibir el aviso."""
        if self.juego_completado:
            return
        self._contabilizar_nivel()
        self.juego_completado = True

    def _limpiar_totales(self):
        """Pone en cero los totales del equipo, para empezar de nuevo."""
        self.juego_completado    = False
        self.tiempo_total        = 0.0
        self.pasos_equipo        = 0
        self.objetos_conseguidos = 0
        self.objetos_campania    = 0

    def _reiniciar_campania(self):
        """Vuelve al nivel 1 con los totales en cero y se lleva al invitado.

        Solo lo hace el anfitrion, por el mismo motivo que solo el decide
        cuando se pasa de nivel: si cada uno reiniciara por su lado,
        terminarian jugando mapas distintos.

        Los totales se limpian DESPUES de setup() porque setup() empieza
        contabilizando el nivel que termina; al reves quedarian sumados
        los del nivel 10 de la partida anterior."""
        self.conexion.enviar({"t": "nivel", "n": 1, "reinicio": True})
        self.setup(1, 0)
        self._limpiar_totales()

    # ── Entrada del jugador ───────────────────────────────────────────────
    def on_key_press(self, symbol, modifiers):
        """Las teclas del jugador de esta computadora.

        Ninguna mueve nada por sí sola: se traducen en un pedido al
        anfitrión, que es quien resuelve (ver _pedir_movimiento)."""
        if symbol == arcade.key.ESCAPE:
            if self.conexion:
                self.conexion.cerrar()
            if hasattr(self, "musica_player") and self.musica_player:
                arcade.stop_sound(self.musica_player)
                self.musica_player = None
            from menu import Menu
            self.window.show_view(Menu())
            return

        # Terminada la partida, R vuelve a empezar desde el nivel 1. Va
        # antes del corte de abajo, que existe para que no se pueda seguir
        # jugando con el nivel ya ganado.
        if self.juego_completado and symbol in (arcade.key.R, arcade.key.N):
            if self.es_host and not self.desconectado:
                self._reiniciar_campania()
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
        """Pide recoger la llave. El anfitrión decide si corresponde."""
        if self.es_host:
            if self._recoger_llave(0):
                self._difundir_estado()
        else:
            self.conexion.enviar({"t": "llave"})

    def _pedir_habilidad(self):
        """La Rampa cambia las reglas del movimiento, así que la decide el
        host igual que todo lo demás. La Guía, en cambio, es solo
        información en pantalla: se resuelve localmente y no se manda."""
        personaje = self.personajes[self.mi_indice]
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

    def _asignar_personaje_invitado(self, id_pedido):
        """Le da al invitado el personaje que pidió, salvo que sea el mismo
        que el del anfitrión: ahí se le da el primero libre de la familia.

        Se resuelve acá y no en la sala porque el invitado no puede saber
        con quién eligió jugar el anfitrión antes de conectarse; recién
        cuando están los dos hay con qué comparar."""
        elegido = personaje_por_id(id_pedido)
        if elegido["id"] == self.personajes[0]["id"]:
            elegido = next(p for p in PERSONAJES_FAMILIA
                           if p["id"] != self.personajes[0]["id"])
        if elegido["id"] == self.personajes[1]["id"]:
            return                      # ya era ese: nada que avisar
        self.personajes[1] = elegido
        self._actualizar_texto_personaje()
        self._difundir_estado()

    def _actualizar_texto_personaje(self):
        """Deja el panel en sintonía con el personaje que me tocó. Hace
        falta porque el texto y su color se arman una sola vez en
        _crear_textos, y el invitado puede enterarse después de que el
        anfitrión le cambió el personaje."""
        soy = self.personajes[self.mi_indice]
        self.txt_quien_soy.text  = (f"Sos {soy['nombre']}"
                                    + ("  (anfitrion)" if self.es_host else "  (invitado)"))
        self.txt_quien_soy.color = arcade.types.Color(*soy["color"])
        self.txt_habilidad.value = self.texto_habilidad()
        # Cambió la habilidad, y con ella el ícono de su sección.
        self._acomodar_panel()

    def _mi_celda(self):
        """La celda donde está el jugador de esta computadora."""
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
        """Aplica un movimiento ya validado y todo lo que dispara.

        Corre solo en el anfitrión. Después de mover, encadena lo que el
        paso haya provocado: deslizar por hielo, teletransportarse, pisar
        una placa, levantar un objeto o llegar al portal."""
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
        jugador["mirando_derecha"] = spr.mirada_segun(dc, jugador["mirando_derecha"])
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
            # Hacia dónde mira cada uno lo calcula el anfitrión al resolver
            # el movimiento, así que tiene que viajar: el invitado no
            # resuelve movimientos ni siquiera los suyos, y sin esto se
            # vería a los dos mirando siempre hacia la izquierda.
            "mirando": [j["mirando_derecha"] for j in self.jugadores],
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
            # Con quién juega cada uno lo decide el anfitrión, así que
            # viaja con el resto del estado en vez de tener su propio
            # mensaje de vuelta.
            "personajes": [p["id"] for p in self.personajes],
            "rampa":     self.rampa_armada,
            "usos":      dict(self.usos_gastados),
        })

    def _aplicar_estado(self, msg):
        """El cliente reemplaza su estado por el que mandó el host. No
        intenta fusionar nada: el host es la única fuente de verdad."""
        for jugador, (col, fila) in zip(self.jugadores, msg["jugadores"]):
            jugador["col"], jugador["fila"] = col, fila
        for jugador, mirando in zip(self.jugadores, msg.get("mirando", [])):
            jugador["mirando_derecha"] = mirando

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

        # Si el anfitrión resolvió un choque de personajes, acá se entera
        # el invitado de con quién le tocó jugar.
        ids = msg.get("personajes")
        if ids and [p["id"] for p in self.personajes] != ids:
            self.personajes = [personaje_por_id(i) for i in ids]
            self._actualizar_texto_personaje()

        if msg["ganado"] and not self.ganado:
            self._completar_nivel()

        self._sincronizar_mi_jugador()
        self._reconstruir_sendero_sprites()
        self.txt_pasos.value = str(self.pasos)
        self._actualizar_texto_llave()
        self._revisar_objetos()

    def _procesar_mensajes(self):
        """Atiende lo que llegó por la red desde el último cuadro.

        Cada lado escucha solo lo suyo: el anfitrión, los pedidos del
        invitado; el invitado, el estado que le manda el anfitrión."""
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
            elif tipo == "personaje" and self.es_host:
                self._asignar_personaje_invitado(msg.get("id"))
            elif tipo == "habilidad" and self.es_host:
                self._activar_habilidad(1)
                self._difundir_estado()
            elif tipo == "estado" and not self.es_host:
                self._aplicar_estado(msg)
            elif tipo == "nivel" and not self.es_host:
                if msg.get("reinicio"):
                    self.setup(1, 0)
                    self._limpiar_totales()
                else:
                    self.setup(msg["n"], self.puntaje_total)
            elif tipo == "fin" and not self.es_host:
                self._terminar_campania()

    # ── Actualización ─────────────────────────────────────────────────────
    def on_update(self, delta_time):
        # Primero se refleja la celda de MI jugador en self.col/self.fila.
        # Es imprescindible y va antes que todo lo demás: Juego interpola el
        # sprite y mueve la cámara mirando esos dos atributos, y quien mueve
        # a los jugadores es _mover_jugador, que solo toca la lista
        # self.jugadores. Sin esta línea, el anfitrión avanzaba de celda en
        # la lógica pero su sprite se quedaba clavado en el lugar.
        """Un cuadro de la partida en red.

        El orden importa: primero se refleja mi celda en self.col/fila,
        porque el motor heredado interpola el sprite y mueve la cámara
        mirando esos dos atributos."""
        self._sincronizar_mi_jugador()

        # Con eso ya puesto, Juego mueve suavemente self.px_x/px_y hacia la
        # celda destino y acomoda la cámara.
        super().on_update(delta_time)

        self._procesar_mensajes()
        self.actualizar_habilidades(delta_time)

        # El cronometro corre mientras se juega: se congela entre niveles
        # -mientras dura el confeti-, al terminar y si se corta la conexion.
        if not (self.ganado or self.desconectado or self.juego_completado):
            self.tiempo_total += delta_time

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
        """Si el otro jugador sigue del otro lado de la conexión."""
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
            datos  = self.familia[self.personajes[i]["id"]]
            frames = datos["walk"] if jugador["moviendose"] else datos["idle"]
            arcade.draw_texture_rect(
                spr.orientar(frames[self.frame_actual % len(frames)],
                             jugador["mirando_derecha"]),
                arcade.XYWH(jugador["px_x"], jugador["px_y"], TAM_CELDA, TAM_CELDA),
                color=arcade.types.Color(*datos["color"])
            )

    def _frames_activos(self):
        """El contador de animación es uno solo para los dos jugadores, así que
        cicla sobre la animación más larga de las dos en curso; cada jugador
        aplica su propio módulo al dibujar. De lo contrario, si un jugador
        tuviera menos frames que el otro, al más largo se le cortarían poses."""
        listas = [
            self.familia[self.personajes[i]["id"]]["walk" if j["moviendose"] else "idle"]
            for i, j in enumerate(self.jugadores)
        ]
        return max(listas, key=len)

    def _crear_textos(self):
        """Suma al panel los textos propios del cooperativo."""
        super()._crear_textos()
        self.txt_nivel.value  = f"Nivel {self.numero_nivel}/{TOTAL_NIVELES}"
        self.txt_limite.value = ""
        self.txt_mision.value = "Lleguen al portal. El camino recorrido es de los dos."

        x = ANCHO_JUEGO + pnl.MARGEN_X
        soy = self.personajes[self.mi_indice]
        self.txt_quien_soy = pnl.crear_texto(
            f"Sos {soy['nombre']}" + ("  (anfitrion)" if self.es_host else "  (invitado)"),
            x, 11, arcade.types.Color(*soy["color"]), bold=True)
        self.txt_conexion  = pnl.crear_texto("Conectado", x, 10, (120, 200, 120))
        self.txt_habilidad = pnl.crear_texto(self.texto_habilidad(), x, 9, (150, 200, 150))

    def _secciones_panel(self):
        """Suma quién es cada uno en esta máquina y su habilidad."""
        secciones = super()._secciones_panel()
        secciones.insert(1, pnl.Seccion("EQUIPO", [self.txt_quien_soy,
                                                   self.txt_conexion]))
        icono = ICONOS_HABILIDAD.get(self.personajes[self.mi_indice]["habilidad"])
        secciones.insert(4, pnl.Seccion("HABILIDAD (ESPACIO)", self.txt_habilidad,
                                        icono=icono))
        return secciones

    def _muestra_llave(self):
        """Los mapas del cooperativo traen llave aunque el modo no se juegue
        por dificultad."""
        return bool(self.pos_llave)

    def _actualizar_panel(self):
        """Lo que cambia mientras se juega: la habilidad gasta usos y la
        conexión se puede caer."""
        super()._actualizar_panel()
        self.txt_habilidad.value = self.texto_habilidad()
        self.txt_conexion.value  = "Desconectado" if self.desconectado else "Conectado"
        self.txt_conexion.color  = (220, 100, 100) if self.desconectado else (120, 200, 120)

    def on_draw(self):
        """Dibuja la partida y encima los avisos del cooperativo."""
        super().on_draw()
        if not (self.ganado or self.desconectado):
            self.dibujar_aviso_habilidad()
        if self.aviso_objeto:
            self._dibujar_aviso_objeto()
        if self.desconectado:
            self._dibujar_aviso_desconexion()

    def _dibujar_overlay_victoria(self):
        """Entre niveles va el overlay normal de Juego; al terminar el
        ultimo, la pantalla de cierre de la partida."""
        if self.juego_completado:
            self._dibujar_overlay_final()
            return
        super()._dibujar_overlay_victoria()

    def _dibujar_overlay_final(self):
        """Cierre de la partida cooperativa: lo que lograron entre los dos.

        Los totales son del equipo, no de cada uno, igual que los pasos y
        el sendero durante el juego."""
        arcade.draw_lrbt_rectangle_filled(0, ANCHO_JUEGO, 0, ALTO_VENTANA, (0, 0, 0, 200))
        for p in self.particulas:
            p.dibujar()

        cx, cy = ANCHO_JUEGO // 2, ALTO_VENTANA // 2
        arcade.Text("¡MISION CUMPLIDA!", cx, cy + 78, arcade.color.GOLD, 32,
                    anchor_x="center", anchor_y="center", bold=True).draw()
        arcade.Text(f"{self.personajes[0]['nombre']} y "
                    f"{self.personajes[1]['nombre']} "
                    f"llegaron juntos al final",
                    cx, cy + 42, (200, 200, 200), 13,
                    anchor_x="center", anchor_y="center").draw()

        # Con objetos puestos en los mapas se muestra el conteo real; hasta
        # que los haya, una linea que no mienta con un 0/0.
        if self.objetos_campania:
            arcade.Text(f"Objetos conseguidos: {self.objetos_conseguidos}"
                        f"/{self.objetos_campania}",
                        cx, cy + 10, (220, 180, 120), 13,
                        anchor_x="center", anchor_y="center").draw()

        arcade.Text(f"Tiempo total: {self.tiempo_total:.1f}s", cx, cy - 24,
                    arcade.color.LIME_GREEN, 16,
                    anchor_x="center", anchor_y="center", bold=True).draw()
        arcade.Text(f"Pasos del equipo: {self.pasos_equipo}", cx, cy - 50,
                    arcade.color.LIME_GREEN, 16,
                    anchor_x="center", anchor_y="center", bold=True).draw()
        arcade.Text(f"Puntaje: {self.puntaje_total}", cx, cy - 76,
                    arcade.color.LIME_GREEN, 16,
                    anchor_x="center", anchor_y="center", bold=True).draw()

        # Reiniciar es del anfitrion, asi que al invitado no se le ofrece
        # una tecla que no le va a hacer nada.
        pie = ("R: jugar de nuevo   ESC: volver al menu" if self.es_host
               else "El anfitrion decide si juegan de nuevo   ESC: volver al menu")
        arcade.Text(pie, cx, cy - 116, (150, 150, 150), 12,
                    anchor_x="center", anchor_y="center").draw()

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
        """Pantalla de corte cuando el otro jugador se va."""
        arcade.draw_lrbt_rectangle_filled(0, ANCHO_JUEGO, 0, ALTO_VENTANA, (0, 0, 0, 190))
        cx, cy = ANCHO_JUEGO // 2, ALTO_VENTANA // 2
        arcade.Text("SE CORTO LA CONEXION", cx, cy + 20, arcade.color.RED, 26,
                    anchor_x="center", anchor_y="center", bold=True).draw()
        arcade.Text("El otro jugador se desconecto", cx, cy - 20, (200, 200, 200), 13,
                    anchor_x="center", anchor_y="center").draw()
        arcade.Text("ESC para volver al menu", cx, cy - 55, (150, 150, 150), 12,
                    anchor_x="center", anchor_y="center").draw()
