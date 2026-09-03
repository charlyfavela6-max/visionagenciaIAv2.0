# Plan de ingeniería — Encendedor de dedo activado al tronar los dedos

## (a) Cómo funciona de verdad un encendedor de piedra

Cinco elementos, en este orden funcional:

1. **Rodillo estriado (rueda de acero)** — cilindro de 8–12 mm de diámetro con knurling agresivo (20–40 estrías). Gira sobre un eje y está empujado contra la piedra por un muelle.
2. **Piedra de ferocerio (aleación de cerio + hierro + lantano)** — varilla de 3–4 mm Ø y 8–15 mm de longitud. Se sostiene en un portapieza y un muelle (1–2 N) la empuja contra el rodillo. No es "cerámica": es una aleación pirofórica que oxida a ~2500–3000 °C al desprenderse.
3. **Chispa** — al raspar el ferocerio se arrancan micropartículas (~0.1–0.5 mg). Cada impacto rueda-piedra lanza una o varias partículas a >1000 °C. Una chispa "útil" necesita apenas ~5–15 mJ; el butano en mezcla aire-gas se inflama con **0.25 mJ** mínimo.
4. **Válvula + chorro de gas** — el butano sale del depósito a 3–5 atm (~40–70 psi), pasa por una válvula de aguja que reduce presión, y sale por una boquilla (~0.3–0.5 mm Ø). El chorro es turbulento y arrastra aire: en ~10–50 ms hay una nube inflamable delante de la boquilla.
5. **Encendido** — la chispa incide en la nube y la deflagración se sostiene. La llama es la recombinación química butano + O₂ → CO₂ + H₂O.

Secuencia operativa real: el pulgar **rueda** mientras **oprime**. El dedo pulgar hace las dos cosas a la vez (gas y chispa simultáneas). Aquí está el primer problema: **el tronar dedos no rueda nada**, solo suelta un golpe. Eso cambia todo el diseño.

---

## (b) Fuerzas y recorridos: lo que pide cada subsistema vs lo que da el tronar dedos

| Parámetro | Necesario | Tronar dedos (medido en biomecánica) | ¿Cierra? |
|---|---|---|---|
| Velocidad angular del rodillo | 5–30 rad/s en el contacto (≈1–2 m/s tangenciales) | El dedo medio llega a3–6 m/s en la punta durante el snap (~7–10 ms) | **Sí**, vía desmultiplicación |
| Ángulo de barrido por intento | 30–90° (mínimo 1 impacto rueda-piedra) | El dedo medio barre ~5–8 cm en la punta, equivalente a 50–80° si va directo al eje del rodillo | **Sí**, pero con un solo impacto, sin redundancia |
| Recorrido de la válvula | 1–3 mm | El impacto del dedo contra el pulgar entrega10–30 N en ~10 ms | **Sí**, de sobra |
| Fuerza de apertura de válvula | 2–5 N | 10–30 N | **Sí** |
| Tiempo entre chispa y nube de gas | < 50 ms | Gas tarda ~20 ms en formar nube tras abrir la válvula | **Apretado pero viable** |
| Energía cinética del impacto | ~1 mJ (umbral de ignición) | 50–200 mJ (energía del snap) | **Sí**, sobrado |

**Conclusión (b):** el gesto da **toda la energía y fuerza que se necesitan**. Pero el tiempo es crítico: un solo impulso, ~10 ms. Sin redundancia, una chispa perdida = fallo.

---

## (c) Traducción del gesto a los dos movimientosEl tronar dedos tiene **dos fases mecánicamente distintas** que conviene separar:

- **Fase 1 — Carga:** el dedo medio se dobla contra el pulgar comprimiendo tendones. No hay movimiento útil para el encendedor; es el "armado".
- **Fase 2 — Liberación:** el dedo medio se dispara hacia adelante-abajo, acelera, golpea la base del pulgar con el chasquido.

Diseño propuesto para mapear las dos acciones:

```
Fase carga Fase disparo Impacto
───────────── ────────────              ─────────
Dedo medio dobla Trinquete se libera Dedo medio golpea
hacia pulgar  ───────►       rueda empieza a girar ──►  botón-válvula se oprime │ │
                                  ▼                           ▼
                            chispas en gas sale por contacto rueda-piedra      boquilla durante ~50 ms
```

Piezas de la traducción (todas modelables en Blender como cuerpos rígidos):

1. **Palanca de entrada (finger lever):** pivota en la base del dedo medio. La punta del dedo la empuja durante el armado.
2. **Trinquete unidireccional (ratchet):** permite que el dedo se doble sin mover nada, pero bloquea al extenderse. Acumula la carga en un muelle.
3. **Muelle de rueda (wheel spring):** se comprime durante la carga, suelta energía en la liberación.
4. **Mecanismo rueda:** la palanca ataca una cremallera (rack) o un excéntrico (cam) que gira el rodillo ~45–60°. Sin desmultiplicación de engranajes (sería inviable miniaturizar en un dedo) — solo palanca + muelle.
5. **Botón de válvula (thumb pad):** un pequeño poste o palanca en la cara interior del encendedor (lado pulgar). El impacto del dedo contra el pulgar durante el cierre del snap lo empuja 1–2 mm.

---

## (d) Orden gas-chispa: lo que pide la física vs lo que da el gesto

**La física exige:** **gas primero, chispa después.** Motivo: la chispa necesita una mezcla aire-butano ya formada (~5–15% de butano en aire) para deflagrar. Si chispa primero, no hay combustible encendido, solo una chispa al aire.

**Lo que da el tronar dedos:** la chispa (rueda girando) ocurre **durante** la liberación del dedo, mientras que la apertura de válvula (impacto contra pulgar) ocurre **al final** del gesto. Sin diseño adicional, chispa va antes que gas. **Mal.**

**Tres formas de arreglarlo (de mejor a peor):**

1. **Válvula de pila con retardo (latch + retardo):** la apertura se dispara durante la carga (cuando el dedo está aún cargado contra el pulgar), un trinquete la mantiene abierta ~60–80 ms, y luego se cierra por muelle. La chispa, generada ~40 ms después, encuentra gas ya mezclado.**Mecanismo viable**, ~3 piezas extra.
2. **Válvula accionada por leva en la propia cremallera:** la misma leva que gira la rueda abre la válvula primero y luego sigue moviendo la rueda. El orden se codifica geométricamente. Más limpio mecánicamente; requiere diseñar el perfil de leva con cuidado.
3. **Encendedor piezoeléctrico en lugar de ferocerio:** un cristal piezo genera1–2 mJ en<1 µs al impacto. El "click" del snap es ya un impacto perfecto para piezo. **Pero esto ya no es un encendedor de piedra**, contradice el enunciado.

**Recomendación técnica:** opción 1 o2. Sin esto el dispositivo no encenderá, solo chisporroteará.

---

## (e) Riesgos reales de llevar gas en la mano

No son teóricos, son los mismos que un Bic peor situado:

1. **Depósito presurizado sobre piel.** Butano a 3–5 atm. Una fisura → butano líquido en mano, **quemadura por frío** (–0.5 °C al expandir) + riesgo de inflamación.
2. **Llama a<30 mm de dedos.** Quemaduras de grado 2–3 garantizadas si la válvula queda abierta. La piel del dorso del dedo se inflama a 44 °C en 6 horas,60 °C en 5 segundos. Una llama de butano (~1300 °C) es otra categoría.
3. **Fallo de cierre de válvula.** Sin pestillo de seguridad accesible, un golpe accidental abre la válvula en el bolsillo y se obtiene una llama continua escondida entre dedos. Riesgo de quemadura grave.
4. **Recarga en el cuerpo.** Rellenar un depósito de butano implica conectar una lata a alta presión cerca de la cara/mano. Una fuga durante recarga + chispa = deflagración.
5. **Ferocerio caliente.** Las partículas a 2500–3000 °C pueden aterrizar en el propio dedo. No quema al instante, pero deja micropuntos de quemadura.
6. **Mecánicos.** Pinchazos por muelles, fatiga de la palanca tras10000 snaps, corrosión por sudor (cloruro de sodio degrada acero y ferocerio).
7. **Químicos.** El butano líquido en contacto prolongado con piel es ligeramente irritante y produce dermatitis por frío.
8. **Legales.** En varias jurisdicciones (ej. transporte público en ES, AR, MX, UE) los mecheros tienen restricción de edad y volumen; un encendedor portátil en mano puede caer en categorías no reguladas.

**Regla de diseño:** si el depósito es > 1 g de butano y va sobre piel desnuda, necesita **válvula de cierre redundante**, **válvula de alivio de presión**, y **ensayo de caída desde 1.5 m**.

---

## (f) Lista de piezas para modelar en Blender

### Cuerpo y sujeción
| # | Pieza | Geometría | Estado |
|---|---|---|---|
| 1 | Anillo base | Toroide Ø int. 18 mm (dedo medio adulto) | estático |
| 2 | Carcasa superior | Prisma curvado siguiendo dorsal del dedo, ~50×20×15 mm | estático |
| 3 | Tapa lateral pulgar | Placa delgada en cara interna | estático |
| 4 | Cuello de boquilla | Cilindro Ø 6 mm, longitud 8 mm | estático |

### Mecanismo de chispa
| # | Pieza | Geometría | Movimiento |
|---|---|---|---|
| 5 | Rodillo estriado | Cilindro Ø 10 mm × 6 mm, con knurling (textura o modifier) | rotación eje Z, 45–60° por snap |
| 6 | Eje del rodillo | Cilindro Ø 1.5 mm × 12 mm | rotación solidaria al rodillo |
| 7 | Barra de ferocerio | Cilindro Ø 3 mm × 10 mm | estático |
| 8 | Muelle del ferocerio | Helicoide comprimido | compresión0.5–1 mm |
| 9 | Wind guard / placa deflectora | Placa cerca de la zona de chispa | estático |

### Mecanismo de gas
| # | Pieza | Geometría | Movimiento |
|---|---|---|---|
| 10 | Depósito de butano | Cilindro Ø 12 mm × 20 mm, dentro de la carcasa | estático (precaución realismo: volumen ~1 cm³) |
| 11 | Cuerpo de válvula | Bloque 8×6×6 mm con orificio | estático |
| 12 | Émbolo de válvula | Cilindro Ø 2 mm × 4 mm | lineal, 2 mm de carrera |
| 13 | Muelle de válvula | Helicoide | compresión 2 mm |
| 14 | Palanca de válvula | Placa 10×3×1 mm pivotada | rotación 15° |
| 15 | Boquilla | Cono Ø 0.4 mm en punta | estático |
| 16 | Canal interno de gas | Tubo Ø 1 mm (visual, no tiene que ser exacto) | estático |

### Transmisión gesto → mecanismo
| # | Pieza | Geometría | Movimiento |
|---|---|---|---|
| 17 | Palanca de dedo | Placa 15×4×2 mm pivotada en base | rotación 25–30° |
| 18 | Cremallera / leva | Prisma dentado o excéntrico,5 mm carrera | lineal 5 mm |
| 19 | Trinquete unidireccional | Pequeña garra pivotada | rotación 20° |
| 20 | Muelle principal | Helicoide Ø 4 mm, compresión 6 mm | compresión |
| 21 | Botón de pulgar (post) | Cilindro Ø 4 mm con tope | lineal 2 mm |

### Animación en Blender (drivers sugeridos)
- **Driver rueda:** Custom property `snap_intensity` (0–1) × tiempo. Cada snap = un evento de 80 ms con curva de velocidad.
- **Driver válvula:** `snap_phase` (0 = carga, 1 = impacto) × tiempo, con offset de 40 ms para que abra **antes** del pico de chispa.
- **Driver partículas:** sistema de partículas en el punto de contacto rueda-piedra, emisión durante el evento `snap`.

Jerarquía sugerida: `Finger_Sleeve → {Spark_Mechanism, Gas_Mechanism}` con constraints `Child Of` o `Copy Rotation` para los movimientos sincronizados.

---

## Lo que no cierra — honestidad

1. **Una chispa por intento no es confiable.** Los encendedores reales usan 3–5 rotaciones de rueda por ignición para asegurar ≥3 impactos rueda-piedra. Aquí tendrás 1 impacto por snap. **Probabilidad de ignición por gesto ≈ 30–60%**, no 95%. Solución: encendedor piezo en lugar de rueda (pero eso deja de ser "de piedra").
2. **El timing gas-antes-chispa depende de la velocidad del snap del usuario.** Un snap lento deja la válvula abierta mucho antes que la chispa = nube de gas se disipa, no enciende. Un snap rápido no da tiempo a la nube a formarse. **Es un problema de diseño de usuario**, no de mecanismo.
3. **Reservorio de 1 g de butano = ~5 minutos de llama continua** si la válvula queda abierta. Es un quemador portátil con todas las consecuencias. **Sin válvula de cierre mecánico redundante, este diseño es inseguro.**
4. **La miniaturización** (rodillo de 10 mm, muelles de 1.5 N, leva con tolerancia de décimas de mm) **es factible con impresión metálica** pero no con FDM PLA. El Blender debe entenderse como prueba de concepto, no como prototipo funcional directo.
5. **El sudor degrada ferocerio** en semanas. La vida útil del dispositivo se mide en días si se lleva permanentemente, meses si se lleva ocasionalmente con funda. **No es un wearable de uso continuo.**
6. **No he verificado experimentalmente** la velocidad angular que un snap puede imprimir en una rueda de 10 mm con palanca de 15 mm. La cifra de 5–30 rad/s es estimación basada en velocidad lineal del dedo y geometría plausible, **no medida**.

Si el objetivo es un wearable funcional y seguro, **piezo + cámara de butano separada del dedo + trigger de dos pasos** es el camino realista. Si el objetivo es una pieza conceptual para Blender, este diseño cierra sobre el papel y enseña los compromisos reales.
