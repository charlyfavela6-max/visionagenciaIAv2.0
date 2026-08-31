// Traduce una jugada a lenguaje de plan: que hace, no solo donde va.
// Todo se calcula del tablero (no hay frases inventadas por partida).
import {
  Chess, PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING, WHITE, BLACK,
  pieceType, pieceColor, sqFile, sqRank, isOnBoard, algebraic,
  mFrom, mTo, mFlags, mPromo, F_CAPTURE, F_KSIDE, F_QSIDE, F_PROMO, F_EP,
} from './chess.mjs';
import { VALUES } from './eval.mjs';

const NOMBRES = { [PAWN]: 'peon', [KNIGHT]: 'caballo', [BISHOP]: 'alfil', [ROOK]: 'torre', [QUEEN]: 'dama', [KING]: 'rey' };
const KING_D = [17, 16, 15, 1, -17, -16, -15, -1];
const KNIGHT_D = [33, 31, 18, 14, -33, -31, -18, -14];
const CENTRO = new Set(['d4', 'e4', 'd5', 'e5']);
const CENTRO_AMPLIO = new Set(['c4', 'd4', 'e4', 'f4', 'c5', 'd5', 'e5', 'f5']);

function zonaRey(chess, color) {
  const k = chess.kings[color];
  const z = new Set([k]);
  for (const d of KING_D) if (isOnBoard(k + d)) z.add(k + d);
  return z;
}

function ataquesAZona(chess, color, zona) {
  // cuantas piezas de `color` atacan casillas de la zona
  let n = 0;
  for (const sq of zona) if (chess.attacked(sq, color)) n++;
  return n;
}

function movilidad(chess, color) {
  const saved = chess.turn;
  chess.turn = color;
  const n = chess.generateMoves({ legal: false }).length;
  chess.turn = saved;
  return n;
}

function colgadas(chess, color) {
  // piezas de `color` atacadas por el rival y no defendidas
  const out = [];
  for (let sq = 0; sq < 128; sq++) {
    if (sq & 0x88) { sq += 7; continue; }
    const p = chess.board[sq];
    if (!p || pieceColor(p) !== color) continue;
    if (pieceType(p) === KING) continue;
    if (chess.attacked(sq, color ^ 1) && !chess.attacked(sq, color)) out.push({ sq, valor: VALUES[pieceType(p)] });
  }
  return out;
}

function movilidadPieza(chess, sq) {
  const p = chess.board[sq];
  if (!p) return 0;
  const t = pieceType(p), color = pieceColor(p);
  if (t === PAWN) return 0;
  const deltas = t === KNIGHT ? KNIGHT_D : t === BISHOP ? [17, 15, -17, -15]
    : t === ROOK ? [16, 1, -16, -1] : KING_D;
  const sliding = t === BISHOP || t === ROOK || t === QUEEN;
  let n = 0;
  for (const d of deltas) {
    let to = sq + d;
    while (isOnBoard(to)) {
      const target = chess.board[to];
      if (!target || pieceColor(target) !== color) n++;
      if (target) break;
      if (!sliding) break;
      to += d;
    }
  }
  return n;
}

// ¿una pieza situada en `desde` ataca la casilla `hasta` en el tablero actual?
function atacaDesde(chess, desde, hasta) {
  const p = chess.board[desde];
  if (!p) return false;
  const t = pieceType(p), color = pieceColor(p);
  if (t === PAWN) {
    const dir = color === WHITE ? 16 : -16;
    return hasta === desde + dir - 1 || hasta === desde + dir + 1;
  }
  const deltas = t === KNIGHT ? KNIGHT_D : t === BISHOP ? [17, 15, -17, -15]
    : t === ROOK ? [16, 1, -16, -1] : KING_D;
  const sliding = t === BISHOP || t === ROOK || t === QUEEN;
  for (const d of deltas) {
    let sq = desde + d;
    while (isOnBoard(sq)) {
      if (sq === hasta) return true;
      if (chess.board[sq]) break;
      if (!sliding) break;
      sq += d;
    }
  }
  return false;
}

function esPuestoAvanzado(chess, sq, color) {
  const f = sqFile(sq), r = sqRank(sq);
  const avanzada = color === WHITE ? r >= 3 : r <= 4;
  if (!avanzada) return false;
  for (let ff = f - 1; ff <= f + 1; ff += 2) {
    if (ff < 0 || ff > 7) continue;
    for (let rr = 0; rr < 8; rr++) {
      const p = chess.board[rr * 16 + ff];
      if (!p || pieceType(p) !== PAWN || pieceColor(p) === color) continue;
      if (color === WHITE ? rr > r : rr < r) return false; // un peon rival puede echarlo
    }
  }
  const dir = color === WHITE ? -16 : 16;
  for (const lado of [-1, 1]) {
    const s = sq + dir + lado;
    if (!isOnBoard(s)) continue;
    const p = chess.board[s];
    if (p && pieceType(p) === PAWN && pieceColor(p) === color) return true; // apoyado por peon
  }
  return false;
}

export function explicarJugada(fen, move) {
  const chess = new Chess(fen);
  const yo = chess.turn, rival = yo ^ 1;
  const from = mFrom(move), to = mTo(move), flags = mFlags(move);
  const pieza = chess.board[from];
  const tipo = pieceType(pieza);
  const capturada = chess.board[to];

  const zonaRival = zonaRey(chess, rival);
  const zonaPropia = zonaRey(chess, yo);
  const antesAtaque = ataquesAZona(chess, yo, zonaRival);
  const antesDefensa = ataquesAZona(chess, rival, zonaPropia);
  const antesMovRival = movilidad(chess, rival);
  const antesColgadasRival = colgadas(chess, rival).length;
  const antesColgadasMias = colgadas(chess, yo).map((c) => c.sq);
  const antesMovPieza = movilidadPieza(chess, from);

  const san = chess.moveToSan(move);
  chess.makeMove(move);

  const despuesAtaque = ataquesAZona(chess, yo, zonaRey(chess, rival));
  const despuesMovRival = movilidad(chess, rival);
  const colgadasRival = colgadas(chess, rival);
  const colgadasMias = colgadas(chess, yo);
  const daJaque = chess.inCheck();
  const esMate = daJaque && chess.generateMoves().length === 0;
  const piezaQuedaAtacada = chess.attacked(to, rival);
  const piezaDefendida = chess.attacked(to, yo);
  const despuesDefensa = ataquesAZona(chess, rival, zonaRey(chess, yo));
  const despuesMovPieza = movilidadPieza(chess, to);
  const salvadas = antesColgadasMias.filter((sq) => {
    const p = chess.board[sq];
    return p && !(chess.attacked(sq, rival) && !chess.attacked(sq, yo));
  }).length;
  const puesto = (tipo === KNIGHT || tipo === BISHOP) && esPuestoAvanzado(chess, to, yo);
  // que piezas rivales pasa a atacar la pieza movida
  const nuevosObjetivos = [];
  for (let sq = 0; sq < 128; sq++) {
    if (sq & 0x88) { sq += 7; continue; }
    const p2 = chess.board[sq];
    if (!p2 || pieceColor(p2) !== rival) continue;
    const v = VALUES[pieceType(p2)];
    if (v < 300 && pieceType(p2) !== KING) continue;
    if (!atacaDesde(chess, to, sq)) continue;
    if (atacaDesde(chess, from, sq)) continue; // ya lo atacaba antes de moverse
    nuevosObjetivos.push(pieceType(p2));
  }
  chess.undoMove();

  const tags = [];
  const frases = [];

  if (esMate) { tags.push('mate'); frases.push('Jaque mate: se acaba la partida.'); }
  else if (daJaque) { tags.push('jaque'); frases.push('Da jaque y obliga al rival a responder: le quitas opciones.'); }

  if (flags & (F_KSIDE | F_QSIDE)) {
    tags.push('enroque');
    frases.push('Enroque: pones el rey a salvo y conectas las torres antes de abrir el juego.');
  }

  if (flags & F_PROMO) { tags.push('promocion'); frases.push(`Corona: el peon se convierte en ${NOMBRES[mPromo(move)]}.`); }

  if (flags & F_CAPTURE) {
    const valorCapturado = (flags & F_EP) ? VALUES[PAWN] : VALUES[pieceType(capturada)];
    const valorPropio = VALUES[tipo];
    if (piezaQuedaAtacada && !piezaDefendida && valorPropio > valorCapturado + 50) {
      tags.push('sacrificio');
      frases.push(`Sacrificio: entregas ${NOMBRES[tipo]} por ${valorCapturado ? 'menos material' : 'nada material'} a cambio de ataque. Es la marca de la casa de Polgar.`);
    } else if (valorCapturado >= valorPropio || !piezaQuedaAtacada) {
      tags.push('gana-material');
      frases.push(`Captura favorable: te llevas ${valorCapturado / 100} de material.`);
    } else {
      tags.push('captura');
      frases.push('Captura para cambiar piezas y aliviar la posicion.');
    }
  } else if (piezaQuedaAtacada && !piezaDefendida && VALUES[tipo] >= 300) {
    tags.push('sacrificio');
    frases.push(`Dejas ${NOMBRES[tipo]} en una casilla atacada: es una entrega intencional para abrir lineas.`);
  }

  const deltaAtaque = despuesAtaque - antesAtaque;
  if (deltaAtaque >= 2) {
    tags.push('ataque-al-rey');
    frases.push(`Suma ${deltaAtaque} casillas atacadas alrededor del rey rival: la pieza entra en la zona caliente.`);
  } else if (deltaAtaque === 1) {
    tags.push('presion');
    frases.push('Acerca una pieza mas al rey rival; el ataque se va acumulando.');
  }

  if (tipo === PAWN && !(flags & F_CAPTURE)) {
    const fileTo = sqFile(to);
    const reyRival = chess.kings[rival];
    const reyEnCasa = reyRival === (rival === WHITE ? 4 : 116);
    const avanzado = yo === WHITE ? sqRank(to) >= 3 : sqRank(to) <= 4;
    if (!reyEnCasa && avanzado && Math.abs(fileTo - sqFile(reyRival)) <= 2) {
      tags.push('avalancha-de-peones');
      frases.push('Empuje de peon hacia el rey rival: abre columnas para tus torres y dama.');
    }
  }

  if (CENTRO.has(algebraic(to)) || (tipo === PAWN && CENTRO_AMPLIO.has(algebraic(to)))) {
    tags.push('centro');
    frases.push('Ocupa o disputa el centro: desde ahi tus piezas alcanzan los dos flancos.');
  }

  const filaInicial = yo === WHITE ? 0 : 7;
  if ((tipo === KNIGHT || tipo === BISHOP) && sqRank(from) === filaInicial) {
    tags.push('desarrollo');
    frases.push(`Desarrollo: saca ${NOMBRES[tipo]} de la fila de atras. Primero todas las piezas fuera, despues el ataque.`);
  }

  if (tipo === ROOK) {
    let peonPropio = false;
    for (let r = 0; r < 8; r++) {
      const p = chess.board[r * 16 + sqFile(to)];
      if (p && pieceType(p) === PAWN && pieceColor(p) === yo) peonPropio = true;
    }
    if (!peonPropio) {
      tags.push('columna-abierta');
      frases.push('Torre a una columna sin peones propios: es la via de entrada al campo rival.');
    }
  }

  const nuevasColgadas = colgadasRival.length - antesColgadasRival;
  if (nuevasColgadas > 0) {
    const mayor = Math.max(...colgadasRival.map((c) => c.valor));
    if (mayor >= 300) {
      tags.push('amenaza');
      frases.push('Crea una amenaza concreta: deja una pieza rival atacada y sin defensa.');
    }
  }

  const deltaMovRival = antesMovRival - despuesMovRival;
  if (deltaMovRival >= 6) {
    tags.push('profilaxis');
    frases.push(`Profilaxis: le quita ${deltaMovRival} jugadas posibles al rival. Antes de atacar, se le corta el aire.`);
  }

  if (colgadasMias.some((c) => c.valor >= 300) && !tags.includes('sacrificio')) {
    tags.push('riesgo');
    frases.push('Ojo: deja alguna pieza propia sin defensa. Revisa las capturas del rival.');
  }

  if (puesto) {
    tags.push('puesto-avanzado');
    frases.push(`Casilla fuerte: ningun peon rival puede echar a ese ${NOMBRES[tipo]}, y un peon propio lo sostiene.`);
  }

  if (salvadas > 0 && !(flags & F_CAPTURE)) {
    tags.push('defiende');
    frases.push('Defiende: pone a cubierto material propio que estaba colgado.');
  }

  if (tipo === KING && !(flags & (F_KSIDE | F_QSIDE)) && antesDefensa - despuesDefensa >= 1) {
    tags.push('rey-a-salvo');
    frases.push('Mueve el rey a una casilla mas tranquila: menos piezas rivales le apuntan.');
  }

  const deltaPieza = despuesMovPieza - antesMovPieza;
  if (deltaPieza >= 4) {
    tags.push('activacion');
    frases.push(`Activa la pieza: ${NOMBRES[tipo]} pasa de ${antesMovPieza} a ${despuesMovPieza} casillas de accion.`);
  } else if (deltaPieza <= -3 && !(flags & F_CAPTURE)) {
    tags.push('reagrupacion');
    frases.push(`Reagrupa: retira ${NOMBRES[tipo]} para volver a entrar por mejor camino. Polgar retrocede piezas para reorganizar el ataque, no para defender.`);
  }

  if (nuevosObjetivos.length && !tags.includes('amenaza')) {
    const mayor = Math.max(...nuevosObjetivos);
    tags.push('gana-tiempo');
    frases.push(`Ataca ${NOMBRES[mayor] === 'rey' ? 'al rey' : 'la ' + NOMBRES[mayor]} rival: el rival gasta su jugada en responder y tu ganas un tiempo.`);
  }

  if (tipo === PAWN && !(flags & F_CAPTURE) && !tags.includes('avalancha-de-peones')) {
    const f = sqFile(to);
    const flanco = f <= 2 ? 'dama' : f >= 5 ? 'rey' : 'centro';
    const avanzado = yo === WHITE ? sqRank(to) >= 3 : sqRank(to) <= 4;
    const reyRivalFlanco = sqFile(chess.kings[rival]) <= 2 ? 'dama' : sqFile(chess.kings[rival]) >= 5 ? 'rey' : 'centro';
    let apuntala = false;
    const dir = yo === WHITE ? 16 : -16;
    for (const lado of [-1, 1]) {
      const s2 = to + dir + lado;
      if (!isOnBoard(s2)) continue;
      const p2 = chess.board[s2];
      if (p2 && pieceType(p2) === PAWN && pieceColor(p2) === yo && CENTRO_AMPLIO.has(algebraic(s2))) apuntala = true;
    }
    if (apuntala) {
      tags.push('apuntala');
      frases.push('Sostiene el centro con otro peon: el centro firme es lo que permite atacar despues por los flancos.');
    } else if (flanco !== 'centro' && avanzado) {
      if (flanco === reyRivalFlanco) {
        tags.push('avalancha-de-peones');
        frases.push(`Avance de peones en el flanco de ${flanco}, justo donde esta el rey rival: asi se abren las lineas del ataque.`);
      } else {
        tags.push('espacio');
        frases.push(`Gana espacio en el flanco de ${flanco} y empuja las piezas rivales hacia atras.`);
      }
    } else if (!tags.includes('centro')) {
      tags.push('espacio');
      frases.push('Avance de peon: gana espacio y le quita casillas a las piezas rivales.');
    }
  }

  if (!frases.length) {
    const mitadRival = yo === WHITE ? sqRank(to) >= 4 : sqRank(to) <= 3;
    tags.push('maniobra');
    frases.push(mitadRival
      ? `Jugada de avance: mete ${NOMBRES[tipo]} en el campo rival y gana terreno.`
      : `Jugada de preparacion: coloca ${NOMBRES[tipo]} para el plan que viene, sin comprometer nada.`);
  }

  return { san, tags, frases };
}
