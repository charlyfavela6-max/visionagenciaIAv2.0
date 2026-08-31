// Servidor sin dependencias: estaticos + API del libro de partidas reales.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PUBLIC = path.join(__dirname, 'public');
const PORT = process.env.PORT || 3000;

const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8', '.svg': 'image/svg+xml',
  '.png': 'image/png', '.ico': 'image/x-icon', '.webmanifest': 'application/manifest+json',
};
const COMPRESIBLE = new Set(['.html', '.js', '.mjs', '.css', '.json', '.svg', '.webmanifest']);

const libros = {};
for (const slug of ['polgar', 'kasparov']) {
  const file = path.join(__dirname, 'books', `${slug}-book.json`);
  if (!fs.existsSync(file)) { console.warn(`[libro] falta ${file}`); continue; }
  const raw = JSON.parse(fs.readFileSync(file, 'utf8'));
  libros[slug] = raw;
  console.log(`[libro] ${raw.meta.player}: ${raw.meta.games} partidas, ${raw.meta.positions} posiciones`);
}

function ficha(libro, gi) {
  const g = libro.games[gi];
  if (!g) return null;
  return {
    blancas: g.w, negras: g.b, evento: g.e, sede: g.s, anio: g.d,
    resultado: g.r, eco: g.eco, colorJugador: g.c, indice: gi,
  };
}

function responderConsejo(libro, key, maxEntradas = 4) {
  const entradas = libro.book[key];
  if (!entradas) return { encontrado: false, jugadas: [] };
  const jugadas = entradas.slice(0, maxEntradas).map(([uci, n, w, d, l, gi, ply]) => {
    const g = libro.games[gi];
    const moves = g ? g.mv.split(' ') : [];
    return {
      uci, partidas: n, ganadas: w, tablas: d, perdidas: l,
      partida: ficha(libro, gi), ply,
      continuacion: moves.slice(ply, ply + 8),
      linea: moves.slice(0, ply),
    };
  });
  return { encontrado: true, jugadas };
}

function leerCuerpo(req) {
  return new Promise((resolve, reject) => {
    let data = '';
    req.on('data', (c) => { data += c; if (data.length > 1e6) req.destroy(); });
    req.on('end', () => { try { resolve(JSON.parse(data || '{}')); } catch (e) { reject(e); } });
    req.on('error', reject);
  });
}

function enviarJson(res, obj, status = 200) {
  const body = Buffer.from(JSON.stringify(obj));
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8', 'Content-Length': body.length });
  res.end(body);
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);

  if (url.pathname === '/api/salud') {
    return enviarJson(res, {
      ok: true,
      libros: Object.fromEntries(Object.entries(libros).map(([k, v]) => [k, v.meta])),
    });
  }

  if (url.pathname === '/api/consejo' && req.method === 'POST') {
    try {
      const { clave, jugador = 'polgar' } = await leerCuerpo(req);
      const libro = libros[jugador];
      if (!libro) return enviarJson(res, { error: 'jugador desconocido' }, 400);
      if (!clave) return enviarJson(res, { error: 'falta la clave de posicion' }, 400);
      return enviarJson(res, { jugador, meta: libro.meta, ...responderConsejo(libro, clave) });
    } catch (e) {
      return enviarJson(res, { error: String(e) }, 400);
    }
  }

  if (url.pathname === '/api/partida') {
    const jugador = url.searchParams.get('jugador') || 'polgar';
    const gi = Number(url.searchParams.get('i'));
    const libro = libros[jugador];
    if (!libro || !libro.games[gi]) return enviarJson(res, { error: 'no existe' }, 404);
    const g = libro.games[gi];
    return enviarJson(res, { ...ficha(libro, gi), jugadas: g.mv.split(' ') });
  }

  // estaticos
  let rel = decodeURIComponent(url.pathname);
  if (rel === '/') rel = '/index.html';
  const file = path.join(PUBLIC, path.normalize(rel).replace(/^(\.\.[/\\])+/, ''));
  if (!file.startsWith(PUBLIC)) { res.writeHead(403); return res.end('403'); }
  fs.readFile(file, (err, data) => {
    if (err) { res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' }); return res.end('No encontrado'); }
    const ext = path.extname(file);
    const headers = { 'Content-Type': MIME[ext] || 'application/octet-stream' };
    const acepta = (req.headers['accept-encoding'] || '').includes('gzip');
    if (acepta && COMPRESIBLE.has(ext)) {
      const gz = zlib.gzipSync(data);
      res.writeHead(200, { ...headers, 'Content-Encoding': 'gzip', 'Content-Length': gz.length });
      return res.end(gz);
    }
    res.writeHead(200, { ...headers, 'Content-Length': data.length });
    res.end(data);
  });
});

server.listen(PORT, () => console.log(`Ajedrez Polgar escuchando en http://localhost:${PORT}`));
