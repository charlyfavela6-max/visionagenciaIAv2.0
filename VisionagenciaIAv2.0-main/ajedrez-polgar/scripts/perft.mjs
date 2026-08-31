import { Chess, perft } from '../public/js/chess.mjs';
const cases = [
  ['rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', [20, 400, 8902, 197281, 4865609]],
  ['r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1', [48, 2039, 97862, 4085603]],
  ['8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1', [14, 191, 2812, 43238, 674624]],
  ['r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1', [6, 264, 9467, 422333]],
  ['rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8', [44, 1486, 62379, 2103487]],
];
let fail = 0;
for (const [fen, expected] of cases) {
  for (let d = 1; d <= expected.length; d++) {
    const c = new Chess(fen);
    const t = Date.now();
    const n = perft(c, d);
    const ok = n === expected[d - 1];
    if (!ok) fail++;
    console.log(`${ok ? 'ok  ' : 'FAIL'} d=${d} ${n} (esperado ${expected[d - 1]}) ${Date.now() - t}ms  ${fen.slice(0, 30)}`);
  }
}
console.log(fail ? `\n${fail} fallos` : '\nperft: todo correcto');
process.exit(fail ? 1 : 0);
