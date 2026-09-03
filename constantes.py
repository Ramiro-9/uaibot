# constantes.py
# Configuración global del juego: tamaños, rutas y posiciones clave.
# Todos los demás módulos importan de acá para mantener consistencia.

# ── Dimensiones de la grilla ──────────────────────────────────────────────────
COLUMNAS = 14          # cantidad de columnas visibles en modo fácil
FILAS    = 10          # cantidad de filas
TAM_CELDA = 60         # tamaño en píxeles de cada celda cuadrada

ANCHO_JUEGO = COLUMNAS * TAM_CELDA   # ancho del área de juego en píxeles
ALTO_JUEGO  = FILAS    * TAM_CELDA   # alto del área de juego en píxeles

# ── Ventana ───────────────────────────────────────────────────────────────────
PANEL_ANCHO   = 280                        # ancho del panel informativo derecho
ANCHO_VENTANA = ANCHO_JUEGO + PANEL_ANCHO  # ancho total de la ventana
ALTO_VENTANA  = ALTO_JUEGO                 # alto total de la ventana

TITULO = "UAIBOT - OFIRCA 2026"

# ── Posiciones especiales (col, fila) ─────────────────────────────────────────
POS_INICIO    = (0, FILAS - 1)      # UAIBOT arranca en la esquina superior izquierda
POS_MERENDERO = (COLUMNAS - 1, 0)   # destino final en modo fácil (esquina inferior derecha)

# ── Rutas de sprites (con fallback a color si el archivo no existe) ───────────
SPRITE_CESPED           = "assets/imagenes/cesped.png"
SPRITE_PARED            = "assets/imagenes/pared.png"
SPRITE_HUELLA_ARRIBA    = "assets/imagenes/huella_arriba.png"
SPRITE_HUELLA_ABAJO     = "assets/imagenes/huella_abajo.png"
SPRITE_HUELLA_IZQUIERDA = "assets/imagenes/huella_izquierda.png"
SPRITE_HUELLA_DERECHA   = "assets/imagenes/huella_derecha.png"
SPRITE_HIELO            = "assets/imagenes/hielo.png"
SPRITE_PLACA            = "assets/imagenes/placa.png"
SPRITE_PUERTA_LLAVE     = "assets/imagenes/puerta_llave_anim.png"
SPRITE_PUERTA_PLACA     = "assets/imagenes/puerta_placa_anim.png"
SPRITE_CAJA             = "assets/imagenes/caja.png"

# Un sprite por tipo de donación del Modo Viaje. La clave es el valor de la
# propiedad "tipo" del objeto "donacion" en Tiled.
DONACIONES_SPRITES = {
    "comida":   "assets/imagenes/donacion_comida.png",
    "libros":   "assets/imagenes/donacion_libros.png",
    "juguetes": "assets/imagenes/donacion_juguetes.png",
    # Las sillas de ruedas ya aparecen en el Tutorial, donde son una
    # mecánica —hay que pasarles por al lado sin pisarlas—. Acá son una
    # donación más, con las mismas reglas que las otras tres: se recoge
    # pisándola y suma al contador del panel.
    "sillas":   "assets/imagenes/donacion_sillas.png",
}

# ── Íconos y marcos de la interfaz ────────────────────────────────────────────
# Acompañan al texto del panel lateral. Si falta alguno, sprites.dibujar_icono
# simplemente no dibuja nada y el texto sigue alcanzando.
ICONO_PASOS = "assets/imagenes/icono_pasos.png"
ICONO_RELOJ = "assets/imagenes/icono_reloj.png"
ICONO_LLAVE = "assets/imagenes/icono_llave.png"
PANEL_MARCO = "assets/imagenes/panel_marco.png"

# Un ícono por habilidad, con la misma clave que usa PERSONAJES_FAMILIA
ICONOS_HABILIDAD = {
    "carga":   "assets/imagenes/icono_carga.png",
    "rampa":   "assets/imagenes/icono_rampa.png",
    "guia":    "assets/imagenes/icono_guia.png",
    "alcance": "assets/imagenes/icono_alcance.png",
}

# ── Colores de UI ─────────────────────────────────────────────────────────────
COLOR_ACENTO = (52, 152, 219)   # azul usado en títulos y bordes del panel

# ── La familia de UAIBOT: personajes jugables ─────────────────────────────────
# Los 4 personajes que se pueden alternar con la tecla C. Los usan dos
# modos, con reglas distintas: en Tutorial están los cuatro disponibles
# desde el arranque, cada uno con su cupo de pasos (consigna 2 de la Ronda
# 2); en Viaje se van desbloqueando al superar niveles y no tienen cupo.
#
# Reutilizan el mismo spritesheet Idle/Walk de UAIBOT (no hace falta arte
# nuevo): "color" es un tinte que se aplica sobre la textura para que se
# distingan entre sí, con el mismo espíritu que el resto del código usa un
# color de fallback cuando falta un sprite propio.
# Cada personaje tiene además una HABILIDAD propia, que funciona en Modo
# Viaje y en Multijugador (en Tutorial no: ahí las reglas las fija la
# consigna de la Ronda 2). Están pensadas como tecnología asistiva —cosas
# que quitan barreras—, que es el eje del certamen:
#
#   carga    UAIBOT     empuja cajas para llevar las donaciones (pasiva)
#   rampa    UAIBOTA    una rampa vuelve transitable una celda ya recorrida
#   guia     UAIBOTINA  señaliza el camino que queda hasta el merendero
#   alcance  UAIBOTINO  un alcanzador toma cosas de una celda vecina (pasiva)
#
# "usos_por_nivel" en None significa sin límite. Solo la rampa está
# limitada, porque es la única que rompe la regla central del juego -no se
# puede repisar el camino- y sin tope volvería triviales los niveles.
MAX_PASOS_PERSONAJE = 8   # cupo de pasos de cada personaje en Tutorial,
                          # antes de tener que cambiar a otro
PERSONAJES_FAMILIA = [
    {"id": "uaibot",    "nombre": "UAIBOT",    "color": (255, 255, 255),
     "habilidad": "carga",   "habilidad_nombre": "Carga",
     "habilidad_desc": "Empuja cajas",       "usos_por_nivel": None},
    {"id": "uaibota",   "nombre": "UAIBOTA",   "color": (255, 170, 210),
     "habilidad": "rampa",   "habilidad_nombre": "Rampa",
     "habilidad_desc": "Cruza lo recorrido", "usos_por_nivel": 1},
    {"id": "uaibotina", "nombre": "UAIBOTINA", "color": (170, 210, 255),
     "habilidad": "guia",    "habilidad_nombre": "Guia",
     "habilidad_desc": "Muestra la ruta",    "usos_por_nivel": None},
    {"id": "uaibotino", "nombre": "UAIBOTINO", "color": (170, 255, 190),
     "habilidad": "alcance", "habilidad_nombre": "Alcance",
     "habilidad_desc": "Toma de al lado",    "usos_por_nivel": None},
]

# Archivo de texto plano (no JSON) donde Tutorial guarda nombre + tiempo de
# cada partida ganada, tal como pide la consigna 4 de Ronda 2.
ARCHIVO_PUNTAJES_TUTORIAL = "puntajes_tutorial.txt"

# ── Objetos coleccionables del Modo Multijugador ──────────────────────────────
# Un objeto por cada uno de los 10 mapas de dificultad difícil. Todos giran
# en torno a la familia de UAIBOT y el merendero: recuerdos, herramientas y
# tecnología asistiva, que es el eje del certamen. En el Multijugador se
# consiguen cooperando (objeto recolectable cooperativo, Fase 4 del plan);
# el Inventario los muestra con su descripción y cuáles ya se consiguieron.
OBJETOS_MULTIJUGADOR = [
    {"id": "foto",       "archivo": "assets/imagenes/objeto_foto.png",
     "nombre": "Foto de familia",
     "descripcion": "Retrato del día en que los cuatro se conocieron en el merendero. UAIBOT lo guarda en su compartimento más seguro."},
    {"id": "tornillo",   "archivo": "assets/imagenes/objeto_tornillo.png",
     "nombre": "Tornillo dorado",
     "descripcion": "El primer repuesto que UAIBOT ajustó solo. Desde entonces, cada tornillo que aprieta lo hace con el mismo orgullo."},
    {"id": "mochila",    "archivo": "assets/imagenes/objeto_mochila.png",
     "nombre": "Mochila de UAIBOTA",
     "descripcion": "Con ella, UAIBOTA carga las donaciones más pesadas. Tiene un bolsillo secreto para las galletas."},
    {"id": "farol",      "archivo": "assets/imagenes/objeto_farol.png",
     "nombre": "Farol de UAIBOTINA",
     "descripcion": "Con su luz, UAIBOTINA señala el camino al merendero cuando el atardecer empieza a apagarse."},
    {"id": "alcanzador", "archivo": "assets/imagenes/objeto_alcanzador.png",
     "nombre": "Alcanzador de UAIBOTINO",
     "descripcion": "Le permite tomar lo que está a una celda de distancia sin moverse de su lugar. Lo presta siempre que alguien lo necesita."},
    {"id": "rueda",      "archivo": "assets/imagenes/objeto_rueda.png",
     "nombre": "Rueda de repuesto",
     "descripcion": "La rueda con la que UAIBOT aprendió a caminar. La familia la guarda como recuerdo de sus primeros pasos torpes."},
    {"id": "herramientas", "archivo": "assets/imagenes/objeto_herramientas.png",
     "nombre": "Caja de herramientas",
     "descripcion": "Con ella, la familia reparó la silla de ruedas del merendero. Nadie explica cómo caben tantas herramientas adentro."},
    {"id": "panel",      "archivo": "assets/imagenes/objeto_panel.png",
     "nombre": "Panel solar",
     "descripcion": "Energía limpia para cargar las baterías de toda la familia. Se despliega en el techo del merendero."},
    {"id": "bateria",    "archivo": "assets/imagenes/objeto_bateria.png",
     "nombre": "Batería recargable",
     "descripcion": "Guarda la energía sobrante del día para la cena del merendero. Nunca se agota frente a quien la necesita."},
    {"id": "taza",       "archivo": "assets/imagenes/objeto_taza.png",
     "nombre": "Taza del merendero",
     "descripcion": "Se la regalaron a la familia al entregar su primera donación. Toman chocolate de ella en cada aniversario."},
]