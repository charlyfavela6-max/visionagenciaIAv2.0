#!/usr/bin/env python3
"""Una imagen fotorrealista POR CUARTO, con Nano Banana Pro.

    python3 cuartos_nanobanana.py                 # todos los que falten
    python3 cuartos_nanobanana.py pb_sala pa_cocina

COMO FUNCIONA, y por que asi
----------------------------
A cada cuarto se le mandan, en una sola llamada:

  1. `<cuarto>_gris.png`    — el cuadro de Blender con la camara DENTRO del
                              cuarto (`cuartos_camara.py`, cuadro 1021)
  2. `<cuarto>_aristas.png` — el mismo encuadre en lineas. Es lo que amarra:
                              el gris solo no basta, la IA se despega e inventa
                              muros
  3-6. las escenas REALES de ese cuarto

y se le pide dibujar el 1 con los materiales de las otras. Es el mismo camino
de `cuartos_gpt.py`, pero con `google/nano-banana-pro/edit-multi` en vez de GPT
Image: aguanta mas referencias y respeta mucho mejor la geometria — se vio en
`casa_nanobanana_v1.png`, donde por primera vez no se invento la planta.

**Maximo 8 imagenes.** El schema dice 14, pero con 14 el proveedor rechaza la
peticion aunque vayan reducidas. Probado: 3 pasa, 8 pasa, 14 no.

LAS REFERENCIAS SON DEL VIDEO DEL 3 SEP, que trajo cuartos que no teniamos:
el vestidor de repisas abiertas, la escalera de madera con barandal negro, la
recamara principal con cabecera capitonada sobre muro CHOCOLATE, la cocina de
isla de madera con cubierta blanca, el sofa ROJO VINO del comedor y la azotea
con jardineras de concreto y matas de verdad.

$0.07 por cuarto, y devuelve dos imagenes de cada uno.
"""
import base64, io, json, os, sys, time, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = "/workspaces/visionagenciaIAv2.0/VisionagenciaIAv2.0-main"
CUADROS = os.path.join(AQUI, "cuartos_cam")
VID = os.path.join(RAIZ, "clientes/Mariano/de_whatsapp/video_3sep/frames")
VID2 = os.path.join(RAIZ, "clientes/Mariano/de_whatsapp/video_3sep/frames2")
FOTOS = os.path.join(AQUI, "fotos_reales")
SALIDA = os.path.join(AQUI, "cuartos_nb")
WAVESPEED = "https://api.wavespeed.ai/api/v3"
MODELO = "google/nano-banana-pro/edit-multi"

v = lambda n: os.path.join(VID, n)
g = lambda n: os.path.join(VID2, n)
p = lambda n: os.path.join(FOTOS, n)

# cuarto -> (referencias reales, que es el cuarto y con que esta acabado)
CUARTOS = {
    "n1_recamara2": ([g("g13.jpg"), v("f07.jpg"), g("g05.jpg")],
        "a secondary bedroom on the lower floor: upholstered headboard, cream "
        "bedding with a chocolate brown throw folded across the foot, a DARK "
        "GREEN rug under the bed, a rounded cream armchair, and a "
        "floor-to-ceiling black-framed sliding window with sheer white curtains"),
    "n1_recamara1": ([g("g13.jpg"), v("f07.jpg")],
        "the other secondary bedroom, same language: upholstered headboard, "
        "cream bedding with a chocolate throw, dark green rug, sheer curtains"),
    "n1_bano": ([p("bano_4_21.jpg"), p("bano_2_10.jpg")],
        "the lower bathroom: WOOD-LOOK tile on the shower wall with a dark "
        "brown horizontal band, a floating wood vanity with a white basin, a "
        "large mirror and a WC"),
    "n1_bodega": ([g("g07.jpg")],
        "the storeroom: plain white walls, beige floor tile and open pale-oak "
        "shelving along one wall"),
    "n1_estudio": ([g("g19.jpg"), v("f09.jpg")],
        "the study: a desk with a monitor and a lamp, a pale-oak grid bookcase "
        "with books, a rug and a big leafy plant"),
    "n1_lavado": ([v("f06.jpg")],
        "the laundry: a plain white room with the water outlets and the tap on "
        "the wall, beige floor tile, a washer and dryer side by side"),
    "pb_sala": ([v("f01.jpg"), v("f09.jpg"), g("g19.jpg")],
        "the ground-floor living room: a curved CREAM boucle sofa with a camel "
        "cushion, a CAMEL LEATHER armchair, a round TRAVERTINE coffee table on "
        "a pale rug, a large abstract canvas in beige and black, and a feature "
        "wall of vertical WOOD SLATS with the TV and a pale-oak grid shelf"),
    "pb_mediobano": ([p("mediobano_1_06.jpg"), p("bano_4_21.jpg")],
        "the guest half-bath: just a floating wood vanity with a white basin, "
        "a mirror and a WC, wood-look tile band"),
    "pb_recamara_ppal": ([g("g15.jpg"), v("f07.jpg")],
        "the master bedroom: an ARCHED TUFTED headboard against a CHOCOLATE "
        "BROWN feature wall, a woven rattan pendant lamp hanging beside the "
        "bed, cream quilted bedding, sheer white curtains over a "
        "floor-to-ceiling black-framed window"),
    "pb_escalera": ([g("g11.jpg"), g("g17.jpg"), v("f05.jpg")],
        "the staircase: pale wood treads, white walls and a very thin BLACK "
        "metal railing with horizontal bars"),
    "pb_vestidor": ([g("g07.jpg")],
        "the walk-in closet: open PALE OAK shelves in several tiers with a "
        "drawer unit, no doors"),
    "pb_bano_ppal": ([p("bano_4_21.jpg"), p("bano_3_14.jpg")],
        "the master bathroom: wood-look tile with a dark brown band in the "
        "shower, floating wood vanity, white basin, large mirror"),
    "pa_cocina": ([g("g21.jpg"), p("cocina_1_30.jpg")],
        "the kitchen: a WOOD-FRONTED ISLAND with a thick WHITE top, plain "
        "white upper cabinets, open floating shelves, a window over the "
        "counter and a black cooktop"),
    "pa_sala": ([v("f10.jpg"), p("sala_5_28.jpg")],
        "the upper living area: a WINE-RED / deep burgundy sofa with pale "
        "cushions, big beige floor tiles and a black-framed window"),
    "pa_comedor": ([v("f10.jpg"), v("f02.jpg")],
        "the dining area: a round pale-wood table with cream chairs, a thin "
        "brass ring pendant lamp above it, and framed abstract art on the wall"),
    "rg_terraza": ([g("g23.jpg"), v("f11.jpg")],
        "the roof terrace: pale floor tile, a low white parapet, LONG "
        "RECTANGULAR CONCRETE PLANTERS with real leafy green plants along the "
        "parapet, a white outdoor lounge chair and a low white table, plus a "
        "teak bench, and the dry hills on the horizon"),
}

PROMPT = (
    "Make ONE photorealistic interior photograph of {que}.\n\n"

    "IMAGE 1 is the grey 3D render of this exact room and IMAGE 2 is its line "
    "drawing. TOGETHER THEY ARE THE LAW:\n"
    "  · Keep the CAMERA exactly — same angle, same height, same lens. Do not "
    "re-frame, do not re-centre, do not zoom.\n"
    "  · Keep every wall, every window and every doorway exactly where the "
    "line drawing puts them. Do not add or remove a wall or an opening.\n"
    "  · Keep every piece of furniture in its exact position and at its exact "
    "size. You are PAINTING what is already modelled, not redecorating.\n"
    "  · A shape that reads as a plain grey box in image 1 is a real piece of "
    "furniture — paint it as one, never leave it as a box.\n\n"

    "The remaining images are photographs of the REAL house. Take from them "
    "the materials, the colours and the light, and nothing else.\n\n"

    "Finishes everywhere in this house: big BEIGE floor tiles, smooth white "
    "plaster walls (flat plaster and concrete, never rough limestone or "
    "textured stucco), black-framed windows, warm daylight coming in from "
    "outside.\n\n"

    "Fill the whole frame — no unfinished corner, no white blocky model. "
    "No text, no watermark, no people."
)


def env(n):
    for l in open(os.path.join(RAIZ, ".env"), encoding="utf8", errors="replace"):
        if l.startswith(n + "="):
            return l.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get(n, "")


CAB = {"Authorization": "Bearer " + env("WAVESPEED_API_KEY"),
       "Content-Type": "application/json"}


def uri(ruta):
    """Reducida a 1024 px: con las referencias en tamano original el proveedor
    rechaza la peticion, y para material no hace falta mas."""
    from PIL import Image
    im = Image.open(ruta).convert("RGB")
    im.thumbnail((1024, 1024), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, "JPEG", quality=88)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


def pide(m, cuerpo):
    req = urllib.request.Request(WAVESPEED + "/" + m,
                                 data=json.dumps(cuerpo).encode(), headers=CAB)
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())


def espera(id_):
    for _ in range(300):
        time.sleep(3)
        req = urllib.request.Request("%s/predictions/%s/result" % (WAVESPEED, id_),
                                     headers=CAB)
        d = (json.loads(urllib.request.urlopen(req, timeout=60).read()) or {}).get("data") or {}
        if d.get("status") == "completed":
            return d["outputs"]
        if d.get("status") == "failed":
            raise RuntimeError(d.get("error"))
    raise RuntimeError("se acabo la espera")


def haz(cuarto):
    refs, que = CUARTOS[cuarto]
    gris = os.path.join(CUADROS, cuarto + "_gris.png")
    aristas = os.path.join(CUADROS, cuarto + "_aristas.png")
    if not (os.path.exists(gris) and os.path.exists(aristas)):
        print("  %-18s sin cuadros de Blender todavia" % cuarto, flush=True)
        return False
    imgs = [gris, aristas] + [r for r in refs if os.path.exists(r)]
    imgs = imgs[:8]
    d = pide(MODELO, {"prompt": PROMPT.format(que=que),
                      "images": [uri(i) for i in imgs],
                      "aspect_ratio": "2:3",
                      "output_format": "png"})
    urls = espera(d["data"]["id"])
    os.makedirs(SALIDA, exist_ok=True)
    for i, u in enumerate(urls, 1):
        destino = os.path.join(SALIDA, "%s_v%d.png" % (cuarto, i))
        with urllib.request.urlopen(u, timeout=300) as r:
            open(destino, "wb").write(r.read())
    print("  %-18s listo (%d refs)" % (cuarto, len(imgs)), flush=True)
    return True


if __name__ == "__main__":
    quiere = sys.argv[1:] or list(CUARTOS)
    for c in quiere:
        if c not in CUARTOS:
            print("  cuarto desconocido:", c)
            continue
        if os.path.exists(os.path.join(SALIDA, c + "_v1.png")):
            print("  %-18s ya estaba" % c)
            continue
        try:
            haz(c)
        except Exception as e:
            print("  %-18s FALLO: %s" % (c, str(e)[:120]), flush=True)
