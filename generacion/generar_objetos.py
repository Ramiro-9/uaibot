# generar_objetos.py
# Genera los 10 objetos coleccionables del Modo Multijugador con la API de
# PixelLab (modelo normal pixflux, plan gratuito). Cada objeto está ligado a
# la familia de UAIBOT o al merendero; nombre y descripción viven en
# constantes.OBJETOS_MULTIJUGADOR.
#
# Uso: la key se lee del registro de Windows (setx PIXELLAB_API_KEY "token")
#   uv run python generacion/generar_objetos.py

import base64
import json
import os
import sys
import urllib.request

API = "https://api.pixellab.ai/v2"

# Los PNG van a assets/imagenes/ de la raíz del proyecto, no al directorio
# desde el que se corre el script: este archivo vive en generacion/ y se
# puede ejecutar parado en cualquier lado.
RAIZ   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(RAIZ, "assets", "imagenes")

key = None

OBJETOS = {
    "objeto_foto":       "pixel art item, framed family photo polaroid of four cute small white robots standing together, warm cozy colors, side view game item, 64x64 pixel art style",
    "objeto_tornillo":   "pixel art item, shiny golden screw with a small sparkle, standing upright, game item, 64x64 pixel art style",
    "objeto_mochila":    "pixel art item, small pink backpack with heart patch and side pocket, cute and sturdy, side view game item, 64x64 pixel art style",
    "objeto_farol":      "pixel art item, vintage hand lantern glowing with warm yellow light, glass panels and metal handle, game item, 64x64 pixel art style",
    "objeto_alcanzador": "pixel art item, telescopic grabber reacher tool with claw grip end and green handle, assistive device, side view game item, 64x64 pixel art style",
    "objeto_rueda":      "pixel art item, single robotic wheel with tire tread and hubcap shine, spare part, game item, 64x64 pixel art style",
    "objeto_herramientas": "pixel art item, small red metal toolbox slightly open showing wrench and screwdriver handles, game item, 64x64 pixel art style",
    "objeto_panel":      "pixel art item, small foldable solar panel with blue cells and grid lines, tilted stand, game item, 64x64 pixel art style",
    "objeto_bateria":    "pixel art item, chunky rechargeable battery pack with green charge indicator lights and lightning bolt symbol, game item, 64x64 pixel art style",
    "objeto_taza":       "pixel art item, cheerful ceramic mug with steam rising and a small heart painted on it, warm colors, game item, 64x64 pixel art style",
}


def generar(nombre, descripcion):
    pedido = urllib.request.Request(
        f"{API}/create-image-pixflux",
        data=json.dumps({
            "description": descripcion,
            "image_size": {"width": 64, "height": 64},
            "no_background": True,
            "negative_description": "text, watermark, border, frame, characters, hands",
        }).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(pedido) as respuesta:
        resultado = json.loads(respuesta.read())
    datos = (resultado.get("image") or {}).get("base64")
    if not datos:
        sys.exit(f"[{nombre}] respuesta sin imagen: {resultado}")
    return base64.b64decode(datos)


def main():
    global key
    if os.environ.get("PIXELLAB_API_KEY"):
        key = os.environ["PIXELLAB_API_KEY"]
    else:
        import subprocess
        r = subprocess.run(
            ["reg", "query", "HKCU\\Environment", "/v", "PIXELLAB_API_KEY"],
            capture_output=True, text=True)
        key = r.stdout.strip().split()[-1] if "REG_SZ" in r.stdout else None
    if not key:
        sys.exit("Falta PIXELLAB_API_KEY")

    for nombre, descripcion in OBJETOS.items():
        png = generar(nombre, descripcion)
        with open(os.path.join(ASSETS, f"{nombre}.png"), "wb") as f:
            f.write(png)
        print(f"[{nombre}] guardado ({len(png)} bytes)")


if __name__ == "__main__":
    main()
