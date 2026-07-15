# nivel.py
# Genera o carga los datos de cada nivel según la dificultad:
#   - Fácil: generación procedural con BFS para garantizar solución
#   - Medio/Difícil: carga desde archivo .tmx de Tiled
#     (si no existe el .tmx, usa generación automática como fallback)

import random
import mapa as mapa_mod
from constantes import *

def generar_nivel(numero_nivel, dificultad):
    """Punto de entrada principal. Decide si generar o cargar el nivel."""
    if dificultad == "facil":
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
        "paredes":       datos["paredes"],
        "portal":        objetos["portal"] or POS_MERENDERO,
        "pos_llave":     objetos["llave"],
        "hielo":         datos["hielo"],
        "teleportes":    datos["teleportes"],
        "puertas_llave": objetos["puertas_llave"],
        "puertas_placa": objetos["puertas_placa"],
        "placas":        objetos["placas"],
        "tile_map":      datos["tile_map"],
        "ancho":         datos["ancho"],
        "alto":          datos["alto"],
        "celdas_fondo":  {},
    }

def _generar_automatico(numero_nivel, dificultad):
    """Genera un mapa aleatorio garantizando que siempre haya camino al portal.
    El nivel 1 siempre tiene exactamente 4 paredes fijas (consigna del PDF).
    A partir del nivel 3 aparece hielo y desde el 5 teleportes."""
    if numero_nivel == 1:
        # Nivel tutorial: paredes fijas, sin hielo ni teleportes
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

    # En dificultad difícil, generar la posición de la llave
    pos_llave = None
    if dificultad == "dificil" and numero_nivel > 1:
        pos_llave = _generar_llave(numero_nivel, paredes)

    return {
        "paredes":       paredes,
        "portal":        POS_MERENDERO,
        "pos_llave":     pos_llave,
        "hielo":         hielo,
        "teleportes":    teleportes,
        "puertas_llave": [],
        "puertas_placa": [],
        "placas":        [],
        "tile_map":      None,
        "ancho":         COLUMNAS,
        "alto":          FILAS,
        "celdas_fondo":  {},
    }

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

def _generar_llave(numero_nivel, paredes):
    """Coloca la llave en una celda accesible desde el inicio.
    A mayor nivel, la llave se ubica más lejos del punto de partida."""
    candidatas = [
        (col, fila)
        for col in range(COLUMNAS)
        for fila in range(FILAS)
        if (col, fila) not in paredes
        and (col, fila) != POS_INICIO
        and (col, fila) != POS_MERENDERO
        and _hay_camino(POS_INICIO, (col, fila), paredes)
    ]
    # Ordenar por distancia Manhattan al inicio (más lejanas primero)
    candidatas.sort(
        key=lambda c: abs(c[0] - POS_INICIO[0]) + abs(c[1] - POS_INICIO[1]),
        reverse=True
    )
    tope = max(1, len(candidatas) // (11 - numero_nivel))
    return random.choice(candidatas[:tope])

def _hay_camino(inicio, destino, paredes):
    """BFS: verifica si existe al menos un camino entre inicio y destino
    sin cruzar paredes. Garantiza que el nivel siempre sea resoluble."""
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
            if (0 <= nc < COLUMNAS and 0 <= nf < FILAS
                    and vecino not in paredes
                    and vecino not in visitados):
                visitados.add(vecino)
                cola.append(vecino)
    return False

def pasos_minimos(inicio, destino, paredes):
    """BFS: retorna la cantidad mínima de pasos para llegar al destino.
    Se usa para calcular el puntaje y mostrar el hint de pasos sugeridos."""
    visitados = {inicio: 0}
    cola = [(inicio, 0)]
    while cola:
        (col, fila), pasos = cola.pop(0)
        if (col, fila) == destino:
            return pasos
        for dc, df in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            vecino = (col + dc, fila + df)
            nc, nf = vecino
            if (0 <= nc < COLUMNAS and 0 <= nf < FILAS
                    and vecino not in paredes
                    and vecino not in visitados):
                visitados[vecino] = pasos + 1
                cola.append((vecino, pasos + 1))
    return None