Nuestro proyecto se llama UAIBOT y está desarrollado en Python con la biblioteca Arcade. Es un videojuego pensado para estudiantes de primaria, que combina desafíos de recorrido con una misión solidaria: reunir donaciones y llegar al merendero.

El jugador debe planificar sus movimientos, administrar los pasos de los robots y cumplir las reglas de recolección. Buscamos que aprenda a resolver problemas y a reconocer cómo distintas capacidades pueden complementarse.

Organizamos el juego en cuatro modos: Tutorial, Viaje, Infinito y Multijugador cooperativo. En Tutorial concentramos las consignas del desafío, para que puedan comprobarse en un solo nivel.

La lógica trabaja con una grilla: antes de aceptar un movimiento, comprueba los límites, las paredes y el camino recorrido. Para deshacer, guardamos el estado anterior de cada acción. Así podemos recuperar la posición, los recursos y los movimientos, e incluso reconstruir una pared destruida.

En esta ronda incorporamos el alto contraste con negro, amarillo y blanco, nombres dentro de las celdas y bordes más gruesos. También agregamos el ranking por tiempo y la posibilidad de romper paredes gastando dos movimientos.

Como extra, desarrollamos una guía que enseña mientras se juega y mensajes que explican por qué una acción no está permitida.

También optimizamos el rendimiento, evitando cargar repetidamente los mismos sonidos para reducir los picos de memoria y las interrupciones del audio.

Utilizamos inteligencia artificial como apoyo para programación y recursos, documentando los pedidos y revisando los resultados antes de incorporarlos.

Con UAIBOT buscamos unir estrategia, cooperación y accesibilidad en una experiencia que permita aprender jugando.