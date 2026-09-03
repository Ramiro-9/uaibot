# mapa.py
# Lee archivos .tmx de Tiled y extrae la información necesaria para el juego:
# paredes, hielo, teleportes y objetos especiales (portal, llave, puertas,
# placas, cajas, pozos, cinta transportadora e interruptores compartidos).
#
# Nota de alcance (Fase 0.3 del plan de Ronda 2): este archivo solo PARSEA
# los objetos nuevos y los deja disponibles como datos crudos. La lógica de
# juego de cada mecánica (qué pasa cuando una caja cae en un pozo, cuándo
# se activa la cinta, cuándo se abre la puerta del interruptor compartido)
# se conecta después, en juego.py, cuando se implemente cada mecánica.

import arcade
from constantes import *

def cargar_mapa(ruta_tmx):
    """Carga un mapa de Tiled y retorna un diccionario con todos los datos del nivel.

    Si falla la carga, retorna None para que nivel.py use la generación automática."""
    try:
        tile_map = arcade.load_tilemap(ruta_tmx, scaling=1.0)

        paredes    = set()
        hielo      = set()
        teleportes = {}
        objetos    = {
            "portal":         None,
            "llave":          None,
            "puertas_llave":  [],
            "puertas_placa":  [],
            "placas":         [],
            "cajas":          [],
            "pozos":          [],
            "controles_cinta": [],
            "bloques_cinta":  [],
            "interruptores":  [],
            "donaciones":     [],
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
                elif nombre == "caja":
                    objetos["cajas"].append((col, fila))
                elif nombre == "pozo":
                    # Puente temporal con caja (mecánica #4 del documento MDA):
                    # celda intransitable hasta que una caja cae adentro. Acá
                    # solo se registra la posición; el "se llena y queda como
                    # piso" es lógica de juego.py, no de este parser.
                    objetos["pozos"].append((col, fila))
                elif nombre == "control_cinta":
                    # Cinta transportadora activada a distancia (mecánica #7):
                    # UAIBOT se para en esta celda y activa el movimiento del
                    # bloque vinculado por id_cinta, en la dirección indicada.
                    id_cinta   = props.get("id_cinta", None)
                    direccion  = props.get("direccion", "derecha")
                    objetos["controles_cinta"].append({
                        "pos": (col, fila), "id": id_cinta, "direccion": direccion
                    })
                elif nombre == "bloque_cinta":
                    id_cinta = props.get("id_cinta", None)
                    objetos["bloques_cinta"].append({"pos": (col, fila), "id": id_cinta})
                elif nombre == "interruptor":
                    # Interruptor compartido (mecánica #6, pensada para
                    # Multijugador): dos interruptores con el mismo id_puerta
                    # deben estar ocupados al mismo tiempo (uno por jugador)
                    # para abrir su puerta vinculada. La verificación de "los
                    # dos al mismo tiempo" es lógica de juego.py / Fase 4.
                    id_puerta = props.get("id_puerta", None)
                    objetos["interruptores"].append({"pos": (col, fila), "id": id_puerta})
                elif nombre == "donacion":
                    # Ítem coleccionable del Modo Viaje: uno de los cuatro
                    # tipos (comida / libros / juguetes / sillas) según la
                    # propiedad "tipo".
                    # La recolección —pisar la celda lo suma al contador— es
                    # lógica de viaje.py, no de este parser.
                    tipo = props.get("tipo", "comida")
                    objetos["donaciones"].append({"pos": (col, fila), "tipo": tipo, "recogida": False})
                elif nombre == "objeto":
                    # Objeto coleccionable cooperativo del Multijugador: uno
                    # de los 10 de OBJETOS_MULTIJUGADOR (constantes.py),
                    # identificado por la propiedad "objeto". La recolección
                    # —cualquiera de los dos jugadores pisando la celda— es
                    # lógica de multijugador.py.
                    id_objeto = props.get("objeto", "foto")
                    objetos["donaciones"].append({"pos": (col, fila), "tipo": id_objeto, "recogida": False})
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