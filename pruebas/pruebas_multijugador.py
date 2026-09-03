# pruebas_multijugador.py
# Prueba automática del Modo Multijugador con los DOS lados reales
# conectados por 127.0.0.1: un anfitrión y un invitado en el mismo proceso,
# hablando por un socket de verdad.
#
# Por qué existe: el multijugador solo se puede jugar de a dos, así que
# probarlo a mano necesita dos personas o dos ventanas y mucha paciencia
# para llegar a los casos raros (que uno recoja la llave, que se corte la
# conexión a mitad de nivel). Acá se recorren esos casos en segundos.
#
# La diferencia con pruebas_red.py (misma carpeta): aquella prueba que los mensajes viajen;
# esta prueba que los dos jugadores terminen viendo lo mismo.
#
# Se ejecuta con:  python pruebas/pruebas_multijugador.py   (desde la raíz)

import os
import sys

# Este archivo vive en pruebas/, pero importa los módulos del juego, que
# están en la raíz del proyecto. Agregarla al path deja que la prueba se
# corra desde donde sea: "python pruebas/pruebas_multijugador.py" parado en la raíz,
# o entrando primero a la carpeta. Sin esto solo andaría como módulo.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time

import arcade

import guardado
import red
from constantes import ALTO_VENTANA, ANCHO_VENTANA
from multijugador import TOTAL_NIVELES, Multijugador

PUERTO = 50133

# Direcciones en el orden en que se prueban al buscar un movimiento legal.
DIRECCIONES = ((0, -1), (1, 0), (0, 1), (-1, 0))


def armar_partida(puerto, personaje_host=None, personaje_invitado=None):
    """Deja lista una partida de dos jugadores: servidor, cliente y las dos
    vistas ya con el nivel 1 cargado y sincronizadas."""
    servidor = red.Servidor(puerto=puerto)
    assert servidor.error is None, servidor.error
    cliente = red.Cliente("127.0.0.1", puerto=puerto)
    assert cliente.error is None, cliente.error

    fin = time.time() + 3
    while time.time() < fin and not servidor.hay_jugador:
        time.sleep(0.01)
    assert servidor.hay_jugador, "no se conectaron"

    anfitrion = Multijugador(conexion=servidor, es_host=True,
                             personaje=personaje_host)
    invitado = Multijugador(conexion=cliente, es_host=False,
                            personaje=personaje_invitado)
    anfitrion.setup(1)
    invitado.setup(1)
    bombear(anfitrion, invitado)
    return servidor, cliente, anfitrion, invitado


def bombear(anfitrion, invitado, veces=25):
    """Simula unos cuadros de juego en los dos lados. Hace falta porque los
    mensajes se procesan en on_update(), y además tienen que viajar por el
    socket: nada llega en el instante siguiente al envío."""
    for _ in range(veces):
        anfitrion.on_update(1 / 60)
        invitado.on_update(1 / 60)
        time.sleep(0.004)


def celdas(vista):
    return [(j["col"], j["fila"]) for j in vista.jugadores]


def mover_legal(anfitrion, invitado, indice):
    """Mueve al jugador indicado hacia la primera dirección que le sirva, y
    devuelve si encontró alguna. Se busca en vez de fijar la dirección a
    mano porque el mapa es un .tmx diseñado aparte: si mañana se lo
    reacomoda, la prueba sigue valiendo."""
    vista = anfitrion if indice == 0 else invitado
    col, fila = celdas(anfitrion)[indice]
    for dc, df in DIRECCIONES:
        destino = (col + dc, fila + df)
        if not (0 <= destino[0] < anfitrion.mapa_ancho
                and 0 <= destino[1] < anfitrion.mapa_alto):
            continue
        if (destino in anfitrion.paredes or destino in anfitrion.sendero
                or destino in celdas(anfitrion)):
            continue
        vista._pedir_movimiento(dc, df)
        bombear(anfitrion, invitado)
        return True
    return False


def cerrar(servidor, cliente):
    servidor.cerrar()
    cliente.cerrar()


# ── Las pruebas ───────────────────────────────────────────────────────────

def prueba_arranque_igual():
    """Los dos lados tienen que arrancar viendo el mismo nivel, con los dos
    jugadores en las mismas celdas."""
    servidor, cliente, anfitrion, invitado = armar_partida(PUERTO)
    assert anfitrion.numero_nivel == invitado.numero_nivel == 1
    assert celdas(anfitrion) == celdas(invitado), \
        f"arrancan distinto: {celdas(anfitrion)} vs {celdas(invitado)}"
    assert celdas(anfitrion)[0] != celdas(anfitrion)[1], "los dos en la misma celda"
    assert anfitrion.sendero == invitado.sendero
    cerrar(servidor, cliente)


def prueba_movimiento_del_anfitrion():
    """El anfitrión resuelve su movimiento y lo difunde; el invitado lo ve."""
    servidor, cliente, anfitrion, invitado = armar_partida(PUERTO + 1)
    antes = celdas(anfitrion)[0]
    assert mover_legal(anfitrion, invitado, 0), "no había movimiento legal"
    assert celdas(anfitrion)[0] != antes, "no se movió"
    assert celdas(invitado) == celdas(anfitrion), "el invitado no lo vio"
    assert invitado.pasos == anfitrion.pasos == 1
    cerrar(servidor, cliente)


def prueba_movimiento_del_invitado():
    """El invitado no mueve nada por su cuenta: le pide al anfitrión, que
    resuelve y le devuelve el estado. Es el camino más largo del protocolo."""
    servidor, cliente, anfitrion, invitado = armar_partida(PUERTO + 2)
    antes = celdas(anfitrion)[1]
    assert mover_legal(anfitrion, invitado, 1), "no había movimiento legal"
    assert celdas(anfitrion)[1] != antes, "el anfitrión no aplicó el pedido"
    assert celdas(invitado) == celdas(anfitrion), "no le volvió el estado"
    assert invitado.pasos == anfitrion.pasos == 1
    cerrar(servidor, cliente)


def prueba_no_se_pisan():
    """Regla propia del cooperativo: no pueden ocupar la misma celda."""
    servidor, cliente, anfitrion, invitado = armar_partida(PUERTO + 3)
    (c1, f1), (c2, f2) = celdas(anfitrion)
    dc, df = c2 - c1, f2 - f1
    if abs(dc) + abs(df) == 1:      # están pegados: probar entrar encima
        anfitrion._pedir_movimiento(dc, df)
        bombear(anfitrion, invitado)
        assert celdas(anfitrion)[0] == (c1, f1), "se metió en la celda del otro"
        assert anfitrion.pasos == 0, "contó un paso que no ocurrió"
        assert celdas(invitado) == celdas(anfitrion)
    cerrar(servidor, cliente)


def prueba_sendero_compartido():
    """El sendero es del equipo: donde caminó uno, el otro no puede pisar.
    Es la consigna de la Ronda 1 llevada a dos jugadores."""
    servidor, cliente, anfitrion, invitado = armar_partida(PUERTO + 4)
    origen = celdas(anfitrion)[0]
    assert mover_legal(anfitrion, invitado, 0), "no había movimiento legal"
    assert celdas(anfitrion)[0] in invitado.sendero, \
        "el invitado no recibió el sendero"

    # El invitado intenta entrar a la celda que el anfitrión acaba de dejar,
    # que ahora es sendero. Solo se prueba si la tiene pegada.
    c2, f2 = celdas(anfitrion)[1]
    dc, df = origen[0] - c2, origen[1] - f2
    if abs(dc) + abs(df) == 1:
        pasos_antes = anfitrion.pasos
        invitado._pedir_movimiento(dc, df)
        bombear(anfitrion, invitado)
        assert celdas(anfitrion)[1] == (c2, f2), "pisó el sendero del otro"
        assert anfitrion.pasos == pasos_antes
    cerrar(servidor, cliente)


def prueba_movimiento_invalido_no_desincroniza():
    """Un pedido imposible (salir del mapa) no tiene que dejar a los dos
    lados viendo cosas distintas: el anfitrión lo rechaza y no difunde."""
    servidor, cliente, anfitrion, invitado = armar_partida(PUERTO + 5)
    for _ in range(6):
        invitado._pedir_movimiento(-1, 0)   # hacia afuera por la izquierda
        invitado._pedir_movimiento(0, 1)
    bombear(anfitrion, invitado, veces=40)
    assert celdas(anfitrion) == celdas(invitado), "quedaron desincronizados"
    assert anfitrion.pasos == invitado.pasos
    assert anfitrion.sendero == invitado.sendero
    cerrar(servidor, cliente)


def prueba_llave_compartida():
    """La llave la agarra cualquiera de los dos y abre las puertas para el
    equipo. Se fuerza poniendo al jugador 2 sobre la llave."""
    servidor, cliente, anfitrion, invitado = armar_partida(PUERTO + 6)
    if not anfitrion.pos_llave:
        cerrar(servidor, cliente)
        return
    anfitrion.jugadores[1]["col"], anfitrion.jugadores[1]["fila"] = anfitrion.pos_llave
    puertas = set(anfitrion.puertas_llave)

    invitado._pedir_llave()             # la pide el invitado
    bombear(anfitrion, invitado)

    assert anfitrion.tiene_llave, "el anfitrión no la registró"
    assert invitado.tiene_llave, "al invitado no le llegó"
    assert invitado.txt_llave.value == "LLAVE: SI"
    for puerta in puertas:
        assert puerta not in anfitrion.paredes, "no se abrió la puerta"
        assert puerta not in invitado.paredes, "el invitado la sigue viendo cerrada"
    cerrar(servidor, cliente)


def prueba_cambio_de_nivel():
    """Solo el anfitrión decide cuándo se pasa de nivel, para que los dos
    carguen el mismo mapa."""
    servidor, cliente, anfitrion, invitado = armar_partida(PUERTO + 7)
    anfitrion._avanzar_de_nivel()
    bombear(anfitrion, invitado, veces=40)
    assert anfitrion.numero_nivel == 2
    assert invitado.numero_nivel == 2, "el invitado se quedó en el nivel anterior"
    assert celdas(anfitrion) == celdas(invitado)
    cerrar(servidor, cliente)


def prueba_eleccion_de_personaje():
    """Cada uno juega con el que eligio, y los dos lados coinciden en quien
    es quien."""
    servidor, cliente, anfitrion, invitado = armar_partida(
        PUERTO + 13, personaje_host="uaibotina", personaje_invitado="uaibotino")

    ids_anfitrion = [p["id"] for p in anfitrion.personajes]
    ids_invitado  = [p["id"] for p in invitado.personajes]
    assert ids_anfitrion == ["uaibotina", "uaibotino"], ids_anfitrion
    assert ids_invitado == ids_anfitrion, f"no coinciden: {ids_invitado}"

    # Y cada uno maneja al suyo: la habilidad que se aplica es la del
    # personaje elegido, no la del que venia por defecto.
    assert anfitrion._personaje_de_habilidad()["habilidad"] == "guia"
    assert invitado.personajes[invitado.mi_indice]["habilidad"] == "alcance"
    cerrar(servidor, cliente)


def prueba_choque_de_personajes():
    """Si los dos eligen el mismo, el anfitrion se queda con el suyo y le da
    otro al invitado. El invitado no puede saber la eleccion del anfitrion
    antes de conectarse, asi que el choque solo se puede resolver aca."""
    servidor, cliente, anfitrion, invitado = armar_partida(
        PUERTO + 14, personaje_host="uaibota", personaje_invitado="uaibota")

    assert anfitrion.personajes[0]["id"] == "uaibota", "el anfitrion perdio el suyo"
    assert anfitrion.personajes[1]["id"] != "uaibota", "quedaron los dos iguales"
    assert [p["id"] for p in invitado.personajes] ==            [p["id"] for p in anfitrion.personajes], "al invitado no le llego el cambio"
    # Y el panel del invitado dice con quien le toco jugar de verdad.
    assert invitado.personajes[1]["nombre"] in invitado.txt_quien_soy.text
    cerrar(servidor, cliente)


def prueba_no_toca_el_highscore():
    """El puntaje cooperativo no entra al highscore general: se consigue
    entre dos y no se puede comparar con una partida en solitario."""
    antes = guardado.cargar()["highscore"]
    servidor, cliente, anfitrion, invitado = armar_partida(PUERTO + 15)

    anfitrion.puntaje_total = antes + 10_000
    anfitrion.jugadores[0]["col"], anfitrion.jugadores[0]["fila"] = anfitrion.portal
    anfitrion._completar_nivel()
    anfitrion._difundir_estado()
    bombear(anfitrion, invitado, veces=40)

    assert guardado.cargar()["highscore"] == antes,         "el multijugador escribio en el highscore general"
    cerrar(servidor, cliente)


def prueba_mirada_viaja_por_la_red():
    """Los personajes miran hacia donde caminaron, y el invitado lo ve.

    Importa que viaje: el invitado no resuelve movimientos ni siquiera los
    suyos, asi que si la orientacion no viniera en el estado los veria a los
    dos mirando siempre hacia el mismo lado."""
    servidor, cliente, anfitrion, invitado = armar_partida(PUERTO + 16)

    # Arrancan con la orientacion natural del arte, que es hacia la derecha.
    assert anfitrion.jugadores[0]["mirando_derecha"]

    # Un paso hacia la izquierda da vuelta al jugador 1. Se lo ubica primero
    # con lugar libre a su izquierda, porque arranca pegado al borde.
    anfitrion.jugadores[0]["col"] = 3
    libre = (2, anfitrion.jugadores[0]["fila"])
    if libre not in anfitrion.paredes and libre not in celdas(anfitrion):
        anfitrion._pedir_movimiento(-1, 0)
        bombear(anfitrion, invitado)
        assert not anfitrion.jugadores[0]["mirando_derecha"], "no se dio vuelta"
        assert not invitado.jugadores[0]["mirando_derecha"],             "al invitado no le llego la orientacion"

        # Y uno hacia la derecha lo devuelve.
        anfitrion._pedir_movimiento(1, 0)
        bombear(anfitrion, invitado)
        assert anfitrion.jugadores[0]["mirando_derecha"], "no volvio a mirar derecha"
        assert invitado.jugadores[0]["mirando_derecha"]
    cerrar(servidor, cliente)


def prueba_mirada_no_cambia_en_vertical():
    """Arriba y abajo no tienen arte propio: caminar en vertical conserva
    hacia donde se estaba mirando, en vez de girar al azar."""
    servidor, cliente, anfitrion, invitado = armar_partida(PUERTO + 17)
    jugador = anfitrion.jugadores[0]

    jugador["mirando_derecha"] = False
    col, fila = jugador["col"], jugador["fila"]
    if (col, fila - 1) not in anfitrion.paredes:
        anfitrion._pedir_movimiento(0, -1)
        bombear(anfitrion, invitado)
        assert not jugador["mirando_derecha"], "un paso vertical le cambio la mirada"
        assert not invitado.jugadores[0]["mirando_derecha"]
    cerrar(servidor, cliente)


def prueba_cada_jugador_mira_por_su_cuenta():
    """La orientacion es de cada uno: que uno se de vuelta no da vuelta al
    otro. Es el mismo motivo por el que 'moviendose' es individual."""
    servidor, cliente, anfitrion, invitado = armar_partida(PUERTO + 18)
    anfitrion.jugadores[0]["mirando_derecha"] = True
    anfitrion.jugadores[1]["mirando_derecha"] = False
    anfitrion._difundir_estado()
    bombear(anfitrion, invitado)

    assert invitado.jugadores[0]["mirando_derecha"]
    assert not invitado.jugadores[1]["mirando_derecha"], "se contagiaron la orientacion"
    cerrar(servidor, cliente)


def prueba_puntaje_sincronizado():
    """Ganar un nivel tiene que dejar a los dos con el mismo puntaje. El
    puntaje no viaja por la red: cada lado lo calcula solo, a partir de los
    pasos y el recorrido minimo que si estan sincronizados. Esta prueba es
    la que verifica que ese atajo de veras da lo mismo de los dos lados."""
    servidor, cliente, anfitrion, invitado = armar_partida(PUERTO + 12)

    # Poner al jugador 1 en el portal y avisar: es ganar el nivel.
    anfitrion.jugadores[0]["col"], anfitrion.jugadores[0]["fila"] = anfitrion.portal
    anfitrion._completar_nivel()
    anfitrion._difundir_estado()
    bombear(anfitrion, invitado, veces=200)   # confeti (180 cuadros) + avance

    assert anfitrion.puntaje_total > 0, "el anfitrion no sumo puntaje"
    assert invitado.puntaje_total == anfitrion.puntaje_total,         f"puntajes distintos: {anfitrion.puntaje_total} vs {invitado.puntaje_total}"
    assert invitado.numero_nivel == anfitrion.numero_nivel == 2
    cerrar(servidor, cliente)


def prueba_pantalla_de_cierre():
    """Al terminar el ultimo nivel los dos lados tienen que prender la
    pantalla de cierre, no quedarse en la victoria del nivel 10."""
    servidor, cliente, anfitrion, invitado = armar_partida(PUERTO + 9)

    # Recorrer la campana entera: los primeros nueve avances cargan el
    # nivel siguiente, el decimo la termina.
    for _ in range(10):
        anfitrion._avanzar_de_nivel()
        bombear(anfitrion, invitado, veces=30)

    assert anfitrion.juego_completado, "el anfitrion no cerro la partida"
    assert invitado.juego_completado, "al invitado no le llego el aviso de fin"
    assert anfitrion.numero_nivel == TOTAL_NIVELES
    # El cronometro se congela al terminar.
    congelado = anfitrion.tiempo_total
    bombear(anfitrion, invitado, veces=30)
    assert anfitrion.tiempo_total == congelado, "el cronometro sigue corriendo"

    # Y las dos pantallas se dibujan sin reventar.
    anfitrion.ganado = invitado.ganado = True
    anfitrion.on_draw()
    invitado.on_draw()
    cerrar(servidor, cliente)


def prueba_totales_del_equipo():
    """Los pasos se acumulan entre niveles: al terminar, el total tiene que
    ser mayor que los pasos del ultimo nivel suelto."""
    servidor, cliente, anfitrion, invitado = armar_partida(PUERTO + 10)
    mover_legal(anfitrion, invitado, 0)
    mover_legal(anfitrion, invitado, 1)
    pasos_nivel_1 = anfitrion.pasos
    assert pasos_nivel_1 > 0

    anfitrion._avanzar_de_nivel()            # pasa al nivel 2
    bombear(anfitrion, invitado, veces=30)
    assert anfitrion.pasos == 0, "el nivel nuevo no arranco en cero"
    assert anfitrion.pasos_equipo == pasos_nivel_1, "no se acumularon los pasos"
    assert invitado.pasos_equipo == pasos_nivel_1, "el invitado no los acumulo"
    cerrar(servidor, cliente)


def prueba_reinicio_desde_el_cierre():
    """Con la partida terminada, R del anfitrion los devuelve a los dos al
    nivel 1 con los totales en cero. El invitado no puede reiniciar solo."""
    servidor, cliente, anfitrion, invitado = armar_partida(PUERTO + 11)
    for _ in range(10):
        anfitrion._avanzar_de_nivel()
        bombear(anfitrion, invitado, veces=30)
    assert anfitrion.juego_completado and invitado.juego_completado

    # El invitado aprieta R: no pasa nada.
    invitado.on_key_press(arcade.key.R, 0)
    bombear(anfitrion, invitado, veces=20)
    assert anfitrion.juego_completado, "el invitado reinicio por su cuenta"

    # El anfitrion aprieta R: vuelven los dos.
    tiempo_viejo = anfitrion.tiempo_total
    assert tiempo_viejo > 0
    anfitrion.on_key_press(arcade.key.R, 0)
    bombear(anfitrion, invitado, veces=40)
    for nombre, vista in (("anfitrion", anfitrion), ("invitado", invitado)):
        assert not vista.juego_completado, f"{nombre} sigue en la pantalla de cierre"
        assert vista.numero_nivel == 1, f"{nombre} no volvio al nivel 1"
        assert vista.pasos_equipo == 0, f"{nombre} arrastro los pasos viejos"
        assert vista.objetos_campania == 0, f"{nombre} arrastro los objetos viejos"
        assert vista.puntaje_total == 0, f"{nombre} arrastro el puntaje viejo"
    # El cronometro arranca de nuevo: no vale cero exacto porque los
    # cuadros simulados arriba ya lo hicieron correr, pero si tiene que
    # haber vuelto a empezar en vez de seguir sumando sobre lo anterior.
    assert anfitrion.tiempo_total < tiempo_viejo, "el cronometro no se reinicio"
    cerrar(servidor, cliente)


def prueba_desconexion_en_partida():
    """Si uno cierra el juego a mitad de nivel, el otro tiene que enterarse:
    es lo que dispara el cartel de desconexión."""
    servidor, cliente, anfitrion, invitado = armar_partida(PUERTO + 8)
    cliente.cerrar()
    bombear(anfitrion, invitado, veces=40)
    assert anfitrion.desconectado, "el anfitrión no detectó que se fue el invitado"
    # Y no debe romperse al seguir jugando solo.
    anfitrion._pedir_movimiento(0, -1)
    bombear(anfitrion, invitado)
    servidor.cerrar()


PRUEBAS = [prueba_arranque_igual, prueba_movimiento_del_anfitrion,
           prueba_movimiento_del_invitado, prueba_no_se_pisan,
           prueba_sendero_compartido, prueba_movimiento_invalido_no_desincroniza,
           prueba_llave_compartida, prueba_cambio_de_nivel,
           prueba_eleccion_de_personaje, prueba_choque_de_personajes,
           prueba_no_toca_el_highscore, prueba_mirada_viaja_por_la_red,
           prueba_mirada_no_cambia_en_vertical,
           prueba_cada_jugador_mira_por_su_cuenta,
           prueba_puntaje_sincronizado, prueba_pantalla_de_cierre,
           prueba_totales_del_equipo,
           prueba_reinicio_desde_el_cierre, prueba_desconexion_en_partida]


if __name__ == "__main__":
    # Las vistas necesitan una ventana para existir, pero no hace falta
    # verla: se abre invisible y nunca se entra al bucle de Arcade.
    ventana = arcade.Window(ANCHO_VENTANA, ALTO_VENTANA, "pruebas", visible=False)
    fallos = 0
    for prueba in PRUEBAS:
        nombre = prueba.__name__.replace("prueba_", "").replace("_", " ")
        try:
            prueba()
            print(f"  OK    {nombre}")
        except AssertionError as e:
            fallos += 1
            print(f"  FALLA {nombre}: {e}")
        except Exception as e:   # noqa: BLE001 - a proposito: si una prueba
            # revienta con algo inesperado se anota y se sigue con las demas,
            # en vez de cortar la corrida entera en la primera sorpresa.
            fallos += 1
            print(f"  ERROR {nombre}: {type(e).__name__}: {e}")
    ventana.close()
    total = len(PRUEBAS)
    print(f"\n{total - fallos}/{total} pruebas de multijugador pasaron")
    raise SystemExit(1 if fallos else 0)
