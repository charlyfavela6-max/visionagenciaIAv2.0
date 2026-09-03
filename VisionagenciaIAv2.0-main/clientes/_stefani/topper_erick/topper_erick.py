#!/usr/bin/env python3
"""Cake topper shaker de Erick — SVG por capas, listo para Cricut.

    python3 topper_erick.py

QUE PIDIO STEFANI (WhatsApp, 2 sep 2026 22:53)
----------------------------------------------
  «Cake topper shaker 3D · del abecedario con los colores primarios ·
   que diga Erick y 4 años · y que separe los elementos para imprimir y
   cortar con Cricut»

y mando dos fotos: unas letras acolchadas con pespunte blanco, y un topper
redondo con ventana de lentejuelas, letras ABC y numeros sueltos.

POR QUE EL TEXTO VA EN TRAZOS Y NO EN <text>
---------------------------------------------
Cricut Design Space NO corta texto vivo si no tiene la fuente instalada: lo
sustituye por otra y el ancho cambia. Aqui cada letra sale como PATH sacado del
contorno real de Poppins Black con fontTools, asi que corta exactamente lo que
se ve, en cualquier maquina.

COMO SE ARMA EL SHAKER (por eso las capas van en este orden)
-----------------------------------------------------------
    1. base            cartulina azul — la silueta completa, es el respaldo
    2. ventana_atras   la MISMA silueta en acetato: el vidrio de atras
    3. marco           cartulina blanca con el hueco: hace la pared del shaker
       (se corta DOS VECES y se pegan una sobre otra para dar hondura;
        ahi adentro van las lentejuelas)
    4. ventana_frente  acetato otra vez: el vidrio de enfrente
    5. sombra_letras   cartulina blanca, el contorno engordado de las letras
    6. letras_*        una capa por color, se pegan encima de su sombra
    7. estrellas_*     los adornos
    8. palito          la varilla

Cada capa es un <g id="..."> con su color. En Design Space entra como un solo
SVG y se separa por capas al ungroup.
"""
import os
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))   # .../VisionagenciaIAv2.0-main
FUENTE = os.path.join(RAIZ, "fonts", "Poppins-Black.ttf")

# Colores primarios, que es lo que pidio. El morado y el naranja entran solo
# como apoyo porque «Erick» tiene cinco letras y con tres colores se repiten.
ROJO, AMARILLO, AZUL = "#E4322B", "#F2B705", "#1668C6"
VERDE, MORADO, NARANJA = "#5FAF2E", "#7B3FA0", "#F2760C"
BLANCO, ACETATO = "#FFFFFF", "#BFE6F2"

ANCHO, ALTO = 150.0, 200.0          # mm, sin contar el palito


class Letras:
    """Saca los contornos reales de la fuente. Cricut no entiende <text>."""

    def __init__(self, ruta):
        self.f = TTFont(ruta)
        self.gs = self.f.getGlyphSet()
        self.upm = self.f["head"].unitsPerEm
        self.cmap = self.f.getBestCmap()
        self.hmtx = self.f["hmtx"]

    def nombre(self, ch):
        return self.cmap[ord(ch)]

    def avance(self, ch, tam):
        return self.hmtx[self.nombre(ch)][0] * tam / self.upm

    def path(self, ch, x, y, tam):
        """Devuelve el `d` de la letra con su base en (x, y). El eje Y de las
        fuentes va al reves que el del SVG, por eso la escala negativa."""
        pen = SVGPathPen(self.gs)
        e = tam / self.upm
        self.gs[self.nombre(ch)].draw(TransformPen(pen, Transform(e, 0, 0, -e, x, y)))
        return pen.getCommands()

    def palabra(self, txt, x, y, tam, track=0.0):
        trozos, ancho = [], 0.0
        for ch in txt:
            trozos.append((ch, ancho))
            ancho += self.avance(ch, tam) + track
        ancho -= track
        return [(ch, self.path(ch, x - ancho / 2 + dx, y, tam)) for ch, dx in trozos], ancho


def estrella(cx, cy, r, puntas=5, hueco=0.46, giro=-90):
    import math
    p = []
    for i in range(puntas * 2):
        ang = math.radians(giro + i * 180 / puntas)
        rr = r if i % 2 == 0 else r * hueco
        p.append(f"{cx + rr*math.cos(ang):.2f},{cy + rr*math.sin(ang):.2f}")
    return "M" + "L".join(p) + "Z"


def nube(cx, cy, rx, ry):
    """La silueta del topper: una nube redonda, como la foto que mando."""
    import math
    p = []
    n = 11
    for i in range(n * 2 + 1):
        ang = 2 * math.pi * i / (n * 2)
        rr = 1.0 if i % 2 == 0 else 0.87
        p.append((cx + rx * rr * math.cos(ang), cy - ry * rr * math.sin(ang)))
    d = f"M{p[0][0]:.2f},{p[0][1]:.2f}"
    for i in range(1, len(p) - 1, 2):
        d += f" Q{p[i][0]:.2f},{p[i][1]:.2f} {p[i+1][0]:.2f},{p[i+1][1]:.2f}"
    return d + " Z"


def nubecita(cx, cy, an, al):
    """La plaquita blanca de atras de «Erick». En la foto de Stefani las letras
    van sobre una nube blanca — asi no hace falta el Offset de Design Space
    para que se despeguen del fondo."""
    import math
    x0, x1 = cx - an / 2, cx + an / 2
    r = al / 2
    return (f"M{x0:.1f},{cy-r:.1f} H{x1:.1f} "
            f"A{r:.1f},{r:.1f} 0 0 1 {x1:.1f},{cy+r:.1f} "
            f"H{x0:.1f} A{r:.1f},{r:.1f} 0 0 1 {x0:.1f},{cy-r:.1f} Z")


if __name__ == "__main__":
    L = Letras(FUENTE)
    cx = ANCHO / 2
    cy, RX, RY = 62.0, 70.0, 56.0        # la ventana del shaker

    silueta = nube(cx, cy, RX, RY)
    hueco = nube(cx, cy, RX - 13, RY - 13)

    capas = []

    capas.append(("base", "cartulina AZUL · la silueta completa, va hasta atras",
                  AZUL, [silueta]))
    capas.append(("ventana_atras", "ACETATO · el vidrio de atras",
                  ACETATO, [nube(cx, cy, RX - 6, RY - 6)]))
    capas.append(("marco", "cartulina BLANCA · CORTAR 2 VECES y pegar una sobre "
                           "otra: eso hace la hondura donde caen las lentejuelas",
                  BLANCO, [silueta + " " + hueco]))
    capas.append(("ventana_frente", "ACETATO · el vidrio de enfrente",
                  ACETATO, [nube(cx, cy, RX - 6, RY - 6)]))

    # --- ERICK, sobre su nubecita blanca ---
    tam, base_y = 27.0, 72.0
    letras, an = L.palabra("Erick", cx, base_y, tam, track=1.0)
    capas.append(("nube_erick", "cartulina BLANCA · la plaquita de atras de las letras",
                  BLANCO, [nubecita(cx, base_y - tam * 0.34, an + 9, tam * 1.22)]))
    for (ch, d), col in zip(letras, [ROJO, AMARILLO, VERDE, AZUL, NARANJA]):
        capas.append((f"letra_{ch}", f"cartulina de color · la «{ch}»", col, [d]))

    # --- el 4, sobre una estrella, montado en la orilla de abajo ---
    capas.append(("estrella_4", "cartulina AMARILLA · la estrella del numero",
                  AMARILLO, [estrella(cx, 122.0, 27.0, puntas=8, hueco=.66)]))
    cuatro, _ = L.palabra("4", cx, 134.0, 34.0)
    capas.append(("numero_4", "cartulina AZUL · el 4", AZUL, [d for _, d in cuatro]))

    # --- la cinta de «años» ---
    anios, anan = L.palabra("años", cx, 158.0, 16.0)
    bw, bh, by = anan + 26, 23.0, 158.0
    banderin = (f"M{cx-bw/2:.1f},{by-bh+4:.1f} H{cx+bw/2:.1f} "
                f"L{cx+bw/2-8:.1f},{by-bh/2+4:.1f} L{cx+bw/2:.1f},{by+4:.1f} "
                f"H{cx-bw/2:.1f} L{cx-bw/2+8:.1f},{by-bh/2+4:.1f} Z")
    capas.append(("banderin", "cartulina BLANCA · la cinta", BLANCO, [banderin]))
    capas.append(("texto_anios", "cartulina ROJA · la palabra «años»", ROJO,
                  [d for _, d in anios]))

    # --- el abecedario suelto, como en su foto de referencia ---
    # van PEGADAS ENCIMA del marco blanco, asi que se acomodan sobre el anillo
    abc = [("A", 30, 42, 12, ROJO), ("B", 120, 44, 12, AZUL),
           ("C", 28, 100, 11, VERDE), ("1", 122, 98, 11, AMARILLO),
           ("2", 48, 26, 10, MORADO), ("3", 103, 24, 10, VERDE)]
    for ch, x, y, t, col in abc:
        d = L.path(ch, x - L.avance(ch, t) / 2, y, t)
        capas.append((f"suelto_{ch}", f"cartulina de color · la «{ch}» suelta, "
                                      f"va pegada encima del marco", col, [d]))

    ad = [(66, 22, 7, AMARILLO), (86, 21, 7, AZUL),
          (22, 70, 6.5, AMARILLO), (128, 68, 6.5, ROJO),
          (58, 106, 6, VERDE), (94, 107, 6, MORADO)]
    for i, (x, y, r, col) in enumerate(ad, 1):
        capas.append((f"estrellita_{i}", f"cartulina de color · estrellita {i}", col,
                      [estrella(x, y, r)]))

    capas.append(("palito", "palito de madera o cartulina blanca", BLANCO,
                  [f"M{cx-3:.1f},{ALTO-30:.1f} h6 v52 h-6 Z"]))

    partes = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{ANCHO}mm" '
              f'height="{ALTO+26}mm" viewBox="0 0 {ANCHO} {ALTO+26}">',
              "<!-- Cake topper shaker de Erick · 4 anos.",
              "     Cada <g> es una CAPA: en Cricut Design Space se sube este SVG,",
              "     se hace Ungroup y cada capa queda como un corte aparte.",
              "     Medidas reales en milimetros: el topper mide 15 x 20 cm. -->"]
    for id_, nota, color, ds in capas:
        partes.append(f'  <g id="{id_}" data-material="{nota}">')
        for d in ds:
            regla = ' fill-rule="evenodd"' if id_ == "marco" else ''
            partes.append(f'    <path d="{d}" fill="{color}"{regla} stroke="none"/>')
        partes.append("  </g>")
    partes.append("</svg>")

    ruta = os.path.join(AQUI, "topper_erick_capas.svg")
    open(ruta, "w", encoding="utf8").write("\n".join(partes))
    print("listo:", ruta, "·", len(capas), "capas")
    for id_, nota, _, _ in capas:
        print(f"   {id_:16} {nota}")
