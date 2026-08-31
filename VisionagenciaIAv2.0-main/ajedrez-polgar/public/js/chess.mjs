// Motor de ajedrez 0x88: generacion de jugadas, SAN, FEN.
// Sin dependencias. Se usa igual en Node (scripts de build) y en el navegador.

export const EMPTY = 0;
export const PAWN = 1, KNIGHT = 2, BISHOP = 3, ROOK = 4, QUEEN = 5, KING = 6;
export const WHITE = 0, BLACK = 1;
const BLACK_BIT = 8;

export const pieceType = (p) => p & 7;
export const pieceColor = (p) => (p & BLACK_BIT) ? BLACK : WHITE;
const mk = (type, color) => type | (color === BLACK ? BLACK_BIT : 0);

const PIECE_CHARS = { 1: 'p', 2: 'n', 3: 'b', 4: 'r', 5: 'q', 6: 'k' };
const CHAR_PIECES = { p: PAWN, n: KNIGHT, b: BISHOP, r: ROOK, q: QUEEN, k: KING };

// Deltas 0x88
const KNIGHT_D = [33, 31, 18, 14, -33, -31, -18, -14];
const BISHOP_D = [17, 15, -17, -15];
const ROOK_D = [16, 1, -16, -1];
const KING_D = [17, 16, 15, 1, -17, -16, -15, -1];

// Banderas de jugada
export const F_NORMAL = 0, F_CAPTURE = 1, F_BIGPAWN = 2, F_EP = 4,
  F_PROMO = 8, F_KSIDE = 16, F_QSIDE = 32;

// Enroque
const C_WK = 1, C_WQ = 2, C_BK = 4, C_BQ = 8;

export const sqFile = (sq) => sq & 15;
export const sqRank = (sq) => sq >> 4;
export const isOnBoard = (sq) => (sq & 0x88) === 0;
export const algebraic = (sq) => 'abcdefgh'[sqFile(sq)] + (sqRank(sq) + 1);
export const fromAlgebraic = (s) => ('abcdefgh'.indexOf(s[0])) + ((s.charCodeAt(1) - 49) * 16);

// Jugada empaquetada en un entero: from | to<<8 | promo<<16 | flags<<20
export const encodeMove = (from, to, promo, flags) => from | (to << 8) | (promo << 16) | (flags << 20);
export const mFrom = (m) => m & 0xff;
export const mTo = (m) => (m >> 8) & 0xff;
export const mPromo = (m) => (m >> 16) & 0xf;
export const mFlags = (m) => (m >> 20) & 0xff;
export const moveToUci = (m) => algebraic(mFrom(m)) + algebraic(mTo(m)) + (mPromo(m) ? PIECE_CHARS[mPromo(m)] : '');

export const START_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';

export class Chess {
  constructor(fen = START_FEN) {
    this.board = new Int8Array(128);
    this.kings = [-1, -1];
    this.history = [];
    this.load(fen);
  }

  clone() {
    const c = new Chess(this.fen());
    return c;
  }

  load(fen) {
    this.board.fill(0);
    const [placement, turn, castling, ep, half, full] = fen.trim().split(/\s+/);
    let sq = 112; // a8
    for (const ch of placement) {
      if (ch === '/') { sq -= 24; continue; }
      if (ch >= '1' && ch <= '8') { sq += +ch; continue; }
      const type = CHAR_PIECES[ch.toLowerCase()];
      const color = ch === ch.toLowerCase() ? BLACK : WHITE;
      this.board[sq] = mk(type, color);
      if (type === KING) this.kings[color] = sq;
      sq++;
    }
    this.turn = turn === 'w' ? WHITE : BLACK;
    this.castling = 0;
    if (castling.includes('K')) this.castling |= C_WK;
    if (castling.includes('Q')) this.castling |= C_WQ;
    if (castling.includes('k')) this.castling |= C_BK;
    if (castling.includes('q')) this.castling |= C_BQ;
    this.ep = (ep && ep !== '-') ? fromAlgebraic(ep) : -1;
    this.halfmove = half ? +half : 0;
    this.fullmove = full ? +full : 1;
    this.history.length = 0;
  }

  fen() {
    let out = '';
    for (let r = 7; r >= 0; r--) {
      let empty = 0;
      for (let f = 0; f < 8; f++) {
        const p = this.board[r * 16 + f];
        if (!p) { empty++; continue; }
        if (empty) { out += empty; empty = 0; }
        const ch = PIECE_CHARS[pieceType(p)];
        out += pieceColor(p) === WHITE ? ch.toUpperCase() : ch;
      }
      if (empty) out += empty;
      if (r) out += '/';
    }
    let c = '';
    if (this.castling & C_WK) c += 'K';
    if (this.castling & C_WQ) c += 'Q';
    if (this.castling & C_BK) c += 'k';
    if (this.castling & C_BQ) c += 'q';
    return `${out} ${this.turn === WHITE ? 'w' : 'b'} ${c || '-'} ${this.ep >= 0 ? algebraic(this.ep) : '-'} ${this.halfmove} ${this.fullmove}`;
  }

  // Clave de posicion sin contadores: sirve para indexar el libro de partidas.
  key() {
    const f = this.fen().split(' ');
    return `${f[0]} ${f[1]} ${f[2]} ${f[3]}`;
  }

  get(sqStr) { return this.board[fromAlgebraic(sqStr)]; }

  attacked(sq, byColor) {
    // peones
    const pd = byColor === WHITE ? -16 : 16; // desde donde vendria el peon
    for (const side of [-1, 1]) {
      const from = sq + pd + side;
      if (isOnBoard(from)) {
        const p = this.board[from];
        if (p && pieceColor(p) === byColor && pieceType(p) === PAWN) return true;
      }
    }
    for (const d of KNIGHT_D) {
      const from = sq + d;
      if (isOnBoard(from)) {
        const p = this.board[from];
        if (p && pieceColor(p) === byColor && pieceType(p) === KNIGHT) return true;
      }
    }
    for (const d of KING_D) {
      const from = sq + d;
      if (isOnBoard(from)) {
        const p = this.board[from];
        if (p && pieceColor(p) === byColor && pieceType(p) === KING) return true;
      }
    }
    for (const d of BISHOP_D) {
      let from = sq + d;
      while (isOnBoard(from)) {
        const p = this.board[from];
        if (p) {
          if (pieceColor(p) === byColor) {
            const t = pieceType(p);
            if (t === BISHOP || t === QUEEN) return true;
          }
          break;
        }
        from += d;
      }
    }
    for (const d of ROOK_D) {
      let from = sq + d;
      while (isOnBoard(from)) {
        const p = this.board[from];
        if (p) {
          if (pieceColor(p) === byColor) {
            const t = pieceType(p);
            if (t === ROOK || t === QUEEN) return true;
          }
          break;
        }
        from += d;
      }
    }
    return false;
  }

  inCheck(color = this.turn) {
    return this.attacked(this.kings[color], color ^ 1);
  }

  generateMoves({ legal = true, capturesOnly = false } = {}) {
    const us = this.turn, them = us ^ 1;
    const moves = [];
    const pushPawn = (from, to, flags) => {
      const rank = sqRank(to);
      if (rank === 0 || rank === 7) {
        for (const promo of [QUEEN, ROOK, BISHOP, KNIGHT]) moves.push(encodeMove(from, to, promo, flags | F_PROMO));
      } else moves.push(encodeMove(from, to, 0, flags));
    };

    for (let sq = 0; sq < 128; sq++) {
      if (sq & 0x88) { sq += 7; continue; }
      const p = this.board[sq];
      if (!p || pieceColor(p) !== us) continue;
      const type = pieceType(p);

      if (type === PAWN) {
        const dir = us === WHITE ? 16 : -16;
        const one = sq + dir;
        if (!capturesOnly && isOnBoard(one) && !this.board[one]) {
          pushPawn(sq, one, F_NORMAL);
          const startRank = us === WHITE ? 1 : 6;
          const two = sq + dir * 2;
          if (sqRank(sq) === startRank && !this.board[two]) moves.push(encodeMove(sq, two, 0, F_BIGPAWN));
        }
        for (const side of [-1, 1]) {
          const to = one + side;
          if (!isOnBoard(to)) continue;
          const target = this.board[to];
          if (target && pieceColor(target) === them) pushPawn(sq, to, F_CAPTURE);
          else if (!target && to === this.ep) moves.push(encodeMove(sq, to, 0, F_EP | F_CAPTURE));
        }
        continue;
      }

      const deltas = type === KNIGHT ? KNIGHT_D : type === KING ? KING_D
        : type === BISHOP ? BISHOP_D : type === ROOK ? ROOK_D : KING_D;
      const sliding = type === BISHOP || type === ROOK || type === QUEEN;
      for (const d of deltas) {
        let to = sq + d;
        while (isOnBoard(to)) {
          const target = this.board[to];
          if (!target) {
            if (!capturesOnly) moves.push(encodeMove(sq, to, 0, F_NORMAL));
          } else {
            if (pieceColor(target) === them) moves.push(encodeMove(sq, to, 0, F_CAPTURE));
            break;
          }
          if (!sliding) break;
          to += d;
        }
      }

      if (type === KING && !capturesOnly) {
        const kSide = us === WHITE ? C_WK : C_BK;
        const qSide = us === WHITE ? C_WQ : C_BQ;
        if ((this.castling & kSide) && !this.board[sq + 1] && !this.board[sq + 2]
          && !this.attacked(sq, them) && !this.attacked(sq + 1, them) && !this.attacked(sq + 2, them)) {
          moves.push(encodeMove(sq, sq + 2, 0, F_KSIDE));
        }
        if ((this.castling & qSide) && !this.board[sq - 1] && !this.board[sq - 2] && !this.board[sq - 3]
          && !this.attacked(sq, them) && !this.attacked(sq - 1, them) && !this.attacked(sq - 2, them)) {
          moves.push(encodeMove(sq, sq - 2, 0, F_QSIDE));
        }
      }
    }

    if (!legal) return moves;
    const out = [];
    for (const m of moves) {
      this.makeMove(m);
      if (!this.attacked(this.kings[us], them)) out.push(m);
      this.undoMove();
    }
    return out;
  }

  makeMove(m) {
    const from = mFrom(m), to = mTo(m), flags = mFlags(m), promo = mPromo(m);
    const us = this.turn, them = us ^ 1;
    const piece = this.board[from];
    let captured = this.board[to];

    this.history.push({
      move: m, captured, castling: this.castling, ep: this.ep,
      halfmove: this.halfmove, kingW: this.kings[0], kingB: this.kings[1],
    });

    this.board[to] = piece;
    this.board[from] = 0;

    if (flags & F_EP) {
      const capSq = us === WHITE ? to - 16 : to + 16;
      captured = this.board[capSq];
      this.history[this.history.length - 1].captured = captured;
      this.history[this.history.length - 1].epCapSq = capSq;
      this.board[capSq] = 0;
    }
    if (flags & F_PROMO) this.board[to] = mk(promo, us);
    if (pieceType(piece) === KING) {
      this.kings[us] = to;
      if (flags & F_KSIDE) { this.board[to - 1] = this.board[to + 1]; this.board[to + 1] = 0; }
      if (flags & F_QSIDE) { this.board[to + 1] = this.board[to - 2]; this.board[to - 2] = 0; }
      this.castling &= us === WHITE ? ~(C_WK | C_WQ) : ~(C_BK | C_BQ);
    }
    // Torres movidas o capturadas
    if (from === 0 || to === 0) this.castling &= ~C_WQ;
    if (from === 7 || to === 7) this.castling &= ~C_WK;
    if (from === 112 || to === 112) this.castling &= ~C_BQ;
    if (from === 119 || to === 119) this.castling &= ~C_BK;

    this.ep = (flags & F_BIGPAWN) ? (us === WHITE ? to - 16 : to + 16) : -1;
    if (pieceType(piece) === PAWN || captured) this.halfmove = 0; else this.halfmove++;
    if (us === BLACK) this.fullmove++;
    this.turn = them;
  }

  undoMove() {
    const h = this.history.pop();
    if (!h) return;
    const m = h.move;
    const from = mFrom(m), to = mTo(m), flags = mFlags(m);
    const us = this.turn ^ 1;
    this.turn = us;
    if (us === BLACK) this.fullmove--;
    this.castling = h.castling; this.ep = h.ep; this.halfmove = h.halfmove;
    this.kings[0] = h.kingW; this.kings[1] = h.kingB;

    let piece = this.board[to];
    if (flags & F_PROMO) piece = mk(PAWN, us);
    this.board[from] = piece;
    this.board[to] = 0;

    if (flags & F_EP) {
      this.board[h.epCapSq] = h.captured;
    } else if (h.captured) {
      this.board[to] = h.captured;
    }
    if (flags & F_KSIDE) { this.board[to + 1] = this.board[to - 1]; this.board[to - 1] = 0; }
    if (flags & F_QSIDE) { this.board[to - 2] = this.board[to + 1]; this.board[to + 1] = 0; }
  }

  // ---- SAN ----
  moveToSan(m, movesCache = null) {
    const flags = mFlags(m), from = mFrom(m), to = mTo(m);
    if (flags & F_KSIDE) return this.withCheckSuffix(m, 'O-O');
    if (flags & F_QSIDE) return this.withCheckSuffix(m, 'O-O-O');
    const piece = this.board[from];
    const type = pieceType(piece);
    let san = '';
    if (type === PAWN) {
      if (flags & F_CAPTURE) san += 'abcdefgh'[sqFile(from)] + 'x';
      san += algebraic(to);
      if (flags & F_PROMO) san += '=' + PIECE_CHARS[mPromo(m)].toUpperCase();
    } else {
      san += PIECE_CHARS[type].toUpperCase();
      const moves = movesCache || this.generateMoves();
      let sameFile = false, sameRank = false, ambiguous = false;
      for (const other of moves) {
        if (other === m) continue;
        if (mTo(other) !== to) continue;
        const op = this.board[mFrom(other)];
        if (pieceType(op) !== type) continue;
        ambiguous = true;
        if (sqFile(mFrom(other)) === sqFile(from)) sameFile = true;
        if (sqRank(mFrom(other)) === sqRank(from)) sameRank = true;
      }
      if (ambiguous) {
        if (!sameFile) san += 'abcdefgh'[sqFile(from)];
        else if (!sameRank) san += (sqRank(from) + 1);
        else san += algebraic(from);
      }
      if (flags & F_CAPTURE) san += 'x';
      san += algebraic(to);
    }
    return this.withCheckSuffix(m, san);
  }

  withCheckSuffix(m, san) {
    this.makeMove(m);
    let suffix = '';
    if (this.inCheck()) suffix = this.generateMoves().length === 0 ? '#' : '+';
    this.undoMove();
    return san + suffix;
  }

  sanToMove(san) {
    const clean = san.replace(/[+#?!]+$/, '').replace(/=([QRBN])/, '=$1');
    const moves = this.generateMoves();
    for (const m of moves) {
      if (this.moveToSan(m, moves).replace(/[+#?!]+$/, '') === clean) return m;
    }
    // tolerancia: notacion larga o sin 'x'
    for (const m of moves) {
      if (moveToUci(m) === clean.toLowerCase()) return m;
    }
    return null;
  }

  moveSan(san) {
    const m = this.sanToMove(san);
    if (m === null) return null;
    this.makeMove(m);
    return m;
  }

  isCheckmate() { return this.inCheck() && this.generateMoves().length === 0; }
  isStalemate() { return !this.inCheck() && this.generateMoves().length === 0; }

  insufficientMaterial() {
    const counts = {};
    let total = 0;
    const bishops = [];
    for (let sq = 0; sq < 128; sq++) {
      if (sq & 0x88) { sq += 7; continue; }
      const p = this.board[sq];
      if (!p) continue;
      total++;
      const t = pieceType(p);
      counts[t] = (counts[t] || 0) + 1;
      if (t === BISHOP) bishops.push((sqRank(sq) + sqFile(sq)) % 2);
    }
    if (total === 2) return true;
    if (total === 3 && (counts[KNIGHT] === 1 || counts[BISHOP] === 1)) return true;
    if (total === 2 + bishops.length && bishops.length && bishops.every((c) => c === bishops[0])) return true;
    return false;
  }

  gameOver() {
    if (this.isCheckmate()) return { over: true, result: this.turn === WHITE ? '0-1' : '1-0', reason: 'jaque mate' };
    if (this.isStalemate()) return { over: true, result: '1/2-1/2', reason: 'rey ahogado' };
    if (this.halfmove >= 100) return { over: true, result: '1/2-1/2', reason: 'regla de 50 jugadas' };
    if (this.insufficientMaterial()) return { over: true, result: '1/2-1/2', reason: 'material insuficiente' };
    return { over: false };
  }

  // Tablero plano para la UI: 64 casillas desde a8 hasta h1
  boardArray() {
    const out = [];
    for (let r = 7; r >= 0; r--) {
      for (let f = 0; f < 8; f++) {
        const p = this.board[r * 16 + f];
        out.push(p ? { type: PIECE_CHARS[pieceType(p)], color: pieceColor(p) === WHITE ? 'w' : 'b', square: algebraic(r * 16 + f) } : null);
      }
    }
    return out;
  }
}

export function perft(chess, depth) {
  if (depth === 0) return 1;
  const moves = chess.generateMoves();
  if (depth === 1) return moves.length;
  let nodes = 0;
  for (const m of moves) {
    chess.makeMove(m);
    nodes += perft(chess, depth - 1);
    chess.undoMove();
  }
  return nodes;
}
