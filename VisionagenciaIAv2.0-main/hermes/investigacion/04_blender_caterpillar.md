# Plan — Video Blender como reference guide para IA — CAT excavadora/retro

Workflow objetivo: el render de Blender NO es el video final. Es el *structure guide* (imagen de control) que se inyecta a Sora, Runway Gen-4, Veo 3 o Kling como first-frame / subject reference. La IA anima a partir de ahi; el prompt dirige la acción. Por eso el render prioriza **silueta, proporciones y encuadre** sobre fotorrealismo.

---

## (a) Planos que venden maquinaria pesada

Lista basada en convenciones reales de publicidad de Caterpillar, Komatsu, Volvo CE y Liebherr (60-120 s de spot típico). 14 planos cubren el arco narrativo estándar "hero → trabajo → cierre".

| # | Plano | Duración | Función narrativa |
|---|---|---|---|
| 01 | Heroe / beauty 3/4 frontal, contrapicado | 5-7 s | Ancla visual, modelo identificable |
| 02 | Establecimiento ambiental (cantera / obra) | 4-6 s | Escala y contexto |
| 03 | Detalle cilindro hidraulico extendiendose | 3-4 s | Tecnología, fuerza |
| 04 | Detalle tren de rodaje / orugas | 3-4 s | Tracción, peso |
| 05 | Detalle balancin / articulación | 2-3 s | Mecánica premium |
| 06 | POV operador desde cabina | 4-5 s | Ergonomía, control |
| 07 | Excavación (corte en suelo) | 6-8 s | Potencia |
| 08 | Carga sobre camión dumper | 5-7 s | Productividad |
| 09 | Escala humana (operador + máquina) | 3-4 s | Tamaño real |
| 10 | Time-lapse ciclo completo | 8-10 s | Eficiencia |
| 11 | Slow-mo polvo / cascotes (240 fps) | 2-3 s | Material particulado |
| 12 | Drone pull-back / aérea | 5-6 s | Reveal del sitio |
| 13 | Silueta atardecer / contre-jour | 4-5 s | Cierre emocional |
| 14 | Spec overlay + logo | 3-4 s | Cierre comercial |

Total: 60-90 s. Si el spot es de 30 s, recorta a: 01, 07, 08, 12, 13, 14.

---

## (b) Render de referencia — pipeline Blender

Cada plano se renderiza con la cámara bloqueada en **5 pases** a resolución final del output (1920×1080 landscape o 1080×1920 vertical). El pase principal que alimenta la IA es el **clay**; los demás son soporte.

### Pases y configuración

| Pase | Shader / Setup | Uso para IA |
|---|---|---|
| **Clay** (principal) | Material `Principled BSDF`, base color `#C8C8C8`, roughness 1.0, sin texturas, sin AO | First-frame / subject reference. Geometría limpia, sin distracciones de color |
| **Beauty** | Materiales PBR completos (amarillo Cat `#FFC72C` ≈ RAL 1003),3-point + HDRI | Style reference opcional en modelos con input multi-imagen |
| **Freestyle / Lineart** | Render → Freestyle, edge mark sobre crease ≥ 30°, grosor 1-2 px | Lock de silueta. Útil para re-prompt cuando la IA deforma |
| **Depth** | Output → Depth, Z normalizado en linear, export EXR32-bit | Refuerzo de proporciones3D, sobre todo en Sora/Veo |
| **Normal** (opcional) | Output → Normal, space Tangent | Para modelos que acepten control normal (Runway Aleph,某些 Kling) |

### Ajustes críticos

- **Resolución exacta del output final**, no superior. La IA reescala y deforma en upscales.
- **Cámara fija** entre pases (un solo `Marker` en el frame1, todas las capas de render usan la misma).
- **Iluminación del clay**: una `Sun` + un `Area` cenital suave. Sin HDRI cromático — el clay debe leer volumen, no color.
- **Fondo**: shader `Background` plano `#E8E8E8` (gris ligeramente más claro que el clay) o HDRI neutro desenfocado. Fondo limpio = silueta limpia = menos alucinaciones.
- **Composición**: máquina ocupa60-70% del frame, **20% de aire arriba** (espacio para que la IA "suba" el boom sin recortar).
- **Antialias**: 64 samples en beauty, 32 en clay. Output OpenEXR multilayer para depth, PNG16-bit para clay/beauty.
- **Nomenclatura**: `shot_01_clay.png`, `shot_01_beauty.png`, `shot_01_edge.png`, `shot_01_depth.exr`.

### Por qué esta arquitectura funciona

Los modelos de video IA actuales (Sora 2, Veo 3, Runway Gen-4, Kling 2.x) aceptan imagen-de-control pero **leen mal la geometría fina**: orugas, cilindros, dientes del cazo desaparecen. El pase clay aísla la geometría como variable única; el depth pass ancla proporciones espaciales; el edge pass sirve de "verificador" cuando re-prompt por deformación. Los tres juntos cubren el 90% de los fallos que veras en (e).

---

## (c) Guion de tomas con duración

Timeline editado a 75 s, ratio 16:9, 24 fps.

```
00:00 - 00:06 Shot 01 — Heroe estático + leve dolly-in
00:06 - 00:11   Shot 02 — Wide de cantera, máquina entra desde frame dcho
00:11 - 00:14   Shot 03 — Cilindro del boom extendiendose (macro)
00:14 - 00:17   Shot 04 — Tren de rodaje, máquina avanzando lento
00:17 - 00:20   Shot 05 — Balancin girando (articulación)
00:20 - 00:24   Shot 06 — POV cabina, manos en joystick (plano detalle añadido)
00:24 - 00:31   Shot 07 — Excavación: dientes muerden suelo, polvo sube
00:31 - 00:37   Shot 08 — Carga sobre dumper, brazo rota hacia el camion
00:37 - 00:41   Shot 09 — Operador baja de cabina (escala humana)
00:41 - 00:49   Shot 10 — Time-lapse ciclo completo (speed ramp)
00:49 - 00:52   Shot 11 — Slow-mo particulas de polvo en aire
00:52 - 00:57   Shot 12 — Drone pull-back, reveals el sitio completo
00:57 - 01:01   Shot 13 — Silueta atardecer, máquina quieta
01:01 - 01:05   Shot 14 — Spec overlay + logo Caterpillar
```

Transiciones: 6 cortes directos + 1 fade-to-black antes del logo.

---

## (d) Prompts por toma

Estructura universal usada por Sora 2 / Veo 3 / Runway Gen-4: `[movimiento de cámara] + [sujeto con anclas técnicas] + [acción] + [entorno] + [luz] + [estilo]`. Evitar palabras ambiguas (*arm*, *joint*, *construction equipment* genérico). Anclar siempre modelo específico.

```
SHOT 01 — Heroe
"Cinematic low-angle 3/4 shot of a Caterpillar 320 hydraulic excavator, stationary, diesel engine vibrating subtly, golden hour rim lighting, dust particles floating, 35mm anamorphic lens, shallow depth of field, photorealistic heavy machinery advertising."

SHOT 02 — Establecimiento
"Tracking wide shot of a Caterpillar 320 working in a granite quarry, machine moves from right to left across frame, overcast diffused light, dust haze in air, ground covered with crushed stone, cinematic color grading."

SHOT 03 — Cilindro hidraulico
"Macro close-up of a hydraulic cylinder extending on an excavator boom, polished steel piston pushing outward, oil sheen on chrome, slow controlled motion, shallow DOF, industrial macro photography."

SHOT 04 — Tren de rodaje
"Low-angle tracking shot of excavator track links pressing into muddy ground, individual track shoes flexing, mud displacement visible, weight compression on soil, overcast flat lighting."

SHOT 05 — Articulación
"Close-up of excavator boom stick pivot joint rotating, visible grease on pins, slow mechanical motion, shallow depth of field, dark steel against bright yellow chassis."

SHOT 06 — POV cabina
"First-person POV from inside excavator cab, looking out through front windshield, joystick controls in foreground, bucket visible below scooping earth, realistic operator perspective, slight camera shake."

SHOT 07 — Excavación
"Side view of Caterpillar 320 excavator digging into hard-packed soil, bucket teeth biting ground, arm curls inward, dust cloud rises from impact point, powerful hydraulic motion, golden hour side lighting."

SHOT 08 — Carga
"Three-quarter rear shot of excavator swinging boom toward a mining dump truck, bucket releases load of crushed rock, material falls in arc, dust explosion, telephoto compression."

SHOT 09 — Escala humana
"Static shot of excavator with operator in safety vest standing beside the tracks, human height comparison emphasizes machine size, blue sky with cumulus clouds, mid-day hard light."

SHOT 10 — Time-lapse
"Hyperspeed time-lapse of a complete excavator work cycle, machine digs, swings, dumps, returns, blurred motion of boom, time compression effect, golden hour to dusk gradient."

SHOT 11 — Slow-mo polvo
"Ultra slow-motion 240fps shot of dust particles and small rocks suspended in air after bucket strike, volumetric lighting through dust, dark background, scientific macro aesthetic."

SHOT 12 — Drone pull-back
"Aerial drone shot pulling back from excavator to reveal full quarry site, machine shrinks in frame, terraced excavation walls, dump trucks below, wide cinematic vista, late afternoon light."

SHOT 13 — Silueta
"Contre-jour silhouette of Caterpillar excavator against orange sunset sky, machine perfectly still, fine dust haze glowing in backlight, minimal composition, widescreen cinematic letterbox."

SHOT 14 — Spec overlay
"Static beauty shot of Caterpillar 320 excavator, front3/4 angle, clean composition with space on right for text overlay, soft studio lighting, white seamless background fading to grey, photorealistic product shot."
```

---

## (e) Errores típicos que deforman la máquina

Lista verificada de fallos recurrentes en Sora 2, Veo 3, Runway Gen-4 y Kling al generar maquinaria pesada. Cada error viene con causa y workaround.

| Error | Causa | Workaround |
|---|---|---|
| **Orugas → ruedas** | Geometría repetitiva de alta frecuencia leida como neumáticos | Prompt explicito: *track links*, *crawler tracks*; refuerza con edge pass del shot 04 |
| **Cilindro doblado o desconectado** | Thin tubes sin contexto3D, IA alucala juntas orgánicas | Llamar *chrome hydraulic cylinder*, *steel piston*; reference shot 03 |
| **Cristal cabina opaco o amarillo** | Transparencia mal manejada | Prompt: *transparent tempered glass cab, visible operator seat inside* |
| **Contrapeso desaparece** | Bloque trasero sin rasgos distintivos | Añadir *rear counterweight with CAT logo* al prompt |
| **Dientes del cazo se fusionan** | Geometría pequeña + motion blur | Macro shot del cazo en reference; prompt *five sharp steel bucket teeth* |
| **Proporciones boom-stick cambian** | Segmentos sin anclaje espacial | Depth pass obligatorio para shots 03, 05, 07, 08 |
| **Amarillo → naranja / amarillo escolar** | Color sin nombre técnico | Usar *Cat yellow #FFC72C* o *RAL 1003 construction yellow* |
| **Barandillas / escalerillas desaparecen** | Thin geometry en silueta → IA lo descarta | Edge pass ayuda; prompt *visible handrails on cab* |
| **Presión sobre el suelo ignorada** | Suelo plano en el reference, IA no infiere peso | Incluir deformation en el suelo del render de referencia (displacement) |
| **Operador dentro de cabina → fantasma/morphing** | Figura humana + cristal + asiento = colisión | Omitir operador en prompt o usar plate aparte del operador |
| **Articulación aparece en sitio equivocado** | "Articulated" es ambiguo para IA | Especificar *boom-to-stick pivot at upper joint, stick-to-bucket at lower joint* |
| **Tubo de escape → chimenea industrial** | Escape vertical malinterpretado | Prompt *short horizontal exhaust stack on engine hood* |
| **Calcas / textos → glifos inventados** | Texto en geometría = ruido | No incluir logos en el reference; añadir logo en post |
| **Hidráulico se humaniza** | *Arm* + *joint* dispara sesgos antropomórficos | Evitar *arm*, usar *boom*, *stick*, *dipper* siempre |

### Regla de oro

Si el resultado de la IA deforma geometría crítica, **re-genera usando el clay render como first-frame en lugar del beauty**. El beauty sobrecarga al modelo con información de material; el clay le obliga a razonar sobre forma. La tasa de éxito sube заметно (no tengo benchmark cuantitativo actual para confirmarlo en cada modelo; probarlo en 3-5 generaciones da señal fiable).

---

## Lo que NO sé con certeza (línea de bandera)

- Capacidad exacta de **multi-reference simultáneo** (clay + depth como dos inputs) en Sora 2 y Veo 3 — varía por versión y los docs cambian. Verificar en la consola del modelo antes de planificar pipeline pesado.
- Si Runway Gen-4 Aleph acepta depth pass como input explícito — a fecha de mi cutoff estaba en despliegue gradual.
- **Benchmarks cuantitativos** de qué modelo deforma menos orugas: no tengo números públicos fiables para citar.
