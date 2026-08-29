// Prueba rápida de la estrategia sobre las últimas 5 horas de velas de 1 min.
// No sustituye un backtest serio (5 h es poquísimo), pero sirve para ver que
// las tres tácticas disparan y con qué frecuencia.
import { SIMBOLOS, TACTICAS, REGLAS, señal } from './lib/estrategia.js';
import { atr } from './lib/indicadores.js';

const CB = 'https://api.exchange.coinbase.com';

async function velasDe(simbolo) {
  const r = await fetch(`${CB}/products/${simbolo}/candles?granularity=60`,
                        { headers: { 'User-Agent': 'cripto-sim' } });
  return (await r.json())
    .map(([t, l, h, o, c, v]) => ({ t: t * 1000, o, h, l, c, v }))
    .sort((a, b) => a.t - b.t);
}

const cuenta = {};
let total = 0, ganancia = 0;

for (const s of SIMBOLOS) {
  const velas = await velasDe(s);
  for (let i = 70; i < velas.length; i++) {
    const hasta = velas.slice(0, i + 1);
    const sig = señal(hasta);
    if (!sig) continue;
    const regla = TACTICAS[sig.tactica];
    const a = atr(hasta, 14);
    const entrada = velas[i].c * (1 + REGLAS.deslizamiento);
    const tp = entrada + a * regla.tp, sl = entrada - a * regla.sl;
    let salida = null, motivo = 'tiempo';
    for (let j = i + 1; j < Math.min(velas.length, i + regla.minutos); j++) {
      if (velas[j].l <= sl) { salida = sl; motivo = 'stop'; break; }
      if (velas[j].h >= tp) { salida = tp; motivo = 'objetivo'; break; }
    }
    salida ??= velas[Math.min(velas.length - 1, i + regla.minutos)].c;
    const pct = (salida * (1 - REGLAS.deslizamiento) / entrada - 1) * 100
                - REGLAS.comision * 200;
    const c = cuenta[sig.tactica] ??= { n: 0, pct: 0, ganadas: 0 };
    c.n++; c.pct += pct; if (pct > 0) c.ganadas++;
    total++; ganancia += pct;
    i += 5;   // no se vuelve a entrar en la misma moneda inmediatamente
  }
}

console.log(`${total} señales en 5 h sobre ${SIMBOLOS.length} monedas`);
for (const [t, c] of Object.entries(cuenta)) {
  console.log(`  ${t.padEnd(10)} ${String(c.n).padStart(3)} ops · ` +
    `${c.ganadas}/${c.n} en verde · ${(c.pct).toFixed(2)}% sumado · ` +
    `${(c.pct / c.n).toFixed(3)}% por operación`);
}
console.log(`total ${ganancia.toFixed(2)}% sumado`);
