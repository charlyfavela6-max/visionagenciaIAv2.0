#!/usr/bin/env python3
"""La casa ENTERA en corte, v2 — con las FOTOS REALES del 2 sep.

    python3 casa_seedream_v2.py [salida.png]

Que cambia contra `casa_seedream.py`:

1. Las referencias ya no son las salidas de GPT Image (`cuartos_reales/*.png`),
   que son interpretaciones y traen sus propios errores encima. Ahora van las
   FOTOS de Mariano. Se eligen por lo que APORTAN, no por cuarto: el sofa
   terracota, el muro de duela, el azulejo madera del bano, la cocina, la
   escalera y la azotea con el mar.
2. El prompt le prohibe lo que hizo mal en la v1: aplanar la camara a un alzado
   frontal, borrar la calle y las vecinas, y convertir la planta baja en
   recamaras.
3. La azotea YA NO se le pide pelada. La foto 15 enseña que la casa real tiene
   sala de exterior gris oscuro y plantas de verdad en el pretil.

Cuesta $0.045.
"""
import base64, io, json, os, sys, time, urllib.request
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = "/workspaces/visionagenciaIAv2.0/VisionagenciaIAv2.0-main"
BASE = os.path.join(AQUI, "catania_corte_base3d.png")
FOTOS = os.path.join(AQUI, "fotos_reales")
DESTINO = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, "casa_seedream_v2.png")
MODELO = "bytedance/seedream-v5.0-pro/edit"
WAVESPEED = "https://api.wavespeed.ai/api/v3"

# archivo de fotos_reales -> que es lo que esa foto viene a fijar
REFS = [
    ("sala_5_28",       "the upstairs living room: a RUST / TERRACOTTA fabric sofa, a "
                        "wall of vertical wood slats behind the TV, big beige floor "
                        "tiles and a black-framed sliding window"),
    ("sala_2_02",       "the ground-floor living room: a curved CREAM BOUCLE sofa, a "
                        "CAMEL LEATHER armchair and a round TRAVERTINE coffee table"),
    ("recamara_ppal_2_24", "the master bedroom: a wall of vertical wood slats behind "
                        "the bed, cream bedding with a chocolate brown throw, sheer "
                        "white curtains over a floor-to-ceiling window"),
    ("recamara_1_12",   "a secondary bedroom: brown upholstered headboard, chocolate "
                        "throw across the foot of the bed, a small wood nightstand"),
    ("bano_4_21",       "the bathrooms: WOOD-LOOK tile in the shower with a DARK BROWN "
                        "horizontal band, a floating wood vanity and a white basin"),
    ("cocina_1_30",     "the kitchen: plain WHITE cabinets, a WOOD ISLAND with a white "
                        "top, open shelves and a window over the counter"),
    ("escalera_1_25",   "the staircase: white walls, pale tile treads and a very thin "
                        "BLACK metal railing with horizontal bars"),
    ("roofgarden_1_15", "the roof terrace: pale floor tile, a low white parapet, a "
                        "DARK GREY outdoor lounge set — sofa, armchairs and a low "
                        "table — real leafy plants along the parapet, and THE SEA on "
                        "the horizon"),
]

PROMPT = (
    "Make ONE photorealistic architectural cutaway of this whole three-storey "
    "house — a doll's-house photograph with the near wall removed, every floor "
    "and every room visible at once, all fully furnished and finished.\n\n"

    "IMAGE 1 is the grey 3D model and it defines the STRUCTURE. It is the law.\n"
    "  · Keep its CAMERA EXACTLY: it is a raised THREE-QUARTER view, looking down "
    "at the house from above and from one side, so the rooms are seen in "
    "perspective and you can see how deep they are. Do NOT flatten it into a "
    "straight-on frontal elevation. Do NOT re-centre it. Do NOT change the lens.\n"
    "  · Keep the STREET and the ROW OF NEIGHBOURING HOUSES that the model shows "
    "on the right, and the ones behind. This house stands in a built street, not "
    "alone on a hill.\n"
    "  · Keep the ROOM PROGRAMME the model shows, floor by floor. The top floor "
    "is the open roof terrace. Under it are the living areas and the master "
    "bedroom. The lower floor holds the secondary bedrooms, the bathroom and the "
    "laundry. Do NOT turn a living room into a bedroom and do NOT repeat the same "
    "bedroom three times.\n"
    "  · Keep the STAIRCASE clearly visible, running between the floors where the "
    "model puts it, with its steps drawn as real steps.\n"
    "  · Do not add or remove a single room, wall, window or piece of furniture.\n\n"

    "IMAGES 2 to 9 are PHOTOGRAPHS OF THIS SAME HOUSE, already built and "
    "furnished. They are the law for MATERIALS and COLOUR — copy them literally, "
    "do not invent finishes:\n" +
    "".join(f"  {i+2}. {q}\n" for i, (_, q) in enumerate(REFS)) + "\n"

    "The whole house shares one palette taken from those photographs: white "
    "painted plaster walls, large beige floor tiles, warm oak wood, black "
    "aluminium window frames, sheer white curtains, and the rust/terracotta and "
    "cream upholstery. Do NOT invent wallpaper, do NOT invent gold or honeycomb "
    "panels, do NOT invent stone cladding.\n\n"

    "FINISH THE WHOLE PICTURE. Every grey or white block in the 3D model is a real "
    "piece of furniture and must end up finished: real wood, real fabric, real "
    "leaves on the plants, real steps on the stairs. Leave no plain box, no "
    "untextured slab and no placeholder shape anywhere. Walls and floor slabs are "
    "smooth painted plaster and smooth concrete of a newly built house — not "
    "porous limestone, not rough stone, not a plaster scale model. Give the small "
    "rooms at the back and below the same care as the big ones in front.\n\n"

    "The rows of identical green cylinders on the terrace in the 3D model are "
    "Blender placeholders: replace them with the real planting and the real "
    "outdoor furniture of image 9.\n\n"

    "This image will be used for slow ZOOM AND PAN moves into each room, so every "
    "room must hold up when the frame closes in on it: sharp edges, readable "
    "materials, correct furniture, no mush and no invented detail.\n\n"

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
    im = Image.open(ruta).convert("RGB")
    if im.height > alto:
        im = im.resize((round(im.width * alto / im.height), alto), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=90)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


if __name__ == "__main__":
    imgs = [uri(BASE, 1400)]
    for k, _ in REFS:
        r = os.path.join(FOTOS, k + ".jpg")
        if not os.path.exists(r):
            raise SystemExit("falta la foto: " + r)
        imgs.append(uri(r))

    # 1024x900 -> el corte es apaisado; pedirlo en 1:1 lo estira. 4:3 le queda.
    cuerpo = {"prompt": PROMPT, "images": imgs, "aspect_ratio": "4:3",
              "resolution": "2k", "output_format": "png"}
    print(f"{len(imgs)} imagenes · payload {len(json.dumps(cuerpo))/1e6:.1f} MB")

    req = urllib.request.Request(f"{WAVESPEED}/{MODELO}",
                                 data=json.dumps(cuerpo).encode(), headers=CAB)
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
