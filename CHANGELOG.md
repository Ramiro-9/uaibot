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

## [1.6] — En desarrollo

Ronda de cierre del Multijugador: se prueba lo que nunca se había podido
probar, se tapan los agujeros que esas pruebas dejaron a la vista, y se
completan las partes del modo que estaban a medio terminar.

### Corrección: el juego iba lento

Los tres modos corrían a **13-22 cuadros por segundo**, contra 117 del
menú. La causa era una sola, y estaba repartida por todo el proyecto:
**crear un `arcade.Text` dentro del dibujo**.

Medido en esta máquina, con el mismo texto y la misma fuente:

| operación | costo |
|---|---|
| crear un `arcade.Text` nuevo | **14,2 ms** |
| cambiarle el valor a uno existente | 3,7 ms |
| asignarle el valor que ya tenía | 0,3 ms |
| dibujar uno ya creado | 0,3 ms |

O sea que crear un texto cuesta **43 veces** más que dibujar uno guardado:
arma el layout del texto de cero cada vez. Como la pantalla se redibuja 60
veces por segundo, cada texto creado dentro del dibujo se pagaba entero en
cada cuadro.

- **El panel lateral** era el peor caso, y era culpa del rediseño por
  secciones de esta misma versión: armaba el `Text` del título de cada
  sección en cada cuadro. Solo el panel se llevaba casi todo el costo de
  dibujar. Ahora el título se crea al acomodar la sección y se reusa.
- **Los contadores de las sillas del Tutorial**: dos sillas, dos textos
  nuevos por cuadro, 15 ms de los 24 que tardaba el modo.
- **El Bestiario y la sala del Multijugador** creaban 11 y 7 textos por
  cuadro. Se agregó `ui.etiqueta()`, que guarda cada texto por el ROL que
  cumple en la pantalla —«el título del cuadro», «la tercera línea del
  párrafo»— y solo le cambia el valor cuando hace falta.

El resultado, contado sobre cuadros reales: **0 textos creados por cuadro
en las seis pantallas**. Se eligió esa medida y no los cuadros por segundo
porque el número de creaciones es determinista, mientras que el tiempo
variaba mucho entre corridas.

Los carteles de fin de partida siguen armando su texto al vuelo: se
dibujan en un estado puntual, con confeti encima, donde un cuadro de más
no se nota.

### Reorganización de archivos

La raíz tenía diecinueve `.py` sueltos, mezclando los módulos del juego
con las pruebas y con los scripts que generaron el arte. Leído de afuera
da impresión de desorden, aunque cada archivo sea chico.

- Las pruebas pasan a **`pruebas/`** y los generadores de arte a
  **`generacion/`**. En la raíz quedan solo los quince módulos que forman
  el juego.
- `assets/` tenía 59 archivos sueltos y mezclados; se parte en
  **`assets/imagenes/`** (49) y **`assets/audio/`** (5).
- **Los cinco `tileset_*.png` quedan sueltos en `assets/`** a propósito:
  los archivos `.tsx` de Tiled los buscan por ruta relativa
  (`../assets/tileset_fondo1.png`), así que moverlos obligaría a editar
  los seis tilesets y arriesgaría los 20 mapas.
- Las pruebas llevan un arranque que agrega la raíz al path de imports,
  así se pueden correr paradas en la raíz (`python pruebas/pruebas_red.py`)
  o entrando a la carpeta. Sin eso solo andarían como módulo.
- Los generadores escriben en `assets/` resolviendo la ruta desde su
  propia ubicación, no desde el directorio en el que se los ejecuta.
- El árbol de archivos del README estaba desactualizado —no listaba
  `viaje.py`, `tutorial.py`, `multijugador.py`, `red.py`, `habilidades.py`,
  `panel.py` ni `ui.py`—. Se rehízo agrupando por rol: vistas, lógica
  compartida, interfaz, recursos y lo que queda fuera del juego.

### Cuarta donación en Modo Viaje: la silla de ruedas

Hasta acá la campaña tenía tres tipos de donación —comida, libros y
juguetes—. Se suma la **silla de ruedas**, que ya aparecía en el Tutorial
pero como mecánica: ahí hay que pasarle por al lado sin pisarla. Como
donación se recoge pisándola, con exactamente las mismas reglas que las
otras tres: suma al contador del panel, entra en el total de la campaña y
el deshacer con Z la devuelve al mapa.

- No hizo falta lógica nueva: la recolección recorre `self.donaciones` sin
  mirar el tipo, así que alcanzó con sumar el sprite al diccionario de
  `constantes.py`. En Tiled se coloca con `tipo = sillas`.
- El sprite se generó con PixelLab. El primer intento salió con marco gris
  oscuro y quedaba como una mancha sobre el pasto —luminancia media 39
  contra 111 de las otras tres—, así que se rehízo pidiendo marco claro y
  **forzando la paleta de las tres donaciones existentes**, y quedó en 96.
  Los dos prompts están anotados en `generacion/generar_donaciones.py`.

### Submenús con la misma interfaz (`ui.py`, archivo nuevo)

Ajustes era el único submenú armado como interfaz: cuadro con marco
nine-patch, título y pie de ayuda. El Inventario / Bestiario y la sala del
Multijugador eran texto suelto sobre el fondo plano, y cada uno repetía a
mano su encabezado y su pie, con márgenes distintos.

- Las piezas compartidas —el cuadro con su marco, el encabezado de
  pantalla, el pie de ayuda y las solapas— quedan en un solo archivo, así
  todas las pantallas se ven iguales y una corrección alcanza a todas.
  Ajustes pasó a usarlas también, en vez de tener su propia copia.
- **Bestiario**: los personajes y los objetos van adentro del cuadro, con
  una línea que separa la grilla de la ficha del seleccionado. Las solapas
  llevan subrayado además del color, porque el dorado sobre gris no se
  distinguía de un vistazo y son la única pista de que ↑↓ cambia de
  sección.
- **Sala del Multijugador**: las cinco pantallas (menú, elección de
  personaje, espera, IP y error) usan el mismo cuadro, con su tamaño y su
  pie declarados en un solo lugar. La IP que hay que dictarle al otro
  jugador va en un recuadro propio: era el dato importante y se perdía
  entre el resto del texto.
- La opción elegida se marca con una banda de fondo, en el menú de la sala
  y en Ajustes.

### Corrección: el texto largo se cortaba a mitad de palabra

En el Bestiario se leía «compartimento m / ás seguro» y «al avanzar la c /
ampaña». El ajuste de línea automático de Arcade agrupa los glifos por
fuente, y cuando la fuente en uso no trae una vocal acentuada cae a otra
fuente para ese carácter: ese cambio abre un punto de corte justo antes
del acento. Ahora el corte se calcula midiendo cada línea, y nunca parte
una palabra.

### Panel lateral rearmado por secciones (`panel.py`, archivo nuevo)

Cada texto del panel llevaba su posición vertical escrita a mano
—`ALTO_VENTANA - 404`, `- 420`, `- 452`—, así que un modo que quería sumar
un bloque tenía que saber en qué píxel había dejado las cosas el modo del
que heredaba y correr a mano los de abajo. De ahí salieron los dos choques
que ya estaban registrados en la 1.5: la llave sobre el bloque de
personaje, y los controles sobre el recordatorio del pie.

- Ahora cada modo declara **qué secciones tiene y en qué orden**, y las
  posiciones se calculan solas. Insertar un bloque en el medio no obliga a
  tocar ningún otro.
- El mismo armador lo usan Infinito, Viaje, Multijugador y **Tutorial**,
  que no hereda de `Juego` pero tenía el mismo panel con los mismos
  números a mano.
- Las secciones se dibujan desde la misma lista que las acomoda, así que
  ya no puede pasar que un modo posicione un texto y se olvide de
  dibujarlo, o al revés.
- **El espacio sobrante se reparte** entre las separaciones, con un tope.
  Antes Infinito usaba el 34% del alto del panel, con un hueco de 88px en
  el medio mientras los títulos rozaban sus números.
- Si el contenido no entra, las separaciones **se aprietan** hasta un piso
  antes que dejar que un bloque se salga del panel, y si aun así no entra
  se avisa por consola en vez de dibujar texto cortado por abajo.
- Cada sección lleva una **regla fina** desde el título hasta el margen
  derecho, que agrupa visualmente sin sumar un solo texto más.
- Los textos se anclan por su borde superior (`anchor_y="top"`), que es lo
  que permite apilarlos sin cuentas: Arcade acomoda las líneas hacia
  abajo, multilínea incluido.

Para que la campaña entrara —le faltaban 125px— se recortó lo que
duplicaba información en vez de achicar la tipografía:

- **Se sacó el recordatorio del pie** (`R=nivel  N=inicio  ESC=menu`), que
  repetía palabra por palabra lo que ya dice el bloque CONTROLES.
- El indicador de llave pierde su encabezado propio: una línea con su
  ícono alcanza, y una sección entera para un sí/no gastaba 20px.
- Los textos de misión y controles dejan de traer saltos de línea a mano.
  Cortarlos a mano desperdiciaba media columna del panel y sumaba líneas
  de más; ahora se acomodan al ancho disponible.

### Los personajes miran hacia donde caminaron

El arte de la familia está dibujado de perfil **mirando hacia la
derecha** —la mochila queda del lado izquierdo del cuerpo y la cara del
derecho—, pero se dibujaba siempre igual, así que al caminar hacia la
izquierda el personaje avanzaba de espaldas.

- Caminar a la izquierda espeja la textura; a la derecha se dibuja tal
  cual. No hicieron falta hojas nuevas. Arrancan mirando a la derecha, que
  además es hacia donde suele quedar el portal.
- **Arriba y abajo conservan hacia dónde miraba**, en vez de girarlo al
  azar: no hay arte de frente ni de espaldas, y es lo que hacen los juegos
  de grilla con vista lateral.
- Vale en los cuatro modos. En Multijugador la orientación es de cada
  jugador —igual que «moviendose»— y **viaja con el estado**, porque el
  invitado no resuelve movimientos ni siquiera los suyos: sin eso se
  verían los dos mirando siempre para el mismo lado.
- El deshacer del Modo Viaje también revierte la orientación, o el
  personaje quedaba mirando hacia donde ya no había caminado.
- Las texturas espejadas se cachean por `cache_name`: `flip_left_right()`
  construye una textura nueva en cada llamada, y esto corre una vez por
  personaje por cuadro.

### Pantalla de cierre del Multijugador

Al completar el nivel 10 se prendía `juego_completado` en los dos lados y
**nadie lo dibujaba**: la pareja quedaba en la pantalla de victoria del
último nivel, tirando confeti, con ESC como única salida. Ahora hay un
cierre propio, con los totales del equipo:

- Tiempo total de la partida, pasos del equipo y puntaje. Los pasos y los
  objetos se acumulan nivel a nivel, porque `setup()` los pisa en cada
  mapa nuevo y al terminar el décimo ya no quedaría nada que mostrar.
- El conteo de objetos aparece solo si el recorrido tenía alguno, para no
  mostrar un «0/0» mientras los mapas todavía no los tienen.
- **R vuelve a empezar desde el nivel 1**, y solo lo puede hacer el
  anfitrión: si cada uno reiniciara por su lado terminarían jugando mapas
  distintos. Al invitado se le muestra un pie diferente, para no
  ofrecerle una tecla que no le va a hacer nada.
- El cronómetro se congela entre niveles, al terminar y si se corta la
  conexión.

### Selección de personaje en el Multijugador

Los dos jugadores eran siempre UAIBOT y UAIBOTA, fijos en el código, así
que UAIBOTINA y UAIBOTINO no se podían jugar en cooperativo y con ellos
quedaban afuera la Guía y el Alcance.

- La sala suma un paso de **elección**, con los cuatro de la familia, su
  habilidad y qué hace. La habilidad se muestra al elegir porque en
  cooperativo es lo que define qué aporta cada uno al equipo.
- **Si los dos eligen el mismo, el anfitrión se queda con el suyo y al
  invitado se le da otro.** El choque se resuelve ahí y no en la sala
  porque el invitado no puede saber con quién eligió jugar el anfitrión
  antes de conectarse: recién cuando están los dos hay con qué comparar.
- El par elegido viaja con el resto del estado, así que no hizo falta un
  mensaje de vuelta: el anfitrión sigue siendo la única autoridad también
  para esto.
- La elección no depende de los desbloqueos del Modo Viaje. Si dependiera,
  una instalación nueva tendría solo a UAIBOT y los dos jugadores no
  podrían siquiera tener personajes distintos.
- ESC en la elección vuelve un paso atrás, no al menú principal: es fácil
  entrar sin querer y perder la partida que se estaba por crear.

### Pruebas automáticas

Hasta acá el proyecto no tenía ninguna prueba automática, y el
Multijugador era la parte más difícil de probar a mano: hace falta que
dos personas se conecten para llegar a los casos raros. Ahora esos casos
se recorren solos, en segundos y en una sola computadora.

- **`pruebas/pruebas_red.py`** prueba la capa de red sola, sin abrir el juego:
  conexión, ida y vuelta de mensajes, mensajes que llegan pegados o
  cortados a la mitad (que es lo que este protocolo existe para
  resolver), basura en el medio del flujo, caída de cada lado, IP mal
  tipeada y puerto ocupado. Es la prueba a la que ya remitía el
  comentario de cabecera de `red.py`, que hasta ahora no existía.
- **`pruebas/pruebas_multijugador.py`** levanta un anfitrión y un invitado de
  verdad, conectados por un socket, y verifica que los dos terminen
  viendo lo mismo: arranque, movimiento de cada lado, la regla de no
  pisarse, el sendero compartido, la llave que abre puertas para los
  dos, el cambio de nivel, la pantalla de cierre, el reinicio y la
  desconexión a mitad de partida. También comprueba que un pedido
  imposible del invitado no los deje desincronizados, y que los dos lados
  lleguen al mismo puntaje —que no viaja por la red, sino que cada lado
  calcula por su cuenta.
- Las dos se corren con `python pruebas/pruebas_red.py` y
  `python pruebas/pruebas_multijugador.py`. Están separadas a propósito: si la
  primera pasa y la segunda falla, el problema es de la lógica del
  juego y no de la red.

### Correcciones

- **Crear dos partidas en la misma computadora no daba error, y las dos
  quedaban escuchando el mismo puerto.** `red.py` usaba `SO_REUSEADDR`,
  que no significa lo mismo en todos los sistemas: en Linux y Mac solo
  permite reabrir un puerto recién cerrado, pero en Windows permite
  además robarle el puerto a un socket que lo está usando ahora mismo.
  Como el juego mismo sugiere en pantalla abrirlo dos veces para probar
  en una sola PC, era un camino fácil de encontrar. Ahora en Windows se
  reserva el puerto en exclusiva con `SO_EXCLUSIVEADDRUSE` y la segunda
  partida avisa que el puerto está ocupado.
- **El puntaje del Multijugador se estaba guardando en el highscore
  general**, en contra de lo que decía su propio código: `_guardar_progreso`
  está sobrescrito en vacío con el comentario de que no tendría sentido
  guardar un récord que depende de con quién se jugó, pero
  `_completar_nivel` llamaba a `actualizar_highscore` por afuera de ese
  método. Ahora hay una costura, `_persiste_highscore`, que el
  Multijugador cierra; Infinito, Tutorial y Viaje no cambian. Lo único que
  el cooperativo sí deja guardado son los objetos conseguidos, que son una
  colección y no un récord.
- **El sonido de movimiento se pedía como `Moverse.wav` pero el archivo
  se llamaba `moverse.wav`.** En Windows funcionaba de casualidad,
  porque no distingue mayúsculas de minúsculas en los nombres de
  archivo; en Linux o Mac el juego se caía al entrar a cualquier
  partida. El archivo pasa a llamarse `Moverse.wav`, igual que el resto
  de los sonidos.

### Limpieza

- Se borran las tres hojas de las animaciones del fondo del menú
  (`nubes_anim.png`, `pajaros_anim.png`, `luciernagas_anim.png`), que
  quedaron sin usar al descartarse esa idea.
- Se borra `muro.png`, que no lo referenciaba ningún código ni ningún
  mapa desde antes de la Ronda 2.
