# guardado.py
# Maneja la persistencia de datos entre sesiones usando un archivo JSON.
# Guarda el highscore, los controles preferidos y la dificultad elegida.

import json
import os

ARCHIVO = "guardado.json"

# Valores por defecto si el archivo no existe todavía
DATOS_DEFAULT = {
    "highscore": 0,
    "controles": "flechas"
}

def cargar():
    """Lee el archivo de guardado y retorna los datos como diccionario.
    Si el archivo no existe, retorna los valores por defecto."""
    if not os.path.exists(ARCHIVO):
        return DATOS_DEFAULT.copy()
    with open(ARCHIVO, "r") as f:
        return json.load(f)

def guardar(datos):
    """Escribe el diccionario de datos en el archivo JSON."""
    with open(ARCHIVO, "w") as f:
        json.dump(datos, f, indent=4)

def actualizar_highscore(puntaje_nuevo):
    """Actualiza el highscore solo si el puntaje nuevo es mayor al guardado."""
    datos = cargar()
    if puntaje_nuevo > datos["highscore"]:
        datos["highscore"] = puntaje_nuevo
        guardar(datos)

def actualizar_controles(modo):
    """Guarda la preferencia de controles: 'flechas' o 'wasd'."""
    datos = cargar()
    datos["controles"] = modo
    guardar(datos)