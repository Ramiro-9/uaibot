
import random
from constantes import *

def generar_nivel(numero_nivel, dificultad):

    inicio  = POS_INICIO
    portal  = POS_MERENDERO

    cantidad_paredes = _calcular_paredes(numero_nivel, dificultad)

    while True:
        paredes = _generar_paredes(cantidad_paredes, inicio, portal)
        if _hay_camino(inicio, portal, paredes):
            break

    pos_llave = None
    if dificultad == "dificil":
        pos_llave = _generar_llave(numero_nivel, paredes, inicio, portal)

    return {
        "paredes":   paredes,
        "portal":    portal,
        "pos_llave": pos_llave
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

def _generar_llave(numero_nivel, paredes, inicio, portal):

    candidatas = [
        (col, fila)
        for col in range(COLUMNAS)
        for fila in range(FILAS)
        if (col, fila) not in paredes
        and (col, fila) != inicio
        and (col, fila) != portal
    ]

    candidatas.sort(key=lambda c: abs(c[0] - inicio[0]) + abs(c[1] - inicio[1]), reverse=True)
    tope = max(1, len(candidatas) // (11 - numero_nivel))
    return random.choice(candidatas[:tope])

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