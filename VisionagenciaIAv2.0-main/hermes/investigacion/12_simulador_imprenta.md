# Simulador de Imprenta Maquiladora — Banco de Práctica

## (a) Modelo de la planta

### Flujo orden → entrega (10 etapas)

```
Cotización → Recepción de archivos → Preprensa (preflight + imposición + prueba)
   → Salida de placas/clisés (CTP / láser) → Tinta (mezcla Pantone)
   → Prensa (offset / flexo / digital) → Acabados (barniz, laminado, hot stamping, relieve)
   → Suaje / corte → Empaque (encajado, etiquetado, retractilado) → Embarque
```

Cada etapa puede re-injectar al flujo (retrabajo). Realimentaciones típicas: preprensa → prensa (archivo mal), prensa → acabados (color fuera de especificación), acabados → empaque (raya en barniz).

### Tiempos y merma — rangos reales (no inventados)

| Etapa | Tiempo de proceso | Makeready / setup | Merma de arranque |
|---|---|---|---|
| Preprensa: preflight | 30 min – 4 h | 0 | 0 |
| Imposición | 15 min – 1 h | por trabajo | 0 |
| CTP plancha offset | 3 – 8 min / plancha | 5 min | 0 |
| Clisé flexo (láser) | 20 – 60 min / clisé | 10 min | 0 |
| Mezcla tinta Pantone | 5 – 15 min / color | 5 min | 200 – 500 g |
| Prensa offset 4 colores (Heidelberg/Komori) | 10 000 – 18 000 sph | 30 – 75 min | 200 – 500 hojas |
| Prensa flexo 8 colores (Mark Andy / Nilpeter / Bobst) | 100 – 300 m/min | 20 – 50 min | 50 – 200 m |
| Prensa digital 4/0 (HP Indigo / Xeikon) | 4 000 – 7 000 sph | 5 – 15 min | 10 – 50 hojas |
| Barniz UV sectorizado | 5 000 – 8 000 sph | 10 – 20 min | 50 – 100 hojas |
| Laminado | 3 000 – 6 000 sph | 15 – 30 min | 50 – 100 hojas |
| Hot stamping | 1 500 – 3 000 sph | 20 – 40 min | 30 – 80 hojas |
| Suaje (corte + doblez) | 4 000 – 7 000 sph | 15 – 30 min | 50 – 150 hojas |
| Encuadernación (plegado, grapado, hot melt) | 1 000 – 3 000 / h | 20 – 60 min | 1 – 3 % |
| Empaque (encajado + retractilado) | variable | 5 – 15 min | < 0.5 % |
| Embarque (carga + ruta) | n/a | 30 – 60 min | n/a |

`sph` = sheets per hour. Las cifras para CTP, prensa y digital vienen de catálogos públicos de Heidelberg, Komori, HP Indigo, Mark Andy. Las de merma son rangos típicos de imprentas comerciales en operación normal — no garantizados.

### Cuellos de botella típicos (los 5 más comunes)

1. **CTP / salida de placas** — capacidad dura 30 – 60 planchas / turno. Una sola torre CTP bloquea toda la planta si se cae.
2. **Prensa monoparental** — un formato (ej. 75×106 cm) sólo lo hace una máquina. Toda la programación se subordina a ella.
3. **Línea de barniz UV** — típicamente una. Si tiene sectorizado o reserva, cola sistemática.
4. **Troqueladora de cajas plegadizas** — el cambio de suaje es 15 – 30 min y a veces hay que esperar el suaje del proveedor.
5. **Embarque fin de mes** — pico estacional (10× el flujo normal en algunas casas). Genera WIP que envejece y retrabajos.

### Variabilidad para alimentar la simulación

- Tiempo de proceso: log-normal, CV 5 – 15 %.
- Setup: distribución triangular (mejor, probable, peor). Ej. prensa offset: (20, 35, 75) min.
- Fallas: exponencial. MTBF prensa offset 80 – 200 h, prensa digital 40 – 100 h, suaje 50 – 150 h. MTTR 30 – 90 min.
- Arribos de órdenes: Poisson no homogéneo. Pico de fin de mes y fin de trimestre (en comercial); en etiquetas, semanal más uniforme.
- Reproceso: 3 – 8 % de las órdenes regresan al menos una vez (defecto, archivo, material).

---

## (b) Fichas de puesto

Para cada uno: **decisiones → datos → herramienta → ritmo → conocimientos en orden de aprendizaje**.

### 1. Planner Junior

- **Decide:** secuencia de órdenes por máquina, fecha de inicio, agrupación por afinidad (sustrato/tinta), tamaño de buffer.
- **Datos que usa:** backlog de OT, capacidad por máquina (velocidad + horas disponibles), matriz de afinidad de setup, fechas prometidas, restricciones de material.
- **Herramienta:** en la realidad: PrintVis, EFI Pace, Microsoft Dynamics, Kanban, Excel avanzado. En el simulador: módulo de secuenciación.
- **Ritmo:** 5 – 15 OT / día re-secuenciadas; publica programa cada 24 h o cada turno.
- **Conocimientos que mezcla y orden en que se aprende:**
  1. Lectura de OT y ficha técnica (formato, sustrato, tintas, acabados, fecha).
  2. Capacidades de máquina (velocidad nominal, formato, gramajes aceptados, número de tintas máx).
  3. Cálculo de tiempo estándar = makeready + run + finish.
  4. Precedencias entre procesos (preprensa → prensa → acabados → empaque).
  5. Reglas de despacho: FCFS, EDD (fecha más próxima), SPT (más corto primero), CR (Critical Ratio = tiempo restante / trabajo restante).
  6. **Matriz de afinidad de setup** (mismo sustrato y misma paleta de tintas = cambio de 20 min en vez de 75).
  7. **Teoría de Restricciones (Goldratt)** — identificar el recurso cuello.
  8. **Drum-Buffer-Rope** — programar al ritmo del cuello, proteger un buffer antes y después, "cuerda" para liberar órdenes nuevas.
  9. Capacidad finita vs. infinita (el ERP normalmente planifica a capacidad infinita; el planner debe ajustar).
  10. Manejo de WIP y edad de órdenes.
  11. Trato con ventas y proyectos: cuándo decir "no" a una fecha, cómo proponer alternativa.

### 2. Gerente de Proyectos

- **Decide:** qué proyectos acepto, fecha promesa al cliente, márgenes, escalaciones.
- **Datos:** cotización, costo estándar, capacidad futura, lead time por etapa, histórico de OTIF por cliente, riesgo por complejidad (número de acabados, color crítico).
- **Herramienta:** CRM (Salesforce, HubSpot), MIS/ERP (EFI, PrintVis), Excel para forecast.
- **Ritmo:** 5 – 20 cuentas activas; 1 – 3 cotizaciones nuevas / día.
- **Conocimientos que mezcla y orden:**
  1. Lectura de cotización y descomposición de costo (sustrato, tinta, proceso, margen).
  2. **OTIF y Fill Rate** por cliente (no basta con "entregar a tiempo", hay que entregar "completo y a tiempo").
  3. Lead time interno por tipo de trabajo (etiqueta, caja, comercial).
  4. Curva de aprendizaje del proyecto (primera vez cuesta 30 % más).
  5. Negociación con cliente sobre fechas realistas y costo de rush.
  6. Análisis de causa raíz cuando se falla (5 Whys, Pareto).
  7. P&L del proyecto (margen bruto, contribución, costo de oportunidad).
  8. Portafolio de proyectos (matriz de priorización: margen × complejidad × riesgo).

### 3. Compras

- **Decide:** qué comprar, a quién, cuánto, cuándo, cómo almacenar.
- **Datos:** catálogo de sustratos, lead time de proveedores, MOQ, calidad de material, histórico de consumo, precios negociados.
- **Herramienta:** ERP (módulo compras), Excel para evaluación de proveedores, plataformas (Alibaba para consumibles, Mercado Libre industrial en LATAM, Papeles y conversión para sustrato).
- **Ritmo:** 5 – 20 OC / semana; 1 – 3 RFQ / semana.
- **Conocimientos que mezcla y orden:**
  1. Catálogo de sustratos (couché, bond, kraft, polipropileno, BOPP, cartulina, cartón corrugado) por calibre y aplicación.
  2. **Lead time real vs. lead time cotizado** (siempre 20 – 30 % mayor).
  3. MOQ (cantidad mínima de orden) y lote económico (EOQ).
  4. Calidad de material entrante (espec, gramaje, humedad).
  5. **JIT vs. stock de seguridad** para cada familia (sustrato crítico: stock; tinta: JIT).
  6. **Análisis ABC** de inventario (20 % de SKUs = 80 % del valor).
  7. Negociación con proveedores (volumen, plazo, calidad, penalización).
  8. **Total Cost of Ownership** (no sólo precio unitario, sino flete, merma, devolución).
  9. Evaluación periódica (scorecard: precio, OTIF proveedor, calidad, respuesta).

### 4. Operador de Prensa (offset / flexo / digital)

- **Decide:** velocidad, ajustes de tinta, registro, cuándo detener, aprobación de primera hoja buena.
- **Datos:** ficha técnica de la OT, estándares de color (ISO 12647-2, G7, Pantone), densidad objetivo, registro, merma autorizada.
- **Herramienta:** densitómetro (X-Rite eXact, Techkon SpectroDens), espectrofotómetro, prensa, control de tinta (viscosímetro).
- **Ritmo:** una prensa produce 1 OT cada 30 min – 4 h según tamaño.
- **Conocimientos que mezcla y orden:**
  1. Operación segura de la prensa (engranes, solventes, atrapamientos).
  2. Montaje de plancha y mantilla.
  3. Registro de color (front-to-back, lado a lado).
  4. Densidad de tinta y trapping.
  5. Balance de agua/tinta (offset) o viscosidad/anilox (flexo).
  6. Aprobación de primera hoja buena y firma de OK de arranque.
  7. **Manejo de merma** — contar, registrar, justificar.
  8. Solución de problemas en marcha (marca de estrella, ganancia de punto, moteado, ghosting).
  9. Mantenimiento autónomo (limpieza, lubricación, inspección).
  10. **SMED** (Single-Minute Exchange of Die) — distinguir setup interno (máquina parada) de externo (máquina corriendo).

### 5. Calidad

- **Decide:** liberar, retener, rechazar, devolver; aprobar primera hoja; auditar proceso.
- **Datos:** especificación del trabajo, tolerancias (∆E, densidad, registro), plan de muestreo, histórico de no conformidades.
- **Herramienta:** espectrofotómetro, densitómetro, calibre, regla, lupa, software de QC (X-Rite ColorCert, Barbieri).
- **Ritmo:** 1 – 3 inspecciones / hora en producción + auditoría por turno.
- **Conocimientos que mezcla y orden:**
  1. Especificación de la OT (rango de tolerancia por variable).
  2. Instrumentos: cómo medir, calibrar, mantener.
  3. **CIE Lab, ∆E (Delta E)**: qué es aceptable (< 2 para comercial, < 1.5 para empaque).
  4. **Muestreo AQL** (Acceptable Quality Level): MIL-STD-1916, ISO 2859-1.
  5. **SPC (Statistical Process Control)** — cartas X̄-R, cartas p, detectar causa especial vs. común.
  6. **ISO 12647-2** (offset) y **G7** (calibración de prensa).
  7. Análisis de causa raíz: 5 Whys, Ishikawa.
  8. CAPA (Corrective and Preventive Action) — cerrar no conformidades.
  9. Costos de calidad (prevención, appraisal, falla interna, falla externa).

### 6. Acabados

- **Decide:** secuencia de acabados, ajustes de registro, aprobación de primera pieza.
- **Datos:** especificación de la OT, plano de suaje, tipo de barniz, sustrato, número de pasadas.
- **Herramienta:** troqueladora (Bobst, Heidelberg, Sanwa), barnizadora UV, laminadora, encuadernadora.
- **Ritmo:** 2 000 – 7 000 sph según operación.
- **Conocimientos que mezcla y orden:**
  1. Lectura de plano de suaje (corte, doblez, perforación, hendido).
  2. Montaje de suaje en máquina (registro, presión, timing).
  3. Registro de barniz / laminado / hot stamping (front-to-back, tensado de película).
  4. Tolerancias dimensionales y visuales.
  5. **Tiempo de armado** (cambio de suaje = 15 – 30 min; cambio de cliché hot stamping = 20 – 40 min).
  6. Merma de material (desecho de suaje, retiro de bordes).
  7. Solución de problemas (corte incompleto, doblez desviada, burbuja en laminado, registro corrido).
  8. Mantenimiento de suajes (afilado, limpieza, almacén).
  9. SMED en acabados (operaciones externas: traer suaje, preparar foil; internas: montar, ajustar).

### 7. Logística

- **Decide:** consolidación de embarques, ruta, transporte, layout de almacén.
- **Datos:** OT listas para embarque, dirección, peso, volumen, urgencia, costo de transporte, capacidad de camión.
- **Herramienta:** WMS, ruteo (Google Maps, Mapbox, optiRoute), Excel.
- **Ritmo:** 1 – 3 embarques / día; ruteo diario.
- **Conocimientos que mezcla y orden:**
  1. Layout de almacén (recepción → producción → embarque).
  2. Empaque primario, secundario, terciario.
  3. Consolidación de embarques (LTL vs. FTL, grupaje).
  4. **Ruteo** (vecino más cercano, optimización).
  5. Costo de transporte por km y por kg.
  6. Documentación: remisión, factura, packing list, carta porte.
  7. Lead time de promesa al cliente (diferencia entre "en planta" y "entregado").
  8. Trazabilidad de lote (recuperar un lote y dar con sus materiales, prensa, turno, operador).

### 8. Puesto que casi siempre se olvida: Ventas / Servicio al cliente

- **Decide:** qué promete, a qué precio, a qué cliente.
- **Datos:** capacidad futura, margen, histórico del cliente, complejidad.
- **Herramienta:** CRM, catálogo, plantillas de cotización.
- **Ritmo:** 1 – 5 cotizaciones / día.
- **Conocimientos en orden:** lectura de RFQ, descomposición de costo, lead time realista, margen mínimo, reglas de descuento, manejo de queja, upselling.

---

## (c) Indicadores — global y por puesto

### Globales (la planta completa)

| Indicador | Fórmula | Target world-class | Target realista | Frecuencia |
|---|---|---|---|---|
| **OEE** | Disponibilidad × Rendimiento × Calidad | ≥ 85 % | 60 – 75 % | Turno / semana |
| Disponibilidad | Tiempo operativo / tiempo programado | ≥ 95 % | 85 – 92 % | Turno |
| Rendimiento | Velocidad real / velocidad nominal | ≥ 95 % | 80 – 90 % | Turno |
| Calidad (First Pass Yield) | Unidades buenas / unidades producidas | ≥ 99 % | 95 – 98 % | Turno |
| **OTD** (On Time Delivery) | Entregas a tiempo / total entregas | ≥ 98 % | 90 – 95 % | Semana / mes |
| **OTIF** (On Time In Full) | Entregas completas a tiempo / total | ≥ 97 % | 85 – 93 % | Mes |
| **Merma** | Kg o unidades desechadas / producido | < 2 % | 3 – 6 % | Semana |
| **WIP** (Work In Process) | Unidades en proceso / capacidad | < 3 días de producción | 5 – 10 días | Diario |
| **Costo por millar (CPM)** | Costo total / unidades × 1 000 | depende del producto | baseline ± 5 % | Por OT |
| **Throughput time** | Tiempo total desde entrada a preprensa hasta embarque | < 5 días para comercial | 7 – 15 días | Por OT |
| **Setup ratio** | Tiempo de setup / tiempo total programado | < 15 % | 20 – 35 % | Semana |
| **Fill Rate** | Líneas entregadas completas / líneas pedidas | ≥ 98 % | 92 – 96 % | Mes |

### Por puesto

- **Planner Junior:** OTD, OTIF, WIP, edad de la orden más vieja, utilización del cuello de botella, número de re-secuenciaciones / día.
- **Gerente de Proyectos:** OTIF por cliente, margen por proyecto, número de escalaciones, varianza fecha promesa vs. fecha real.
- **Compras:** Lead time real vs. cotizado, OTIF de proveedores, costo de inventario, porcentaje de compras urgentes (rush), scorecard ABC.
- **Prensa:** OEE, FPY, merma de arranque, velocidad real vs. nominal, número de paros no programados, tiempo de setup vs. estándar.
- **Calidad:** FPY, número de no conformidades / millón de unidades (DPMO), ∆E promedio, porcentaje de retrabajo, cierre de CAPA en plazo.
- **Acabados:** FPY, merma, tiempo de setup, número de paros, First Piece Right.
- **Logística:** OTIF logística, costo de transporte / kg, tiempo de carga, ocupación de camión, exactitud de inventario.
- **Ventas:** Conversión de cotización a orden, margen promedio, tiempo de respuesta de cotización.

---

## (d) Diseño del simulador

### Datos de entrada de una orden real (lo que carga el usuario)

```json
{
  "id": "OT-2026-00134",
  "cliente": "ACME S.A.",
  "producto": "Caja plegadiza 30 ml serum",
  "tiraje": 50000,
  "sustrato": {
    "tipo": "cartulina_sbs",
    "gramaje_g_m2": 300,
    "ancho_mm": 720,
    "largo_mm": 1020,
    "proveedor_habitual": "P-014"
  },
  "tintas": {
    "num": 4,
    "paleta": "CMYK",
    "especiales": ["barniz_uv_sectorizado", "hot_stamping_oro"]
  },
  "repeticion_en_plancha": 6,
  "hojas_por_ot": 8333,
  "acabados": ["barniz_uv", "laminado_brillante", "suaje", "encajado"],
  "calidad": {
    "estandar": "ISO_12647-2",
    "delta_e_max": 2.0,
    "densidad_objetivo": {"C": 1.45, "M": 1.40, "Y": 1.20, "K": 1.70}
  },
  "fecha_promesa": "2026-10-15",
  "fecha_entrada": "2026-09-25",
  "prioridad": 3,
  "costo_objetivo_millar_usd": 45,
  "ruta_preferida": ["prensa_2", "barniz_uv_1", "laminadora_1", "suaje_1", "empaque_1"],
  "ruta_alternativa": ["prensa_3", ...],
  "muestra_aprobada": true,
  "restricciones": ["no_lunes_antes_9am", "solo_operador_certificado_K"]
}
```

Este JSON es el contrato. Cargas N OTs y la simulación corre.

### Motor: simulación de eventos discretos (DES)

**Por qué DES y no otra cosa:** el sistema tiene colas, recursos compartidos, variabilidad y decisiones de secuenciación. Sólo DES captura bien la interacción. Un solver de programación lineal entera (ILP) te da el óptimo estático pero no la variabilidad; una heurística greedy no te da la dinámica. DES te da las dos cosas.

**Herramientas por nivel:**

| Nivel | Herramienta | Costo | Para qué sirve |
|---|---|---|---|
| Prototipo | **SimPy** (Python) | gratis | DES rápida, integrable con el resto del banco |
| Investigación | **Mesa** (Python, agent-based) | gratis | modelar decisiones de cada puesto como agente |
| Industrial | **Arena** (Rockwell) | licencia | estándar de la industria, animación 3D |
| Industrial alto nivel | **AnyLogic** | licencia | multi-método (DES + agent-based + SD) |
| Industrial Siemens | **Plant Simulation** | licencia | si la planta ya usa Siemens |
| Open source UI | **Salabim** (Python) | gratis | animación 2D built-in |

**Para este simulador recomiendo:** SimPy como motor + una UI en Streamlit o Panel. Si se requiere animación, Salabim. Si el cliente paga, Arena.

### Estructura del motor (módulos)

1. **Generador de órdenes** — lee JSONs de OTs, las inyecta al sistema según la distribución de arribos.
2. **Recursos** — cada máquina con sus parámetros (velocidad nominal, MTBF, MTTR, setup matrix, calendarización).
3. **Colas** — por recurso, con disciplina elegible (FCFS, EDD, SPT, CR, prioridad).
4. **Reglas de decisión por puesto** — el planner decide secuencia, el operador de prensa decide velocidad, etc. Esto se modela como función que el motor llama.
5. **Generador de variabilidad** — RNG con semillas para reproducibilidad (esto es crítico para el aprendizaje: mismo escenario, distintas decisiones, comparar).
6. **Recolector de KPIs** — por evento y por intervalo.
7. **Visualizador** — Gantt de planta, gráfica de Gantt por máquina, KPIs en tiempo real, log de decisiones.

### Cómo se muestra al aprendiz si su decisión estuvo bien o mal

Cinco mecanismos, todos juntos:

1. **Delta a óptimo.** El motor corre la misma OT con la regla de secuenciación óptima (ILP o regla heurística fuerte) y reporta la brecha. Ej: "Tu OEE fue 62 %, el óptimo en este escenario era 78 %. Brecha: 16 pp."
2. **Scorecard por turno.** KPIs del aprendiz vs. target world-class y vs. su propio histórico.
3. **Replay lado a lado.** Mismo escenario, dos decisiones. Se ve la planta con la decisión A y la planta con la decisión B animadas en paralelo.
4. **Atribución de costo.** Cada decisión se traduce a pesos/dólares. "Tu secuencia generó 4 horas extra de setup → MXN 12 800 de merma adicional."
5. **Causa raíz automática.** Cuando se falla OTIF, el motor identifica el evento que disparó la cadena. "El atraso se originó porque la prensa #2 se paró a las 14:32 por falla de mantilla y la OT-00134 no tenía buffer."

Para el aprendizaje lo más útil es el **replay con delta a óptimo** porque hace visible el costo de la decisión sin sermonear.

---

## (e) Proyectos reales por puesto (del más fácil al más difícil)

Cada proyecto: **problema → dato que necesita → resultado medible**.

### Planner Junior

1. **Agrupar por afinidad de sustrato en la secuencia semanal.**
   - Problema: cambios de bobina de 30 min cada uno.
   - Dato: matriz de afinidad de sustratos + backlog semanal.
   - Resultado: reducción de 20 – 35 % del tiempo total de setup.

2. **Implementar Drum-Buffer-Rope en el cuello de botella.**
   - Problema: el cuello se muere de hambre o se satura.
   - Dato: utilización del cuello, buffer actual antes y después.
   - Resultado: throughput +10 – 20 % y WIP -25 %.

3. **Reducir la edad de la orden más vieja en backlog.**
   - Problema: hay OTs de 30 días sin tocar.
   - Dato: timestamp de entrada y última operación por OT.
   - Resultado: 95 % del backlog con edad < 10 días.

4. **Política de rush: cuántos rush acepto por semana sin colapsar la planta.**
   - Problema: ventas mete 5 rush por semana y todo se atrasa.
   - Dato: histórico de OTs rush y su impacto en OTD.
   - Resultado: política publicada (ej. "máximo 2 rush por turno") con costo de rush explícito.

### Gerente de Proyectos

1. **Cuadrar OTIF por cliente (no global).**
   - Problema: el OTIF global oculta clientes con 70 %.
   - Dato: OTIF segmentado por cliente.
   - Resultado: lista de clientes con OTIF < 90 % y plan de acción.

2. **Curva de costo del primer trabajo vs. repetido.**
   - Problema: se cotiza todo al mismo costo.
   - Dato: tiempo y merma de la primera vez vs. la repetida.
   - Resultado: recotización de prototipos con margen correcto.

3. **Márgenes reales por tipo de producto.**
   - Problema: el margen agregado dice 18 % pero hay productos en 2 %.
   - Dato: costo real (no estándar) por OT.
   - Resultado: discontinuar o re-cotizar lo que da margen < 8 %.

### Compras

1. **Aceptar el inventario ABC y reducir el stock de clase C.**
   - Problema: mucho dinero en materiales que rara vez se usan.
   - Dato: consumo histórico por SKU durante 12 meses.
   - Resultado: stock clase C -40 % con OTIF de planta sin cambio.

2. **Reducir compras urgentes (rush) de 20 % a 8 %.**
   - Problema: el planner pide rush porque no hay material.
   - Dato: lead time real vs. cotizado por proveedor.
   - Resultado: reasignación de proveedores o ajuste de políticas.

3. **Scorecard trimestral de proveedores.**
   - Problema: "siempre le compro al mismo" sin evidencia.
   - Dato: precio, OTIF, calidad, tiempo de respuesta.
   - Resultado: documento publicado, cambio de proveedor si aplica.

### Prensa

1. **SMED en prensa: pasar de 45 min de makeready a 25 min.**
   - Problema: 35 % del tiempo programado es setup.
   - Dato: video y cronómetro del setup actual, separar interno de externo.
   - Resultado: setup -20 – 45 %, capacidad efectiva +15 %.

2. **Reducir merma de arranque de 350 a 200 hojas por cambio.**
   - Problema: la primera media hora del tiro sale mal.
   - Dato: conteo de hojas malas en arranque por prensa.
   - Resultado: First Good Sheet más rápido, merma -30 %.

3. **Estandarizar la firma de "OK de arranque" con densitómetro.**
   - Problema: a veces se arranca sin medir densidad.
   - Dato: densidad de la primera hoja vs. objetivo.
   - Resultado: 0 % de arranques sin firma de calidad.

4. **Programa de mantenimiento autónomo del operador.**
   - Problema: fallas por suciedad, falta de aceite, calibración perdida.
   - Dato: bitácora de fallas, MTBF por causa.
   - Resultado: -30 % de paros no programados.

### Calidad

1. **Implementar AQL en recepción de sustrato.**
   - Problema: llegan bobinas defectuosas que se descubren en prensa.
   - Dato: plan de muestreo + histórico de no conformidades.
   - Resultado: -50 % de no conformidades por material.

2. **Carta de control X̄-R en densidad de tinta CMYK por prensa.**
   - Problema: la densidad se va bailando en el turno.
   - Dato: lecturas de densitómetro cada 500 hojas.
   - Resultado: detectar causa especial antes de que se acumulen 5 000 hojas malas.

3. **Certificación G7 de una prensa.**
   - Problema: inconsistencia de color entre prensas.
   - Dato: caracterización de prensa con espectrofotómetro, curva TVI.
   - Resultado: ∆E entre prensas < 1.5.

4. **Cerrar CAPA de las 10 no conformidades más frecuentes en 90 días.**
   - Problema: las mismas no conformidades se repiten.
   - Dato: Pareto de no conformidades del último año.
   - Resultado: -50 % de recurrencia.

### Acabados

1. **SMED en troquel: pasar de 25 a 12 min de cambio de suaje.**
   - Problema: la troqueladora pasa 30 % del tiempo cambiando.
   - Dato: video y cronómetro del cambio, separar interno y externo.
   - Resultado: capacidad +20 %.

2. **Reducir First Piece Wrong en barniz UV de 8 % a 1 %.**
   - Problema: la primera hoja barnizada sale mal.
   - Dato: registro de inspección de primera pieza.
   - Resultado: setup ajustado, merma -60 %.

3. **Almacén de suajes: cada suaje con su OT histórica.**
   - Problema: tardamos 20 min en encontrar el suaje.
   - Dato: tiempo de búsqueda por orden de suaje.
   - Resultado: tiempo de búsqueda < 3 min, base de datos digital.

### Logística

1. **Consolidar embarques: pasar de 8 envíos/semana a 4.**
   - Problema: muchos envíos pequeños, alto costo por kg.
   - Dato: lista de embarques de 3 meses con destino, peso, costo.
   - Resultado: -20 – 30 % costo de transporte, sin afectar OTIF.

2. **Cross-docking en embarques de fin de mes.**
   - Problema: el almacén se llena y luego se vacía.
   - Dato: edad de OTs y fecha de embarque.
   - Resultado: almacén funcionando al 70 % de su capacidad.

3. **Ruteo optimizado de últimas 3 rutas del día.**
   - Problema: el chofer decide por intuición.
   - Dato: direcciones, ventanas de entrega, capacidad.
   - Resultado: -15 % km, -20 % tiempo de ruta.

### Ventas

1. **Plantilla de cotización que detecte automáticamente si una fecha es realista.**
   - Problema: ventas promete fechas imposibles.
   - Dato: capacidad futura en planta por tipo de trabajo.
   - Resultado: tasa de cumplimiento de fecha promesa > 95 %.

2. **Recotizar 5 productos con margen < 8 % o eliminarlos.**
   - Problema: hay productos que dan pérdida.
   - Dato: costo real por OT de los últimos 6 meses.
   - Resultado: margen promedio del portafolio +3 pp.

---

## (f) Qué se puede construir primero

### Fase 0 — Hoja de cálculo (1 – 2 semanas)

Lo que se hace en Excel / Google Sheets sin código:

1. **Catálogo de máquinas** con parámetros (velocidad, formato, setup estándar, MTBF).
2. **Catálogo de sustratos** (tipo, gramaje, costo, proveedor, lead time).
3. **Lista de OTs reales** con todos los campos del JSON de arriba.
4. **Calculadora de tiempo estándar** = makeready + run + finish.
5. **Gantt manual en Excel** con formato condicional (una fila por máquina, barras por OT).
6. **Dashboard de KPIs** con tablas dinámicas que se actualizan a mano.
7. **Matriz de afinidad de setup** (qué combinaciones de sustrato/tinta son rápidas).

**Lo que NO se puede en Excel:** simular variabilidad, comparar N decisiones sobre el mismo escenario, generar Delta a óptimo, reproducir exactamente el mismo escenario.

### Fase 1 — Python con SimPy (1 – 2 meses)

Lo mínimo viable técnico:

1. **Modelo DES en SimPy** con 3 máquinas (prensa, barniz, suaje) y un cuello de botella.
2. **Generador de OTs** que lee un CSV o JSON.
3. **Reglas de secuenciación** seleccionables (FCFS, EDD, SPT, CR, afinidad).
4. **Recolector de KPIs** que exporta a pandas DataFrame.
5. **Visualización** con matplotlib o plotly (Gantt de planta, curvas de WIP, histogramas de tiempo de ciclo).
6. **Comparador de escenarios**: misma semilla, dos reglas → ver el delta.
7. **UI mínima en Streamlit** para que el aprendiz cargue OTs y vea el resultado.

**Stack recomendado:**

```
SimPy          ← motor DES
pandas         ← manejo de datos
plotly / matplotlib ← gráficas
Streamlit      ← UI web
openpyxl       ← leer Excel de OTs reales
pytest         ← pruebas
```

### Fase 2 — Python + UI + persistencia (2 – 4 meses)

- Base de datos (SQLite al inicio, Postgres si crece).
- Múltiples puestos (no sólo planner).
- Decisión por turno (el aprendiz decide, no sólo la regla).
- Animación de planta con Salabim o Plotly Dash.
- Sistema de score y ranking (opcional, si se quiere gamificar).
- Catálogo de proyectos reales ligado a cada puesto.

### Fase 3 — App de producción (6 – 12 meses)

- Web app con React/Vue + backend Python (FastAPI).
- Multi-usuario con roles.
- Persistencia en Postgres.
- Conexión a ERP real (si se quiere modo "shadow" contra la planta).
- Analytics avanzado (ML para predecir fechas, detectar anomalías).
- Mobile-friendly para que el operador de prensa vea su programa en el piso.

### Costo y tiempos aproximados (honestos)

| Fase | Esfuerzo | Resultado |
|---|---|---|
| 0 — Excel | 1 persona, 1 – 2 semanas | banco de datos y KPIs básicos |
| 1 — Python SimPy | 1 dev, 1 – 2 meses | simulador de un solo puesto (planner) |
| 2 — Multi-puesto + UI | 2 devs, 2 – 4 meses | simulador completo de los 7 puestos |
| 3 — App producción | 3 – 4 devs, 6 – 12 meses | producto comercializable |

No tengo datos de mercado actualizados 2025 – 2026 de cuánto cuesta un proyecto así en México o LATAM. Los precios de software DES comerciales (Arena, AnyLogic) típicamente van de 5 000 a 30 000 USD por licencia anual; no los he verificado para 2026.

---

## Lo que no sé y declaro como supuesto

- **Cifras de mercado 2025 – 2026 de OTIF, OEE, merma para imprentas maquiladoras en México o LATAM**: no tengo datos actualizados. Los rangos que doy son típicos de la industria a nivel global y de mi conocimiento hasta 2024.
- **Costos reales por millar en 2026**: altamente variables según país, volumen, sustrato y energía. Los rangos que doy son referenciales, no cotizables.
- **Benchmarks específicos de alguna imprenta maquiladora real** (Smurfit Kappa, WestRock, Grupo Gondi, Gráficos Corona, etc.): no los cito porque no los tengo verificados.
- **Precios de licencias Arena, AnyLogic, Plant Simulation en 2026**: no los he confirmado.
- **Normativa mexicana específica (NOMs aplicables a imprentas)**: no incluida; recomiendo consulta con un asesor regulatorio si se requiere.
- **Idiomas de la UI**: el diseño está en español, pero las técnicas (SMED, TOC, OEE, AQL) son universales.
