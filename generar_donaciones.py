# generar_donaciones.py
# Genera los tres ítems de donación del Modo Viaje con la API de PixelLab
# (modelo normal pixflux, disponible en el plan gratuito) y los guarda
# en assets/.
#
# Uso:
#   1. Configurar la API key como variable de entorno PIXELLAB_API_KEY
#      (en PowerShell: setx PIXELLAB_API_KEY "tu-key", y reabrir la terminal).
#   2. Ejecutar:  uv run python generar_donaciones.py
#
# A diferencia de los endpoints Pro, pixflux es sincrónico: la respuesta
# trae la imagen codificada en base64, que se decodifica directo a PNG.

import base64
import json
import os
import sys
import urllib.request

API     = "https://api.pixellab.ai/v2"
API_KEY = os.environ.get("PIXELLAB_API_KEY")

# Los tres tipos de donación, en el tamaño de los ítems existentes
# (icono_llave, icono_carga: 64x64) y sin fondo para dibujarlos sobre
# cualquier celda del mapa.
DONACIONES = {
    "donacion_comida":   "pixel art item, woven basket full of fresh bread, fruits and vegetables, warm colors, top-down game item, 64x64 pixel art style",
    "donacion_libros":   "pixel art item, small stack of colorful books with one open on top, cozy warm colors, top-down game item, 64x64 pixel art style",
    "donacion_juguetes": "pixel art item, teddy bear sitting next to a red ball and a small toy block, cheerful colors, top-down game item, 64x64 pixel art style",
}


def generar(nombre, descripcion):
    """Genera la imagen y devuelve los bytes del PNG."""
    pedido = urllib.request.Request(
        f"{API}/create-image-pixflux",
        data=json.dumps({
            "description": descripcion,
            "image_size": {"width": 64, "height": 64},
            "no_background": True,
        }).encode(),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(pedido) as respuesta:
        resultado = json.loads(respuesta.read())

    imagen = resultado.get("image") or {}
    datos = imagen.get("base64") if isinstance(imagen, dict) else None
    if not datos:
        sys.exit(f"[{nombre}] respuesta sin imagen: {resultado}")
    return base64.b64decode(datos)


def main():
    if not API_KEY:
        sys.exit('Falta PIXELLAB_API_KEY en el entorno (setx PIXELLAB_API_KEY "tu-key")')

    for nombre, descripcion in DONACIONES.items():
        png = generar(nombre, descripcion)
        with open(f"assets/{nombre}.png", "wb") as f:
            f.write(png)
        print(f"[{nombre}] guardado ({len(png)} bytes)")


if __name__ == "__main__":
    main()
