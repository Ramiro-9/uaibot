# mapa.py
# Lee archivos .tmx de Tiled y extrae la información necesaria para el juego:
# paredes, hielo, teleportes y objetos especiales (portal, llave, puertas, placas).

import arcade
from constantes import *

def cargar_mapa(ruta_tmx):
    """Carga un mapa de Tiled y retorna un diccionario con todos los datos del nivel.
    Si falla la carga, retorna None para que nivel.py use la generación automática."""
    try:
        tile_map = arcade.load_tilemap(ruta_tmx, scaling=1.0)
        print(f"Capas: {list(tile_map.sprite_lists.keys())}")
        print(f"Objetos: {list(tile_map.object_lists.keys())}")

        paredes    = set()
        hielo      = set()
        teleportes = {}
        objetos    = {
            "portal":        None,
            "llave":         None,
            "puertas_llave": [],
            "puertas_placa": [],
            "placas":        [],
        }

        # Leer la capa de obstáculos y clasificar cada tile según su propiedad "tipo"
        if "obstaculos" in tile_map.sprite_lists:
            for sprite in tile_map.sprite_lists["obstaculos"]:
                col  = int(sprite.center_x // TAM_CELDA)
                fila = int(sprite.center_y // TAM_CELDA)
                tipo = sprite.properties.get("tipo", "pared") if sprite.properties else "pared"

                if tipo == "hielo":
                    hielo.add((col, fila))
                elif tipo == "teleporte":
                    id_tel = sprite.properties.get("id_teleporte", None)
                    if id_tel is not None:
                        teleportes.setdefault(id_tel, []).append((col, fila))
                elif tipo in ("pared", ""):
                    paredes.add((col, fila))

        # Leer la capa de objetos para portal, llave, puertas, placas y teleportes
        if "objetos" in tile_map.object_lists:
            for obj in tile_map.object_lists["objetos"]:
                col    = int(obj.shape[0] // TAM_CELDA)
                fila   = int(obj.shape[1] // TAM_CELDA)
                nombre = (obj.name or "").lower()
                props  = obj.properties if obj.properties else {}

                print(f"  Objeto: {nombre} en ({col},{fila})")

                if nombre == "portal":
                    objetos["portal"] = (col, fila)
                elif nombre == "llave":
                    objetos["llave"] = (col, fila)
                elif nombre == "puerta_llave":
                    objetos["puertas_llave"].append((col, fila))
                elif nombre == "puerta_placa":
                    id_puerta = props.get("id_puerta", None)
                    objetos["puertas_placa"].append({
                        "pos": (col, fila), "id": id_puerta, "abierta": False
                    })
                elif nombre == "placa":
                    id_puerta = props.get("id_puerta", None)
                    objetos["placas"].append({"pos": (col, fila), "id": id_puerta})
                elif nombre == "teleporte":
                    id_tel = props.get("id_teleporte", 1)
                    teleportes.setdefault(id_tel, []).append((col, fila))

        # Vincular los pares de teleportes: cada celda apunta a la otra
        teleportes_vinculados = {}
        for id_tel, celdas in teleportes.items():
            if len(celdas) == 2:
                teleportes_vinculados[celdas[0]] = celdas[1]
                teleportes_vinculados[celdas[1]] = celdas[0]

        return {
            "paredes":    paredes,
            "hielo":      hielo,
            "teleportes": teleportes_vinculados,
            "objetos":    objetos,
            "tile_map":   tile_map,
            "ancho":      tile_map.width,
            "alto":       tile_map.height,
        }

    except Exception as e:
        import traceback
        print(f"Error en cargar_mapa: {e}")
        traceback.print_exc()
        return None