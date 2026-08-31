// Simulacion sin navegador: yo sigo el libro de Polgar, Kasparov el suyo.
import { Chess, moveToUci } from '../public/js/chess.mjs';
import { posKey } from '../public/js/poskey.mjs';
import { createSearcher } from '../public/js/search.mjs';
import { STYLES } from '../public/js/eval.mjs';
import { explicarJugada } from '../public/js/explain.mjs';

const API = process.env.API || 'http://localhost:3000';
const consultar = async (chess, jugador) => {
  const r = await fetch(`${API}/api/consejo`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ clave: posKey(chess.key()), jugador }),
  });
  return r.json();
};
const uciAMove = (c, u) => c.generateMoves().find((m) => moveToUci(m) === u) ?? null;

const miColor = 0;
const chess = new Chess();
const sPolgar = createSearcher(STYLES.polgar), sKasp = createSearcher(STYLES.kasparov);
let enLibroYo = 0, enLibroEl = 0, ply = 0;

while (!chess.gameOver().over && ply < 60) {
  const soyYo = chess.turn === miColor;
  const libro = await consultar(chess, soyYo ? 'polgar' : 'kasparov');
  let move = null, etiqueta;
  const validas = (libro.jugadas || []).filter((j) => uciAMove(chess, j.uci));
  if (validas.length) {
    const j = validas[0];
    move = uciAMove(chess, j.uci);
    etiqueta = `libro(${j.partidas}) ${j.partida.blancas.split(',')[0]}-${j.partida.negras.split(',')[0]} ${j.partida.anio}`;
    if (soyYo) enLibroYo++; else enLibroEl++;
  } else {
    const r = (soyYo ? sPolgar : sKasp).analyze(chess, { maxDepth: 4, timeMs: 600 });
    move = uciAMove(chess, r.lines[0].uci);
    etiqueta = `motor d${r.depth} ${(r.lines[0].score / 100).toFixed(2)}`;
  }
  const ex = explicarJugada(chess.fen(), move);
  const san = chess.moveToSan(move);
  console.log(`${String(Math.floor(ply / 2) + 1).padStart(2)}${soyYo ? '.' : '…'} ${san.padEnd(7)} ${soyYo ? 'POLGAR ' : 'KASPAROV'} ${etiqueta.padEnd(46)} ${ex.tags.join(',')}`);
  chess.makeMove(move);
  ply++;
}
console.log(`\nfin: ${JSON.stringify(chess.gameOver())}`);
console.log(`jugadas de libro — yo: ${enLibroYo}, Kasparov: ${enLibroEl}, total plies: ${ply}`);
