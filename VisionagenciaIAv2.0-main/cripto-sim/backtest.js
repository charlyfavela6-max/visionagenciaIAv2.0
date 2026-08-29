// Backtest de cartera sobre la historia bajada con `node historia.js 3600 120`.
// Simula lo mismo que el motor en vivo: velas de 4 h, máximo N posiciones, una
// por moneda, comisión y deslizamiento en los dos lados.
//
// La referencia no es "ganar": es GANARLE A COMPRAR Y ESPERAR. Una estrategia
// que rinde 8% mientras el mercado subió 30% está destruyendo dinero.
import fs from 'node:fs';
import { SIMBOLOS, REGLAS, TACTICAS, HORAS_VELA, GRANULARIDAD, agrupa,
         entrada, salida, protecciones } from './lib/estrategia.js';

const H = JSON.parse(
  fs.readFileSync(`estado/historia_${GRANULARIDAD}.json`, 'utf8'));
const DATOS = Object.fromEntries(
  SIMBOLOS.map((s) => [s, agrupa(H[s], HORAS_VELA)]));
const N = Math.min(...SIMBOLOS.map((s) => DATOS[s].length));
const ARRANQUE = TACTICAS.tendencia.lenta + 5;

export function corre({ capital = 1000, reglas = REGLAS, solo = null } = {}) {
  let efectivo = capital;
  const abiertas = [];
  const cerradas = [];

  for (let i = ARRANQUE; i < N; i++) {
    const precio = (s) => DATOS[s][i].c;
    const valor = () => abiertas.reduce((a, p) => a + p.unidades * precio(p.simbolo), 0);

    for (const p of [...abiertas]) {
      const velas = DATOS[p.simbolo].slice(0, i + 1);
      const v = velas.at(-1);
      p.maxVisto = Math.max(p.maxVisto, v.h);
      p.velas = i - p.i;

      // Lo pesimista es lo honesto: si la vela tocó el stop, se asume que lo
      // tocó antes de cualquier otra cosa.
      let motivo = null, precioSalida = v.c;
      if (v.l <= p.stopDuro) { motivo = 'stop de emergencia'; precioSalida = p.stopDuro; }
      else motivo = salida(velas, p);
      if (!motivo) continue;

      const neto = p.unidades * precioSalida * (1 - reglas.deslizamiento)
                   * (1 - reglas.comision);
      efectivo += neto;
      abiertas.splice(abiertas.indexOf(p), 1);
      cerradas.push({ simbolo: p.simbolo, tactica: p.tactica, motivo,
                      ganancia: neto - p.invertido,
                      pct: (neto - p.invertido) / p.invertido * 100,
                      horas: p.velas * HORAS_VELA });
    }

    for (const s of SIMBOLOS) {
      if (abiertas.length >= reglas.maxAbiertas) break;
      if (abiertas.some((p) => p.simbolo === s)) continue;
      const velas = DATOS[s].slice(0, i + 1);
      const sig = entrada(velas);
      if (!sig) continue;
      if (solo && !solo.includes(sig.tactica)) continue;
      const monto = (efectivo + valor()) * reglas.fraccion;
      if (monto > efectivo) continue;

      const p0 = velas.at(-1).c * (1 + reglas.deslizamiento);
      const comision = monto * reglas.comision;
      efectivo -= monto;
      abiertas.push({ i, simbolo: s, tactica: sig.tactica, precioEntrada: p0,
                      unidades: (monto - comision) / p0, invertido: monto,
                      maxVisto: p0, velas: 0, ...protecciones(sig.tactica, p0, velas) });
    }
  }

  const final = efectivo + abiertas.reduce(
    (a, p) => a + p.unidades * DATOS[p.simbolo][N - 1].c, 0);
  const porTactica = {};
  for (const c of cerradas) {
    const t = porTactica[c.tactica] ??= { n: 0, ganancia: 0, ganadas: 0, horas: 0 };
    t.n++; t.ganancia += c.ganancia; t.horas += c.horas;
    if (c.ganancia > 0) t.ganadas++;
  }
  return { final, retorno: (final / capital - 1) * 100, cerradas, porTactica,
           dias: (N - ARRANQUE) * HORAS_VELA / 24 };
}

export function comprarYesperar(capital = 1000) {
  const parte = capital / SIMBOLOS.length;
  const fin = SIMBOLOS.reduce(
    (a, s) => a + parte * (DATOS[s][N - 1].c / DATOS[s][ARRANQUE].c), 0);
  return (fin / capital - 1) * 100;
}

if (process.argv[1]?.endsWith('backtest.js')) {
  const r = corre({});
  console.log(`${r.dias.toFixed(0)} días · ${r.cerradas.length} operaciones · ` +
              `velas de ${HORAS_VELA} h`);
  for (const [t, v] of Object.entries(r.porTactica)) {
    console.log(`  ${t.padEnd(10)} ${String(v.n).padStart(3)} ops · ` +
      `${v.ganadas}/${v.n} en verde (${(v.ganadas / v.n * 100).toFixed(0)}%) · ` +
      `${v.ganancia >= 0 ? '+' : ''}$${v.ganancia.toFixed(2)} · ` +
      `${(v.horas / v.n).toFixed(0)} h por operación`);
  }
  const motivos = {};
  for (const c of r.cerradas) motivos[c.motivo] = (motivos[c.motivo] ?? 0) + 1;
  console.log('  salidas:', motivos);
  const h = comprarYesperar();
  console.log(`ESTRATEGIA         ${r.retorno >= 0 ? '+' : ''}${r.retorno.toFixed(2)}%`);
  console.log(`comprar y esperar  ${h >= 0 ? '+' : ''}${h.toFixed(2)}%`);
  console.log(`ventaja            ${(r.retorno - h) >= 0 ? '+' : ''}${(r.retorno - h).toFixed(2)} puntos`);
}
