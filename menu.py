# menu.py
# Pantalla de inicio del juego con fondo ilustrado y botones tipo ribbon.
# Navegación por teclado (↑↓ + ENTER) y mouse (hover + click).
#
# Ronda 2 (Fase 0.4 del plan): el menú pasa de 3 a 6 entradas —
# Viaje, Infinito, Multijugador, Tutorial, Inventario/Bestiario y
# Ajustes — y se elimina la selección manual de dificultad (el Modo
# Infinito la reemplaza escalando solo, ver Fase 1 del plan).
#
# De estas 6 entradas, Tutorial, Infinito, Viaje y Ajustes llevan a una
# pantalla funcional:
#   - Tutorial (tutorial.py) es el nivel único y fijo donde se cumplen
#     las 13 consignas graduadas de OFIRCA (7 de Ronda 1 + 6 de Ronda 2)
#     — vista propia, autocontenida, sin dificultad ni mapas de Tiled.
#   - Infinito (juego.py) genera niveles procedurales sin techo, con la
#     dificultad escalando sola cada 10 niveles hasta tope "dificil".
#   - Viaje (viaje.py) es la campaña: 10 niveles fijos diseñados en Tiled
#     (los de dificultad media), con cronómetro y desbloqueo de los
#     personajes de la familia de UAIBOT.
#   - Multijugador (multijugador.py) es el cooperativo para dos jugadores
#     en red local, sobre los 10 mapas de dificultad difícil.
# Solo Inventario/Bestiario sigue mostrando la pantalla "Próximamente"
# (clase Placeholder, al final del archivo).

import math

import arcade

import guardado
import sprites as spr
from constantes import *

OPCIONES = ["Viaje", "Infinito", "Multijugador", "Tutorial", "Inventario / Bestiario", "Ajustes"]

# Filas del submenu de Ajustes: la primera es el selector de controles que
# antes era su propia entrada del menú; las otras dos, el volumen de la
# música del menú y el de la música de niveles, en pasos de 10%.
FILAS_AJUSTES = ["Controles", "Volumen menú", "Volumen niveles"]
PASO_VOLUMEN  = 0.1

# Modos que todavía no tienen pantalla propia: al seleccionarlos se
# muestra el Placeholder en vez de iniciar algo. Se van sacando de esta
# lista a medida que cada modo se implementa en las fases siguientes.
MODOS_PENDIENTES: set = set()

# ── Fondo animado: la familia caminando ───────────────────────────────────────
# Los cuatro personajes cruzan el sendero de la ilustración en loop. Se dibujan
# ENTRE el fondo y el overlay oscuro, así reciben el mismo oscurecido que la
# escena -quedan integrados en vez de pegados encima- y los botones se leen
# por arriba sin competir con ellos.
# La altura importa: puestos al nivel de los pies del UAIBOT ilustrado, sus
# 72px contra los 250px de él se leen como un error de escala. Subidos al
# plano medio del sendero, el mismo tamaño se lee como distancia y funciona.
CAMINATA_Y          = 210   # altura de la banda del sendero, en plano medio
CAMINATA_TAM        = 115   # lado del frame al dibujarlo
CAMINATA_SEPARACION = 105   # distancia entre uno y otro: caminan en grupo
# Los sprites del juego son claros y fríos; la ilustración es cálida y está en
# penumbra de atardecer. Dibujados tal cual quedan flotando, como calcomanías
# sobre el fondo. Estas dos cosas los meten en la escena: la luz los tiñe con
# el color de la hora, y la sombra los apoya en el piso.
CAMINATA_LUZ        = (188, 158, 122)   # luz cálida de atardecer
# La sombra va en NEGRO con alpha, no en un gris oscuro: la escena tiene
# zonas de valor 4-7, más oscuras que cualquier gris, y mezclar hacia un
# color más claro que el fondo ACLARA en vez de oscurecer. Mezclar hacia
# negro oscurece siempre, sea cual sea el piso, y deja pasar su textura.
CAMINATA_SOMBRA     = (0, 0, 0, 70)     # sombra elíptica a los pies
CAMINATA_VELOCIDAD  = 26    # px por segundo
CAMINATA_FPS        = 6     # poses por segundo

# ── Nubes animadas del fondo ──────────────────────────────────────────────────
# Spritesheet de 4 frames (assets/nubes_anim.png) generado con PixelLab y
# puesto en tira horizontal con el mismo criterio que llave_anim.png. Las
# nubes derivan por el cielo del fondo ilustrado a distintas velocidades:
# eso, más el morphing del spritesheet, es lo que le da vida al menú sin
# tocar la ilustración original.
NUBE_TAM  = 192   # lado del frame al dibujarlo (64px nativos, x3)
NUBES_FPS = 3     # cuadros por segundo del morphing: sutil, no frenético
NUBES = [
    # (altura y, velocidad px/s, fase inicial 0-1, transparencia 0-255)
    (ALTO_VENTANA - 110, 14, 0.00, 190),   # baja y cercana, la más rápida
    (ALTO_VENTANA - 170,  9, 0.45, 170),
    (ALTO_VENTANA - 235,  5, 0.75, 150),   # alta y lejana, casi quieta
]

# ── Pájaros y luciérnagas del fondo ───────────────────────────────────────────
# Mismo mecanismo que las nubes (tira de 4 frames), pero cruzando y
# deambulando: los pájaros van altos y rápido, las luciérnagas titilan
# cerca del pasto. La idea es que el fondo tenga tres capas de vida a
# distintas alturas y velocidades.
PAJARO_TAM   = 96    # los pájaros se dibujan a la mitad que las nubes
PAJAROS_FPS  = 6     # aleteo más rápido que el morphing de las nubes
PAJAROS = [
    # (altura y, velocidad px/s, fase inicial 0-1)
    (ALTO_VENTANA - 290, 60, 0.10),
    (ALTO_VENTANA - 330, 52, 0.55),
]
LUCIERNAGA_TAM   = 44   # chiquitas: son puntos de luz, no protagonistas
LUCIERNAGAS_FPS  = 4
# (centro x, centro y, amplitud x, amplitud y, velocidad de vaivén, fase)
LUCIERNAGAS = [
    (ANCHO_VENTANA * 0.18, 120, 55, 30, 0.45, 0.0),
    (ANCHO_VENTANA * 0.42,  95, 70, 38, 0.33, 1.3),
    (ANCHO_VENTANA * 0.60, 150, 45, 26, 0.52, 2.4),
    (ANCHO_VENTANA * 0.80,  80, 60, 32, 0.38, 4.0),
    (ANCHO_VENTANA * 0.32, 185, 38, 22, 0.60, 5.1),
]


class Menu(arcade.View):
    # Player de música a nivel de clase: el menú se reconstruye cada vez que
    # se vuelve de un modo (show_view(Menu())), y así el nuevo Menú puede
    # detener la música del anterior en vez de montarle una encima.
    musica_player = None

    def __init__(self):
        super().__init__()
        self.datos               = guardado.cargar()
        self.opcion_seleccionada = 0
        self.submenu             = None   # None | "ajustes"
        self.ajuste_seleccionado = 0      # fila activa dentro del submenu de Ajustes
        self._cargar_assets()
        self._crear_textos()

    # ── Assets ────────────────────────────────────────────────────────────────
    def _cargar_assets(self):
        """Carga el fondo del menú, los ribbons de botones y la familia que
        camina por el fondo animado."""
        self.img_fondo = arcade.load_texture("assets/fondo_menu.png")

        # Los ribbons vienen apilados verticalmente, uno por opción del menú.
        # El alto de cada uno sale de la altura REAL del archivo dividida por
        # la cantidad de ribbons: antes estaba escrito a mano como 1563, que
        # no es la altura del PNG (1536), y eso corría todos los cortes 27px
        # y hacía que el primer ribbon leyera fuera de la imagen.
        sheet        = arcade.load_spritesheet("assets/botones.png")
        alto_hoja    = sheet.image.height
        cantidad     = len(OPCIONES)
        alto_ribbon  = alto_hoja // cantidad
        self.img_btn = [
            sheet.get_texture(
                arcade.LRBT(0, sheet.image.width,
                            alto_hoja - (i + 1) * alto_ribbon,
                            alto_hoja - i * alto_ribbon)
            )
            for i in range(cantidad)
        ]

        # Familia para el fondo animado. Reusa exactamente las mismas hojas
        # que el juego, con la misma regla de tinte: quien tiene arte propio
        # va sin teñir, quien no, teñido con su color.
        self.familia         = spr.cargar_familia(PERSONAJES_FAMILIA, 128, 128)
        self.orden_desfile   = [p["id"] for p in PERSONAJES_FAMILIA]
        self.desplazamiento  = 0.0
        self.frame_caminata  = 0
        self.timer_caminata  = 0.0

        # Nubes, pájaros y luciérnagas: tiras horizontales de 4 frames. El
        # corte por geometría real de la imagen (y no un número mágico) va
        # en un helper porque las tres comparten el mismo formato.
        def cortar_tira(ruta, ida_y_vuelta=False):
            """Corta una tira horizontal de 4 frames para el fondo animado.

            Descarta los frames completamente transparentes: nubes_anim.png
            trae el primero vacío, y dejarlo hacía que las nubes se borraran
            un tercio de segundo en cada vuelta del ciclo.

            Con ida_y_vuelta el ciclo va y vuelve en vez de reiniciar de
            golpe. Las nubes lo necesitan porque su tira no es un loop sino
            una animación de crecimiento -chica, mediana, grande-, y saltar
            de la grande a la chica se ve como un tirón; yendo y volviendo
            la nube se hincha y se deshincha, que es lo que hace una nube."""
            sheet   = arcade.load_spritesheet(ruta)
            ancho_f = sheet.image.width // 4
            frames  = []
            for i in range(4):
                recorte = sheet.image.crop((i * ancho_f, 0, (i + 1) * ancho_f,
                                            sheet.image.height))
                if recorte.getbbox() is None:
                    continue          # frame vacío: solo haría parpadear
                frames.append(sheet.get_texture(
                    arcade.LRBT(i * ancho_f, (i + 1) * ancho_f,
                                0, sheet.image.height)))
            if ida_y_vuelta and len(frames) > 2:
                frames += frames[-2:0:-1]
            return frames

        self.frames_nubes       = cortar_tira("assets/nubes_anim.png",
                                              ida_y_vuelta=True)
        self.frames_pajaros     = cortar_tira("assets/pajaros_anim.png")
        self.frames_luciernagas = cortar_tira("assets/luciernagas_anim.png")
        # Las tres capas animadas del fondo siguen el mismo patrón: un
        # acumulador de tiempo continuo -compartido, del que salen todas las
        # derivas- y, por capa, un timer propio más un contador de frames para
        # el morphing de su tira. Se inicializan las tres juntas a propósito:
        # faltaban las de pájaros y luciérnagas, y el menú crasheaba con
        # AttributeError en el primer on_update.
        self.tiempo_nubes = 0.0   # acumulador común de las derivas
        self.frame_nubes,       self.timer_nubes       = 0, 0.0
        self.frame_pajaros,     self.timer_pajaros     = 0, 0.0
        self.frame_luciernagas, self.timer_luciernagas = 0, 0.0

        self.musica = arcade.load_sound("assets/MenuMusic.wav")

        # De un borde a otro con margen para entrar y salir de cuadro. Van
        # juntos y no repartidos por toda la pantalla: repartidos, la columna
        # de botones tapa siempre a dos, y la idea es que se vea la familia
        # entera. En grupo cruzan los claros de izquierda y derecha completos.
        self.recorrido = ANCHO_VENTANA + CAMINATA_TAM * 2

    # ── Textos ────────────────────────────────────────────────────────────────
    def _crear_textos(self):
        """Crea todos los objetos Text del menú. Se llama una sola vez en __init__."""
        cx = ANCHO_VENTANA // 2

        self.txt_titulo    = arcade.Text("UAIBOT", cx, ALTO_VENTANA - 90,
                                          arcade.color.GOLD, 56, anchor_x="center", bold=True)
        self.txt_subtitulo = arcade.Text("OFIRCA 2026", cx, ALTO_VENTANA - 132,
                                          (52, 152, 219), 18, anchor_x="center")
        self.txt_highscore = arcade.Text(f"Highscore: {self.datos['highscore']}",
                                          cx, ALTO_VENTANA - 164,
                                          arcade.color.GOLD, 13, anchor_x="center")

        # Con 6 opciones el espaciado se achica respecto a la versión de 3
        # (Ronda 1 usaba 60px entre botones; acá 46px para que las 6 entren
        # en la ventana sin superponerse con las instrucciones de abajo).
        self.espaciado_opciones = 46
        self.y_primera_opcion   = ALTO_VENTANA - 210

        self.txt_opciones  = [
            arcade.Text(op, cx, self.y_primera_opcion - i * self.espaciado_opciones,
                        arcade.color.WHITE, 17, anchor_x="center")
            for i, op in enumerate(OPCIONES)
        ]
        self.txt_instruccion = arcade.Text("↑↓ para navegar   ENTER para seleccionar",
                                            cx, 34, (150, 150, 150), 11, anchor_x="center")

        # Subtexto de Ajustes (solo visible en el submenu): un resumen de la
        # configuración actual, refrescado por _actualizar_subtextos.
        idx_ajustes = OPCIONES.index("Ajustes")
        y_ajustes   = self.y_primera_opcion - idx_ajustes * self.espaciado_opciones - 18
        self.txt_controles_val = arcade.Text("", cx, y_ajustes,
                                              (52, 152, 219), 11, anchor_x="center")
        self._actualizar_subtextos()

    def _actualizar_subtextos(self):
        """Refresca el resumen de configuración que se ve bajo el botón."""
        controles = self.datos.get("controles", "flechas")
        vol_menu  = int(self.datos.get("volumen_musica_menu", 0.3) * 100)
        vol_nivel = int(self.datos.get("volumen_musica_nivel", 0.3) * 100)
        self.txt_controles_val.value = f"{controles} · música {vol_menu}% / {vol_nivel}%"

    # ── Animación del fondo ───────────────────────────────────────────────────
    def on_show_view(self):
        """Arranca la música del menú. Se usa on_show_view y no __init__ porque
        __init__ también corre antes de que la ventana muestre esta vista; acá
        se garantiza que suena cada vez que el menú aparece en pantalla."""
        self.detener_musica()
        Menu.musica_player = arcade.play_sound(
            self.musica, volume=self.datos.get("volumen_musica_menu", 0.3), loop=True)

    @classmethod
    def detener_musica(cls):
        """Detiene la música del menú si estaba sonando."""
        if cls.musica_player:
            arcade.stop_sound(cls.musica_player)
            cls.musica_player = None

    def on_update(self, delta_time):
        """Avanza el desfile de la familia. El menú no tenía on_update: era una
        pantalla estática, y esta es la única animación que corre acá."""
        self.desplazamiento = (self.desplazamiento
                               + CAMINATA_VELOCIDAD * delta_time) % self.recorrido
        self.timer_caminata += delta_time
        if self.timer_caminata >= 1 / CAMINATA_FPS:
            self.timer_caminata -= 1 / CAMINATA_FPS
            self.frame_caminata += 1

        # Nubes: acumulador continuo para la deriva (velocidades fraccionales)
        # y timer propio para el morphing del spritesheet.
        self.tiempo_nubes += delta_time
        self.timer_nubes  += delta_time
        if self.timer_nubes >= 1 / NUBES_FPS:
            self.timer_nubes -= 1 / NUBES_FPS
            self.frame_nubes += 1

        # Pájaros y luciérnagas: mismo patrón, cada uno a su ritmo.
        self.timer_pajaros += delta_time
        if self.timer_pajaros >= 1 / PAJAROS_FPS:
            self.timer_pajaros -= 1 / PAJAROS_FPS
            self.frame_pajaros += 1

        self.timer_luciernagas += delta_time
        if self.timer_luciernagas >= 1 / LUCIERNAGAS_FPS:
            self.timer_luciernagas -= 1 / LUCIERNAGAS_FPS
            self.frame_luciernagas += 1

    def _dibujar_nubes(self):
        """Dibuja las tres nubes del fondo animado: cada una deriva a su
        velocidad y comparte el frame de morphing. La transparencia crece
        con la altura para que las lejanas se integren al cielo."""
        recorrido = ANCHO_VENTANA + NUBE_TAM
        frame     = self.frames_nubes[self.frame_nubes % len(self.frames_nubes)]
        for y, velocidad, fase, alpha in NUBES:
            x = -NUBE_TAM + (fase * recorrido
                             + self.tiempo_nubes * velocidad) % recorrido
            arcade.draw_texture_rect(
                frame, arcade.XYWH(x, y, NUBE_TAM, NUBE_TAM),
                color=arcade.types.Color(255, 255, 255, alpha)
            )

    def _dibujar_pajaros(self):
        """Dos pájaros cruzando el cielo aleteando (frames a PAJAROS_FPS).
        Van más alto y más rápido que las nubes: son la capa media del
        fondo animado."""
        recorrido = ANCHO_VENTANA + PAJARO_TAM
        frame     = self.frames_pajaros[self.frame_pajaros % len(self.frames_pajaros)]
        for y, velocidad, fase in PAJAROS:
            x = -PAJARO_TAM + (fase * recorrido
                               + self.tiempo_nubes * velocidad) % recorrido
            arcade.draw_texture_rect(
                frame, arcade.XYWH(x, y, PAJARO_TAM, PAJARO_TAM),
                color=arcade.types.Color(255, 255, 255, 220)
            )

    def _dibujar_luciernagas(self):
        """Las luciérnagas deambulan cerca del pasto con un vaivén suave
        (seno en x e y, desfasado para que no orbiten en círculos) y su
        brillo pulsa con el sprite. Van al final para que titilen por
        encima de la familia que camina."""
        frame = self.frames_luciernagas[self.frame_luciernagas
                                        % len(self.frames_luciernagas)]
        t     = self.tiempo_nubes
        for cx, cy, ampx, ampy, vel, fase in LUCIERNAGAS:
            x = cx + math.sin(vel * t + fase) * ampx
            y = cy + math.sin(vel * t * 1.7 + fase * 2.0) * ampy
            arcade.draw_texture_rect(
                frame, arcade.XYWH(x, y, LUCIERNAGA_TAM, LUCIERNAGA_TAM),
                color=arcade.types.Color(255, 255, 255, 230)
            )

    def _dibujar_caminata(self):
        """Dibuja a los cuatro cruzando el sendero, repartidos parejo y en loop.

        El módulo sobre len(frames) es necesario porque cada personaje puede
        traer distinta cantidad de poses (UAIBOT tiene 6, sus hermanos 4)."""
        # el personaje va apoyado al fondo de su frame, así que los pies caen
        # en el borde inferior del cuadrado que se dibuja
        y_pies = CAMINATA_Y - CAMINATA_TAM / 2 + 2

        for i, id_personaje in enumerate(self.orden_desfile):
            datos  = self.familia[id_personaje]
            frames = datos["walk"]
            x = -CAMINATA_TAM + (i * CAMINATA_SEPARACION
                                 + self.desplazamiento) % self.recorrido

            arcade.draw_ellipse_filled(x, y_pies, CAMINATA_TAM * 0.17,
                                       CAMINATA_TAM * 0.05, CAMINATA_SOMBRA)
            arcade.draw_texture_rect(
                frames[self.frame_caminata % len(frames)],
                arcade.XYWH(x, CAMINATA_Y, CAMINATA_TAM, CAMINATA_TAM),
                color=arcade.types.Color(*self._tinte_escena(datos["color"]))
            )

    @staticmethod
    def _tinte_escena(color):
        """Multiplica el color del personaje por la luz de la escena. Se
        multiplica en vez de reemplazar para no perder el tinte de los
        personajes que todavía no tienen arte propio."""
        return tuple(c * luz // 255 for c, luz in zip(color, CAMINATA_LUZ))

    # ── Eventos de teclado ────────────────────────────────────────────────────
    def on_key_press(self, symbol, modifiers):
        if self.submenu == "ajustes":
            self._manejar_ajustes(symbol)
        else:
            self._manejar_menu(symbol)

    def _manejar_menu(self, symbol):
        if symbol == arcade.key.UP:
            self.opcion_seleccionada = (self.opcion_seleccionada - 1) % len(OPCIONES)
        elif symbol == arcade.key.DOWN:
            self.opcion_seleccionada = (self.opcion_seleccionada + 1) % len(OPCIONES)
        elif symbol == arcade.key.ENTER:
            self._elegir_opcion(OPCIONES[self.opcion_seleccionada])

    def _elegir_opcion(self, opcion):
        """Punto único de entrada para resolver qué hacer al elegir una
        opción del menú, sea por teclado o por mouse."""
        if opcion == "Tutorial":
            self._iniciar_tutorial()
        elif opcion == "Infinito":
            self._iniciar_infinito()
        elif opcion == "Viaje":
            self._iniciar_viaje()
        elif opcion == "Multijugador":
            self._iniciar_multijugador()
        elif opcion == "Ajustes":
            self.submenu = "ajustes"
        elif opcion == "Inventario / Bestiario":
            self._iniciar_inventario()
        elif opcion in MODOS_PENDIENTES:
            self.window.show_view(Placeholder(opcion))

    def _manejar_ajustes(self, symbol):
        """Navega el submenu de Ajustes: ↑↓ elige fila, ← → cambia el valor
        de esa fila (controles o volumen), ESC cierra el submenu."""
        if symbol == arcade.key.UP:
            self.ajuste_seleccionado = (self.ajuste_seleccionado - 1) % len(FILAS_AJUSTES)
        elif symbol == arcade.key.DOWN:
            self.ajuste_seleccionado = (self.ajuste_seleccionado + 1) % len(FILAS_AJUSTES)
        elif symbol in (arcade.key.LEFT, arcade.key.RIGHT):
            direccion = 1 if symbol == arcade.key.RIGHT else -1
            self._cambiar_ajuste(self.ajuste_seleccionado, direccion)
        elif symbol == arcade.key.ESCAPE:
            self.submenu = None
            self.ajuste_seleccionado = 0

    def _cambiar_ajuste(self, fila, direccion):
        """Aplica y persiste el cambio de la fila indicada.

        El volumen del menú se aplica EN VIVO sobre el player que ya está
        sonando (el player de pyglet acepta .volume a mitad de reproducción),
        así el jugador escucha el efecto sin cortar la música; el de niveles
        solo se guarda y rige desde la próxima partida que arranque."""
        if fila == 0:  # Controles: flechas <-> wasd
            actual = self.datos.get("controles", "flechas")
            guardado.actualizar_controles("wasd" if actual == "flechas" else "flechas")
        elif fila == 1:  # Volumen de la música del menú
            actual = self.datos.get("volumen_musica_menu", 0.3)
            nuevo   = min(1.0, max(0.0, round(actual + direccion * PASO_VOLUMEN, 2)))
            if Menu.musica_player:
                Menu.musica_player.volume = nuevo
            guardado.actualizar_volumenes(menu=nuevo)
        elif fila == 2:  # Volumen de la música de los niveles
            actual = self.datos.get("volumen_musica_nivel", 0.3)
            nuevo   = min(1.0, max(0.0, round(actual + direccion * PASO_VOLUMEN, 2)))
            guardado.actualizar_volumenes(nivel=nuevo)

        self.datos = guardado.cargar()
        self._actualizar_subtextos()

    # ── Eventos de mouse ──────────────────────────────────────────────────────
    def _opcion_bajo_cursor(self, x, y):
        """Devuelve el índice de la opción bajo (x, y), o None si no hay
        ninguna. Centraliza el cálculo del hitbox para que on_mouse_motion
        y on_mouse_press usen siempre el mismo criterio."""
        cx = ANCHO_VENTANA // 2
        for i in range(len(OPCIONES)):
            y_boton = self.y_primera_opcion - i * self.espaciado_opciones
            if (cx - 140 <= x <= cx + 140) and (y_boton - 20 <= y <= y_boton + 20):
                return i
        return None

    def on_mouse_motion(self, x, y, dx, dy):
        """Resalta la opción bajo el cursor cuando no hay submenú abierto."""
        if self.submenu is not None:
            return
        indice = self._opcion_bajo_cursor(x, y)
        if indice is not None:
            self.opcion_seleccionada = indice

    def on_mouse_press(self, x, y, button, modifiers):
        """Selecciona la opción bajo el cursor al hacer click izquierdo."""
        if button != arcade.MOUSE_BUTTON_LEFT or self.submenu is not None:
            return
        indice = self._opcion_bajo_cursor(x, y)
        if indice is not None:
            self.opcion_seleccionada = indice
            self._elegir_opcion(OPCIONES[indice])

    # ── Inicio de partida ─────────────────────────────────────────────────────
    def _iniciar_tutorial(self):
        """Arranca el nivel único de Tutorial (tutorial.py), donde se
        cumplen las 13 consignas graduadas de OFIRCA — separado de la
        progresión de 10 niveles con dificultad que usa Juego."""
        self.detener_musica()
        from tutorial import Tutorial
        vista = Tutorial(controles=self.datos.get("controles", "flechas"))
        vista.setup()
        self.window.show_view(vista)

    def _iniciar_infinito(self):
        """Arranca Juego (juego.py) sin selección manual de dificultad:
        escala sola cada 10 niveles y no tiene techo de nivel."""
        self.detener_musica()
        from juego import Juego
        juego = Juego(controles=self.datos.get("controles", "flechas"))
        juego.setup()
        self.window.show_view(juego)

    def _iniciar_viaje(self):
        """Arranca la campaña (viaje.py): 10 niveles fijos diseñados en
        Tiled, con cronómetro y desbloqueo de personajes."""
        self.detener_musica()
        from viaje import Viaje
        vista = Viaje(controles=self.datos.get("controles", "flechas"))
        vista.setup()
        self.window.show_view(vista)

    def _iniciar_multijugador(self):
        """Abre la sala de multijugador (multijugador.py), donde se crea
        una partida o se entra a una existente por la red local."""
        self.detener_musica()
        from multijugador import SalaMultijugador
        self.window.show_view(SalaMultijugador(
            controles=self.datos.get("controles", "flechas")
        ))

    def _iniciar_inventario(self):
        """Abre el Inventario/Bestiario: la familia con sus habilidades y
        los objetos coleccionables del Multijugador con su descripción.
        La música del menú sigue sonando (como en el Placeholder)."""
        self.window.show_view(Inventario())

    # ── Dibujo ────────────────────────────────────────────────────────────────
    def on_draw(self):
        self.window.clear((20, 28, 36))

        # Fondo ilustrado con overlay oscuro para legibilidad del texto
        arcade.draw_texture_rect(
            self.img_fondo,
            arcade.XYWH(ANCHO_VENTANA // 2, ALTO_VENTANA // 2, ANCHO_VENTANA, ALTO_VENTANA)
        )
        self._dibujar_nubes()
        self._dibujar_pajaros()
        self._dibujar_caminata()
        self._dibujar_luciernagas()
        arcade.draw_lrbt_rectangle_filled(0, ANCHO_VENTANA, 0, ALTO_VENTANA, (0, 0, 0, 100))

        self.txt_titulo.draw()
        self.txt_subtitulo.draw()
        self.txt_highscore.draw()
        self.txt_instruccion.draw()

        cx = ANCHO_VENTANA // 2
        for i, txt in enumerate(self.txt_opciones):
            y = self.y_primera_opcion - i * self.espaciado_opciones
            seleccionada = (i == self.opcion_seleccionada and self.submenu is None)
            ancho = 260 if seleccionada else 240
            ribbon = self.img_btn[i]
            arcade.draw_texture_rect(ribbon, arcade.XYWH(cx, y - 4, ancho, 40))
            txt.color = arcade.color.WHITE if seleccionada else (200, 200, 200)
            txt.draw()

        if self.submenu == "ajustes":
            self._dibujar_submenu_ajustes()

    def _dibujar_submenu_ajustes(self):
        """Dibuja el cuadro de Ajustes: una fila por ajuste con su valor,
        la activa resaltada en dorado. Reusa el marco nine-patch del
        submenu de siempre, con más alto porque entran tres filas."""
        cx = ANCHO_VENTANA // 2
        cy = ALTO_VENTANA // 2
        ancho, alto = 440, 220

        marco = spr.marco(PANEL_MARCO)
        if marco is not None:
            marco.draw_rect(rect=arcade.XYWH(cx, cy, ancho, alto))
        else:
            arcade.draw_lrbt_rectangle_filled(cx - 220, cx + 220, cy - 110, cy + 110, (30, 39, 46))
            arcade.draw_lrbt_rectangle_outline(cx - 220, cx + 220, cy - 110, cy + 110, (52, 152, 219), 2)

        arcade.Text("Ajustes", cx, cy + 78, arcade.color.GOLD, 18,
                    anchor_x="center", bold=True).draw()

        # El valor de cada fila al lado de su etiqueta: el control actual y
        # los volúmenes como porcentaje. La fila activa se lee en dorado con
        # los adjudicadores de siempre para indicar que ← → la cambia.
        valores = [
            self.datos.get("controles", "flechas"),
            f"{int(self.datos.get('volumen_musica_menu', 0.3) * 100)}%",
            f"{int(self.datos.get('volumen_musica_nivel', 0.3) * 100)}%",
        ]
        for i, fila in enumerate(FILAS_AJUSTES):
            y      = cy + 34 - i * 38
            activa = (i == self.ajuste_seleccionado)
            color  = arcade.color.GOLD if activa else (170, 170, 170)
            arcade.Text(fila, cx - 190, y, color, 14).draw()
            arcade.Text(f"< {valores[i]} >", cx + 120, y, color, 14,
                        anchor_x="center").draw()

        arcade.Text("↑↓ para elegir   ← → para cambiar   ESC para volver",
                    cx, cy - 80, (120, 120, 120), 11, anchor_x="center").draw()


class Inventario(arcade.View):
    """Inventario / Bestiario (Fase 5 del plan): dos secciones.

    - PERSONAJES: la familia completa con su habilidad. Los aún no
      desbloqueados en Modo Viaje se ven oscurecidos y sin datos — es el
      "bestiario" que se completa jugando la campaña.
    - OBJETOS: los 10 coleccionables cooperativos del Multijugador, cada
      uno con su descripción. El que todavía no se consiguió se ve
      desvanecido; conseguirlo es parte de la Fase 4.

    Navegación: ←→ mueve la selección dentro de la sección, ↑↓ cambia de
    sección, ESC vuelve al menú. La música del menú sigue sonando, como en
    el Placeholder."""

    def __init__(self):
        super().__init__()
        self.seccion       = 0    # 0 = personajes, 1 = objetos
        self.sel_personaje = 0
        self.sel_objeto    = 0

        # Texturas: la familia reusa las mismas hojas que el fondo del menú
        # (frame 0 de Idle, el "retrato"), y los objetos ya son PNG chicos.
        self.familia     = spr.cargar_familia(PERSONAJES_FAMILIA, 128, 128)
        self.img_objetos = [spr.cargar(o["archivo"]) for o in OBJETOS_MULTIJUGADOR]

    def on_show_view(self):
        """Se releen los desbloqueos cada vez que se entra, así lo conseguido
        en otra partida aparece sin reiniciar el juego."""
        self.datos = guardado.cargar()

    # ── Eventos ───────────────────────────────────────────────────────────
    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.ESCAPE:
            self.window.show_view(Menu())
        elif symbol == arcade.key.UP:
            self.seccion = (self.seccion - 1) % 2
        elif symbol == arcade.key.DOWN:
            self.seccion = (self.seccion + 1) % 2
        elif self.seccion == 0:
            if symbol in (arcade.key.LEFT, arcade.key.RIGHT):
                paso = -1 if symbol == arcade.key.LEFT else 1
                self.sel_personaje = (self.sel_personaje + paso) % len(PERSONAJES_FAMILIA)
        elif self.seccion == 1:
            if symbol in (arcade.key.LEFT, arcade.key.RIGHT):
                paso = -1 if symbol == arcade.key.LEFT else 1
                self.sel_objeto = (self.sel_objeto + paso) % len(OBJETOS_MULTIJUGADOR)
            elif symbol in (arcade.key.UP, arcade.key.DOWN):
                # En la grilla de 5 columnas, subir/bajar es saltar de fila.
                fila = -5 if symbol == arcade.key.UP else 5
                self.sel_objeto = (self.sel_objeto + fila) % len(OBJETOS_MULTIJUGADOR)

    # ── Dibujo ────────────────────────────────────────────────────────────
    def on_draw(self):
        self.window.clear((20, 28, 36))
        cx = ANCHO_VENTANA // 2

        arcade.Text("INVENTARIO / BESTIARIO", cx, ALTO_VENTANA - 50,
                    arcade.color.GOLD, 26, anchor_x="center", bold=True).draw()

        # Solapas de sección: la activa en dorado, la otra en gris.
        for i, nombre in enumerate(("PERSONAJES", "OBJETOS")):
            color = arcade.color.GOLD if i == self.seccion else (120, 120, 120)
            arcade.Text(nombre, cx + (i - 0.5) * 220, ALTO_VENTANA - 92,
                        color, 14, anchor_x="center", bold=True).draw()

        if self.seccion == 0:
            self._dibujar_personajes()
        else:
            self._dibujar_objetos()

        arcade.Text("←→ moverse   ↑↓ cambiar sección   ESC para volver",
                    cx, 24, (120, 120, 120), 11, anchor_x="center").draw()

    def _dibujar_personajes(self):
        """La familia en fila: retrato (Idle frame 0), nombre en su color y,
        abajo, la habilidad del seleccionado. Bloqueado = oscurecido."""
        cx, cy = ANCHO_VENTANA // 2, ALTO_VENTANA // 2
        desbloqueados = self.datos["personajes_desbloqueados"]

        for i, personaje in enumerate(PERSONAJES_FAMILIA):
            x       = cx + (i - 1.5) * 190
            activo  = (i == self.sel_personaje)
            abierto = personaje["id"] in desbloqueados

            if activo:
                arcade.draw_lrbt_rectangle_outline(
                    x - 75, x + 75, cy - 40, cy + 110, arcade.color.GOLD, 2)

            frame = self.familia[personaje["id"]]["idle"][0]
            # Sin desbloquear se dibuja casi negro: se ve la silueta, no el
            # detalle — el incentivo a jugar la campaña es conocerlos.
            tinte = (60, 60, 60) if not abierto else personaje["color"]
            arcade.draw_texture_rect(frame, arcade.XYWH(x, cy + 35, 110, 110),
                                     color=arcade.types.Color(*tinte))
            nombre = personaje["nombre"] if abierto else "??????"
            arcade.Text(nombre, x, cy - 25, personaje["color"] if abierto else (110, 110, 110),
                        13, anchor_x="center", bold=True).draw()

        # Ficha del personaje seleccionado
        personaje = PERSONAJES_FAMILIA[self.sel_personaje]
        y = cy - 120
        if personaje["id"] in desbloqueados:
            arcade.Text(
                f"{personaje['nombre']} — {personaje['habilidad_nombre']}",
                cx, y, arcade.color.WHITE, 15, anchor_x="center", bold=True).draw()
            extra = (f"{personaje['habilidad_desc']}. "
                     "Disponible desde el inicio en Tutorial y Multijugador; "
                     "en Modo Viaje se suma al equipo al avanzar la campaña.")
            arcade.Text(extra, cx, y - 30, (200, 200, 200), 12,
                        anchor_x="center", multiline=True, width=760).draw()
        else:
            arcade.Text("Aún no se sumó al equipo.", cx, y,
                        (200, 120, 120), 14, anchor_x="center", bold=True).draw()
            arcade.Text("Se desbloquea avanzando el Modo Viaje.",
                        cx, y - 28, (200, 200, 200), 12, anchor_x="center").draw()

    def _dibujar_objetos(self):
        """Los 10 coleccionables en grilla de 5×2 con su ficha debajo.
        Sin conseguir = desvanecido; la selección se marca en dorado."""
        cx, cy = ANCHO_VENTANA // 2, ALTO_VENTANA // 2
        conseguidos = self.datos["objetos_multijugador"]

        for i, objeto in enumerate(OBJETOS_MULTIJUGADOR):
            col, fila = i % 5, i // 5
            x = cx + (col - 2) * 125
            y = cy + 95 - fila * 120
            activo = (i == self.sel_objeto)

            if activo:
                arcade.draw_lrbt_rectangle_outline(
                    x - 52, x + 52, y - 52, y + 52, arcade.color.GOLD, 2)

            # Sin conseguir se ve la silueta desvanecida: alcanza para
            # reconocerlo, pero invita a ir a buscarlo.
            alpha = 255 if objeto["id"] in conseguidos else 90
            arcade.draw_texture_rect(
                self.img_objetos[i], arcade.XYWH(x, y, 76, 76),
                color=arcade.types.Color(255, 255, 255, alpha))

        # Ficha del objeto seleccionado
        objeto = OBJETOS_MULTIJUGADOR[self.sel_objeto]
        estado = "Conseguido" if objeto["id"] in conseguidos \
                 else "Aún no conseguido — se encuentra en el Modo Multijugador"
        color_estado = (100, 200, 100) if objeto["id"] in conseguidos else (200, 120, 120)
        arcade.Text(objeto["nombre"], cx, cy - 105, arcade.color.WHITE, 15,
                    anchor_x="center", bold=True).draw()
        arcade.Text(objeto["descripcion"], cx, cy - 140, (200, 200, 200), 12,
                    anchor_x="center", multiline=True, width=700).draw()
        arcade.Text(estado, cx, cy - 205, color_estado, 12,
                    anchor_x="center", bold=True).draw()


class Placeholder(arcade.View):
    """Pantalla temporal para los modos que todavía no tienen contenido
    propio. Queda sin uso desde que Inventario/Bestiario pasó a tener su
    pantalla (Fase 5), pero se mantiene: es el destino natural de cualquier
    entrada futura del menú que todavía no exista."""

    def __init__(self, titulo):
        super().__init__()
        self.titulo = titulo

    def on_draw(self):
        self.window.clear((20, 28, 36))
        cx, cy = ANCHO_VENTANA // 2, ALTO_VENTANA // 2
        arcade.Text(self.titulo, cx, cy + 30, arcade.color.GOLD, 32,
                    anchor_x="center", anchor_y="center", bold=True).draw()
        arcade.Text("Proximamente", cx, cy - 10, (200, 200, 200), 16,
                    anchor_x="center", anchor_y="center").draw()
        arcade.Text("ESC para volver al menu", cx, cy - 50, (120, 120, 120), 12,
                    anchor_x="center", anchor_y="center").draw()

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.ESCAPE:
            self.window.show_view(Menu())