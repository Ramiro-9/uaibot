# mapa.py
import arcade
from constantes import *

def cargar_mapa(ruta_tmx):
    try:
        tile_map = arcade.load_tilemap(ruta_tmx, scaling=1.0, use_spatial_hash=True, offset=arcade.math.Vec2(0, 0), use_texture_atlas=True)
        print(f"Capas disponibles: {list(tile_map.sprite_lists.keys())}")
        print(f"Objetos disponibles: {list(tile_map.object_lists.keys())}")

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
                col, fila = _px_a_celda(sprite.center_x, sprite.center_y, tile_map.tile_height)
                tipo = sprite.properties.get("tipo", "pared")
                print(f"  Obstaculo en ({col},{fila}) tipo={tipo}")
                if tipo == "hielo":
                    hielo.add((col, fila))
                elif tipo == "teleporte":
                    id_tel = sprite.properties.get("id_teleporte", None)
                    if id_tel is not None:
                        teleportes.setdefault(id_tel, []).append((col, fila))
                else:
                    paredes.add((col, fila))

        if "objetos" in tile_map.object_lists:
            if "objetos" in tile_map.object_lists:
                for obj in tile_map.object_lists["objetos"]:
                    print(f"Atributos del objeto: {dir(obj)}")
                    break
            for obj in tile_map.object_lists["objetos"]:
                col, fila = _px_a_celda(obj.shape[0], obj.shape[1], tile_map.tile_height)
                nombre = (obj.name or "").lower()
                props = obj.properties if obj.properties else {}
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

        teleportes_vinculados = {}
        for id_tel, celdas in teleportes.items():
            if len(celdas) == 2:
                teleportes_vinculados[celdas[0]] = celdas[1]
                teleportes_vinculados[celdas[1]] = celdas[0]

        resultado = {
            "paredes":    paredes,
            "hielo":      hielo,
            "teleportes": teleportes_vinculados,
            "objetos":    objetos,
            "tile_map":   tile_map,
            "ancho":      tile_map.width,
            "alto":       tile_map.height,
            "celdas_fondo": celdas_fondo,
        }
        print(f"Mapa cargado OK, paredes={len(paredes)}")
        celdas_fondo = {}
        if "fondo" in tile_map.sprite_lists:
            for sprite in tile_map.sprite_lists["fondo"]:
                col  = int(sprite.center_x // TAM_CELDA)
                fila = int((tile_map.height * TAM_CELDA - sprite.center_y) // TAM_CELDA)
                celdas_fondo[(col, fila)] = sprite.texture
        return resultado

    except Exception as e:
        import traceback
        print(f"Error dentro de cargar_mapa: {e}")
        traceback.print_exc()
        return None

def _px_a_celda(px, py, tile_height):
    col  = int(px // TAM_CELDA)
    fila = int(py // TAM_CELDA)
    return col, fila