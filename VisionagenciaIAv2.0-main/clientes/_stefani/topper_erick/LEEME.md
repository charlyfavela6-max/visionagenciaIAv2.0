# Cake topper shaker · Erick, 4 años

Pedido de Stefani por WhatsApp el 2026-09-02 22:53:

> «Cake topper shaker 3D · del abecedario con los colores primarios ·
>  que diga Erick y 4 años · y que separe los elementos para imprimir y
>  cortar con Cricut»

Referencias que mandó: `pedido_2sep/01_...jpg` (letras acolchadas con pespunte)
y `pedido_2sep/02_...jpg` (topper redondo con ventana de lentejuelas).

## Archivos

| archivo | qué es |
|---|---|
| `topper_erick_capas.svg` | **El de cortar.** 27 capas, medidas reales en mm |
| `topper_erick_vista.png` | Cómo se ve armado |
| `topper_erick.py` | El generador. Cambiar nombre/edad es una línea |

**Medida real: 15 × 20 cm** más el palito. El SVG lleva `width`/`height` en
milímetros, así que Design Space lo importa a tamaño real sin escalarlo.

## Por qué el texto va en trazos y no en `<text>`

Cricut Design Space **no corta texto vivo** si no tiene la fuente instalada: lo
sustituye por otra y cambia el ancho. Aquí cada letra sale como `path` del
contorno real de Poppins Black, así que corta exactamente lo que se ve, en
cualquier máquina.

## Cómo se arma el shaker

El orden de las capas ES el orden de armado, de atrás hacia adelante:

1. **`base`** — cartulina azul, la silueta completa
2. **`ventana_atras`** — acetato
3. **`marco`** — cartulina blanca con el hueco. **Se corta DOS veces** y se
   pegan una sobre otra: ese grosor es la cámara donde caen las lentejuelas
4. *(aquí se echan las lentejuelas y se sella)*
5. **`ventana_frente`** — acetato
6. **`nube_erick`** — la plaquita blanca de atrás de las letras
7. **`letra_E` … `letra_k`** — una capa por color, encima de la plaquita
8. **`estrella_4`** + **`numero_4`** — montados en la orilla de abajo
9. **`banderin`** + **`texto_anios`**
10. **`suelto_A/B/C/1/2/3`** y las **`estrellita_*`** — pegadas encima del marco
11. **`palito`**

## En Design Space

Subir el SVG → **Ungroup** → cada capa queda como corte aparte, ya con su color
asignado. Agrupar por color de cartulina antes de mandar a cortar.

Las capas `ventana_atras` y `ventana_frente` van en **acetato**, no en
cartulina — el material se cambia en el panel de la derecha antes de cortar.

## Los colores

Primarios, como pidió. El morado y el naranja entran sólo de apoyo porque
«Erick» tiene cinco letras y con tres colores se repetirían:

| | |
|---|---|
| rojo | `#E4322B` |
| amarillo | `#F2B705` |
| azul | `#1668C6` |
| verde | `#5FAF2E` |
| morado | `#7B3FA0` |
| naranja | `#F2760C` |

## Para otro niño

    python3 topper_erick.py

Dentro, la línea `L.palabra("Erick", ...)` y la de `L.palabra("4", ...)`.
Cambias nombre y edad y sale el SVG nuevo con las capas ya acomodadas.
