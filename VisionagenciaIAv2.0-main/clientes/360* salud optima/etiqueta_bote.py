#!/usr/bin/env python3
"""Las etiquetas de BOTE de las cápsulas — Kuira Ba y Rar~Amore — corregidas.

    python3 etiqueta_bote.py              # las tres: kuiraba30, raramore30, raramore60
    python3 etiqueta_bote.py kuiraba30

QUE PIDIO ANGEL EL 3 SEP
------------------------
1. «Las letras están muy chiquitas (SOLO LAS CHICAS)… casi no se pueden dar
   lectura. Las grandes están bien de tamaño.»
2. «Le agrega Fecha de caducidad: Dic del 2028.»
3. Los INGREDIENTES de las cápsulas, que en la v5 era una sola línea
   («Boswellia Serrata») y son siete.

DE DONDE SALE EL ARTE
---------------------
No se vuelve a inventar: las guirnaldas de oro, el sello «100% NATURAL» y el
icono de WhatsApp se RECORTAN de su propio PDF v5 (el que él reenvió), a 600
dpi. Así el arte es idéntico al que ya aprobó y lo único que cambia es el
texto. El fondo es plano (1,29,15), así que un recorte rectangular se pega sin
costura.

    python3 etiqueta_bote.py sprites      # rehace los recortes desde el PDF

POR QUE SE MOVIO EL ACOMODO
---------------------------
Con un solo ingrediente cabía todo en la columna izquierda. Con SIETE y encima
más grandes, ya no. Así que las dos leyendas legales se bajaron al pie —donde
la guirnalda deja un claro al centro, que es donde su v5 ya ponía CONTENIDO— y
la columna izquierda se quedó con ingredientes y modo de uso, que es lo que la
gente lee en el anaquel.

MEDIDA: la misma de su v5 — 464.88 x 187.2 pts = 164.0 x 66.0 mm.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = "/workspaces/visionagenciaIAv2.0/VisionagenciaIAv2.0-main"
FUENTES = os.path.join(RAIZ, "fonts")
SPRITES = os.path.join(AQUI, "bote_sprites")
PDF_V5 = os.path.join(AQUI, "pedido_3sep", "47_09-03_160255_document.pdf")

DPI = 600
MM = DPI / 25.4
ANCHO_MM, ALTO_MM = 164.03, 66.04
W, H = int(ANCHO_MM * MM), int(ALTO_MM * MM)

FONDO = (1, 29, 15)
CREMA = (240, 229, 199)
ORO = (198, 166, 106)

SERIF = "CormorantGaramond-Bold.ttf"


def f(nombre, pt):
    return ImageFont.truetype(os.path.join(FUENTES, nombre), max(6, int(pt * MM / 2.845)))


# ------------------------------------------------------------------ sprites
def saca_sprites():
    """Recorta del PDF v5 las bandas de guirnalda, el sello y el WhatsApp."""
    import subprocess
    os.makedirs(SPRITES, exist_ok=True)
    base = os.path.join(SPRITES, "_v5")
    subprocess.run(["pdftoppm", "-png", "-r", str(DPI), "-f", "1", "-l", "1",
                    PDF_V5, base], check=True)
    im = Image.open(base + "-1.png").convert("RGB")
    w, h = im.size
    for nom, (a, b, c, d) in {
            "banda_arriba": (0, 0, 1, .185),
            "banda_abajo": (0, .755, 1, 1),
            "sello": (.560, .425, .685, .640),
            "wa": (.310, .590, .365, .705)}.items():
        im.crop((int(a * w), int(b * h), int(c * w), int(d * h))).save(
            os.path.join(SPRITES, nom + ".png"))
    print("  sprites listos en", SPRITES)


def sprite(nom):
    return Image.open(os.path.join(SPRITES, nom + ".png")).convert("RGB")


# ------------------------------------------------------------------ texto
def linea(d, x, y, texto, fu, color, esp=0, centro=None):
    t = esp * " ".join(texto) if esp else texto
    if centro is not None:
        x = centro - d.textlength(t, font=fu) / 2
    d.text((x, y), t, font=fu, fill=color)
    return y + fu.size


def parrafo(d, x, y, lineas, fu, color, inter=1.30):
    for l in lineas:
        d.text((x, y), l, font=fu, fill=color)
        y += fu.size * inter
    return y


def regla(d, x0, x1, y, color=ORO, gr=None):
    d.line([(x0, y), (x1, y)], fill=color, width=gr or max(1, int(0.18 * MM)))


# ------------------------------------------------------------------ contenido
INGREDIENTES = ("Piel de camarón", "Boswellia Serrata", "Calcio", "Magnesio",
                "Extracto de naranja", "Extracto de limón",
                "Extracto de semilla de uva (Resveratrol)")

MODO = ("2 cápsulas con los alimentos", "por la mañana, diariamente")
UTIL = ("Regenerador de cartílagos", "Anti-estrés")
LEGAL_D = ("Indicado para mayores de 18 años en adelante.",)
LEGAL_D2 = ("Este producto no es un medicamento,", "es responsabilidad de quien lo",
            "recomienda y lo usa.")
PIE = "No se deje al alcance de los niños  ·  Manténgase en un lugar fresco y seco"
CADUCIDAD = "CADUCIDAD:  DIC 2028"

MODELOS = {
    "kuiraba30":  ("KUIRA BA", 30),
    "raramore30": ("Rar ~ Amore", 30),
    "raramore60": ("Rar ~ Amore", 60),
}


def haz(clave):
    nombre, capsulas = MODELOS[clave]
    im = Image.new("RGB", (W, H), FONDO)

    arriba, abajo = sprite("banda_arriba"), sprite("banda_abajo")
    im.paste(arriba.resize((W, arriba.height), Image.LANCZOS), (0, 0))
    im.paste(abajo.resize((W, abajo.height), Image.LANCZOS), (0, H - abajo.height))

    d = ImageDraw.Draw(im)
    mm = lambda v: int(v * MM)

    # ---- columna izquierda: ingredientes y modo de uso ----------------------
    # Antes eran 5 pt y una sola linea de ingredientes; ahora 7.4 y siete.
    x = mm(9)
    y = mm(13.5)
    y = linea(d, x, y, "INGREDIENTES:", f(SERIF, 9), ORO, esp=1) + mm(1.4)
    y = parrafo(d, x, y, INGREDIENTES, f(SERIF, 8.4), CREMA, inter=1.22)
    y += mm(2.2)
    y = linea(d, x, y, "MODO DE USO:", f(SERIF, 9), ORO, esp=1) + mm(1.4)
    parrafo(d, x, y, MODO, f(SERIF, 8.4), CREMA, inter=1.22)

    # ---- columna derecha: para que sirve y lo legal -------------------------
    x = mm(112)
    y = mm(13.5)
    y = linea(d, x, y, "ÚTIL PARA:", f(SERIF, 9), ORO, esp=1) + mm(1.4)
    y = parrafo(d, x, y, UTIL, f(SERIF, 8.4), CREMA, inter=1.22)
    y += mm(1.6)
    regla(d, x, mm(155), y)
    y += mm(2.4)
    y = parrafo(d, x, y, LEGAL_D, f(SERIF, 7.4), CREMA, inter=1.22)
    y += mm(1.8)
    parrafo(d, x, y, LEGAL_D2, f(SERIF, 7.4), CREMA, inter=1.22)

    # ---- centro: el nombre, que NO se toca de tamaño ------------------------
    cx = mm(60) + (mm(106) - mm(60)) // 2
    y = mm(14.5)
    fu = f(SERIF, 30)
    while d.textlength(nombre, font=fu) > mm(50):
        fu = f(SERIF, fu.size * 2.845 / MM - 0.5)
    y = linea(d, 0, y, nombre, fu, CREMA, centro=cx)
    y += mm(1.6)
    regla(d, cx - mm(23), cx + mm(23), y)
    y += mm(2.0)
    y = linea(d, 0, y, "CÁPSULAS", f(SERIF, 11), CREMA, esp=1, centro=cx) + mm(3.0)

    wa = sprite("wa")
    alto_wa = mm(6.2)
    wa = wa.resize((int(wa.width * alto_wa / wa.height), alto_wa), Image.LANCZOS)
    fu_ped = f(SERIF, 10)
    ancho_ped = d.textlength("P E D I D O S   W H A T S A P P", font=fu_ped)
    x_wa = int(cx - (wa.width + mm(2) + ancho_ped) / 2)
    im.paste(wa, (x_wa, int(y)))
    d.text((x_wa + wa.width + mm(2), y + mm(0.6)),
           "P E D I D O S   W H A T S A P P", font=fu_ped, fill=ORO)
    y += mm(6.6)
    linea(d, 0, y, "81 8466 8456", f(SERIF, 15), CREMA, centro=cx)

    sel = sprite("sello")
    alto_sel = mm(13)
    sel = sel.resize((int(sel.width * alto_sel / sel.height), alto_sel), Image.LANCZOS)
    im.paste(sel, (mm(98), mm(27)))

    # ---- pie: contenido, caducidad y las dos leyendas ----------------------
    # Aqui la guirnalda deja un claro al centro; es donde su v5 ponia CONTENIDO.
    cxx = W // 2
    y = mm(50.5)
    t = "CONTENIDO: %d CÁPSULAS      ·      %s" % (capsulas, CADUCIDAD)
    fu = f(SERIF, 9.5)
    an = d.textlength(t, font=fu)
    d.text((cxx - an / 2, y), t, font=fu, fill=CREMA)
    regla(d, cxx - an / 2 - mm(8), cxx - an / 2 - mm(2.5), y + fu.size * 0.55)
    regla(d, cxx + an / 2 + mm(2.5), cxx + an / 2 + mm(8), y + fu.size * 0.55)

    y += mm(4.6)
    fu = f(SERIF, 7.8)
    d.text((cxx - d.textlength(PIE, font=fu) / 2, y), PIE, font=fu, fill=ORO)

    png = os.path.join(AQUI, "360_%s_IMPRENTA_v6.png" % clave.upper())
    pdf = os.path.join(AQUI, "360_%s_IMPRENTA_v6.pdf" % clave.upper())
    im.save(png, dpi=(DPI, DPI))
    im.save(pdf, resolution=DPI, title="360 Salud Óptima · %s" % nombre)
    print("  %-11s %s  (%.1f x %.1f mm)" % (clave, os.path.basename(pdf), ANCHO_MM, ALTO_MM))
    return pdf


if __name__ == "__main__":
    args = sys.argv[1:]
    if not os.path.isdir(SPRITES) or "sprites" in args:
        saca_sprites()
        args = [a for a in args if a != "sprites"]
    for clave in (args or list(MODELOS)):
        haz(clave)
