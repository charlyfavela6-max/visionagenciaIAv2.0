#!/usr/bin/env python3
"""El flyer de VISION AGENCIA, en GPT Image.

    python3 flyer_agencia.py

Hermano del de Caza Impresos: mismo formato, misma logica. Pero aqui NO se
menciona imprenta ni se compara con nadie — son dos negocios y dos flyers.

EL ANGULO. El negocio chico no teme el precio, teme quedar amarrado. Por eso
el remate no es el precio: es «si algun dia te vas, te llevas el sistema».
Es la idea de Carlos y es lo unico que un competidor no puede copiar sin
destruirse.

EL TESTIMONIO. Va el de Angel (360 Salud Optima) porque es el unico real y
fuerte que hay en los chats — los demas clientes solo escriben «ok gracias».
"""
import base64, json, os, time, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = "/workspaces/visionagenciaIAv2.0/VisionagenciaIAv2.0-main"
WS = "https://api.wavespeed.ai/api/v3"
TEL = "631 247 0486"


def env(n):
    for l in open(os.path.join(RAIZ, ".env"), encoding="utf8", errors="replace"):
        if l.startswith(n + "="):
            return l.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


CAB = {"Authorization": "Bearer " + env("WAVESPEED_API_KEY"),
       "Content-Type": "application/json"}

PROMPT = (
    "Design a PRINT-READY advertising FLYER for a marketing agency, TALL "
    "VERTICAL half-letter format. Premium, confident, modern.\n\n"

    "PALETTE: a deep near-black INK background over the whole flyer, warm "
    "cream text, and one accent colour: a bright ELECTRIC BLUE. Generous "
    "margins, lots of breathing room. It must look expensive.\n\n"

    "LAYOUT, top to bottom:\n"
    "  1. At the top, centred, the wordmark 'VISIÓN AGENCIA' in a clean bold "
    "sans-serif, cream, with a small electric-blue geometric mark above it: a "
    "simple open eye formed by two arcs, drawn with thin lines.\n"
    "  2. A large three-line headline in heavy cream capitals:\n"
    "     'TU NEGOCIO,' / 'ANUNCIADO COMO' / 'MARCA GRANDE'\n"
    "     with the last line in ELECTRIC BLUE.\n"
    "  3. Under it, one line of smaller cream text: 'Videos, anuncios y diseño "
    "todos los meses. Sin contratar a nadie.'\n"
    "  4. FOUR services in a single column, each a thin electric-blue line "
    "icon on the left with a bold cream title and one small grey line under "
    "it:\n"
    "     VIDEOS PARA TUS REDES — 'Tú apareces, sin grabarte ni estudio' — "
    "icon: a play triangle inside a rounded rectangle\n"
    "     ANUNCIOS QUE SÍ VENDEN — 'Pensados para que te escriban' — icon: a "
    "small target with an arrow\n"
    "     DISEÑO CUANDO LO NECESITES — 'Sin cotizar cada vez' — icon: a "
    "pen nib\n"
    "     SABEMOS QUÉ FUNCIONÓ — 'Para no gastar a ciegas' — icon: a simple "
    "rising bar chart\n"
    "  5. A QUOTE BLOCK: a large cream quotation mark, then in italic cream "
    "text: 'Usted me tiene cautivado con su gran inteligencia.' and under it "
    "in small electric blue: 'Ángel · 360 Salud Óptima'\n"
    "  6. A bordered box outlined in ELECTRIC BLUE with cream text: "
    "'SI ALGÚN DÍA TE VAS, TE LLEVAS EL SISTEMA' in bold, and under it "
    "smaller: 'No te dejamos vendido. Te entregamos la forma de seguir "
    "produciendo tu contenido, sin volver a pagarle a nadie.'\n"
    "  7. At the bottom: 'PRIMER VIDEO GRATIS' in electric blue bold, then "
    "'WhatsApp " + TEL + "' large in cream.\n\n"

    "THE PHONE NUMBER IS EXACTLY: " + TEL + ". Check every digit. The agency "
    "name is exactly VISIÓN AGENCIA with an accent on the O.\n\n"

    "Flat vector print design, perfectly legible Spanish with correct "
    "accents. No photographs, no gradients, no 3D, no stock imagery, no "
    "watermark, no extra words, no prices."
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
    d = pide("openai/gpt-image-2/text-to-image",
             {"prompt": PROMPT, "aspect_ratio": "2:3", "output_format": "png"})
    for i, u in enumerate(espera(d["data"]["id"]), 1):
        p = os.path.join(AQUI, "VisionAgencia_flyer_v%d.png" % i)
        with urllib.request.urlopen(u, timeout=300) as r:
            open(p, "wb").write(r.read())
        print("listo", p)
