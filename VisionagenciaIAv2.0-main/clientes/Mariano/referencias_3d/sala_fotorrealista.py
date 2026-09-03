#!/usr/bin/env python3
"""La sala de la Catania: el 3D convertido en foto, fiel a la casa real.

Entran dos imágenes:
  1. `base_sala_3d_f111.jpg` — el frame 111 del recorrido de Blender. Es el mejor
     del timeline para la sala de planta baja: 36 de 39 piezas visibles, centradas
     y a 4.8 m. De ahí salen el ángulo, la planta y dónde va cada mueble.
  2. `ref_sala_catania_real.jpg` — cuatro cuadros de los videos que mandó Mariano
     el 29/08 (v05 y v06): el palo de madera, el sillón curvo, la mesa redonda y
     la escalera. De ahí salen los acabados, los colores y la luz reales.

Va a ser el END FRAME de un clip, así que la geometría NO se puede mover: si la
cámara o los muebles cambian de sitio, el clip no cierra.

Sale una imagen: ~$0.025.

    python3 sala_fotorrealista.py [base] [salida]
"""
import base64, json, os, sys, time, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, "base_sala_3d_f111.jpg")
REFS = os.path.join(AQUI, "ref_sala_catania_real.jpg")
DESTINO = sys.argv[2] if len(sys.argv) > 2 else os.path.join(AQUI, "sala_catania_fotorrealista.png")
WAVESPEED = "https://api.wavespeed.ai/api/v3"
ENV = "/workspaces/visionagenciaIAv2.0/VisionagenciaIAv2.0-main/.env"

PROMPT = (
    "Turn the FIRST image into a photorealistic architectural cutaway photograph "
    "of this house — the doll's-house shot where the near wall has been removed "
    "and you look straight into the finished living room. "

    "GEOMETRY IS LOCKED. This is the end frame of a clip, so nothing may move. "
    "Same camera position, same angle, same perspective, same floors, same room "
    "layout, same staircase, same opening in the wall, same neighbouring houses "
    "and hillside behind. "
    "THE CREAM CURVED SOFA STAYS EXACTLY WHERE IT IS in the first image — same "
    "spot in the frame, same orientation, same size, same distance from the "
    "camera. Do NOT centre it, do NOT rotate it, do NOT bring it closer, do NOT "
    "make it bigger. The same rule applies to the round coffee table, the wooden "
    "trunk sculpture on its dark square base, the plant, the floor lamp and the "
    "canvas: every object keeps its exact position and scale. Add nothing, "
    "remove nothing. "

    "THE GREEN PLANT IS A PLACEHOLDER. In the first image it is a crude 3D shape: "
    "three flat green blobs stacked on a stem. Replace it with a REAL, "
    "PHOTOGRAPHIC houseplant — a fiddle-leaf fig with big glossy veined leaves "
    "growing irregularly, some leaves turned, some overlapping, natural colour "
    "variation and a few imperfections — standing in the SAME white ribbed pot, at "
    "the SAME spot and the SAME height. It must read as a living plant that was "
    "photographed, never as a 3D model, never as a topiary ball, never as "
    "geometric foliage. "

    "The SECOND image is a strip of real photographs of THIS EXACT living room. "
    "It is the only source of truth for the finishes: the natural wood trunk "
    "sculpture on its dark square base, the cream curved sofa, the round "
    "light-wood coffee table, the real fiddle-leaf fig in its white ribbed pot, "
    "the vertical light-oak slat panelling, the large abstract canvas in black and "
    "beige, the big-format cream stone floor tiles, the woven beige rug, the white "
    "plaster walls, the black slim window frames, the black horizontal-tube stair "
    "railing with light wood treads. "

    "Bright Baja midday sun from the terrace side, warm, with real soft shadows on "
    "the floor and a real dark contact shadow under every piece of furniture. Real "
    "texture on plaster, oak, fabric, stone and the raw wood of the trunk — visible "
    "grain, weave and grit. "
    "NOTHING in this image may look like a 3D render: no smooth plastic surfaces, "
    "no perfect edges, no flat untextured colour. It is a photograph. "
    "No text, no labels, no watermark, no people."
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
                     "aspect_ratio": "4:5", "resolution": "2k",
                     "output_format": "png"}).encode(),
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
