// LA ESTRATEGIA. Tres tácticas long-only corriendo a la vez sobre el mismo
// capital, cada una etiquetada, para poder ver en vivo cuál gana y podarla.
//
//   tendencia — el corazón: entra cuando la EMA20 cruza arriba de la EMA50 y
//               sale cuando el precio cierra debajo de la EMA20. Deja correr
//               las ganadoras y corta rápido las perdedoras.
//   reversion — compra el pánico (RSI < 30) y suelta en cuanto el RSI vuelve
//               a la mitad.
//   ruptura   — compra el máximo de 5 días con volumen y lo suelta con un
//               stop que sube.
//
// Tres cosas que se aprendieron a golpes y que NO hay que deshacer:
//
// 1. La vela es de 4 HORAS. Con velas de 1 minuto el ATR de BTC es ~0.05% del
//    precio: un objetivo de 2 ATR quedaba en 0.1%, por DEBAJO del 0.2% que se
//    va en comisiones. Perdía por construcción.
// 2. Operar poco es la mitad del resultado. Las versiones que hacían 400
//    operaciones en 125 días perdían ~20% SÓLO en comisiones. Ésta hace ~27.
// 3. El trailing stop empeoró TODAS las variantes que se probaron (de +21% a
//    +7%): en cripto el ruido normal lo salta antes de que corra el movimiento.
//    Por eso `tendencia` sale por la EMA, no por trailing.
import { ema, rsi, atr, maximo, promedioVol } from './indicadores.js';

export const SIMBOLOS = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'XRP-USD',
                         'LINK-USD', 'DOGE-USD'];

export const HORAS_VELA = 4;          // la unidad de tiempo de la estrategia
export const GRANULARIDAD = 3600;     // lo que se le pide a Coinbase (1 h)

export const REGLAS = {
  fraccion: 0.20,
  maxAbiertas: 4,
  comision: 0.001,       // 0.1% por lado, taker
  deslizamiento: 0.0003,
};

export const TACTICAS = {
  tendencia: { rapida: 20, lenta: 50, stopDuro: 12, velasMax: 120 },
  reversion: { rsiEntra: 30, rsiSale: 55, stopDuro: 8, velasMax: 60 },
  ruptura: { ventana: 30, vol: 1.4, trailingAtr: 4, stopDuro: 10, velasMax: 90 },
};

// Junta velas chicas en velas de la temporalidad de la estrategia.
export function agrupa(velas, k) {
  const out = [];
  for (let i = 0; i + k <= velas.length; i += k) {
    const g = velas.slice(i, i + k);
    out.push({ t: g[0].t, o: g[0].o, c: g.at(-1).c,
               h: Math.max(...g.map((v) => v.h)),
               l: Math.min(...g.map((v) => v.l)),
               v: g.reduce((a, v) => a + v.v, 0) });
  }
  return out;
}

// ------------------------------------------------------------- entrar ------
export function entrada(velas, t = TACTICAS) {
  if (velas.length < t.tendencia.lenta + 5) return null;
  const c = velas.map((v) => v.c);
  const precio = c.at(-1);
  const prev = c.slice(0, -1);

  // 1. tendencia: el cruce tiene que ser NUEVO.
  const er = ema(c, t.tendencia.rapida), el = ema(c, t.tendencia.lenta);
  const erP = ema(prev, t.tendencia.rapida), elP = ema(prev, t.tendencia.lenta);
  if (er && el && erP && elP && erP <= elP && er > el && precio > er) {
    return { tactica: 'tendencia', razon: 'EMA20 cruzó arriba de la EMA50' };
  }

  // 2. reversion: pánico medido.
  const r = rsi(c, 14);
  if (r !== null && r < t.reversion.rsiEntra) {
    return { tactica: 'reversion', razon: `RSI ${r.toFixed(0)}, sobrevendido` };
  }

  // 3. ruptura: máximo de la ventana CON volumen. Se compara contra las velas
  //    anteriores, no contra la actual, que ya trae el máximo nuevo.
  const previo = velas.slice(0, -1);
  if (previo.length >= t.ruptura.ventana) {
    const techo = maximo(previo, t.ruptura.ventana);
    const volMedio = promedioVol(previo, t.ruptura.ventana);
    const vol = velas.at(-1).v;
    if (precio > techo && volMedio > 0 && vol > volMedio * t.ruptura.vol) {
      return { tactica: 'ruptura',
               razon: `máximo de ${(t.ruptura.ventana * HORAS_VELA / 24).toFixed(0)} ` +
                      `días con ${(vol / volMedio).toFixed(1)}x volumen` };
    }
  }
  return null;
}

// ------------------------------------------------------------- salir -------
// Devuelve el motivo del cierre, o null. `p` es la posición abierta.
export function salida(velas, p, t = TACTICAS) {
  const c = velas.map((v) => v.c);
  const precio = c.at(-1);
  const regla = t[p.tactica];

  if (precio <= p.stopDuro) return 'stop de emergencia';
  if (p.velas >= regla.velasMax) return 'se acabó el tiempo';

  if (p.tactica === 'tendencia') {
    const er = ema(c, regla.rapida);
    if (er && precio < er) return 'cerró bajo la EMA20';
  }
  if (p.tactica === 'reversion') {
    const r = rsi(c, 14);
    if (r !== null && r > regla.rsiSale) return `RSI de vuelta en ${r.toFixed(0)}`;
  }
  if (p.tactica === 'ruptura' && p.trailing && p.maxVisto > p.precioEntrada
      && precio <= p.maxVisto - p.trailing) {
    return 'trailing';
  }
  return null;
}

// Lo que hay que calcular al abrir: stop de emergencia y trailing.
export function protecciones(tactica, entrada, velas, t = TACTICAS) {
  const regla = t[tactica];
  return {
    stopDuro: entrada * (1 - regla.stopDuro / 100),
    trailing: regla.trailingAtr ? (atr(velas, 14) ?? 0) * regla.trailingAtr : 0,
  };
}
