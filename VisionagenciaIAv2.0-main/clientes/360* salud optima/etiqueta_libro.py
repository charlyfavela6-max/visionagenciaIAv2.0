#!/usr/bin/env python3
"""El librito de Rar~Amore, a la medida que se le pida.

    python3 etiqueta_libro.py 93        # librito de 5 x 9.3 cm
    python3 etiqueta_libro.py 89        # el que si da 6 por hoja carta
    python3 etiqueta_libro.py 50 93 100 # varias de un jalon

Angel lleva tres cambios de medida en una noche (10x10 -> 5x5 -> 5x9.3), asi que
esto ya no se rehace a mano: se le pasa el ALTO en milimetros y sale todo — el
librito, la hoja carta impuesta y las dos caras en PNG.

COMO ACOMODA EL TEXTO
---------------------
No hay coordenadas fijas: cada panel es una LISTA DE BLOQUES y el sobrante
vertical se reparte entre ellos segun su peso. Por eso el mismo contenido cae
bien tanto en 50 mm como en 100. Los cuerpos crecen con (alto/50)**0.45 —
lineal se veria gigante en los altos.

CUANTOS CABEN EN CARTA
----------------------
Se calcula, no se supone. Con 5 mm de margen de impresora quedan 205.9 x 269.4
mm utiles, y ahi entran floor(205.9/ancho) x floor(269.4/alto) tejas. El corte
esta en 89.8 mm: a 89 salen SEIS, a 93 solo CUATRO.
"""
import os, sys
from PIL import Image, ImageChops, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
FUENTES = os.path.join(RAIZ, "fonts")
ARTE = os.path.join(AQUI, "librito_fondos", "exterior.png")

DPI = 600
MM = DPI / 25.4
ANCHO_PAN = 50                      # el ancho del librito no se mueve: 5 cm
CARTA_W, CARTA_H = int(215.9 * MM), int(279.4 * MM)
MARGEN_IMP = 5                      # lo que ninguna impresora casera alcanza

VERDE = (11, 58, 39)
VERDE_CLARO = (31, 92, 63)


def f(nombre, pt):
    return ImageFont.truetype(os.path.join(FUENTES, nombre), max(6, int(pt * MM / 2.845)))


def ancho_de(d, texto, fu, esp):
    return max(d.textlength(esp * " ".join(l) if esp else l, font=fu)
               for l in texto.split("\n") if l.strip())


def encaja(d, texto, nombre, pt, ancho, esp=0):
    while pt > 3:
        fu = f(nombre, pt)
        if ancho_de(d, texto, fu, esp) <= ancho:
            return fu
        pt -= 0.25
    return f(nombre, pt)


# bloque = (texto, fuente, pt, color, interlinea, espaciado, peso)
# el peso es cuanto sobrante se lleva el hueco que va ANTES del bloque
def bloques_portada():
    return [("RAR~AMORE", "CormorantGaramond-Bold.ttf", 15, VERDE, 1.2, 1, 3),
            ("__RAYA__", None, 0, VERDE, 0, 0, 1),
            ("C Á P S U L A S", "Montserrat-Medium.ttf", 6.5, VERDE_CLARO, 1.2, 0, .6),
            ("Comienza a cuidarte\na partir de los 30",
             "CormorantGaramond-Bold.ttf", 8.5, VERDE, 1.35, 0, 2.4)]


def bloques_contraportada():
    return [("PRECIO DE PROMOCIÓN", "Montserrat-Black.ttf", 6, VERDE_CLARO, 1.2, 0, 2),
            ("Bálsamo + Cápsulas", "CormorantGaramond-Bold.ttf", 8, VERDE, 1.3, 0, .7),
            ("$1,895", "Montserrat-Black.ttf", 15, VERDE, 1.1, 0, .8),
            ("Precio normal $2,359", "Montserrat-Medium.ttf", 6, VERDE_CLARO, 1.2, 0, .5),
            ("PEDIDOS WHATSAPP", "Montserrat-Medium.ttf", 5.8, VERDE_CLARO, 1.2, 0, 2.4),
            ("818 466 84 56", "Montserrat-Black.ttf", 8, VERDE, 1.2, 0, .35)]


def bloques_contenido():
    # La lista que mando Angel el 3 sep 15:32 con su correccion de las 15:42:
    # «Extracto en lugar de cáscara» y «(Resveratrol)». Vitamina D y toronja
    # salieron porque su lista nueva ya no las trae.
    ing = "\n".join(("Piel de camarón", "Boswelia serrata", "Calcio", "Vitamina D",
                     "Magnesio", "Extracto de naranja", "Extracto de limón",
                     "Extracto de semilla", "de uva (Resveratrol)"))
    return [("CÁPSULAS · CONTIENE", "Montserrat-Black.ttf", 6.2, VERDE_CLARO, 1.2, 0, 1.6),
            (ing, "Montserrat-Medium.ttf", 6.6, VERDE, 1.5, 0, .9),
            ("CONTENIDO:  30 CÁPSULAS", "Montserrat-Medium.ttf", 5.6, VERDE_CLARO, 1.2, 0, 1.4),
            ("CADUCIDAD:  DIC 2028", "Montserrat-Medium.ttf", 5.6, VERDE_CLARO, 1.2, 0, .25)]


def bloques_promesa():
    return [("Vive sin dolores.\nVive sin estrés.\nVive sin insomnio.",
             "CormorantGaramond-Bold.ttf", 8.5, VERDE, 1.45, 0, 2.2),
            ("__RAYA__", None, 0, VERDE, 0, 0, 1.2),
            ("BIENESTAR PARA TUS\nMÚSCULOS Y ARTICULACIONES",
             "Montserrat-Black.ttf", 6.2, VERDE, 1.5, 0, 1),
            ("818 466 84 56", "Montserrat-Black.ttf", 7.5, VERDE, 1.2, 0, 2)]


def dibuja_panel(d, x0, alto_mm, arriba_mm, bloques):
    """Acomoda los bloques entre `arriba_mm` y el pie del panel."""
    pan = int(ANCHO_PAN * MM)
    util_x = pan - int(9 * MM)
    esc = (alto_mm / 50.0) ** 0.45
    hueco_raya = int(0.9 * MM)

    # Se mide con un factor global y, si no cabe, se encoge TODO el panel a la
    # vez. Antes el sobrante se volvia negativo y los bloques se encimaban sin
    # avisar — asi salio el 5x5 con «CONTIENE» encima del primer ingrediente.
    hueco = (alto_mm - arriba_mm - 5) * MM
    factor = 1.0
    while True:
        medidos = []
        total = 0
        for texto, nom, pt, color, inter, esp, peso in bloques:
            if texto == "__RAYA__":
                medidos.append((texto, None, color, 0, 0, hueco_raya, peso)); total += hueco_raya
                continue
            fu = encaja(d, texto, nom, pt * esc * factor, util_x, esp)
            n = len([l for l in texto.split("\n") if l.strip()])
            al = fu.size * inter * n
            medidos.append((texto, fu, color, inter, esp, al, peso)); total += al
        if total <= hueco or factor <= 0.45:
            break
        factor -= 0.02

    libre = max(0, hueco - total)
    pesos = sum(b[6] for b in medidos) or 1
    y = arriba_mm * MM
    for texto, fu, color, inter, esp, al, peso in medidos:
        y += libre * peso / pesos
        if texto == "__RAYA__":
            d.line([(x0 + pan // 2 - int(8 * MM), y), (x0 + pan // 2 + int(8 * MM), y)],
                   fill=color, width=3)
            y += al
            continue
        for l in texto.split("\n"):
            t = esp * " ".join(l) if esp else l
            w = d.textlength(t, font=fu)
            d.text((x0 + (pan - w) / 2, y), t, font=fu, fill=color)
            y += fu.size * inter


def ornamento(alto_mm):
    """El copete y el filete. El copete crece con el panel pero nunca pasa del
    18 % del alto, o se traga el texto — eso paso en el primer 5x5."""
    arte = Image.open(ARTE).convert("RGB")
    e = arte.width
    copete = arte.crop((int(e * 0.53), int(e * 0.055), int(e * 0.97), int(e * 0.185)))
    copete = copete.point(lambda v: max(0, 255 - int((255 - v) * 1.5)))

    pan, W, H = int(ANCHO_PAN * MM), int(ANCHO_PAN * 2 * MM), int(alto_mm * MM)
    hoja = Image.new("RGB", (W, H), "white")
    an = int(min(ANCHO_PAN * 0.72, alto_mm * 0.60) * MM)
    al = int(an * copete.height / copete.width)
    if al > alto_mm * 0.18 * MM:
        al = int(alto_mm * 0.18 * MM); an = int(al * copete.width / copete.height)
    c = copete.resize((an, al), Image.LANCZOS)
    tope = int(3.4 * MM)
    for p in (0, 1):
        x = p * pan + (pan - an) // 2
        reg = hoja.crop((x, tope, x + an, tope + al))
        hoja.paste(ImageChops.darker(reg, c), (x, tope))

    d = ImageDraw.Draw(hoja)
    for p in (0, 1):
        x0 = p * pan
        for mm, gr in ((2.6, 3), (3.6, 1)):
            m = int(mm * MM)
            d.rectangle([x0 + m, m, x0 + pan - m, H - m], outline=VERDE, width=gr)
        cx, cy, r = x0 + pan // 2, int(6 * MM), int(1.3 * MM)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(190, 190, 190), width=int(0.25 * MM))
    for y in range(0, H, int(3 * MM)):
        d.line([(pan, y), (pan, y + int(1.5 * MM))], fill=(190, 190, 190), width=int(0.2 * MM))
    return hoja, (tope + al) / MM


def imposicion(caras, alto_mm):
    W, H = int(ANCHO_PAN * 2 * MM), int(alto_mm * MM)
    util_w = CARTA_W - 2 * int(MARGEN_IMP * MM)
    util_h = CARTA_H - 2 * int(MARGEN_IMP * MM)
    cols, filas = max(1, util_w // W), max(1, util_h // H)
    mx, my = (CARTA_W - cols * W) // 2, (CARTA_H - filas * H) // 2
    hojas = []
    for c in caras:
        pl = Image.new("RGB", (CARTA_W, CARTA_H), "white")
        for r in range(filas):
            for k in range(cols):
                pl.paste(c, (mx + k * W, my + r * H))
        d = ImageDraw.Draw(pl)
        largo, fino = int(4 * MM), int(0.25 * MM)
        for i in range(cols + 1):
            x = mx + i * W
            d.line([(x, my - largo), (x, my - int(1 * MM))], fill="black", width=fino)
            d.line([(x, my + filas * H + int(1 * MM)), (x, my + filas * H + largo)],
                   fill="black", width=fino)
        for i in range(filas + 1):
            y = my + i * H
            d.line([(mx - largo, y), (mx - int(1 * MM), y)], fill="black", width=fino)
            d.line([(mx + cols * W + int(1 * MM), y), (mx + cols * W + largo, y)],
                   fill="black", width=fino)
        hojas.append(pl)
    return hojas, cols * filas, cols, filas


def haz(alto_mm):
    caras = []
    for partes in ((bloques_contraportada, bloques_portada),
                   (bloques_contenido, bloques_promesa)):
        im, abajo = ornamento(alto_mm)
        d = ImageDraw.Draw(im)
        for i, blo in enumerate(partes):
            dibuja_panel(d, i * int(ANCHO_PAN * MM), alto_mm, abajo + 2, blo())
        caras.append(im)
    # el nombre lleva CENTIMETROS: 50 mm es "5x5", no "5x50"
    cm = alto_mm / 10
    et = ("5x%.0f" % cm) if abs(cm - round(cm)) < 0.01 else ("5x%.1f" % cm).replace(".", "_")
    caras[0].save(os.path.join(AQUI, f"RarAmore_{et}_afuera.png"), dpi=(DPI, DPI))
    caras[1].save(os.path.join(AQUI, f"RarAmore_{et}_adentro.png"), dpi=(DPI, DPI))
    caras[0].save(os.path.join(AQUI, f"RarAmore_librito_{et}.pdf"), save_all=True,
                  append_images=[caras[1]], resolution=DPI)
    hojas, n, cols, filas = imposicion(caras, alto_mm)
    hojas[0].save(os.path.join(AQUI, f"RarAmore_{et}_CARTA_{n}up.pdf"), save_all=True,
                  append_images=[hojas[1]], resolution=DPI)
    print(f"  5 x {alto_mm/10:.2f} cm  ->  {n} por hoja carta ({cols} col x {filas} filas)")
    return n


if __name__ == "__main__":
    for a in (sys.argv[1:] or ["93"]):
        haz(float(a))
