// Precios en vivo. La vela base es de 1 hora (la estrategia las junta de a 4);
// el precio para stops llega tick a tick por WebSocket.
// Coinbase Exchange es la fuente: su API pública no pide
// llave y, a diferencia de Binance, no bloquea por región (Binance contesta
// 451 desde este servidor). Kraken queda de respaldo si Coinbase se cae.
//
// Historia: /candles a 1 minuto (300 velas, o sea 5 horas).
// Vivo:     WebSocket canal `ticker`; si el socket muere, se cae a sondeo REST.
import WebSocket from 'ws';

const CB = 'https://api.exchange.coinbase.com';
const CB_WS = 'wss://ws-feed.exchange.coinbase.com';
const KRAKEN = 'https://api.kraken.com/0/public/Ticker';
const KRAKEN_PAR = {
  'BTC-USD': 'XBTUSD', 'ETH-USD': 'ETHUSD', 'SOL-USD': 'SOLUSD',
  'XRP-USD': 'XRPUSD', 'LINK-USD': 'LINKUSD', 'DOGE-USD': 'DOGEUSD',
};

export class Feed {
  constructor(simbolos, { alVela = () => {}, granularidad = 3600 } = {}) {
    this.simbolos = simbolos;
    this.gran = granularidad;          // segundos por vela base
    this.alVela = alVela;              // (simbolo, velas) al cerrar cada minuto
    this.velas = new Map();            // simbolo -> [{t,o,h,l,c,v}]
    this.ultimo = new Map();           // simbolo -> precio
    this.enCurso = new Map();          // vela del minuto que va corriendo
    this.fuente = 'iniciando';
    this.ws = null;
    this.vivo = 0;                     // último tick recibido (ms)
  }

  async arranca() {
    await Promise.all(this.simbolos.map((s) => this.historia(s)));
    this.conecta();
    // Vigilante: si el socket lleva 20 s callado, se sondea por REST y se
    // reconecta. Un feed mudo es peor que uno lento: el motor cree que el
    // precio no se movió y deja las posiciones sin stop.
    this.reloj = setInterval(() => this.late(), 5000);
  }

  para() {
    clearInterval(this.reloj);
    try { this.ws?.close(); } catch { /* ya estaba cerrado */ }
  }

  // Coinbase da 300 velas por llamada. La estrategia junta las de 1 h de a 4 y
  // necesita 50 velas de 4 h para la EMA lenta, o sea 200 horas: con una sola
  // página iba justo, así que se paginan tres.
  async historia(simbolo, paginas = 3) {
    const filas = [];
    let fin = new Date();
    for (let i = 0; i < paginas; i++) {
      const ini = new Date(fin.getTime() - this.gran * 300 * 1000);
      const u = `${CB}/products/${simbolo}/candles?granularity=${this.gran}` +
                `&start=${ini.toISOString()}&end=${fin.toISOString()}`;
      const r = await fetch(u, { headers: { 'User-Agent': 'cripto-sim' } });
      if (!r.ok && i === 0) throw new Error(`historia ${simbolo}: ${r.status}`);
      if (r.ok) filas.push(...await r.json());
      fin = ini;
      await new Promise((x) => setTimeout(x, 250));
    }
    // Coinbase entrega [tiempo, bajo, alto, apertura, cierre, volumen], del
    // más nuevo al más viejo.
    const velas = filas
      .map(([t, l, h, o, c, v]) => ({ t: t * 1000, o, h, l, c, v }))
      .sort((a, b) => a.t - b.t)
      .filter((v, i, a) => i === 0 || v.t !== a[i - 1].t);
    this.velas.set(simbolo, velas);
    this.ultimo.set(simbolo, velas.at(-1)?.c ?? 0);
    return velas.length;
  }

  conecta() {
    const ws = new WebSocket(CB_WS);
    this.ws = ws;
    ws.on('open', () => {
      this.fuente = 'coinbase-ws';
      ws.send(JSON.stringify({
        type: 'subscribe', product_ids: this.simbolos,
        channels: ['ticker'],
      }));
    });
    ws.on('message', (buf) => {
      let m;
      try { m = JSON.parse(buf); } catch { return; }
      if (m.type !== 'ticker' || !m.product_id) return;
      this.tick(m.product_id, Number(m.price), Number(m.last_size) || 0);
    });
    ws.on('close', () => { if (this.reloj) setTimeout(() => this.conecta(), 3000); });
    ws.on('error', () => { /* el 'close' hace la reconexión */ });
  }

  tick(simbolo, precio, tam) {
    if (!precio || Number.isNaN(precio)) return;
    this.vivo = Date.now();
    this.ultimo.set(simbolo, precio);
    const paso = this.gran * 1000;
    const minuto = Math.floor(Date.now() / paso) * paso;
    const abierta = this.enCurso.get(simbolo);
    if (!abierta || abierta.t !== minuto) {
      if (abierta) {
        const velas = this.velas.get(simbolo) ?? [];
        velas.push(abierta);
        if (velas.length > 800) velas.shift();
        this.velas.set(simbolo, velas);
        this.alVela(simbolo, velas);
      }
      this.enCurso.set(simbolo,
        { t: minuto, o: precio, h: precio, l: precio, c: precio, v: tam });
      return;
    }
    abierta.h = Math.max(abierta.h, precio);
    abierta.l = Math.min(abierta.l, precio);
    abierta.c = precio;
    abierta.v += tam;
  }

  async late() {
    if (Date.now() - this.vivo < 20000) return;
    // El socket está mudo: se sondea a mano para no quedarse ciego.
    for (const s of this.simbolos) {
      const p = await this.precioRest(s);
      if (p) this.tick(s, p, 0);
    }
  }

  async precioRest(simbolo) {
    try {
      const r = await fetch(`${CB}/products/${simbolo}/ticker`,
                            { headers: { 'User-Agent': 'cripto-sim' } });
      if (r.ok) {
        this.fuente = 'coinbase-rest';
        return Number((await r.json()).price);
      }
    } catch { /* se intenta Kraken */ }
    try {
      const par = KRAKEN_PAR[simbolo];
      const r = await fetch(`${KRAKEN}?pair=${par}`);
      const j = await r.json();
      const clave = Object.keys(j.result ?? {})[0];
      if (clave) {
        this.fuente = 'kraken-rest';
        return Number(j.result[clave].c[0]);
      }
    } catch { /* ni modo: se queda con el último precio conocido */ }
    return null;
  }

  precio(simbolo) { return this.ultimo.get(simbolo) ?? 0; }

  // Las velas cerradas más la que va corriendo: los indicadores necesitan el
  // precio de ahorita, no el de hace un minuto.
  serie(simbolo) {
    const v = this.velas.get(simbolo) ?? [];
    const a = this.enCurso.get(simbolo);
    return a ? [...v, a] : v;
  }
}
