#!/usr/bin/env python3
"""El cake topper shaker de Erick, renderizado en GPT Image.

    python3 topper_erick_gpt.py [v1 v2 v3]

Esto NO sustituye al SVG de corte (`topper_erick_capas.svg`, ese es el que va a
Cricut). Esto es lo que Stefani le ENSEÑA a la mamá para aprobar: el topper como
se va a ver armado, con el brillo del foamy, las lentejuelas de verdad y el
palito.

Las dos referencias son las que ella mando el 2 sep 22:53:
  01 — letras acolchadas con pespunte blanco (el estilo de las letras)
  02 — topper redondo con ventana de lentejuelas (la forma y el armado)

La 02 dice «3 años» porque es de otro pedido: aqui va CUATRO. Es el error que
GPT Image copia si no se le grita, asi que el numero va repetido tres veces en
el prompt.

~$0.025 por imagen.
"""
import base64, json, os, sys, time, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = "/workspaces/visionagenciaIAv2.0/VisionagenciaIAv2.0-main"
REFS = os.path.join(AQUI, "..", "pedido_2sep")
WAVESPEED = "https://api.wavespeed.ai/api/v3"

LETRAS = os.path.join(REFS, "01_09-02_225343_image.jpg")   # el pespunte
FORMA = os.path.join(REFS, "02_09-02_225422_image.jpg")    # el shaker armado


def env(n):
    for l in open(os.path.join(RAIZ, ".env"), encoding="utf8", errors="replace"):
        if l.startswith(n + "="):
            return l.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get(n, "")


CAB = {"Authorization": "Bearer " + env("WAVESPEED_API_KEY"),
       "Content-Type": "application/json"}


def uri(ruta):
    tipo = "png" if ruta.lower().endswith(".png") else "jpeg"
    return "data:image/%s;base64,%s" % (
        tipo, base64.b64encode(open(ruta, "rb").read()).decode())


def pide(ruta, cuerpo):
    req = urllib.request.Request(WAVESPEED + "/" + ruta,
                                 data=json.dumps(cuerpo).encode(), headers=CAB)
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())


def espera(id_):
    for _ in range(180):
        time.sleep(2)
        req = urllib.request.Request("%s/predictions/%s/result" % (WAVESPEED, id_),
                                     headers=CAB)
        d = (json.loads(urllib.request.urlopen(req, timeout=60).read()) or {}).get("data") or {}
        if d.get("status") == "completed":
            return d["outputs"][0]
        if d.get("status") == "failed":
            raise RuntimeError("WaveSpeed fallo: %s" % d.get("error"))
    raise RuntimeError("se acabo la espera")


# ---------------------------------------------------------------- el prompt
# El NUMERO es lo unico que la referencia trae mal, asi que se repite.
NUMERO = (
    "The big number in the yellow starburst at the bottom MUST be the digit "
    "FOUR — 4 — because the boy turns four. NOT a three. Look at it again: it "
    "is a 4. The little banner under it reads 'años'. Anywhere a number "
    "appears large, it is 4."
)

BASE = (
    "A handmade layered CAKE TOPPER photographed straight on, product photo. "
    "Follow IMAGE 2 for the shape and the build, and IMAGE 1 for how the "
    "letters are made.\n\n"
    "THE BUILD, front to back:\n"
    "· A scalloped cloud-shaped plaque with a thick royal blue outline.\n"
    "· In the middle, a round SHAKER WINDOW: clear acetate over a cavity "
    "packed loose with colourful sequins, tiny flower confetti and small "
    "plastic alphabet letters and numbers in red, yellow, blue, green, purple "
    "and orange, scattered at random as if they really slid there.\n"
    "· Floating over the window, chunky glossy alphabet letters — A, B, C — "
    "and digits 1, 2, 3 in primary colours, plus a few five-point stars in "
    "yellow, blue, red, green and purple.\n"
    "· Across the centre, the name ERICK in large chunky rounded letters, one "
    "colour per letter: E red, r yellow, i green, c blue, k orange. Each "
    "letter sits on a white offset backing plate, exactly the layered look of "
    "IMAGE 1, with the soft puffy foam sheen and the fine WHITE DASHED "
    "STITCH line running just inside each letter.\n"
    "· At the bottom, a yellow starburst with the big number, and under it a "
    "small cream banner with 'años' in red, yellow, blue and green letters.\n"
    "· A round white wooden stick coming out of the bottom edge.\n\n"
    + NUMERO + "\n\n"
    "Spelling is exact: E-R-I-C-K. No other words, no watermark, no logo. "
    "Bright saturated primary palette, glossy craft foam and acrylic look, "
    "soft studio light, gentle drop shadows between the layers so the stack "
    "reads. TALL VERTICAL portrait format."
)

FONDOS = {
    "v1": "Plain pure WHITE seamless background, nothing else in frame.",
    "v2": "Set on top of a simple round birthday cake with white buttercream "
          "and a few coloured sprinkles, on a light table, softly blurred party "
          "background. The topper is in sharp focus and fills most of the frame.",
    "v3": "Plain BLACK seamless background, like the reference images, so the "
          "colours pop for the WhatsApp preview.",
}


def haz(cual):
    destino = os.path.join(AQUI, "topper_erick_gpt_%s.png" % cual)
    d = pide("openai/gpt-image-2/edit", {
        "prompt": BASE + " " + FONDOS[cual],
        "images": [uri(FORMA), uri(LETRAS)],
        "aspect_ratio": "2:3",
        "output_format": "png",
    })
    url = espera(d["data"]["id"])
    with urllib.request.urlopen(url, timeout=300) as r:
        open(destino, "wb").write(r.read())
    print("  listo", destino, flush=True)
    return destino


if __name__ == "__main__":
    for cual in (sys.argv[1:] or ["v1", "v2", "v3"]):
        print(cual, flush=True)
        haz(cual)
