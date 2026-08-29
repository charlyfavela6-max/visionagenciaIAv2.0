#!/usr/bin/env python3
"""Cada cuarto de la Catania, fotorrealista, desde el ANGULO QUE YA TIENE LA
CAMARA DEL RECORRIDO.

    python3 cuartos_gpt.py [cuarto ...]

Como funciona: se le mandan a GPT Image 2 DOS imagenes por cuarto —
  1. el cuadro de Blender del recorrido (frame exacto de la spline): pone el
     angulo, el encuadre y donde va cada mueble;
  2. el clip real que mando Mariano: pone los acabados, los colores y la luz.
y se le pide que dibuje el 1 con los materiales del 2.

Va de uno en uno y guarda cada salida, asi que si falla uno no se pierde el
resto. ~$0.025 por cuarto.
"""
import base64, json, os, sys, time, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
MARIANO = os.path.dirname(AQUI)
RAIZ = os.path.dirname(os.path.dirname(MARIANO))
CUADROS = os.environ.get("CUADROS", "/tmp/claude-1000/-workspaces-visionagenciaIAv2-0/"
                         "d5acfe85-a63b-414f-9711-7013de146741/scratchpad")
SALIDA = os.path.join(AQUI, "cuartos_reales")
WAVESPEED = "https://api.wavespeed.ai/api/v3"

# cuarto -> (clips reales de referencia, que es el cuarto)
CUARTOS = {
    "fachada":       (["10"], "the front facade of the house seen from the street, "
                              "with the neighbouring houses of the same row on both sides"),
    "cochera":       (["10"], "the covered carport and the front entrance"),
    "escalones":     (["14"], "the wooden staircase going up between floors"),
    "sala":          (["15", "18"], "the living room with the curved cream sofa, "
                                    "the low travertine coffee table and the TV wall"),
    "cocina":        (["04"], "the kitchen with taupe cabinets, stone countertop and "
                              "the window over the sink"),
    "pasillo":       (["07"], "the hallway with doors to the bedrooms"),
    "roofgarden":    (["17"], "the roof garden terrace with the teak table and the "
                              "view over the hills"),
    "recamara_ppal": (["12"], "the master bedroom with the beige upholstered headboard, "
                              "the chocolate throw at the foot of the bed and cream bedding"),
    "vestidor":      (["11"], "the walk-in closet in pale oak, with open shelves and drawers"),
    "dos_recamaras": (["13", "19"], "the secondary bedroom with the floor-to-ceiling "
                                    "sliding window, white curtains and the view of the hills"),
    "estudio":       (["19"], "the study with a desk, a bookshelf with books, a monitor "
                              "and a plant, finished like the rest of the house"),
    "lavado":        (["23"], "the laundry room with washer and dryer"),
    "jardin":        (["16"], "the back garden with artificial turf, the concrete "
                              "retaining wall and the view down to the road"),
}

PROMPT = (
    "Turn the FIRST image into a realistic photograph of {que}. "
    "The first image is a grey 3D block model: keep its camera angle, its framing, "
    "its perspective and the position of every wall, window and piece of furniture "
    "EXACTLY as they are — do not move the camera, do not re-arrange the room, do "
    "not add or remove furniture. "
    "The other image or images are real photographs of this same house: copy their "
    "materials, colours, finishes and daylight — the wall paint, the floor tile, the "
    "wood tones, the fabric of the bedding, the window frames. "
    "It must look like a photo taken on a phone inside the finished house at midday: "
    "natural daylight coming through the windows, soft real shadows, slight lens "
    "distortion, real texture on every surface. Not a render, not a 3D image, no "
    "text, no watermark, no people. "
    "TALL VERTICAL 9:16 PORTRAIT ORIENTATION."
)


def env(nombre):
    ruta = os.path.join(RAIZ, "VisionagenciaIAv2.0-main", ".env")
    if not os.path.exists(ruta):
        ruta = os.path.join(RAIZ, ".env")
    for l in open(ruta, encoding="utf8", errors="replace"):
        if l.startswith(nombre + "="):
            return l.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get(nombre, "")


CAB = {"Authorization": "Bearer " + env("WAVESPEED_API_KEY"),
       "Content-Type": "application/json"}


def uri(ruta):
    tipo = "png" if ruta.lower().endswith(".png") else "jpeg"
    return "data:image/%s;base64,%s" % (
        tipo, base64.b64encode(open(ruta, "rb").read()).decode())


def clip(num):
    import glob
    v = sorted(glob.glob(os.path.join(MARIANO, "escenas_wa", num + "_*.jpg")))
    return v[0] if v else None


def pide(ruta, cuerpo):
    req = urllib.request.Request(WAVESPEED + "/" + ruta,
                                 data=json.dumps(cuerpo).encode(), headers=CAB)
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())


def espera(id_):
    for _ in range(180):
        time.sleep(2)
        req = urllib.request.Request(
            "%s/predictions/%s/result" % (WAVESPEED, id_), headers=CAB)
        d = (json.loads(urllib.request.urlopen(req, timeout=60).read()) or {}).get("data") or {}
        if d.get("status") == "completed":
            return d["outputs"][0]
        if d.get("status") == "failed":
            raise RuntimeError("WaveSpeed falló: %s" % d.get("error"))
    raise RuntimeError("se acabó la espera")


def haz(cuarto):
    clips, que = CUARTOS[cuarto]
    base = os.path.join(CUADROS, "cuadro_%s.png" % cuarto)
    if not os.path.exists(base):
        print("  falta el cuadro de Blender:", base); return None
    destino = os.path.join(SALIDA, "%s.png" % cuarto)
    if os.path.exists(destino):
        print("  ya existe %s — bórralo si quieres rehacerlo" % cuarto); return destino

    imagenes = [uri(base)] + [uri(clip(c)) for c in clips if clip(c)]
    d = pide("openai/gpt-image-2/edit", {
        "prompt": PROMPT.format(que=que),
        "images": imagenes,
        "aspect_ratio": "9:16",
        "output_format": "png",
    })
    url = espera(d["data"]["id"])
    os.makedirs(SALIDA, exist_ok=True)
    with urllib.request.urlopen(url, timeout=240) as r:
        open(destino, "wb").write(r.read())
    print("  listo", destino)
    return destino


if __name__ == "__main__":
    cuales = sys.argv[1:] or list(CUARTOS)
    for c in cuales:
        if c not in CUARTOS:
            print("no conozco el cuarto", c); continue
        print(c)
        try:
            haz(c)
        except Exception as e:
            print("  ERROR:", e)
