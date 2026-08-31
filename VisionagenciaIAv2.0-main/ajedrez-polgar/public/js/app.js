import {
  Chess, WHITE, BLACK, KNIGHT, BISHOP, ROOK, QUEEN, PAWN,
  pieceType, algebraic, fromAlgebraic, sqFile, sqRank,
  mFrom, mTo, mPromo, moveToUci,
} from './chess.mjs';
import { posKey } from './poskey.mjs';
import { explicarJugada } from './explain.mjs';

const $ = (id) => document.getElementById(id);
const GLIFOS = { p: '♟', n: '♞', b: '♝', r: '♜', q: '♛', k: '♚' };
const NOMBRE_PZ = { p: 'peón', n: 'caballo', b: 'alfil', r: 'torre', q: 'dama', k: 'rey' };
const NIVELES = {
  1: { tiempo: 500, prof: 3, holgura: 90, nitidez: 0.45 },
  2: { tiempo: 1400, prof: 5, holgura: 35, nitidez: 0.8 },
  3: { tiempo: 2800, prof: 6, holgura: 12, nitidez: 0.95 },
};

const estado = {
  chess: new Chess(),
  miColor: WHITE,
  consejo: null,
  seleccion: null,
  ultima: null,
  historial: [],
  stats: { total: 0, aciertos: 0, racha: 0, mejorRacha: 0, libro: 0 },
  claves: [],
  modoFantasma: 'siempre',
  nivel: 2,
  pensando: false,
  finalizada: false,
  fantasmaVisible: true,
};

// ─────────────── worker de análisis ───────────────
let worker = null, pendientes = new Map(), contador = 0;
function iniciarWorker() {
  try {
    worker = new Worker(new URL('./worker.js', import.meta.url), { type: 'module' });
    worker.onmessage = ({ data }) => {
      const resolver = pendientes.get(data.id);
      if (resolver) { pendientes.delete(data.id); resolver(data); }
    };
    worker.onerror = () => { worker = null; };
  } catch { worker = null; }
}
iniciarWorker();

let buscadorLocal = null;
async function analizar(fen, estilo, { profundidad = 5, tiempo = 1200 } = {}) {
  if (worker) {
    const id = ++contador;
    return new Promise((resolve) => {
      pendientes.set(id, resolve);
      worker.postMessage({ id, fen, estilo, profundidad, tiempo });
      setTimeout(() => { if (pendientes.has(id)) { pendientes.delete(id); resolve({ lineas: [] }); } }, tiempo + 8000);
    });
  }
  // respaldo en el hilo principal si el navegador no soporta workers de módulo
  if (!buscadorLocal) {
    const { createSearcher } = await import('./search.mjs');
    const { STYLES } = await import('./eval.mjs');
    buscadorLocal = { polgar: createSearcher(STYLES.polgar), kasparov: createSearcher(STYLES.kasparov), neutral: createSearcher(STYLES.neutral) };
  }
  const r = buscadorLocal[estilo].analyze(new Chess(fen), { maxDepth: profundidad, timeMs: tiempo });
  return { lineas: r.lines.slice(0, 6).map((l) => ({ uci: l.uci, score: l.score })), profundidad: r.depth };
}

// ─────────────── libro de partidas reales ───────────────
async function consultarLibro(jugador) {
  try {
    const res = await fetch('/api/consejo', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ clave: posKey(estado.chess.key()), jugador }),
    });
    if (!res.ok) return { encontrado: false, jugadas: [] };
    return await res.json();
  } catch { return { encontrado: false, jugadas: [] }; }
}

// ─────────────── tablero ───────────────
const tablero = $('tablero');
const casillas = new Map();

function construirTablero() {
  tablero.innerHTML = '';
  casillas.clear();
  const filas = estado.miColor === WHITE ? [7, 6, 5, 4, 3, 2, 1, 0] : [0, 1, 2, 3, 4, 5, 6, 7];
  const cols = estado.miColor === WHITE ? [0, 1, 2, 3, 4, 5, 6, 7] : [7, 6, 5, 4, 3, 2, 1, 0];
  for (const r of filas) {
    for (const f of cols) {
      const sq = r * 16 + f;
      const nombre = algebraic(sq);
      const div = document.createElement('div');
      div.className = `casilla ${(r + f) % 2 ? 'clara' : 'oscura'}`;
      div.dataset.casilla = nombre;
      if (f === cols[0]) div.insertAdjacentHTML('beforeend', `<span class="coord r">${r + 1}</span>`);
      if (r === filas[7]) div.insertAdjacentHTML('beforeend', `<span class="coord f">${'abcdefgh'[f]}</span>`);
      div.addEventListener('click', () => clicCasilla(nombre));
      tablero.appendChild(div);
      casillas.set(nombre, div);
    }
  }
}

function coordsSvg(sq) {
  const f = sqFile(sq), r = sqRank(sq);
  const x = estado.miColor === WHITE ? f + 0.5 : 7 - f + 0.5;
  const y = estado.miColor === WHITE ? 7 - r + 0.5 : r + 0.5;
  return [x, y];
}

function pintar() {
  const chess = estado.chess;
  for (const [nombre, div] of casillas) {
    div.querySelectorAll('.pieza, .fantasma-pieza').forEach((n) => n.remove());
    div.classList.remove('origen', 'destino', 'ocupada', 'ultima', 'jaque', 'movible', 'fantasma-origen');
    const p = chess.board[fromAlgebraic(nombre)];
    if (p) {
      const color = (p & 8) ? 'b' : 'w';
      const span = document.createElement('span');
      span.className = `pieza ${color}`;
      span.textContent = glifoDe(p);
      div.appendChild(span);
      if (color === (estado.miColor === WHITE ? 'w' : 'b') && chess.turn === estado.miColor) div.classList.add('movible');
    }
  }
  if (estado.ultima) {
    casillas.get(algebraic(estado.ultima.from))?.classList.add('ultima');
    casillas.get(algebraic(estado.ultima.to))?.classList.add('ultima');
  }
  if (chess.inCheck()) casillas.get(algebraic(chess.kings[chess.turn]))?.classList.add('jaque');
  if (estado.seleccion !== null) {
    casillas.get(algebraic(estado.seleccion))?.classList.add('origen');
    for (const m of chess.generateMoves()) {
      if (mFrom(m) !== estado.seleccion) continue;
      const d = casillas.get(algebraic(mTo(m)));
      d.classList.add('destino');
      if (chess.board[mTo(m)]) d.classList.add('ocupada');
    }
  }
  pintarFantasmas();
}

function pintarFantasmas() {
  const svg = $('capa-flechas');
  svg.innerHTML = '';
  for (const div of casillas.values()) {
    div.querySelectorAll('.fantasma-pieza').forEach((n) => n.remove());
    div.classList.remove('fantasma-origen');
  }
  const c = estado.consejo;
  const debeVerse = c && !estado.finalizada && estado.chess.turn === estado.miColor
    && (estado.modoFantasma !== 'pedido' || estado.fantasmaVisible);
  if (!debeVerse) return;

  // Paso 1: la jugada sugerida. Pasos 2 y 3 (modo "plan"): las siguientes
  // jugadas NUESTRAS en la partida real de referencia, simuladas sobre el tablero.
  const pasos = [];
  const sim = new Chess(estado.chess.fen());
  const linea = (c.fuente === 'libro' && c.continuacion && c.continuacion.length) ? c.continuacion : [c.uci];
  const maxPasos = estado.modoFantasma === 'plan' ? 3 : 1;

  for (const uci of linea) {
    const m = uciAMove(sim, uci);
    if (m === null) break;
    if (sim.turn === estado.miColor) {
      pasos.push({ from: mFrom(m), to: mTo(m), glifo: glifoDe(sim.board[mFrom(m)]), n: pasos.length + 1 });
      if (pasos.length >= maxPasos) { sim.makeMove(m); break; }
    }
    sim.makeMove(m);
  }
  if (!pasos.length) {
    const m = uciAMove(estado.chess, c.uci);
    if (m === null) return;
    pasos.push({ from: mFrom(m), to: mTo(m), glifo: glifoDe(estado.chess.board[mFrom(m)]), n: 1 });
  }

  casillas.get(algebraic(pasos[0].from))?.classList.add('fantasma-origen');
  for (const paso of pasos) {
    const destino = casillas.get(algebraic(paso.to));
    if (!destino) continue;
    const fant = document.createElement('span');
    fant.className = `fantasma-pieza${paso.n > 1 ? ' paso-' + paso.n : ''}`;
    fant.innerHTML = `${paso.glifo}${paso.n > 1 ? `<span class="num">${paso.n}</span>` : ''}`;
    destino.appendChild(fant);

    dibujarFlecha(svg, coordsSvg(paso.from), coordsSvg(paso.to), paso.n);
  }
}

function dibujarFlecha(svg, [x1, y1], [x2, y2], paso) {
  const dx = x2 - x1, dy = y2 - y1;
  const largo = Math.hypot(dx, dy) || 1;
  const ux = dx / largo, uy = dy / largo;
  const fin = 0.45; // se corta antes del centro para no tapar la pieza fantasma
  const ax = x2 - ux * fin, ay = y2 - uy * fin;
  const op = paso === 1 ? 0.9 : paso === 2 ? 0.45 : 0.3;
  const ancho = paso === 1 ? 0.1 : 0.075;
  const punta = 0.2;
  const px = ax - ux * punta, py = ay - uy * punta;
  const nx = -uy * punta * 0.62, ny = ux * punta * 0.62;
  svg.insertAdjacentHTML('beforeend',
    `<line x1="${x1 + ux * 0.3}" y1="${y1 + uy * 0.3}" x2="${px}" y2="${py}" stroke="#6ad3ff" stroke-opacity="${op}"`
    + ` stroke-width="${ancho}" stroke-linecap="round"${paso > 1 ? ' stroke-dasharray="0.16 0.12"' : ''}/>`
    + `<polygon points="${ax},${ay} ${px + nx},${py + ny} ${px - nx},${py - ny}" fill="#6ad3ff" fill-opacity="${op}"/>`);
}

function glifoDe(p) {
  return GLIFOS[{ 1: 'p', 2: 'n', 3: 'b', 4: 'r', 5: 'q', 6: 'k' }[pieceType(p)]] || '';
}

// "Saint Louis Blitz 2017" + anio 2017 no debe salir dos veces
function evento(p) {
  const nombre = (p.evento || p.sede || '').trim();
  const anio = p.anio || '';
  if (!nombre) return anio;
  return nombre.includes(anio) ? nombre : `${nombre} ${anio}`;
}

function uciAMove(chess, uci) {
  if (!uci) return null;
  for (const m of chess.generateMoves()) if (moveToUci(m) === uci) return m;
  return null;
}

// ─────────────── interacción ───────────────
function clicCasilla(nombre) {
  if (estado.finalizada || estado.pensando) return;
  const chess = estado.chess;
  if (chess.turn !== estado.miColor) return;
  const sq = fromAlgebraic(nombre);

  if (estado.seleccion !== null) {
    const candidatas = chess.generateMoves().filter((m) => mFrom(m) === estado.seleccion && mTo(m) === sq);
    if (candidatas.length === 1) { estado.seleccion = null; jugarUsuario(candidatas[0]); return; }
    if (candidatas.length > 1) { estado.seleccion = null; pedirPromocion(candidatas); return; }
  }
  const p = chess.board[sq];
  estado.seleccion = (p && (p & 8 ? BLACK : WHITE) === estado.miColor) ? sq : null;
  pintar();
}

function pedirPromocion(candidatas) {
  const caja = $('promocion');
  caja.innerHTML = '';
  const color = estado.miColor === WHITE ? 'w' : 'b';
  for (const t of [QUEEN, ROOK, BISHOP, KNIGHT]) {
    const m = candidatas.find((x) => mPromo(x) === t);
    if (!m) continue;
    const b = document.createElement('button');
    b.className = `pieza ${color}`;
    b.textContent = GLIFOS[{ 2: 'n', 3: 'b', 4: 'r', 5: 'q' }[t]];
    b.onclick = () => { caja.classList.add('oculto'); jugarUsuario(m); };
    caja.appendChild(b);
  }
  caja.classList.remove('oculto');
}

async function jugarUsuario(move) {
  const chess = estado.chess;
  const uci = moveToUci(move);
  const consejo = estado.consejo;
  const fenAntes = chess.fen();
  const san = chess.moveToSan(move);
  const coincide = consejo && consejo.uci === uci;

  estado.stats.total++;
  if (coincide) {
    estado.stats.aciertos++;
    estado.stats.racha++;
    estado.stats.mejorRacha = Math.max(estado.stats.mejorRacha, estado.stats.racha);
  } else {
    estado.stats.racha = 0;
  }
  if (consejo && consejo.fuente === 'libro') estado.stats.libro++;

  chess.makeMove(move);
  estado.claves.push(chess.key());
  estado.ultima = { from: mFrom(move), to: mTo(move) };
  estado.historial.push({ san, por: 'yo', acierto: coincide, uci });
  estado.consejo = null;
  pintar(); pintarJugadas(); pintarStats();

  if (coincide) {
    mostrarAviso(`<b>Exacto: ${san}.</b> Es la jugada que Polgar jugó en esta posición.`, 'ok');
  } else if (consejo) {
    comparar(fenAntes, uci, consejo, san);
  }
  if (revisarFinal()) return;
  await turnoKasparov();
}

async function comparar(fenAntes, uciMio, consejo, sanMio) {
  const base = new Chess(fenAntes);
  const mMio = uciAMove(base, uciMio);
  const mSuyo = uciAMove(base, consejo.uci);
  if (!mMio || !mSuyo) return;
  const sanSuyo = base.moveToSan(mSuyo);
  mostrarAviso(`<b>Polgar jugó ${sanSuyo}</b>, tú jugaste ${sanMio}. Midiendo la diferencia…`, 'aviso');

  const fenA = (() => { const c = new Chess(fenAntes); c.makeMove(mMio); return c.fen(); })();
  const fenB = (() => { const c = new Chess(fenAntes); c.makeMove(mSuyo); return c.fen(); })();
  const [a, b] = await Promise.all([
    analizar(fenA, 'neutral', { profundidad: 4, tiempo: 700 }),
    analizar(fenB, 'neutral', { profundidad: 4, tiempo: 700 }),
  ]);
  if (!a.lineas.length || !b.lineas.length) return;
  const evalMio = -a.lineas[0].score, evalSuyo = -b.lineas[0].score;
  const dif = (evalSuyo - evalMio) / 100;
  const explicacion = explicarJugada(fenAntes, mSuyo);
  const juicio = dif > 1.2 ? 'Se pierde bastante.' : dif > 0.4 ? 'Se pierde algo.' : dif < -0.3 ? '¡La tuya es incluso mejor!' : 'Prácticamente igual de buena.';
  mostrarAviso(
    `<b>Polgar jugó ${sanSuyo}</b> (tú: ${sanMio}). Diferencia ${dif >= 0 ? '+' : ''}${dif.toFixed(2)}. ${juicio}<br>` +
    `<span style="color:var(--suave)">${explicacion.frases[0]}</span>`,
    dif > 0.4 ? 'aviso' : 'ok',
    [{ texto: 'Deshacer y probar la suya', accion: () => { deshacer(); } }],
  );
}

// ─────────────── turno de Kasparov ───────────────
async function turnoKasparov() {
  const chess = estado.chess;
  if (chess.turn === estado.miColor || estado.finalizada) return;
  estado.pensando = true;
  $('kasparov-fuente').textContent = 'Kasparov está pensando…';

  const libro = await consultarLibro('kasparov');
  let move = null, fuente = '';
  if (libro.encontrado) {
    const opciones = libro.jugadas.filter((j) => uciAMove(chess, j.uci));
    if (opciones.length) {
      const total = opciones.reduce((s, o) => s + o.partidas, 0);
      let r = Math.random() * total, elegida = opciones[0];
      for (const o of opciones) { r -= o.partidas; if (r <= 0) { elegida = o; break; } }
      if (estado.nivel === 3) elegida = opciones[0];
      move = uciAMove(chess, elegida.uci);
      const p = elegida.partida;
      fuente = `De <b>${p.blancas} – ${p.negras}</b>, ${evento(p)} (${p.resultado}). ${elegida.partidas} ${elegida.partidas === 1 ? 'partida suya' : 'partidas suyas'} desde esta posición.`;
    }
  }
  if (!move) {
    const cfg = NIVELES[estado.nivel];
    const r = await analizar(chess.fen(), 'kasparov', { profundidad: cfg.prof, tiempo: cfg.tiempo });
    if (!r.lineas.length) { estado.pensando = false; revisarFinal(); return; }
    const mejor = r.lineas[0].score;
    const cerca = r.lineas.filter((l) => mejor - l.score <= cfg.holgura);
    const elegida = (cerca.length > 1 && Math.random() > cfg.nitidez)
      ? cerca[Math.floor(Math.random() * cerca.length)] : r.lineas[0];
    move = uciAMove(chess, elegida.uci);
    fuente = `Fuera de sus partidas: el motor sigue con su <b>estilo</b> (espacio, piezas activas, presión). Profundidad ${r.profundidad || '—'}.`;
  }
  if (!move) { estado.pensando = false; return; }

  const san = chess.moveToSan(move);
  chess.makeMove(move);
  estado.claves.push(chess.key());
  estado.ultima = { from: mFrom(move), to: mTo(move) };
  estado.historial.push({ san, por: 'kasparov' });
  $('kasparov-san').textContent = san;
  $('kasparov-fuente').innerHTML = fuente;
  $('chip-fuente').textContent = '…';
  estado.pensando = false;
  pintar(); pintarJugadas();
  if (revisarFinal()) return;
  await calcularConsejo();
}

// ─────────────── consejo de Polgar ───────────────
async function calcularConsejo() {
  const chess = estado.chess;
  if (chess.turn !== estado.miColor || estado.finalizada) return;
  $('consejo-san').textContent = '…';
  $('consejo-fuente').textContent = 'Buscando esta posición en las partidas de Polgar…';
  $('consejo-porques').innerHTML = '';
  $('consejo-plan').innerHTML = '';
  $('alternativas').classList.add('oculto');

  const libro = await consultarLibro('polgar');
  const fen = chess.fen();
  let consejo = null;

  const validas = (libro.jugadas || []).filter((j) => uciAMove(chess, j.uci));
  if (libro.encontrado && validas.length) {
    const j = validas[0];
    const move = uciAMove(chess, j.uci);
    const p = j.partida;
    const propias = [];
    // de la continuación real, quedarse con las jugadas de nuestro bando
    for (let i = 0; i < j.continuacion.length; i += 2) propias.push(j.continuacion[i]);
    consejo = {
      uci: j.uci, move, fuente: 'libro',
      san: chess.moveToSan(move),
      partida: p, partidas: j.partidas, ganadas: j.ganadas, tablas: j.tablas, perdidas: j.perdidas,
      continuacion: j.continuacion, plan: propias,
      alternativas: validas.slice(1),
    };
  } else {
    const r = await analizar(fen, 'polgar', { profundidad: 5, tiempo: 1500 });
    if (!r.lineas.length) return;
    const move = uciAMove(chess, r.lineas[0].uci);
    if (!move) return;
    consejo = {
      uci: r.lineas[0].uci, move, fuente: 'motor', san: chess.moveToSan(move),
      profundidad: r.profundidad, puntaje: r.lineas[0].score,
      alternativas: r.lineas.slice(1, 4).map((l) => ({ uci: l.uci, puntaje: l.score })),
    };
  }
  estado.consejo = consejo;
  estado.fantasmaVisible = estado.modoFantasma !== 'pedido';
  pintarConsejo();
  pintar();
  actualizarBarraEval();
}

function pintarConsejo() {
  const c = estado.consejo;
  if (!c) return;
  const chess = estado.chess;
  $('consejo-san').textContent = c.san;
  $('chip-fuente').textContent = c.fuente === 'libro' ? 'partida real' : 'estilo Polgar';
  $('chip-fuente').className = `chip${c.fuente === 'libro' ? '' : ' motor'}`;

  if (c.fuente === 'libro') {
    const p = c.partida;
    const marcador = [c.ganadas && `${c.ganadas} ganada${c.ganadas > 1 ? 's' : ''}`, c.tablas && `${c.tablas} tabla${c.tablas > 1 ? 's' : ''}`, c.perdidas && `${c.perdidas} perdida${c.perdidas > 1 ? 's' : ''}`].filter(Boolean).join(', ');
    $('consejo-fuente').innerHTML =
      `Judit Polgar llegó aquí <b>${c.partidas}</b> ${c.partidas === 1 ? 'vez' : 'veces'} y jugó <b>${c.san}</b>${marcador ? ` (${marcador})` : ''}.<br>` +
      `Ej.: <b>${p.blancas} – ${p.negras}</b>, ${evento(p)} · ${p.resultado}${p.eco ? ` · ${p.eco}` : ''}`;
  } else {
    $('consejo-fuente').innerHTML =
      `Ya no hay partidas suyas con esta posición exacta. El motor propone la jugada más <b>polgariana</b>: ` +
      `iniciativa y ataque al rey. Profundidad ${c.profundidad || '—'}, ventaja ${(c.puntaje / 100).toFixed(2)}.`;
  }

  const ex = explicarJugada(chess.fen(), c.move);
  $('consejo-porques').innerHTML = ex.frases.slice(0, 3).map((f) => `<li>${f}</li>`).join('');

  if (c.fuente === 'libro' && c.continuacion && c.continuacion.length > 1) {
    const sim = new Chess(chess.fen());
    const sans = [];
    for (const u of c.continuacion.slice(0, 6)) {
      const m = uciAMove(sim, u);
      if (!m) break;
      sans.push(sim.moveToSan(m));
      sim.makeMove(m);
    }
    $('consejo-plan').innerHTML = `<b>Cómo siguió esa partida:</b> ${sans.join(' ')}`;
  } else {
    $('consejo-plan').innerHTML = '';
  }

  const alts = c.alternativas || [];
  $('btn-alternativas').classList.toggle('oculto', alts.length === 0);
  $('alternativas').innerHTML = alts.map((a) => {
    const m = uciAMove(chess, a.uci);
    if (!m) return '';
    const san = chess.moveToSan(m);
    const detalle = a.partidas !== undefined
      ? `${a.partidas} ${a.partidas === 1 ? 'partida' : 'partidas'}${a.partida ? ` · ${a.partida.anio}` : ''}`
      : `${(a.puntaje / 100).toFixed(2)}`;
    return `<div class="alt" data-uci="${a.uci}"><span>${san}</span><small>${detalle}</small></div>`;
  }).join('');
  $('alternativas').querySelectorAll('.alt').forEach((el) => {
    el.onclick = () => {
      const m = uciAMove(estado.chess, el.dataset.uci);
      if (m) jugarUsuario(m);
    };
  });
}

async function actualizarBarraEval() {
  const r = await analizar(estado.chess.fen(), 'neutral', { profundidad: 3, tiempo: 400 });
  if (!r.lineas.length) return;
  const desdeMiLado = estado.chess.turn === estado.miColor ? r.lineas[0].score : -r.lineas[0].score;
  const v = Math.max(-800, Math.min(800, desdeMiLado));
  const barra = $('eval-yo');
  barra.classList.toggle('negativo', v < 0);
  barra.style.setProperty('--w', `${Math.abs(v) / 16}%`);
  $('eval-txt').textContent = `${v >= 0 ? '+' : ''}${(v / 100).toFixed(1)}`;
}

// ─────────────── paneles ───────────────
function pintarJugadas() {
  const lista = $('lista-jugadas');
  lista.innerHTML = '';
  for (let i = 0; i < estado.historial.length; i += 2) {
    const a = estado.historial[i], b = estado.historial[i + 1];
    const li = document.createElement('li');
    const clase = (h) => h ? (h.por === 'yo' ? `mia ${h.acierto ? 'acierto' : 'desvio'}` : 'suya') : '';
    li.innerHTML = `<span class="num">${Math.floor(i / 2) + 1}.</span>` +
      `<span class="${clase(a)}">${a ? a.san : ''}</span>` +
      `<span class="${clase(b)}">${b ? b.san : ''}</span>`;
    lista.appendChild(li);
  }
  lista.scrollTop = lista.scrollHeight;
}

function pintarStats() {
  const s = estado.stats;
  $('st-precision').textContent = s.total ? `${Math.round(s.aciertos / s.total * 100)}%` : '—';
  $('st-racha').textContent = s.racha;
  $('st-libro').textContent = s.libro;
}

let temporizadorAviso = null;
function mostrarAviso(html, tipo = 'aviso', acciones = []) {
  const caja = $('aviso');
  caja.className = 'aviso';
  caja.style.borderLeftColor = tipo === 'ok' ? 'var(--ok)' : 'var(--rival)';
  caja.innerHTML = html;
  if (acciones.length) {
    const cont = document.createElement('div');
    cont.className = 'acciones-aviso';
    for (const a of acciones) {
      const b = document.createElement('button');
      b.className = 'btn mini';
      b.textContent = a.texto;
      b.onclick = () => { caja.classList.add('oculto'); a.accion(); };
      cont.appendChild(b);
    }
    caja.appendChild(cont);
  }
  caja.classList.remove('oculto');
  clearTimeout(temporizadorAviso);
  temporizadorAviso = setTimeout(() => caja.classList.add('oculto'), acciones.length ? 14000 : 7000);
}

function repeticion() {
  const actual = estado.claves[estado.claves.length - 1];
  return estado.claves.filter((k) => k === actual).length >= 3;
}

function revisarFinal() {
  let fin = estado.chess.gameOver();
  if (!fin.over && repeticion()) fin = { over: true, result: '1/2-1/2', reason: 'tablas por repetición de jugadas' };
  if (!fin.over) return false;
  estado.finalizada = true;
  const gane = fin.result !== '1/2-1/2' &&
    ((fin.result === '1-0') === (estado.miColor === WHITE));
  const caja = $('fin');
  caja.innerHTML = `<h2>${fin.result === '1/2-1/2' ? 'Tablas' : gane ? '¡Ganaste!' : 'Ganó Kasparov'}</h2>` +
    `<p>${fin.reason}. Coincidiste con Polgar en ${estado.stats.aciertos} de ${estado.stats.total} jugadas` +
    ` (mejor racha: ${estado.stats.mejorRacha}).</p>`;
  const b = document.createElement('button');
  b.className = 'btn primario';
  b.textContent = 'Otra partida';
  b.onclick = nuevaPartida;
  caja.appendChild(b);
  caja.classList.remove('oculto');
  pintar();
  return true;
}

function deshacer() {
  if (estado.pensando) return;
  // deshacemos hasta que vuelva a ser nuestro turno (nuestra jugada + la suya)
  let quitadas = 0;
  while (estado.chess.history.length && quitadas < 2) {
    estado.chess.undoMove();
    estado.historial.pop();
    estado.claves.pop();
    quitadas++;
    if (estado.chess.turn === estado.miColor) break;
  }
  if (estado.stats.total > 0) { estado.stats.total--; estado.stats.racha = 0; }
  estado.finalizada = false;
  estado.ultima = null;
  $('fin').classList.add('oculto');
  pintar(); pintarJugadas(); pintarStats();
  calcularConsejo();
}

async function nuevaPartida() {
  estado.chess = new Chess();
  estado.historial = [];
  estado.consejo = null;
  estado.seleccion = null;
  estado.ultima = null;
  estado.finalizada = false;
  estado.pensando = false;
  estado.stats = { total: 0, aciertos: 0, racha: 0, mejorRacha: 0, libro: 0 };
  estado.claves = [estado.chess.key()];
  $('fin').classList.add('oculto');
  $('aviso').classList.add('oculto');
  $('kasparov-san').textContent = '—';
  $('kasparov-fuente').textContent = estado.miColor === WHITE ? 'Te toca abrir.' : 'Kasparov abre con blancas.';
  construirTablero();
  pintar(); pintarJugadas(); pintarStats();
  if (estado.chess.turn !== estado.miColor) await turnoKasparov();
  else await calcularConsejo();
}

// ─────────────── controles ───────────────
$('btn-nueva').onclick = nuevaPartida;
$('btn-ayuda').onclick = () => $('dlg-ayuda').showModal();
$('btn-deshacer').onclick = deshacer;
$('btn-jugar-sugerida').onclick = () => {
  if (estado.consejo && estado.chess.turn === estado.miColor && !estado.pensando) {
    if (estado.modoFantasma === 'pedido' && !estado.fantasmaVisible) {
      estado.fantasmaVisible = true; pintarFantasmas(); return;
    }
    jugarUsuario(estado.consejo.move);
  }
};
$('btn-alternativas').onclick = () => $('alternativas').classList.toggle('oculto');
$('sel-fantasma').onchange = (e) => {
  estado.modoFantasma = e.target.value;
  estado.fantasmaVisible = e.target.value !== 'pedido';
  guardarAjustes(); pintarFantasmas();
};
$('sel-nivel').onchange = (e) => { estado.nivel = +e.target.value; guardarAjustes(); };
$('sel-color').onchange = (e) => {
  estado.miColor = e.target.value === 'w' ? WHITE : BLACK;
  guardarAjustes(); nuevaPartida();
};

function guardarAjustes() {
  try {
    localStorage.setItem('ajedrez-polgar', JSON.stringify({
      fantasma: estado.modoFantasma, nivel: estado.nivel, color: estado.miColor,
    }));
  } catch { /* modo privado */ }
}
function cargarAjustes() {
  try {
    const a = JSON.parse(localStorage.getItem('ajedrez-polgar') || '{}');
    if (a.fantasma) { estado.modoFantasma = a.fantasma; $('sel-fantasma').value = a.fantasma; }
    if (a.nivel) { estado.nivel = a.nivel; $('sel-nivel').value = String(a.nivel); }
    if (a.color !== undefined) { estado.miColor = a.color; $('sel-color').value = a.color === WHITE ? 'w' : 'b'; }
  } catch { /* nada */ }
}

document.addEventListener('keydown', (e) => {
  if (e.key === 'h' && estado.modoFantasma === 'pedido') { estado.fantasmaVisible = !estado.fantasmaVisible; pintarFantasmas(); }
  if (e.key === 'Enter') $('btn-jugar-sugerida').click();
});

(async function iniciar() {
  cargarAjustes();
  try {
    const salud = await (await fetch('/api/salud')).json();
    const p = salud.libros?.polgar, k = salud.libros?.kasparov;
    $('subtitulo').textContent = p && k
      ? `${p.games} partidas de Polgar · ${k.games} de Kasparov · jugadas reales`
      : 'Libro no disponible: se juega solo con el motor de estilo';
  } catch {
    $('subtitulo').textContent = 'Sin conexión al libro: se juega solo con el motor de estilo';
  }
  await nuevaPartida();
})();
