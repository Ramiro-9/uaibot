# UAIBOT — Mecánicas nuevas para Ronda 2 (marco MDA)

Documento de trabajo para pensar qué mecánicas incorporar en los mapas
exportados de Tiled (**Modo Viaje** y **Modo Multijugador**), analizadas
con el marco **MDA** (Mecánica → Dinámica → Estética).

> **Decisión tomada:** se incorporan todas las mecánicas de este
> documento **excepto la #3 (corriente/viento direccional)**, que queda
> descartada.

> Recordatorio de alcance: estas mecánicas viven **solo en mapas Tiled**.
> El Modo Infinito sigue siendo puro (paredes, hielo, teleporte + BFS),
> sin tocar `nivel.py` ni la validación de camino garantizado.

---

## Cómo leer la tabla

- **Mecánica**: la regla concreta que se agrega al sistema.
- **Dinámica**: el comportamiento de juego que emerge cuando el jugador
  interactúa con esa regla (lo que el jugador *hace* y *piensa*).
- **Estética**: la sensación o tipo de experiencia que le deja al
  jugador (lo que el jugador *siente*).
- **Reutiliza**: qué sistema ya existente en el código se aprovecha,
  para minimizar código nuevo y mantener la performance.

---

## 1. Caja empujable *(ya acordada — base de todo lo demás)*

| MDA | Detalle |
|---|---|
| **Mecánica** | Un objeto en la celda que se desplaza una celda cuando UAIBOT se mueve contra él. Se traba si detrás hay pared, otra caja, o el borde del mapa. |
| **Dinámica** | El jugador tiene que planificar la secuencia de empujones antes de moverse, porque un empujón mal calculado puede volver el puzzle irresoluble sin reiniciar. |
| **Estética** | Pasa de "explorar un camino" (Ronda 1) a "resolver un rompecabezas espacial" — más cerebral, menos de reflejos. |
| **Reutiliza** | Sistema de colisión contra `self.paredes` ya existente en `_intentar_mover`; se suma un set nuevo de posiciones de cajas con la misma lógica de choque. |

---

## 2. Caja + placa de presión combinadas

| MDA | Detalle |
|---|---|
| **Mecánica** | Las placas de presión (que ya tenés) también se activan si una **caja** queda encima, no solo si pisa UAIBOT. |
| **Dinámica** | Aparece el puzzle de "empujar la caja hasta la placa para abrir la puerta, porque yo necesito seguir de largo" — separa quién activa el mecanismo de quién lo atraviesa. |
| **Estética** | Sensación de mecanismo/ingeniería resuelta, no solo de esquivar obstáculos. |
| **Reutiliza** | El sistema de `placas` + `puertas_placa` que ya está armado con animación de apertura; solo se agrega la verificación de "hay una caja en esta celda" además de "está UAIBOT". |

---

## 3. ~~Corriente / viento direccional~~ *(descartada)*

| MDA | Detalle |
|---|---|
| **Mecánica** | Celdas que empujan a UAIBOT (o a una caja) siempre hacia una dirección fija definida en el mapa, en vez de continuar en la dirección en que caminaste (como el hielo). |
| **Dinámica** | Fuerza rutas de entrada/salida específicas hacia una zona — el jugador tiene que entrar por el lado correcto o la corriente lo saca de nuevo. |
| **Estética** | Sensación de "el escenario tiene voluntad propia", suma variedad visual (ríos, viento) ligada al tema de inclusión/entorno. |
| **Reutiliza** | Mismo patrón de "movimiento forzado después del input" que ya existe para el hielo en `_intentar_mover`; cambia solo qué dirección se aplica. |

---

## 4. Puente temporal con caja (pozo tapable)

| MDA | Detalle |
|---|---|
| **Mecánica** | Una celda de "pozo" intransitable hasta que se empuja una caja dentro; la caja tapa el pozo y se vuelve piso cruzable de forma permanente. |
| **Dinámica** | El jugador debe decidir **qué caja sacrificar** como puente, sabiendo que ya no podrá usarla para otro puzzle del mismo nivel — genera tensión de recursos limitados. |
| **Estética** | Sensación de sacrificio/costo de oportunidad, un poco más avanzada — buena para los últimos niveles del Modo Viaje. |
| **Reutiliza** | Extensión directa de la mecánica de caja (#1): el pozo es un tipo más de "pared condicional" similar a como ya tratás puertas cerradas. |

---

## 5. Sensor de peso (puerta que necesita algo "pesado")

| MDA | Detalle |
|---|---|
| **Mecánica** | Variante de puerta con placa que solo se abre si detecta una caja encima (no alcanza con que pise UAIBOT solo). |
| **Dinámica** | Es un caso particular de #2, pero con lectura narrativa: "esta rampa/mecanismo necesita algo con peso para activarse". |
| **Estética** | Refuerza el eje temático de inclusión social si se presenta como una rampa de acceso o mecanismo asistido, no como un puzzle abstracto. |
| **Reutiliza** | Mismo código que #2; es más una decisión de diseño/arte que una mecánica técnica distinta. |

---

## 6. Interruptor compartido *(pensada para Modo Multijugador)*

| MDA | Detalle |
|---|---|
| **Mecánica** | Una puerta que solo se abre si **los dos jugadores** están parados sobre sus respectivas placas al mismo tiempo. |
| **Dinámica** | Obliga a coordinación explícita por voz/chat entre los dos jugadores ("quedate ahí, yo sigo") — encaja con el eje de "trabajo en equipo" que ya mencionaste para el Multijugador. |
| **Estética** | Cooperación real, no solo "cada uno junta lo suyo" como el objeto recolectable que ya definieron — variedad de por qué cooperar. |
| **Reutiliza** | Mismo sistema de placas/puertas; la única diferencia es que ahora la condición de apertura depende del estado de **dos** entidades en vez de una. Requiere que el estado de "quién está en qué celda" viaje entre host y cliente, lo cual ya vas a tener resuelto por el netcode básico del modo multijugador. |

---

## 7. Cinta transportadora activada a distancia

UAIBOT se para en una celda de "control" y, al presionar una tecla, mueve
un bloque que está en **otro punto del mapa**, en una dirección fija.
A diferencia de la caja (#1), acá UAIBOT no empuja directamente: activa
el movimiento desde lejos. Se analiza en dos variantes de input, porque
cada una genera una dinámica distinta aunque la mecánica base sea la misma.

### 7a. Variante "mantener presionado"

| MDA | Detalle |
|---|---|
| **Mecánica** | Mientras se mantiene la tecla apretada, el bloque se mueve celda por celda de forma continua en su dirección fija hasta soltarla, chocar contra una pared, u otro bloque/caja. |
| **Dinámica** | El jugador tiene que calcular *cuánto tiempo* sostener la tecla para que el bloque quede exactamente donde lo necesita — parecido a "frenar a tiempo", más de timing y feedback visual claro que de cálculo exacto. |
| **Estética** | Sensación de control directo y en tiempo real, más cercana a la acción que al puzzle frío. |
| **Reutiliza** | El mismo patrón de `on_key_press`/`on_key_release` que ya usan para animación caminando/idle de UAIBOT; el bloque se mueve con la misma lógica de colisión contra `self.paredes` que ya existe. |

### 7b. Variante "un click, una celda"

| MDA | Detalle |
|---|---|
| **Mecánica** | Cada pulsación de la tecla mueve el bloque exactamente una celda, sin importar cuánto se mantenga apretada. |
| **Dinámica** | El jugador cuenta pasos exactos antes de actuar, igual que ya hace al mover a UAIBOT — es un puzzle de precisión y planificación, no de reflejos. |
| **Estética** | Coherente con la sensación general del juego (todo por celdas discretas, sin timing de por medio) — más fácil de razonar para un chico de nivel primario que la variante 7a. |
| **Reutiliza** | Igual que el movimiento de UAIBOT en `_intentar_mover`: un solo `on_key_press` mueve el bloque una celda, mismo patrón de verificación de choque. |

> **Decisión tomada:** se implementa la variante **7b (un click = una
> celda)**. La 7a (mantener presionado) queda para más adelante, solo
> si sobra tiempo.

---

Para no comprometer el tiempo (arranca 10 de agosto, entrega 27):

1. **Caja empujable (#1)** — imprescindible, es la base de todo lo demás.
2. **Caja + placa (#2)** — bajo costo (reutiliza casi todo), alto impacto en profundidad de puzzle.
3. **Cinta transportadora, variante click (#7b)** — mecánica nueva más distintiva, decidida como prioridad sobre la variante de mantener presionado.
4. **Interruptor compartido (#6)** — si el netcode básico ya anda bien, es la mecánica que más valor le da específicamente al Multijugador.
5. **Puente temporal (#4)** y **Sensor de peso (#5)** — dejarlas como "extra si sobra tiempo": son variantes de lo anterior, no mecánicas urgentes.
6. **Cinta transportadora, variante mantener presionado (#7a)** — solo si sobra tiempo después de todo lo demás.

---

*Documento vivo — actualizar a medida que se define el diseño de personajes
y se conozca la consigna oficial de la Ronda 2 (10 de agosto).*
