#!/usr/bin/env python3
"""Cartel tamano carta de Rar~Amore, para publicidad y para enmicar.

    python3 cartel_carta.py fondo    # el ornamento, en GPT Image (~$0.025)
    python3 cartel_carta.py arma     # el texto encima y el PDF
    python3 cartel_carta.py          # las dos

Lo pidio Angel el 1 y el 2 de sep: «tamaño carta para enmicarla», con el
encabezado BIENESTAR TUS MUSCULOS Y ARTICULACIONES, y luego «una sola etiqueta,
tamaño carta, para publicidad».

Mismo estilo que el librito: grabado botanico de la Kuira Ba invertido a blanco
con verde bosque. Aqui el formato es 3:4 en vez de cuadrado, asi que el
ornamento se pide aparte — no sirve recortar el del librito.
"""
import base64, json, os, sys, time, urllib.request
from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
FUENTES = os.path.join(RAIZ, "fonts")
FONDO = os.path.join(AQUI, "librito_fondos", "cartel.png")
REF = os.path.join(AQUI, "etiquetas", "KUIRABA_verde_v1.png")
WAVESPEED = "https://api.wavespeed.ai/api/v3"

DPI = 300
MM = DPI / 25.4
W, H = int(215.9 * MM), int(279.4 * MM)
VERDE = (11, 58, 39)         # tinta subida: Angel la queria mas marcada
VERDE_CLARO = (31, 92, 63)

PROMPT = (
    "Design the ornamental artwork for a large apothecary poster, in EXACTLY the "
    "engraving style of the reference image: fine antique botanical line-engraving "
    "of medicinal leaves, sprigs and berries, hairline double rule borders, the "
    "look of an old herbal pharmacy label. "
    "INVERT the colour scheme of the reference: the background is PURE WHITE, "
    "clean and empty, and every line, leaf and rule is DEEP FOREST GREEN. No dark "
    "background anywhere, no gold, no cream, no beige, no paper texture — flat "
    "white paper with green ink only. "
    "Layout: a hairline double-rule green frame inset from the edges of the whole "
    "sheet. A wide, generous crown of engraved leaves and berries spreading across "
    "the TOP inside the frame. A narrower mirrored spray of leaves at the very "
    "BOTTOM. Slim vertical sprigs of leaves hugging the inside of the left and "
    "right frame lines, no wider than a finger, so they never crowd the middle. "
    "The whole CENTRE of the sheet — the big middle area — stays COMPLETELY EMPTY "
    "WHITE: that is where the type will be set later. "
    "ABSOLUTELY NO TEXT: no letters, no words, no numbers, no signatures, no "
    "logos, no watermark anywhere. Ornament only. "
    "Flat vector-clean print artwork, portrait 3:4, no perspective, no mockup, no "
    "bottle, no hands, no shadows."
)


def env(n):
    for l in open(os.path.join(RAIZ, ".env"), encoding="utf8", errors="replace"):
        if l.startswith(n + "="):
            return l.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get(n, "")


CAB = {"Authorization": "Bearer " + env("WAVESPEED_API_KEY"),
       "Content-Type": "application/json"}


def uri(r):
    t = "png" if r.lower().endswith(".png") else "jpeg"
    return "data:image/%s;base64,%s" % (t, base64.b64encode(open(r, "rb").read()).decode())


def pide(ruta, cuerpo):
    rq = urllib.request.Request(WAVESPEED + "/" + ruta,
                                data=json.dumps(cuerpo).encode(), headers=CAB)
    with urllib.request.urlopen(rq, timeout=300) as r:
        return json.loads(r.read())


def fondo():
    os.makedirs(os.path.dirname(FONDO), exist_ok=True)
    if os.path.exists(FONDO):
        print("  ya existe el fondo — borralo si quieres rehacerlo"); return
    d = pide("openai/gpt-image-2/edit", {"prompt": PROMPT, "images": [uri(REF)],
                                         "aspect_ratio": "3:4", "output_format": "png"})
    id_ = d["data"]["id"]
    for _ in range(300):
        time.sleep(3)
        rq = urllib.request.Request("%s/predictions/%s/result" % (WAVESPEED, id_), headers=CAB)
        dd = (json.loads(urllib.request.urlopen(rq, timeout=60).read()) or {}).get("data") or {}
        if dd.get("status") == "completed":
            with urllib.request.urlopen(dd["outputs"][0], timeout=300) as f:
                open(FONDO, "wb").write(f.read())
            print("  listo", FONDO); return
        if dd.get("status") == "failed":
            raise SystemExit("fallo: %s" % dd.get("error"))


# ---------------------------------------------------------------- tipografia
def f(nombre, pt):
    return ImageFont.truetype(os.path.join(FUENTES, nombre), int(pt * MM / 2.845))


def centro(d, y, texto, fu, color=VERDE, interlinea=1.3, espaciado=0, x0=0, an=W):
    for l in texto.split("\n"):
        if not l.strip():
            y += fu.size * interlinea * 0.5; continue
        t = espaciado * " ".join(l) if espaciado else l
        w = d.textlength(t, font=fu)
        d.text((x0 + (an - w) / 2, y), t, font=fu, fill=color)
        y += fu.size * interlinea
    return y


def sello(d, cx, cy, r):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=VERDE, width=int(0.7 * MM))
    r2 = r - int(2 * MM)
    d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], outline=VERDE, width=int(0.25 * MM))
    fu = f("Montserrat-Black.ttf", 8)
    for i, t in enumerate(("100%", "NATURAL")):
        w = d.textlength(t, font=fu)
        d.text((cx - w / 2, cy - fu.size * 1.1 + i * fu.size * 1.25), t, font=fu, fill=VERDE)


def cabe(d, texto, nombre, pt, ancho, espaciado=0):
    """Achica el cuerpo hasta que la linea mas larga entre en `ancho`."""
    while pt > 5:
        fu = f(nombre, pt)
        largo = max(d.textlength(espaciado * " ".join(l) if espaciado else l, font=fu)
                    for l in texto.split("\n") if l.strip())
        if largo <= ancho:
            return fu
        pt -= 0.5
    return f(nombre, pt)


# La reticula, en milimetros. La corona del ornamento termina en 50 y la rama de
# abajo empieza en 248, asi que todo el texto vive entre esas dos.
def arma():
    if os.path.exists(FONDO):
        im = Image.open(FONDO).convert("RGB").resize((W, H), Image.LANCZOS)
    else:
        print("  sin fondo — sale en blanco"); im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    m = int(20 * MM)
    util = W - 2 * m

    tit = "BIENESTAR PARA TUS\nMÚSCULOS Y ARTICULACIONES"
    centro(d, int(58 * MM), tit, cabe(d, tit, "Montserrat-Black.ttf", 15, util),
           interlinea=1.45, x0=m, an=util)

    centro(d, int(78 * MM), "RAR~AMORE",
           cabe(d, "RAR~AMORE", "CormorantGaramond-Bold.ttf", 46, util, espaciado=1),
           espaciado=1)

    y = int(99 * MM)
    d.line([(W // 2 - int(26 * MM), y), (W // 2 + int(26 * MM), y)],
           fill=VERDE, width=6)
    centro(d, int(100 * MM), "B Á L S A M O   ·   C Á P S U L A S",
           f("Montserrat-Medium.ttf", 13), color=VERDE_CLARO)

    centro(d, int(110 * MM), "Vive sin dolores.\nVive sin estrés.\nVive sin insomnio.",
           f("CormorantGaramond-Bold.ttf", 24), interlinea=1.45, x0=m, an=util)

    centro(d, int(150 * MM), "COMIENZA A CUIDARTE A PARTIR DE LOS 30",
           f("Montserrat-Medium.ttf", 12), color=VERDE_CLARO, x0=m, an=util)

    centro(d, int(160 * MM), "LAS CÁPSULAS CONTIENEN",
           f("Montserrat-Black.ttf", 11.5), color=VERDE_CLARO, x0=m, an=util)

    # dos columnas, y el sello en el hueco que queda al centro
    # La lista de Angel del 3 sep, con sus tres correcciones: «Extracto» en vez
    # de «cascara», «(Resveratrol)» y la Vitamina D enseguida del Calcio.
    # Angel mando la lista TAL CUAL la quiere para el cartel del mostrador
    # (3 sep 22:47), con las dos correcciones que el mismo pidio antes:
    # «Extracto» en vez de «cascara» (15:42) y Vitamina D tras el Calcio (20:42).
    # En un cartel de mostrador se lee de pie y de lejos: van en UNA columna
    # centrada y grande, no en dos columnas chicas.
    TODOS = ("Piel de camarón", "Boswelia serrata", "Calcio", "Vitamina D",
             "Magnesio", "Extracto de naranja", "Extracto de limón",
             "Extracto de semilla de uva", "(Resveratrol)")
    # DOS COLUMNAS, no una. Angel (4 sep 01:35) pidio las letras mas grandes
    # porque «se ve desde el aparador de afuera» y «las personas mayores son
    # las que compran y las que mas batallan para leer». En una sola columna,
    # nueve renglones obligaban a bajar el cuerpo a 7 pt — que es justo lo
    # contrario de lo que pidio. En dos columnas caben a mas del doble.
    IZQ = TODOS[:5]
    DER = TODOS[5:]
    ancho_col = (util - int(14 * MM)) / 2
    pt = 18.0
    while pt > 8:
        fu = f("Montserrat-Medium.ttf", pt)
        if (max(d.textlength(t, font=fu) for t in TODOS) <= ancho_col
                and fu.size * 1.34 * 5 <= int(30 * MM)):
            break
        pt -= 0.25
    fu = f("Montserrat-Medium.ttf", pt)
    y0 = int(163 * MM)
    for cx, lista in ((m + int(7 * MM) + ancho_col / 2, IZQ),
                      (W - m - int(7 * MM) - ancho_col / 2, DER)):
        yy = y0
        for t in lista:
            d.text((cx - d.textlength(t, font=fu) / 2, yy), t, font=fu, fill=VERDE)
            yy += fu.size * 1.34
    yy = y0 + fu.size * 1.34 * 5 + int(2 * MM)
    fc = f("Montserrat-Medium.ttf", 11.5)
    tc = "CONTENIDO:  30 CÁPSULAS"
    d.text(((W - d.textlength(tc, font=fc)) / 2, yy), tc, font=fc, fill=VERDE_CLARO)

    caja = int(206 * MM)
    d.rectangle([m + int(6 * MM), caja, W - m - int(6 * MM), caja + int(34 * MM)],
                outline=VERDE, width=4)
    centro(d, caja + int(5 * MM), "PRECIO DE PROMOCIÓN",
           f("Montserrat-Black.ttf", 12), color=VERDE_CLARO, x0=m, an=util)
    centro(d, caja + int(12 * MM), "Paquete Bálsamo + Cápsulas",
           f("CormorantGaramond-Bold.ttf", 20), x0=m, an=util)
    fu2, fu3 = f("Montserrat-Black.ttf", 30), f("Montserrat-Medium.ttf", 12)
    a, b = "$1,895", "   Precio normal $2,359"
    x = (W - d.textlength(a, font=fu2) - d.textlength(b, font=fu3)) / 2
    yv = caja + int(22 * MM)
    d.text((x, yv), a, font=fu2, fill=VERDE)
    d.text((x + d.textlength(a, font=fu2), yv + fu2.size * 0.55), b, font=fu3,
           fill=VERDE_CLARO)

    centro(d, int(244 * MM), "PEDIDOS POR WHATSAPP",
           f("Montserrat-Medium.ttf", 12), color=VERDE_CLARO, x0=m, an=util)
    centro(d, int(249 * MM), "818 466 84 56", f("Montserrat-Black.ttf", 24))
    return im


if __name__ == "__main__":
    paso = sys.argv[1] if len(sys.argv) > 1 else "todo"
    if paso in ("fondo", "todo"):
        fondo()
    if paso in ("arma", "todo"):
        im = arma()
        pdf = os.path.join(AQUI, "RarAmore_CARTEL_carta.pdf")
        im.save(pdf, resolution=DPI, title="Rar~Amore · cartel carta")
        im.save(os.path.join(AQUI, "RarAmore_CARTEL_carta.png"), dpi=(DPI, DPI))
        print("listo:", pdf)
