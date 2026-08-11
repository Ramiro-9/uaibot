# guardado.py
# Maneja la persistencia de datos entre sesiones usando un archivo JSON.
#
# Ronda 2 (Fase 0.5 del plan): además del highscore simple y los
# controles que ya existían, se suma el estado de los modos nuevos:
#   - "infinito": highscore DOBLE (puntaje total acumulado + nivel más
#     alto alcanzado), tal como se definió al diseñar ese modo.
#   - "personajes_desbloqueados": lista de personajes jugables que el
#     equipo ya ganó en Modo Viaje. UAIBOT siempre está disponible.
#   - "progreso_viaje": en qué nivel va la partida de Modo Viaje.
#
# Nota de compatibilidad: un guardado.json viejo (de antes de esta
# tarea) no tiene estas claves nuevas, así que cargar() las completa
# con sus valores por defecto en vez de fallar con KeyError. La clave
# "dificultad" de guardados viejos (selección manual, ya eliminada del
# menú) se ignora sin problema si aparece: no rompe nada, simplemente
# no se usa.

import json
import os
import time

from constantes import ARCHIVO_PUNTAJES_TUTORIAL

ARCHIVO = "guardado.json"

# Valores por defecto si el archivo no existe todavía, o si existe pero
# le faltan claves nuevas (ver _completar_con_default).
DATOS_DEFAULT = {
    "highscore": 0,
    "controles": "flechas",
    "infinito": {
        "puntaje_total": 0,
        "nivel_maximo": 0,
    },
    "personajes_desbloqueados": ["uaibot"],
    "progreso_viaje": {
        "nivel_actual": 1,
        "completado": False,
    },
}


def _completar_con_default(datos):
    """Completa un diccionario de guardado con las claves que le falten,
    tomándolas de DATOS_DEFAULT. Hace merge un nivel adentro para los
    valores que son a su vez diccionarios (infinito, progreso_viaje),
    para que un guardado viejo con "infinito" a medio definir no pierda
    las claves que sí tenía.

    Se usa una copia de cada valor por defecto (en vez de la referencia
    directa) para que dos partidas guardadas no terminen compartiendo el
    mismo diccionario u lista en memoria."""
    for clave, valor_default in DATOS_DEFAULT.items():
        if clave not in datos:
            datos[clave] = (
                valor_default.copy() if isinstance(valor_default, (dict, list))
                else valor_default
            )
        elif isinstance(valor_default, dict):
            for subclave, subvalor_default in valor_default.items():
                datos[clave].setdefault(subclave, subvalor_default)
    return datos


def cargar():
    """Lee el archivo de guardado y retorna los datos como diccionario,
    completando cualquier clave nueva que falte con su valor por
    defecto. Si el archivo no existe, retorna los valores por defecto."""
    if not os.path.exists(ARCHIVO):
        return _completar_con_default({})
    with open(ARCHIVO, "r") as f:
        datos = json.load(f)
    return _completar_con_default(datos)


def guardar(datos):
    """Escribe el diccionario de datos en el archivo JSON."""
    with open(ARCHIVO, "w") as f:
        json.dump(datos, f, indent=4)


def actualizar_highscore(puntaje_nuevo):
    """Actualiza el highscore simple (Tutorial / Viaje / Multijugador)
    solo si el puntaje nuevo es mayor al guardado."""
    datos = cargar()
    if puntaje_nuevo > datos["highscore"]:
        datos["highscore"] = puntaje_nuevo
        guardar(datos)


def actualizar_controles(modo):
    """Guarda la preferencia de controles: 'flechas' o 'wasd'."""
    datos = cargar()
    datos["controles"] = modo
    guardar(datos)


def actualizar_highscore_infinito(puntaje_total, nivel_alcanzado):
    """Actualiza las dos métricas del Modo Infinito de forma independiente:
    el puntaje total solo sube si es mayor al guardado, y lo mismo para
    el nivel más alto alcanzado — no hace falta que ambos récords se
    batan en la misma partida."""
    datos = cargar()
    if puntaje_total > datos["infinito"]["puntaje_total"]:
        datos["infinito"]["puntaje_total"] = puntaje_total
    if nivel_alcanzado > datos["infinito"]["nivel_maximo"]:
        datos["infinito"]["nivel_maximo"] = nivel_alcanzado
    guardar(datos)


def desbloquear_personaje(nombre):
    """Agrega un personaje a la lista de desbloqueados (Modo Viaje).
    No hace nada si el personaje ya estaba desbloqueado."""
    datos = cargar()
    if nombre not in datos["personajes_desbloqueados"]:
        datos["personajes_desbloqueados"].append(nombre)
        guardar(datos)


def actualizar_progreso_viaje(nivel_actual, completado=False):
    """Guarda en qué nivel va la partida de Modo Viaje, y si ya se
    completó por entero."""
    datos = cargar()
    datos["progreso_viaje"]["nivel_actual"] = nivel_actual
    datos["progreso_viaje"]["completado"]   = completado
    guardar(datos)


def registrar_puntaje_tutorial(nombre, tiempo_segundos):
    """Agrega una línea a puntajes_tutorial.txt con el nombre ingresado al
    ganar Tutorial y el tiempo que tardó (consigna 4 de Ronda 2).

    Es un archivo de texto plano aparte de guardado.json a propósito: la
    consigna pide explícitamente un .txt, y no tiene sentido mezclar un
    historial de partidas (que solo crece) con el estado de configuración
    de una sola partida en curso que sí se sobrescribe."""
    nombre = nombre.strip() or "Jugador"
    marca_tiempo = time.strftime("%Y-%m-%d %H:%M")
    linea = f"{marca_tiempo} | {nombre} | {tiempo_segundos:.1f}s\n"
    with open(ARCHIVO_PUNTAJES_TUTORIAL, "a", encoding="utf-8") as f:
        f.write(linea)