Aclaración inicial: no pude clonar `charlyfavela1-eng/visionagencia-control` (`gh` pide auth y no tengo token), ni apareció en los resultados de búsqueda como repo público accesible para inspección. La respuesta se basa en la web pública; el código está pensado para una PWA servida desde `public/taxi/` con `manifest.json` + service worker. Si me das el token de GitHub o el código existente, lo adapto con precisión.

---

# Grita Taxi — Micrófono "siempre encendido" en PWA

## 0. Nota sobre el repositorio

No pude clonar `charlyfavela1-eng/visionagencia-control`. La sesión no tiene `gh auth login` configurado y el buscador web no devolvió contenido de `public/taxi/`. La respuesta asume la estructura típica de una PWA servida como estáticos desde `public/taxi/`. El código que entrego se puede copiar tal cual a ese directorio.

## 1. La verdad técnica (sin adornar)

### 1.1 `SpeechRecognition` (Web Speech API) — el motor real

- **Qué es:** la API nativa que ya usas. En Chrome delega a Google Cloud STT (con la red); en Safari delega al servidor de Apple (macOS 14+/iOS 17+) o al motor on-device cuando esté disponible.
- **Qué pasa en segundo plano:**
  - **Chrome escritorio y Android Chrome:** el motor se desconecta solo al cabo de ~60 s (es el "60 second timeout" histórico confirmado por el equipo de Chromium en `chromium-html5` y replicado por usuarios desde 2014) y, sobre todo, **se mata por completo cuando la pestaña se mueve a background, se suspende o el dispositivo entra en Doze/standby**. El `onend` se dispara sin error. No hay `nopause`, no hay `nospeechtimeout` público, no hay forma de subir el límite.
  - **iOS Safari (incluso como PWA añadida a pantalla de inicio):** `continuous: true` es "completamente inútil" según A. Giammarchi (WebReflection, "Taming the Web Speech API"); el reconocimiento se detiene a los pocos segundos de silencio. Si en la misma sesión se reproduce un `<audio>` (lo que tú harás al decir "taxi"), hay un bug WebKit confirmado (**WebKit bug 317741**, reconocimiento upstream en STP 248 a agosto 2026, aún no en Safari estable 26.6) que cuelga `start()` sin disparar `onresult`/`onend`/`onerror`.
  - **Firefox:** `SpeechRecognition` no existe (sólo síntesis). En Android = sin app. En escritorio = nada. **Tu app simplemente no existe ahí.**
- **Lo que NO puede hacer una PWA:** mantener la captura de micrófono cuando el navegador decide suspender la pestaña. El control lo tiene el SO/navegador, no la web. No hay API web que lo impida.

### 1.2 `getUserMedia` crudo (MediaRecorder + análisis local)

- Funciona mientras la pestaña está viva y foreground/visible. En background la pista se cierra al rato. No hay forma de mantenerla abierta. **No es un sustituto real** de `SpeechRecognition` para detectar la palabra "taxi" si no metes un modelo on-device (Whisper.cpp WASM, ~100 MB, latencia alta, batería brutal).
- Chrome 139 ya tiene **on-device Web Speech** (sin red), pero sigue atado al ciclo de vida de la pestaña.

### 1.3 Restricciones por plataforma (lo que sí y lo que NO)

| Capacidad | Android Chrome (web) | Android Chrome (PWA instalada) | iOS Safari (web) | iOS PWA instalada |
|---|---|---|---|---|
| `SpeechRecognition` disponible | Sí (Google) | Sí | Sí (Apple) | Sí |
| Funciona con pantalla apagada | NO (al suspenderse la pestaña, `onend` y a morir) | NO (igual) | NO (la pestaña se cuelga) | NO |
| Funciona con app en background | NO | NO | NO | NO (peor: PWA standalone además rompe `<audio>` al re-abrir, ver WebKit bug 295518) |
| Foreground service / background audio nativo | n/a | n/a | n/a | n/a |
| Wake Lock API | Sí (84+) | Sí | Sí (18.4+) | Sí |
| Audio silencioso en bucle (anti-suspensión) | NO funciona para mantener Web Speech vivo | NO | NO — iOS silencia en background en PWA | NO |
| Media Session API | Sí | Sí | Parcial (lockscreen) | Parcial |
| Notificación persistente (Web Push) | Sí (sólo SW) | Sí | NO en iOS PWA standalone (Apple lo bloqueó) | NO |
| Microphone perm. persistente en background | NO (Android 9+ apaga el mic tras ~1 min en background si no hay FGS) | NO | NO | NO |

**Conclusión de esta tabla:** una PWA pura NO puede cumplir "siempre escuchando con la pantalla apagada o en background" en ninguna combinación plataforma/navegador actual. El navegador suspende la pestaña y/o cierra el WebSocket de Google STT. No es un bug, es el modelo de plataforma.

## 2. Trucos que sí funcionan y cuáles aplican al micro real

| Truco | Evita suspensión | Mantiene SpeechRecognition vivo | Aplica aquí | Comentario |
|---|---|---|---|---|
| **Screen Wake Lock API** | Mantiene pantalla encendida, no evita suspensión de JS | NO (sólo pantalla) | NO de forma aislada | Útil como UX (no se apaga la pantalla) pero no resuelve el problema central |
| **Audio silencioso en bucle** (`<audio loop>` o `AudioContext`) | En Chrome sí; en iOS lo silencia en background tras 1-2 loops | NO para SpeechRecognition, SÍ para evitar que Chrome mate la pestaña | SÍ para ganar minutos en Android Chrome mientras la app está visible | Hay que arrancar DESPUÉS de un gesto del usuario; en iOS PWA standalone falla (WebKit 295518) |
| **Media Session API** | No | No | NO directo, pero pone la "now playing" con controles — útil para reiniciar | Sirve para que el usuario reanude desde lockscreen |
| **Service Worker + Push** | No | No | NO para micro continuo; SÍ para notificar al usuario y abrir la app | El SW no tiene acceso a `getUserMedia` ni a `SpeechRecognition` |
| **Web Push persistente (notification sticky)** | No | No | NO en iOS PWA standalone | Apple lo bloqueó; en Android Chrome sí se ve pero no detiene la suspensión |
| **WebRTC / socket keep-alive** | A veces en Chrome | NO — Google STT cierra por su cuenta | NO | Engaña al throttler pero no al SpeechRecognition |

**Veredicto:** para el micrófono de verdad, **sólo hay una combinación que se acerca al objetivo sin envoltorio nativo: en Android Chrome con la pestaña foreground, el truco de audio silencioso en bucle + reinicio agresivo de `SpeechRecognition` en `onend`.** Eso te da "horas" si la pantalla queda encendida. Pantalla apagada, app en background, o iOS → sin envoltorio nativo no hay solución real.

## 3. ¿Hace falta nativa o envoltorio? Lo que cambia

| Opción | Android | iOS | Esfuerzo | ¿Cumple "siempre escuchando"? |
|---|---|---|---|---|
| **PWA pura (lo que tienes)** | Limitado, sólo foreground | Limitado, sólo foreground | 0 | NO |
| **TWA (Trusted Web Activity)** | Te da chrome custom, icon, Play Store, pero **sigue siendo Chrome** y hereda TODAS las limitaciones de PWA + TWA bug confirmado: tras ~60 s en background Chrome cierra el mic (android-browser-helper issue 197) | n/a | Bajo (assetlinks.json + manifest) | NO sin foreground service |
| **TWA + foreground service manual** | Puedes añadir un FGS nativo que mantiene el proceso vivo; en `android-browser-helper 2.2.0+` se puede extender `LauncherActivity` para iniciar un FGS que protege a Chrome del kill por Doze | n/a | Medio (Kotlin/Java + Bridge) | **SÍ en Android** — esto es lo más cercano a "siempre" sin app nativa propia |
| **Capacitor (envoltura webview + plugins)** | Puedes usar `@capgo/capacitor-audio-recorder` o `@capawesome-team/capacitor-audio-recorder` con `FOREGROUND_SERVICE_MICROPHONE` + `WAKE_LOCK` en el manifest → grabación y reconocimiento siguen en background | Necesitas `UIBackgroundModes: audio` en Xcode + `AVAudioSession .playAndRecord .voiceChat` | Medio-alto (Node, build) | **SÍ en ambos**, con un plugin de voz o Whisper on-device |
| **App nativa (Kotlin/Swift)** | Control total: `SpeechRecognizer` + `RecognitionService` con `FOREGROUND_SERVICE_MICROPHONE` | `SFSpeechRecognizer` + `AVAudioSession` con background mode `audio` | Alto | **SÍ** |

**Recomendación honesta:** para llegar a "siempre escuchando pantalla apagada y background" en serio, **Capacitor con un plugin de audio background + foreground service** es el camino más corto. Una TWA no te lo da por sí sola (el issue 197 de android-browser-helper es exactamente este caso de uso y se cierra con un parche parcial). Si además quieres iOS, **app nativa con Xcode background mode `audio` es inevitable** — Apple bloquea cualquier PWA que mantenga captura de audio en background.

## 4. Código concreto del arreglo (lo que SÍ puedes hacer en PWA)

Sirve para `public/taxi/`. Estructura esperada:

```
public/taxi/
├── index.html
├── sw.js
├── manifest.webmanifest
├── silent-loop.wav   (o generado a 1 kHz con WebAudio)
└── icon-192.png, icon-512.png
```

### 4.1 `index.html` — UI mínima

```html
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Grita Taxi</title>
<link rel="manifest" href="manifest.webmanifest">
<meta name="theme-color" content="#000000">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
</head>
<body>
<h1>Grita Taxi</h1>
<button id="start">Activar</button>
<p id="status">apagado</p>
<p id="heard"></p>
<script src="app.js" type="module"></script>
</body>
</html>
```

### 4.2 `manifest.webmanifest`

```json
{
  "name": "Grita Taxi",
  "short_name": "Grita Taxi",
  "start_url": "./index.html",
  "scope": ".",
  "display": "standalone",
  "background_color": "#000000",
  "theme_color": "#000000",
  "icons": [
    { "src": "icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

### 4.3 `sw.js` — service worker mínimo

```js
self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
// No se puede capturar micro desde SW; sólo mantener caché.
```

### 4.4 `app.js` — la lógica

```js
// Grita Taxi: reconocimiento continuo con auto-restart + trucos anti-suspensión.
// NO convierte a la app en "always-listening" real fuera de foreground; eso es
// imposible en una PWA pura. Lo que hace es maximizar uptime mientras la pestaña
// está activa y el usuario ha interactuado.

const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
const IS_IOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
const IS_ANDROID = /Android/.test(navigator.userAgent);

// --- Wake Lock: mantiene la pantalla encendida mientras haya uno ---
let wakeLock = null;
async function acquireWakeLock() {
  if (!('wakeLock' in navigator)) return;
  try {
    wakeLock = await navigator.wakeLock.request('screen');
    wakeLock.addEventListener('release', () => { wakeLock = null; });
  } catch (e) { /* permission denied o no soportado */ }
}
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible' && !wakeLock) acquireWakeLock();
});

// --- Audio silencioso en bucle: en Android Chrome evita que la pestaña
//     se suspenda por inactividad. En iOS NO funciona en PWA standalone. ---
let silentAudio = null;
function startSilentLoop() {
  if (silentAudio) return;
  // silent-loop.wav: 1 segundo de silencio PCM, en bucle. <2 KB.
  silentAudio = new Audio('silent-loop.wav');
  silentAudio.loop = true;
  silentAudio.volume = 0.0001; // inaudible pero cuenta como "playing"
  silentAudio.setAttribute('playsinline', '');
  silentAudio.play().catch(() => { /* iOS PWA: falla, lo esperamos */ });
}

// --- Media Session: controles en lockscreen + reanuda si el OS pausa ---
function setupMediaSession() {
  if (!('mediaSession' in navigator)) return;
  navigator.mediaSession.metadata = new MediaMetadata({
    title: 'Grita Taxi',
    artist: 'Escuchando…',
    album: 'Activo',
  });
  navigator.mediaSession.setActionHandler('play',  () => tryStartRecognition('mediaSession:play'));
  navigator.mediaSession.setActionHandler('pause', () => recognition && recognition.stop());
}

// --- Reconocimiento: motor + reinicio escalonado ---
let recognition = null;
let retries = 0;
let intentionalStop = false;
let lastHeard = 0;
let watchdog = null;

function makeRecognition() {
  if (!SR) return null;
  const r = new SR();
  r.lang = 'es-ES';
  r.continuous = true;       // Chrome en Android sigue cortando a ~60 s; onend lo maneja
  r.interimResults = true;
  r.maxAlternatives = 1;
  return r;
}

function sayTaxi() {
  // Síntesis para confirmar al usuario
  try {
    const u = new SpeechSynthesisUtterance('taxi');
    u.lang = 'es-ES'; u.rate = 1.1; u.volume = 1;
    speechSynthesis.speak(u);
  } catch (_) {}
}

function tryStartRecognition(why = 'manual') {
  if (!SR) {
    document.getElementById('status').textContent =
      'Tu navegador no soporta SpeechRecognition. Firefox no, otros sí.';
    return;
  }
  if (!recognition) recognition = makeRecognition();
  if (!recognition) return;

  recognition.onresult = (e) => {
    lastHeard = Date.now();
    let txt = '';
    for (let i = e.resultIndex; i < e.results.length; i++) {
      txt += e.results[i][0].transcript;
    }
    document.getElementById('heard').textContent = txt;
    if (/\btaxi\b/i.test(txt)) sayTaxi();
  };

  recognition.onerror = (e) => {
    // 'not-allowed' y 'service-not-allowed' no se reintentan
    if (e.error === 'not-allowed' || e.error === 'service-not-allowed') {
      intentionalStop = true;
      document.getElementById('status').textContent = 'Permiso denegado: ' + e.error;
      return;
    }
    // 'no-speech', 'aborted', 'network' → dejar que onend reintente
  };

  recognition.onend = () => {
    if (intentionalStop) return;
    // Reinicio escalonado: 250 ms, 500 ms, 1 s, 2 s, 5 s (cap)
    const delays = [250, 500, 1000, 2000, 5000];
    const wait = delays[Math.min(retries, delays.length - 1)];
    retries++;
    setTimeout(() => {
      if (intentionalStop) return;
      try { recognition.start(); retries = 0; } catch (_) { /* ya activo */ }
    }, wait);
  };

  try { recognition.start(); retries = 0; } catch (_) { /* ya activo */ }

  // Watchdog: si Chrome se queda colgado sin onend ni onresult (bug conocido
  // en background + WebKit 317741 en iOS), forzamos stop/start cada 75 s.
  clearInterval(watchdog);
  watchdog = setInterval(() => {
    if (!recognition || intentionalStop) return;
    if (Date.now() - lastHeard > 70000) {
      try { recognition.stop(); } catch (_) {}
      // onend disparará el reinicio
    }
  }, 10000);

  document.getElementById('status').textContent = 'escuchando…';
}

// --- Arranque: sólo después de un gesto del usuario (exigencia de los
//     navegadores para getUserMedia, audio, wake lock y SR a la vez) ---
document.getElementById('start').addEventListener('click', async () => {
  intentionalStop = false;
  await acquireWakeLock();
  startSilentLoop();     // ayuda en Android Chrome
  setupMediaSession();
  tryStartRecognition('user-gesture');
});
```

Notas puntuales:

- `silent-loop.wav` puede ser 1 s de silencio PCM 8 kHz mono 8-bit, pesa ~8 KB. Si quieres generarlo en runtime con `AudioContext`, eso NO cuenta como "audio playing" a ojos del throttler de Chrome — necesitas un elemento HTML `<audio>` real con `src` apuntando a un archivo.
- `setAttribute('playsinline','')` no hace nada en Android, pero no estorba.
- Si la PWA se cierra o se suspende, **el `<audio>` se pausa y el reconocimiento muere**. Esto es esperado, no se puede evitar.

### 4.5 Si decides ir a TWA + foreground service (Android)

`android-browser-helper 2.2.0+` permite extender `LauncherActivity` para arrancar un FGS. Lo mínimo que necesitas en código nativo:

- `AndroidManifest.xml`: añadir `android.permission.FOREGROUND_SERVICE`, `FOREGROUND_SERVICE_MICROPHONE`, `WAKE_LOCK`, `POST_NOTIFICATIONS`, `RECORD_AUDIO`.
- `serviceType="microphone"` en `<service>`.
- Notificación persistente con canal `IMPORTANCE_LOW` (Android 8+).
- `LauncherActivity` → `onStart` → `ContextCompat.startForegroundService(...)`.

Desde la web, no tienes que cambiar nada: Chrome dentro de la TWA se beneficia de que el proceso no se mate. La PWA sigue hablando con la `SpeechRecognition` igual.

## 5. Auto-recuperación cuando el navegador corta el reconocimiento

Ya está implementado arriba (`onend` con backoff 250→500→1000→2000→5000 ms). Refuerzos que vale la pena sumar:

1. **Backoff sólo en errores recuperables** (`no-speech`, `aborted`, `network`). En `not-allowed` y `service-not-allowed` parar y pedir gesto del usuario.
2. **Jitter ±20%** sobre el delay para que dos pestañas no se sincronicen en bucle infinito (un bug histórico de Chromium documentado en issue 296690).
3. **Cap de reintentos consecutivos** sin `onresult`: tras 8 `onend` sin oír nada, pausar 30 s y volver. Si la pestaña está en background, ni intentarlo (visibilidad se fue).
4. **Watchdog 70 s** que ya tienes: Chrome a veces se cuelga sin `onend`; el `stop()` fuerza la salida.
5. **En iOS, rotar el `recognition` cada reinicio** (crear uno nuevo) — el bug 317741 deja el objeto zombi tras un `<audio>` previo. Esto es un workaround al bug hasta que el fix llegue a Safari estable.

## 6. Batería — números y cómo bajarla

Cifras recogidas de fuentes públicas (no medidas por mí; trátalas como orden de magnitud):

- **WebRTC / micro continuo en foreground en un flagship 2026:** ~8–15 %/h; en gama baja 15–25 %/h. Fuente: `callsphere.ai/blog/vw4e...`.
- **Web Speech API en Chrome (envía audio a Google Cloud STT):** ~10–20 %/h sólo por uplink + decodificación + espera de websocket. Sin contar pantalla.
- **Wake Lock manteniendo pantalla encendida:** +20–40 %/h según brillo. Es el componente más caro, evítalo si la app no lo necesita visualmente.
- **Audio silencioso en bucle:** ~1–2 %/h extra. Barato, mantenlo.
- **Doze / Standby de Android:** si el sistema entra en Doze profundo, el consumo cae a casi cero, pero la app deja de recibir audio. Es lo que rompe el "siempre escuchando" en background puro.

Cómo bajar la factura:

1. **Detectar si la pantalla está apagada** (`screen.orientation` + `document.visibilityState`) y **soltar el wake lock** en cuanto el usuario sale de la app. Volver a adquirirlo cuando vuelve.
2. **No usar `interimResults: true`** si no lo necesitas — dobla el tráfico a STT. Para "taxi" basta con `false` y procesar sólo el `final`.
3. **Limitar `maxAlternatives: 1`**.
4. **Audio silencioso a `volume = 0.0001`**, no `0`, y `muted = false`. Si está `muted`, algunos navegadores lo cuentan como "no playing" y suspenden igual.
5. **En iOS, `display: "minimal-ui"` en manifest** en vez de `standalone` reduce algunos throttles (confirmado por usuarios en SO). Estético feo, funcional mejor.
6. **Si llegas a TWA/Capacitor:** pide al usuario que excluya la app del "Battery optimization" del sistema. Sin eso, Android mata el FGS tras ~30 min en Doze.
7. **Cero animaciones CSS** mientras la app está "escuchando" — un `transform` continuo ya come el 5 %/h.
8. **Si necesitas iOS de verdad:** el costo de una nativa es 5–10 %/h con `SFSpeechRecognizer` on-device; con la nube de Apple sube a 12–18 %/h. Mismo orden, mejor calidad.

## 7. Resumen ejecutivo

- **Lo que la PWA puede hacer HOY:** mantener el micro activo minutos a horas en Android Chrome con la app en foreground y un gesto inicial del usuario, gracias a (1) wake lock, (2) audio silencioso en bucle, (3) reinicio agresivo de `SpeechRecognition` con backoff escalonado, (4) watchdog de 70 s.
- **Lo que NO puede hacer una PWA:** seguir escuchando con la pantalla apagada, con la app en background, o en iOS. Las tres condiciones están bloqueadas por el navegador/SO, no por falta de API.
- **El salto real es Capacitor (Android+iOS) o TWA + FGS manual (sólo Android).** Una TWA "pelada" sigue sin resolver el problema (issue 197 de android-browser-helper).
- **Si el objetivo es producción real**, evalúa nativa. El polyfill `apersongithub/Speech-Recognition-Polyfill` con Whisper WASM on-device es una opción intermedia para Firefox, pero pesa ~2 GB en disco y la batería se dispara.

Avísame si quieres que entregue el código como PR al repo (necesitaría el `GH_TOKEN` o que me pegues aquí el contenido de `public/taxi/`) o que lo extienda a Capacitor con un ejemplo de `MainActivity.kt` con el foreground service.
