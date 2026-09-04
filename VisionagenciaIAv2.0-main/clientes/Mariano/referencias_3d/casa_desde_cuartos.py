#!/usr/bin/env python3
"""La casa entera en corte, vestida con LAS IMAGENES DE SUS PROPIOS CUARTOS.

    python3 casa_desde_cuartos.py [salida.png]

EL PASO QUE FALTABA
-------------------
`casa_nanobanana.py` le daba a la IA fotos sueltas del video: buenas para el
color, pero de otro angulo y de otra luz, asi que cada cuarto lo resolvia a su
manera y varios quedaban a medio terminar.

Aqui las referencias ya no son fotos: son **los cuartos de ESTA casa ya
resueltos** por `cuartos_nanobanana.py`, cada uno calzado a su propio cuadro de
Blender y aprobado por `revisa_cuartos.py`. La IA ya no tiene que inventar como
se ve la recamara — la esta viendo, en su sitio y con su luz.

Se mandan OCHO imagenes, que es el techo del proveedor (con 14 rechaza la
peticion aunque vayan reducidas):

  1. `corte/corte_gris.png`    — el volumen, del Blender de Carlos
  2. `corte/corte_aristas.png` — la estructura, que es la ley
  3-8. los seis cuartos que de verdad se ven en el corte

$0.07 y devuelve dos.
"""
import base64, io, json, os, sys, time, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = "/workspaces/visionagenciaIAv2.0/VisionagenciaIAv2.0-main"
CORTE = os.path.join(AQUI, "corte")
NB = os.path.join(AQUI, "cuartos_nb")
WAVESPEED = "https://api.wavespeed.ai/api/v3"
MODELO = "google/nano-banana-pro/edit-multi"

# Los seis que se ven en el corte, y donde caen en el cuadro. El orden es el
# que nombra el prompt.
CUARTOS = [
    ("n1_recamara2",     "the FRONT bedroom on the LOWEST floor"),
    ("n1_recamara1",     "the BACK bedroom on the LOWEST floor"),
    ("pb_sala",          "the LIVING ROOM on the MIDDLE floor, with the slatted wood wall"),
    ("pb_recamara_ppal", "the MASTER BEDROOM on the MIDDLE floor, with the arched "
                         "tufted headboard against the chocolate wall"),
    ("pa_comedor",       "the DINING and KITCHEN area on the TOP floor"),
    ("rg_terraza",       "the open ROOF TERRACE on the TOP floor, with the concrete "
                         "planters full of green plants"),
]

PROMPT = (
    "Make ONE photorealistic architectural CUTAWAY photograph of this whole "
    "three-storey house — a doll's-house view with the near side wall removed, "
    "every floor open and visible at once, fully furnished and finished.\n\n"

    "IMAGE 1 is the grey 3D render and IMAGE 2 is its line drawing. TOGETHER "
    "THEY ARE THE LAW:\n"
    "  · Keep the CAMERA exactly — same angle, same height, same lens. Do not "
    "re-frame, do not re-centre, do not zoom in.\n"
    "  · Keep every floor slab, every wall and every opening exactly where the "
    "line drawing puts them. Do not add or remove a wall, do not invent a "
    "courtyard, do not move the stair.\n"
    "  · Keep every piece of furniture in its exact place and at its exact "
    "size. You are painting what is modelled, not redecorating.\n"
    "  · Three floors. THE ROOF TERRACE IS NOT A FOURTH FLOOR: it is the open, "
    "uncovered part of the TOP floor, on the same slab as the kitchen and "
    "dining.\n\n"

    "THE REMAINING IMAGES ARE THE ROOMS OF THIS VERY HOUSE, already finished. "
    "They are not mood boards — each one is that exact room, seen from inside. "
    "Reproduce each room in the cutaway with the materials, colours, furniture "
    "and light of its own image:\n{lista}\n\n"

    "Everywhere: big BEIGE floor tiles, smooth white plaster walls (flat "
    "plaster and concrete, never rough limestone or textured stucco), "
    "black-framed windows, thin black metal railings, warm daylight.\n\n"

    "FINISH THE WHOLE PICTURE. No room left as a white blocky model, no piece "
    "of furniture left as a plain grey box. No text, no watermark, no people."
)


def env(n):
    for l in open(os.path.join(RAIZ, ".env"), encoding="utf8", errors="replace"):
        if l.startswith(n + "="):
            return l.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get(n, "")


CAB = {"Authorization": "Bearer " + env("WAVESPEED_API_KEY"),
       "Content-Type": "application/json"}


def uri(ruta):
    from PIL import Image
    im = Image.open(ruta).convert("RGB")
    im.thumbnail((1024, 1024), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, "JPEG", quality=88)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


def pide(m, cuerpo):
    req = urllib.request.Request(WAVESPEED + "/" + m,
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
            raise RuntimeError(d.get("error"))
    raise RuntimeError("se acabo la espera")


def mejor(cuarto):
    """La version aprobada del cuarto; si hay dos, la v1."""
    for v in (1, 2):
        p = os.path.join(NB, "%s_v%d.png" % (cuarto, v))
        if os.path.exists(p):
            return p
    return None


if __name__ == "__main__":
    imgs = [os.path.join(CORTE, "corte_gris.png"),
            os.path.join(CORTE, "corte_aristas.png")]
    lista, faltan = [], []
    n = 3
    for c, que in CUARTOS:
        p = mejor(c)
        if p is None:
            faltan.append(c)
            continue
        imgs.append(p)
        lista.append("  · IMAGE %d is %s." % (n, que))
        n += 1
    if faltan:
        print("ojo, sin imagen todavia:", ", ".join(faltan))
    imgs = imgs[:8]

    print("mandando %d imagenes" % len(imgs), flush=True)
    d = pide(MODELO, {"prompt": PROMPT.format(lista="\n".join(lista)),
                      "images": [uri(i) for i in imgs],
                      "aspect_ratio": "4:3",
                      "output_format": "png"})
    urls = espera(d["data"]["id"])
    base = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, "casa_desde_cuartos")
    base = base[:-4] if base.endswith(".png") else base
    for i, u in enumerate(urls, 1):
        destino = "%s_v%d.png" % (base, i)
        with urllib.request.urlopen(u, timeout=300) as r:
            open(destino, "wb").write(r.read())
        print("listo", destino, flush=True)
