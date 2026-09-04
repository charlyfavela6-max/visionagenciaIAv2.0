#!/usr/bin/env python3
"""El logo de CAZA IMPRESOS, con GPT Image.

    python3 logo.py

El nombre juega con «caza» — se sale a buscar al cliente — y con «casa». La
marca tiene que verse de imprenta de barrio pero seria: la compite gente que
imprime desde un local sin logo, asi que tener uno ya es media venta.

Sale en PNG con fondo transparente para poder ponerlo sobre el flyer oscuro y
sobre papel blanco.
"""
import base64, json, os, time, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = "/workspaces/visionagenciaIAv2.0/VisionagenciaIAv2.0-main"
WS = "https://api.wavespeed.ai/api/v3"


def env(n):
    for l in open(os.path.join(RAIZ, ".env"), encoding="utf8", errors="replace"):
        if l.startswith(n + "="):
            return l.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


CAB = {"Authorization": "Bearer " + env("WAVESPEED_API_KEY"),
       "Content-Type": "application/json"}

PROMPT = (
    "A clean, modern LOGO for a printing shop called CAZA IMPRESOS. "
    "Flat vector logo on a PURE WHITE background, centred, with generous "
    "margin.\n\n"
    "Layout: a bold geometric emblem above, and under it the words "
    "'CAZA IMPRESOS' set in a heavy condensed sans-serif, all caps, tightly "
    "letterspaced.\n\n"
    "The emblem: a simple arrow head pointing up-right, cut out of a solid "
    "rounded square, drawn as if it were a sheet of paper folded at one "
    "corner — reading at once as an arrow and as a printed sheet. Two flat "
    "colours only: a deep INK BLUE (#123A63) and a warm RED-ORANGE (#E4552B). "
    "No gradients, no shadows, no 3D, no texture.\n\n"
    "Spelling exactly: C-A-Z-A  I-M-P-R-E-S-O-S. No other words, no tagline, "
    "no printer machine drawings, no ink drops, no clichés."
)


def pide(m, cuerpo):
    r = urllib.request.Request(WS + "/" + m, data=json.dumps(cuerpo).encode(), headers=CAB)
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
        "images": [],
        "aspect_ratio": "4:3",
        "output_format": "png"}) if False else pide(
        "openai/gpt-image-2/text-to-image",
        {"prompt": PROMPT, "aspect_ratio": "1:1", "output_format": "png"})
    for i, u in enumerate(espera(d["data"]["id"]), 1):
        p = os.path.join(AQUI, "logo_caza_v%d.png" % i)
        with urllib.request.urlopen(u, timeout=300) as r:
            open(p, "wb").write(r.read())
        print("listo", p)
