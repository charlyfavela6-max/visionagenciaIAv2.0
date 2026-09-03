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
    "puerta_abre":   (["17", "12"], "a cross-section of two floors at once: on top the "
                                    "roof terrace — a BARE sun-baked terrace with pale "
                                    "floor tile, a low white parapet wall and one large "
                                    "teak table with chairs, NO planters and NO potted "
                                    "plants (the green cylinders in the grey model are "
                                    "placeholders that do not exist in the real house), "
                                    "plus the built-in outdoor lounge seating along the "
                                    "right-hand side of that terrace, which must stay — "
                                    "and underneath, the master bedroom on the left and, "
                                    "on the right, the ground-floor living room — the two "
                                    "plain boxes there are a CAMEL-COLOURED LEATHER "
                                    "ARMCHAIR on a wood base and a SQUARE TRAVERTINE "
                                    "COFFEE TABLE, and that room also has sheer gauze "
                                    "curtains, vertical wood slats and a framed canvas on "
                                    "the wall; draw them all as the real furniture they "
                                    "are, never as bare blocks"),
    "dos_rec_bano":  (["13", "19"], "a cross-section of the lower floor: two secondary "
                                    "bedrooms side by side with a bathroom between them, "
                                    "the left bed with a chocolate throw, the right one "
                                    "with a beige upholstered headboard"),
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


# Los cuartos que hay que leer como CORTE de la casa. GPT Image, si se le deja,
# mete la camara dentro y los cierra en un cuarto normal de cuatro paredes: se
# pierde que son parte de una estructura abierta, con sus losas y sus niveles.
CORTE = {"sala", "recamara_ppal", "dos_recamaras", "dos_rec_bano", "lavado",
         "puerta_abre", "jardin"}

PROMPT_CORTE = (
    "Turn the FIRST image into a realistic photograph of {que}. "
    "IMPORTANT — this is an ARCHITECTURAL CUTAWAY, a doll's-house section of a real "
    "building photographed FROM OUTSIDE: the front wall is removed and you look "
    "straight into the rooms. Keep it that way. Do NOT move the camera inside the "
    "room, do NOT close the space into an ordinary four-walled interior, do NOT "
    "invent a front wall or a ceiling over the viewer. "
    "Keep EXACTLY what the grey model shows: the same camera position and framing, "
    "the horizontal concrete floor slabs cut through and seen edge-on as bands "
    "across the picture, more than one room and more than one storey visible at "
    "once, the open sky and the outdoors where the model has them, and every wall, "
    "window and piece of furniture in its place. Do not add or remove furniture. "
    "The other image or images are real photographs of this same house: copy their "
    "materials, colours, finishes and daylight — the wall paint, the floor tile, the "
    "wood tones, the fabrics, the window frames. "
    "It must look like a real photograph of a finished house at midday, sharp and "
    "sunlit, with real texture on every surface and the cut slab edges reading as "
    "real concrete. "
    "FINISH THE WHOLE PICTURE, not just the main room. Every grey or white block in "
    "the model is a REAL piece of furniture and must end up fully finished — real "
    "wood, real fabric, real leaves on the plants, real steps on the stairs. Do not "
    "leave any plain white or grey box, any untextured slab or any placeholder shape "
    "anywhere in the frame: the rooms behind and below the main one must look just as "
    "finished as the main one. "
    "The walls and floor slabs are smooth painted plaster and smooth concrete, like a "
    "newly built house — NOT porous limestone, NOT rough stone, NOT a plaster scale "
    "model or a museum maquette. "
    "The roof terrace of the real house (see the photographs) has pale floor tile, a "
    "low white parapet, a dark grey outdoor lounge set — sofa, armchairs and a low "
    "table — and real leafy plants along the parapet, with the sea on the horizon. "
    "The rows of identical green cylinders in the grey model are Blender "
    "placeholders: replace them with those real plants and that real furniture. "
    "Not a render, not a 3D image, no text, no watermark, no people. "
    "TALL VERTICAL 9:16 PORTRAIT ORIENTATION."
)


# Las FOTOS REALES que mando Mariano el 2 sep 2026 (fotos_reales/). Van antes que
# los frames de `escenas_wa`, que salian de un video y estaban borrosos. Si un
# cuarto no aparece aqui se sigue usando su clip de siempre.
FOTOS = {
    "fachada":       ["fachada_1_03", "fachada_2_17"],
    "cochera":       ["fachada_1_03", "fachada_2_17"],
    "escalones":     ["escalera_1_25", "escalera_2_29"],
    "sala":          ["sala_2_02", "sala_1_01", "sala_6_32"],
    "cocina":        ["cocina_1_30"],
    "pasillo":       ["escalera_1_25"],
    "roofgarden":    ["roofgarden_1_15", "roofgarden_2_20"],
    "recamara_ppal": ["recamara_ppal_1_22", "recamara_ppal_2_24"],
    "vestidor":      ["recamara_ppal_2_24"],
    "dos_recamaras": ["recamara_1_12", "recamara_2_16", "recamara_3_26"],
    "estudio":       ["recamara_3_26", "sala_pa_3_19"],
    "lavado":        ["bano_3_14"],
    "jardin":        ["jardin_1_11", "fachada_3_23"],
    "puerta_abre":   ["roofgarden_1_15", "sala_2_02", "recamara_ppal_1_22"],
    "dos_rec_bano":  ["recamara_1_12", "bano_4_21", "recamara_3_26"],
}


def foto(nombre):
    ruta = os.path.join(AQUI, "fotos_reales", nombre + ".jpg")
    return ruta if os.path.exists(ruta) else None


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

    reales = [foto(n) for n in FOTOS.get(cuarto, [])]
    reales = [r for r in reales if r] or [clip(c) for c in clips if clip(c)]
    imagenes = [uri(base)] + [uri(r) for r in reales[:9]]
    plantilla = PROMPT_CORTE if cuarto in CORTE else PROMPT
    d = pide("openai/gpt-image-2/edit", {
        "prompt": plantilla.format(que=que),
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
