#!/usr/bin/env python3
"""Tres cuadros fotorrealistas para probar el movimiento en Kling:
frente, atrás y la vista desde el mar.

Cada uno son DOS imágenes a GPT Image: el render de Blender (pone el ángulo y
la geometría) y la foto real que le toca (pone los acabados y la luz).
Tres generaciones, ~$0.08 en total.

    python3 tres_para_kling.py [frente|atras|mar ...]
"""
import base64, glob, json, os, sys, time, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
MARIANO = os.path.dirname(AQUI)
CUADROS = os.environ.get("CUADROS", "/tmp/claude-1000/-workspaces-visionagenciaIAv2-0/"
                         "d5acfe85-a63b-414f-9711-7013de146741/scratchpad")
SALIDA = os.path.join(AQUI, "kling")
WAVESPEED = "https://api.wavespeed.ai/api/v3"
ENV = "/workspaces/visionagenciaIAv2.0/VisionagenciaIAv2.0-main/.env"

COMUN = (
    "Keep the FIRST image exactly as it is in geometry: same camera angle, same "
    "perspective, same buildings in the same places, same horizon line. Do not move "
    "the camera and do not invent architecture that is not there. "
    "The other image is a real photograph of this same development — copy its "
    "materials, colours and daylight. "
    "Render it as a real photograph taken at midday in Baja California: hard "
    "sunlight, real shadows, dry scrub, real texture on stucco, glass and concrete. "
    "Not a 3D render, not a diagram. No text, no watermark, no people, no cars. "
    "TALL VERTICAL 9:16 PORTRAIT ORIENTATION."
)

TOMAS = {
    "frente": (
        "hd_frente.png", ["10"],
        "Turn the first image into a photograph of the FRONT of this white "
        "three-storey townhouse seen from the street, with its neighbours of the "
        "same row on both sides, the concrete-and-grass striped walkway leading to "
        "the front door, black window frames and a flat parapet roof. " + COMUN),
    "atras": (
        "libre_atras_b.png", ["16"],
        "Turn the first image into a photograph of the BACK of this white townhouse "
        "seen from its garden: the artificial turf lawn in the foreground, the "
        "concrete retaining wall, the black steel balcony railing on the first "
        "floor, the tall black-framed sliding window behind it, and the roof "
        "terrace parapet at the top. " + COMUN),
    "roofgarden": (
        "hd_roofgarden.png", ["17"],
        "Turn the first image into a photograph of this ROOF TERRACE: the long "
        "planter box with succulents along the parapet, the teak dining table with "
        "its chairs, the light stone floor tiles, the white parapet wall, and the "
        "dry hills and the rest of the development beyond it. " + COMUN),
    "estudio": (
        "hd_estudio.png", ["19"],
        "Turn the first image into a photograph of this STUDY room: the desk with a "
        "monitor and keyboard, the task chair, the bookshelf with books, the table "
        "lamp, the rug and the plant, finished like the rest of this house — white "
        "walls, pale oak furniture, large-format light stone floor tiles, black "
        "window frames. " + COMUN),
    "mar": (
        "hd_mar.png", ["ref3"],
        "Turn the first image into a photograph taken from a drone out over the "
        "Pacific Ocean, looking back at the coast: turquoise water with swell and "
        "lines of white foam in the foreground, the beach, then the dry ochre "
        "hillside covered with the white houses of the development, and the ridge "
        "line against a clear blue sky. " + COMUN),
}


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


def referencia(clave):
    if clave == "ref3":
        return os.path.join(AQUI, "ref_3_dron_real_mariano.jpg")
    v = sorted(glob.glob(os.path.join(MARIANO, "escenas_wa", clave + "_*.jpg")))
    return v[0] if v else None


def haz(nombre):
    base, refs, prompt = TOMAS[nombre]
    ruta = os.path.join(CUADROS, base)
    destino = os.path.join(SALIDA, "%s.png" % nombre)
    if os.path.exists(destino):
        print("  ya existe", destino); return
    imagenes = [uri(ruta)] + [uri(referencia(c)) for c in refs if referencia(c)]
    req = urllib.request.Request(
        WAVESPEED + "/openai/gpt-image-2/edit",
        data=json.dumps({"prompt": prompt, "images": imagenes,
                         "aspect_ratio": "9:16", "output_format": "png"}).encode(),
        headers=CAB)
    id_ = json.loads(urllib.request.urlopen(req, timeout=180).read())["data"]["id"]
    for _ in range(180):
        time.sleep(3)
        r = urllib.request.Request("%s/predictions/%s/result" % (WAVESPEED, id_),
                                   headers=CAB)
        d = (json.loads(urllib.request.urlopen(r, timeout=60).read()) or {}).get("data") or {}
        if d.get("status") == "completed":
            os.makedirs(SALIDA, exist_ok=True)
            with urllib.request.urlopen(d["outputs"][0], timeout=240) as f:
                open(destino, "wb").write(f.read())
            print("  listo", destino)
            return
        if d.get("status") == "failed":
            raise RuntimeError(d.get("error"))
    raise RuntimeError("se acabó la espera")


if __name__ == "__main__":
    for n in (sys.argv[1:] or list(TOMAS)):
        print(n)
        try:
            haz(n)
        except Exception as e:
            print("  ERROR:", e)
