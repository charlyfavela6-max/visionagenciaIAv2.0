#!/usr/bin/env python3
"""La casa entera en corte, con Nano Banana Pro y las 14 referencias.

    python3 casa_nanobanana.py [salida.png]

POR QUE ESTE MODELO Y NO SEEDREAM
---------------------------------
`casa_seedream_v2.png` salio preciosa y ERA OTRA CASA: patio central que no
existe, el programa movido, tres camas donde no van. Un solo *edit* sobre el
render gris no amarra nada — el modelo lo toma de inspiracion y redibuja.

`google/nano-banana-pro/edit-multi` (Gemini 3 Pro Image) acepta **14 imagenes**
de referencia en una sola llamada, contra las pocas de Seedream, y sigue mejor
las instrucciones. Aqui se le dan:

  1. el pase GRIS del corte  — el volumen
  2. el pase de LINEAS       — la estructura, que es la ley
  3-14. las escenas reales   — los acabados

Los dos primeros salen del Blender DE CARLOS, con su encuadre, por el conector:
el cuadro 1021 (los muebles ya brotados), la piel poniente escondida y la casa
vecina borrada.

LAS ESCENAS SON DEL VIDEO NUEVO del 3 sep 21:32, que corrige dos cosas que
teniamos mal:
  · el ROOF GARDEN **si tiene jardinera con plantas** — no esta pelado, y las
    `rg_jardinera_*` del modelo no eran placeholder;
  · en la zona de comedor/cocina hay un **sofa ROJO VINO**, que no estaba en
    ninguna referencia anterior.

Cuesta $0.07 y devuelve DOS imagenes.
"""
import base64, json, os, sys, time, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = "/workspaces/visionagenciaIAv2.0/VisionagenciaIAv2.0-main"
CORTE = os.path.join(AQUI, "corte")
VIDEO = os.path.join(RAIZ, "clientes/Mariano/de_whatsapp/video_3sep/frames")
FOTOS = os.path.join(AQUI, "fotos_reales")
WAVESPEED = "https://api.wavespeed.ai/api/v3"
MODELO = "google/nano-banana-pro/edit-multi"

# (ruta, que aporta esa imagen). El ORDEN importa: el prompt las nombra.
# OCHO como maximo: con 14 el proveedor rechaza la peticion.
#
# Estas seis son las tomas del video del 3 sep que Carlos senalo como las que
# hay que respetar — sala de abajo, sala de arriba con la TV, comedor, cocineta,
# bano y terraza.
V3 = os.path.join(RAIZ, "clientes/Mariano/de_whatsapp/video_3sep")
REFS = [
    (os.path.join(CORTE, "corte_gris.png"), "grey 3D cutaway — the volume"),
    (os.path.join(CORTE, "corte_aristas.png"), "line drawing — the structure"),
]
# TRES imagenes, no ocho. Con las fotos de interior puestas, el modelo se metia
# DENTRO de la casa: probado tres veces (casa_v3, v4, v5) — la v5 acabo siendo
# una foto de la terraza. Las fotos de interior le ganan al encuadre. Los
# acabados van descritos con palabras, que para material alcanza, y las tres
# imagenes que quedan son las que mandan la geometria.

# Cinco intentos (v3 a v7) acabaron todos ACERCANDOSE a un piso, aunque el
# prompt pidiera lo contrario y aunque se le diera una imagen de encuadre. Lo
# que si funciona es cambiarle el SUJETO: en vez de «una casa en corte» —que le
# suena a fotografia de arquitectura y se mete dentro— se le pide el
# PORTAFOLIO de un MODELO A ESCALA sobre una mesa. Un objeto se fotografia
# entero; un interior, no.
# El encuadre se resolvio pidiendo un MODELO A ESCALA sobre una mesa: cinco
# intentos como «casa en corte» acabaron todos metidos dentro de un piso. Un
# objeto se fotografia entero; un interior, no. Las maquetas de arquitectura
# llevan figuritas, asi que las personas y el perrito que pidio Angel caben sin
# romper el truco.
PROMPT = (
    "A studio product photograph of a highly detailed ARCHITECTURAL SCALE "
    "MODEL of a three-storey house, standing on a plain table, photographed "
    "from a few metres away so THE WHOLE MODEL IS INSIDE THE FRAME with empty "
    "space around it. One single object seen complete — not an interior "
    "photograph, not a close-up of one floor.\n\n"

    "The model is a cutaway: its near side wall is removed, so all three floors "
    "are open and every room is visible at once, each fully furnished and "
    "finished in photorealistic materials.\n\n"

    "IMAGE 1 is the grey render of this model and IMAGE 2 its line drawing. "
    "TOGETHER THEY ARE THE LAW. Reproduce image 1 at EXACTLY the same size and "
    "position in the frame. Keep every floor slab, wall, opening and piece of "
    "furniture where the drawings put them. Do not add or remove a wall, do "
    "not invent a courtyard, do not rearrange furniture.\n\n"

    "THREE floors. The roof terrace is NOT a fourth floor: it is the open part "
    "of the top floor, on the same slab as the kitchen and dining.\n\n"

    "THREE THINGS THE LAST ATTEMPT GOT WRONG — get them right:\n"
    "  1. THE ROOF TERRACE has exactly THREE SEPARATE rectangular CONCRETE "
    "PLANTERS standing apart from each other along the parapet, each FULL of "
    "big glossy split-leaf philodendron foliage spilling over the rim. Not one "
    "long continuous planter, not empty boxes, not small pots.\n"
    "  2. THE TOP-FLOOR LIVING ROOM has a large flat-screen TV mounted on a "
    "wall of VERTICAL WOOD SLATS, with a wood panel above it and a wood ledge "
    "below. The TV must be there and must be on that slatted panel.\n"
    "  3. THE KITCHENETTE window is a SMALL WIDE HORIZONTAL window above the "
    "counter — wider than it is tall, black frame, two panes. It is NOT a tall "
    "vertical window.\n\n"

    "EVERY ROOM MUST LOOK DIFFERENT from the others — different palette, "
    "different furniture, its own character. Do not repeat the same bedroom "
    "three times:\n"
    "  · LOWER FLOOR — front bedroom: upholstered headboard, cream bedding, "
    "CHOCOLATE throw, DARK GREEN rug, a cream armchair. Back bedroom: a "
    "headboard of vertical wood slats, terracotta throw, wood nightstand, no "
    "green rug. Bathroom: OPEN walk-in shower with NO glass screen, wood-look "
    "tile with a dark brown band, small horizontal window, floating wood "
    "vanity. Study: desk, monitor, pale-oak grid bookcase full of books, rug, "
    "big fiddle-leaf plant. Laundry: plain white, washer and dryer. "
    "Storeroom: open oak shelves with boxes.\n"
    "  · MIDDLE FLOOR — living room: curved CREAM boucle sofa, CAMEL leather "
    "armchair, round TRAVERTINE table, large abstract canvas, a wall of "
    "vertical wood slats. Master bedroom: ARCHED TUFTED headboard against a "
    "CHOCOLATE wall, cream quilted bedding, rattan pendant. Walk-in closet: "
    "pale oak, four open cubbies above, eight drawers below. Master bathroom: "
    "same open shower. Stair: pale treads, thin BLACK railing, one big "
    "abstract artwork.\n"
    "  · TOP FLOOR — WINE-RED curved sofa, cream rounded armchair, OVAL "
    "pale-wood table, the slatted TV wall; dining with a round pale-wood "
    "table, cream chairs, a single LOOPED white LED pendant, TWO white candles "
    "on a black tray, TWO beige art panels; and the compact L-shaped "
    "kitchenette with a wood island, thick WHITE top and white upper "
    "cabinets.\n\n"

    "LIFE IN THE HOUSE — small photorealistic scale figures, natural, not "
    "posed: a SMILING couple sitting on the wine-red sofa upstairs, a person "
    "reading in the cream armchair downstairs, someone at the dining table. "
    "And on the middle floor beside the sofa, a SMALL DOG lying in its own "
    "round dog bed. In the top-floor living area add a GAMING / HOME-CINEMA "
    "corner: a low console under the TV with a game controller on it and a "
    "soft floor cushion facing the screen.\n\n"

    "Everywhere: big BEIGE floor tiles, smooth white plaster walls (flat "
    "plaster and concrete, never rough limestone), black-framed windows, warm "
    "daylight. Every room fully finished — no white blocky rooms, no grey "
    "boxes. No text, no watermark."
)


def env(n):
    for l in open(os.path.join(RAIZ, ".env"), encoding="utf8", errors="replace"):
        if l.startswith(n + "="):
            return l.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get(n, "")


CAB = {"Authorization": "Bearer " + env("WAVESPEED_API_KEY"),
       "Content-Type": "application/json"}


CACHE = os.path.join(AQUI, "_refs_chicas")


def uri(ruta):
    """Manda la referencia REDUCIDA. Con las 14 en su tamano original el
    proveedor tumbaba la peticion («The provider rejected the request»): son
    ~10 MB de base64. A 1024 px de lado largo y JPEG 88 bajan a menos de 2 MB
    en total y no se pierde nada — son referencias de MATERIAL, no de detalle.
    """
    from PIL import Image
    os.makedirs(CACHE, exist_ok=True)
    chico = os.path.join(CACHE, os.path.basename(ruta).rsplit(".", 1)[0] + ".jpg")
    if not os.path.exists(chico):
        im = Image.open(ruta).convert("RGB")
        im.thumbnail((1024, 1024), Image.LANCZOS)
        im.save(chico, quality=88)
    return "data:image/jpeg;base64,%s" % base64.b64encode(
        open(chico, "rb").read()).decode()


def pide(ruta, cuerpo):
    req = urllib.request.Request(WAVESPEED + "/" + ruta,
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
            raise RuntimeError("WaveSpeed fallo: %s" % d.get("error"))
    raise RuntimeError("se acabo la espera")


if __name__ == "__main__":
    faltan = [r for r, _ in REFS if not os.path.exists(r)]
    if faltan:
        raise SystemExit("faltan referencias:\n  " + "\n  ".join(faltan))
    print("mandando %d referencias a %s" % (len(REFS), MODELO), flush=True)
    d = pide(MODELO, {
        "prompt": PROMPT,
        "images": [uri(r) for r, _ in REFS],
        "aspect_ratio": "4:3",
        "output_format": "png",
    })
    urls = espera(d["data"]["id"])
    base = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, "casa_nanobanana")
    base = base[:-4] if base.endswith(".png") else base
    for i, u in enumerate(urls, 1):
        destino = "%s_v%d.png" % (base, i)
        with urllib.request.urlopen(u, timeout=300) as r:
            open(destino, "wb").write(r.read())
        print("listo", destino, flush=True)
