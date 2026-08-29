// ¿Y si en vez de cazar movimientos se sigue la tendencia y se opera poco?
// Velas de 4 h (armadas juntando las de 1 h), entrada cuando EMA20 > EMA50 y
// salida cuando el precio pierde la EMA20. Pocas operaciones = poca comisión.
import fs from 'node:fs';
import { ema, atr } from './lib/indicadores.js';
import { SIMBOLOS, REGLAS } from './lib/estrategia.js';

const H = JSON.parse(fs.readFileSync('estado/historia_3600.json', 'utf8'));

const junta = (velas, k) => {
  const out = [];
  for (let i = 0; i + k <= velas.length; i += k) {
    const g = velas.slice(i, i + k);
    out.push({ t: g[0].t, o: g[0].o, c: g.at(-1).c,
               h: Math.max(...g.map((v) => v.h)), l: Math.min(...g.map((v) => v.l)),
               v: g.reduce((a, v) => a + v.v, 0) });
  }
  return out;
};

function corre({ horas = 4, rapida = 20, lenta = 50, trailAtr = 0,
                 capital = 1000, maxAb = 4, frac = 0.20 } = {}) {
  const datos = Object.fromEntries(SIMBOLOS.map((s) => [s, junta(H[s], horas)]));
  const n = Math.min(...SIMBOLOS.map((s) => datos[s].length));
  let efectivo = capital;
  const abiertas = [];
  const cerradas = [];

  for (let i = lenta + 5; i < n; i++) {
    const valor = () => abiertas.reduce((a, p) => a + p.unidades * datos[p.simbolo][i].c, 0);

    for (const p of [...abiertas]) {
      const d = datos[p.simbolo].slice(0, i + 1);
      const c = d.map((v) => v.c);
      const er = ema(c, rapida);
      p.maxVisto = Math.max(p.maxVisto, d.at(-1).h);
      const stopTrail = p.trailing ? p.maxVisto - p.trailing : -Infinity;
      const salir = d.at(-1).c < er || d.at(-1).l <= stopTrail;
      if (!salir) continue;
      const precio = Math.max(d.at(-1).c, Math.min(d.at(-1).c, stopTrail));
      const neto = p.unidades * precio * (1 - REGLAS.deslizamiento) * (1 - REGLAS.comision);
      efectivo += neto;
      abiertas.splice(abiertas.indexOf(p), 1);
      cerradas.push({ simbolo: p.simbolo, ganancia: neto - p.invertido,
                      pct: (neto - p.invertido) / p.invertido * 100,
                      horas: (i - p.i) * horas });
    }

    for (const s of SIMBOLOS) {
      if (abiertas.length >= maxAb || abiertas.some((p) => p.simbolo === s)) continue;
      const d = datos[s].slice(0, i + 1);
      const c = d.map((v) => v.c);
      const er = ema(c, rapida), el = ema(c, lenta);
      const erP = ema(c.slice(0, -1), rapida), elP = ema(c.slice(0, -1), lenta);
      if (!er || !el || !erP || !elP) continue;
      if (!(erP <= elP && er > el && d.at(-1).c > er)) continue;

      const monto = (efectivo + valor()) * frac;
      if (monto > efectivo) continue;
      const entrada = d.at(-1).c * (1 + REGLAS.deslizamiento);
      const comision = monto * REGLAS.comision;
      efectivo -= monto;
      abiertas.push({ i, simbolo: s, entrada, invertido: monto,
                      unidades: (monto - comision) / entrada, maxVisto: entrada,
                      trailing: trailAtr ? atr(d, 14) * trailAtr : 0 });
    }
  }
  const final = efectivo + abiertas.reduce(
    (a, p) => a + p.unidades * datos[p.simbolo][n - 1].c, 0);
  return { ret: (final / capital - 1) * 100, ops: cerradas.length,
           ganadas: cerradas.filter((c) => c.ganancia > 0).length,
           dias: n * horas / 24 };
}

const parte = 1000 / SIMBOLOS.length;
const nH = Math.min(...SIMBOLOS.map((s) => H[s].length));
const hold = (SIMBOLOS.reduce((a, s) => a + parte * (H[s][nH - 1].c / H[s][55].c), 0)
              / 1000 - 1) * 100;

console.log('horas rapida lenta trail   ops  ganadas   estrategia   ventaja vs esperar');
for (const horas of [4, 8, 12, 24]) {
  for (const [rapida, lenta] of [[10, 30], [20, 50], [8, 21]]) {
    for (const trailAtr of [0, 3]) {
      const r = corre({ horas, rapida, lenta, trailAtr });
      console.log(
        `${String(horas).padStart(5)} ${String(rapida).padStart(6)} ` +
        `${String(lenta).padStart(5)} ${String(trailAtr).padStart(5)} ` +
        `${String(r.ops).padStart(5)} ${String(r.ganadas).padStart(8)} ` +
        `${r.ret.toFixed(2).padStart(11)}% ${(r.ret - hold).toFixed(2).padStart(12)}`);
    }
  }
}
console.log(`comprar y esperar: ${hold.toFixed(2)}%  ·  ${(nH / 24).toFixed(0)} días`);
