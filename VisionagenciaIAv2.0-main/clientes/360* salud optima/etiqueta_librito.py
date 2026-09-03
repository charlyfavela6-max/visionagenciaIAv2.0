#!/usr/bin/env python3
"""Etiqueta-librito de Rar~Amore para colgar del bote con hilo.

Lo que pidio Angel (WhatsApp 2 sep, notas de voz 05 y 12 + texto de las 18:40):
hoja de 10 x 10 cm con doblez VERTICAL al centro -> librito cerrado de 5 x 10 cm,
fondo blanco y letras verdes, con el precio de promocion.

    pagina 1 = cara EXTERIOR  (izq contraportada / der PORTADA)
    pagina 2 = cara INTERIOR  (izq el contenido / der el precio)

Se imprime a doble cara, se dobla al centro y se perfora arriba para el hilo.
No usa IA: el texto tiene que salir exacto, y GPT Image lo deforma.

    python3 etiqueta_librito.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
FUENTES = os.path.join(AQUI, "..", "..", "fonts")
DPI = 600
MM = DPI / 25.4
HOJA = int(100 * MM)              # 10 x 10 cm
MEDIA = HOJA // 2                 # cada pagina del librito: 5 cm de ancho
VERDE = (20, 74, 52)              # el verde del bote
VERDE_CLARO = (58, 125, 90)
GRIS = (200, 200, 200)


def f(nombre, pt):
    return ImageFont.truetype(os.path.join(FUENTES, nombre), int(pt * MM / 2.845))


def centrado(d, y, texto, fuente, x0, ancho, color=VERDE, interlinea=1.25):
    """Escribe centrado en la columna [x0, x0+ancho) y devuelve la nueva y."""
    for linea in texto.split("\n"):
        if not linea.strip():
            y += fuente.size * interlinea * 0.5
            continue
        w = d.textlength(linea, font=fuente)
        d.text((x0 + (ancho - w) / 2, y), linea, font=fuente, fill=color)
        y += fuente.size * interlinea
    return y


def marco(d, x0):
    """Doblez al centro y guia de perforacion arriba de cada pagina."""
    for y in range(0, HOJA, int(3 * MM)):
        d.line([(MEDIA, y), (MEDIA, y + int(1.5 * MM))], fill=GRIS, width=int(0.2 * MM))
    cx, cy, r = x0 + MEDIA // 2, int(6 * MM), int(1.5 * MM)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=GRIS, width=int(0.25 * MM))


def portada(d):
    x0, an = MEDIA, MEDIA
    m = int(7 * MM)
    y = int(16 * MM)
    y = centrado(d, y, "COMIENZA A CUIDARTE\nA PARTIR DE LOS 30",
                 f("Montserrat-Black.ttf", 9), x0 + m, an - 2 * m)
    y += int(6 * MM)
    centrado(d, y, "Rar ~ Amore", f("CormorantGaramond-Bold.ttf", 26), x0, an)
    y += int(16 * MM)
    d.line([(x0 + an // 2 - int(10 * MM), y), (x0 + an // 2 + int(10 * MM), y)],
           fill=VERDE_CLARO, width=int(0.5 * MM))
    y += int(7 * MM)
    y = centrado(d, y, "Vive sin dolores.\nVive sin estrés.\nVive sin insomnio.",
                 f("Montserrat-Medium.ttf", 10), x0 + m, an - 2 * m, interlinea=1.6)
    y += int(8 * MM)
    centrado(d, y, "C Á P S U L A S", f("Montserrat-Medium.ttf", 7),
             x0 + m, an - 2 * m, color=VERDE_CLARO)


def contraportada(d):
    x0, an = 0, MEDIA
    m = int(7 * MM)
    y = int(20 * MM)
    y = centrado(d, y, "PRECIO DE PROMOCIÓN", f("Montserrat-Black.ttf", 7.5),
                 x0 + m, an - 2 * m)
    y += int(3 * MM)
    y = centrado(d, y, "Paquete\nBálsamo + Cápsulas", f("Montserrat-Medium.ttf", 9),
                 x0 + m, an - 2 * m, interlinea=1.4)
    y += int(4 * MM)
    y = centrado(d, y, "$1,399", f("Montserrat-Black.ttf", 22), x0, an)
    y += int(3 * MM)
    y = centrado(d, y, "Precio normal $1,600", f("Montserrat-Medium.ttf", 7),
                 x0 + m, an - 2 * m, color=VERDE_CLARO)
    y = int(74 * MM)
    y = centrado(d, y, "PEDIDOS WHATSAPP", f("Montserrat-Medium.ttf", 6.5),
                 x0 + m, an - 2 * m, color=VERDE_CLARO)
    y += int(1 * MM)
    centrado(d, y, "818 466 84 56", f("Montserrat-Black.ttf", 11), x0, an)


def contenido(d):
    x0, an = 0, MEDIA
    m = int(6 * MM)
    y = int(15 * MM)
    y = centrado(d, y, "Cápsulas", f("CormorantGaramond-Bold.ttf", 20), x0, an)
    y += int(5 * MM)
    y = centrado(d, y, "CONTIENE", f("Montserrat-Black.ttf", 7),
                 x0 + m, an - 2 * m, color=VERDE_CLARO)
    y += int(4 * MM)
    ingredientes = ["Piel de camarón", "Calcio", "Magnesio", "Vitamina D",
                    "Semilla de uva", "Cáscara de limón", "Cáscara de toronja",
                    "Cáscara de naranja"]
    fu = f("Montserrat-Medium.ttf", 8.5)
    for ing in ingredientes:
        w = d.textlength(ing, font=fu)
        d.text((x0 + (an - w) / 2, y), ing, font=fu, fill=VERDE)
        y += fu.size * 1.55
    y += int(4 * MM)
    centrado(d, y, "30 cápsulas", f("Montserrat-Medium.ttf", 7),
             x0 + m, an - 2 * m, color=VERDE_CLARO)


def promesa(d):
    x0, an = MEDIA, MEDIA
    m = int(7 * MM)
    y = int(24 * MM)
    y = centrado(d, y, "A partir de los 30\ncuídate con",
                 f("Montserrat-Medium.ttf", 9.5), x0 + m, an - 2 * m, interlinea=1.5)
    y += int(5 * MM)
    y = centrado(d, y, "Rar ~ Amore", f("CormorantGaramond-Bold.ttf", 22), x0, an)
    y += int(16 * MM)
    d.line([(x0 + an // 2 - int(10 * MM), y), (x0 + an // 2 + int(10 * MM), y)],
           fill=VERDE_CLARO, width=int(0.5 * MM))
    y += int(6 * MM)
    y = centrado(d, y, "BIENESTAR PARA TUS\nMÚSCULOS Y\nARTICULACIONES",
                 f("Montserrat-Black.ttf", 8), x0 + m, an - 2 * m, interlinea=1.5)
    y = int(88 * MM)
    centrado(d, y, "818 466 84 56", f("Montserrat-Black.ttf", 10), x0, an)


def cara(dibuja):
    im = Image.new("RGB", (HOJA, HOJA), "white")
    d = ImageDraw.Draw(im)
    for parte in dibuja:
        parte(d)
    marco(d, 0)
    marco(d, MEDIA)
    return im


if __name__ == "__main__":
    exterior = cara([contraportada, portada])
    interior = cara([contenido, promesa])
    pdf = os.path.join(AQUI, "RarAmore_etiqueta_librito_10x10.pdf")
    exterior.save(pdf, save_all=True, append_images=[interior],
                  resolution=DPI, title="Rar~Amore etiqueta librito")
    exterior.save(os.path.join(AQUI, "RarAmore_librito_1_exterior.png"), dpi=(DPI, DPI))
    interior.save(os.path.join(AQUI, "RarAmore_librito_2_interior.png"), dpi=(DPI, DPI))
    print("listo:", pdf)
