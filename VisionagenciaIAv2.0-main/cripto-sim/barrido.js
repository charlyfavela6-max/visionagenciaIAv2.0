// Barrido de parámetros: prueba combinaciones y las ordena por retorno.
// La referencia no es "ganar", es GANARLE A COMPRAR Y ESPERAR: en un mercado
// que subió 28% en 12 días, cualquier estrategia que no le gane sobra.
import { corre, comprarYesperar, usaGranularidad } from './backtest.js';
import { UMBRALES } from './lib/estrategia.js';

const combos = [];
for (const gran of [900, 3600]) {
  for (const tpM of [2.5, 4, 6]) {
    for (const slM of [1.5, 2.5, 3.5]) {
      for (const tr of [0, 2.5, 4]) {
        for (const ventana of [24, 48]) {
          combos.push({ gran, tpM, slM, tr, ventana });
        }
      }
    }
  }
}

const filas = [];
for (const c of combos) {
  usaGranularidad(c.gran);
  const tacticas = {
    momentum: { tp: { atr: c.tpM, pctMin: 1.5 }, sl: { atr: c.slM, pctMin: 0.9 },
                minutos: c.gran / 60 * 60, trailing: c.tr },
    reversion: { tp: { atr: c.tpM * 0.8, pctMin: 1.2 },
                 sl: { atr: c.slM, pctMin: 0.9 }, minutos: c.gran / 60 * 40, trailing: 0 },
    ruptura: { tp: { atr: c.tpM * 1.4, pctMin: 2.5 },
               sl: { atr: c.slM, pctMin: 1.0 }, minutos: c.gran / 60 * 90,
               trailing: c.tr || 3 },
  };
  const u = { ...UMBRALES, ventanaRuptura: c.ventana };
  const r = corre({ tacticas, umbrales: u });
  filas.push({ ...c, ops: r.cerradas.length, ret: r.retorno,
               dias: r.dias, hold: comprarYesperar() });
}

filas.sort((a, b) => (b.ret - b.hold) - (a.ret - a.hold));
console.log('gran  tp   sl   trail vent  ops   estrategia  comprar-y-esperar  ventaja');
for (const f of filas.slice(0, 14)) {
  console.log(
    `${String(f.gran).padStart(4)} ${String(f.tpM).padStart(4)} ` +
    `${String(f.slM).padStart(4)} ${String(f.tr).padStart(5)} ` +
    `${String(f.ventana).padStart(4)} ${String(f.ops).padStart(5)} ` +
    `${f.ret.toFixed(2).padStart(11)}% ${f.hold.toFixed(2).padStart(16)}% ` +
    `${(f.ret - f.hold).toFixed(2).padStart(8)}`);
}
