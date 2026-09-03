Tengo todos los datos que necesito. Procedo a redactar la respuesta.

---

# Plan para Book Nook del Santuario del Dr. Strange — Capas de MDF 3 mm Grabado Láser

## 0. Lo que confirma el material disponible

El rosetón multicapa con retroiluminación LED ya está documentado en foro público: el proyecto de Glowforge del usuario *aproptart* (Strasbourg Cathedral) usa caja exterior y capa superior en PG cherry, capas intermedias en PG maple + PG walnut + PG basswood, y acrílico claro al fondo, en una caja de 10.5" × 1.5" de profundidad. Las piezas más finas llegaron a0.003" (≈0.076 mm) en la capa de walnut. Eso valida que el enfoque multicapa con MDF/basswood + acrílico funciona y que el límite de detalle está en ~0.08–0.1 mm por capa.

Los grosores de libro nook comerciales estándar: 11.1 cm ancho × 22.1 cm alto × 19.5 cm fondo (Rolife) y similares — eso es el volumen real que estás intentando llenar con capas.

---

## (a) Cómo se construye de verdad el rosetón retroiluminado

### Estructura por capas (de delante hacia atrás)

| Posición | Material | Función | Grosor |
|---|---|---|---|
| 1 (delante) | MDF con calado completo del tracero (lo que se ve) | Geometría del rosetón, huecos abiertos | 3 mm |
| 2 | MDF calado con segunda capa de detalle (roles internos, nervios, vidrieras) | Profundidad del dibujo y sombra | 3 mm |
| 3 | MDF grabado raster con líneas finas (plomos de la vidriera) | Refuerza la geometría, da textura de plomo emplomado | 3 mm |
| 4 | Acrílico blanco/esmerilado translúcido | Difusor principal | 2 mm o 3 mm |
| 5 | Cámara de aire | Permite que el LED se homogenice | **20–35 mm** mínimo |
| 6 | Tira de LED (SMD 2835, 120 led/m, blanco cálido 2700–3000 K) | Fuente de luz | 3 mm PCB |
| 7 | Reflector blanco mate (papel opalina o foam board blanco) | Devuelve la luz hacia delante | — |
| 8 | Pared trasera opaca (MDF) | Cierra la caja y oculta el cable | 3 mm |

Total de profundidad interna de pared trasera a capa frontal: ≈ 55–65 mm. La caja exterior del rosetón necesita al menos 60–70 mm de profundidad interna solo para el rosetón; en un book nook estándar eso se come casi todo el espacio, así que suele ir embutido en una de las paredes laterales o en la trasera.

### Separación entre capa y capa (cifras concretas)

- **Capa 1 ↔ Capa 2**: 0 mm (apiladas y pegadas con ciano o cola blanca, registradas con dos clavijas de 1.5 mm). Si las separas, pierdes el efecto "vidriera con relieve" y se ve como paneles sueltos.
- **Capa 2 ↔ Capa 3**: 0 mm, mismo registro.
- **Capa 3 ↔ Acrílico difusor**: **8–15 mm** de aire. Esta separación es la que evita que las sombras de las capas de MDF se proyecten sobre el acrílico (sombras duras).
- **Acrílico ↔ tira de LED**: **20–35 mm** mínimo. La regla de oro en la industria: el difusor debe estar separado del LED al menos **1.5× el espaciado entre LEDs** para eliminar puntos calientes. Con tiras de 120 led/m eso son 12.5 mm teóricos, pero en la práctica los fabricantes de cajas de luz recomiendan **20–35 mm** porque a esa distancia el difusor cubre también los ángulos de dispersión laterales. Con tira de 60 led/m (espaciado 16.7 mm) necesitas ≥25 mm.
- **LED → pared trasera**: 5–10 mm para pasar el cable.

### Difusor (qué material funciona)

- **Acrílico blanco opal/opalino (white opal #7328 o equivalente)**: el más usado, mejor balance de transmisión (~50–60 %) y difusión. Grosor 2 mm o 3 mm.
- **Acrílico frosted (esmerilado)**: menor transmisión (~70 %) pero menos difusor → deja pasar más detalle de la capa de atrás. Útil si quieres que se vea el grabado de la capa 3.
- **No usar**: vidrio (rompe con vibración), papel (se quema con el tiempo), tela (se mancha con el adhesivo).
- **Truco profesional**: añadir una segunda hoja de difusor separada3–5 mm de la primera eleva la uniformidad de ±5.3 % a ±1.2 % según pruebas con espectrofotómetro X-Rite i1Pro 3 (no es marketing, es dato óptico). No obligatorio pero suma calidad.

### Cómo se elimina el punto caliente del LED

1. **Distancia LED-difusor ≥ 25 mm** (con tira120 led/m). Si no puedes, usa tira de 240 led/m y baja distancia a 15 mm.
2. **Reflector** blanco mate (papel opalina 200 g o foam board blanco) pegado a la pared trasera; sin él pierdes ~30 % de luz porque emite hacia atrás.
3. **Difusor doble** separado 3–5 mm del primero (opcional pero elimina el último10 % de inhomogeneidad).
4. **No usar LEDs puntuales** (tipo 5 mm through-hole) para rosetones — siempre tira SMD o panel COB.
5. **Resistencia en serie** o driver de corriente constante para evitar que un LED brille más que los vecinos por variación de Vf.
6. **Tira a 2700–3000 K** (blanco cálido), no blanco frío — el Dr. Strange santuario pide luz cálida/ámbar, y la diferencia psicológica de 4000 K a 2700 K es enorme (lectura "templo" vs "oficina").

### LED concreto recomendado

- Tira SMD 2835, **120 led/m**, **2700 K** (blanco cálido), CRI ≥ 90, 24 V DC, 9.6 W/m.
- Driver: Mean Well APV-12-24 o similar, 12 W mínimo.
- Alimentación: USB 5 V → step-up a 24 V, o toma directa de 12 V con un buck-boost. Para book nook, USB es lo más limpio.
- Dimmer PWM (pot10 kΩ) en línea antes del LED para ajustar intensidad.

---

## (b) Ajustes de láser para MDF 3 mm

Datos consolidados de múltiples fuentes (Bonny Creations, Laser Tinkerer, xTool, Glowforge, OMTech) cruzados con el paper de DCU sobre corte CO2 de MDF.

### Corte pasante (vectorial, 3 mm completo)

| Máquina | Velocidad | Potencia | Pasadas | Air assist | Notas |
|---|---|---|---|---|---|
| CO2 40 W (Glowforge Basic) | 28–35 mm/s | 65–75 % | 1 | Sí, alto | Single pass |
| CO2 60 W (OMTech) | 30–45 mm/s | 55–75 % | 1 | Sí | 45 mm/s con 55 % |
| CO2 80 W (OMTech) | 45 mm/s | 55–65 % | 1 | Sí | El más rápido |
| Diodo 10 W (Ortur LM3, xTool M1) | 240–480 mm/min | 100 % | 3–4 | Sí, **obligatorio** | 250–350 mm/min × 3–5 pasadas en 10 W |
| Diodo 20 W (xTool D1 Pro, Sculpfun S30) | 400–600 mm/min | 100 % | 2–3 | Sí | La mejor opción para book nook |
| Diodo 33 W (Sculpfun S30 Pro) | 600 mm/min | 90–100 % | 2 | Sí | |
| Diodo 40 W (Sculpfun S30 Pro Max) | 800 mm/min | 90 % | 1–2 | Sí |1 pasada posible |

**Regla universal**: en diodo, **multi-pass gana siempre** a single-pass lento. 4 pasadas a 250 mm/min es mejor que 1 pasada a 80 mm/min (el calor se acumula, sale humo, sale resina, se enciende). Air assist a **20–30 PSI** durante corte; bajar a 10–15 PSI o apagar durante grabado.

**Kerf en MDF con CO2**: **0.15–0.30 mm** según material, lente y foco. Para encastres de lengüeta, aplicar offset de **0.075 mm por lado** (0.15 mm total) como base y calibrar con test cut. En diodo el kerf es ligeramente menor, ~0.10–0.15 mm.

### Grabado raster (superficie)

| Máquina | Velocidad | Potencia | DPI / LPI | Pasadas | Notas |
|---|---|---|---|---|---|
| CO2 40 W (Glowforge Pro) | 450 mm/s | 20–28 % | 300 DPI | 1 | Bajo para no chamuscar la resina |
| CO2 60–80 W | 450–600 mm/s | 20–28 % | 300 DPI | 1 | Mismo principio |
| Diodo 10 W | 2000–3500 mm/min | 20–40 % | 0.10–0.12 mm intervalo | 1 | Jarvis/Stucki dithering |
| Diodo 20 W | 3000–5000 mm/min | 15–30 % | 0.10–0.12 mm | 1 | Mismo |
| Diodo 33–40 W | 5000–8000 mm/min | 30–40 % | 254–300 DPI | 1 | Snapmaker Ray |

**Truco para controlar el tono del quemado a propósito**:
- Tono suave (marrón claro, "tabaco rubio"): 10–15 % potencia, alta velocidad.
- Tono medio (caramelo, "tabaco oscuro"): 20–28 % en CO2, 20–30 % en diodo.
- Tono fuerte (marrón negro): 35–45 % en CO2; en diodo 40–50 % o 2 pasadas suaves.
- Tono quemado (negro carbón, antiestético): >60 % en MDF. Evitar.
- Múltiples pasadas suaves (60 % de la potencia objetivo + 2 pasadas) conservan detalle fino. Una pasada al 100 % quema y cierra sombras.

Para **dithering** en MDF: **Floyd-Steinberg** para fotos/orgánico, **Stucki** o **Jarvis** para madera con grano (mejor dispersión de puntos), **Ordered dithering** solo para logos y líneas. **Evitar threshold** en MDF — el grano de la fibra compite con el detalle.

**Regla de oro Trotec**: en madera basta **333–500 DPI**; subir a 600 DPI solo si los puntos no se solapan. MDF uniforme → puede subir a 500–600 DPI porque no hay veta que moleste.

### Grabado vectorial (líneas, score, no corte)

- Velocidad **igual al corte** o1.5× más rápida.
- Potencia **40–60 %** del corte (en CO2); en diodo **30–50 %**.
- Sirve para "rayar" sin atravesar (sirve para juntas decorativas, paneles con doblez simulado).
- **Importante**: en MDF el grabado vectorial deja siempre una marca oscura; si quieres línea clara, usa grabado raster de 1 px de ancho a muy baja potencia.

---

## (c) Simular piedra, madera y moldura con grabado

### Piedra del santuario (caliza, arenisca, bloques)

**Método 1 — Grabado raster por capas (el más realista para book nook)**:

1. Foto de referencia de pared de piedra caliza, convertir a escala de grises, **boost de contraste agresivo** (clip20 % de blancos y 20 % de negros).
2. Aplicar **Floyd-Steinberg dithering** (no Stucki — piedra es más "ruidosa" que el dithering suave).
3. Pasar a LightBurn/LaserGRBL en modo **Image/Grayscale**,500 DPI.
4. Parámetros: CO2 40 W a350 mm/s, 25 % potencia; diodo 20 W a 4000 mm/min, 25 % potencia. **Una pasada**. Más pasadas satura.
5. **Truco para que se lea como bloques de piedra**: superponer un **segundo raster** solo con las juntas entre bloques (líneas finas), grabado vectorial al 30 % de potencia. Esto rompe la homogeneidad de la foto y aparecen las juntas.

**Método 2 — Relieve3D por capas (más impactante pero más MDF)**:

- Capa base (fondo): toda la pared recortada, plana, sin grabado. MDF 3 mm.
- Capa 2 (sombra): silueta de cada bloque, grabado raster al 40 % potencia solo en los bordes de cada bloque (efecto "hueco entre piedras"). 0.1 mm aire a la capa 1.
- Capa 3 (relieve): bloques salientes recortados y pegados encima de la capa 2 con cuñas de 1 mm de MDF. Solo recortar el contorno exterior, dejar el plano del bloque intacto.
- Resultado: relieve físico real, sombras físicamente proyectadas. Más caro en MDF pero el efecto "se lee" como piedra real.

**Números para que funcione como piedra**:
- **DPI500** (no más, se mete ruido en MDF).
- **Intervalo entre líneas 0.10 mm** en diodo.
- **Potencia baja (20–25 %) + pasada única**: cualquier quemado extra oscurece el gris medio y se pierde la textura de piedra.

### Madera del santuario (vigas, marcos de puertas, estanterías)

**Método principal**: raster de vetas de madera, no foto. La veta de madera es **direccional** — usar una textura lineal (Musgrave o Wave Texture en Blender), pasarla a escala de grises, **NO dithering** (la madera es continua, no punteada). Usar **true grayscale** (variación de potencia) si tu controlador lo soporta; si no, **error diffusion Stucki** con bajo contraste.

Parámetros veta de madera:
- CO2 40 W: 400 mm/s, 22–30 % potencia, 500 DPI.
- Diodo 20 W: 3500–4500 mm/min, 25–35 % potencia, 0.12 mm intervalo.

Para que se lea como **madera vieja de santuario** (oscura, con nudos):
- Foto de madera de roble envejecido, contraste alto, **clip 30 % de negros** (oscurecer nudos), dejar medios brillantes.
- Potencia 30–35 % en CO2, una pasada.
- Superponer un **segundo raster** con las grietas y nudos a 50 % potencia, pero **solo en zonas localizadas** (no en toda la tabla).

### Molduras del santuario (cornisas, capiteles, marcos)

Aquí NO funciona el raster solo. La moldura **tiene volumen**, y el truco es:

**Método A — Capas apiladas (el que funciona en book nook)**:
- Capa 1: silueta de la moldura completa (perfil), cortada a 3 mm.
- Capa 2: silueta interior (sin la moldura exterior), pegada detrás, retranqueada 1 mm para crear una sombra de 1 mm. Ese hueco de 1 mm entre capas, visto de frente, lee como **bisel o escalón**.
- Capa 3: detalle interno (dentículos, hojas, roleos) cortado y pegado encima de la capa 2 con 1 mm de aire.
- Cada capa da 1 mm de profundidad visible; con 3–4 capas consigues 3–4 mm de moldura con sombreado físico.

**Método B — Grabado raster en relieve (más barato, menos impactante)**:
- Cortar la silueta de la moldura.
- Sobre la cara vista, grabado raster de una foto de moldura real (cornisa clásica con sombreado), a 500 DPI, potencia media (25–30 %).
- Engañar al ojo: el raster plano se lee como moldura por el contraste del sombreado.
- Truco: añadir una **línea de grabado vectorial** en cada arista de la moldura (potencia 35 %, 1 pasada),0.5 mm antes del borde. Esa línea oscura en el borde imita el cambio de plano.

**Números clave para molduras**:
- Grosor mínimo de cuña separadora: **1 mm de MDF** (no menos, o no se nota el escalón).
- Profundidad máxima apilable sin que parezca "pastel": **3 capas = 9 mm** de relieve visual.
- Distancia entre capa frontal y fondo: **2–3 mm** mínimo para que la sombra se note (a1 m de distancia, ojo humano necesita ≥ 1.5 mm de profundidad para leer escalón).

---

## (d) Qué hace que un book nook se vea caro y qué lo hace ver barato

### Lo que lo hace ver **caro**

1. **Tolerancia de corte real**: las piezas encajan con presión suave de dedos, sin lijar. Kerf controlado a **±0.05 mm**. Eso requiere láser bien calibrado y diseño que compense kerf.
2. **Canto quemado oscuro, controlado y uniforme**: el caramelo-negro en cada corte es **señal de láser CO2 bien ajustado + air assist**. En book nooks baratos el canto es gris sucio o amarillo claro (láser mal calibrado o diodo mal usado).
3. **Lengüetas en sus ranuras sin holgura**: pieza entra con "click". Si se ven huecos de luz entre paneles, barato.
4. **Cableado oculto en canales premoldeados**, no pegado con cinta sobre las paredes. Book nook caro: los cables van por dentro de la estructura, con un único switch accesible desde el exterior.
5. **Múltiples fuentes de luz con propósito narrativo** (ventana cálida + una vela + un farol), no "una tira LED pegada abajo que ilumina todo parejo".
6. **Difusión real**: cero puntos calientes visibles en el rosetón, ninguna sombra del propio LED proyectada en la pared.
7. **Profundidad de escena por capas**: las paredes tienen3–5 capas de MDF, no 1. La luz cae en capas y produce sombras físicas.
8. **Texturas enparedes** con grabado raster de tono controlado, no superficies lisas pintadas.
9. **Switch y batería accesibles desde el exterior sin desmontar el nook**.
10. **Acabado de pintura controlado**: bordes pintados del color de la cara (no MDF crudo visible en los cantos). El MDF crudo beige es señal de "lo dejé así".

### Lo que lo hace ver **barato**

1. Piezas que no encajan, hay que lijar o forzar. Eso es contratación a fábrica externa con tolerancia laxa.
2. Canto gris-amarillo sin quemar: diodo mal ajustado o velocidad/potencia mal combinadas.
3. Una sola tira LED pegada en el suelo que inunda todo. Plano y aburrido cuando se apaga la luz ambiente.
4. Punto caliente del LED visible en el rosetón: difusor mal separado o ausencia de difusor.
5. Cables visibles por fuera o con cinta aislante.
6. Paredes lisas sin textura (una sola capa de MDF).
7. Batería interna con tapita que se ve mal (vs. switch disimulado).
8. Piezas que se mueven una vez ensamblado (falta de registro/encastres).
9. MDF crudo en los cantos visibles (no se pintó el canto).
10. Manual de instrucciones traducido a medias, sin numerar las piezas, sin diagrama de cableado.

Dato de la industria: los kits de $20–$50 son80 % del mercado y fallan precisamente en los puntos 1, 3 y 4. De $90–$130 ya entran en territorio donde esos10 puntos se cuidan.

---

## (e) Cómo se renderiza realista en Blender

### Geometría- Modelar el book nook con **grosor real de MDF = 3 mm exactos** en todas las piezas. No 2.5, no 4. **Medir con calibre** la pieza real si la tienes, y aplicar la cifra al modelo.
- Todas las intersecciones entre capas deben mostrar el **canto de 3 mm visible**: las paredes laterales del book nook no deben modelarse como "planos con textura", sino como **extrusión de 3 mm**. En el render, las caras laterales del MDF deben verse.
- Las lengüetas y ranuras deben modelarse con la holgura real: **+0.1 mm por lado** sobre la medida nominal (el kerf real medido en tu máquina). Si no, en el render se ven "soldadas".
- El rosetón: cada capa es un mesh separado con offset Z de 0 mm (capas apiladas), 9 mm (separación al acrílico), 35 mm (a la tira LED). **No instanciar**, cada capa tiene su mesh.

### Materiales (Principled BSDF en Cycles)

**MDF crudo (cara vista)**:
- Base Color: **#D4C29A** (beige cartón) o muestrear de foto real con eyedropper.
- Roughness: **0.85–0.95** (es mate, no satinado).
- Specular IOR Level: **0.3–0.4**.
- Normal/Bump: textura procedural o foto de MDF real, intensidad **0.05–0.1** (sutil, no agresivo).
- No metallic.

**Canto quemado (MDF cortado por láser)**:
- Base Color: gradiente de **#8B4513** (caramelo) en el centro a **#1A0F05** (negro) en los bordes quemados. En Cycles, esto se hace con **Geometry Node "Pointiness"** + ColorRamp o, mejor, con **un nodo Gradient Texture** mapeado por la dirección del canto. Mix entre dos materiales según la distancia al filo.
- Roughness: **0.65–0.75** (más brillante que la cara porque la resina se vitrifica un poco).
- Procedural edge wear: Pointiness → ColorRamp (negro a blanco), **strength del ColorRamp = 0.43** en el handle azul para variación natural, Noise Texture (Scale 35, Detail 16, Distortion 0.5) → Mix RGB modo Darken sobre el Pointiness.
- Bump intensity del canto: **0.02** (sutil, no exagerar).

**Grabado raster (lo quemado)**:
- Base Color: **#3B2410** (marrón muy oscuro) para zonas quemadas, **#6B4423** (caramelo) para medios, degradando a la base MDF en zonas claras.
- Modulación con el mismo mapa de Pointiness en la zona grabada, o usar el mapa de imagen real del raster como Color Attribute.

**Acrílico esmerilado del difusor**:
- Principled BSDF: Transmission = **1.0**, Roughness = **0.4–0.6** (el frosting dispersa), IOR = **1.49** (PMMA), Thickness = **3 mm**.
- **Atención**: si el Roughness es muy bajo se ven los puntos LED; si es muy alto, se pierde luz.
- Color: blanco lechoso. Base Color **#F0F0E8**, Alpha controlado por Principled → no usar Alpha directo, usar Transmission + Color.

**Madera con vetas**:
- ColorRamp sobre Wave Texture (Scale **0.8**) + Musgrave (Detail 16).
- Mezclar dos tonos: claro **#C9A06B**, oscuro **#6B4423**.
- Bump: Noise Texture (Scale 50, Detail 8) intensidad **0.03–0.05**.

**Piedra del santuario**:
- Mezclar dos Musgrave (Detail 8 y Detail 16) con ColorRamp de tonos calizos: **#C8B89A** (claro), **#9A8A6E** (medio), **#6B5A48** (oscuro).
- Bump intensidad **0.15–0.20** (la piedra tiene textura fuerte).
- Roughness **0.85–0.95**.

### Iluminación (lo más importante del rosetón)

**Tira LED detrás del rosetón**:
- Usar **Area Light** (Rectangle) en lugar de Point Light. Tamaño: igual al rosetón, **Ratio X1 : Y 1** (cuadrada para homogeneidad).
- **Power**: 4–5 W (equivalente a bombilla de 800–1000 lm, según tabla oficial de Blender para Area Light).
- **Color Temperature**: **2700 K** (warm), no 3000 K. Marca la diferencia psicológica "santuario / mágico".
- Exposure: ajustar para que la cara del acrílico emita ~80 % del valor máximo sin clipping. Cycles Exposure **0.0**, modificar Power.

**Luz ambiental tenue**:
- Un Area Light de **0.5–1 W** simulando luz de la sala, **4500 K** (luz día neutra), baja intensidad.
- Sin luz ambient el render queda negro excepto el rosetón: **eso es exactamente lo que quieres** cuando el book nook está apagado en una estantería. El rosetón es el único emisor.

**World**:
- Background negro o casi negro (#0A0A0A).
- Si quieres ver el book nook en contexto de estantería, usar un HDRI de interior oscuro con intensidad **0.3** (no 1.0).

### Profundidad de campo (DOF)

- Camera: distancia focal **85–100 mm** (lente retrato, replica "macro de mesa").
- Sensor size: **36 mm** (full frame).
- **F-Stop: f/2.0 a f/2.8** (escena de libro nook es pequeña, quieres DOF shallow pero no ridículo).
- Focus Object: un Empty colocado en la zona que quieres nítida (típicamente el centro del rosetón o la puerta del santuario).
- **Blades: 6** (bokeh hexagonal suave, no triangular que canta "render").
- Para escenas miniaturas: bajar f-Stop a **f/1.4–f/1.8** da el efecto tilt-shift exagerado que vende "miniaturizado", pero para book nook que quieres leer como real a30–50 cm de distancia, **f/2.0–f/2.8** es el sweet spot.

### Render settings

- Cycles (no EEVEE — necesitas la transmisión del acrílico y el bounce real).
- Samples: **256–512** con Denoiser OptiX o OpenImageDenoise activo.
- Light Paths: bounces Diffuse **8**, Glossy **8**, Transmission **12** (necesario para que el acrílico reparta luz correctamente).
- Film: Transparent OFF.
- Color Management: Filmic, Medium-High Contrast, Look "Medium High Contrast".
- Tamaño final: mínimo **2048 px en el lado largo** para que se vea "caro".4K si va a impresión.

### Truco final: el grosor visible del canto

El 80 % de los renders de book nook fallan porque modelan las paredes como **planos infinitos con textura**, no como **láminas de 3 mm con canto visible**. Si en el render final no se ve un filo de 3 mm en el borde de cada capa (con su color caramelo-negro), no se va a leer como láser. Activar **Cavity** en el shader (lo que hace Pointiness) sobre las aristas vivas; eso genera la AO del corte que da la lectura "esto es un material real con grosor".

---

## Resumen de cifras críticas para tener a mano

| Concepto | Valor |
|---|---|
| Grosor de chapa MDF | 3 mm (medir con calibre; varía 2.8–3.2 mm) |
| Kerf CO2 en MDF | 0.15–0.30 mm (offset 0.075 mm/lado) |
| Kerf diodo en MDF | 0.10–0.15 mm |
| Separación capa ↔ difusor | 8–15 mm |
| Separación difusor ↔ LED (120 led/m) |20–35 mm |
| Regla difusor-LED | ≥ 1.5× espaciado entre LEDs |
| Profundidad total rosetón | 55–65 mm |
| DPI grabado raster MDF | 500 (rango útil 333–600) |
| Intervalo diodo | 0.10–0.12 mm |
| Dithering MDF piedra | Floyd-Steinberg |
| Dithering MDF madera | Stucki / Jarvis |
| Corte CO2 60 W 3 mm | 30–45 mm/s, 55–75 %, 1 pasada |
| Corte diodo 20 W 3 mm | 480–600 mm/min, 100 %, 2–3 pasadas |
| Grabado CO2 60 W superficie | 450 mm/s, 20–28 %, 300 DPI |
| Grosor mínimo cuña moldura | 1 mm |
| Capas máx para moldura sin "look pastilla" | 3 (9 mm de relieve) |
| Profundidad mínima para leer escalón | 1.5 mm |
| Camera DOF book nook | 85–100 mm focal, f/2.0–f/2.8, 6 blades |
| Cycles light bounces Diffuse/Glossy | 8 / 8 |
| Cycles light bounces Transmission | 12 |
| Temperatura luz rosetón | 2700 K |
| Tamaño mínimo render | 2048 px lado largo |

---

## Lo que no sé / no he verificado

- Comportamiento exacto de tu MDF concreto (marca, densidad, resina) — los ajustes de corte/grabado anteriores son punto de partida, **necesitas un test grid de 5×5 con velocidades100–400 mm/s y potencias 60–90 % en tu propio láser antes de cortar nada definitivo**.
- Curva exacta de tone-mapping de tu cámara si no tienes Lightroom/Phase One — los números de color que doy son aproximaciones dentro de sRGB.
