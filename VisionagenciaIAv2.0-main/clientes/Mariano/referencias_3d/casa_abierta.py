#!/usr/bin/env python3
"""La casa ENTERA en corte, fotorrealista, usando los cuartos ya resueltos.

    python3 casa_abierta.py <corte_base.png> [salida.png]

Entran tres imagenes:
  1. el corte del 3D de la casa completa — de ahi salen el angulo, los tres
     niveles y donde va cada mueble;
  2. `lamina_cuartos_reales.jpg` — los 7 cuartos que ya quedaron fotorrealistas,
     cada uno etiquetado. Es la fuente de acabados, y sobre todo lo que hace que
     la casa entera quede COHERENTE con lo que ya se aprobo cuarto por cuarto;
  3. `ref_1_catania_por_cuarto.jpg` — los clips reales de Mariano, por si algun
     rincon no aparece en la lamina.

Sale una imagen: ~$0.025.
"""
import base64, json, os, sys, time, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = "/workspaces/visionagenciaIAv2.0/VisionagenciaIAv2.0-main"
BASE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, "catania_corte_base3d.png")
DESTINO = sys.argv[2] if len(sys.argv) > 2 else os.path.join(AQUI, "casa_abierta.png")
LAMINA = os.path.join(AQUI, "lamina_cuartos_reales.jpg")
CLIPS = os.path.join(AQUI, "ref_1_catania_por_cuarto.jpg")
WAVESPEED = "https://api.wavespeed.ai/api/v3"

PROMPT = (
    "Turn the FIRST image into one photorealistic ARCHITECTURAL CUTAWAY of this "
    "whole three-storey house — a doll's-house photograph with the near wall "
    "removed, every floor and every room visible at once, all of them fully "
    "furnished and finished. "
    "Keep the FIRST image exactly as it is in structure: the same camera angle and "
    "perspective, the same three floors in the same order, the same room layout, "
    "the same staircase, the same roof terrace, the same neighbouring houses of the "
    "row and the same hillside behind. Do not move the camera, do not add or remove "
    "a single room, wall or piece of furniture. "
    "The SECOND image is a sheet of the SAME HOUSE already rendered photorealistically, "
    "room by room, each panel labelled. It is the source of truth: every room in your "
    "picture must match its panel — the same wall finishes, the same floor tile, the "
    "same furniture in the same colours and materials, the same daylight. Keep the "
    "whole house consistent with that sheet. "
    "The THIRD image holds real photographs of the house, for any corner the sheet "
    "does not cover. "
    "FINISH THE WHOLE PICTURE. Every grey or white block in the 3D model is a real "
    "piece of furniture and must end up finished — real wood, real fabric, real "
    "leaves on the plants, real steps on the stairs. Do not leave any plain box, any "
    "untextured slab or any placeholder shape anywhere in the frame. The walls and "
    "floor slabs are smooth painted plaster and smooth concrete of a newly built "
    "house — NOT porous limestone, NOT rough stone, NOT a plaster scale model. "
    "The roof terrace is BARE: pale floor tile, a low white parapet and one teak "
    "table with chairs. The rows of identical green cylinders in the 3D model are "
    "Blender placeholders and do NOT exist in the real house — leave that terrace "
    "without planters and without potted plants. "
    "This image will be used for slow ZOOM AND PAN moves into each individual "
    "room, so every room has to hold up on its own when the frame closes in on "
    "it: sharp edges, readable materials, correct furniture, no mush and no "
    "invented detail. Give the same care to the small rooms at the back and "
    "below as to the big ones in front. "
    "Render it as a real photograph taken outdoors at midday: bright natural "
    "sunlight, real shadows inside each room, real texture on plaster, wood, fabric "
    "and stone. Not a 3D render, not a diagram. No text, no labels, no watermark, "
    "no people."
)


def env(n):
    for l in open(os.path.join(RAIZ, ".env"), encoding="utf8", errors="replace"):
        if l.startswith(n + "="):
            return l.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


CAB = {"Authorization": "Bearer " + env("WAVESPEED_API_KEY"),
       "Content-Type": "application/json"}


def uri(ruta):
    tipo = "png" if ruta.lower().endswith(".png") else "jpeg"
    return "data:image/%s;base64,%s" % (
        tipo, base64.b64encode(open(ruta, "rb").read()).decode())


imgs = [uri(BASE), uri(LAMINA)]
if os.path.exists(CLIPS):
    imgs.append(uri(CLIPS))

req = urllib.request.Request(
    WAVESPEED + "/openai/gpt-image-2/edit",
    data=json.dumps({"prompt": PROMPT, "images": imgs,
                     "aspect_ratio": "1:1", "output_format": "png"}).encode(),
    headers=CAB)
d = json.loads(urllib.request.urlopen(req, timeout=180).read())
id_ = d["data"]["id"]
print("job", id_, "·", len(imgs), "imagenes de entrada")

for _ in range(200):
    time.sleep(3)
    r = urllib.request.Request("%s/predictions/%s/result" % (WAVESPEED, id_), headers=CAB)
    dd = (json.loads(urllib.request.urlopen(r, timeout=60).read()) or {}).get("data") or {}
    if dd.get("status") == "completed":
        with urllib.request.urlopen(dd["outputs"][0], timeout=300) as f:
            open(DESTINO, "wb").write(f.read())
        print("listo", DESTINO)
        break
    if dd.get("status") == "failed":
        raise SystemExit("fallo: %s" % dd.get("error"))
else:
    raise SystemExit("se acabo la espera")
