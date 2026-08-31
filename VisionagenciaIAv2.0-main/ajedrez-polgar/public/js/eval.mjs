// Evaluacion con "perfiles de estilo".
// El perfil no inventa jugadas de nadie: solo pondera que rasgos pesan mas
// (ataque al rey, actividad, centro...) cuando salimos del libro de partidas reales.
import {
  PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING, WHITE, BLACK,
  pieceType, pieceColor, sqFile, sqRank, isOnBoard,
} from './chess.mjs';

export const VALUES = [0, 100, 320, 330, 500, 950, 0];

const flip = (t) => { const o = new Int16Array(64); for (let i = 0; i < 64; i++) o[i] = t[63 - (i - (i % 8)) + (i % 8) - (i % 8) + (i % 8)]; return o; };

// PST desde la perspectiva de las blancas, indice 0 = a1
const PST = {
  [PAWN]: [
    0, 0, 0, 0, 0, 0, 0, 0,
    5, 10, 10, -20, -20, 10, 10, 5,
    5, -5, -10, 0, 0, -10, -5, 5,
    0, 0, 0, 20, 20, 0, 0, 0,
    5, 5, 10, 25, 25, 10, 5, 5,
    10, 10, 20, 30, 30, 20, 10, 10,
    50, 50, 50, 50, 50, 50, 50, 50,
    0, 0, 0, 0, 0, 0, 0, 0],
  [KNIGHT]: [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20, 0, 5, 5, 0, -20, -40,
    -30, 5, 10, 15, 15, 10, 5, -30,
    -30, 0, 15, 20, 20, 15, 0, -30,
    -30, 5, 15, 20, 20, 15, 5, -30,
    -30, 0, 10, 15, 15, 10, 0, -30,
    -40, -20, 0, 0, 0, 0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50],
  [BISHOP]: [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10, 5, 0, 0, 0, 0, 5, -10,
    -10, 10, 10, 10, 10, 10, 10, -10,
    -10, 0, 10, 10, 10, 10, 0, -10,
    -10, 5, 5, 10, 10, 5, 5, -10,
    -10, 0, 5, 10, 10, 5, 0, -10,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -20, -10, -10, -10, -10, -10, -10, -20],
  [ROOK]: [
    0, 0, 5, 10, 10, 5, 0, 0,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    5, 10, 10, 10, 10, 10, 10, 5,
    0, 0, 0, 0, 0, 0, 0, 0],
  [QUEEN]: [
    -20, -10, -10, -5, -5, -10, -10, -20,
    -10, 0, 5, 0, 0, 0, 0, -10,
    -10, 5, 5, 5, 5, 5, 0, -10,
    0, 0, 5, 5, 5, 5, 0, -5,
    -5, 0, 5, 5, 5, 5, 0, -5,
    -10, 0, 5, 5, 5, 5, 0, -10,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -20, -10, -10, -5, -5, -10, -10, -20],
  [KING]: [
    20, 30, 10, 0, 0, 10, 30, 20,
    20, 20, 0, 0, 0, 0, 20, 20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30],
};
const KING_END = [
  -50, -30, -30, -30, -30, -30, -30, -50,
  -30, -30, 0, 0, 0, 0, -30, -30,
  -30, -10, 20, 30, 30, 20, -10, -30,
  -30, -10, 30, 40, 40, 30, -10, -30,
  -30, -10, 30, 40, 40, 30, -10, -30,
  -30, -10, 20, 30, 30, 20, -10, -30,
  -30, -20, -10, 0, 0, -10, -20, -30,
  -50, -40, -30, -20, -20, -30, -40, -50];

const idx64 = (sq, color) => {
  const r = sqRank(sq), f = sqFile(sq);
  return color === WHITE ? r * 8 + f : (7 - r) * 8 + f;
};

export const STYLES = {
  polgar: {
    nombre: 'Judit Polgar',
    material: 0.97, pst: 1.0, movilidad: 1.15, ataqueRey: 1.45, seguridadPropia: 0.8,
    centro: 1.0, peonPasado: 1.0, parDeAlfiles: 1.1, iniciativa: 14, torreAbierta: 1.2,
    lema: 'iniciativa y ataque directo al rey; el material es negociable',
  },
  kasparov: {
    nombre: 'Garry Kasparov',
    material: 1.0, pst: 1.05, movilidad: 1.35, ataqueRey: 1.2, seguridadPropia: 1.1,
    centro: 1.3, peonPasado: 1.15, parDeAlfiles: 1.05, iniciativa: 10, torreAbierta: 1.0,
    lema: 'espacio, piezas activas y presion permanente',
  },
  neutral: {
    nombre: 'Motor neutral',
    material: 1, pst: 1, movilidad: 1, ataqueRey: 1, seguridadPropia: 1,
    centro: 1, peonPasado: 1, parDeAlfiles: 1, iniciativa: 8, torreAbierta: 1,
    lema: 'evaluacion equilibrada',
  },
};

const KNIGHT_D = [33, 31, 18, 14, -33, -31, -18, -14];
const BISHOP_D = [17, 15, -17, -15];
const ROOK_D = [16, 1, -16, -1];
const KING_D = [17, 16, 15, 1, -17, -16, -15, -1];
const CENTER = [51, 52, 67, 68]; // d4 e4 d5 e5 en 0x88

const ATTACK_UNITS = { [KNIGHT]: 20, [BISHOP]: 20, [ROOK]: 40, [QUEEN]: 80, [PAWN]: 8, [KING]: 0 };
// Un solo atacante no es un ataque: la tabla solo se dispara con dos o mas piezas.
const SAFETY_TABLE = (peso, atacantes) => atacantes >= 2
  ? Math.min(300, (peso * peso) / 70)
  : Math.min(50, (peso * peso) / 220);

// Devuelve la evaluacion en centipeones desde el punto de vista de las BLANCAS.
const ZONE = [new Uint8Array(128), new Uint8Array(128)];
const IS_CENTER = new Uint8Array(128);
for (const sq of CENTER) IS_CENTER[sq] = 1;

// Devuelve la evaluacion en centipeones desde el punto de vista de las BLANCAS.
export function evaluate(chess, style = STYLES.neutral) {
  const b = chess.board;
  const mat = [0, 0], pstScore = [0, 0], mob = [0, 0], attackUnits = [0, 0], atacantes = [0, 0];
  const bishops = [0, 0];
  const pawnsFile = [new Int8Array(8), new Int8Array(8)];
  const pawnSq = [[], []];
  let phase = 0;

  ZONE[0].fill(0); ZONE[1].fill(0);
  for (const color of [WHITE, BLACK]) {
    const k = chess.kings[color];
    ZONE[color][k] = 1;
    for (const d of KING_D) if (isOnBoard(k + d)) ZONE[color][k + d] = 1;
  }

  // 1a pasada: peones (los necesitamos completos antes de juzgar columnas abiertas)
  for (let sq = 0; sq < 128; sq++) {
    if (sq & 0x88) { sq += 7; continue; }
    const p = b[sq];
    if (!p || pieceType(p) !== PAWN) continue;
    const c = pieceColor(p);
    pawnsFile[c][sqFile(sq)]++;
    pawnSq[c].push(sq);
  }

  for (let sq = 0; sq < 128; sq++) {
    if (sq & 0x88) { sq += 7; continue; }
    const p = b[sq];
    if (!p) continue;
    const c = pieceColor(p), t = pieceType(p);
    const them = c ^ 1;
    const zoneThem = ZONE[them];
    mat[c] += VALUES[t];
    if (t !== KING && t !== PAWN) phase += t === QUEEN ? 4 : t === ROOK ? 2 : 1;
    pstScore[c] += PST[t][idx64(sq, c)];
    if (t === BISHOP) bishops[c]++;

    if (t === PAWN) {
      const dir = c === WHITE ? 16 : -16;
      for (const side of [-1, 1]) {
        const to = sq + dir + side;
        if (isOnBoard(to) && zoneThem[to]) attackUnits[c] += ATTACK_UNITS[PAWN];
      }
      continue;
    }
    let casillasEnZona = 0;
    if (t === KING) continue;

    const deltas = t === KNIGHT ? KNIGHT_D : t === BISHOP ? BISHOP_D : t === ROOK ? ROOK_D : KING_D;
    const sliding = t === BISHOP || t === ROOK || t === QUEEN;
    for (const d of deltas) {
      let to = sq + d;
      while (isOnBoard(to)) {
        const target = b[to];
        if (!target || pieceColor(target) !== c) {
          mob[c]++;
          if (zoneThem[to]) casillasEnZona++;
          if (IS_CENTER[to]) mob[c] += 0.6;
        }
        if (target) break;
        if (!sliding) break;
        to += d;
      }
    }
    if (casillasEnZona > 0) {
      atacantes[c]++;
      attackUnits[c] += ATTACK_UNITS[t] + 6 * (casillasEnZona - 1);
    }
    if (t === ROOK && !pawnsFile[c][sqFile(sq)]) pstScore[c] += 12 * style.torreAbierta;
  }

  // Rey en el final: se activa
  const phaseFactor = Math.min(1, phase / 24); // 1 = apertura/medio juego
  for (const color of [WHITE, BLACK]) {
    const k = chess.kings[color];
    const i = idx64(k, color);
    pstScore[color] += (1 - phaseFactor) * (KING_END[i] - PST[KING][i]);
  }

  // Estructura de peones: doblados, aislados, pasados
  const pawnScore = [0, 0];
  for (const color of [WHITE, BLACK]) {
    const files = pawnsFile[color], enemy = pawnsFile[color ^ 1];
    for (let f = 0; f < 8; f++) {
      if (files[f] > 1) pawnScore[color] -= 14 * (files[f] - 1);
      if (files[f] && !(f > 0 && files[f - 1]) && !(f < 7 && files[f + 1])) pawnScore[color] -= 16;
    }
    for (const sq of pawnSq[color]) {
      const f = sqFile(sq), r = sqRank(sq);
      let passed = true;
      for (const sq2 of pawnSq[color ^ 1]) {
        const f2 = sqFile(sq2), r2 = sqRank(sq2);
        if (Math.abs(f2 - f) <= 1 && (color === WHITE ? r2 > r : r2 < r)) { passed = false; break; }
      }
      if (passed) {
        const adv = color === WHITE ? r : 7 - r;
        pawnScore[color] += (10 + adv * adv * 4) * style.peonPasado;
      }
    }
    // escudo del rey
    const k = chess.kings[color];
    const dir = color === WHITE ? 16 : -16;
    let shield = 0;
    for (const df of [-1, 0, 1]) {
      const s1 = k + dir + df, s2 = k + dir * 2 + df;
      if (isOnBoard(s1) && b[s1] && pieceType(b[s1]) === PAWN && pieceColor(b[s1]) === color) shield += 12;
      else if (isOnBoard(s2) && b[s2] && pieceType(b[s2]) === PAWN && pieceColor(b[s2]) === color) shield += 6;
      else shield -= 8;
    }
    pawnScore[color] += shield * phaseFactor;
  }

  let score = 0;
  for (const color of [WHITE, BLACK]) {
    const sign = color === WHITE ? 1 : -1;
    let s = 0;
    s += mat[color] * style.material;
    s += pstScore[color] * style.pst;
    s += mob[color] * 3 * style.movilidad;
    s += pawnScore[color];
    if (bishops[color] >= 2) s += 35 * style.parDeAlfiles;
    // ataque al rey rival (bonificado por el estilo) y riesgo propio (penalizado)
    s += SAFETY_TABLE(attackUnits[color], atacantes[color]) * style.ataqueRey * phaseFactor;
    s -= SAFETY_TABLE(attackUnits[color ^ 1], atacantes[color ^ 1]) * (style.seguridadPropia - 1) * phaseFactor;
    score += sign * s;
  }
  score += (chess.turn === WHITE ? 1 : -1) * style.iniciativa;
  return Math.round(score);
}
