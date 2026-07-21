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
