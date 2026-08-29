// Simulador de operaciones en cripto: precios de verdad, dinero de mentiras.
//
// No hay llaves de exchange en ningún lado y el motor no sabe mandar órdenes:
// lo único que hace es aritmética sobre el precio que publica Coinbase. Sirve
// para ver cómo se habría portado la estrategia, nada más.
import 'dotenv/config';
import express from 'express';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Feed } from './lib/feed.js';
import { Motor } from './lib/motor.js';
import { SIMBOLOS, REGLAS, TACTICAS, GRANULARIDAD, HORAS_VELA }
  from './lib/estrategia.js';
import { avisa, activo as waActivo, bitacora } from './lib/whatsapp.js';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const PUERTO = process.env.PORT || 8080;

const feed = new Feed(SIMBOLOS, { granularidad: GRANULARIDAD });
const motor = new Motor(feed, { avisa });

const app = express();
app.use(express.json());
app.use(express.static(path.join(AQUI, 'public')));

app.get('/api/estado', (_req, res) => res.json({
  ...motor.resumen(),
  whatsapp: { activo: waActivo, ultimos: bitacora.slice(0, 15) },
  reglas: { ...REGLAS, tacticas: TACTICAS, simbolos: SIMBOLOS,
            horasVela: HORAS_VELA },
}));

app.post('/api/ejecutar', async (req, res) => {
  try {
    const monto = Number(req.body?.monto);
    res.json(await motor.arranca(monto));
  } catch (e) { res.status(400).json({ error: String(e.message ?? e) }); }
});

app.post('/api/detener', async (_req, res) => {
  try { res.json(await motor.detiene()); }
  catch (e) { res.status(400).json({ error: String(e.message ?? e) }); }
});

app.get('/api/salud', (_req, res) => res.json({
  ok: true, fuente: feed.fuente, corriendo: motor.e.corriendo,
  ultimoTick: feed.vivo,
}));

// El pulso: el stop de emergencia no puede esperar a que cierre la vela de
// 4 h, así que se revisa cada 3 s. El resumen se pregunta solo cuándo le toca.
setInterval(() => {
  motor.pulso().catch((e) => console.error('pulso', e));
  motor.resumenHorario().catch((e) => console.error('resumen', e));
}, 3000);

feed.arranca()
  .then(() => app.listen(PUERTO, () =>
    console.log(`cripto-sim en http://localhost:${PUERTO} · fuente ${feed.fuente}`)))
  .catch((e) => { console.error('no arrancó el feed:', e); process.exit(1); });
