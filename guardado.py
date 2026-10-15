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
import math
import os
import time

from constantes import ARCHIVO_PUNTAJES_TUTORIAL

ARCHIVO = "guardado.json"

# Valores por defecto si el archivo no existe todavía, o si existe pero
# le faltan claves nuevas (ver _completar_con_default).
DATOS_DEFAULT = {
    "highscore": 0,
    "controles": "flechas",
    "volumen_musica_menu": 0.3,
    "volumen_musica_nivel": 0.3,
    "infinito": {
        "puntaje_total": 0,
        "nivel_maximo": 0,
    },
    "personajes_desbloqueados": ["uaibot"],
    "objetos_multijugador": [],
    "progreso_viaje": {
        "nivel_actual": 1,
        "completado": False,
    },
}


# ── Lectura y escritura del archivo ─────────────────────────────────────────

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


# ── Récords y progreso ──────────────────────────────────────────────────────

def actualizar_highscore(puntaje_nuevo):
    """Actualiza el highscore simple (Tutorial / Viaje)
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


def actualizar_volumenes(menu=None, nivel=None):
    """Guarda los volúmenes de música por separado (menú y niveles).

    Solo actualiza el que reciba; el otro queda como estaba."""
    datos = cargar()
    if menu is not None:
        datos["volumen_musica_menu"]  = menu
    if nivel is not None:
        datos["volumen_musica_nivel"] = nivel
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


# ── Desbloqueos que alimentan el Bestiario ──────────────────────────────────

def desbloquear_personaje(nombre):
    """Agrega un personaje a la lista de desbloqueados (Modo Viaje).

    No hace nada si el personaje ya estaba desbloqueado."""
    datos = cargar()
    if nombre not in datos["personajes_desbloqueados"]:
        datos["personajes_desbloqueados"].append(nombre)
        guardar(datos)


def desbloquear_objeto(id_objeto):
    """Agrega un objeto coleccionable a la lista de conseguidos (Modo
    Multijugador). No hace nada si ya estaba. Lo lee el Inventario."""
    datos = cargar()
    if id_objeto not in datos["objetos_multijugador"]:
        datos["objetos_multijugador"].append(id_objeto)
        guardar(datos)


def actualizar_progreso_viaje(nivel_actual, completado=False):
    """Guarda en qué nivel va la partida de Modo Viaje, y si ya se
    completó por entero."""
    datos = cargar()
    datos["progreso_viaje"]["nivel_actual"] = nivel_actual
    datos["progreso_viaje"]["completado"]   = completado
    guardar(datos)


# ── Puntajes del Tutorial (consigna 4) ──────────────────────────────────────

def registrar_puntaje_tutorial(nombre, tiempo_segundos):
    """Agrega una línea a puntajes_tutorial.txt con el nombre ingresado al
    ganar Tutorial y el tiempo que tardó (consigna 4 de Ronda 2).

    Es un archivo de texto plano aparte de guardado.json a propósito: la
    consigna pide explícitamente un .txt, y no tiene sentido mezclar un
    historial de partidas (que solo crece) con el estado de configuración
    de una sola partida en curso que sí se sobrescribe."""
    # El formato conserva los puntajes anteriores. Cada partida terminada
    # cuenta como una participación; los empates comparten puesto (1, 1, 3).
    puntajes = leer_puntajes_tutorial()
    tiempo = float(f"{tiempo_segundos:.1f}")
    if not math.isfinite(tiempo) or tiempo < 0:
        raise ValueError("El tiempo debe ser finito y no negativo")
    nombre = " ".join(nombre.replace("|", " ").split()) or "Jugador"
    marca_tiempo = time.strftime("%Y-%m-%d %H:%M")
    linea = f"{marca_tiempo} | {nombre} | {tiempo_segundos:.1f}s\n"
    with open(ARCHIVO_PUNTAJES_TUTORIAL, "a", encoding="utf-8") as f:
        f.write(linea)
    puntajes.append({"nombre": nombre, "tiempo": tiempo})
    puntajes.sort(key=lambda puntaje: puntaje["tiempo"])
    puesto = 1 + sum(p["tiempo"] < tiempo for p in puntajes)
    return puesto, len(puntajes)


def leer_puntajes_tutorial():
    """Lee resultados válidos del formato fecha | nombre | segundos.

    Ignora líneas dañadas, sin borrar el archivo, y ordena de menor a mayor.
    Un archivo todavía inexistente equivale a un ranking vacío.
    """
    try:
        with open(ARCHIVO_PUNTAJES_TUTORIAL, encoding="utf-8") as archivo:
            lineas = archivo.readlines()
    except FileNotFoundError:
        return []
    puntajes = []
    for linea in lineas:
        partes = linea.strip().split(" | ")
        if len(partes) != 3:
            continue
        try:
            tiempo = float(partes[2].removesuffix("s"))
        except ValueError:
            continue
        if math.isfinite(tiempo) and tiempo >= 0:
            puntajes.append({"nombre": partes[1], "tiempo": tiempo})
    return sorted(puntajes, key=lambda puntaje: puntaje["tiempo"])
