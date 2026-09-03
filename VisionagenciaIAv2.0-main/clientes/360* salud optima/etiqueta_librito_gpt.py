#!/usr/bin/env python3
"""Etiqueta-librito de Rar~Amore con el arte hecho en GPT Image.

Estilo: el de las etiquetas Kuira Ba (grabado botanico fino, filete doble,
capitulares espaciadas, sello redondo) pero INVERTIDO — fondo blanco y todo el
verde bosque, que es lo que pidio Angel.

Medidas que dio: librito de 5 x 10 cm cerrado. O sea hoja de 10 x 10 cm con
doblez vertical al centro, impresa a doble cara.

    python3 etiqueta_librito_gpt.py fondos     # pide el arte a GPT Image (~$0.05)
    python3 etiqueta_librito_gpt.py arma       # pone el texto encima y saca el PDF
    python3 etiqueta_librito_gpt.py            # las dos cosas

GPT Image pone el ORNAMENTO; el texto va encima con tipografia de verdad, porque
son ocho ingredientes en cuerpo chico y la IA los deforma. El arte es suyo, las
letras salen exactas.
"""
import base64, json, os, sys, time, urllib.request
from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
FUENTES = os.path.join(RAIZ, "fonts")
FONDOS = os.path.join(AQUI, "librito_fondos")
REF = os.path.join(AQUI, "etiquetas", "KUIRABA_verde_v1.png")
WAVESPEED = "https://api.wavespeed.ai/api/v3"

DPI = 600
MM = DPI / 25.4
HOJA = int(100 * MM)
MEDIA = HOJA // 2
VERDE = (20, 74, 52)
VERDE_CLARO = (58, 125, 90)


# ---------------------------------------------------------------- GPT Image
def env(nombre):
    for l in open(os.path.join(RAIZ, ".env"), encoding="utf8", errors="replace"):
        if l.startswith(nombre + "="):
            return l.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get(nombre, "")


CAB = {"Authorization": "Bearer " + env("WAVESPEED_API_KEY"),
       "Content-Type": "application/json"}


def uri(ruta):
    tipo = "png" if ruta.lower().endswith(".png") else "jpeg"
    return "data:image/%s;base64,%s" % (
        tipo, base64.b64encode(open(ruta, "rb").read()).decode())


def pide(ruta, cuerpo):
    req = urllib.request.Request(WAVESPEED + "/" + ruta,
                                 data=json.dumps(cuerpo).encode(), headers=CAB)
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())


def espera(id_):
    for _ in range(180):
        time.sleep(2)
        req = urllib.request.Request("%s/predictions/%s/result" % (WAVESPEED, id_),
                                     headers=CAB)
        d = (json.loads(urllib.request.urlopen(req, timeout=60).read()) or {}).get("data") or {}
        if d.get("status") == "completed":
            return d["outputs"][0]
        if d.get("status") == "failed":
            raise RuntimeError("WaveSpeed fallo: %s" % d.get("error"))
    raise RuntimeError("se acabo la espera")


BASE = (
    "Design the ornamental artwork for a small apothecary label, in EXACTLY the "
    "engraving style of the reference image: fine antique botanical line-engraving "
    "of medicinal leaves, sprigs and berries, hairline double rule borders, the look "
    "of an old herbal pharmacy label. "
    "INVERT the colour scheme of the reference: the background is PURE WHITE, clean "
    "and empty, and every line, leaf and rule is DEEP FOREST GREEN. No dark "
    "background anywhere, no gold, no cream, no beige, no texture, no paper grain — "
    "flat white paper with green ink only. "
    "The square sheet is split into TWO EQUAL VERTICAL PANELS by a thin dashed green "
    "fold line running straight down the exact middle, from top edge to bottom edge. "
    "Each panel carries its own hairline double-rule green frame, inset about 5mm "
    "from the sheet edges and from the fold line. "
    "{arte} "
    "ABSOLUTELY NO TEXT: no letters, no words, no numbers, no signatures, no logos, "
    "no watermark anywhere in the image. Ornament only. Leave the whole middle of "
    "each panel completely EMPTY WHITE — that is where the type will be set later. "
    "Flat vector-clean print artwork, square 1:1, no perspective, no mockup, no "
    "bottle, no hands, no shadows."
)

CARAS = {
    "exterior": "In the LEFT panel, a slender engraved botanical sprig arching across "
                "the top inside the frame and a smaller mirrored sprig at the bottom. "
                "In the RIGHT panel, a fuller crown of engraved leaves and berries "
                "across the top, and at the bottom a small empty circular medallion "
                "made of a laurel wreath — an empty ring, nothing written inside it.",
    "interior": "In BOTH panels, a narrow vertical garland of engraved leaves running "
                "down the inner edge of the frame on each side, and one small sprig "
                "centred at the very bottom of each panel. Keep it lighter and airier "
                "than the outside face.",
}


def fondo(cara):
    os.makedirs(FONDOS, exist_ok=True)
    destino = os.path.join(FONDOS, "%s.png" % cara)
    if os.path.exists(destino):
        print("  ya existe %s — borralo si quieres rehacerlo" % cara)
        return destino
    d = pide("openai/gpt-image-2/edit", {
        "prompt": BASE.format(arte=CARAS[cara]),
        "images": [uri(REF)],
        "aspect_ratio": "1:1",
        "output_format": "png",
    })
    url = espera(d["data"]["id"])
    with urllib.request.urlopen(url, timeout=240) as r:
        open(destino, "wb").write(r.read())
    print("  listo", destino)
    return destino


# ---------------------------------------------------------------- tipografia
def f(nombre, pt):
    return ImageFont.truetype(os.path.join(FUENTES, nombre), int(pt * MM / 2.845))


def cabe(d, texto, nombre, pt, ancho, espaciado=0):
    """Baja el cuerpo hasta que la linea mas larga entre en `ancho` (en px).

    Las guirnaldas del interior dejan una columna limpia de solo 30 mm, y ahi
    cualquier titulo se sale sin avisar.
    """
    while pt > 4:
        fu = f(nombre, pt)
        largo = max(d.textlength(espaciado * " ".join(l) if espaciado else l, font=fu)
                    for l in texto.split("\n") if l.strip())
        if largo <= ancho:
            return fu
        pt -= 0.25
    return f(nombre, pt)


def centrado(d, y, texto, fuente, x0, ancho, color=VERDE, interlinea=1.25,
             espaciado=0):
    for linea in texto.split("\n"):
        if not linea.strip():
            y += fuente.size * interlinea * 0.5
            continue
        if espaciado:
            linea = espaciado * " ".join(linea)
        w = d.textlength(linea, font=fuente)
        d.text((x0 + (ancho - w) / 2, y), linea, font=fuente, fill=color)
        y += fuente.size * interlinea
    return y


def sello(d, cx, cy):
    """El «100% NATURAL» va DENTRO de la corona de laurel que dibujo GPT Image."""
    fu = f("Montserrat-Black.ttf", 5.8)
    for i, t in enumerate(("100%", "NATURAL")):
        w = d.textlength(t, font=fu)
        d.text((cx * MM - w / 2, cy * MM - fu.size * 1.05 + i * fu.size * 1.2), t,
               font=fu, fill=VERDE)


def portada(d):
    """Panel derecho de la cara exterior. Zona limpia: 27 a 70 mm."""
    x0, an, m = MEDIA, MEDIA, int(9 * MM)
    y = int(28 * MM)
    y = centrado(d, y, "COMIENZA A CUIDARTE\nA PARTIR DE LOS 30",
                 f("Montserrat-Black.ttf", 8), x0 + m, an - 2 * m, interlinea=1.5)
    y += int(6 * MM)
    centrado(d, y, "RAR~AMORE", f("CormorantGaramond-Bold.ttf", 15), x0, an,
             espaciado=1)
    y += int(10 * MM)
    d.line([(x0 + an // 2 - int(9 * MM), y), (x0 + an // 2 + int(9 * MM), y)],
           fill=VERDE, width=int(0.3 * MM))
    y += int(2.5 * MM)
    y = centrado(d, y, "C Á P S U L A S", f("Montserrat-Medium.ttf", 7),
                 x0 + m, an - 2 * m, color=VERDE_CLARO)
    y += int(3 * MM)
    centrado(d, y, "Vive sin dolores.\nVive sin estrés.\nVive sin insomnio.",
             f("CormorantGaramond-Bold.ttf", 10), x0 + m, an - 2 * m, interlinea=1.45)
    sello(d, 74.9, 84.0)


def contraportada(d):
    """Panel izquierdo de la cara exterior. Zona limpia: 26 a 78 mm."""
    x0, an, m = 0, MEDIA, int(9 * MM)
    y = int(28 * MM)
    y = centrado(d, y, "PRECIO DE PROMOCIÓN", f("Montserrat-Black.ttf", 7.5),
                 x0 + m, an - 2 * m, color=VERDE_CLARO)
    y += int(4 * MM)
    y = centrado(d, y, "Paquete\nBálsamo + Cápsulas",
                 f("CormorantGaramond-Bold.ttf", 11), x0 + m, an - 2 * m, interlinea=1.4)
    y += int(3 * MM)
    y = centrado(d, y, "$1,399", f("Montserrat-Black.ttf", 17), x0, an)
    y += int(2 * MM)
    centrado(d, y, "Precio normal $1,600", f("Montserrat-Medium.ttf", 7),
             x0 + m, an - 2 * m, color=VERDE_CLARO)
    y = int(64 * MM)
    y = centrado(d, y, "PEDIDOS WHATSAPP", f("Montserrat-Medium.ttf", 7),
                 x0 + m, an - 2 * m, color=VERDE_CLARO)
    y += int(1.5 * MM)
    centrado(d, y, "818 466 84 56", f("Montserrat-Black.ttf", 9), x0, an)


# La lista que mando Angel por WhatsApp el 3 sep 15:32, con su correccion de
# las 15:42: «que diga Extracto en lugar de cáscara» y «(Resveratrol)».
# Salieron VITAMINA D y CÁSCARA DE TORONJA porque su lista ya no las trae —
# si las quiere de vuelta, se vuelven a meter aqui y ya.
INGREDIENTES = ("Piel de camarón", "Boswelia serrata", "Calcio", "Magnesio",
                "Extracto de naranja", "Extracto de limón",
                "Extracto de semilla\nde uva (Resveratrol)")
CADUCIDAD = "CADUCIDAD:  DIC 2028"


def contenido(d):
    """Panel izquierdo del interior. La guirnalda deja limpio de 10 a 40 mm.

    Angel pidio el 3 sep que las letras CHICAS crezcan («casi no se pueden dar
    lectura»), asi que la lista ya no se dibuja con un cuerpo fijo: se le da el
    hueco entre el titulo y el pie, y toma el cuerpo MAS GRANDE que entre a lo
    ancho y a lo alto. Cabe mas grande que antes porque su lista nueva son 7
    ingredientes, no 8.
    """
    x0, an, m = 0, MEDIA, int(10.8 * MM)   # la guirnalda: menos margen y la roza
    y = int(21 * MM)
    y = centrado(d, y, "CÁPSULAS",
                 cabe(d, "CÁPSULAS", "CormorantGaramond-Bold.ttf", 13,
                      an - 2 * m, espaciado=1), x0, an, espaciado=1)
    y += int(4.5 * MM)
    y = centrado(d, y, "INGREDIENTES", f("Montserrat-Black.ttf", 7),
                 x0 + m, an - 2 * m, color=VERDE_CLARO)
    y += int(3.5 * MM)

    renglones = [l for ing in INGREDIENTES for l in ing.split("\n")]
    pie = int(77 * MM)                      # abajo empieza el CONTENIDO
    pt = 9.5
    while pt > 4:
        fu = f("Montserrat-Medium.ttf", pt)
        ancho_ok = max(d.textlength(l, font=fu) for l in renglones) <= an - 2 * m
        if ancho_ok and y + fu.size * 1.5 * len(renglones) <= pie:
            break
        pt -= 0.25
    for l in renglones:
        w = d.textlength(l, font=fu)
        d.text((x0 + (an - w) / 2, y), l, font=fu, fill=VERDE)
        y += fu.size * 1.5

    y = pie + int(2 * MM)
    y = centrado(d, y, "CONTENIDO:  30 CÁPSULAS", f("Montserrat-Medium.ttf", 6.5),
                 x0 + m, an - 2 * m, color=VERDE_CLARO)
    y += int(1.2 * MM)
    centrado(d, y, CADUCIDAD, f("Montserrat-Medium.ttf", 6.5),
             x0 + m, an - 2 * m, color=VERDE_CLARO)


def promesa(d):
    """Panel derecho del interior."""
    x0, an, m = MEDIA, MEDIA, int(10.5 * MM)
    y = int(26 * MM)
    y = centrado(d, y, "A partir de los 30\ncuídate con",
                 f("CormorantGaramond-Bold.ttf", 11), x0 + m, an - 2 * m, interlinea=1.5)
    y += int(4 * MM)
    centrado(d, y, "RAR~AMORE",
             cabe(d, "RAR~AMORE", "CormorantGaramond-Bold.ttf", 13,
                  an - 2 * m, espaciado=1), x0, an, espaciado=1)
    y += int(11 * MM)
    d.line([(x0 + an // 2 - int(8 * MM), y), (x0 + an // 2 + int(8 * MM), y)],
           fill=VERDE, width=int(0.3 * MM))
    y += int(6 * MM)
    bien = "BIENESTAR PARA TUS\nMÚSCULOS Y\nARTICULACIONES"
    y = centrado(d, y, bien,
                 cabe(d, bien, "Montserrat-Black.ttf", 7.5, an - 2 * m),
                 x0 + m, an - 2 * m, interlinea=1.55)
    y = int(72 * MM)
    y = centrado(d, y, "PEDIDOS WHATSAPP", f("Montserrat-Medium.ttf", 7),
                 x0 + m, an - 2 * m, color=VERDE_CLARO)
    y += int(1.5 * MM)
    centrado(d, y, "818 466 84 56", f("Montserrat-Black.ttf", 8.5), x0, an)


def cara(nombre, partes):
    ruta = os.path.join(FONDOS, "%s.png" % nombre)
    if os.path.exists(ruta):
        im = Image.open(ruta).convert("RGB").resize((HOJA, HOJA), Image.LANCZOS)
    else:
        print("  sin fondo de GPT Image para %s — sale en blanco" % nombre)
        im = Image.new("RGB", (HOJA, HOJA), "white")
    d = ImageDraw.Draw(im)
    for parte in partes:
        parte(d)
    return im


# ---------------------------------------------------------------- hoja carta
CARTA_W, CARTA_H = int(215.9 * MM), int(279.4 * MM)


def imposicion(exterior, interior):
    """4 libritos por hoja carta, con marcas de corte.

    La hoja plana mide 100 x 100 mm, asi que en carta (215.9 x 279.4) entran
    dos columnas y dos filas: CUATRO. No caben mas.

    La segunda hoja lleva las COLUMNAS INVERTIDAS a proposito: al imprimir a
    doble cara volteando por el lado largo, el papel gira sobre su eje
    vertical, asi que lo que va a la izquierda en la cara 2 cae detras de lo
    que esta a la derecha en la cara 1.
    """
    mx, my = (CARTA_W - 2 * HOJA) // 2, (CARTA_H - 2 * HOJA) // 2
    hojas = []
    for cara, invertir in ((exterior, False), (interior, True)):
        pl = Image.new("RGB", (CARTA_W, CARTA_H), "white")
        d = ImageDraw.Draw(pl)
        for fila in range(2):
            for col in range(2):
                destino = (1 - col) if invertir else col
                pl.paste(cara, (mx + destino * HOJA, my + fila * HOJA))
        # marcas de corte: rayitas fuera del area impresa, en las cuatro esquinas
        largo, fino = int(4 * MM), int(0.25 * MM)
        for i in range(3):
            x, y = mx + i * HOJA, my + i * HOJA
            d.line([(x, my - largo), (x, my - int(1 * MM))], fill="black", width=fino)
            d.line([(x, my + 2 * HOJA + int(1 * MM)), (x, my + 2 * HOJA + largo)],
                   fill="black", width=fino)
            d.line([(mx - largo, y), (mx - int(1 * MM), y)], fill="black", width=fino)
            d.line([(mx + 2 * HOJA + int(1 * MM), y), (mx + 2 * HOJA + largo, y)],
                   fill="black", width=fino)
        hojas.append(pl)
    return hojas


if __name__ == "__main__":
    paso = sys.argv[1] if len(sys.argv) > 1 else "todo"
    if paso in ("fondos", "todo"):
        for c in CARAS:
            print(c)
            fondo(c)
    if paso in ("arma", "todo"):
        ext = cara("exterior", [contraportada, portada])
        inte = cara("interior", [contenido, promesa])
        pdf = os.path.join(AQUI, "RarAmore_librito_KUIRABA_10x10.pdf")
        ext.save(pdf, save_all=True, append_images=[inte], resolution=DPI,
                 title="Rar~Amore etiqueta librito")
        ext.save(os.path.join(AQUI, "RarAmore_KUIRABA_1_exterior.png"), dpi=(DPI, DPI))
        inte.save(os.path.join(AQUI, "RarAmore_KUIRABA_2_interior.png"), dpi=(DPI, DPI))
        print("listo:", pdf)

        h1, h2 = imposicion(ext, inte)
        carta = os.path.join(AQUI, "RarAmore_librito_CARTA_4up.pdf")
        h1.save(carta, save_all=True, append_images=[h2], resolution=DPI,
                title="Rar~Amore · 4 libritos por hoja carta")
        h1.save(os.path.join(AQUI, "RarAmore_CARTA_1_exterior.png"), dpi=(DPI, DPI))
        h2.save(os.path.join(AQUI, "RarAmore_CARTA_2_interior.png"), dpi=(DPI, DPI))
        print("listo:", carta, "· 4 libritos por hoja")
