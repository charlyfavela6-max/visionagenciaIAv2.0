// Busqueda negamax con poda alfa-beta, quiescencia y orden de jugadas.
import { Chess, pieceType, mFrom, mTo, mFlags, mPromo, moveToUci, F_CAPTURE, F_PROMO } from './chess.mjs';
import { evaluate, VALUES, STYLES } from './eval.mjs';

export const MATE = 100000;

function orderMoves(chess, moves, ttMove, killers, ply) {
  const scored = moves.map((m) => {
    let s = 0;
    if (m === ttMove) s += 1000000;
    const flags = mFlags(m);
    if (flags & F_CAPTURE) {
      const victim = chess.board[mTo(m)];
      const attacker = chess.board[mFrom(m)];
      s += 100000 + (victim ? VALUES[pieceType(victim)] : 100) * 10 - VALUES[pieceType(attacker)];
    }
    if (flags & F_PROMO) s += 90000 + VALUES[mPromo(m)];
    const k = killers[ply];
    if (k && (m === k[0] || m === k[1])) s += 80000;
    return { m, s };
  });
  scored.sort((a, b) => b.s - a.s);
  return scored.map((x) => x.m);
}

export function createSearcher(style = STYLES.neutral) {
  let nodes = 0, deadline = 0, aborted = false;
  const killers = [];

  function quiesce(chess, alpha, beta, ply) {
    nodes++;
    const sign = chess.turn === 0 ? 1 : -1;
    const stand = sign * evaluate(chess, style);
    if (stand >= beta) return beta;
    if (stand > alpha) alpha = stand;
    if (ply > 24) return alpha;
    const caps = chess.generateMoves({ capturesOnly: true });
    const ordered = orderMoves(chess, caps, 0, killers, ply);
    for (const m of ordered) {
      chess.makeMove(m);
      const score = -quiesce(chess, -beta, -alpha, ply + 1);
      chess.undoMove();
      if (score >= beta) return beta;
      if (score > alpha) alpha = score;
    }
    return alpha;
  }

  function negamax(chess, depth, alpha, beta, ply) {
    if ((nodes & 1023) === 0 && Date.now() > deadline) { aborted = true; return 0; }
    nodes++;
    const inCheck = chess.inCheck();
    if (inCheck) depth++; // extension por jaque
    if (depth <= 0) return quiesce(chess, alpha, beta, ply);

    const moves = chess.generateMoves();
    if (moves.length === 0) return inCheck ? -MATE + ply : 0;
    if (chess.halfmove >= 100) return 0;

    const ordered = orderMoves(chess, moves, 0, killers, ply);
    let best = -Infinity;
    for (let i = 0; i < ordered.length; i++) {
      const m = ordered[i];
      chess.makeMove(m);
      let score;
      if (i === 0) score = -negamax(chess, depth - 1, -beta, -alpha, ply + 1);
      else {
        score = -negamax(chess, depth - 1, -alpha - 1, -alpha, ply + 1);
        if (score > alpha && score < beta) score = -negamax(chess, depth - 1, -beta, -alpha, ply + 1);
      }
      chess.undoMove();
      if (aborted) return 0;
      if (score > best) best = score;
      if (score > alpha) alpha = score;
      if (alpha >= beta) {
        if (!(mFlags(m) & F_CAPTURE)) {
          killers[ply] = killers[ply] || [0, 0];
          if (killers[ply][0] !== m) { killers[ply][1] = killers[ply][0]; killers[ply][0] = m; }
        }
        break;
      }
    }
    return best;
  }

  // Devuelve todas las jugadas de la raiz puntuadas, de mejor a peor.
  function analyze(chess, { maxDepth = 5, timeMs = 1500 } = {}) {
    nodes = 0; aborted = false; deadline = Date.now() + timeMs;
    killers.length = 0;
    const work = new Chess(chess.fen());
    const rootMoves = work.generateMoves();
    if (!rootMoves.length) return { lines: [], depth: 0, nodes: 0, over: true };
    let results = rootMoves.map((m) => ({ move: m, uci: moveToUci(m), score: -Infinity }));
    let completed = 0;

    for (let depth = 1; depth <= maxDepth; depth++) {
      const partial = [];
      let alpha = -Infinity;
      for (const r of results) {
        work.makeMove(r.move);
        const score = -negamax(work, depth - 1, -Infinity, Infinity, 1);
        work.undoMove();
        if (aborted) break;
        partial.push({ move: r.move, uci: r.uci, score });
        if (score > alpha) alpha = score;
      }
      if (aborted) break;
      partial.sort((a, b) => b.score - a.score);
      results = partial;
      completed = depth;
      if (Math.abs(results[0].score) > MATE - 100) break;
      if (Date.now() > deadline) break;
    }
    return { lines: results, depth: completed, nodes, aborted };
  }

  return { analyze, get nodes() { return nodes; } };
}

// Elige una jugada con algo de variedad humana: entre las que estan
// dentro de `slack` centipeones de la mejor, prefiere la mejor con sesgo.
export function pickMove(lines, slack = 25, sharpness = 0.75) {
  if (!lines.length) return null;
  const best = lines[0].score;
  const pool = lines.filter((l) => best - l.score <= slack);
  if (pool.length === 1 || Math.random() < sharpness) return pool[0];
  return pool[Math.floor(Math.random() * pool.length)];
}
