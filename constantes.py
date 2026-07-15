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
SPRITE_CESPED           = "assets/cesped.png"
SPRITE_TIERRA           = "assets/tierra.png"
SPRITE_PARED            = "assets/pared.png"
SPRITE_PORTAL           = "assets/portal.png"
SPRITE_LLAVE            = "assets/llave.png"
SPRITE_HUELLA_ARRIBA    = "assets/huella_arriba.png"
SPRITE_HUELLA_ABAJO     = "assets/huella_abajo.png"
SPRITE_HUELLA_IZQUIERDA = "assets/huella_izquierda.png"
SPRITE_HUELLA_DERECHA   = "assets/huella_derecha.png"
SPRITE_HIELO            = "assets/hielo.png"
SPRITE_TELEPORTE        = "assets/teleporte.png"
SPRITE_PLACA            = "assets/placa.png"
SPRITE_PUERTA_LLAVE     = "assets/puerta_llave_anim.png"
SPRITE_PUERTA_PLACA     = "assets/puerta_placa_anim.png"

# ── Colores de UI ─────────────────────────────────────────────────────────────
COLOR_ACENTO = (52, 152, 219)   # azul usado en títulos y bordes del panel