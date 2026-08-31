import { Chess } from './chess.mjs';
import { createSearcher } from './search.mjs';
import { STYLES } from './eval.mjs';

const buscadores = {
  polgar: createSearcher(STYLES.polgar),
  kasparov: createSearcher(STYLES.kasparov),
  neutral: createSearcher(STYLES.neutral),
};

self.onmessage = ({ data }) => {
  const { id, fen, estilo = 'neutral', profundidad = 5, tiempo = 1200 } = data;
  try {
    const chess = new Chess(fen);
    const r = buscadores[estilo].analyze(chess, { maxDepth: profundidad, timeMs: tiempo });
    self.postMessage({
      id,
      lineas: r.lines.slice(0, 6).map((l) => ({ uci: l.uci, score: l.score })),
      profundidad: r.depth, nodos: r.nodes,
    });
  } catch (e) {
    self.postMessage({ id, error: String(e && e.message || e) });
  }
};
