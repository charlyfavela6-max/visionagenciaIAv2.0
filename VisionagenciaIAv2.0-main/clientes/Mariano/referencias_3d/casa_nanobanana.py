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
#
# OCHO, no catorce. El schema dice `maxItems: 14`, pero con las 14 el proveedor
# tumbaba la peticion («The provider rejected the request») aunque fueran
# reducidas; con 3 pasa y con 8 tambien. Se quedan las de los cuartos que de
# verdad se ven en el corte; el bano, la cocina y el vestidor se describen con
# palabras en el prompt, que para material alcanza.
REFS = [
    (os.path.join(CORTE, "corte_gris.png"), "grey 3D cutaway — the volume"),
    (os.path.join(CORTE, "corte_aristas.png"), "line drawing — the structure"),
    (os.path.join(VIDEO, "f01.jpg"), "ground-floor living room"),
    (os.path.join(VIDEO, "f09.jpg"), "slatted wood TV wall"),
    (os.path.join(VIDEO, "f10.jpg"), "dining + kitchen, wine-red sofa"),
    (os.path.join(VIDEO, "f07.jpg"), "bedroom with cream armchair"),
    (os.path.join(VIDEO, "f11.jpg"), "roof terrace with planter"),
    (os.path.join(VIDEO, "f05.jpg"), "wooden stair"),
]

PROMPT = (
    "Turn this into ONE photorealistic architectural CUTAWAY photograph of a "
    "three-storey house — a doll's-house view with the near side wall removed, "
    "so all three floors are open and visible at once, fully furnished and "
    "finished.\n\n"

    "IMAGE 1 is the grey 3D render and IMAGE 2 is its line drawing. TOGETHER "
    "THEY ARE THE LAW — the geometry is already decided:\n"
    "  · Keep the CAMERA exactly: same angle, same height, same lens. Do not "
    "re-centre, do not flatten it, do not zoom.\n"
    "  · Keep EVERY floor slab, EVERY wall and EVERY opening where the line "
    "drawing puts them. Do not add a wall, do not remove a wall, do not move a "
    "doorway, do not invent a courtyard or a staircase that is not drawn.\n"
    "  · Keep EVERY piece of furniture in its exact place and at its exact "
    "size. The beds, the sofas, the tables and the shelves are already "
    "positioned — you are painting them, not re-arranging them.\n"
    "  · Three levels, bottom to top: LOWER FLOOR with two bedrooms, a "
    "bathroom, a study, a storeroom and a laundry; MIDDLE FLOOR with the "
    "living room, the master bedroom, the walk-in closet, the master bathroom "
    "and the stair; TOP FLOOR open-plan with kitchen, dining and a second "
    "living area; and above it the open ROOF TERRACE.\n\n"

    "IMAGES 3 to 8 are photographs of the REAL house. Take from them ONLY the "
    "materials, colours and light:\n"
    "  · ground-floor living room: curved CREAM boucle sofa, CAMEL leather "
    "armchair, round TRAVERTINE coffee table, large abstract canvas in beige "
    "and black;\n"
    "  · a feature wall of vertical WOOD SLATS with the TV, an open shelf unit "
    "and a big fiddle-leaf plant;\n"
    "  · dining and kitchen upstairs: a WINE-RED / deep burgundy sofa, a round "
    "pale-wood table with cream chairs, a wood-fronted island with a white "
    "top, a thin brass ring pendant lamp;\n"
    "  · bedrooms: upholstered headboards, cream bedding with a chocolate "
    "brown throw, a rounded cream armchair, sheer curtains over "
    "floor-to-ceiling black-framed sliding windows;\n"
    "  · bathrooms: WOOD-LOOK tile with a dark brown band, floating wood "
    "vanity, white basin;\n"
    "  · stair: pale tile treads, white walls, very thin black metal railing;\n"
    "  · closet: open shelves in pale oak;\n"
    "  · laundry: plain room with the water outlets on a white wall;\n"
    "  · ROOF TERRACE: pale floor tile, low white parapet, a TEAK table with "
    "chairs and a REAL PLANTER WITH GREEN PLANTS along the parapet — the roof "
    "is NOT bare;\n"
    "  · back yard: artificial turf and a grey concrete block retaining wall.\n"
    "  · Everywhere: big beige floor tiles, smooth white plaster walls. The "
    "walls are FLAT PLASTER AND CONCRETE, never rough limestone or stucco "
    "texture.\n\n"

    "FINISH THE WHOLE PICTURE. Every room must be fully furnished and lit — do "
    "not leave any room as a white blocky model, and do not leave any piece of "
    "furniture as a plain grey box: if a shape reads as a box in image 1, it is "
    "a real piece of furniture and you must paint it as one.\n\n"

    "Natural daylight from outside, soft shadows, clean architectural "
    "photography. No text, no labels, no watermark, no people."
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
