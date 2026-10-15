Hola, somos el equipo que desarrolló UAIBOT, un videojuego creado en Python con la biblioteca Arcade, pensado para estudiantes de segundo ciclo de primaria.

La propuesta combina estrategia, cooperación e inclusión social. El jugador acompaña a una familia de robots que debe reunir donaciones y llegar a un merendero. Para conseguirlo, tiene que planificar el recorrido, administrar los movimientos y comprender las reglas de cada elemento.

Quisimos que la temática solidaria también estuviera presente en la forma de jugar. Por eso, los personajes tienen capacidades que se complementan y, en el modo cooperativo, los jugadores necesitan coordinar sus decisiones.

[Mostrar el menú principal.]

Organizamos el proyecto en cuatro modos.

Tutorial reúne las consignas del desafío en un nivel fijo. Esto permite aprender las reglas y facilita comprobar las funciones solicitadas.

Viaje es una campaña de diez niveles diseñados en Tiled, donde se incorporan personajes y se recolectan distintos tipos de donaciones.

Infinito ofrece niveles generados de manera procedural, con dificultad creciente y registro de récords.

Finalmente, Multijugador permite que dos personas jueguen desde computadoras conectadas a una misma red local, compartiendo el recorrido y los recursos del equipo.

[Entrar a Tutorial.]

En Tutorial, el objetivo es recoger toda la comida, completar las pasadas necesarias junto a las sillas de ruedas y llegar al merendero.

La comida se representa con hexágonos y se recoge al pisarla. Las sillas se representan con triángulos y se recolectan pasando por las celdas vecinas. Su contador debe quedar en la cantidad exacta que se pide.

Los cuatro robots comparten el camino recorrido, pero cada uno dispone de ocho movimientos. Con C podemos cambiar de personaje. Esto obliga a pensar cómo distribuir los recursos para completar la misión.

Internamente, el escenario se representa mediante una grilla de filas y columnas. Antes de aceptar un movimiento, el programa comprueba que la celda esté dentro del mapa, que no tenga una pared y que no forme parte del sendero ya recorrido.

Usamos conjuntos para registrar posiciones, como las paredes y el sendero, y diccionarios para guardar información como los movimientos disponibles y el estado de las sillas.

Una función importante es deshacer. Antes de una acción válida, guardamos una copia del estado relevante en un historial. Al presionar Z, recuperamos el último estado guardado. Así se restauran la posición, los movimientos y los recursos recolectados.

[Ubicarse junto a una pared.]

En la ronda final incorporamos la posibilidad de destruir una pared adyacente. Primero presionamos X y después una flecha para elegir la dirección. La acción consume dos movimientos del robot activo.

Si deshacemos con Z, la pared vuelve a aparecer y recuperamos ambos movimientos. Utilizamos el mismo historial para que esta nueva mecánica sea consistente con las anteriores.

[Mostrar la destrucción de la pared y deshacerla.]

Otra incorporación es el modo de alto contraste, que se activa con A.

[Activar el alto contraste.]

La presentación utiliza negro, amarillo y blanco, con bordes de las celdas más gruesos y nombres dentro de las celdas del robot activo y del merendero. También adaptamos los textos y las pantallas de resultado.

Buscamos que la información importante pueda reconocerse por formas, nombres y contadores, además del color.

Al completar el nivel, el jugador ingresa su nombre. El juego registra su tiempo, ordena los resultados de menor a mayor y muestra su posición sobre el total de participaciones registradas. Los tiempos iguales comparten puesto.

Como aporte extra, agregamos una guía que enseña mediante acciones. Reconoce lo que el jugador hace, aunque lo haga en otro orden, y puede ocultarse con G. También incorporamos mensajes que explican por qué no se puede avanzar o qué falta para entrar al merendero.

Durante el desarrollo trabajamos en el rendimiento. Un problema era que algunos sonidos se cargaban nuevamente al cambiar de pantalla. Incorporamos una caché para reutilizarlos, lo que redujo los picos de memoria y las interrupciones del audio.

También utilizamos inteligencia artificial como apoyo para programación, imágenes y música. Documentamos su uso y los pedidos realizados. El equipo tomó decisiones, revisó las propuestas y probó los resultados antes de incorporarlos.

Con UAIBOT buscamos que la tecnología permita aprender a planificar, colaborar y reconocer distintas capacidades mediante una experiencia de juego accesible y entretenida.

Muchas gracias.