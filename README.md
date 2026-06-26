## Instalación

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Controles

| Tecla | Acción |
|-------|--------|
| Flechas o WASD | Mover UAIBOT |
| E | Recoger llave (dificultad difícil) |
| R | Reiniciar nivel |
| N | Reiniciar desde el nivel 1 |
| ESC | Volver al menú |

## Para el diseñador de sprites

Todos los archivos van en la carpeta `assets/` en formato PNG con fondo transparente.

### Tamaño

Todos los tiles: `60x60` px

### Archivos necesarios

| Archivo | Descripción |
|---------|-------------|
| `cesped.png` | Tile de fondo, se repite en toda la grilla |
| `pared.png` | Árbol o piedra, bloquea el paso de UAIBOT |
| `portal.png` | Portal para pasar al siguiente nivel |
| `llave.png` | Llave que UAIBOT debe recoger en dificultad difícil |
| `huella_arriba.png` | Huella cuando UAIBOT caminó hacia arriba |
| `huella_abajo.png` | Huella cuando UAIBOT caminó hacia abajo |
| `huella_izquierda.png` | Huella cuando UAIBOT caminó hacia la izquierda |
| `huella_derecha.png` | Huella cuando UAIBOT caminó hacia la derecha |

### Sonidos existentes

Estos ya están en `assets/` pero los podemos cambiar

| Archivo | Descripción |
|---------|-------------|
| `Moverse.wav` | Sonido al caminar |
| `NoMoverse.wav` | Sonido al chocar o no poder moverse |
| `CompletedLevel.wav` | Sonido al completar un nivel |

### Sprites existentes

| Archivo | Descripción |
|---------|-------------|
| `Idle.png` | Spritesheet de UAIBOT quieto, 6 frames de 128x128 |
| `Walk.png` | Spritesheet de UAIBOT caminando, 6 frames de 128x128 |
| `merendero.png` | Imagen del merendero final, 60x60 |

### Flujo de trabajo

si queres subir cambios, lo haces asi:

```bash
git add assets/
git commit -m "agrego sprite cesped"
git push
```


