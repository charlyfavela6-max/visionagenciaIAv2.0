# Nexus — Llevar "Crear Video Completo" de Claude Code a una plataforma web propia

> Mapeo del proceso manual que hoy corre como sesión conversacional con un agente (guion → voz → imágenes → video → subtítulos → render) a un sistema asíncrono, durable y observable dentro de Nexus.

---

## (a) Arquitectura que conviene

### Pieza por pieza

```
┌─────────────┐    POST /jobs ┌──────────────┐
│  Nexus Web  │ ─────────────────► │  API Gateway │
│  (Next/Remix)│ │  (FastAPI)   │
└─────────────┘ ◄── 202 + job_id  └──────┬───────┘
                                          │ enqueue
                                          ▼ ┌──────────────────────┐
                              │  Cola durable │
                              │  (Temporal/Inngest/  │
                              │   BullMQ+S3+Postgres)│
                              └──────────┬───────────┘
                                         │ poll / dispatch HTTP
                                         ▼
                              ┌──────────────────────┐
                              │  Worker pool │
                              │  (Node o Python)     │
                              │  - tts-worker        │
                              │  - image-worker │
                              │  - video-worker      │
                              │  - render-worker     │
                              │  corriendo en K8s/ECS│
                              └──────────┬───────────┘
                                         │
 ▼
                              ┌──────────────────────┐
                              │  Almacenamiento      │
                              │  S3 / R2 │
                              │  (assets, drafts,    │
                              │   final render)      │
                              └──────────┬───────────┘
                                         │
 ▼
                              ┌──────────────────────┐
                              │  Postgres            │
                              │  jobs / steps /      │
                              │  artifacts / usage  │
                              └──────────────────────┘
```

**Componentes clave con nombres concretos:**

- **Orquestador**: el motor que mantiene la ejecución viva entre llamadas a APIs externas. Tres opciones viables y una recomendación:
  - **Temporal** (self-host o Temporal Cloud). Engine de workflows durable con replay determinístico. SDK Go/Java/TS/Python/.NET/PHP/Ruby. Persiste event history en Postgres/Cassandra/MySQL. Workflows pueden correr horas o meses. Limitación: el código del workflow debe ser determinístico (replay semantics).
  - **Inngest** (SaaS o self-host). Serverless-first, event-driven, HTTP-callable. Step memoization nativo: pasos completados NO se re-ejecutan en retry. Diseñado específicamente para cargas AI. Sin workers que mantener. Tiene `step.run()`, `waitForEvent()`, `debounce`, rate limiting per-key, bulk replay.
  - **Trigger.dev** (SaaS o self-host v3). Similar a Inngest pero con modelo de "tasks" más explícito. Buena DX para TypeScript. Pricing por "actions" (5 activities pueden consumir 15-20 actions).
  - **BullMQ + Postgres + Redis** (low-level). Cola Node madura pero requiere que TÚ escribas el state machine de pasos completados, idempotencia por paso, y la lógica de skip-on-retry. Más superficie operacional, menos abstracción.

- **Recomendación pragmática para Nexus**: **Inngest** o **Temporal**, no BullMQ puro. La razón concreta que da la industria:

 > "If your incident log is mostly 'job vanished,' you have a queue problem. If it's mostly 'job ran twice' or 'pipeline half-completed and we had to write a reconciliation script,' you have an orchestration problem."

  Un pipeline de video toca 5-7 APIs externas de pago. Si la API de voz cobró y luego el worker muere, NO quieres re-cobrarla. Quieres que el orquestador sepa "voz ya fue generada, archivo en s3://bucket/abc/narration.mp3, salta al siguiente paso."

- **Cola / broker**: Redis (si vas BullMQ/Celery), Postgres (si vas Temporal), o el event store de Inngest.

- **Workers**: procesos separados del API server. Stateless. Pueden correr en:
  - K8s (EKS/GKE) con HPA por queue length
  - ECS Fargate para tareas largas
  - Railway/Fly.io si quieres simplicidad
  - **RunPod Serverless / Modal / fal.ai** para pasos GPU (image/video gen)
  - Workers spot con handler de interruption (guardar checkpoint a S3 + reencolar)

- **Webhook receiver**: endpoint público `POST /webhooks/{provider}` con verificación HMAC-SHA256 (todos los proveedores de video serios lo soportan hoy). Dedupe por `event_id` en Redis o tabla Postgres con índice único.

- **Modelo de estado del job** (state machine durable):

```
accepted → preparing → queued
  ├─ script_generation (LLM)
  ├─ voice_synthesis (TTS API)
  ├─ image_generation (image API, paralelo por escena)
  ├─ video_generation (video API, paralelo por escena)
  ├─ subtitle_generation (Whisper o similar)
  ├─ composition (FFmpeg local o Shotstack/MpegFlow)
  └─ final_render (FFmpeg, posiblemente GPU)
                 → completed | failed | partial (con costo reservado)
```

Cada paso tiene `status: pending | running | succeeded | failed | skipped`, `attempts`, `idempotency_key`, `cost_reserved`, `cost_charged`, `started_at`, `finished_at`, `output_artifact_ids`.

### Por qué esto es el patrón correcto para video específicamente

- Generar un clip de 8s toma 30-90 segundos. Una cadena completa toma 5-30 minutos. **HTTP request/response síncrono NO funciona** (timeouts de 30-60s en gateways).
- Workers deben poder **morir y ser reemplazados** sin perder progreso.
- APIs externas tienen **rate limits** y **capacity outages**. Necesitas backpressure.
- Cobro es por evento exitoso, no por intento. **Idempotencia al nivel de provider call es obligatoria.**

---

## (b) Orquestación de la cadena guion → voz → imagen → video → subtítulos → render

### Diseño del workflow (pseudocódigo en estilo Inngest/Temporal)

```typescript
// Workflow: createFullVideo
async ({ event, step }) => {
  const { brief, userId, jobId } = event.data;

  // ── PASO 1: Guion (LLM) ─────────────────────────────
  const script = await step.run('generate-script', async () => {
    return await llm.generateScript(brief); // GPT-5 / Claude
  }, { idempotencyKey: `job:${jobId}:script` });

  // ── PASO 2: Storyboard (LLM, paralelo) ──────────────
  const storyboard = await step.run('generate-storyboard', async () => {
    return await llm.splitIntoScenes(script);  // 5-10 escenas
  }, { idempotencyKey: `job:${jobId}:storyboard` });

  // ── PASO 3: Voz (TTS API) ────────────────────────────
  const narration = await step.run('synthesize-voice', async () => {
    return await elevenLabs.generate(script.fullText, voiceId);
 }, {
    idempotencyKey: `job:${jobId}:voice`,
    timeout: '5m',
    // No re-cobrar si el provider ya facturó
  });

  // ── PASO 4: Imágenes por escena (PARALELO con fan-out) ─  const sceneImages = await Promise.all(
    storyboard.scenes.map((scene, idx) =>
      step.run(`image-${idx}`, async () => {
        return await flux.generate(scene.prompt);
      }, { idempotencyKey: `job:${jobId}:img:${idx}` })
    )
  );

  // ── PASO 5: Video por escena (PARALELO con fan-out) ──
  // Aquí: image-to-video usando cada imagen + narración como guía
  const sceneVideos = await Promise.all(
    sceneImages.map((img, idx) =>
      step.run(`video-${idx}`, async () => {
        return await veo.runway.kling({ image: img.url, prompt: storyboard.scenes[idx].prompt, audio: narration.url, duration: sceneDuration });
      }, { idempotencyKey: `job:${jobId}:vid:${idx}` })
    )
  );

  // ── PASO 6: Subtítulos (Whisper / provider) ───────────
  const subtitles = await step.run('generate-subtitles', async () => {
    const result = await openai.audio.transcriptions.create({
      file: narration.audioUrl,
      model: 'whisper-1',
      response_format: 'verbose_json',
      timestamp_granularities: ['word'],
    });
    return formatAsSRT(result);
  }, { idempotencyKey: `job:${jobId}:subs` });

  // ── PASO 7: Composición final ───────────
  const finalVideo = await step.run('compose-final', async () => {
    // Concatenar clips, quemar subtítulos, mezclar narración + música
    return await shotstack.render({
      timeline: { tracks: [
        { clips: sceneVideos.map(v => ({ asset: v.url, start: v.start, length: v.duration })) },
        { clips: [{ asset: narration.url, type: 'audio' }] },
        { clips: subtitles.map(s => ({ type: 'caption', text: s.text, start: s.start, end: s.end, style: brandStyle })) }
      ]},
      output: { format: 'mp4', resolution: '1080p' }
    });
  }, { idempotencyKey: `job:${jobId}:render` });

  // ── PASO 8: Notificación final ───────────
  await step.run('notify-user', async () => {
    await notifyUser(userId, { jobId, videoUrl: finalVideo.url });
  });

  return { jobId, videoUrl: finalVideo.url };
}
```

### Patrones de orquestación críticos

| Patrón | Por qué importa | Implementación |
|--------|----------------|----------------|
| **Step memoization** | No re-cobrar al provider si el step ya corrió | Inngest nativo, Temporal via event history |
| **Idempotency-Key por step** | Si el worker muere post-API-call pero pre-DB-write, retry no duplica cobro | Header `Idempotency-Key: UUIDv4` en TODA llamada POST al provider |
| **Fan-out / fan-in** | 5-10 escenas en paralelo, después recoger | `Promise.all` sobre `step.run()` |
| **Webhook callback** | APIs de video demoran 30-90s, no hacer polling abierto | Worker hace `POST /videos` → recibe `task_id` → termina. Provider hace POST a `https://nexus.app/webhooks/provider?task=X` cuando esté listo |
| **Backpressure / queue cap** | Evitar que 1 cliente mande 1000 jobs y bloquee a todos | Por workspace: `concurrency_limit + queued_jobs_limit`. Sume expone este patrón explícitamente |
| **Priority preemption** | P0 (pago premium) salta la cola de P2 (free tier) | `priority` field en queue, drain de workers lower-priority |
| **Spot interruption handler** | 80% del fleet en spot; si AWS te avisa 2 min antes, guardar checkpoint | Handler SIGTERM → escribe `current_step`, `s3_prefix` a Postgres → reencolar |

### Estado en la base de datos (Postgres)

```sql
CREATE TABLE jobs (
  id UUID PRIMARY KEY,
  workspace_id UUID NOT NULL,
  user_id UUID NOT NULL,
  status TEXT NOT NULL, -- accepted|preparing|queued|rendering|validating|completed|failed
  brief JSONB,
  total_cost_cents INT DEFAULT 0,
  cost_reserved_cents INT DEFAULT 0,
  cost_charged_cents INT DEFAULT 0,
  workflow_run_id TEXT,        -- Inngest/Temporal run id
  created_at, started_at, finished_at,
  error JSONB
);

CREATE TABLE job_steps (
  id UUID PRIMARY KEY,
  job_id UUID REFERENCES jobs(id),
  step_name TEXT,              -- 'voice_synthesis', 'image-3', etc.
  status TEXT,
  attempts INT DEFAULT 0,
  idempotency_key TEXT UNIQUE,
  provider TEXT,               -- 'elevenlabs', 'flux', 'veo'
  provider_job_id TEXT,        -- id devuelto por el provider
  cost_cents INT,
  input_artifact_ids UUID[],
  output_artifact_ids UUID[],
  started_at, finished_at,
  error JSONB
);

CREATE TABLE artifacts (
  id UUID PRIMARY KEY,
  job_id UUID REFERENCES jobs(id),
  step_id UUID REFERENCES job_steps(id),
  kind TEXT,                  -- 'image'|'video'|'audio'|'subtitle'|'final'
  s3_key TEXT,
  metadata JSONB              -- duración, resolución, etc.
);
```

Índice crítico: `CREATE INDEX ON job_steps (idempotency_key);` para evitar doble cobro en race conditions.

---

## (c) Qué se llama por API y qué necesita máquina propia

### Decisión por etapa del pipeline

| Etapa | ¿API externa o propia? | Por qué | Proveedores concretos | Costo aprox. |
|-------|------------------------|---------|----------------------|--------------|
| **Guion (LLM)** | API externa | No vale la pena self-host para volumen variable | OpenAI GPT-5, Anthropic Claude, Together AI | $0.005-$0.05 por guion típico |
| **Voz (TTS)** | API externa | ElevenLabs SOTA y costo por char es competitivo; self-host de XTTS/Coqui es caro en GPU | ElevenLabs, Cartesia, LMNT, PlayHT | ElevenLabs API: $0.05-$0.10/1K chars. ~$0.17/min en escala Pro |
| **Imágenes** | API externa (con fallback GPU propio para volumen alto) | FLUX/Kosten son baratos en serverless; self-host solo si >100K imgs/mes | fal.ai, Replicate, BFL FLUX.2, Midjourney (vía third-party) | FLUX.2 [klein] $0.014/imagen; [max] $0.07; Kontext [pro] $0.04 |
| **Video clips** | API externa (casi siempre) | Self-host de modelos de video (Wan, CogVideoX) requiere A100/H100 y todavía pierde calidad | Veo 3.1, Runway Gen-4.5, Kling 3.0, Seedance, Sora 2 | Veo 3.1 Lite $0.03-$0.08/s; Standard $0.40/s; Runway $0.12/s; Sora 2 $0.10/s (deprecated24-Sep-2026) |
| **Subtítulos** | API externa (Whisper) | $0.006/min API vs. self-host con GPU NVIDIA ($276+/mes mínimo) | OpenAI Whisper, AssemblyAI Universal-2 | Whisper $0.006/min ($0.36/hr); AssemblyAI $0.15/hr |
| **Composición final (FFmpeg)** | **MÁQUINA PROPIA** | Tú controlas el filter graph, quemas subtítulos, mezclas audio. Contratar Shotstack por cada render es 5-10x más caro a escala | EC2/RunPod con FFmpeg; o servicio como Shotstack/MpegFlow para evitar DevOps | Self-host: c5.xlarge $0.20/hr o spot $0.06/hr. Shotstack ~$0.05-$0.20 por render |
| **Transcoding final / HLS / múltiples bitrates** | **MÁQUINA PROPIA con NVENC** | x264 medium en CPU: 2 min para 5 min de video. NVENC: 12 s. Hardware accel corta costos 4x | EC2 g4dn.xlarge (T4) o self-host con NVENC | AWS MediaConvert $0.015/min 1080p; self-host ~$0.004/min con spot |

### Tu máquina propia

Lo que sí o sí necesitas en infraestructura propia:

1. **API server** (FastAPI/Express) — stateless, escala horizontal.
2. **Worker pool** con auto-scaling (K8s HPA o ECS). Cada worker es stateless.
4. **Render workers** con FFmpeg instalado y opcionalmente GPU NVENC. Instancias spot al 80% del fleet.
5. **Postgres** (RDS o Neon) para estado durable.
6. **Object storage** (S3 / R2 / GCS) para assets intermedios y finales. Lifecycle policy: borrar drafts a 7 días.
7. **Redis** (Upstash o Elasticache) si vas BullMQ, o para cache de idempotency keys.
8. **Webhook endpoint público** con verificación HMAC y dedupe.

### Lo que NO necesitas en máquina propia (al inicio)

- LLMs. Costo prohibitivo de GPUs vs. API.
- Modelos de generación de imagen/video. Self-host no paga hasta >100K imgs/mes o >5K seg-video/mes.
- TTS de calidad. ElevenLabs SOTA, self-host (Coqui/XTTS) pierde calidad显著.

### Referencia de costo de infraestructura propia (AWS, lectura actual)

| Componente | Spec | Costo on-demand | Costo con reserved/spot |
|------------|------|-----------------|------------------------|
| Worker CPU-only | c5.xlarge 4vCPU/8GB | $0.192/hr | spot $0.06/hr |
| Worker GPU (NVENC) | g4dn.xlarge T4 | $0.526/hr | spot $0.18/hr |
| Worker Graviton | c7g.2xlarge | $0.181/hr | spot ~$0.05/hr |
| RDS Postgres | db.r6g.large | $0.24/hr | reserved1y ~$0.14/hr |
| Redis (Upstash) | Pay-per-request | ~$0.20/100K reqs | n/a |
| S3 | 500TB drafts + 50TB final | ~$11K/mes si retiene 30 días | con lifecycle ~$4K |
| fal.ai H100 serverless | n/a | $1.89/hr on-demand, $4.49/hr B300 | n/a |

---

## (d) Costo y reintento cuando un paso falla

### Pricing por paso (referencia actualizada, todas son API list prices leídas ago-2026)

| Servicio | Modelo | Unidad | Costo | Costo por video de 60s con 8 escenas |
|----------|--------|--------|-------|--------------------------------------|
| ElevenLabs Multilingual v2 | TTS API | por 1K chars | $0.10 | ~$0.06 (600 chars × 8 escenas) |
| OpenAI Whisper | STT API | por minuto | $0.006 | ~$0.006 (1 min de audio) |
| FLUX.2 [dev] | Image API | por imagen | $0.025-0.05 | $0.20-$0.40 (8 imágenes) |
| Veo 3.1 Lite 720p | Video API | por segundo | $0.03 | $1.92 (8 clips × 8s) |
| Veo 3.1 Standard 1080p | Video API | por segundo | $0.40 | $25.60 |
| Runway Gen-4.5 | Video API | por segundo | $0.12 | $7.68 |
| Sora 2 (720p, deprecated24-Sep-2026) | Video API | por segundo | $0.10 | $6.40 |
| Kling 3.0 (audio nativo) | Video API | por segundo | $0.11 | $7.04 |
| Seedance 1 Lite | Video API | por segundo | $0.03 | $1.92 |
| Shotstack | Render API | por minuto output | $0.05-$0.20 | $0.05-$0.20 |
| FFmpeg propio en spot GPU | Render | por hora GPU | $0.18 spot | ~$0.05 (60s @ 1080p en NVENC) |

**Costo total de un video de 60s con stack "calidad media-alta"**:
- TTS + Subtítulos: ~$0.07
- Imágenes (8× FLUX.2 dev): ~$0.40
- Videos (8× Veo 3.1 Lite): ~$1.92
- Render final: ~$0.05
- **Total: ~$2.44/video**

Con Sora 2 Pro1080p sube a ~$30/video. La diferencia entre "Lite" y "Pro" es 10-15x.

### Estrategia de costo1. **Reserva de presupuesto al submit** (no al ejecutar). Cuando el cliente manda `POST /jobs`, cobras `cost_reserved_cents = estimated_total +20%` de su balance. Si falla, reembolso. Si completa, cobras `cost_charged_cents = actual`. Patrón idéntico al de Sume.
2. **Auto-pricing tiers por workspace**: `generation_concurrency_limit` (3 / 8 / 25) + `queued_jobs_limit = concurrency × 5`. Free tier tiene concurrency 1, queue 5.
3. **Idempotency-Key obligatoria en cada POST a provider**. UUIDv4. TTL 24h. Si el cliente reintenta la misma operación, devuelves la respuesta cacheada sin re-cobrar.
4. **Pre-flight cost check**: antes de llamar al provider, verificar `cost_reserved - cost_charged >= estimated_step_cost`. Si no, fail con `402 insufficient_credits`.
5. **Bulk replay**: Inngest permite re-ejecutar miles de runs fallidos después de un fix. Útil cuando Sora 2 cae y hay que cambiar a Veo.

### Estrategia de reintento cuando un paso falla

| Tipo de falla | Acción | Reintentos |
|---------------|--------|------------|
| **Transient (5xx, timeout, rate limit)** | Exponential backoff con jitter: `delay = base × 2^n + random(0, base)` | 3-5 intentos, cap 30 min total |
| **Provider capacity (`provider_capacity_exceeded`)** | Re-encolar, no reintentar inmediatamente | Hasta `max_queue_time` (default 30 min) |
| **Permanent (400 invalid params, content moderation)** | Marcar step como failed, notificar, NO reintentar | 0 |
| **Network glitch post-API-call pero pre-DB-write** | Idempotency-Key garantiza no doble cobro | El orquestador re-ejecuta el step, el provider devuelve el mismo resultado |
| **Worker crash mid-step** | Step nunca marca `succeeded`. Orquestador ve status `running` sin heartbeat. Timeout del step → re-asignar a otro worker. Re-ejecutar step desde cero. | Idempotency-Key evita doble cobro |
| **Todo el job falla** | Mover a `dead_letter_jobs`. Notificar. NO auto-retry global. | Manual |

### Patrón de webhook handler```typescript
app.post('/webhooks/elevenlabs', async (req, res) => {
  // 1. Verificar HMAC-SHA256 con secret rotable
  const sig = req.headers['x-signature'];
  if (!verifyHMAC(req.rawBody, sig, WEBHOOK_SECRET)) return res.status(401).end();

  // 2. Dedupe por event_id
  const eventId = req.body.event_id;
  const seen = await redis.set(`webhook:seen:${eventId}`, '1', 'EX', 86400, 'NX');
  if (!seen) return res.status(200).end();  // ya procesado

  // 3. Buscar el job interno por provider_job_id
  const step = await db.job_steps.findOne({ provider_job_id: req.body.task_id });
  if (!step) return res.status(200).end();  // huérfano, descartar

  // 4. Actualizar estado, disparar siguiente paso
  await db.job_steps.update(step.id, {
    status: req.body.status === 'completed' ? 'succeeded' : 'failed',
    output_artifact_id: await storeAudio(req.body.audio_url),
    cost_cents: req.body.cost_cents,
    finished_at: new Date(),
  });
  await resumeWorkflow(step.job_id);  // signal al orquestador

  res.status(200).end();
});
```

Backoff de delivery de webhook del provider típico: 1m → 5m → 30m → 2h → 6h (at-least-once, debes dedupe).

---

## (e) Patrón que usan plataformas parecidas

### HeyGen (avatar video, enterprise)

- **API**: REST + MCP server + CLI. "Every endpoint ships with an MCP server, llms.txt, and typed schemas."
- **Patrón**: explícitamente asíncrono con webhooks. Su propia doc recomienda: *"your application should register a webhook URL to receive an automated push notification once the avatar_video.success event triggers."*
- **Concurrencia**: enterprise tiers tienen compute reservado en HeyGen Cloud + rate limits más altos. Batch API acepta hasta 100 requests por llamada.
- **Pricing tiers**: rate limits por plan (Tier 1 Enterprise: 120 req/min escritura, 80K req/day lectura).
- **Aprendizaje para Nexus**: ofrecen un MCP server público para que Claude/Cursor generen videos sin glue code. Vale la pena exponer tu propio MCP server para que agentes externos (incluido el Claude Code que hoy hace el proceso manual) puedan disparar jobs Nexus desde su sesión.

### Synthesia (avatar video, templates)

- **API**: REST con `create-video`, `retrieve-video`, `create-video-from-template`, `create-webhook`, `upload-script-audio`, `create-asset`.
- **Patrón**: dual mode — submit y poll vs. webhook. Templates permiten generar variantes a escala (substitución de variables).
- **Rate limits tabulados por tier** (120/600/3000 req/day Tier 1).
- **Aprendizaje**: separa `create-video` (asíncrono, devuelve video_id) de `retrieve-video` (polling). El endpoint de upload de audio custom es relevante si quieres que el usuario suba su propia voz.

### Creatify (URL-to-video, ads)

- **Endpoint estrella `Link to Video`**: el cliente pasa una URL de producto, la API scrape la página, extrae detalles, genera variantes de guion, devuelve múltiples videos de ad.
- **Patrón**: input mínimo del usuario, máxima automatización. Cubre "URL → múltiples creatividades".
- **Aprendizaje para Nexus**: el input del job no tiene que ser un brief largo. Una URL + un goal basta. El agente puede hacer el resto: scrape, extract, generate.

### OpusClip / Captions (repurposing)

- **API de captions**: word-by-word con timestamps. El job es chico pero el output es muy estilizado.
- **MCP server**: OpusClip expone MCP para conectar a agentes.
- **Aprendizaje**: cada vez más plataformas exponen MCP. El estándar emergente es REST + MCP + signed webhooks.

### Patrones transversales del sector

1. **Async by default, sync optional con timeout corto** (Shotstack, HeyGen, MpegFlow todos). Submit devuelve `job_id` en <1s. Sync espera max 30s, después devuelve `job_id` y el cliente debe polling/webhook.
3. **Webhook signature HMAC-SHA256 obligatorio** (todos).
4. **Idempotency-Key en POST mutation** (ReelsBuilder, UGC Copilot, JSON2Video). TTL 24h. Cached response byte-for-byte en retry.
5. **Queue admission control** (Sume docs explícito): `concurrency_limit + queued_jobs_limit = accepted_capacity`. Devuelven `429 queue_full` si excedes. Tu UI debe mostrar "X jobs en cola, Y en proceso".
6. **Reserved compute por tier** (HeyGen Enterprise): cliente premium tiene GPU reservada, free tier entra a cola compartida. Patrón Netflix: tiers con capacidad dedicada vs. best-effort.
7. **Spot fleet con interruption handler** (builds grandes): 80% spot, 20% on-demand. Spot interruption → checkpoint a S3 → reencolar en <2 min. Patrón MpegFlow y YouTube.
8. **Element-level cache** (JSON2Video): si regeneras el mismo guion, el provider ya cacheó TTS/images, solo re-encodifica el final. Implementar con `content_hash` en cache key.
9. **MCP server** para que agentes externos llamen tu plataforma. Hoy Claude Code puede llamar HeyGen/OpusClip vía MCP — Nexus debería ofrecer lo mismo para capturar ese tráfico.
10. **State model canónico** (Zvid): `accepted → preparing → queued → rendering → validating → completed | failed`. DB es source of truth, NO el mensaje en cola.

---

## Resumen ejecutivo para Nexus

| Pregunta | Respuesta corta |
|----------|-----------------|
| **Orquestador** | Inngest (si quieres serverless-first, menos DevOps) o Temporal (si quieres polyglot, control total, self-host posible). **No** BullMQ puro para un pipeline de 5+ pasos con APIs de pago. |
| **Cola** | Event store del orquestador + Postgres como source of truth de jobs y steps. Redis solo para idempotency cache y dedupe. |
| **Workers** | Pool stateless, auto-scaling por queue depth, 80% spot con interruption handler. Separar workers de image/video/render para escalado independiente. |
| **Webhooks** | Endpoint público único con router por provider, HMAC-SHA256 verify, dedupe por event_id, actualiza DB + signal al orquestador. |
| **APIs externas (Sí)** | LLM guion, TTS, image gen, video gen, STT para subtítulos. |
| **Máquina propia (Sí)** | Render final con FFmpeg/NVENC, almacenamiento, Postgres, API server, workers, webhook endpoint. |
| **Costo de un video de 60s** | ~$2.50 con stack Lite (Veo 3.1 Lite + FLUX dev + ElevenLabs), hasta ~$30 con Sora 2 Pro 1080p. |
| **Reintentos** | 3-5 attempts con exponential backoff + jitter. Idempotency-Key obligatoria en TODO POST a provider. Dead-letter queue para fallos permanentes. |
| **Patrón del sector** | Async-by-default, webhook callback con HMAC, idempotency keys, queue admission con concurrency cap, MCP server para agentes externos, state model `accepted→…→completed\|failed` con DB como source of truth. |

### Lo que NO sé con certeza

- Costos exactos de GPU self-host de modelos de video (Wan 2.5, CogVideoX, Mochi) en producción 24/7 a escala de miles de clips/día. La literatura apunta a que a >5K segundos/día self-host puede competir con APIs, pero el break-even depende de tu capacidad de mantener MLOps.
- Si Temporal Cloud pricing actual sigue siendo favorable vs. self-hosted Temporal server para tu volumen. Lo razonable: empezar con Inngest (SaaS, free tier generoso, zero infra) y migrar a Temporal cuando pases de ~10K jobs/mes o necesites polyglot.
- Latencias reales de Sora 2 / Veo 3.1 en producción con queue de profundidad alta. Documentación dice "30-90 segundos" pero hay reportes de colas de varios minutos en picos. Asume worst-case 5 min y diseña timeouts en consecuencia.
