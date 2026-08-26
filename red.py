# red.py
# Capa de red del Modo Multijugador. Este archivo se ocupa ÚNICAMENTE de
# mandar y recibir mensajes: no sabe nada de UAIBOT, de niveles ni de
# celdas. Toda la lógica de juego vive en multijugador.py.
#
# Está separado a propósito para poder probarlo solo, sin abrir el juego
# (ver la prueba automática sobre 127.0.0.1), que es lo que permite
# distinguir "falla la red" de "falla el juego" cuando algo no anda.
#
# ── Cómo funciona ────────────────────────────────────────────────────────
# Arcade dibuja en un único hilo, y leer de un socket es una operación que
# BLOQUEA hasta que llega algo. Si se leyera desde on_update(), el juego se
# congelaría esperando al otro jugador. Por eso cada conexión tiene un hilo
# de fondo dedicado a leer, y ese hilo NUNCA toca el estado del juego: deja
# lo que recibe en una queue.Queue, que la vista vacía desde on_update().
# La cola es el único punto de contacto entre los dos hilos, y es segura
# para eso por diseño.
#
# ── Protocolo ────────────────────────────────────────────────────────────
# Un mensaje = un objeto JSON + un salto de línea. Se eligió JSON en texto
# plano en vez de un formato binario compacto porque se puede leer a simple
# vista cuando algo falla. El salto de línea hace de separador: TCP entrega
# un flujo de bytes sin fronteras, así que sin un separador explícito dos
# mensajes seguidos podrían llegar pegados o cortados a la mitad.

import json
import queue
import socket
import threading

# Puerto por el que se juega. Es de la franja alta (49152-65535), reservada
# para uso libre, así que no choca con servicios conocidos del sistema.
PUERTO_JUEGO = 50007

TIEMPO_ESPERA_CONEXION = 5.0   # segundos que el cliente espera al conectar


class _Conexion:
    """Una conexión ya establecida, del lado que sea. Envuelve un socket y
    le suma el hilo lector y la cola de mensajes recibidos.

    La usan tanto Servidor como Cliente: una vez que hay socket, los dos
    lados hablan exactamente igual."""

    def __init__(self, sock, al_desconectar=None):
        self.sock     = sock
        self.recibidos = queue.Queue()
        self.conectado = True
        self._al_desconectar = al_desconectar

        # Un lock para enviar: los dos hilos (el del juego y el lector, que
        # podría responder algo) pueden querer escribir a la vez, y dos
        # sendall() simultáneos entrelazarían los bytes de ambos mensajes.
        self._lock_envio = threading.Lock()

        # daemon=True para que el hilo no impida cerrar el juego si quedó
        # esperando datos que nunca llegan.
        self._hilo = threading.Thread(target=self._bucle_lectura, daemon=True)
        self._hilo.start()

    def _bucle_lectura(self):
        """Corre en el hilo de fondo: lee del socket hasta que se corta la
        conexión, y va dejando los mensajes completos en la cola."""
        buffer = b""
        try:
            while self.conectado:
                datos = self.sock.recv(4096)
                if not datos:
                    break   # el otro lado cerró la conexión

                buffer += datos
                # Puede haber llegado más de un mensaje de una, o uno
                # cortado a la mitad: se procesan las líneas completas y lo
                # que sobra queda en el buffer para la próxima vuelta.
                while b"\n" in buffer:
                    linea, buffer = buffer.split(b"\n", 1)
                    if not linea.strip():
                        continue
                    try:
                        self.recibidos.put(json.loads(linea.decode("utf-8")))
                    except (ValueError, UnicodeDecodeError):
                        # Un mensaje corrupto no debe tumbar la conexión.
                        pass
        except OSError:
            # Socket cerrado o error de red: se trata como desconexión.
            pass
        finally:
            self._marcar_desconectado()

    def _marcar_desconectado(self):
        if not self.conectado:
            return
        self.conectado = False
        if self._al_desconectar:
            self._al_desconectar()

    def enviar(self, mensaje):
        """Manda un diccionario como una línea JSON. Devuelve True si se
        pudo enviar. No lanza excepción si la conexión se cayó: el juego no
        debería romperse porque el otro jugador cerró la ventana."""
        if not self.conectado:
            return False
        datos = (json.dumps(mensaje) + "\n").encode("utf-8")
        try:
            with self._lock_envio:
                self.sock.sendall(datos)
            return True
        except OSError:
            self._marcar_desconectado()
            return False

    def leer_mensajes(self):
        """Devuelve todos los mensajes recibidos desde la última llamada.
        Pensado para llamarse desde on_update(): no bloquea nunca."""
        mensajes = []
        while True:
            try:
                mensajes.append(self.recibidos.get_nowait())
            except queue.Empty:
                break
        return mensajes

    def cerrar(self):
        self._marcar_desconectado()
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self.sock.close()
        except OSError:
            pass


class Servidor:
    """El lado que crea la partida. Abre un puerto, espera a que se conecte
    el otro jugador y a partir de ahí es la autoridad: su estado del juego
    es el que vale."""

    def __init__(self, puerto=PUERTO_JUEGO):
        self.puerto    = puerto
        self.conexion  = None    # se llena cuando el cliente se conecta
        self.error     = None    # texto del error, si no se pudo abrir
        self._sock_escucha = None
        self._cerrando = False

        try:
            self._sock_escucha = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Permite reabrir el mismo puerto enseguida después de cerrar,
            # sin esperar el tiempo que el sistema lo deja reservado.
            self._sock_escucha.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock_escucha.bind(("", self.puerto))
            self._sock_escucha.listen(1)
        except OSError as e:
            self.error = f"No se pudo abrir el puerto {self.puerto}: {e}"
            return

        self._hilo = threading.Thread(target=self._esperar_cliente, daemon=True)
        self._hilo.start()

    def _esperar_cliente(self):
        """Acepta UNA conexión y arma la _Conexion. Corre en su propio hilo
        porque accept() bloquea hasta que alguien se conecta."""
        try:
            sock_cliente, _ = self._sock_escucha.accept()
            self.conexion = _Conexion(sock_cliente)
        except OSError:
            if not self._cerrando:
                self.error = "Se corto la espera de conexion"

    @property
    def hay_jugador(self):
        return self.conexion is not None and self.conexion.conectado

    def enviar(self, mensaje):
        return self.conexion.enviar(mensaje) if self.conexion else False

    def leer_mensajes(self):
        return self.conexion.leer_mensajes() if self.conexion else []

    def cerrar(self):
        self._cerrando = True
        if self.conexion:
            self.conexion.cerrar()
        if self._sock_escucha:
            try:
                self._sock_escucha.close()
            except OSError:
                pass


class Cliente:
    """El lado que se une a una partida existente. No simula el juego: le
    manda al host lo que el jugador quiere hacer y dibuja lo que el host
    le contesta."""

    def __init__(self, ip, puerto=PUERTO_JUEGO):
        self.conexion = None
        self.error    = None
        try:
            sock = socket.create_connection((ip, puerto), timeout=TIEMPO_ESPERA_CONEXION)
            # Se saca el timeout después de conectar: durante la partida el
            # hilo lector tiene que quedarse esperando indefinidamente, no
            # cortar cada 5 segundos porque nadie se movió.
            sock.settimeout(None)
            self.conexion = _Conexion(sock)
        except OSError as e:
            self.error = f"No se pudo conectar a {ip}: {e}"

    @property
    def conectado(self):
        return self.conexion is not None and self.conexion.conectado

    def enviar(self, mensaje):
        return self.conexion.enviar(mensaje) if self.conexion else False

    def leer_mensajes(self):
        return self.conexion.leer_mensajes() if self.conexion else []

    def cerrar(self):
        if self.conexion:
            self.conexion.cerrar()


def ip_local():
    """Devuelve la IP de esta computadora en la red local, que es la que hay
    que dictarle al otro jugador para que se conecte.

    Se averigua "abriendo" un socket UDP hacia una dirección externa: no se
    manda nada ni hace falta internet, pero obliga al sistema a elegir qué
    placa de red usaría, que es justo el dato que se quiere. Es más
    confiable que preguntar por el nombre del equipo, que en Windows suele
    contestar 127.0.0.1."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()
