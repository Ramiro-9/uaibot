# mapa.py
import arcade
from constantes import *

def cargar_mapa(ruta_tmx):
    try:
        tile_map = arcade.load_tilemap(ruta_tmx, scaling=1.0)
        print(f"Capas: {list(tile_map.sprite_lists.keys())}")
        print(f"Objetos: {list(tile_map.object_lists.keys())}")

        paredes   = set()
        hielo     = set()
        teleportes = {}
        objetos   = {
            "portal":        None,
            "llave":         None,
            "puertas_llave": [],
            "puertas_placa": [],
            "placas":        [],
        }

        if "obstaculos" in tile_map.sprite_lists:
            for sprite in tile_map.sprite_lists["obstaculos"]:
                col  = int(sprite.center_x // TAM_CELDA)
                fila = int((tile_map.height * TAM_CELDA - sprite.center_y) // TAM_CELDA)
                tipo = sprite.properties.get("tipo", "pared") if sprite.properties else "pared"
                if tipo == "hielo":
                    hielo.add((col, fila))
                elif tipo == "teleporte":
                    id_tel = sprite.properties.get("id_teleporte", None)
                    if id_tel is not None:
                        teleportes.setdefault(id_tel, []).append((col, fila))
                elif tipo == "pared" or tipo == "":
                    paredes.add((col, fila))

        if "objetos" in tile_map.object_lists:
            for obj in tile_map.object_lists["objetos"]:
                col  = int(obj.shape[0] // TAM_CELDA)
                fila = int((tile_map.height * TAM_CELDA - obj.shape[1]) // TAM_CELDA)
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
                    objetos["puertas_placa"].append({"pos": (col, fila), "id": id_puerta, "abierta": False})
                elif nombre == "placa":
                    id_puerta = props.get("id_puerta", None)
                    objetos["placas"].append({"pos": (col, fila), "id": id_puerta})
                elif nombre == "teleporte":
                    id_tel = props.get("id_teleporte", 1)
                    teleportes.setdefault(id_tel, []).append((col, fila))

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