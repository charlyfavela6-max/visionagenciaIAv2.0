#!/usr/bin/env python3
"""Ornamento del cartel carta, sin gastar creditos.

Se acabaron los de WaveSpeed a media tanda el 2 sep 2026, pero el grabado ya
estaba hecho en `librito_fondos/`. Aqui se despieza y se recompone en carta.

DOS COSAS QUE SE APRENDIERON EN EL PRIMER INTENTO
-------------------------------------------------
1. La corona a lo ancho de la hoja queda de 45 mm de alto y se come el titulo.
   Va al 40 % del ancho, no al 90 %.
2. Las guirnaldas laterales del librito estan hechas para una columna de 50 mm.
   Estiradas a 279 mm de alto se deforman y ensucian todo. En carta NO van: el
   filete doble solo ya sostiene la hoja.
"""
import os
from PIL import Image, ImageChops, ImageDraw

AQUI = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(AQUI, "librito_fondos")
DPI = 300
MM = DPI / 25.4
W, H = int(215.9 * MM), int(279.4 * MM)
VERDE = (11, 58, 39)   # subido de tono a peticion de Angel


def pon(lienzo, trozo, x_mm, y_mm, ancho_mm):
    an = int(ancho_mm * MM)
    al = int(an * trozo.height / trozo.width)
    x, y = int(x_mm * MM), int(y_mm * MM)
    t = trozo.resize((an, al), Image.LANCZOS).convert("RGB")
    region = lienzo.crop((x, y, x + an, y + al))
    lienzo.paste(ImageChops.darker(region, t), (x, y))
    return y_mm + al / MM


if __name__ == "__main__":
    ext = Image.open(os.path.join(F, "exterior.png")).convert("RGB")
    e = ext.width
    lienzo = Image.new("RGB", (W, H), "white")

    # Misma curva de tinta que el librito 5x5: hunde lo oscuro y deja el blanco
    # en blanco. Multiplicar plano pinta el fondo de gris.
    tinta = lambda im: im.point(lambda v: max(0, 255 - int((255 - v) * 1.5)))
    corona = tinta(ext.crop((int(e * 0.53), int(e * 0.055), int(e * 0.97), int(e * 0.205))))
    abajo = pon(lienzo, corona, (215.9 - 86) / 2, 15, 86)

    rama = tinta(ext.crop((int(e * 0.03), int(e * 0.80), int(e * 0.47), int(e * 0.96))))
    pon(lienzo, rama, (215.9 - 70) / 2, 252, 70)

    d = ImageDraw.Draw(lienzo)
    for mm, grueso in ((8.0, 4), (9.6, 2)):
        m = int(mm * MM)
        d.rectangle([m, m, W - m, H - m], outline=VERDE, width=grueso)

    lienzo.save(os.path.join(F, "cartel.png"))
    print("corona termina en %.0f mm · listo %s" % (abajo, lienzo.size))
