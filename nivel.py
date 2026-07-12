# nivel.py
import random
from constantes import *

def generar_nivel(numero_nivel, dificultad):
    return _generar_automatico(numero_nivel, dificultad)

def _generar_automatico(numero_nivel, dificultad):
    if numero_nivel == 1:
        paredes = {(3, 5), (7, 3), (10, 7), (5, 1)}
        hielo = set()
        teleportes = {}
    else:
        cantidad = _calcular_paredes(numero_nivel, dificultad)
        while True:
            paredes = _generar_paredes(cantidad, POS_INICIO, POS_MERENDERO)
            if _hay_camino(POS_INICIO, POS_MERENDERO, paredes):
                break

        # hielo: aparece a partir del nivel 3
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

        # teleportes: aparecen a partir del nivel 5, siempre en pares
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
    base = 4 + numero_nivel * 2
    if dificultad == "medio":
        base += 4
    elif dificultad == "dificil":
        base += 8
    return min(base, int(COLUMNAS * FILAS * 0.30))

def _generar_paredes(cantidad, inicio, portal):
    celdas_libres = [
        (col, fila)
        for col in range(COLUMNAS)
        for fila in range(FILAS)
        if (col, fila) != inicio and (col, fila) != portal
    ]
    return set(random.sample(celdas_libres, cantidad))

def _generar_llave(numero_nivel, paredes):
    candidatas = [
        (col, fila)
        for col in range(COLUMNAS)
        for fila in range(FILAS)
        if (col, fila) not in paredes
        and (col, fila) != POS_INICIO
        and (col, fila) != POS_MERENDERO
        and _hay_camino(POS_INICIO, (col, fila), paredes)
    ]
    candidatas.sort(key=lambda c: abs(c[0] - POS_INICIO[0]) + abs(c[1] - POS_INICIO[1]), reverse=True)
    tope = max(1, len(candidatas) // (11 - numero_nivel))
    return random.choice(candidatas[:tope])

def _hay_camino(inicio, destino, paredes):
    visitados = {inicio}
    cola = [inicio]
    while cola:
        actual = cola.pop(0)
        if actual == destino:
            return True
        col, fila = actual
        for dc, df in [(0,1),(0,-1),(1,0),(-1,0)]:
            vecino = (col + dc, fila + df)
            nc, nf = vecino
            if (0 <= nc < COLUMNAS and 0 <= nf < FILAS
                    and vecino not in paredes
                    and vecino not in visitados):
                visitados.add(vecino)
                cola.append(vecino)
    return False

def pasos_minimos(inicio, destino, paredes):
    visitados = {inicio: 0}
    cola = [(inicio, 0)]
    while cola:
        (col, fila), pasos = cola.pop(0)
        if (col, fila) == destino:
            return pasos
        for dc, df in [(0,1),(0,-1),(1,0),(-1,0)]:
            vecino = (col + dc, fila + df)
            nc, nf = vecino
            if (0 <= nc < COLUMNAS and 0 <= nf < FILAS
                    and vecino not in paredes
                    and vecino not in visitados):
                visitados[vecino] = pasos + 1
                cola.append((vecino, pasos + 1))
    return None