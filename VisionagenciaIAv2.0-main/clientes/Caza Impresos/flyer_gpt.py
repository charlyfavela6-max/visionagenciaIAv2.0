#!/usr/bin/env python3
"""El flyer de CAZA IMPRESOS hecho en GPT Image, con el logo de referencia.

    python3 flyer_gpt.py

A diferencia del de PIL, aqui el ARTE lo pone la IA: fondo, formas, iconos y
jerarquia. Se le manda el logo para que respete la marca y los colores.

OJO CON EL TEXTO: son ocho servicios, un telefono y varias frases. GPT Image
deforma letras cuando hay mucho texto chico, asi que el telefono y el nombre
van repetidos en el prompt y despues se revisan. Si sale mal una palabra, la
version de PIL (`flyer.py`) sigue siendo la que se manda a imprenta.
"""
import base64, json, os, time, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = "/workspaces/visionagenciaIAv2.0/VisionagenciaIAv2.0-main"
WS = "https://api.wavespeed.ai/api/v3"
TEL = "631 130 1667"


def env(n):
    for l in open(os.path.join(RAIZ, ".env"), encoding="utf8", errors="replace"):
        if l.startswith(n + "="):
            return l.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


CAB = {"Authorization": "Bearer " + env("WAVESPEED_API_KEY"),
       "Content-Type": "application/json"}


def uri(ruta):
    from PIL import Image
    import io
    im = Image.open(ruta).convert("RGB")
    im.thumbnail((1024, 1024))
    b = io.BytesIO()
    im.save(b, "JPEG", quality=90)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


# LA VERSION PARA IMPRESIONAR. La primera cumplia; esta tiene que verse como
# el volante de una imprenta que ya la hizo, no de una que empieza. Tres cosas
# la suben de nivel:
#   · una FOTO de los impresos de verdad arriba, no puros iconos — el que
#     compra impresion quiere ver papel;
#   · JERARQUIA: un solo mensaje manda y el resto se subordina;
#   · el remate del mismo dia, que es lo unico que la competencia no promete.
PROMPT = (
    "Design a PREMIUM print advertising FLYER for a printing shop, TALL "
    "VERTICAL half-letter format. It must look like the flyer of an "
    "established print house, not a startup.\n\n"

    "IMAGE 1 is the shop LOGO — reproduce it faithfully and take the palette "
    "from it: deep INK BLUE (#123A63) and warm RED-ORANGE (#E4552B).\n\n"

    "STRUCTURE, top to bottom:\n"
    "  1. TOP THIRD — a rich photographic hero shot, warm and softly lit, "
    "shot slightly from above on a dark wood surface: a neat arrangement of "
    "REAL PRINTED GOODS — a stack of crisp business cards fanned out, a "
    "wooden-handled rubber stamp resting on its pad, a roll of white labels "
    "partly unrolled, a folded flyer and a receipt book. Shallow depth of "
    "field, soft shadows, a little warm light from the left. Photorealistic, "
    "premium, like a stationery catalogue cover. The LOGO sits over this in "
    "the top-left corner, small, in cream.\n"
    "  2. Immediately under the photo, a solid DEEP BLUE band with one line "
    "of large cream capitals: 'IMPRENTA CAZA'\n"
    "  3. On warm off-white paper, a big two-line headline in heavy blue "
    "capitals: 'TODO LO QUE TU NEGOCIO' / 'NECESITA IMPRESO', with a short "
    "thick orange rule under it.\n"
    "  4. The eight services as a clean two-column list — each a bold small "
    "blue title with a thin grey description under it, separated by hairline "
    "grey rules. NO icons, just beautiful typography:\n"
    "     SELLOS · de goma y automáticos\n"
    "     TARJETAS · de presentación\n"
    "     VOLANTES · para repartir\n"
    "     LONAS · de cualquier medida\n"
    "     LETREROS · preventivos y de seguridad\n"
    "     ETIQUETAS · de rollo y sueltas\n"
    "     NOTAS DE VENTA · y recibos foliados\n"
    "     PAPELERÍA · hojas, sobres, folders\n"
    "  5. A wide ORANGE band with cream text, bold and centred: "
    "'EL DISEÑO VA INCLUIDO' and under it smaller: 'Tú nos dices qué "
    "necesitas. Nosotros lo diseñamos y lo imprimimos.'\n"
    "  6. Bottom: 'COTIZA HOY' in small grey caps, then '631 130 1667' very "
    "large in deep blue, then 'Te decimos precio el mismo día' in small "
    "orange.\n\n"

    "THE PHONE NUMBER IS EXACTLY: 631 130 1667. Check every digit. The name "
    "is exactly CAZA IMPRESOS.\n\n"

    "Editorial, elegant, generous margins, confident typography, warm paper "
    "tone. Perfect Spanish with correct accents. No watermark, no extra "
    "words, no printer machines, no clip art.\n\n"

    "CRITICAL — DELIVER THE ARTWORK FLAT. The first attempt came back as a "
    "photo of the flyer leaning against a wall, tilted and cropped. Do NOT do "
    "that. Output ONLY the flat artwork: perfectly straight-on, no "
    "perspective, no tilt, no mockup, no wall, no floor, no shadow of the "
    "sheet, no hand holding it. The design fills the ENTIRE frame edge to "
    "edge, like a PDF page exported for print. Every line of text fully "
    "inside the frame — nothing cropped at the right edge."
)


def pide(m, c):
    r = urllib.request.Request(WS + "/" + m, data=json.dumps(c).encode(), headers=CAB)
    with urllib.request.urlopen(r, timeout=300) as x:
        return json.loads(x.read())


def espera(i):
    for _ in range(200):
        time.sleep(3)
        r = urllib.request.Request("%s/predictions/%s/result" % (WS, i), headers=CAB)
        d = (json.loads(urllib.request.urlopen(r, timeout=60).read()) or {}).get("data") or {}
        if d.get("status") == "completed":
            return d["outputs"]
        if d.get("status") == "failed":
            raise RuntimeError(d.get("error"))
    raise RuntimeError("timeout")


if __name__ == "__main__":
    d = pide("google/nano-banana-pro/edit-multi", {
        "prompt": PROMPT,
        "images": [uri(os.path.join(AQUI, "logo_caza_v1.png"))],
        "aspect_ratio": "2:3",
        "output_format": "png"})
    for i, u in enumerate(espera(d["data"]["id"]), 1):
        p = os.path.join(AQUI, "CazaImpresos_flyer_PRO2_v%d.png" % i)
        with urllib.request.urlopen(u, timeout=300) as r:
            open(p, "wb").write(r.read())
        print("listo", p)
