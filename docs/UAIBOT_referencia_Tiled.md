# UAIBOT — Referencia de mapas en Tiled

Todo lo que `mapa.py` lee de un archivo `.tmx`: qué capas mira, qué nombre
tiene que llevar cada objeto, qué propiedades espera, y cuáles de esas
mecánicas ya tienen lógica de juego detrás.

Sale de leer `mapa.py` (el parser), `nivel.py` (la carga y el respaldo
procedural) y `constantes.py` (los ids de los objetos coleccionables).

> Recordatorio de alcance: los mapas de Tiled son **solo** para Modo Viaje
> (los 10 de dificultad media) y Modo Multijugador (los 10 de dificultad
> difícil). El Modo Infinito genera sus niveles de forma procedural y no
> lee `.tmx` nunca.

---

## 1. El archivo

| | |
|---|---|
| Orientación | Ortogonal |
| Grilla | 28 × 10 celdas |
| Celda | 60 × 60 píxeles (`TAM_CELDA`) |
| Ruta | `mapas/nivel_{dificultad}_{n}.tmx` |

**Capas de tiles.** Se pueden dibujar todas las capas decorativas que se
quieran —`fondo`, `fondo2`, `fondo3`—, pero el juego solo las muestra. La
única capa de tiles que se **lee** es `obstaculos`, y el nombre tiene que
ser exactamente ese, sin tilde y en minúscula.

**Capa de objetos.** Una sola, y tiene que llamarse `objetos`. Todo lo que
no sea pared, hielo ni teleporte se coloca acá como objeto suelto, con su
`name` y sus propiedades.

**Coordenadas.** La posición se convierte dividiendo por 60:
`col = x // 60`, `fila = y // 60`. La fila **0 es la de abajo**, así que la
fila 9 es la de arriba. Los jugadores arrancan siempre en `(0, 9)`, la
esquina superior izquierda.

---

## 2. Capa `obstaculos`

Acá va todo lo que se pinta con tiles. Cada tile se clasifica por su
propiedad `tipo`.

| `tipo` | Propiedades extra | Qué hace |
|---|---|---|
| `pared` | — | Bloquea el paso. Es también lo que se asume si el tile no tiene la propiedad, o si la tiene vacía. |
| `hielo` | — | Al pisarlo, el personaje sigue deslizándose una celda más en la misma dirección, si esa celda está libre. |
| `teleporte` | `id_teleporte` (int) | Se vincula con el otro teleporte que tenga el mismo id. **Tienen que ser exactamente dos por id**: con uno solo o con tres, el par no se arma y ninguno funciona. |

---

## 3. Capa `objetos`

El `name` del objeto es lo que decide qué es. Se pasa a minúsculas antes de
compararlo, así que la mayúscula no importa — pero **un nombre que no esté
en esta lista se ignora en silencio**, sin error ni aviso.

Estados:

- **Anda** — se parsea, tiene lógica de juego y ya está usado en mapas.
- **Parcial** — anda en algunos modos pero no en todos.
- **Sin lógica** — se lee y se guarda, pero ningún código de juego lo mira.
- **Sin colocar** — tiene lógica, pero ningún mapa lo usa todavía.

| `name` | Propiedades | Qué hace | Estado |
|---|---|---|---|
| `portal` | — | El merendero: llegar acá completa el nivel. Uno por mapa. | Anda |
| `llave` | — | Se recoge pisándola y abre todas las `puerta_llave` del mapa. Una por mapa. | Anda |
| `puerta_llave` | — | Cerrada hasta que alguien agarre la llave. Puede haber varias. | Anda |
| `placa` | `id_puerta` | Placa de presión. Abre la `puerta_placa` que lleve el mismo `id_puerta`. | Anda |
| `puerta_placa` | `id_puerta` | Se abre cuando se pisa su placa. En multijugador alcanza con que la pise cualquiera de los dos. | Anda |
| `caja` | — | Se empuja caminando contra ella, si el personaje tiene la habilidad de Carga. | **Parcial** |
| `objeto` | `objeto` (uno de los 10 ids) | Coleccionable cooperativo del Multijugador. Lo consigue el equipo si cualquiera de los dos pisa la celda, y se desbloquea en el Bestiario. | **Sin colocar** |
| `donacion` | `tipo` = `comida` / `libros` / `juguetes` / `sillas` | Coleccionable del Modo Viaje; alimenta el contador «Donaciones: x/y» del panel. | **Sin colocar** |
| `interruptor` | `id_puerta` | Pensado para que los dos jugadores pisen uno cada uno al mismo tiempo y se abra la puerta vinculada. | **Sin lógica** |
| `pozo` | — | Celda intransitable hasta que una caja cae adentro y queda como piso. | **Sin lógica** |
| `control_cinta` | `id_cinta`, `direccion` | Celda que, al pisarla, mueve el `bloque_cinta` del mismo id en la dirección indicada. | **Sin lógica** |
| `bloque_cinta` | `id_cinta` | El bloque que mueve su control. | **Sin lógica** |

### Detalle de los estados que no son «Anda»

- **`caja` (parcial)** — hoy solo está en `nivel_medio_1` y
  `nivel_medio_2`. En Multijugador **no colisiona**: los jugadores la
  atraviesan y la caja no se mueve. El empuje vive en
  `juego.py:679-701`, dentro de `_intentar_mover`, que es justo el método
  que `Multijugador` reemplaza por su propio `_resolver_movimiento`.
- **`objeto` (sin colocar)** — ningún `.tmx` tiene uno. Como
  `self.donaciones` queda vacía, `_revisar_objetos()` nunca entra al
  bucle, nunca se llama a `guardado.desbloquear_objeto()`, y los diez
  objetos del Bestiario quedan en silueta para siempre. El arte, las
  descripciones, el cartel de «¡OBJETO CONSEGUIDO!» y el guardado ya
  están hechos: falta solamente colocarlos.
- **`donacion` (sin colocar)** — mismo caso en Modo Viaje: el contador
  «Donaciones» del panel sale siempre vacío porque no hay ninguna en los
  mapas.
- **`interruptor` (sin lógica)** — es la mecánica #6 del documento MDA, y
  la única que obliga a los dos jugadores a coordinarse de verdad. Sin
  ella, el cooperativo es «dos personas resolviendo el mismo laberinto».

---

## 4. Con qué tener cuidado

- **Una propiedad que falta no da error: toma un valor por defecto.** El
  más peligroso es `objeto`, que sin la propiedad vale `foto` — si se
  olvida en los diez mapas, quedan diez fotos y nueve objetos que nunca
  se consiguen. Los otros: `tipo` de donación vale `comida`, `direccion`
  vale `derecha`, y los `id_puerta` / `id_cinta` quedan en nulo.
- **Los teleportes van de a pares exactos.** El vínculo solo se arma si
  hay dos celdas con el mismo `id_teleporte`. Con una sola, o con tres,
  no se arma ninguno y el mapa se juega sin ese teleporte.
- **Si el `.tmx` no carga, el juego no se rompe: cambia de mapa.**
  `nivel.py` cae a la generación procedural y sigue como si nada, así que
  un mapa que no se ve como se lo dibujó puede ser un error de carga y no
  un error de diseño. La consola lo dice.
- **Los nombres de capa son exactos**: `obstaculos` y `objetos`, sin
  tilde y en minúscula. Si no coinciden, esa capa simplemente no se lee.
- **El mapa no viaja por la red.** En Multijugador las dos computadoras
  cargan su propio `.tmx` y el anfitrión solo dice qué número de nivel
  es. Si los archivos no son idénticos en las dos, cada jugador ve un
  mapa distinto.

---

## 5. Lo que falta colocar para la 1.6

- [ ] **Un `objeto` en cada mapa difícil.** De `nivel_dificil_1` a
      `nivel_dificil_10`, uno por mapa, sin repetir el id. Es lo único
      que falta para que la sección de objetos del Bestiario se pueda
      llenar jugando. Los diez ids, en el orden en que aparecen en
      `constantes.py`:

      foto · tornillo · mochila · farol · alcanzador
      rueda · herramientas · panel · bateria · taza

- [ ] **Donaciones en los mapas de Viaje.** De `nivel_medio_1` a
      `nivel_medio_10`, con `tipo` en `comida`, `libros`, `juguetes` o
      `sillas`. La silla de ruedas ya aparece en el Tutorial, donde es una
      mecánica —hay que pasarle por al lado sin pisarla—; como donación se
      recoge pisándola, igual que las otras tres.

- [ ] **Cajas en los mapas difíciles — después del código.** Conviene
      esperar a que `Multijugador` maneje la colisión y el empuje;
      colocarlas antes deja un bug a la vista.

---

## Si se agrega una mecánica nueva

El lugar donde se declara el nombre del objeto y sus propiedades es
`mapa.py`, en el bucle que recorre la capa `objetos`. Agregar un `elif`
ahí alcanza para que el dato llegue al juego; la lógica de qué hace esa
mecánica va después, en `juego.py` o en el modo que corresponda.
