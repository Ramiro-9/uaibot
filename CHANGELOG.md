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

## [1.3] — Versión entregada en la 1ra ronda

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

## [1.5.1] — Personajes jugables y deshacer en Viaje

Parche sobre la 1.5. Hasta acá, desbloquear un personaje en la campaña
no servía de nada: aparecía el aviso, quedaba guardado, y no se podía
jugar con él en ningún lado. Ahora el desbloqueo tiene consecuencia.

- **Cambio de personaje con la tecla C en Modo Viaje**, limitado a los
  que ya se desbloquearon: al empezar solo está UAIBOT, y se van sumando
  a medida que se superan los niveles 2, 5 y 8. A diferencia de
  Tutorial, acá no hay cupo de pasos por personaje. El panel muestra
  quién está activo, y el sprite se tiñe con su color.
- **Deshacer con la tecla Z en Modo Viaje**, que revierte movimientos,
  cambios de personaje y la recolección de la llave —incluida la
  apertura de las puertas que esa llave provoca, que vuelven a cerrarse.
  El historial se vacía en cada nivel. El Modo Infinito no lo tiene a
  propósito: poder deshacer un paso vaciaría de sentido su límite de
  pasos y su puntaje por eficiencia.
- La lista de personajes pasa a llamarse `PERSONAJES_FAMILIA` en vez de
  `PERSONAJES_TUTORIAL`, porque ya la usan dos modos con reglas
  distintas.
- Los archivos `.pyc` de `__pycache__` dejan de estar versionados:
  estaban trackeados desde antes de que existiera la regla en
  `.gitignore`, que no afecta a lo ya trackeado.

### Correcciones

- Al empujar una caja hacia una celda ya recorrida, la caja se movía
  igual pero el personaje no, dejando el empujón hecho a medias. Ahora
  la comprobación del sendero va antes del empujón. Solo afectaba a
  mapas con cajas, que todavía no hay ninguno.
- El indicador de llave se superponía con el bloque de personaje en el
  panel de Viaje.

## [1.5.2] — Multijugador, habilidades, Bestiario, Ajustes y arte propio

Cierre de las Fases 4 y 5 del plan de trabajo, más el reemplazo del arte
prestado por arte propio. Es la versión más grande de la Ronda 2: suma el
cuarto modo jugable, le da a cada personaje una razón mecánica para
existir, y deja de dibujar a los cuatro hermanos con el mismo sprite
teñido de distinto color.

### Modo Multijugador (`multijugador.py` y `red.py`, archivos nuevos)

- Cooperativo de dos jugadores por red local, sobre los 10 mapas de
  dificultad difícil, que hasta acá estaban diseñados pero sin ningún
  modo donde jugarse.
- Diez objetos coleccionables repartidos por los mapas, que son los que
  después se ven en el Bestiario.
- `red.py` envuelve el socket con un hilo de lectura de fondo. El motivo
  es que Arcade dibuja en un solo hilo: si se leyera del socket en el
  bucle de dibujo, cada espera de mensaje congelaría la pantalla.

### Habilidades (`habilidades.py`, archivo nuevo)

Una habilidad por personaje, pensadas como tecnología asistiva —cada una
resuelve una barrera del escenario en vez de dar ventaja de combate:

- **Carga** (UAIBOT): empuja cajas.
- **Rampa** (UAIBOTINO): vuelve transitable una celda ya recorrida.
- **Guía** (UAIBOTINA): señaliza el camino al merendero.
- **Alcance** (UAIBOTA): toma cosas de una celda vecina sin moverse.

La rampa es la única con tope de usos, porque es la única que rompe la
regla de no volver a pisar el camino: sin límite, desactivaría de hecho
una de las consignas del desafío.

### Inventario / Bestiario y Ajustes

- **Bestiario**: la familia con sus habilidades y los diez objetos del
  Multijugador. Lo que todavía no se consiguió se muestra como silueta,
  así se ve que existe sin revelar qué es.
- **Ajustes**: controles y volúmenes de música, persistidos en el
  guardado. El volumen del menú se aplica en vivo sobre el player que ya
  está sonando, en vez de esperar a la próxima reproducción.

### Arte propio

- Hojas **Idle/Walk propias para los cuatro personajes**, que hasta acá
  compartían el spritesheet de UAIBOT con un tinte encima. Cada uno lleva
  el rasgo de su habilidad, y UAIBOT sus dos antenas con orbes verdes.
  Los personajes sin hoja propia siguen cayendo al sprite compartido con
  tinte, así que el sistema viejo sigue funcionando de respaldo.
- Sprite de **caja** y las **cuatro huellas** rehechas, todas cuadradas
  de 64×64: el dibujado estira el sprite al tamaño de la celda sin
  respetar la proporción, y como las huellas viejas tenían cada una una
  forma distinta, cada una se deformaba de manera diferente.
- Íconos del panel lateral (habilidades, llave, pasos, reloj), sexto
  ribbon de botón y marco de submenú con nine-patch.
- Diez objetos coleccionables y tres donaciones.
- **Ilustración nueva del menú**, con la familia y el merendero pintados
  dentro de la escena. Antes el fondo mostraba solo a UAIBOT.

### Correcciones

- El corte de ribbons de `botones.png` usaba 1563 de alto cuando la
  imagen mide 1536: eso corría todos los cortes 27px y hacía que el
  primer ribbon leyera fuera de la imagen.
- `Viaje` definía `_dibujar_uaibot` dos veces, y la segunda tapaba a la
  que aplicaba el tinte del personaje. Resultado: en la campaña el tinte
  nunca se veía, aunque el cambio de personaje con C sí funcionaba.
- `constantes.py` pedía `huella_abajo.png` pero el archivo se llamaba
  `huellas_abajo.png`, en plural, así que todas las huellas hacia abajo
  se dibujaban con el color de respaldo en vez de con su arte.
- La cantidad de frames ahora sale del ancho de cada hoja, en vez de una
  constante `TOTAL_FRAMES = 6` duplicada en `juego.py` y `tutorial.py`
  que forzaba exactamente seis poses. Así conviven hojas de cuatro y de
  seis frames.
- `guardado.json` sale del control de versiones: es estado local del
  jugador y ya estaba listado en `.gitignore`, pero seguía trackeado de
  antes de esa regla.

### Limpieza

- Se descartan las animaciones del fondo del menú (pájaros, nubes y
  luciérnagas). La idea era animar el fondo por capas, pero las capas
  nunca llegaron a leerse consistentes con la ilustración, así que el
  menú queda con el fondo pintado y quieto.

## [1.6] — Version entregada para la ronda 2

Ronda de cierre del Multijugador: se prueba lo que nunca se había podido probar, se tapan los agujeros que esas pruebas dejaron a la vista, y se completan las partes del modo que estaban a medio terminar.

### Corrección: el juego iba lento

Los tres modos corrían a 13-22 FPS contra 117 del menú. La causa: crear un `arcade.Text` dentro del dibujo cuesta 43x más que reusar uno existente (14,2 ms vs 0,3 ms), y se hacía en cada cuadro.

- **Panel lateral**: armaba el título de cada sección en cada cuadro; ahora se crea una sola vez al acomodar la sección.
- **Sillas del Tutorial**: 2 textos nuevos por cuadro se llevaban 15 de los 24 ms del modo.
- **Bestiario y sala del Multijugador**: creaban 11 y 7 textos por cuadro. Se agregó `ui.etiqueta()`, que guarda cada texto por el rol que cumple y solo le cambia el valor.
- Resultado: 0 textos creados por cuadro en las seis pantallas (se midió así, y no en FPS, porque las creaciones son deterministas y el tiempo variaba entre corridas). Los carteles de fin de partida siguen armando texto al vuelo: son puntuales y no se nota.

### Reorganización de archivos

La raíz tenía 19 `.py` sueltos mezclando juego, pruebas y generadores de arte.

- Pruebas → `pruebas/`, generadores de arte → `generacion/`. Quedan 15 módulos en la raíz.
- `assets/` (59 archivos sueltos) se divide en `assets/imagenes/` (49) y `assets/audio/` (5). Los 5 `tileset_*.png` quedan sueltos a propósito: los `.tsx` de Tiled los referencian por ruta relativa, y moverlos arriesgaría los 20 mapas.
- Pruebas y generadores resuelven sus rutas solos, sin depender de desde dónde se los ejecute.
- README actualizado: faltaban `viaje.py`, `tutorial.py`, `multijugador.py`, `red.py`, `habilidades.py`, `panel.py` y `ui.py`.

### Cuarta donación en Modo Viaje: silla de ruedas

Se suma a comida, libros y juguetes. Ya existía en el Tutorial como mecánica (esquivarla); acá se recoge pisándola, igual que las otras tres. No requirió lógica nueva, solo sumar el sprite a `constantes.py` (`tipo = sillas` en Tiled). El sprite se rehizo con PixelLab forzando la paleta de las otras tres donaciones (luminancia 39 → 96); prompts anotados en `generacion/generar_donaciones.py`.

### Submenús con interfaz unificada (`ui.py`, nuevo)

Antes solo Ajustes tenía cuadro con marco, título y pie; Bestiario y sala Multijugador eran texto suelto con márgenes repetidos a mano.

- Cuadro, encabezado, pie y solapas quedan en un solo archivo; Ajustes también pasa a usarlos.
- Bestiario: personajes y objetos dentro del cuadro, separados por una línea de la ficha del seleccionado; solapas con subrayado para distinguirse mejor.
- Sala Multijugador: sus 5 pantallas comparten cuadro y medidas; la IP a dictar va en recuadro propio.
- La opción elegida se marca con banda de fondo (sala y Ajustes).

### Corrección: texto largo cortado a mitad de palabra

El wrap automático de Arcade cambiaba de fuente en vocales acentuadas y cortaba justo ahí. Ahora el corte se calcula midiendo cada línea.

### Panel lateral por secciones (`panel.py`, nuevo)

Cada texto llevaba su Y escrita a mano, causando choques entre bloques (ya registrados en 1.5).

- Cada modo declara qué secciones tiene y en qué orden; las posiciones se calculan solas. Lo usan Infinito, Viaje, Multijugador y Tutorial.
- El espacio sobrante se reparte entre separaciones (con tope); si no entra, se aprieta hasta un piso o avisa por consola en vez de cortar texto.
- Cada sección lleva una regla fina de separación visual.
- Para hacer entrar la campaña (faltaban 125px): se sacó el recordatorio de pie duplicado, la llave perdió su encabezado propio, y misión/controles dejan de tener saltos de línea a mano.

### Los personajes miran hacia donde caminaron

El arte mira a la derecha por defecto; antes no se espejaba nunca.

- Caminar a la izquierda espeja la textura (sin hojas nuevas); arriba/abajo conservan la orientación previa.
- Vale en los 4 modos; en Multijugador viaja con el estado del invitado (que no resuelve sus propios movimientos).
- El deshacer de Viaje también revierte la orientación.
- Texturas espejadas cacheadas por `cache_name` (antes se reconstruían cada cuadro).

### Pantalla de cierre del Multijugador

Al completar el nivel 10, `juego_completado` se prendía pero nadie lo dibujaba.

- Nueva pantalla con tiempo total, pasos y puntaje del equipo (acumulados nivel a nivel); conteo de objetos solo si el recorrido tenía alguno.
- R reinicia desde el nivel 1, pero solo el anfitrión puede (evita que cada uno reinicie mapas distintos); el invitado ve un pie distinto.
- Cronómetro se congela entre niveles, al terminar y si se corta la conexión.

### Selección de personaje en el Multijugador

Antes los jugadores eran siempre UAIBOT y UAIBOTA fijos.

- Nueva sala de elección con los 4 personajes, su habilidad y qué hace.
- Si eligen el mismo, el anfitrión se lo queda y al invitado se le asigna otro (se resuelve recién cuando están los dos conectados).
- La elección no depende de los desbloqueos de Viaje.
- ESC en la elección vuelve un paso atrás, no al menú.

### Pruebas automáticas

Primeras pruebas del proyecto; antes el Multijugador solo se probaba a mano con dos personas.

- `pruebas/pruebas_red.py`: capa de red sola (conexión, mensajes cortados/pegados, basura en el flujo, caída de cada lado, IP mal tipeada, puerto ocupado).
- `pruebas/pruebas_multijugador.py`: anfitrión e invitado reales conectados por socket — arranque, movimiento, sendero compartido, llave, cambio de nivel, cierre, reinicio, desconexión a mitad de partida, sincronía ante pedidos imposibles y puntaje calculado igual en ambos lados.
- Se corren por separado a propósito, para aislar si una falla es de red o de lógica del juego.

### Correcciones

- **Puerto compartido en Windows**: `SO_REUSEADDR` en Windows permite robarle el puerto a un socket en uso (no pasa en Linux/Mac). Ahora se usa `SO_EXCLUSIVEADDRUSE` en Windows y se avisa si el puerto está ocupado.
- **Highscore del Multijugador se guardaba de más**: `_completar_nivel` llamaba a `actualizar_highscore` por fuera del método pensado para evitarlo. Se agrega la costura `_persiste_highscore` que el Multijugador cierra; solo quedan guardados los objetos conseguidos.
- **`Moverse.wav`/`moverse.wav`**: el mismatch de mayúsculas rompía el juego en Linux/Mac (Windows lo toleraba). Unificado a `Moverse.wav`.

### Limpieza

- Se borran `nubes_anim.png`, `pajaros_anim.png`, `luciernagas_anim.png` (animaciones descartadas del fondo del menú) y `muro.png` (sin referencias desde antes de Ronda 2).