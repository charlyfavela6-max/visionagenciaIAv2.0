#!/usr/bin/env python3
"""UNA sola generación de GPT Image: la casa entera en corte, fotorrealista.

Entran dos imágenes:
  1. `base_corte.png` — el corte del 3D desde el eje de la cámara del recorrido
     (frame 224, la sala), con las casas de la calle y sin el barandal flotante.
     De ahí salen el ángulo, la planta y dónde va cada mueble.
  2. `ref_1_catania_por_cuarto.jpg` — los 10 clips reales que mandó Mariano.
     De ahí salen los acabados, los colores y la luz.

Sale una imagen: ~$0.025.
"""
import base64, json, os, sys, time, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = sys.argv[1] if len(sys.argv) > 1 else "base_corte.png"
REFS = ("/workspaces/visionagenciaIAv2.0/VisionagenciaIAv2.0-main/clientes/"
        "Mariano/referencias_3d/ref_1_catania_por_cuarto.jpg")
DESTINO = sys.argv[2] if len(sys.argv) > 2 else "casa_fotorrealista.png"
WAVESPEED = "https://api.wavespeed.ai/api/v3"
ENV = "/workspaces/visionagenciaIAv2.0/VisionagenciaIAv2.0-main/.env"

PROMPT = (
    "Turn the FIRST image into a photorealistic architectural cutaway of this "
    "three-storey house — the kind of doll's-house photograph where the near wall "
    "has been removed and you can see every room at once, all of them furnished "
    "and finished. "
    "Keep the first image EXACTLY as it is in structure: the same camera angle, the "
    "same perspective, the same three floors in the same order, the same room "
    "layout, the same staircase, the same roof terrace with its planter, the same "
    "neighbouring houses of the row on both sides and the same hillside behind. Do "
    "not move anything, do not add or remove a single room or piece of furniture. "
    "The SECOND image is a sheet of real photographs of this exact house. Use it as "
    "the source of truth for every finish: the cream curved sofa and the travertine "
    "coffee table in the living room, the beige upholstered headboard and the "
    "chocolate throw in the master bedroom, the pale oak walk-in closet, the "
    "terracotta round headboard in the second bedroom, the taupe kitchen cabinets, "
    "the large-format light stone floor tiles, the white walls, the black window "
    "frames, the teak table on the roof terrace, the artificial turf in the garden. "
    "Render it as a real photograph taken outdoors at midday: bright natural "
    "sunlight, real shadows inside each room, real textures on plaster, wood, fabric "
    "and stone. Not a 3D render, not a diagram. No text, no labels, no watermark, "
    "no people."
)


def env(nombre):
    for l in open(ENV, encoding="utf8", errors="replace"):
        if l.startswith(nombre + "="):
            return l.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


CAB = {"Authorization": "Bearer " + env("WAVESPEED_API_KEY"),
       "Content-Type": "application/json"}


def uri(ruta):
    tipo = "png" if ruta.lower().endswith(".png") else "jpeg"
    return "data:image/%s;base64,%s" % (
        tipo, base64.b64encode(open(ruta, "rb").read()).decode())


req = urllib.request.Request(
    WAVESPEED + "/openai/gpt-image-2/edit",
    data=json.dumps({"prompt": PROMPT, "images": [uri(BASE), uri(REFS)],
                     "aspect_ratio": "1:1", "output_format": "png"}).encode(),
    headers=CAB)
d = json.loads(urllib.request.urlopen(req, timeout=180).read())
id_ = d["data"]["id"]
print("job", id_)

for _ in range(180):
    time.sleep(3)
    r = urllib.request.Request("%s/predictions/%s/result" % (WAVESPEED, id_), headers=CAB)
    dd = (json.loads(urllib.request.urlopen(r, timeout=60).read()) or {}).get("data") or {}
    if dd.get("status") == "completed":
        with urllib.request.urlopen(dd["outputs"][0], timeout=240) as f:
            open(DESTINO, "wb").write(f.read())
        print("listo", DESTINO)
        break
    if dd.get("status") == "failed":
        raise SystemExit("falló: %s" % dd.get("error"))
else:
    raise SystemExit("se acabó la espera")
