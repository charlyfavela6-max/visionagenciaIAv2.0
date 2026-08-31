// Clave corta y estable de una posicion (FEN sin contadores) -> 2 hashes FNV-1a de 32 bits.
export function posKey(fenKey) {
  let h1 = 0x811c9dc5, h2 = 0x01000193;
  for (let i = 0; i < fenKey.length; i++) {
    const c = fenKey.charCodeAt(i);
    h1 ^= c; h1 = Math.imul(h1, 0x01000193) >>> 0;
    h2 = (h2 + c) >>> 0; h2 = Math.imul(h2, 0x85ebca6b) >>> 0; h2 ^= h2 >>> 13;
  }
  return (h1 >>> 0).toString(36) + '.' + (h2 >>> 0).toString(36);
}
