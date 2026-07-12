import json
import os

ARCHIVO = "guardado.json"

DATOS_DEFAULT = {
    "highscore": 0,
    "controles": "flechas"
}

def cargar():
    if not os.path.exists(ARCHIVO):
        return DATOS_DEFAULT.copy()
    with open(ARCHIVO, "r") as f:
        return json.load(f)

def guardar(datos):
    with open(ARCHIVO, "w") as f:
        json.dump(datos, f, indent=4)

def actualizar_highscore(puntaje_nuevo):
    datos = cargar()
    if puntaje_nuevo > datos["highscore"]:
        datos["highscore"] = puntaje_nuevo
        guardar(datos)

def actualizar_controles(modo):
    datos = cargar()
    datos["controles"] = modo
    guardar(datos)