// ¿Qué táctica aporta y cuál estorba? Cada una sola, con la cartera entera a
// su disposición, contra comprar y esperar.
import { corre, comprarYesperar } from './backtest.js';

const hold = comprarYesperar();
const casos = [['tendencia'], ['reversion'], ['ruptura'],
               ['tendencia', 'ruptura'], null];
console.log('táctica'.padEnd(22) + 'ops   en verde   retorno   ventaja');
for (const solo of casos) {
  const r = corre({ solo });
  const g = r.cerradas.filter((c) => c.ganancia > 0).length;
  console.log((solo ? solo.join(' + ') : 'las tres juntas').padEnd(22) +
    String(r.cerradas.length).padStart(3) +
    `${(g + '/' + r.cerradas.length).padStart(10)}` +
    `${((r.retorno >= 0 ? '+' : '') + r.retorno.toFixed(2) + '%').padStart(10)}` +
    `${((r.retorno - hold >= 0 ? '+' : '') + (r.retorno - hold).toFixed(2)).padStart(10)}`);
}
console.log('comprar y esperar'.padEnd(22) + '  —         —' +
            ((hold >= 0 ? '+' : '') + hold.toFixed(2) + '%').padStart(10));
