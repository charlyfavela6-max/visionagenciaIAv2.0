#!/usr/bin/env python3
"""Librito de Rar~Amore de 5 x 5 cm — la version que pidio Angel el 2 sep 23:08.

    python3 etiqueta_5x5.py

QUE CAMBIO CONTRA EL DE 5 x 10
------------------------------
1. «Mejor de 5 x 5. Que no sean de 5 x 10.» -> la hoja plana pasa de 10x10 a
   10x5 cm, con el mismo doblez vertical. Cada pagina del librito queda
   cuadrada de 5x5.
2. «Subale el tono de tinta para que al momento de imprimir se noten bien las
   letras.» -> el verde bajo de (20,74,52) a (11,58,39) y el claro de
   (58,125,90) a (31,92,63); y el grabado se oscurece tambien, porque venia
   demasiado palido para imprenta casera.
3. En hoja carta ya no caben 4 sino DIEZ: la teja de 100x50 mm entra dos veces
   a lo ancho (200 de 215.9) y cinco a lo alto (250 de 279.4).

EL TEXTO SE REPARTIO
--------------------
A la mitad de alto no cabe lo mismo. Las tres promesas se pasaron al panel de
adentro y la portada se quedo con el nombre y el gancho, que es lo que se ve
colgando del bote.
"""
import os
from PIL import Image, ImageChops, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
FUENTES = os.path.join(RAIZ, "fonts")
ARTE = os.path.join(AQUI, "librito_fondos", "exterior.png")

DPI = 600
MM = DPI / 25.4
PAN = int(50 * MM)                 # cada pagina del librito: 5 x 5 cm
HOJA_W, HOJA_H = PAN * 2, PAN      # la hoja plana: 10 x 5 cm
CARTA_W, CARTA_H = int(215.9 * MM), int(279.4 * MM)

VERDE = (11, 58, 39)               # subido de tono a peticion de Angel
VERDE_CLARO = (31, 92, 63)


def f(nombre, pt):
    return ImageFont.truetype(os.path.join(FUENTES, nombre), int(pt * MM / 2.845))


def cabe(d, texto, nombre, pt, ancho, esp=0):
    while pt > 3.5:
        fu = f(nombre, pt)
        largo = max(d.textlength(esp * " ".join(l) if esp else l, font=fu)
                    for l in texto.split("\n") if l.strip())
        if largo <= ancho:
            return fu
        pt -= 0.25
    return f(nombre, pt)


def centro(d, y, texto, fu, x0, an, color=VERDE, inter=1.3, esp=0):
    for l in texto.split("\n"):
        if not l.strip():
            y += fu.size * inter * 0.5; continue
        t = esp * " ".join(l) if esp else l
        w = d.textlength(t, font=fu)
        d.text((x0 + (an - w) / 2, y), t, font=fu, fill=color)
        y += fu.size * inter
    return y


def ornamento():
    """Un copete chico en cada panel y el filete doble. Sacado del mismo grabado
    del librito grande, oscurecido para que imprima."""
    arte = Image.open(ARTE).convert("RGB")
    e = arte.width
    copete = arte.crop((int(e * 0.53), int(e * 0.055), int(e * 0.97), int(e * 0.185)))
    # Oscurecer SOLO la tinta. Multiplicar por 0.72 tambien pinta el blanco de
    # gris (255 -> 184) y el copete sale como una caja gris pegada al panel.
    # Esta curva deja el 255 en 255 y hunde nada mas lo que ya era oscuro.
    copete = copete.point(lambda v: max(0, 255 - int((255 - v) * 1.5)))

    hoja = Image.new("RGB", (HOJA_W, HOJA_H), "white")
    an = int(26 * MM)
    al = int(an * copete.height / copete.width)
    c = copete.resize((an, al), Image.LANCZOS)
    for panel in (0, 1):
        x = panel * PAN + (PAN - an) // 2
        y = int(3.4 * MM)
        reg = hoja.crop((x, y, x + an, y + al))
        hoja.paste(ImageChops.darker(reg, c), (x, y))

    d = ImageDraw.Draw(hoja)
    for panel in (0, 1):
        x0 = panel * PAN
        for mm, gr in ((2.6, 3), (3.6, 1)):
            m = int(mm * MM)
            d.rectangle([x0 + m, m, x0 + PAN - m, HOJA_H - m], outline=VERDE, width=gr)
    # el doblez
    for y in range(0, HOJA_H, int(3 * MM)):
        d.line([(PAN, y), (PAN, y + int(1.5 * MM))], fill=(190, 190, 190), width=int(0.2 * MM))
    # guia de perforacion
    for panel in (0, 1):
        cx, cy, r = panel * PAN + PAN // 2, int(6 * MM), int(1.3 * MM)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(190, 190, 190), width=int(0.25 * MM))
    return hoja


# ---- los cuatro paneles. m = margen util dentro de cada 50 mm ----
def portada(d, x0):
    m, an = int(5 * MM), PAN - int(10 * MM)
    centro(d, int(16 * MM), "RAR~AMORE",
           cabe(d, "RAR~AMORE", "CormorantGaramond-Bold.ttf", 15, an, esp=1),
           x0, PAN, esp=1)
    y = int(26 * MM)
    d.line([(x0 + PAN // 2 - int(8 * MM), y), (x0 + PAN // 2 + int(8 * MM), y)],
           fill=VERDE, width=3)
    centro(d, int(28.5 * MM), "C Á P S U L A S", f("Montserrat-Medium.ttf", 5),
           x0 + m, an, color=VERDE_CLARO)
    centro(d, int(35 * MM), "Comienza a cuidarte\na partir de los 30",
           f("CormorantGaramond-Bold.ttf", 8.5), x0 + m, an, inter=1.35)


def contraportada(d, x0):
    m, an = int(4.5 * MM), PAN - int(9 * MM)
    centro(d, int(15 * MM), "PRECIO DE PROMOCIÓN", f("Montserrat-Black.ttf", 4.5),
           x0 + m, an, color=VERDE_CLARO)
    centro(d, int(19 * MM), "Bálsamo + Cápsulas", f("CormorantGaramond-Bold.ttf", 8),
           x0 + m, an)
    centro(d, int(24 * MM), "$1,399", f("Montserrat-Black.ttf", 15), x0, PAN)
    centro(d, int(32 * MM), "antes $1,600", f("Montserrat-Medium.ttf", 4.5),
           x0 + m, an, color=VERDE_CLARO)
    centro(d, int(38 * MM), "PEDIDOS WHATSAPP", f("Montserrat-Medium.ttf", 4.2),
           x0 + m, an, color=VERDE_CLARO)
    centro(d, int(41 * MM), "818 466 84 56", f("Montserrat-Black.ttf", 8), x0, PAN)


def contenido(d, x0):
    m, an = int(4 * MM), PAN - int(8 * MM)
    centro(d, int(13 * MM), "CÁPSULAS · CONTIENE", f("Montserrat-Black.ttf", 4.6),
           x0 + m, an, color=VERDE_CLARO)
    ing = ("Piel de camarón", "Calcio", "Magnesio", "Vitamina D", "Semilla de uva",
           "Cáscara de limón", "Cáscara de toronja", "Cáscara de naranja")
    fu = cabe(d, "\n".join(ing), "Montserrat-Medium.ttf", 5.3, an)
    y = int(17 * MM)
    for t in ing:
        w = d.textlength(t, font=fu)
        d.text((x0 + (PAN - w) / 2, y), t, font=fu, fill=VERDE)
        y += fu.size * 1.62
    centro(d, int(42.5 * MM), "CONTENIDO:  30 CÁPSULAS", f("Montserrat-Medium.ttf", 4.2),
           x0 + m, an, color=VERDE_CLARO)


def promesa(d, x0):
    m, an = int(4.5 * MM), PAN - int(9 * MM)
    centro(d, int(14.5 * MM), "Vive sin dolores.\nVive sin estrés.\nVive sin insomnio.",
           f("CormorantGaramond-Bold.ttf", 8.5), x0 + m, an, inter=1.45)
    y = int(28 * MM)
    d.line([(x0 + PAN // 2 - int(8 * MM), y), (x0 + PAN // 2 + int(8 * MM), y)],
           fill=VERDE, width=3)
    bien = "BIENESTAR PARA TUS\nMÚSCULOS Y ARTICULACIONES"
    centro(d, int(31 * MM), bien, cabe(d, bien, "Montserrat-Black.ttf", 5, an),
           x0 + m, an, inter=1.5)
    centro(d, int(41 * MM), "818 466 84 56", f("Montserrat-Black.ttf", 7.5), x0, PAN)


def cara(partes):
    im = ornamento()
    d = ImageDraw.Draw(im)
    for parte, x0 in partes:
        parte(d, x0)
    return im


def imposicion(ext, inte):
    """10 por hoja carta: 2 columnas x 5 filas de la teja de 100 x 50 mm."""
    mx, my = (CARTA_W - 2 * HOJA_W) // 2, (CARTA_H - 5 * HOJA_H) // 2
    hojas = []
    for c in (ext, inte):
        pl = Image.new("RGB", (CARTA_W, CARTA_H), "white")
        for fila in range(5):
            for col in range(2):
                pl.paste(c, (mx + col * HOJA_W, my + fila * HOJA_H))
        d = ImageDraw.Draw(pl)
        largo, fino = int(4 * MM), int(0.25 * MM)
        for i in range(3):
            x = mx + i * HOJA_W
            d.line([(x, my - largo), (x, my - int(1 * MM))], fill="black", width=fino)
            d.line([(x, my + 5 * HOJA_H + int(1 * MM)), (x, my + 5 * HOJA_H + largo)],
                   fill="black", width=fino)
        for i in range(6):
            y = my + i * HOJA_H
            d.line([(mx - largo, y), (mx - int(1 * MM), y)], fill="black", width=fino)
            d.line([(mx + 2 * HOJA_W + int(1 * MM), y), (mx + 2 * HOJA_W + largo, y)],
                   fill="black", width=fino)
        hojas.append(pl)
    return hojas


if __name__ == "__main__":
    ext = cara([(contraportada, 0), (portada, PAN)])
    inte = cara([(contenido, 0), (promesa, PAN)])
    ext.save(os.path.join(AQUI, "RarAmore_5x5_1_exterior.png"), dpi=(DPI, DPI))
    inte.save(os.path.join(AQUI, "RarAmore_5x5_2_interior.png"), dpi=(DPI, DPI))
    ext.save(os.path.join(AQUI, "RarAmore_librito_5x5.pdf"), save_all=True,
             append_images=[inte], resolution=DPI, title="Rar~Amore librito 5x5")

    h1, h2 = imposicion(ext, inte)
    h1.save(os.path.join(AQUI, "RarAmore_5x5_CARTA_10up.pdf"), save_all=True,
            append_images=[h2], resolution=DPI, title="Rar~Amore · 10 libritos por hoja")
    h1.save(os.path.join(AQUI, "RarAmore_5x5_CARTA_exterior.png"), dpi=(DPI, DPI))
    print("listo · librito 5x5 y hoja carta con 10")
