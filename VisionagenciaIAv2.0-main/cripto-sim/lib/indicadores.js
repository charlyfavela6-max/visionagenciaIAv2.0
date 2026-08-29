// Indicadores sobre arreglos de velas {t, o, h, l, c, v}. Todos devuelven
// null cuando no hay suficiente historia: el motor no abre nada con null.

export function ema(valores, periodo) {
  if (valores.length < periodo) return null;
  const k = 2 / (periodo + 1);
  let e = valores.slice(0, periodo).reduce((a, b) => a + b, 0) / periodo;
  for (let i = periodo; i < valores.length; i++) e = valores[i] * k + e * (1 - k);
  return e;
}

export function rsi(cierres, periodo = 14) {
  if (cierres.length < periodo + 1) return null;
  let ganancia = 0, perdida = 0;
  for (let i = cierres.length - periodo; i < cierres.length; i++) {
    const d = cierres[i] - cierres[i - 1];
    if (d >= 0) ganancia += d; else perdida -= d;
  }
  if (perdida === 0) return 100;
  const rs = (ganancia / periodo) / (perdida / periodo);
  return 100 - 100 / (1 + rs);
}

// Rango medio verdadero: la unidad con la que medimos "cuánto se mueve" cada
// moneda. Sin esto un stop de 0.7% es enorme para BTC y ridículo para DOGE.
export function atr(velas, periodo = 14) {
  if (velas.length < periodo + 1) return null;
  let suma = 0;
  for (let i = velas.length - periodo; i < velas.length; i++) {
    const p = velas[i - 1].c;
    suma += Math.max(velas[i].h - velas[i].l, Math.abs(velas[i].h - p),
                     Math.abs(velas[i].l - p));
  }
  return suma / periodo;
}

export const maximo = (velas, n) => Math.max(...velas.slice(-n).map((v) => v.h));
export const promedioVol = (velas, n) =>
  velas.slice(-n).reduce((a, v) => a + v.v, 0) / Math.min(n, velas.length);
