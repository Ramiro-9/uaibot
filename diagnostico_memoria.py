"""Ejecutar junto a main.py: python diagnostico_memoria.py
F8: recoleccion manual (una prueba al terminar el recorrido).
Genera diagnosticos/memoria_FECHA.jsonl. No modifica el codigo del juego.
"""
from pathlib import Path
import collections
import ctypes
import datetime
import functools
import gc
import json
import os
import platform
import sys
import time
import weakref


def lector_memoria():
    if sys.platform == 'win32':
        from ctypes import wintypes
        class Contadores(ctypes.Structure):
            _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
                (n, ctypes.c_size_t) for n in (
                    'PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage',
                    'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
                    'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage', 'PrivateUsage')]
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        psapi = ctypes.WinDLL('psapi', use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Contadores), wintypes.DWORD]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        handle = kernel.GetCurrentProcess()
        def leer():
            c = Contadores()
            c.cb = ctypes.sizeof(c)
            if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(c), c.cb):
                raise ctypes.WinError(ctypes.get_last_error())
            return {'rss_MiB': round(c.WorkingSetSize / 1048576, 2),
                    'privada_MiB': round(c.PrivateUsage / 1048576, 2),
                    'pico_rss_MiB': round(c.PeakWorkingSetSize / 1048576, 2)}
        return leer
    if sys.platform.startswith('linux'):
        def leer():
            fields = dict(line.split(':', 1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
            return {'rss_MiB': round(int(fields['VmRSS'].split()[0]) / 1024, 2)}
        return leer
    raise RuntimeError('Este diagnostico admite Windows y Linux.')


def instrumentar(arcade, registrar):
    vistas = weakref.WeakValueDictionary()
    cargas = collections.Counter()
    original_init = arcade.View.__init__
    @functools.wraps(original_init)
    def init(vista, *args, **kwargs):
        original_init(vista, *args, **kwargs)
        vistas[id(vista)] = vista
    arcade.View.__init__ = init

    def estado():
        return {'vistas_vivas': [
            {'tipo': type(v).__name__, 'id': hex(id(v)), 'nivel': getattr(v, 'numero_nivel', None)}
            for v in vistas.values()], 'cargas_audio': dict(cargas)}

    def envolver(objeto, nombre, etiqueta):
        original = getattr(objeto, nombre, None)
        if original is None:
            return
        @functools.wraps(original)
        def llamada(*args, **kwargs):
            registrar(etiqueta + ':antes')
            inicio = time.perf_counter()
            try:
                resultado = original(*args, **kwargs)
            except Exception as error:
                registrar(etiqueta + ':error', error=repr(error))
                raise
            registrar(etiqueta + ':despues', duracion_ms=round((time.perf_counter()-inicio)*1000, 2))
            return resultado
        setattr(objeto, nombre, llamada)

    original_load = arcade.load_sound
    @functools.wraps(original_load)
    def cargar(path, *args, **kwargs):
        nombre = str(path)
        cargas[nombre] += 1
        registrar('audio:antes', archivo=nombre, llamada=cargas[nombre])
        sonido = original_load(path, *args, **kwargs)
        registrar('audio:despues', archivo=nombre)
        return sonido
    arcade.load_sound = cargar

    # Instrumentar el lector antes de importar las vistas que lo utilizan.
    import mapa
    envolver(mapa, 'cargar_mapa', 'mapa_tiled')
    import menu
    import juego
    import viaje
    for clase, nombres in ((menu.Menu, ('_cargar_assets',)),
                           (juego.Juego, ('_cargar_assets', '_construir_capas_estaticas')),
                           (viaje.Viaje, ('setup',))):
        for nombre in nombres:
            envolver(clase, nombre, clase.__name__ + '.' + nombre)
    envolver(arcade.Window, 'show_view', 'cambio_vista')

    dispatch = arcade.Window.dispatch_event
    @functools.wraps(dispatch)
    def evento(ventana, nombre, *args):
        if nombre == 'on_key_press' and args and args[0] == arcade.key.F8:
            registrar('gc_manual:antes')
            cantidad = gc.collect()
            registrar('gc_manual:despues', objetos_recogidos=cantidad)
            print('F8: recoleccion registrada. Espera 10 segundos antes de cerrar.')
            return True
        return dispatch(ventana, nombre, *args)
    arcade.Window.dispatch_event = evento
    return estado


def main():
    raiz = Path(__file__).resolve().parent
    os.chdir(raiz)
    if not (raiz / 'main.py').is_file():
        raise SystemExit('Coloca este archivo en la misma carpeta que main.py.')
    carpeta = raiz / 'diagnosticos'
    carpeta.mkdir(exist_ok=True)
    ruta = carpeta / ('memoria_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f') + '.jsonl')
    leer = lector_memoria()
    inicio = time.perf_counter()
    estado = lambda: {}
    with ruta.open('w', encoding='utf-8', buffering=1) as salida:
        def registrar(evento, **datos):
            fila = {'segundos': round(time.perf_counter()-inicio, 3), 'evento': evento}
            fila.update(leer())
            fila.update(estado())
            fila.update(datos)
            salida.write(json.dumps(fila, ensure_ascii=False) + '\n')
        registrar('inicio', python=sys.version, sistema=platform.platform())
        import arcade
        import pyglet
        estado = instrumentar(arcade, registrar)
        registrar('instrumentado', arcade=getattr(arcade, '__version__', '?'))
        def muestra(dt):
            registrar('muestra_2s')
        pyglet.clock.schedule_interval(muestra, 2.0)
        print('Registro:', ruta)
        print('Juga normalmente. F8 fuerza GC solo cuando quieras hacer esa prueba.')
        try:
            import main as juego_main
            juego_main.main()
        except Exception as error:
            registrar('error', error=repr(error))
            raise
        finally:
            pyglet.clock.unschedule(muestra)
            registrar('fin')
    print('Registro guardado:', ruta)


if __name__ == '__main__':
    main()
