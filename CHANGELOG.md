# Changelog — UAIBOT (OFIRCA 2026)

Registro de versiones del proyecto.

## [1.0] — Código base

- Reimplementación en `arcade` del juego de referencia que facilitó la
  organización (originalmente hecho con `pygame`).
- Punto de partida: escenario en grilla, panel lateral con misión y
  controles, movimiento básico de UAIBOT.

## [1.1] — Consignas obligatorias completas

- Cumplimiento de las 7 consignas del desafío: contador de pasos,
  imagen en la celda del merendero, sonido al moverse, bloqueo de
  camino ya recorrido, 4 paredes marrones, reinicio con tecla R en
  cualquier momento, animación al ganar.
- Incluye subversiones de parches sobre esta base (fixes y ajustes
  menores no versionados individualmente en este changelog).

## [1.2] — Extras grandes: sistemas y dificultad

- Generación procedural de mapas con validación de camino garantizado
  (BFS).
- Sistema de dificultad (fácil / medio / difícil).
- Límite de pasos en dificultades media y difícil.
- Elementos visuales adicionales dibujados en esta etapa (base para lo
  que en 1.3 se conecta a lógica de juego real).
- Incluye subversiones de parches sobre esta base.

## [1.3] — Versión entregada

- Incorporación definitiva de las mecánicas jugables (más allá de lo
  visual): hielo, teletransporte vinculado, llave + puertas con llave,
  placas de presión + puertas con placa.
- Menú principal gráfico con fondo ilustrado y navegación por
  teclado y mouse.
- Animaciones: UAIBOT (Idle/Walk), llave/portal/teleporte (idle en
  loop), puertas con llave y con placa (apertura de un sentido).
- Soporte de mapas externos diseñados en Tiled (.tmx) para dificultad
  media/difícil, con cámara que sigue al jugador.
- Guardado persistente de highscore, controles y dificultad.
- Sin subversiones de parches registradas por límite de tiempo antes
  de la entrega.

## [1.4] — Ronda 2: Tutorial e Infinito

Primera versión que responde a la consigna oficial de la Ronda 2
(publicada el 10 de agosto). El juego pasa a tener modos separados en
vez de una sola partida: **Tutorial** concentra las consignas del
desafío, e **Infinito** muestra el juego completo con progresión.

### Modo Tutorial (`tutorial.py`, archivo nuevo)

Nivel único, fijo y autocontenido —sin dificultad, sin mapas de Tiled y
sin progresión de niveles— donde se cumplen las 13 consignas graduadas
de OFIRCA: las 7 obligatorias de la Ronda 1 más las 6 nuevas de la
Ronda 2:

- Cronómetro en pantalla, que se muestra al terminar el nivel.
- Cuatro personajes jugables (UAIBOT, UAIBOTA, UAIBOTINA, UAIBOTINO)
  alternables con la tecla C, cada uno con un cupo propio de 8 pasos.
  El cambio es automático al agotarse el cupo, y si los cuatro se
  quedan sin movimientos el nivel se reinicia.
- Celdas de comida, dibujadas como hexágonos, de recolección
  obligatoria: no se puede completar el nivel si falta alguna.
- Celdas de sillas de ruedas, dibujadas como triángulos, que se
  recolectan pasando por sus lados una cantidad exacta de veces; la
  celda avisa si se pasó de más y el nivel no se puede completar.
- Ingreso del nombre del jugador al ganar, guardado junto con el
  tiempo en `puntajes_tutorial.txt`.
- Deshacer con la tecla Z (movimientos, recolecciones y cambios de
  personaje), resuelto con una pila de estados del nivel.

El sendero recorrido es compartido por los cuatro personajes, y el
fondo y las paredes se dibujan en color plano para que los elementos
de las consignas se distingan con claridad.

### Modo Infinito (`juego.py`)

- Se elimina la selección manual de dificultad: ahora escala sola cada
  10 niveles (fácil, medio, difícil) con tope en difícil.
- Se elimina el techo del nivel 10: la progresión sigue indefinidamente
  hasta que el jugador pierde o vuelve al menú.
- Generación siempre procedural, en todas las dificultades: los mapas
  de Tiled quedan reservados para el Modo Viaje.
- Highscore doble (puntaje total y nivel más alto alcanzado), visible
  en la pantalla de fin de partida.

### Cambios de base

- Menú principal reestructurado a seis entradas (Viaje, Infinito,
  Multijugador, Tutorial, Inventario/Bestiario, Controles), con
  pantallas "Próximamente" para los modos todavía no implementados.
- Rendimiento: las capas de fondo, paredes, hielo y sendero pasan de
  dibujarse celda por celda en cada cuadro a agruparse en
  `arcade.SpriteList`, con una sola llamada de dibujo por capa.
- `guardado.py` extendido con highscore de Infinito, personajes
  desbloqueados y progreso de Viaje, completando los valores que
  falten al leer guardados de versiones anteriores.
- `mapa.py` extendido para reconocer objetos nuevos de Tiled (cajas,
  pozos, cinta transportadora e interruptores compartidos), como base
  para el Modo Viaje.
- Corrección: la ubicación de la llave dividía por `11 - nivel`,
  fórmula que asumía un máximo de 10 niveles y que fallaba al llegar
  el Modo Infinito a niveles más altos.

## [1.5] — Modo Viaje

Se suma la campaña del juego, el tercer modo jugable. Con esto los mapas
diseñados a mano en Tiled vuelven a tener un modo donde jugarse: los 10
de dificultad media son la campaña de Viaje, y los 10 de dificultad
difícil quedan reservados para el Modo Multijugador.

### Modo Viaje (`viaje.py`, archivo nuevo)

- Campaña de 10 niveles fijos, diseñados a mano en Tiled, con final: al
  completar el último se muestra una pantalla de cierre con el tiempo
  total y el puntaje, en vez de seguir de largo como el Modo Infinito.
- Desbloqueo de los personajes de la familia de UAIBOT a medida que se
  avanza: UAIBOTINO al superar el nivel 2, UAIBOTA en el 5 y UAIBOTINA
  en el 8, con aviso en pantalla y guardado persistente.
- Cronómetro de la partida completa: acumula entre niveles y se detiene
  al terminar la campaña.
- Sin límite de pasos, a diferencia del Modo Infinito: la campaña está
  pensada para recorrerse y explorarse, no como prueba de eficiencia.

### Reorganización interna

`Viaje` hereda de `Juego` para reutilizar todo el motor que ya
compartían: movimiento en grilla, colisiones, sendero, cámara para mapas
más anchos que la pantalla, animaciones y panel lateral. Para eso se
extrajeron cuatro puntos de extensión en `juego.py` —de dónde salen los
datos del nivel, si hay límite de pasos, qué pasa al completar un nivel
y qué se persiste—, cada uno con el comportamiento del Modo Infinito
como implementación por defecto. El Modo Infinito no cambia en nada.

### Correcciones

- El cálculo del recorrido mínimo recorría la grilla con las medidas de
  los mapas procedurales (14×10), pero los mapas de Tiled son de 28×10:
  la búsqueda nunca pasaba de la mitad del mapa y daba el portal por
  inalcanzable. Ahora recibe el tamaño real del mapa.
- Ese mismo cálculo seguía fallando en los mapas con puertas, porque las
  puertas empiezan cerradas y cuentan como pared. Ahora se las descuenta
  al estimar el recorrido, asumiendo que el jugador las va a abrir con
  la llave o la placa de presión.
- En el panel lateral, el bloque de controles se superponía con el
  recordatorio del pie.
