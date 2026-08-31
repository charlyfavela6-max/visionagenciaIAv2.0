// Convierte los PGN de partidas reales en un "libro" indexado por posicion.
// Salida: public/data/<slug>-book.json
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Chess, moveToUci } from '../public/js/chess.mjs';
import { posKey } from '../public/js/poskey.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, '..');
const MAX_PLY = Number(process.env.MAX_PLY || 80);

function* parsePgn(text) {
  const blocks = text.split(/\r?\n\r?\n(?=\[)/);
  let headers = null;
  for (const raw of blocks) {
    const block = raw.trim();
    if (!block) continue;
    if (block.startsWith('[')) {
      const h = {};
      let movetext = '';
      for (const line of block.split(/\r?\n/)) {
        const m = line.match(/^\[(\w+)\s+"(.*)"\]\s*$/);
        if (m) h[m[1]] = m[2];
        else movetext += line + ' ';
      }
      if (movetext.trim()) { yield { headers: h, movetext: movetext.trim() }; headers = null; }
      else headers = h;
    } else if (headers) {
      yield { headers, movetext: block.replace(/\r?\n/g, ' ') };
      headers = null;
    }
  }
}

function movetextToSans(movetext) {
  return movetext
    .replace(/\{[^}]*\}/g, ' ')
    .replace(/;[^\n]*/g, ' ')
    .replace(/\$\d+/g, ' ')
    .replace(/\([^()]*\)/g, ' ')
    .replace(/\d+\.(\.\.)?/g, ' ')
    .replace(/(1-0|0-1|1\/2-1\/2|\*)\s*$/, ' ')
    .trim().split(/\s+/).filter(Boolean);
}

function buildBook({ pgnFile, playerRe, slug, label }) {
  const text = fs.readFileSync(path.join(ROOT, 'data', pgnFile), 'utf8');
  const games = [];
  const book = new Map();
  let parsed = 0, skipped = 0, badMoves = 0;

  for (const { headers, movetext } of parsePgn(text)) {
    const white = headers.White || '', black = headers.Black || '';
    const isWhite = playerRe.test(white), isBlack = playerRe.test(black);
    if (!isWhite && !isBlack) { skipped++; continue; }
    const sans = movetextToSans(movetext);
    if (sans.length < 6) { skipped++; continue; }

    const chess = new Chess();
    const uci = [];
    const ourTurn = isWhite ? 0 : 1;
    const positions = [];
    let ok = true;
    for (let ply = 0; ply < sans.length; ply++) {
      const turnBefore = chess.turn;
      const key = turnBefore === ourTurn && ply < MAX_PLY ? posKey(chess.key()) : null;
      const m = chess.sanToMove(sans[ply]);
      if (m === null) { ok = false; break; }
      if (key) positions.push([key, moveToUci(m), ply]);
      chess.makeMove(m);
      uci.push(moveToUci(m));
    }
    if (!ok || uci.length < 6) { badMoves++; continue; }

    const result = headers.Result || '*';
    const gi = games.length;
    games.push({
      w: white, b: black,
      e: headers.Event || '', s: headers.Site || '',
      d: (headers.Date || '').slice(0, 4),
      r: result, eco: headers.ECO || '',
      c: isWhite ? 'w' : 'b',
      mv: uci.join(' '),
    });
    // puntuacion desde el punto de vista del jugador
    const score = result === '1-0' ? (isWhite ? 1 : -1) : result === '0-1' ? (isWhite ? -1 : 1) : 0;
    for (const [key, mv, ply] of positions) {
      let entry = book.get(key);
      if (!entry) { entry = new Map(); book.set(key, entry); }
      let e = entry.get(mv);
      if (!e) { e = { mv, n: 0, w: 0, d: 0, l: 0, g: gi, p: ply }; entry.set(mv, e); }
      e.n++;
      if (score > 0) { e.w++; if (e.bg === undefined) { e.bg = gi; e.bp = ply; } }
      else if (score === 0) e.d++;
      else e.l++;
      // partida representativa: preferimos una victoria y, entre ellas, la mas reciente
      const year = +(games[gi].d || 0);
      if (e.best === undefined || (score > 0 && (e.bestScore < 1 || year > e.bestYear))) {
        if (e.best === undefined || score >= e.bestScore) {
          e.best = gi; e.bestPly = ply; e.bestScore = score; e.bestYear = year;
        }
      }
    }
    parsed++;
  }

  const out = {};
  for (const [key, entry] of book) {
    const arr = [...entry.values()]
      .sort((a, b) => (b.n - a.n) || ((b.w - b.l) - (a.w - a.l)))
      .slice(0, 4)
      .map((e) => [e.mv, e.n, e.w, e.d, e.l, e.best ?? e.g, e.bestPly ?? e.p]);
    out[key] = arr;
  }

  const json = { meta: { player: label, slug, games: games.length, positions: Object.keys(out).length, maxPly: MAX_PLY }, games, book: out };
  const file = path.join(ROOT, 'books', `${slug}-book.json`);
  fs.writeFileSync(file, JSON.stringify(json));
  const kb = (fs.statSync(file).size / 1024).toFixed(0);
  console.log(`${label}: ${parsed} partidas, ${Object.keys(out).length} posiciones, ${kb} KB (descartadas ${skipped} ajenas, ${badMoves} ilegibles)`);
  return json;
}

buildBook({ pgnFile: 'PolgarJ.pgn', playerRe: /^Polgar,\s?Ju/i, slug: 'polgar', label: 'Judit Polgar' });
buildBook({ pgnFile: 'Kasparov.pgn', playerRe: /^Kasparov,\s?G/i, slug: 'kasparov', label: 'Garry Kasparov' });
