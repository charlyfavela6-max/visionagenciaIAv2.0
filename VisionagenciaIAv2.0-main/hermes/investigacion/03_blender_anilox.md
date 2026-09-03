# Plan de produccion — Rodillo Anilox (video Blender)

**Nota previa honesta:** no tengo tu guion de 9 cuadros en el contexto. Lo que sigue propone los 9 planos en orden pedagogico que cubren los 4 conceptos que pediste; si tu guion ya define los planos, mapéalos contra esta lista y veré si algo se contradice.

---

## A. Que TIENE que ensenar el video (criterio pedagogico + numeros)

Un impresor flexografico que vea este video debe poder responder al final, sin ayuda:

1. **Que es BCM y por que importa mas que la lineatura sola.**
   - BCM = mil millones de micrones cubicos por pulgada cuadrada. 1 micron = 0.000039 pulgadas (25.4 um en 0.001 pulg).   - Rango real: 1.0 BCM (ultra fino, 1300-2000 LPI) hasta 40 BCM (adhesivos, 55 LPI).
   - Regla de oro: si necesitas +25% de densidad, NO vayas a un rodillo con 25% menos lineatura — vas a un rodillo con 25% más volumen y misma o mayor lineatura. (Dato FFTA, +52% de densidad probada hasta profundidad/apertura 0.52.)

2. **Que es lineatura (LPI/cpi) y como se relaciona con el ancho de celda.**
   - Una celda de 800 LPI ocupa aprox 32 um de ancho. Una de 200 LPI ocupa aprox 127 um. Una de 1200 LPI ocupa aprox 21 um.
   - Mas lineatura = celdas mas chicas = pelicula de tinta mas delgada = soporta tramas finas y porcentajes de punto bajos.

3. **Que es el angulo de grabado y por que60° domina.**
   - 60° hex: empaque optimo, ~15% mas celdas por pulgada cuadrada que 45°.
   - 45° diamante: el largo de la apertura queda paralelo al eje del rodillo (visible en3D como un rombo alargado).
   - 30° hex: alternativa a 60°, mejor para UV viscoso.
   - Trihelicoidal: surcos continuos helicoidales, NO celdas individuales — distinto fisicamente.

4. **Que le pasa al rodillo en operacion: pulido vs. tapado vs. desgaste.**
   - Pulido (light scoring): particulas pequeñas entre racla y celda, destruye pared celular sin profundizar, raya clara en impresion.
   - Ranurado profundo (deep gouging): particula grande atrapada, surco ancho y oscuro.
   - Tapado (plugging/fill-in): tinta seca se mete en celdas, perdida local de volumen, raya clara.
   - Regla de auditoria: rodillo especificado a 8.0 BCM que mide 6.0 BCM perdio 25% de capacidad.

5. **Cadena de transferencia (4 puntos) que nunca debe faltar.**
   Anilox → plancha flexo → sustrato. La celda solo tiene sentido si la pelicula que sale va a la plancha; eso explica porque60° hex entrega mejor: mas celdas por area = mejor distribucion, no mas tinta.

---

## B. Plan de 9 planos en orden (lo que se ve en cada uno)

**Plano 1 — Apertura: la prensa flexo en silencio.**
Rodillo anilox rotando lento, sin tinta. Camara orbital lenta. Color neutro, sin musica. Texto superpuesto: "El corazon de la prensa flexo". Duracion sugerida: 4-5 s. Proposito: anclar el objeto antes de explicar nada.

**Plano 2 — Acercamiento a la superficie, mystery shot.**
Macroscopica del cilindro. NO se distinguen celdas todavia, solo "una superficie metalica/ceramica rara". Voz en off: "Esto no es liso." Transicion con zoom rapido hacia plano 3. 3-4 s.

**Plano 3 — Revelacion: el patron de celdas.**
Vista macro de la superficie grabada, patron hexagonal 60°, en movimiento de rotacion lento. Color de celdas resaltado (cyan o magenta), resto en gris. Aqui el impresor debe ver por primera vez que "esta cosa esta llena de hoyitos". 5-6 s.

**Plano 4 — Comparativa de lineatura (split-screen o morph).**
A la izquierda: 200 LPI (celdas grandes, ~127 um). A la derecha: 1200 LPI (celdas pequenas, ~21 um). Misma escala de cuadro. Numero grande en pantalla. Aqui se entiende que "mas lineatura = celdas mas chicas". 6-7 s.

**Plano 5 — Definicion visual de BCM.**
Una sola celda aislada, en corte seccionado (ver errores comunes abajo). Se muestra su profundidad y apertura. La celda se "llena" de tinta animada hasta el borde. Texto: "BCM = volumen de tinta por pulgada²". Animacion: cubo de 1 pulgada cuadrada con miles de celdas llenandose. 7-8 s.

**Plano 6 — Angulo de grabado: los 3 patrones lado a lado.**
Tres parches rotando:
- 60° hex (empaque optimo, 100% celdas en area).
- 45° diamante (rombo, ~85% celdas por area — el "15% menos" real).
- Trihelicoidal (surcos, NO celdas aisladas — diferente fisica).
Numero visible del % de cobertura. 8-10 s. Este es el plano que mas cuesta hacer bien en 3D.

**Plano 7 — La cadena de transferencia.**
Cuatro rodillos animados lado a lado (anilox → racla → plancha → cliché → sustrato). Pelicula de tinta visible migrando. Camara hace travelling siguiendo la tinta. Aqui se cierra el "para que sirve el BCM". 8-10 s.

**Plano 8 — Desgaste en operacion.**
Mismo patron hexagonal 60° pero ahora con tres variantes:
- Celda nueva (profunda).
- Celda pulida (pared superior rebajada, "platinum" suave).
- Celda tapada (rellena de tinta seca).
- Ranurado (surco continuo cortando varias filas).
Comparativa con etiqueta de porcentaje de BCM perdido (8.0 → 6.0 = -25%). 8-10 s.

**Plano 9 — Cierre: impresion en sustrato.**
Tira de sustrato pasando por la prensa. Trama CMYK visible. Zoom a una zona: se ve el patron de celdas "traducido" en micropuntos de tinta. Voz: "Cada celda es un punto de control." 5-6 s.

---

## C. Que se puede simplificar en 3D sin mentir

- **Escala:** la celda real es de 20 a 130 um. En pantalla es imposible mostrar escala real y contexto. **Mentira aceptable:**放大 (放大) la celda entre 500x y 5000x. **Honestidad obligatoria:** poner numero real (ej. "celda real: 32 um — vista amplificada 2500x") al menos una vez.
- **Forma de celda:** una piramide truncada real tiene paredes con micro-rugosidad laser. **Simplificar a:** piramide truncada limpia con paredes lisas. No afecta la explicacion de BCM.
- **Cantidad de celdas visibles:** una pulgada cuadrada de 800 LPI tiene 640.000 celdas. Renderizar todas es suicida. **Simplificar a:** matriz de 20x20 a 50x50 celdas representativas, con la frase "area representativa". El patron periodico permite esto sin mentir.
- **Angulo 60° hex:** NO simplificar como panal de abejas perfecto. Las celdas reales tienen paredes comunes compartidas y ligeras irregularidades de grabacion. Con suficientes vertices y subdivision surface el panal luce natural.
- **Trihelicoidal:** se puede mostrar como canales helicoidales continuos SIN paredes transversales, sin mentir — esa es la diferencia fisica con 60° hex.
- **Volumen animado:** se puede animar la celda llenandose de un fluido sin simulacion real (usar Shape Keys o relleno animado frame por frame). El publico no notara.
- **Rotacion del rodillo:** a300 rpm reales el movimiento se ve borroso. Se puede usar slow-motion (mostrar a 30 rpm efectivas). Es simplificacion cinematografica estandar, no tecnica.

---

## D. Errores tipicos al representar celdas anilox en 3D

1. **Celdas como "agujeros cilindricos" en vez de piramides truncadas.** Las celdas grabadas con laser NO son cilindros. Son piramides truncadas (formula D/3 * (A1 + A2 + sqrt(A1*A2))). Un cilindro subestima volumen entre 20 y 40%.

2. **Hexagono perfecto (panal de abejas cerrado) para 60°.** El60° real tiene paredes comunes entre dos celdas adyacentes; el area de apertura NO es exactamente un hexagono regular con pared propia. Si renderizas panal perfecto tipo Minecraft, estas mintiendo sobre densidad.

3. **45° como rombo con cuatro paredes simetricas.** En realidad el rombo esta ALARGADO con su eje mayor paralelo al eje del rodillo. Esto es lo que causa el "15% menos celdas por area". Si lo dibujas cuadrado, desaparece la diferencia clave.

4. **Trihelicoidal mostrado como "hexagono pero en filas".** Es el error mas grave. Trihelicoidal son surcos helicoidales continuos SIN paredes transversales; no es un patron de celdas en zigzag. Si haces eso, ensenas algo que NO existe.

5. **Celdas sin "land area" (pared superior entre celdas).** El land area es la superficie entre celdas que la racla toca. Sin el, la racla "no tiene donde apoyarse" y el concepto de presion de racla pierde sentido.

6. **Profundidad proporcional incorrecta.** En una celda 800 LPI / 4 BCM real, profundidad ~12-15 um, ancho ~32 um. Relacion profundidad/apertura ~0.4. Si la haces cuadrada o invertida (mas ancha que profunda), estas mostrando una celda de 200 LPI y el numero BCM sera incorrecto.

7. **Simetria radial perfecta al render.** Las celdas reales tienen microvariaciones de ±2 um por el pulso laser. Si son perfectas geometricamente, parece ceramica sintetica y el publico experimentado deja de confiar. Una ligera Noise Displacement lo soluciona.

8. **Mostrar celdas con color de tinta visible cuando el anilox esta "seco".** La tinta esta EN la celda solo cuando el rodillo esta dentro de la fuente entintadora. Fuera de ahi, el rodillo tiene pelicula residual apenas visible. Si pintas las celdas de color solido antes del plano 7, parece decorativo.

9. **Olvidar el eje de rotacion en la animacion de45°.** Las celdas diamante deben rotar con su eje mayor paralelo al eje del cilindro. Si las pones con el eje mayor transversal, es geometricamente imposible.

10. **No mostrar el sentido de la rosca del trihelicoidal.** Los surcos helicoidales tienen angulo de helix (30-60°) respecto al eje. Si los pones paralelos al eje (longitudinales), parecen un cilindro estriado, no un anilox trihelicoidal.

---

**Lo que NO se y deberias confirmar:** el "estilo Carlos Alfredo" concreto al que te refieres (canal, ritmo, paleta) — las busquedas no devolvieron un canal Blender especifico con ese nombre. Si tenes un video referencia, mandame la URL y mapeo los planos contra su ritmo.
