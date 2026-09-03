# nivel.py
# Genera o carga los datos de cada nivel. Hay dos fuentes posibles:
#   - Generación procedural, con BFS para garantizar que siempre exista
#     solución. La dificultad ajusta cuántas paredes, hielo, teleportes y
#     llave aparecen.
#   - Mapas .tmx dibujados a mano en Tiled (carpeta mapas/), que existen
#     numerados 1 a 10 por dificultad.
#
# Quién usa qué:
#   - Modo Infinito llama con usar_tiled=False: siempre procedural, en
#     todas las dificultades. Un modo "infinito" pierde sentido si repite
#     un conjunto finito de mapas hechos a mano.
#   - Modo Viaje (todavía sin implementar) es el que va a usar los mapas
#     de Tiled, porque son niveles fijos diseñados uno por uno.

import random
import mapa as mapa_mod
from constantes import *

# ── Punto de entrada: de dónde sale cada nivel ──────────────────────────────

def generar_nivel(numero_nivel, dificultad, usar_tiled=True):
    """Punto de entrada principal. Decide si generar el nivel de forma
    procedural o cargarlo desde un mapa de Tiled.

    Con usar_tiled=False nunca se toca la carpeta mapas/, sin importar la
    dificultad — es el camino que usa Modo Infinito."""
    if dificultad == "facil" or not usar_tiled:
        return _generar_automatico(numero_nivel, dificultad)
    else:
        return _cargar_desde_tmx(numero_nivel, dificultad)

def _cargar_desde_tmx(numero_nivel, dificultad):
    """Carga el mapa desde un archivo .tmx de Tiled.

    Si el archivo no existe o falla, usa generación automática."""
    ruta = f"mapas/nivel_{dificultad}_{numero_nivel}.tmx"
    print(f"Cargando: {ruta}")
    datos = mapa_mod.cargar_mapa(ruta)

    if datos is None:
        print("Error cargando TMX, usando generacion automatica")
        return _generar_automatico(numero_nivel, dificultad)

    objetos = datos["objetos"]

    # Las puertas empiezan cerradas, o sea se agregan al set de paredes
    for pos in objetos["puertas_llave"]:
        datos["paredes"].add(pos)
    for puerta in objetos["puertas_placa"]:
        datos["paredes"].add(puerta["pos"])

    return {
        "paredes":         datos["paredes"],
        "portal":          objetos["portal"] or POS_MERENDERO,
        "pos_llave":       objetos["llave"],
        "hielo":           datos["hielo"],
        "teleportes":      datos["teleportes"],
        "puertas_llave":   objetos["puertas_llave"],
        "puertas_placa":   objetos["puertas_placa"],
        "placas":          objetos["placas"],
        "cajas":           objetos["cajas"],
        "pozos":           objetos["pozos"],
        "controles_cinta": objetos["controles_cinta"],
        "bloques_cinta":   objetos["bloques_cinta"],
        "interruptores":   objetos["interruptores"],
        "donaciones":      objetos.get("donaciones", []),
        "tile_map":        datos["tile_map"],
        "ancho":           datos["ancho"],
        "alto":            datos["alto"],
        "celdas_fondo":    {},
    }

def _generar_automatico(numero_nivel, dificultad):
    """Genera un mapa aleatorio garantizando que siempre haya camino al portal.

    El nivel 1 no es aleatorio: tiene 4 paredes fijas, sin hielo ni
    teleportes, para que la primera partida sea una entrada suave.
    A partir del nivel 3 aparece hielo y desde el 5 teleportes."""
    if numero_nivel == 1:
        # Mismas 4 paredes que usa el nivel de Tutorial (tutorial.py), que
        # es donde vive la consigna obligatoria de "4 paredes marrones".
        paredes    = {(3, 5), (7, 3), (10, 7), (5, 1)}
        hielo      = set()
        teleportes = {}
    else:
        # Generar paredes aleatorias con BFS para verificar solución
        cantidad = _calcular_paredes(numero_nivel, dificultad)
        while True:
            paredes = _generar_paredes(cantidad, POS_INICIO, POS_MERENDERO)
            if _hay_camino(POS_INICIO, POS_MERENDERO, paredes):
                break

        # Agregar celdas de hielo a partir del nivel 3
        hielo = set()
        if numero_nivel >= 3:
            cantidad_hielo = min(numero_nivel - 2, 4)
            candidatas = [
                (col, fila)
                for col in range(COLUMNAS)
                for fila in range(FILAS)
                if (col, fila) not in paredes
                and (col, fila) != POS_INICIO
                and (col, fila) != POS_MERENDERO
            ]
            hielo = set(random.sample(candidatas, min(cantidad_hielo, len(candidatas))))

        # Agregar un par de teleportes a partir del nivel 5
        teleportes = {}
        if numero_nivel >= 5:
            candidatas = [
                (col, fila)
                for col in range(COLUMNAS)
                for fila in range(FILAS)
                if (col, fila) not in paredes
                and (col, fila) not in hielo
                and (col, fila) != POS_INICIO
                and (col, fila) != POS_MERENDERO
            ]
            if len(candidatas) >= 2:
                par = random.sample(candidatas, 2)
                teleportes[par[0]] = par[1]
                teleportes[par[1]] = par[0]

    # En dificultad difícil, generar la posición de la llave. Se le pasan
    # el hielo y los teleportes porque son celdas donde la llave quedaría
    # imposible de recoger (ver _generar_llave).
    pos_llave = None
    if dificultad == "dificil" and numero_nivel > 1:
        pos_llave = _generar_llave(numero_nivel, paredes, hielo, teleportes)

    return {
        "paredes":         paredes,
        "portal":          POS_MERENDERO,
        "pos_llave":       pos_llave,
        "hielo":           hielo,
        "teleportes":      teleportes,
        "puertas_llave":   [],
        "puertas_placa":   [],
        "placas":          [],
        "cajas":           [],   # las mecánicas nuevas solo viven en mapas Tiled
        "pozos":           [],
        "controles_cinta": [],
        "bloques_cinta":   [],
        "interruptores":   [],
        "tile_map":        None,
        "ancho":           COLUMNAS,
        "alto":            FILAS,
        "celdas_fondo":    {},
    }

# ── Generación procedural del escenario ─────────────────────────────────────

def _calcular_paredes(numero_nivel, dificultad):
    """Calcula la cantidad de paredes según el nivel y la dificultad.

    Más nivel y más dificultad = más paredes, con un tope del 30% de la grilla."""
    base = 4 + numero_nivel * 2
    if dificultad == "medio":
        base += 4
    elif dificultad == "dificil":
        base += 8
    return min(base, int(COLUMNAS * FILAS * 0.30))

def _generar_paredes(cantidad, inicio, portal):
    """Genera un set de posiciones aleatorias para paredes,
    evitando el inicio y el portal."""
    celdas_libres = [
        (col, fila)
        for col in range(COLUMNAS)
        for fila in range(FILAS)
        if (col, fila) != inicio and (col, fila) != portal
    ]
    return set(random.sample(celdas_libres, cantidad))

# ── Búsqueda de caminos (BFS) ───────────────────────────────────────────────

def _celdas_vecinas_libres(celda, paredes, ancho=COLUMNAS, alto=FILAS):
    """Las celdas transitables pegadas a la dada (arriba, abajo, izquierda,
    derecha)."""
    col, fila = celda
    vecinas = []
    for dc, df in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        vecina = (col + dc, fila + df)
        if (0 <= vecina[0] < ancho and 0 <= vecina[1] < alto
                and vecina not in paredes):
            vecinas.append(vecina)
    return vecinas


def _camino_mas_corto(inicio, destino, paredes, ancho=COLUMNAS, alto=FILAS):
    """BFS que devuelve el camino completo (lista de celdas) en vez de solo
    su longitud, o None si no hay. Hace falta para saber QUÉ celdas se
    gastan al ir a buscar la llave."""
    if inicio == destino:
        return [inicio]
    padres = {inicio: None}
    cola   = [inicio]
    while cola:
        actual = cola.pop(0)
        for vecina in _celdas_vecinas_libres(actual, paredes, ancho, alto):
            if vecina in padres:
                continue
            padres[vecina] = actual
            if vecina == destino:
                camino, paso = [], vecina
                while paso is not None:
                    camino.append(paso)
                    paso = padres[paso]
                return list(reversed(camino))
            cola.append(vecina)
    return None


# ── Ubicación de la llave ───────────────────────────────────────────────────

def _llave_es_alcanzable_y_con_salida(candidata, paredes):
    """Comprueba que la llave se pueda buscar Y que después se pueda seguir
    hasta el merendero, teniendo en cuenta que en este juego NO se puede
    volver a pisar el camino ya recorrido.

    Sin esta verificación aparecían niveles imposibles: la llave quedaba al
    fondo de un pasillo sin salida, el jugador entraba a buscarla y ya no
    podía volver, porque las celdas de ida estaban gastadas.

    Se valida una ruta concreta: se toma el camino más corto de la salida a
    la llave, se marcan esas celdas como usadas, y se exige que desde la
    llave todavía se llegue al merendero sin repetir ninguna."""
    ida = _camino_mas_corto(POS_INICIO, candidata, paredes)
    if ida is None:
        return False
    # La celda de la llave sí se puede seguir usando: es donde se está
    # parado al momento de continuar viaje.
    gastadas = set(ida) - {candidata}
    return _hay_camino(candidata, POS_MERENDERO, paredes | gastadas)


def _generar_llave(numero_nivel, paredes, hielo=frozenset(), teleportes=None):
    """Coloca la llave en una celda desde la que el nivel siga siendo
    ganable. A mayor nivel, se ubica más lejos del punto de partida.

    Quedan descartadas:
      - Las celdas de HIELO: al pisarlas el jugador se desliza una celda
        más, así que nunca puede quedarse quieto encima para apretar E.
      - Las celdas de TELEPORTE: trasladan al jugador apenas las pisa, con
        el mismo resultado.
      - Los callejones sin salida y, en general, toda ubicación desde la
        que no se pueda seguir hasta el merendero sin repisar el camino.

    Si ninguna celda sirviera, se devuelve None y el nivel se juega sin
    llave: es preferible un nivel más fácil que uno imposible de terminar."""
    teleportes = teleportes or {}

    candidatas = [
        (col, fila)
        for col in range(COLUMNAS)
        for fila in range(FILAS)
        if (col, fila) not in paredes
        and (col, fila) not in hielo
        and (col, fila) not in teleportes
        and (col, fila) != POS_INICIO
        and (col, fila) != POS_MERENDERO
        # Con un solo vecino libre la celda es un callejón sin salida:
        # se entra y no se puede salir sin repisar.
        and len(_celdas_vecinas_libres((col, fila), paredes)) >= 2
        and _llave_es_alcanzable_y_con_salida((col, fila), paredes)
    ]
    if not candidatas:
        return None

    # Ordenar por distancia Manhattan al inicio (más lejanas primero)
    candidatas.sort(
        key=lambda c: abs(c[0] - POS_INICIO[0]) + abs(c[1] - POS_INICIO[1]),
        reverse=True
    )
    # El divisor se calculó pensando en una progresión de 10 niveles: a
    # mayor nivel, más grande el tramo de candidatas elegibles. Modo
    # Infinito no tiene techo de nivel, así que se limita a ese rango —
    # sin el max(1, ...) el divisor daría 0 en el nivel 11 (división por
    # cero) y negativo de ahí en adelante.
    divisor = max(1, 11 - numero_nivel)
    tope = max(1, len(candidatas) // divisor)
    return random.choice(candidatas[:tope])

def _hay_camino(inicio, destino, paredes, ancho=COLUMNAS, alto=FILAS):
    """BFS: verifica si existe al menos un camino entre inicio y destino
    sin cruzar paredes. Garantiza que el nivel siempre sea resoluble.

    `ancho` y `alto` son las dimensiones de la grilla a recorrer. Por
    defecto valen COLUMNAS x FILAS, que es el tamaño de los mapas
    generados proceduralmente, pero los mapas de Tiled son más anchos que
    la pantalla y hay que pasarles su tamaño real — si no, el BFS se
    detiene en la columna 13 y da por inalcanzable todo lo que esté más
    a la derecha."""
    visitados = {inicio}
    cola = [inicio]
    while cola:
        actual = cola.pop(0)
        if actual == destino:
            return True
        col, fila = actual
        for dc, df in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            vecino = (col + dc, fila + df)
            nc, nf = vecino
            if (0 <= nc < ancho and 0 <= nf < alto
                    and vecino not in paredes
                    and vecino not in visitados):
                visitados.add(vecino)
                cola.append(vecino)
    return False

def pasos_minimos(inicio, destino, paredes, ancho=COLUMNAS, alto=FILAS):
    """BFS: retorna la cantidad mínima de pasos para llegar al destino,
    o None si no hay camino posible. Se usa para calcular el puntaje y
    mostrar el hint de pasos sugeridos.

    Igual que _hay_camino, hay que pasarle el tamaño real del mapa cuando
    no es una grilla procedural de COLUMNAS x FILAS."""
    visitados = {inicio: 0}
    cola = [(inicio, 0)]
    while cola:
        (col, fila), pasos = cola.pop(0)
        if (col, fila) == destino:
            return pasos
        for dc, df in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            vecino = (col + dc, fila + df)
            nc, nf = vecino
            if (0 <= nc < ancho and 0 <= nf < alto
                    and vecino not in paredes
                    and vecino not in visitados):
                visitados[vecino] = pasos + 1
                cola.append((vecino, pasos + 1))
    return None