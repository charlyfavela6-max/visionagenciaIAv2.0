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
            # OJO: a .755 el recorte se lleva PEGADO el «CONTENIDO: 30
            # CÁPSULAS» de su v5, y al escribir el nuestro encima salia doble.
            # Se corta por debajo de esa linea.
            "banda_abajo": (0, .862, 1, 1),
            # el recorte del sello arrastraba un pedazo del filete de oro de su v5, que
            # quedaba flotando arriba a la izquierda: se aprieta.
            "sello": (.582, .448, .682, .630),
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
# Lista de Angel del 3 sep 15:32, con «Extracto» en vez de «cascara» (15:42) y
# la Vitamina D enseguida del Calcio (20:42).
INGREDIENTES = ("Piel de camarón", "Boswellia Serrata", "Calcio", "Vitamina D",
                "Magnesio", "Extracto de naranja", "Extracto de limón",
                "Extracto de semilla de uva", "(Resveratrol)")

MODO = ("2 cápsulas con los alimentos", "por la mañana, diariamente")
UTIL = ("Rodillas sanas", "Músculos sanos", "Huesos sanos",
        "Piel y cabello radiante", "Anti-estrés", "Anti-ansiedad")
# Al pie y en una sola linea: con seis «útil para» ya no caben en la columna.
# UN SOLO renglon: con dos, el segundo caia encima de la guirnalda de abajo y
# no se leia. Se aprieta hasta que entre a lo ancho de la etiqueta.
LEGAL_PIE = ("Indicado para mayores de 18 años  ·  No se deje al alcance de los niños  ·  "
             "Manténgase en un lugar fresco y seco  ·  Este producto no es un medicamento, "
             "es responsabilidad de quien lo recomienda y lo usa",)
CADUCIDAD = "CADUCIDAD:  DIC 2028"

MODELOS = {
    "kuiraba30":  ("KUIRA BA", 30),
    "raramore30": ("Rar ~ Amore", 30),
    "raramore60": ("Rar ~ Amore", 60),
}

# (texto, fuente, pt, color, interlinea, hueco que va ANTES en mm)
def bloques_izq():
    return [("INGREDIENTES:", SERIF, 9.0, ORO, 1.15, 0.0, 1)] + \
           [(t, SERIF, 11.0, CREMA, 1.12, (1.2 if i == 0 else 0.0), 0)
            for i, t in enumerate(INGREDIENTES)]


def bloques_der():
    b = [("ÚTIL PARA:", SERIF, 9.0, ORO, 1.15, 0.0, 1)]
    b += [(t, SERIF, 11.0, CREMA, 1.12, (1.2 if i == 0 else 0.0), 0)
          for i, t in enumerate(UTIL)]
    b += [("MODO DE USO:", SERIF, 9.0, ORO, 1.15, 2.2, 1)]
    b += [(t, SERIF, 9.0, CREMA, 1.15, (1.2 if i == 0 else 0.0), 0)
          for i, t in enumerate(MODO)]
    return b


def columna(d, im, x_mm, an_mm, y0_mm, y1_mm, bloques):
    """Escribe los bloques entre y0 e y1, encogiendo TODO si no caben.

    La v6 iba con posiciones fijas y se encimaba: «PEDIDOS WHATSAPP» debajo del
    sello, «CONTENIDO» encima del modo de uso. Aqui se mide primero y, si no
    entra a lo alto o a lo ancho, baja el cuerpo de la columna entera. Misma
    leccion que el librito.
    """
    an = an_mm * MM
    factor = 1.0
    while factor > 0.45:
        alto = 0.0
        cabe = True
        for texto, fam, pt, _c, inter, antes, _e in bloques:
            fu = f(fam, pt * factor)
            if d.textlength(texto, font=fu) > an:
                cabe = False
                break
            alto += antes * MM + fu.size * inter
        if cabe and alto <= (y1_mm - y0_mm) * MM:
            break
        factor -= 0.02
    y = y0_mm * MM
    for texto, fam, pt, color, inter, antes, esp in bloques:
        fu = f(fam, pt * factor)
        y += antes * MM
        t = " ".join(texto) if esp else texto
        d.text((x_mm * MM, y), t, font=fu, fill=color)
        y += fu.size * inter
    return factor


def haz(clave):
    nombre, capsulas = MODELOS[clave]
    im = Image.new("RGB", (W, H), FONDO)

    arriba, abajo = sprite("banda_arriba"), sprite("banda_abajo")
    im.paste(arriba.resize((W, arriba.height), Image.LANCZOS), (0, 0))
    im.paste(abajo.resize((W, abajo.height), Image.LANCZOS), (0, H - abajo.height))

    d = ImageDraw.Draw(im)
    mm = lambda v: int(v * MM)

    # Tres columnas y un pie. El sello y el bloque del centro NO se solapan
    # porque el centro va centrado en x=78 (no en la mitad de la etiqueta),
    # igual que en su v5, y el sello vive a su derecha.
    columna(d, im, 8, 42, 13.0, 48.5, bloques_izq())
    columna(d, im, 118, 40, 13.0, 48.5, bloques_der())

    # ---- centro: el nombre, que NO se toca de tamano ------------------------
    cx = mm(78)
    y = mm(14.0)
    fu = f(SERIF, 30)
    while d.textlength(nombre, font=fu) > mm(44):
        fu = f(SERIF, fu.size * 2.845 / MM - 0.5)
    y = linea(d, 0, y, nombre, fu, CREMA, centro=cx)
    y += mm(1.4)
    regla(d, cx - mm(21), cx + mm(21), y)
    y += mm(1.8)
    y = linea(d, 0, y, "CÁPSULAS", f(SERIF, 11), CREMA, esp=1, centro=cx) + mm(3.2)

    wa = sprite("wa")
    alto_wa = mm(5.8)
    wa = wa.resize((int(wa.width * alto_wa / wa.height), alto_wa), Image.LANCZOS)
    fu_ped = f(SERIF, 8.0)
    ped = "P E D I D O S   W H A T S A P P"
    x_wa = int(cx - (wa.width + mm(2) + d.textlength(ped, font=fu_ped)) / 2)
    im.paste(wa, (x_wa, int(y)))
    d.text((x_wa + wa.width + mm(2), y + mm(0.5)), ped, font=fu_ped, fill=ORO)
    y += mm(6.2)
    linea(d, 0, y, "81 8466 8456", f(SERIF, 14), CREMA, centro=cx)

    sel = sprite("sello")
    alto_sel = mm(12)
    sel = sel.resize((int(sel.width * alto_sel / sel.height), alto_sel), Image.LANCZOS)
    im.paste(sel, (mm(102), mm(31)))

    # ---- pie: contenido y caducidad, en el claro de la guirnalda ----------
    cm = W // 2
    y = mm(49.6)
    t = "CONTENIDO: %d CÁPSULAS      ·      %s" % (capsulas, CADUCIDAD)
    fu = f(SERIF, 9.5)
    an = d.textlength(t, font=fu)
    d.text((cm - an / 2, y), t, font=fu, fill=CREMA)
    regla(d, cm - an / 2 - mm(8), cm - an / 2 - mm(2.5), y + fu.size * 0.55)
    regla(d, cm + an / 2 + mm(2.5), cm + an / 2 + mm(8), y + fu.size * 0.55)
    y += mm(4.4)
    for l in LEGAL_PIE:
        fl = f(SERIF, 7.6)
        while d.textlength(l, font=fl) > W - mm(16):
            fl = f(SERIF, fl.size * 2.845 / MM - 0.25)
        d.text((cm - d.textlength(l, font=fl) / 2, y), l, font=fl, fill=ORO)
        y += fl.size * 1.25

    png = os.path.join(AQUI, "360_%s_IMPRENTA_v7.png" % clave.upper())
    pdf = os.path.join(AQUI, "360_%s_IMPRENTA_v7.pdf" % clave.upper())
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
