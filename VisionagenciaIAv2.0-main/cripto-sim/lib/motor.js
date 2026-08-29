// El motor de la simulación: abre y cierra posiciones de mentiras contra
// precios de verdad. No toca ningún exchange, no hay llaves de trading y no
// existe forma de que mande una orden real: sólo aritmética sobre el precio
// que publica Coinbase.
import fs from 'node:fs';
import path from 'node:path';
import { REGLAS, TACTICAS, SIMBOLOS, HORAS_VELA, agrupa, entrada, salida,
         protecciones } from './estrategia.js';

const ARCHIVO = path.join(process.cwd(), 'estado', 'corrida.json');

const vacio = () => ({
  corriendo: false, capitalInicial: 0, efectivo: 0,
  posiciones: [], cerradas: [], inicio: null, fin: null,
  siguienteId: 1, ultimoResumen: 0,
});

export class Motor {
  constructor(feed, { avisa = async () => {} } = {}) {
    this.feed = feed;
    this.avisa = avisa;                 // (texto) -> manda por WhatsApp
    this.e = this.lee();
    this.ultimaVela = new Map();        // simbolo -> t de la última vela de 4 h
  }

  // La serie con la que piensa la estrategia: las velas de 1 h del feed
  // juntadas de a 4.
  serie(simbolo) { return agrupa(this.feed.serie(simbolo), HORAS_VELA); }

  lee() {
    try { return { ...vacio(), ...JSON.parse(fs.readFileSync(ARCHIVO, 'utf8')) }; }
    catch { return vacio(); }
  }

  guarda() {
    fs.mkdirSync(path.dirname(ARCHIVO), { recursive: true });
    fs.writeFileSync(ARCHIVO, JSON.stringify(this.e, null, 2));
  }

  // ------------------------------------------------------------ el dinero --
  valorPosiciones() {
    return this.e.posiciones.reduce(
      (a, p) => a + p.unidades * this.feed.precio(p.simbolo), 0);
  }

  capital() { return this.e.efectivo + this.valorPosiciones(); }

  ganancia() {
    const g = this.capital() - this.e.capitalInicial;
    return { abs: g, pct: this.e.capitalInicial ? g / this.e.capitalInicial * 100 : 0 };
  }

  // -------------------------------------------------------------- arrancar --
  async arranca(monto) {
    if (this.e.corriendo) throw new Error('ya hay una corrida en marcha');
    if (!(monto > 0)) throw new Error('el monto tiene que ser mayor que cero');
    this.e = { ...vacio(), corriendo: true, capitalInicial: monto,
               efectivo: monto, inicio: Date.now(), ultimoResumen: Date.now() };
    this.guarda();
    await this.avisa(
      `🟢 *Simulación iniciada*\n` +
      `Capital: $${monto.toFixed(2)} USD (simulado)\n` +
      `Estrategia: tendencia + reversión + ruptura (velas de ${HORAS_VELA} h)\n` +
      `Monedas: ${SIMBOLOS.map((s) => s.split('-')[0]).join(', ')}\n` +
      `Máx ${REGLAS.maxAbiertas} posiciones, ${(REGLAS.fraccion * 100).toFixed(0)}% del capital cada una.`);
    return this.resumen();
  }

  async detiene(motivo = 'a mano') {
    if (!this.e.corriendo) return this.resumen();
    for (const p of [...this.e.posiciones]) this.cierra(p, 'corrida detenida');
    this.e.corriendo = false;
    this.e.fin = Date.now();
    this.guarda();
    const g = this.ganancia();
    await this.avisa(
      `🔴 *Simulación detenida* (${motivo})\n` +
      `Capital final: $${this.capital().toFixed(2)}\n` +
      `Resultado: ${g.abs >= 0 ? '+' : ''}$${g.abs.toFixed(2)} (${g.pct.toFixed(2)}%)\n` +
      `Operaciones cerradas: ${this.e.cerradas.length}`);
    return this.resumen();
  }

  // ------------------------------------------------------- abrir  y cerrar --
  abre(simbolo, tactica, razon, velas) {
    const precio = this.feed.precio(simbolo);
    if (!precio) return null;

    const monto = this.capital() * REGLAS.fraccion;
    if (monto > this.e.efectivo) return null;      // no se apalanca, jamás

    const precioEntrada = precio * (1 + REGLAS.deslizamiento);
    const comision = monto * REGLAS.comision;
    const unidades = (monto - comision) / precioEntrada;
    const prot = protecciones(tactica, precioEntrada, velas);

    const p = {
      id: this.e.siguienteId++, simbolo, tactica, razon,
      abierta: Date.now(), precioEntrada, unidades,
      invertido: monto, comisiones: comision,
      stopDuro: prot.stopDuro, trailing: prot.trailing,
      maxVisto: precioEntrada, velas: 0,
    };
    this.e.efectivo -= monto;
    this.e.posiciones.push(p);
    this.guarda();
    return p;
  }

  cierra(p, motivo) {
    const precio = this.feed.precio(p.simbolo) || p.precioEntrada;
    const salida = precio * (1 - REGLAS.deslizamiento);
    const bruto = p.unidades * salida;
    const comision = bruto * REGLAS.comision;
    const neto = bruto - comision;
    const g = neto - p.invertido;

    this.e.efectivo += neto;
    this.e.posiciones = this.e.posiciones.filter((x) => x.id !== p.id);
    const cerrada = {
      ...p, cerrada: Date.now(), precioSalida: salida, motivo,
      comisiones: p.comisiones + comision, ganancia: g,
      gananciaPct: g / p.invertido * 100,
      minutos: Math.round((Date.now() - p.abierta) / 60000),
    };
    this.e.cerradas.unshift(cerrada);
    if (this.e.cerradas.length > 400) this.e.cerradas.pop();
    this.guarda();
    return cerrada;
  }

  // -------------------------------------------------------------- el pulso --
  // Dos ritmos distintos, a propósito:
  //   · cada tick se revisa SÓLO el stop de emergencia y el trailing, porque
  //     esos no pueden esperar cuatro horas.
  //   · las señales de entrada y de salida se miran cuando CIERRA una vela de
  //     4 h. Reaccionar a media vela es perseguir ruido, y fue justo lo que
  //     hizo que la primera versión operara 400 veces y perdiera en comisiones.
  async pulso() {
    if (!this.e.corriendo) return;

    for (const p of [...this.e.posiciones]) {
      const precio = this.feed.precio(p.simbolo);
      if (!precio) continue;
      if (precio > p.maxVisto) p.maxVisto = precio;
      let motivo = null;
      if (precio <= p.stopDuro) motivo = 'stop de emergencia';
      else if (p.trailing && p.maxVisto > p.precioEntrada
               && precio <= p.maxVisto - p.trailing) motivo = 'trailing';
      if (motivo) await this.anuncioCierre(this.cierra(p, motivo));
    }

    for (const s of SIMBOLOS) {
      const velas = this.serie(s);
      const ultima = velas.at(-1)?.t;
      if (!ultima || this.ultimaVela.get(s) === ultima) continue;
      const primera = this.ultimaVela.get(s) === undefined;
      this.ultimaVela.set(s, ultima);
      if (primera) continue;          // la primera pasada sólo toma la foto

      for (const p of this.e.posiciones.filter((x) => x.simbolo === s)) {
        p.velas++;
        const motivo = salida(velas, p);
        if (motivo) await this.anuncioCierre(this.cierra(p, motivo));
      }
      await this.revisaEntradas(s, velas);
    }
    this.guarda();
  }

  async anuncioCierre(c) {
    await this.avisa(
      `${c.ganancia >= 0 ? '✅' : '❌'} *Cerrada* ${c.simbolo} · ${c.tactica}\n` +
      `${c.motivo} · ${c.minutos} min\n` +
      `Entró $${c.precioEntrada.toFixed(4)} → salió $${c.precioSalida.toFixed(4)}\n` +
      `${c.ganancia >= 0 ? '+' : ''}$${c.ganancia.toFixed(2)} (${c.gananciaPct.toFixed(2)}%)\n` +
      `Capital: $${this.capital().toFixed(2)}`);
  }

  async revisaEntradas(simbolo, velas) {
    if (!this.e.corriendo) return;
    if (this.e.posiciones.length >= REGLAS.maxAbiertas) return;
    if (this.e.posiciones.some((p) => p.simbolo === simbolo)) return;  // una por moneda

    const s = entrada(velas);
    if (!s) return;
    const p = this.abre(simbolo, s.tactica, s.razon, velas);
    if (!p) return;
    await this.avisa(
      `📈 *Abrió* ${simbolo} · ${p.tactica}\n` +
      `${p.razon}\n` +
      `Entrada $${p.precioEntrada.toFixed(4)} · $${p.invertido.toFixed(2)}\n` +
      `Stop de emergencia $${p.stopDuro.toFixed(4)}\n` +
      `Capital: $${this.capital().toFixed(2)}`);
  }

  async resumenHorario() {
    if (!this.e.corriendo) return;
    if (Date.now() - this.e.ultimoResumen < 3600000) return;
    this.e.ultimoResumen = Date.now();
    this.guarda();

    const g = this.ganancia();
    const porTactica = {};
    for (const c of this.e.cerradas) {
      const t = porTactica[c.tactica] ??= { n: 0, g: 0, ganadas: 0 };
      t.n++; t.g += c.ganancia; if (c.ganancia > 0) t.ganadas++;
    }
    const lineas = Object.entries(porTactica).map(([k, v]) =>
      `  ${k}: ${v.n} ops, ${v.ganadas}/${v.n} en verde, ${v.g >= 0 ? '+' : ''}$${v.g.toFixed(2)}`);
    const abiertas = this.e.posiciones.map((p) => {
      const pr = this.feed.precio(p.simbolo);
      const pl = (pr * p.unidades - p.invertido);
      return `  ${p.simbolo} ${p.tactica}: ${pl >= 0 ? '+' : ''}$${pl.toFixed(2)}`;
    });
    const horas = ((Date.now() - this.e.inicio) / 3600000).toFixed(1);

    await this.avisa(
      `📊 *Resumen* · ${horas} h corriendo\n` +
      `Capital: $${this.capital().toFixed(2)} (empezó con $${this.e.capitalInicial.toFixed(2)})\n` +
      `Resultado: ${g.abs >= 0 ? '+' : ''}$${g.abs.toFixed(2)} (${g.pct.toFixed(2)}%)\n` +
      `Abiertas (${this.e.posiciones.length}):\n${abiertas.join('\n') || '  ninguna'}\n` +
      `Por táctica:\n${lineas.join('\n') || '  todavía nada cerrado'}`);
  }

  // ----------------------------------------------------------- para la web --
  resumen() {
    const g = this.ganancia();
    const porTactica = {};
    for (const c of this.e.cerradas) {
      const t = porTactica[c.tactica] ??= { n: 0, ganancia: 0, ganadas: 0 };
      t.n++; t.ganancia += c.ganancia; if (c.ganancia > 0) t.ganadas++;
    }
    return {
      corriendo: this.e.corriendo,
      capitalInicial: this.e.capitalInicial,
      capital: this.capital(),
      efectivo: this.e.efectivo,
      ganancia: g.abs, gananciaPct: g.pct,
      inicio: this.e.inicio, fin: this.e.fin,
      fuente: this.feed.fuente,
      precios: Object.fromEntries(SIMBOLOS.map((s) => [s, this.feed.precio(s)])),
      posiciones: this.e.posiciones.map((p) => {
        const pr = this.feed.precio(p.simbolo);
        const vivo = pr * p.unidades - p.invertido;
        return { ...p, precio: pr, ganancia: vivo,
                 gananciaPct: vivo / p.invertido * 100 };
      }),
      cerradas: this.e.cerradas.slice(0, 60),
      porTactica,
    };
  }
}
