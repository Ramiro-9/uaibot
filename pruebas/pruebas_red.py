# pruebas_red.py
# Prueba automática de la capa de red del Modo Multijugador, sobre
# 127.0.0.1 (la dirección que toda computadora tiene hacia sí misma). Es la
# prueba a la que remite el comentario de cabecera de red.py.
#
# Sirve para separar dos culpas que desde adentro del juego se confunden:
# si esta prueba pasa y el multijugador igual falla, el problema está en la
# lógica de multijugador.py, no en la red. Y no hace falta una segunda
# computadora ni abrir el juego para correrla.
#
# Se ejecuta con:  python pruebas/pruebas_red.py   (desde la raíz)

import os
import sys

# Este archivo vive en pruebas/, pero importa los módulos del juego, que
# están en la raíz del proyecto. Agregarla al path deja que la prueba se
# corra desde donde sea: "python pruebas/pruebas_red.py" parado en la raíz,
# o entrando primero a la carpeta. Sin esto solo andaría como módulo.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import socket
import time

import red

# Puerto distinto al del juego, para poder correr esta prueba con una
# partida abierta sin pelearse por el puerto.
PUERTO = 50117


def esperar(condicion, limite=3.0):
    """Espera a que se cumpla una condición que depende de otro hilo (la
    conexión viaja por la red y la lee un hilo de fondo, así que nunca está
    lista en el instante siguiente). Devuelve si se cumplió antes del
    límite."""
    fin = time.time() + limite
    while time.time() < fin:
        if condicion():
            return True
        time.sleep(0.01)
    return False


def un_par(puerto):
    """Arma un servidor y un cliente ya conectados entre sí."""
    servidor = red.Servidor(puerto=puerto)
    assert servidor.error is None, servidor.error
    cliente = red.Cliente("127.0.0.1", puerto=puerto)
    assert cliente.error is None, cliente.error
    assert esperar(lambda: servidor.hay_jugador), "el servidor no aceptó al cliente"
    return servidor, cliente


def recibir(lado, cuantos=1, limite=3.0):
    """Junta mensajes de un lado hasta llegar a `cuantos` o agotar el
    tiempo. Hace falta acumular en vez de leer una sola vez porque
    leer_mensajes() no bloquea: devuelve lo que haya llegado hasta ese
    instante, que bien puede ser nada todavía."""
    juntados = []
    fin = time.time() + limite
    while time.time() < fin and len(juntados) < cuantos:
        juntados.extend(lado.leer_mensajes())
        if len(juntados) < cuantos:
            time.sleep(0.01)
    return juntados


# ── Las pruebas ───────────────────────────────────────────────────────────

def prueba_conexion():
    servidor, cliente = un_par(PUERTO)
    assert cliente.conectado
    assert servidor.hay_jugador
    servidor.cerrar()
    cliente.cerrar()


def prueba_ida_y_vuelta():
    """Un mensaje en cada sentido, con la estructura real del juego."""
    servidor, cliente = un_par(PUERTO + 1)

    servidor.enviar({"t": "estado", "pasos": 7, "llave": True,
                     "jugadores": [[3, 4], [5, 6]]})
    recibidos = recibir(cliente)
    assert len(recibidos) == 1, "el estado del host no llegó al invitado"
    assert recibidos[0]["t"] == "estado"
    assert recibidos[0]["pasos"] == 7
    # Las tuplas de celdas viajan como listas: JSON no tiene tuplas.
    assert recibidos[0]["jugadores"] == [[3, 4], [5, 6]]

    cliente.enviar({"t": "mover", "dc": 0, "df": 1})
    recibidos = recibir(servidor)
    assert recibidos == [{"t": "mover", "dc": 0, "df": 1}], recibidos

    servidor.cerrar()
    cliente.cerrar()


def prueba_mensajes_pegados_y_partidos():
    """Lo que este protocolo tiene que resolver: TCP entrega un flujo de
    bytes sin fronteras, así que dos mensajes seguidos pueden llegar
    pegados en una sola lectura, y uno solo puede llegar cortado al medio.
    Se escribe directo al socket para forzar los dos casos."""
    servidor, cliente = un_par(PUERTO + 2)

    a = json.dumps({"t": "mover", "dc": 1, "df": 0}).encode() + b"\n"
    b = json.dumps({"t": "llave"}).encode() + b"\n"

    # Pegados: los dos en un solo envío.
    cliente.conexion.sock.sendall(a + b)
    recibidos = recibir(servidor, cuantos=2)
    assert len(recibidos) == 2, f"llegaron {len(recibidos)} mensajes, no 2"
    assert recibidos[0]["t"] == "mover" and recibidos[1]["t"] == "llave"

    # Partido: la mitad, una pausa, y la otra mitad.
    mitad = len(a) // 2
    cliente.conexion.sock.sendall(a[:mitad])
    time.sleep(0.1)
    assert servidor.leer_mensajes() == [], "entregó un mensaje incompleto"
    cliente.conexion.sock.sendall(a[mitad:])
    recibidos = recibir(servidor)
    assert len(recibidos) == 1 and recibidos[0]["t"] == "mover", recibidos

    servidor.cerrar()
    cliente.cerrar()


def prueba_mensaje_corrupto():
    """Basura en el medio del flujo no debe cortar la partida: se descarta
    esa línea y las siguientes siguen llegando."""
    servidor, cliente = un_par(PUERTO + 3)

    cliente.conexion.sock.sendall(b"esto no es json\n")
    cliente.conexion.sock.sendall(json.dumps({"t": "llave"}).encode() + b"\n")

    recibidos = recibir(servidor)
    assert len(recibidos) == 1, "no descartó la línea corrupta"
    assert recibidos[0]["t"] == "llave"
    assert servidor.hay_jugador, "la basura tumbó la conexión"

    servidor.cerrar()
    cliente.cerrar()


def prueba_desconexion_del_cliente():
    """Si el invitado cierra la ventana, el host se tiene que enterar: es
    lo que dispara el aviso de desconexión en pantalla."""
    servidor, cliente = un_par(PUERTO + 4)
    cliente.cerrar()
    assert esperar(lambda: not servidor.hay_jugador), "el host no detectó la caída"
    # Enviar a una conexión caída devuelve False en vez de reventar.
    assert servidor.enviar({"t": "estado"}) is False
    servidor.cerrar()


def prueba_desconexion_del_host():
    """Y al revés: si el host se va, el invitado también se entera."""
    servidor, cliente = un_par(PUERTO + 5)
    servidor.cerrar()
    assert esperar(lambda: not cliente.conectado), "el invitado no detectó la caída"
    assert cliente.enviar({"t": "mover", "dc": 1, "df": 0}) is False
    cliente.cerrar()


def prueba_conectar_a_la_nada():
    """IP mal tipeada o partida no creada: tiene que dar un error legible
    en vez de colgar el juego."""
    cliente = red.Cliente("127.0.0.1", puerto=PUERTO + 6)
    assert cliente.error is not None, "no reportó el error de conexión"
    assert not cliente.conectado


def prueba_puerto_ocupado():
    """Dos partidas creadas en la misma computadora: la segunda tiene que
    avisar, no romperse."""
    ocupador = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ocupador.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ocupador.bind(("", PUERTO + 7))
    ocupador.listen(1)
    try:
        servidor = red.Servidor(puerto=PUERTO + 7)
        assert servidor.error is not None, "no avisó que el puerto estaba ocupado"
        servidor.cerrar()
    finally:
        ocupador.close()


def prueba_ip_local():
    """La IP que se le dicta al otro jugador tiene que ser una IPv4 válida."""
    ip = red.ip_local()
    partes = ip.split(".")
    assert len(partes) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in partes), ip


PRUEBAS = [prueba_conexion, prueba_ida_y_vuelta, prueba_mensajes_pegados_y_partidos,
           prueba_mensaje_corrupto, prueba_desconexion_del_cliente,
           prueba_desconexion_del_host, prueba_conectar_a_la_nada,
           prueba_puerto_ocupado, prueba_ip_local]


if __name__ == "__main__":
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
    total = len(PRUEBAS)
    print(f"\n{total - fallos}/{total} pruebas de red pasaron")
    raise SystemExit(1 if fallos else 0)
