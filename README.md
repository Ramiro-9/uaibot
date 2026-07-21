# UAIBOT — OFIRCA 2026

Juego de grilla en 2D (vista cenital) hecho con `arcade`, desarrollado
para la Olimpíada Federal de Informática y Robótica. UAIBOT debe llegar
al merendero sorteando obstáculos, mecánicas de puzzle y niveles con
dificultad creciente.

Este README es referencia personal para seguir desarrollando — no es
el documento de entrega (para eso están `prompt.txt` y `extras.txt`
en la carpeta del proyecto).

---

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
| Flechas o WASD | Mover UAIBOT (configurable en el menú) |
| E | Recoger llave (dificultad difícil) |
| R | Reiniciar nivel actual |
| N | Reiniciar desde el nivel 1 |
| ESC | Volver al menú |
| Mouse | Navegar y seleccionar opciones del menú (además del teclado) |

---

## Descripción del juego y mecánicas

### Estructura general
- Menú principal con selección de **controles** (flechas/WASD) y
  **dificultad** (fácil/medio/difícil), navegable por teclado o mouse.
- Progresión de **10 niveles**, con puntaje acumulado entre ellos.
- En dificultad fácil, el **nivel 1 es fijo** (4 paredes predefinidas)
  — es el nivel de referencia que cumple las 7 consignas obligatorias
  del desafío de forma clara.
- Del nivel 2 en adelante (fácil), y todos los niveles en medio/difícil,
  los mapas se **generan proceduralmente**, validando con BFS que
  siempre exista un camino posible entre el inicio y el portal.
- En dificultad medio y difícil, los niveles también pueden cargarse
  desde archivos `.tmx` diseñados en **Tiled** (ver sección
  "Mapas en Tiled" más abajo).

### Mecánicas de juego
- **Sendero no repetible**: UAIBOT no puede volver a pisar una celda
  por la que ya pasó en el nivel actual.
- **Hielo**: al pisar una celda de hielo, UAIBOT desliza una celda
  extra en la misma dirección del movimiento.
- **Teletransporte**: pares de celdas vinculadas que trasladan a
  UAIBOT de una a otra (con animación idle en loop).
- **Llave + puertas con llave**: en dificultad difícil, hay que
  recoger una llave (tecla E) antes de poder cruzar el portal; al
  recogerla se abren automáticamente todas las puertas con llave del
  nivel (con animación de apertura).
- **Placas de presión + puertas con placa**: pisar una placa abre su
  puerta vinculada (vinculación por `id_puerta`, configurada en
  Tiled). También con animación de apertura.
- **Límite de pasos** (dificultad medio/difícil): si se supera el
  doble del recorrido mínimo calculado por BFS, se pierde el nivel.
- **Puntaje por eficiencia**: se compara la cantidad de pasos usados
  contra el mínimo posible para asignar 1 a 10 puntos por nivel.

### Persistencia
`guardado.json` guarda highscore, controles preferidos y última
dificultad elegida entre partidas.

---

## Mapas en Tiled

Para dificultad media/difícil, los niveles pueden diseñarse en el
editor Tiled y cargarse desde `mapas/nivel_<dificultad>_<numero>.tmx`.

Todo se define en la capa de objetos `objetos` (no se pintan tiles):

| Objeto | Nombre en Tiled | Propiedades |
|--------|------------------|-------------|
| Portal | `portal` | — |
| Llave | `llave` | — |
| Puerta con llave | `puerta_llave` | — |
| Puerta con placa | `puerta_placa` | `id_puerta` (int) |
| Placa de presión | `placa` | `id_puerta` (int, debe coincidir con su puerta) |
| Teleporte | `teleporte` | `id_teleporte` (int, se vinculan de a pares) |

La capa de tiles `obstaculos` se usa para paredes (`tipo: pared` o
vacío) y hielo (`tipo: hielo`), vía propiedades del tile.

---

## Estructura de archivos

```
UAIBOT/
├── main.py            # arranca la ventana y muestra el menú
├── menu.py             # menú principal (teclado + mouse), submenús
├── juego.py             # vista principal del juego: setup, input,
│                        # update, dibujo. Contiene la clase Particula
│                        # para el efecto de victoria
├── nivel.py             # generación procedural de niveles + carga
│                        # desde .tmx + utilidades BFS (camino /
│                        # pasos mínimos)
├── mapa.py              # parser de archivos .tmx (Tiled) hacia las
│                        # estructuras que usa nivel.py
├── sprites.py            # carga de texturas con caché y fallback
├── guardado.py            # persistencia en guardado.json
├── constantes.py          # configuración de grilla, rutas de
│                          # sprites, posiciones fijas
├── guardado.json           # datos guardados (no versionar cambios
│                           # de este archivo si son de una partida
│                           # personal de prueba)
├── requirements.txt
├── assets/               # sprites, sonidos, spritesheets (ver tabla
│                         # más abajo)
└── mapas/                 # archivos .tmx para dificultad medio/difícil
```

---

## Para el diseñador de sprites

Todos los archivos van en la carpeta `assets/` en formato PNG con
fondo transparente.

### Tamaño
Tiles simples: `60x60` px. Ver la tabla de abajo para los
spritesheets, que tienen su propio tamaño de frame.

### Archivos necesarios

| Archivo | Descripción |
|---------|-------------|
| `cesped.png` | Tile de fondo, se repite en toda la grilla |
| `pared.png` | Árbol o piedra, bloquea el paso de UAIBOT |
| `huella_arriba.png` | Huella cuando UAIBOT caminó hacia arriba |
| `huella_abajo.png` | Huella cuando UAIBOT caminó hacia abajo |
| `huella_izquierda.png` | Huella cuando UAIBOT caminó hacia la izquierda |
| `huella_derecha.png` | Huella cuando UAIBOT caminó hacia la derecha |
| `hielo.png` | Tile de hielo |
| `placa.png` | Placa de presión (fallback si no hay animación) |

### Spritesheets (animados)

| Archivo | Frames | Tipo de animación |
|---------|--------|--------------------|
| `Idle.png` | 6, de 128x128 c/u | UAIBOT quieto, loop |
| `Walk.png` | 6, de 128x128 c/u | UAIBOT caminando, loop |
| `llave_anim.png` | 9 | Idle en loop |
| `portal_anim.png` | 8 | Idle en loop |
| `teleporte_anim.png` | 2 | Idle en loop |
| `puerta_llave_anim.png` | 5 (937x150 total) | Apertura de un sentido (cerrada → abierta), se dispara una vez |
| `puerta_placa_anim.png` | 5 (907x155 total) | Apertura de un sentido, se dispara una vez |

### Imágenes sueltas
- `merendero.png` — imagen final del merendero (60x60), se dibuja en
  el portal del último nivel.
- `fondo_menu.png` — fondo del menú principal (generado con IA, ver
  `prompt.txt`).
- `botones.png` — spritesheet de 5 botones tipo ribbon para el menú.

### Sonidos existentes

| Archivo | Descripción |
|---------|-------------|
| `Moverse.wav` | Sonido al caminar |
| `NoMoverse.wav` | Sonido al chocar o no poder moverse |
| `CompletedLevel.wav` | Sonido al completar un nivel |
| `GameLevelMusic.wav` | Música de fondo en loop durante el juego |

### Flujo de trabajo

```bash
git add assets/
git commit -m "agrego sprite cesped"
git push
```

---

## Pendientes / ideas para seguir (referencia personal)

Ver `revision_refactor_uaibot.md` para el detalle de puntos de
refactorización identificados (prioridad: blindar `_generar_llave`
contra mapas sin celdas libres, centralizar el hitbox del menú).
