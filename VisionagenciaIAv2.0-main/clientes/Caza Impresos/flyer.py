#!/usr/bin/env python3
"""Flyer de CAZA IMPRESOS — media carta, 2 por hoja.

    python3 flyer.py

Media carta (139.7 x 215.9 mm) para que salgan DOS por hoja y cueste la mitad
imprimirlo. Es un flyer de imprenta: tiene que verse impreso bien, o no vende.

El texto va con tipografia de verdad, no con IA: son diez servicios y un
telefono, y ahi la IA deforma letras. El logo si es de IA y se pega encima.
"""
import os
from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = "/workspaces/visionagenciaIAv2.0/VisionagenciaIAv2.0-main"
FUENTES = os.path.join(RAIZ, "fonts")
DPI = 300
MM = DPI / 25.4
W, H = int(139.7 * MM), int(215.9 * MM)
CARTA_W, CARTA_H = int(215.9 * MM), int(279.4 * MM)

AZUL = (18, 58, 99)
NARANJA = (228, 85, 43)
CREMA = (247, 245, 240)
GRIS = (108, 118, 130)

SERVICIOS = [
    ("SELLOS", "de goma y automáticos"),
    ("TARJETAS", "de presentación"),
    ("VOLANTES", "para repartir"),
    ("LONAS", "de cualquier medida"),
    ("LETREROS", "preventivos y de seguridad"),
    ("ETIQUETAS", "de rollo y sueltas"),
    ("NOTAS DE VENTA", "y recibos foliados"),
    ("PAPELERÍA", "hojas, sobres, folders"),
]


def f(nombre, pt):
    return ImageFont.truetype(os.path.join(FUENTES, nombre), max(7, int(pt * MM / 2.845)))


def centro(d, y, texto, fu, color, esp=0, ancho=None, x0=0):
    an = ancho or W
    t = esp * " ".join(texto) if esp else texto
    d.text((x0 + (an - d.textlength(t, font=fu)) / 2, y), t, font=fu, fill=color)
    return y + fu.size


def haz():
    im = Image.new("RGB", (W, H), CREMA)
    d = ImageDraw.Draw(im)
    m = int(9 * MM)

    # banda azul de arriba, con el logo
    d.rectangle([0, 0, W, int(52 * MM)], fill=AZUL)
    logo = os.path.join(AQUI, "logo_caza_v1.png")
    if os.path.exists(logo):
        lg = Image.open(logo).convert("RGB")
        # el logo viene sobre blanco: se recorta la marca y se invierte a claro
        lg = lg.crop((int(lg.width * .13), int(lg.height * .10),
                      int(lg.width * .87), int(lg.height * .90)))
        alto = int(34 * MM)
        lg = lg.resize((int(lg.width * alto / lg.height), alto), Image.LANCZOS)
        # blanco -> azul de fondo, para que se funda
        px = lg.load()
        for yy in range(lg.height):
            for xx in range(lg.width):
                r, g, b = px[xx, yy]
                if r > 205 and g > 205 and b > 205:
                    px[xx, yy] = AZUL
                elif r < 90 and g < 110 and b < 150:
                    px[xx, yy] = CREMA           # el azul del logo, a claro
        im.paste(lg, ((W - lg.width) // 2, int(9 * MM)))

    y = int(58 * MM)
    y = centro(d, y, "TODO LO QUE TU NEGOCIO", f("Montserrat-Black.ttf", 15), AZUL)
    y = centro(d, y + int(1 * MM), "NECESITA IMPRESO", f("Montserrat-Black.ttf", 15), AZUL)

    y += int(4 * MM)
    d.line([(W // 2 - int(16 * MM), y), (W // 2 + int(16 * MM), y)],
           fill=NARANJA, width=int(1.0 * MM))

    # la lista de servicios, en dos columnas
    y += int(7 * MM)
    fu_t = f("Montserrat-Black.ttf", 10)
    fu_s = f("Montserrat-Medium.ttf", 7.5)
    col_an = (W - 2 * m) / 2
    for i, (tit, sub) in enumerate(SERVICIOS):
        cx = m + (i % 2) * col_an
        yy = y + (i // 2) * int(16 * MM)
        d.ellipse([cx, yy + int(1.6 * MM), cx + int(2.4 * MM), yy + int(4.0 * MM)],
                  fill=NARANJA)
        d.text((cx + int(4.5 * MM), yy), tit, font=fu_t, fill=AZUL)
        d.text((cx + int(4.5 * MM), yy + int(5.4 * MM)), sub, font=fu_s, fill=GRIS)
    y += int(16 * MM) * ((len(SERVICIOS) + 1) // 2) + int(2 * MM)

    # el diferenciador
    caja = y
    d.rectangle([m, caja, W - m, caja + int(28 * MM)], fill=AZUL)
    yy = caja + int(4.5 * MM)
    yy = centro(d, yy, "EL DISEÑO VA INCLUIDO", f("Montserrat-Black.ttf", 12), CREMA)
    yy += int(3 * MM)
    for l in ("No hace falta que traigas tu archivo.",
              "Nos dices qué necesitas, te lo diseñamos,",
              "te lo enseñamos y lo imprimimos."):
        yy = centro(d, yy, l, f("Montserrat-Medium.ttf", 8), CREMA) + int(0.8 * MM)

    # cierre
    y = caja + int(34 * MM)
    y = centro(d, y, "COTIZA HOY POR WHATSAPP", f("Montserrat-Medium.ttf", 9), GRIS)
    y += int(2 * MM)
    y = centro(d, y, "631 247 0486", f("Montserrat-Black.ttf", 21), NARANJA)
    y += int(3 * MM)
    centro(d, y, "Te decimos precio el mismo día", f("Montserrat-Medium.ttf", 8), GRIS)

    # franja naranja al pie
    d.rectangle([0, H - int(6 * MM), W, H], fill=NARANJA)

    im.save(os.path.join(AQUI, "CazaImpresos_flyer.png"), dpi=(DPI, DPI))

    # dos por hoja carta
    pl = Image.new("RGB", (CARTA_W, CARTA_H), "white")
    mx = (CARTA_W - 2 * W) // 2
    my = (CARTA_H - H) // 2
    pl.paste(im, (mx, my)); pl.paste(im, (mx + W, my))
    dd = ImageDraw.Draw(pl)
    for i in range(3):
        x = mx + i * W
        dd.line([(x, my - int(4 * MM)), (x, my - int(1 * MM))], fill="black", width=2)
        dd.line([(x, my + H + int(1 * MM)), (x, my + H + int(4 * MM))], fill="black", width=2)
    pl.save(os.path.join(AQUI, "CazaImpresos_CARTA_2up.pdf"), resolution=DPI,
            title="Caza Impresos · flyer")
    pl.save(os.path.join(AQUI, "CazaImpresos_CARTA_2up.png"), dpi=(DPI, DPI))
    print("listo · media carta, 2 por hoja")


if __name__ == "__main__":
    haz()
