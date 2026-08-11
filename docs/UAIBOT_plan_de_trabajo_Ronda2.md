# UAIBOT — Plan de trabajo Ronda 2

Equipo 30094 - FuryDevelopers · OFIRCA 2026
Consigna oficial de Ronda 2: **10 de agosto** · Entrega: **27 de agosto**

---

## Estado actual — qué se puede arrancar ya

Toda la **Fase 0** está lista para empezar hoy mismo: ninguna de sus
tareas depende de la consigna oficial ni de decisiones de diseño
pendientes.

- 0.1 Performance + comentarios (feedback Ronda 1)
- 0.2 Sistema base de caja empujable
- 0.3 Extender `mapa.py` para los objetos nuevos de Tiled
- 0.4 Reestructurar `menu.py` a 6 entradas
- 0.5 Extender `guardado.py`

**Lo único que sigue pendiente y frena más adelante** (no frena la
Fase 0):

- **Habilidades de los personajes** (UAIBOTA, UAIBOTINA, UAIBOTINO) —
  bloquea Fase 3 (Modo Viaje) si se llega ahí sin definirlo antes.
- **Cantidad de niveles** de Modo Viaje y Multijugador — todavía "a
  definir", no bloquea el código, pero sí cuánto contenido hay que
  diseñar en Tiled.
- **Consigna oficial de Ronda 2** (10 de agosto) — puede traer
  requisitos puntuales que ajusten el plan; nada de la Fase 0 debería
  quedar invalidado por eso, pero conviene revisar el plan ese día.

---

## Cómo está armado este plan

Está dividido en una **Fase 0** (todo lo que se puede empezar ya,
porque no depende de la consigna oficial que todavía no salió) y
fases posteriores ordenadas por **dependencia técnica**, no por orden
de mención en las charlas de diseño. Cada fase indica qué archivos
toca, qué depende de qué, y el riesgo real de implementación.

Al final hay una sección de **qué recortar primero** si el tiempo
aprieta — pensada para no tener que decidirlo en caliente el 26 de
agosto.

---

## Fase 0 — Arrancable ya (antes del 10 de agosto)

No depende de la consigna oficial. Es además la base técnica de todo
lo que sigue, así que conviene hacerla primero sí o sí.

### 0.1. Performance + equilibrio de comentarios (feedback de Ronda 1)
- Perfilar los métodos `_dibujar_*` de `juego.py` (son los que corren
  todos los frames) para confirmar si el cuello de botella real está
  ahí o en la generación con reintentos de `_generar_automatico`.
- Pasada de comentarios en `juego.py`, que es el archivo con menos
  densidad de comentario línea a línea comparado con `nivel.py`,
  `guardado.py`, `mapa.py` y `sprites.py`.
- **Riesgo:** bajo. **Bloquea a:** nada, pero conviene cerrarlo antes
  de que el archivo crezca más con las mecánicas nuevas.

### 0.2. Sistema base de "objeto empujable" (caja)
- Estructura de datos para posiciones de cajas + lógica de colisión
  en `_intentar_mover` (reutilizando el mismo patrón que ya existe
  para paredes).
- **Riesgo:** bajo. **Bloquea a:** caja+placa (1.2), puente temporal,
  sensor de peso, cinta transportadora — todo lo demás depende de que
  esto exista primero.

### 0.3. Extender `mapa.py` para nuevos objetos de Tiled
- Agregar el parseo de: caja, celda de pozo, sensor de peso, celda de
  control + bloque de cinta transportadora, marcador de interruptor
  compartido — siguiendo el mismo patrón que ya usan para
  `puerta_llave` / `placa`.
- **Riesgo:** bajo-medio (es repetitivo, pero cada objeto nuevo es una
  fuente más de bugs de parseo). **Bloquea a:** todo el contenido de
  Modo Viaje y Multijugador, porque sin esto los mapas de Tiled no
  pueden usar las mecánicas nuevas.

### 0.4. Reestructurar `menu.py` a 6 entradas
- Viaje / Infinito / Multijugador / Tutorial / Inventario-Bestiario /
  Controles, reemplazando el esquema actual de
  Iniciar-partida/Controles/Dificultad.
- Al principio pueden ser pantallas "cascarón" (placeholder) para los
  modos que todavía no tienen contenido — lo importante acá es que la
  navegación ya funcione.
- **Riesgo:** medio (es un rediseño de UI grande, con hitbox de mouse
  y teclado para 6 opciones en vez de 3). **Bloquea a:** todo lo
  demás, porque cada modo nuevo necesita un punto de entrada.

### 0.5. Extender `guardado.py`
- Sumar: highscore doble de Infinito (puntaje total + nivel más alto),
  personajes desbloqueados, progreso de Viaje.
- **Riesgo:** bajo. **Bloquea a:** Inventario/Bestiario (necesita leer
  qué está desbloqueado) e Infinito (necesita el highscore doble).

---

## Fase 1 — Modo Infinito

- Sacar la selección manual de dificultad, dejar que escale sola cada
  10 niveles hasta tope "difícil".
- Conectar el highscore doble (0.5) a la pantalla de fin de partida.
- **Depende de:** 0.4, 0.5. **Riesgo:** bajo — es mayormente reutilizar
  `nivel.py` tal cual está, solo cambia quién decide la dificultad
  (el sistema, no el jugador).
- **Por qué primero:** es el modo más simple de los tres nuevos
  (Infinito / Viaje / Multijugador) porque no toca mapas de Tiled ni
  personajes ni redes. Sirve como "primer modo completo" para validar
  que el menú nuevo (0.4) funciona de punta a punta.

---

## Fase 2 — Mecánicas nuevas (sobre mapas Tiled de prueba)

Antes de meterlas en niveles reales de Viaje/Multijugador, conviene
probarlas en un mapa de Tiled de test, sin narrativa ni arte final.

1. Caja + placa combinada (2 en el documento de MDA)
2. Cinta transportadora, variante click (7b)
3. Puente temporal con caja (4)
4. Sensor de peso (5)
5. Interruptor compartido (6) — **este último requiere que el
   Multijugador (Fase 4) ya tenga aunque sea la sincronización básica
   de "dónde está parado cada jugador", así que en la práctica se
   implementa en paralelo con Fase 4, no antes.**

- **Depende de:** 0.2, 0.3. **Riesgo:** bajo-medio, escala con la
  cantidad de mecánicas — cada una es chica pero suman.

---

## Fase 2.5 — Animaciones nuevas

Surge de pensar en más pulido visual. Técnicamente no es riesgoso —
todo entra en uno de los dos patrones que ya existen en `juego.py`:
**loop** (como llave/portal/teleporte, timer compartido) o **de un
solo sentido** (como las puertas, estado propio por instancia). El
costo real no es de performance en juego (`_cargar_assets` corre una
sola vez al arrancar), sino de **contenido**: cada animación nueva es
un spritesheet más que alguien tiene que dibujar.

Priorización sugerida, de mayor a menor valor por esfuerzo:

1. **Idle/Walk de los personajes nuevos** (UAIBOTA, UAIBOTINA,
   UAIBOTINO) — no es opcional en rigor: si se van a poder elegir y
   jugar con ellos (Viaje, Multijugador), necesitan moverse en
   pantalla. Mismo molde que ya tiene UAIBOT (128x128, 6 frames).
2. **Idle loop en los objetos interactivos nuevos** (caja al
   asentarse, celda de control de la cinta transportadora al
   activarse, placa del interruptor compartido al pisarse) — le da
   al jugador **feedback visual de estado**, no es solo decorativo.
   Mismo patrón que la llave/portal/teleporte.
3. **Idle decorativo en obstáculos de Tiled** (paredes con un sutil
   balanceo, césped con detalle en loop, etc.) — la idea que surgió
   ahora. Es la que más entra en el criterio de "estética/innovación"
   del jurado por menor costo de código, pero es puramente decorativa:
   el juego funciona igual sin ella. **Primera candidata a recortar si
   falta tiempo**, junto con la variante 7a de la cinta transportadora.

- **Depende de:** el molde de animación ya existe (nada que
  desbloquear técnicamente); depende de **contenido/arte**, no de
  otra fase de código.
- **Riesgo:** bajo en código, variable en tiempo según cuántos sprites
  haya que conseguir o encargar.

---

- Niveles fijos con mapas Tiled ya usando las mecánicas de Fase 2.
- Desbloqueo de personajes (UAIBOTA, UAIBOTINA, UAIBOTINO).
- **Bloqueador real:** las habilidades de cada personaje todavía no
  están definidas. Esto es una decisión de diseño, no de código —
  conviene cerrarla antes de llegar a esta fase para no frenar acá.
- **Depende de:** Fase 2, 0.5. **Riesgo:** medio — depende de cuántos
  niveles Tiled haya que diseñar a mano (tiempo de contenido, no solo
  de código).

---

## Fase 4 — Modo Multijugador

La pieza de mayor riesgo técnico del plan, por ser la primera vez que
el equipo encara redes. Conviene reservarle más margen del que parece
necesitar en el papel.

1. **Descubrimiento LAN** (UDP broadcast) + lista de partidas.
2. **Conexión TCP** host-autoritativo + intercambio de inputs.
3. **Selección de personaje compartida** (mismo mecanismo de mensajes
   que el punto 2, aplicado a un estado más simple).
4. **Objeto recolectable cooperativo** (uno por nivel).
5. **Interruptor compartido** (mecánica 6 de Fase 2, en paralelo).

- **Depende de:** 0.4, Fase 3 (reutiliza mapas/personajes ya armados).
- **Riesgo:** alto. Es la fase que más fácil se puede desbordar en
  tiempo — dejar margen extra en el cronograma para esta.

---

## Fase 5 — Inventario / Bestiario

- Submenú con personajes (historia + habilidad), donaciones (Viaje),
  objetos (Multijugador).
- **Depende de:** Fase 3 y Fase 4 completas o casi (necesita contenido
  real para mostrar, si no queda una pantalla vacía).
- **Riesgo:** bajo. Es más trabajo de UI/texto que de lógica nueva.

---

## Qué recortar primero si el tiempo aprieta

En este orden (lo de más abajo se sacrifica primero):

1. **Idle decorativo en obstáculos de Tiled** y **cinta transportadora
   variante 7a** (mantener presionado) — ninguna de las dos toca la
   jugabilidad central, son puro pulido/variedad.
2. **Sensor de peso (5)** y **puente temporal (4)** — son variantes
   de la caja+placa, no mecánicas centrales. El juego funciona sin
   ellas.
3. **Interruptor compartido (6)** — si el Multijugador (Fase 4) ya
   está ajustado de tiempo, esta mecánica es la primera candidata a
   caer dentro de esa fase (el modo sigue funcionando solo con el
   objeto recolectable cooperativo).
4. **Cantidad de niveles de Modo Viaje** — reducir la cantidad de
   niveles diseñados a mano es más seguro que sacar el modo entero,
   porque ahí vive el desbloqueo de personajes que después usa
   Inventario/Bestiario.
5. **Modo Multijugador completo** — es la última opción, no la
   primera: es la fase de mayor riesgo pero también la que más
   diferencia respecto a otros equipos (ustedes ya notaron que años
   anteriores metieron "trabajo en equipo" en Ronda 2, así que tiene
   peso para el jurado). Si hay que cortar por tiempo, mejor una
   versión reducida (menos objetos, sin interruptor compartido) que
   sacarlo entero.

---

*Documento vivo — se ajusta cuando salga la consigna oficial el 10 de
agosto y cuando se cierre el diseño de personajes.*
