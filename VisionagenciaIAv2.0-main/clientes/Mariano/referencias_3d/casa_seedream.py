#!/usr/bin/env python3
"""La casa ENTERA en corte, fotorrealista, con Seedream 5.0 Pro.

    python3 casa_seedream.py [salida.png]

A diferencia de GPT Image, Seedream acepta hasta 10 imagenes de referencia, asi
que los 7 cuartos van SUELTOS y no apelmazados en una lamina: cada uno entra con
su propio detalle y el modelo puede seguirlos cuarto por cuarto. Sale a 2k, que
es lo que aguanta los zoom-pans.

Entradas:
  1. `catania_corte_base3d.png` — el corte del 3D. Pone la estructura: el angulo,
     los tres niveles, la planta y donde va cada mueble.
  2..8. los 7 cuartos ya fotorrealistas. Ponen los acabados de cada cuarto.

Cuesta $0.045.
"""
import base64, io, json, os, sys, time, urllib.request
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = "/workspaces/visionagenciaIAv2.0/VisionagenciaIAv2.0-main"
BASE = os.path.join(AQUI, "catania_corte_base3d.png")
DESTINO = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, "casa_seedream.png")
MODELO = "bytedance/seedream-v5.0-pro/edit"
WAVESPEED = "https://api.wavespeed.ai/api/v3"

# el cuarto y como se llama, para nombrarselos en el prompt en el mismo orden
CUARTOS = [
    ("sala",          "the living room and dining area"),
    ("puerta_abre",   "the roof terrace and the master bedroom under it"),
    ("recamara_ppal", "the master bedroom"),
    ("dos_recamaras", "the second bedroom"),
    ("dos_rec_bano",  "the two lower bedrooms with the bathroom between them"),
    ("lavado",        "the laundry room"),
    ("jardin",        "the back garden"),
]

PROMPT = (
    "Make ONE photorealistic architectural cutaway of this whole three-storey "
    "house — a doll's-house photograph with the near wall removed, every floor "
    "and every room visible at once, all fully furnished and finished.\n\n"
    "IMAGE 1 is the grey 3D model and defines the STRUCTURE. Keep it exactly: the "
    "same camera angle and perspective, the same three floors in the same order, "
    "the same room layout, the same staircase, the same roof terrace, the same "
    "neighbouring houses of the row and the same hillside behind. Do not move the "
    "camera. Do not add or remove a single room, wall or piece of furniture.\n\n"
    "IMAGES 2 to 8 are the SAME HOUSE already photographed room by room, in this "
    "order: " + "; ".join(f"{i+2}) {q}" for i, (_, q) in enumerate(CUARTOS)) + ". "
    "Each room in your picture must match its reference exactly — the same wall "
    "finishes, the same floor tile, the same furniture in the same colours and "
    "materials, the same daylight. Keep the whole house consistent with them.\n\n"
    "FINISH THE WHOLE PICTURE. Every grey or white block in the 3D model is a real "
    "piece of furniture and must end up finished: real wood, real fabric, real "
    "leaves on the plants, real steps on the stairs. Leave no plain box, no "
    "untextured slab and no placeholder shape anywhere. Walls and floor slabs are "
    "smooth painted plaster and smooth concrete of a newly built house — not "
    "porous limestone, not rough stone, not a plaster scale model.\n\n"
    "The roof terrace is BARE: pale floor tile, a low white parapet and one teak "
    "table with chairs. The rows of identical green cylinders in the 3D model are "
    "placeholders that do not exist in the real house — leave that terrace with no "
    "planters and no potted plants.\n\n"
    "This image will be used for slow ZOOM AND PAN moves into each room, so every "
    "room must hold up when the frame closes in on it: sharp edges, readable "
    "materials, correct furniture, no mush and no invented detail. Give the small "
    "rooms at the back and below the same care as the big ones in front.\n\n"
    "A real photograph taken outdoors at midday: bright natural sunlight, real "
    "shadows inside each room, real texture on plaster, wood, fabric and stone. "
    "Not a 3D render, not a diagram. No text, no labels, no watermark, no people."
)


def env(n):
    for l in open(os.path.join(RAIZ, ".env"), encoding="utf8", errors="replace"):
        if l.startswith(n + "="):
            return l.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


CAB = {"Authorization": "Bearer " + env("WAVESPEED_API_KEY"),
       "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}


def uri(ruta, alto=1100):
    """Reduce a JPEG antes de mandar: 8 PNG completos son ~17 MB de base64 y el
    POST se cae. A 1100 px de alto siguen sirviendo de referencia de acabados."""
    im = Image.open(ruta).convert("RGB")
    if im.height > alto:
        im = im.resize((round(im.width * alto / im.height), alto), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=90)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


imgs = [uri(BASE, 1400)]
for k, _ in CUARTOS:
    r = os.path.join(AQUI, "cuartos_reales", k + ".png")
    if not os.path.exists(r):
        raise SystemExit("falta el cuarto: " + r)
    imgs.append(uri(r))

cuerpo = {"prompt": PROMPT, "images": imgs, "aspect_ratio": "1:1",
          "resolution": "2k", "output_format": "png"}
print(f"{len(imgs)} imagenes · payload {len(json.dumps(cuerpo))/1e6:.1f} MB")

req = urllib.request.Request(f"{WAVESPEED}/{MODELO}", data=json.dumps(cuerpo).encode(), headers=CAB)
d = json.loads(urllib.request.urlopen(req, timeout=300).read())
id_ = d["data"]["id"]
print("job", id_)

for _ in range(300):
    time.sleep(3)
    r = urllib.request.Request(f"{WAVESPEED}/predictions/{id_}/result", headers=CAB)
    dd = (json.loads(urllib.request.urlopen(r, timeout=60).read()) or {}).get("data") or {}
    if dd.get("status") == "completed":
        with urllib.request.urlopen(dd["outputs"][0], timeout=300) as f:
            open(DESTINO, "wb").write(f.read())
        print("listo", DESTINO, os.path.getsize(DESTINO) // 1024, "KB")
        break
    if dd.get("status") == "failed":
        raise SystemExit("fallo: %s" % dd.get("error"))
else:
    print("sigue corriendo; job:", id_)
