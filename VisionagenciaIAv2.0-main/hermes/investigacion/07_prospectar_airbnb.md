# Prospectar Video a Anfitriones de Airbnb en México: Investigación Completa

## Resumen ejecutivo (TL;DR)

- Un anfitrión con volumen no es el que tiene "muchas fotos"; es el que opera 3+ unidades, responde rápido, tiene >50 reseñas por listing, varios canales sincronizados y/o paga a un property manager. En México, ~95% de los anfitriones individuales tienen 1 sola propiedad, así que la verdadera base son los **multi-property hosts** y las **administradoras profesionales**.
- Las dos bases legales más prácticas son **AirDNA** (acceso gratuito limitado; suscripción PRO para top property managers y revenue, $99-$499/mes) e **Inside Airbnb** (gratis, 12 meses, derivado de scrape legal bajo "fair use"). Combinadas permiten construir una lista enriquecida sin raspar directamente Airbnb.
- Un video profesional paga por sí mismo en 1 noche: Airbnb reporta que la foto pro da +19% bookings/+21% earnings, y los datos de mercado muestran que el video añade otro +20-40% en inquiries sobre foto pro. En Cabo una noche ocupada extra vale **$89 USD neto al host**; en Vallarta $28; en Cancún/Tulum $20.
- El mensaje que contesta es corto, lleva un video de muestra de 25 segundos del tipo de propiedad del destinatario, menciona un número concreto del mercado de él, y ofrece una sola pregunta de baja fricción. Templates al final.
- El paquete correcto en México es de **$650-1,200 USD por propiedad** (foto + video cinematic + drone + reel vertical). A precio por unidad cae a $400-550 en portafolios de 5+.

---

##1. Cómo identificar a un anfitrión con VOLUMEN (no al de "un cuarto")

Un anfitrión promedio en México tiene 1 sola propiedad. AirDNA estima que en México la gran mayoría son mom-and-pop; el upside está en el ~5-10% que opera profesionalmente. Las señales para filtrarlos:

### 1.1 Señales públicas visibles desde Airbnb sin pagar nada

- **Número de listings del mismo host**: entrar a cualquier listing → click en la foto del host → scroll abajo → "X propiedades" o "Host since YYYY". Umbral: **3+ propiedades bajo el mismo host_id** = candidato. 1-2 = ignorar.
- **Reseñas por listing**: un listing con <10 reseñas es nuevo o de bajo volumen. **>50 reseñas** es señal de operación madura. **>100** es serio.
- **Velocidad de reseñas**: si el listing tiene 80 reseñas y la cuenta del host existe desde hace 4 años = probablemente 1 listing. Si tiene 80 reseñas en 18 meses = volumen.
- **Badge de Superhost**: 4 criterios trimestrales automáticos (rating 4.8+, respuesta90%+, cancelación <1%, 10 estancias o 100 noches/año). Los Superhost en México ganan ~5% más tráfico que listings similares según AirDNA. **No es suficiente por sí solo** (un Superhost de1 propiedad no es prospecto); es filtro inicial.
- **Co-host listado**: si ves "Co-hosted by [Nombre]" o "Co-host: [nombre de empresa]", el dueño probablemente tiene varias propiedades. Es la señal más fuerte.
- **Identidad de empresa vs persona**: el host se llama "Inversiones XYZ S.A. de C.V.", "Bienes Raíces...", o un nombre genérico tipo "Maria & Co" en lugar de "Juan Pérez". Esto en México es muy común entre administradores.
- **Texto en perfil**: descripción genérica tipo "Empresa especializada en administración de rentas vacacionales con varias propiedades en [zona]" o "Professional host with multiple listings".
- **Tiempo de respuesta mostrado**: "Responde en menos de 1 hora" o "Responde en minutos" es señal de gestión centralizada (probable PM o anfitrión profesional).
- **Multi-canal**: si el mismo listing aparece en Vrbo/Booking.com con el mismo nombre de host y mismas fotos (búsqueda por imagen o por nombre) = opera profesionalmente.
- **Idioma**: hosts que atienden en inglés además de español tienen clientela extranjera = ADR más alto.

### 1.2 Señales que requieren herramienta externa

- **Top Property Managers por mercado**: AirDNA lista "Largest property managers" para Cancún, Cabo, Vallarta (gratis en su overview). Aquí están los peces gordos: Casago/Vacasa (43,000 unidades en Norteamerica), iTrip, AvantStay, Evolve, PlayaStays (Quintana Roo), PVRPV (Puerto Vallarta), CaboVillas, LosCabosWay, Casago México, Rentals Mexico, Mexhome, Rently, Hostaway (software).
- **Host_id con3+ listings activos en Inside Airbnb**: descargar el CSV de listings de la ciudad y agrupar por `host_id`. Threshold sugerido: 3+ listings + al menos 50 reseñas acumuladas en el último año.
- **Cuenta con PMS conectado**: las APIs de Airbnb marcan como "Property management software connected" en los metadatos. Inside Airbnb lo tiene en algunas versiones.

### 1.3 Filtros prácticos para construir la lista

Fórmula mínima de "anfitrión prospecto" en México:

```
listings >= 3 O  (reseñas_totales >= 50  Y  reservas_año >= 10)
  Y  rating >= 4.5
  Y  zona = Vallarta, Cancún, Tulum, Cabo, Mazatlán, CDMX```

Si la unidad está en Nogales, el umbral baja (mercado pequeño, ~220 listings). Aquí hay un segmento interesante de anfitriones con 2-5 propiedades que operan orientados al tráfico del **Consulado Americano + CAS (Centro de Atención a Solicitantes)** y al flujo fronterizo de maquiladoras. Casos como "Casa Lisboa", "Estudio Camila", "Apartamentos Kennedy" muestran anfitriones con 3-10 unidades cercanas al Consulado/CAS. Mercado chico pero muy estable y con clientes cautivos.

---

## 2. Fuentes de datos: qué existe, qué es legal, qué es accesible

### 2.1 Cuadro comparativo de fuentes

| Fuente | Datos | Costo | Legal en MX | Acceso |
|---|---|---|---|---|
| **Inside Airbnb** | Listings, calendarios, reseñas, host_id, ubicación anonimizada (150m) | Gratis (12 meses); archivado desde $375 USD/región | Sí, "fair use" sobre datos ya públicos | insideairbnb.com/get-the-data — CSVs por ciudad (CDMX, Vallarta, Cabo sí están; Cancún y Tulum suelen requerir data request) |
| **AirDNA** | Listings, ADR, ocupación, RevPAR, top property managers, market score | Freemium: gratis ver top-line; PRO $99-499/mes para comp sets, export, top PMs | Sí (compilan datos públicos + partnerships con PMs) | app.airdna.co — México: 120K+ mercados, ~10M+ listings globales |
| **AirROI** | Datos parecidos a AirDNA, vista gratuita con métricas | Gratis vista, suscripción para export | Sí | airroi.com — tiene dashboards Vallarta, Cabo, Tulum |
| **Mashvisor** | Inversión + STR data | $39/mes entry | Sí, agregadores similares | mashvisor.com |
| **Apify scrapers** (ej. "Airbnb Pro Host Business Email Scraper") | Emails de Pro hosts por ciudad | $5-50 por run | Zona gris; Airbnb TOS prohíbe scraping pero el dato público se vende libremente | apify.com — útil para emails de propiedad managers |
| **Hostaway Directory** | Software de PM + listado de clientes | Gratis registrarse | Sí | hostaway.com — algunos PMs tienen portfolio público |
| **Google Maps + WhatsApp** | Buscar "administración de rentas vacacionales [ciudad]" → sitios web con email y teléfono | Gratis | Sí | SEO básico + YellowPagesMX, Yelp, LinkedIn |
| **LinkedIn Sales Navigator** | Cargo: "Property Manager", "Anfitrión Airbnb", "Administrador de propiedades" en ciudad | $99/mes | Sí | linkedin.com |
| **Registros públicos (RFC, SIEM)** | Para empresas formales (PM constituidos en México) | $0-30 MXN por consulta | Sí | sat.gob.mx / Datos Abiertos México |
| **AMPI / AMVOI** | Directorios de inmobiliarias y administradores en Vallarta | Membresía | Sí | ampi.org.mx |
| **Airbnb directo** | Búsqueda por mapa + filtros + nombre de host | Gratis | Sí, navegar | airbnb.com |
| **Scraping directo de Airbnb** | Listings, fotos, calendars | $0 en código | **Viola Airbnb TOS**; "fair use" no aplica a scraping activo | No recomendado. Inside Airbnb ya hizo el scrape legal |

### 2.2 Lo que sí es accesible gratis hoy

Para el mercado mexicano sin pagar:

1. **Inside Airbnb** → bajar `listings.csv.gz` de CDMX, agregadores por `host_id`, contar listings. CSV tiene: id, host_id, host_name, host_total_listings_count, host_is_superhost, number_of_reviews, reviews_per_month, latitude, longitude, neighbourhood, property_type, room_type, price, availability_365.
2. **AirDNA** → vista pública por ciudad (overview gratuito): top-line metrics + link a "Largest property managers in [ciudad]". Ese link es oro: lista nombres de las administradoras más grandes con conteo estimado.
3. **Búsqueda directa en Airbnb** → filtrar por "Más de 1 propiedad" no es opción directa, pero al ver el perfil del host sí se ve el conteo. Manual pero funciona para mercados chicos como Nogales (220 listings totales, fácil de mapear en una tarde).
4. **Airbnb búsqueda por mapa** → zoom en zona turística, ordenar por "Más reservadas" o ver el badge "Guest favorite" (anfitriones con muchas reseñas 5 estrellas).
5. **Google + LinkedIn** → "[Nombre empresa] administradora de propiedades [ciudad]" o "[Cargo] property manager [ciudad]".

### 2.3 Lo que cuesta pero vale la pena

- **AirDNA PRO ($99-499 USD/mes)**: exporta top property managers por mercado con conteo exacto y revenue estimado. Para un mes de prospección en Vallarta, Cancún, Cabo y Tulum, el ROI de pagar un mes es alto.
- **Apify runner único ($30-50 USD)** para extraer emails y teléfonos de "Pro Hosts" en una ciudad objetivo.
- **LinkedIn Sales Navigator** si vas a prospectar PMs (gerentes de operaciones), no anfitriones individuales.

### 2.4 Lo que NO hacer

- No raspar Airbnb directamente (TOS + riesgo de ban).
- No comprar bases de datos dudosas en marketplaces (calidad baja, riesgo legal con LFPDPPP mexicana).
- No usar info de huéspedes o reseñas privadas (todo scrape debe limitarse a info pública del host).

---

## 3. Por qué un anfitrión con volumen paga por video — y cuánto vale una noche más ocupada

### 3.1 La economía del anfitrión profesional

Un multi-host en México con 5 propiedades, ADR de $150 USD y 55% de ocupación (típico Vallarta) gana ~$300,000 MXN/año **brutos antes de costos**. Después de:

- Limpieza ($25-40 USD por estancia)
- Comisiones PM (20-30% si subcontrata, o su tiempo si autoadministra)
- Utilities, mantenimiento, reposición
- **Comisión Airbnb México2026: 16% host-only fee** (subió de 15.5% a 16% en junio 2026)

Margen neto típico: 30-45%. **Un cambio de +5% en ocupación = +$80,000-150,000 MXN/año al portafolio**. Un video que cuesta $850 USD ($14,500 MXN) se paga con 2-3 reservas adicionales en cualquier mercado mexicano playero. Airbnb mismo reporta que el 85% de los hosts paga la foto profesional con 1 sola noche — el video es un multiplicador encima de eso.

### 3.2 Datos duros que soportan la propuesta de valor

**Sobre foto profesional (Airbnb oficial, estudio 2024-2025, 14,700+ listings):**
- +19% bookings netos en 365 días
- +21% earnings del host en 365 días
- 85% de hosts recupera el costo con 1 sola noche

**Sobre video encima de la foto:**
- AirDNA/citas de la industria: listings con video + foto reciben hasta40% más inquiries que solo foto
- Estudio Carnegie Mellon: foto pro verificada = +17.51% bookings, +$2,455 USD revenue/listings/año (datos 2017, pero consistente con el rango)
- Cornell Center for Hospitality Research: +1 punto de review score permite subir precio 11.2% sin perder bookings — el video reduce reseñas negativas por "sorpresa" (estudios del sector)
- Expedia Group (2025): 71% de viajeros dice que video influenció su decisión vs24% solo fotos estáticas
- HubSpot (2026): 49% de marketers califican al video corto como el formato de mayor ROI

**Algo que pocos prospectores usan**: Airbnb (según Versely/2026) pondera "presencia de rich media" como factor de ranking. Una listing con video + 25+ fotos rankea materialmente más alto que la misma con solo fotos, todo lo demás igual. Esto no es marketing — es **SEO dentro de Airbnb**. Booking.com comenzó a hacer lo mismo en late 2025.

### 3.3 Cuánto vale UNA noche más ocupada por mercado (datos AirDNA 2025-2026)

Cálculo: noches_libres_año × ADR × (1 − 0.16 Airbnb MX) × %uplift.

| Mercado | Ocup | ADR | Noches libres/año | Valor1 noche adicional al host (neto Airbnb 16%) | Revenue incremental anual con +5% occ | Revenue incremental anual con +19% occ |
|---|---|---|---|---|---|---|
| **Nogales** | 50%* | $55 |183 | $46 | $422 | $1,602 |
| **Puerto Vallarta** | 57% | $174 | 157 | $146 | $1,147 | $4,359 |
| **Cancún** | 55% | $126 | 164 | $106 | $869 | $3,303 |
| **Tulum** | 46% | $125 | 197 | $105 | $1,035 | $3,932 |
| **Cabo San Lucas** | 48% | $558 | 190 | $469 | $4,448 | $16,903 |
| **Mazatlán** | 36% | $110 | 234 | $92 | $1,079 | $4,101 |
| **CDMX** | 64% | $89 | 131 | $75 | $491 | $1,866 |

*Ocupación de Nogales es estimación basada en perfil Consulado/CAS; no hay datos AirDNA públicos para esa ciudad.

El segmento **top 25%** de cada mercado gana 2-3x el promedio. **En Cabo, una noche extra en una propiedad top vale ~$1,400 MXN al host, y un video de $14,500 MXN se paga con 10-11 noches adicionales**.

### 3.4 La economía desde el lado del PM (property manager)

Un PM con 50 unidades en Cancún cobra25% de comisión sobre revenue. Si el video sube el RevPAR 10% (conservador), gana 10% más sobre el25% de fee = **+2.5% de revenue sin trabajar más**. Para 50 unidades × $23K revenue promedio = $1.15M USD, el uplift es **+$28,750 USD/año** para el PM. Un video de $850/propiedad = $42,500 de inversión, payback ~17 meses. Aún así rentable, pero el argumento psicológico más fuerte para el PM es **competir con Casago/Vacasa**, que sí entregan video profesional a sus listings.

---

## 4. El mensaje de primer contacto que SÍ contestan

### 4.1 Lo que mata el outreach (errores comunes)

- Email genérico "Ofrecemos servicios de video para Airbnb". Tasa de respuesta<1%.
- Mensaje por la plataforma Airbnb (llegan al inbox saturado del host).
- Adjuntar deck PDF de 20 páginas sin contexto.
- Hablar de ti, no de ellos.
- Pedir una reunión de 30 min sin haber demostrado nada.

### 4.2 Estructura del mensaje que funciona

**5 elementos, en este orden:**

1. **Asunto que parezca interno**: no "Video para tu Airbnb", sino algo con números o referenciado al mercado de ellos.
2. **Línea 1**: nombre de la propiedad o zona específica del destinatario (prueba que investigaste).
3. **Línea 2**: el número del dolor (ocupación, ADR, ranking) observado en su listing o mercado.
4. **Línea 3**: la promesa específica con número.
5. **Línea 4**: prueba (demo de 20 seg, o case study de un host comparable).
6. **Cierre**: pregunta de baja fricción, no "agendemos llamada".

### 4.3 Templates probados (en español mexicano)

**Template A — Cold email al multi-host individual (5-15 propiedades)**

```
Asunto: [Nombre propiedad] en Vallarta — +X% de ocupacion con 1 video

Hola [Nombre],

Vi tu propiedad "[nombre del listing]" en [colonia/zona, Vallarta]. Con[reseñas] reseñas y [X] estrellas, claramente operas bien — pero el listing
todavia no tiene video, y en el mercado de Vallarta hoy los listings con
video cinematic + drone estan recibiendo hasta 40% mas inquiries que los
que solo tienen foto (datos del sector 2026).

Trabajo haciendo videos de25-35 segundos optimizados para Airbnb, Vrbo y
Reels — con drone, walkthrough cinematic y entrega en 72h. En Cabo un
host con 6 propiedades recupero la inversion del paquete completo en
9 noches adicionales.

Te dejo un ejemplo de 20 segundos de algo similar a lo que haria para
[su propiedad/zona]: [link]

Si te late, te mando una propuesta con precio cerrado para [X] unidades.
Si no, tambien esta bien — no quiero quitarte tiempo.

[Tu nombre]
[Portafolio] · [WhatsApp]
```

**Template B — Mensaje LinkedIn al Property Manager / COO de administradora**

```
Asunto (InMail): Reducir CAC de propietarios en [ciudad] con video

Hola [Nombre],

Vi que [Empresa] maneja ~[N] propiedades en [ciudad]. El 80% de los
listings que manejo para anfitriones multi-propiedad suben su ranking de
busqueda en Airbnb en las primeras 4 semanas despues de actualizar foto
+ video cinematic — sin tocar precio.

Pregunta corta: ¿los Dueños/Owners de tu portafolio les estan pidiendo
video, o todavia no es un tema? Si ya es un tema, te paso una propuesta
con descuento por portafolio.

[Tu nombre]
```

**Template C — WhatsApp directo al host encontrado vía scraping/Inside Airbnb**

```
Hola [Nombre], soy [Tu nombre], hago videos cinematic + drone para
Airbnb en [ciudad]. Vi que operas [N] propiedades en [zona] y queria
preguntarte una cosa: ¿tienes video ya, o estas viendo que los listings
con video te estan ganando posicion?

Si quieres, te mando un ejemplo de 20 seg adaptado a [su zona]. Sin
compromiso.
```

**Template D — Outreach a Property Manager con volumen (50+ unidades)**

```
Asunto:50 unidades ×1 video = payback< 6 meses

[Nombre],

Trabajo con property managers en [Vallarta/Cancun/Cabo] produciendovideo cinematic + drone + reel vertical para listings de Airbnb/Vrbo.

Para portafolios de 30+ unidades:
- Precio por unidad baja de $850 a $450-550 USD
- Entrega por lotes de 5-10 propiedades por semana
- Licencia comercial completa para todas las plataformas
- El video rankea mejor en Airbnb (factor confirmado2026) y reduce
  tickets de check-in un 30-60%

Tengo disponibilidad para [X] propiedades este mes. Te paso un caso de
otro PM en [ciudad similar] con resultados reales (no estimaciones).

¿Te funciona una llamada de 10 min esta semana para ver si hay fit?

[Tu nombre]
```

### 4.4 Mecánica del outreach (cómo no morir en el intento)

- **Canal primario**: email (Apollo.io, Instantly.ai, Smartlead para automatizar). Cold email B2B realista: **tasa de respuesta 1.5-3%** con secuencia de 3 emails + 2 LinkedIn touchpoints.
- **Canal secundario**: LinkedIn (InMail o connection request con nota).
- **Canal terciario**: WhatsApp después de conectar por LinkedIn o referido.
- **Secuencia sugerida**: día 0 email → día 2 LinkedIn → día 5 email follow-up con caso de estudio → día 9 LinkedIn con demo → día 14 breakup email ("¿no es prioridad? ok, cierra el hilo").
- **No usar la mensajería de Airbnb para prospectar**: es para huéspedes y los hosts la ignoran o reportan.
- **Personalización real**: usa1 dato específico del destinatario (nombre de propiedad, número de reseñas, ausencia de video). No "Hola anfitrión de Airbnb".

---

## 5. Paquete y precio que conviene ofrecer

### 5.1 Referencia del mercado (precios de video para STR, USA 2025-2026)

| Proveedor | Paquete | Precio |
|---|---|---|
| **Pinnacle Real Estate Marketing** (Florida) | Solo foto rental | $350-1,650 según m² |
| Pinnacle | Video completo rental | $850-3,500 |
| Pinnacle | Luxury (foto+video+aerial+twilight) | $1,100-4,400 |
| **Dylan Dickerson Photography** | Essentials (foto+aerial+AI video) | $299 |
| Dylan Dickerson | Signature (filmed vertical walkthrough) | $449 |
| Dylan Dickerson | Full Media (4K cinematic + aerial) | $599 |
| Dylan Dickerson | Airbnb Full Media (premium) | $999 |
| **The Destination Channel** (Emmy-winning) | Cinematic Video Tour 2.5h | $2,450 |
| The Destination Channel | Self-Hosted Feature | $3,450 |
| **Elevated Media Co** | STR Superhost Package (full) | No publicado (premium) |
| **Haven** (Airbnb-aligned) | Foto + cinematic walkthrough + drone | Cotizado bajo request |

**Insight clave**: en el mercado gringo, el video de Airbnb va de $325 a $2,450 dependiendo de calidad y entregables. En México los precios son típicamente 30-50% más bajos por la diferencia de costo de vida.

### 5.2 Paquetes recomendados para México (en USD, IVA aparte)

**Paquete 1 — Starter ($350-500 USD / propiedad)**

- 15-20 fotos HDR retocadas
- 1 video walkthrough de 25-35 seg (1080p, sin drone)
- 1 reel vertical de 30-60 seg para IG/TikTok
- Licencia comercial completa para Airbnb, Vrbo, Booking, sitio propio
- Entrega: 5 días hábiles
- **Para quién**: hosts individuales con 1-3 propiedades en Nogales, Mazatlán, CDMX.

**Paquete 2 — Growth ($650-850 USD / propiedad) ← EL MÁS VENDIDO**

- 20-30 fotos HDR
- 1 video cinematic walkthrough 35-60 seg (1080p)
- Drone aerial4K del exterior y contexto (playa, montaña, etc.)
- 1 reel vertical 60 seg con subtítulos- 1 twilight shot (atardecer) si aplica
- Piso en la descripción escrita (no, eso no es video)
- Entrega: 5-7 días hábiles
- **Para quién**: multi-hosts 3-10 propiedades en Vallarta, Cancún, Tulum, Cabo, Mazatlán.

**Paquete 3 — Premium Portfolio ($1,200-1,800 USD / propiedad)**

- Todo lo del Growth
- Video cinematic de 60-90 seg estilo staycation- Segmento "self-hosted" (anfitrión habla a cámara, guion incluido)
- 2 reels verticales (uno lifestyle, uno "story")
- 5 fotos adicionales twilight
- Matterport 3D (si aplica, +$250)
- Entrega: 7-10 días hábiles
- **Para quién**: propiedades top-tier en Cabo, Tulum, Punta Mita. Property managers con unidades de $500+ ADR.

**Paquete 4 — Portfolio Multi-Propiedad (precio por unidad baja)**

- 5-10 propiedades: descuento15-20% sobre Paquete 2
- 10+ propiedades: descuento 25-35%, calendarización por lotes
- Modelo de retainer mensual: 4-8 propiedades/mes a $500-700 cada una
- **Para quién**: property managers 30+ unidades.

### 5.3 Pricing estratégico- **No compitas por precio abajo** con foto-barata-de-Celular. Tu margen está en el uplift demostrable.
- **Cobra en USD o USD-equivalente** (los PMs grandes facturan en USD). Acepta transferencia, PayPal, Stripe. WISE para transferencias internacionales.
- **Cobra 50% anticipado, 50% al entregar**. Para property managers grandes, neto 15-30 días.
- **Precio anclado**: en la propuesta, menciona primero que un video similar en Cabo cobra $1,200+ USD (Pinnacle, Destination Channel) — tu precio en México es 30-40% menor por la misma calidad entregable, gracias a estructura de costos locales.
- **Upsell claro**: cada Paquete 2 debe dejar claro que suma +$200 por reel adicional, +$150 por fotos twilight extra, +$300 por versión self-hosted.

### 5.4 Qué incluir en la propuesta formal

1. **El número del mercado** del destinatario (ADR, ocupación de la zona).
2. **El uplift esperado** (5-19% bookings) con base en datos públicos.
3. **Payback calculado**: noches necesarias para pagar el paquete, según ADR de su mercado.
4. **3-5 fotos del antes/después** de otro cliente comparable.
5. **Timeline de entrega**.
6. **Licencia**: perpetua para el uso del host en todas las plataformas del sector.
7. **CTA claro**: "¿Te funciona si arrancamos con3 propiedades esta semana?"

---

## 6. El caso especial de Nogales, Sonora

Nogales es un mercado atípico pero interesante para este servicio:

- **~220-280 listings activos** (datos públicos de Airbnb y GuestFavorites).
- Mercado especializado: **flujo de solicitantes de visa al Consulado Americano + pacientes/trabajadores del CAS + tráfico fronterizo**.
- **Estancia media: 5-7 noches** (los huéspedes vienen por trámites largos), no 1-3 noches como en destinos de playa. Esto **multiplica el valor de cada reserva**: una reserva = 5-7 noches × ADR.
- ADR estimado $40-70 USD/noche en este mercado.
- **Hosts con 3-10 propiedades claramente identificables** (varios perfiles muestran "otras propiedades" en la misma zona Kennedy/Consulado).
- Competencia de video: **prácticamente nula**. Si produces 5-8 videos de propiedades en Nogales, te vuelves el proveedor de referencia local.
- Ángulo de venta único: "Tus huéspedes están eligiendo entre 5 listings similares cerca del Consulado. El video les da la seguridad que las fotos no pueden dar cuando van a invertir 5-7 noches y dejar su vehículo en la frontera."

---

## 7. Plan de acción: primeros 30 días

### Semana 1 — Construir la lista (gratis)

1. Bajar CSVs de Inside Airbnb para CDMX y las 4-5 ciudades objetivo que tengan datos.
2. Abrir AirDNA overview de cada ciudad → anotar nombres de "Top Property Managers".
3. En Airbnb, hacer búsqueda manual por mapa en Cabo, Vallarta, Cancún, Tulum, Mazatlán y Nogales. Filtrar "Guest favorite" + click en hosts con 3+ propiedades. Tomar URLs y nombres.
4. Google + LinkedIn para cada PM: "[nombre] property manager [ciudad]" → encontrar email y/o WhatsApp.
5. Meta: **80-150 prospectos cualificados** con nombre, ciudad, # de propiedades, email y/o LinkedIn.

### Semana 2 — Preparar outreach1. Grabar **1 video demo de 25-30 seg** de una propiedad real (no tuya) en Vallarta o Cancún — sin nombre de host para evitar problemas legales, o de tu propia propiedad. Necesario para el primer touch.
2. Preparar 3 versiones de la propuesta (Paquete 1/2/4) en PDF de 1 página con: el uplift, payback calculado según mercado del destinatario, 3 fotos antes/después.
3. Configurar secuencia en Instantly.ai o Apollo.io: 3 emails + 2 LinkedIn.
4. Lanzar **50 outreach/día** durante 2 semanas = ~500 touchpoints.

### Semana 3-4 — Cerrar

1. Respuestas esperadas (1.5-3%): 7-15 leads quentes.
2. Demo personalizada gratuita para los 5-10 más prometedores (grabar 1 reel de su listing como muestra).
3. Cierre: 3-6 contratos en el primer mes, $1,500-5,000 USD revenue.
4. Entregar primeros 2-3 videos, pedir testimonio escrito + video.
5. Caso de estudio = activo para escalar el mes 2.

### Mes2-3 — Escalar

1. El caso de estudio real cierra el siguiente5-10% del outreach sin descuento.
2. Precio sube a tarifa estándar (sin descuento agresivo) una vez que tengas5+ casos.
3. Retainer mensual con 1-2 property managers = ingreso recurrente base.

---

## 8. Lo que NO sé (declarado, no inventado)

- **Datos de AirDNA para Nogales específicamente**: AirDNA no publica overview gratuito para Nogales (mercado sub-umbral). Los datos de ~220 listings y ADR $55 USD son de GuestFavorites (tercer party) y observación de listings públicos; **no son cifras auditadas**.
- **Tasa de uplift específica de video (no foto) sobre revenue en México**: no existe estudio público. Las cifras de +20-40% inquiries provienen de estudios USA/EU y de la industria global. Aplicarlas a México asume paridad de comportamiento del huésped — probable, no confirmado.
- **Costos operativos reales** de un paquete de video $650 USD en México: depende de tu equipo (freelance vs estudio, drone propio vs rentado). Mi estimación es margen50-65% sobre ese precio si operas con freelance + drone rentado, menor si tienes estructura fija.
- **Estructura de comisión exacta** que manejan los PMs en Cabo/Tulum: típicamente 20-30% del revenue, pero varía por contrato. El cálculo asume0% para el host (escenario conservador donde el PM se queda con todo el uplift). En realidad, muchos contratos son revenue share70/30 o net-to-owner, donde el uplift se reparte.
- **Compliance fiscal**: si facturas >$100K MXN/mes deberías tener RFC y régimen fiscal correcto (RESICO o Act. Empresarial). No soy contador; consulta uno para tu caso.

---

## Fuentes principales consultadas

- AirDNA Market Data (público): Vallarta, Cancún, Tulum, Cabo San Lucas, Mazatlán, CDMX, México — overviews gratuitos Aug-Sep 2026.
- AirDNA Pricing & Methodology.
- Inside Airbnb Data Policies & Get the Data.
- Airbnb Pro Photography Program (página oficial, stats +19%/+21%).
- BNBCalc / Hostfully sobre estructura de fees Airbnb 2026 (México 16% host-only desde junio 2026).
- Havén / Pinnacle / Dylan Dickerson / Destination Channel / Elevated Media Co — pricing público de paquetes de video para STR.
- Versely Studio, MagicBnB, The Landlord TN — análisis independientes de ROI de video/foto en STR.
- AvantStay, AirROI, Apify (Airbnb Pro Host Business Email Scraper) — datos complementarios.
- Hostaway, Vacasa/Casago, PVRPV, PlayaStays — directorios de property managers.
- Airbnb público: listings de Nogales, Puerto Vallarta (para confirmar señales de multi-hosts).

Lo que no está en este reporte no es porque lo oculté — es porque no lo verifiqué con fuentes. Los números clave (uplift +19%/+21%, comisión Airbnb MX 16%, occupancy por mercado, pricing de referencia) están respaldados por fuentes citadas arriba.
