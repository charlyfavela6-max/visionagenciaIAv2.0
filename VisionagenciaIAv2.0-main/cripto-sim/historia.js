// Baja velas históricas de Coinbase y las deja en estado/historia_<gran>.json
// Coinbase da 300 velas por llamada, así que se pagina hacia atrás.
import fs from 'node:fs';
import { SIMBOLOS } from './lib/estrategia.js';

const CB = 'https://api.exchange.coinbase.com';
const gran = Number(process.argv[2] ?? 300);      // segundos por vela
const dias = Number(process.argv[3] ?? 10);
const espera = (ms) => new Promise((r) => setTimeout(r, ms));

async function trae(simbolo, desde, hasta) {
  const u = `${CB}/products/${simbolo}/candles?granularity=${gran}` +
            `&start=${desde.toISOString()}&end=${hasta.toISOString()}`;
  for (let i = 0; i < 4; i++) {
    const r = await fetch(u, { headers: { 'User-Agent': 'cripto-sim' } });
    if (r.ok) return r.json();
    await espera(1200 * (i + 1));
  }
  return [];
}

const salida = {};
for (const s of SIMBOLOS) {
  const trozos = [];
  let fin = new Date();
  for (let i = 0; i < Math.ceil(dias * 86400 / (gran * 300)); i++) {
    const ini = new Date(fin.getTime() - gran * 300 * 1000);
    trozos.push(...await trae(s, ini, fin));
    fin = ini;
    await espera(260);
  }
  const velas = trozos.map(([t, l, h, o, c, v]) => ({ t: t * 1000, o, h, l, c, v }))
    .sort((a, b) => a.t - b.t)
    .filter((v, i, a) => i === 0 || v.t !== a[i - 1].t);
  salida[s] = velas;
  console.log(s, velas.length, 'velas',
    new Date(velas[0].t).toISOString().slice(0, 16), '→',
    new Date(velas.at(-1).t).toISOString().slice(0, 16));
}
fs.mkdirSync('estado', { recursive: true });
fs.writeFileSync(`estado/historia_${gran}.json`, JSON.stringify(salida));
