# Ajedrez Polgar vs Kasparov

Juegas **como Judit Polgar** contra **Garry Kasparov**, y unas *piezas fantasma* te
van marcando en el tablero la jugada que ella jugó de verdad en esa misma posición.
No es un tutorial grabado: se adapta a lo que Kasparov responda en cada partida.

## De dónde salen las jugadas

| | Fuente | Cuántas |
|---|---|---|
| Tus sugerencias | Partidas reales de Judit Polgar | 1.823 partidas, 52.146 posiciones |
| Jugadas de Kasparov | Partidas reales de Garry Kasparov | 2.127 partidas, 57.468 posiciones |

Los PGN vienen de la base pública **PgnMentor** (`data/*.pgn`). El script
`scripts/build-book.mjs` recorre cada partida jugada por jugada y guarda, para cada
posición en la que le tocaba mover a la protagonista, **qué jugó**, en qué partida y
cómo terminó. Ese índice es el "libro".

Mientras la posición exista en su libro, la pieza fantasma es historia:
`Polgar–Kasparov, Wijk aan Zee 2001`, no una invención.

## Qué pasa cuando la posición se sale del libro

En cuanto tú o Kasparov jugáis algo que ninguno de los dos jugó nunca, ya no hay
partida que copiar. Ahí entra el motor, con **dos perfiles de evaluación distintos**:

- **Polgar**: pondera fuerte el ataque al rey y la iniciativa, y castiga poco el
  riesgo propio — está dispuesta a entregar material por el ataque.
- **Kasparov**: pondera espacio, movilidad de piezas y seguridad del rey propio.

La tarjeta de la derecha siempre dice cuál de los dos casos es: **`partida real`** o
**`estilo Polgar`**. Nunca se presenta una jugada de motor como si fuera suya.

## Cómo se juega

1. Las piezas fantasma azules marcan la jugada sugerida (y, en modo *plan*, las dos
   siguientes jugadas tuyas de esa misma partida, numeradas 2 y 3).
2. Mueves con dos clics: pieza y destino. `Jugar esta` juega la sugerida; `Enter` también.
3. Si juegas otra cosa, el motor mide las dos jugadas y te dice cuánto se pierde,
   con la opción de deshacer y probar la suya.
4. La barra de estadísticas lleva cuántas veces coincidiste con ella y tu racha.

## Correr en local

```bash
node scripts/build-book.mjs   # regenera books/*.json desde data/*.pgn (~20 s)
npm start                     # http://localhost:3000
```

Sin dependencias: solo Node 18+.

## Estructura

```
public/js/chess.mjs    motor de ajedrez 0x88 (movimientos, SAN, FEN)
public/js/eval.mjs     evaluación + perfiles de estilo
public/js/search.mjs   negamax con poda alfa-beta y quiescencia
public/js/explain.mjs  traduce una jugada a "qué plan es esto"
public/js/app.js       tablero, piezas fantasma y panel
server.js              estáticos + API del libro (/api/consejo)
scripts/build-book.mjs PGN -> índice por posición
scripts/perft.mjs      validación del motor (perft)
scripts/simular.mjs    partida completa sin navegador
```

## Verificación del motor

- `npm test` corre **perft** sobre 5 posiciones estándar hasta profundidad 5
  (4.865.609 nodos en la inicial): todos los conteos coinciden.
- El constructor del libro reprodujo las **3.950 partidas** de los dos PGN sin un
  solo error de notación, lo que valida generador de jugadas y parser SAN a la vez.
