#!/usr/bin/env python3
"""Genera una pose de Carlos corriendo, usando el character sheet como referencia
de identidad (mismo rostro, complexión, tatuajes) para el reel de IG sobre
medicina + correr como la forma de convertir el ruido en ideas claras.

Costo: ~$0.11 la imagen (gpt-image-2/edit).
Correr:  python3 "clientes/Vision Agencia/carlos_running_v1.py"
"""
import base64
import hashlib
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

BASE = "https://api.wavespeed.ai/api/v3"
MODELO = "openai/gpt-image-2/edit"
CARPETA = Path(__file__).resolve().parent
REF = CARPETA / "CARLOS_CHARACTER_SHEET.png"
SALIDA = CARPETA / "carlos_running_v1.png"

PROMPT = """Using this character sheet as the identity reference, generate a NEW photorealistic
candid photo of the SAME man — same face, same beard, same hair, same build, same skin tone,
same tattoos on his forearm — but now RUNNING outdoors, mid-stride, full sprint action pose,
captured like a real photo, not a studio shot.

SHOT ON A SMARTPHONE, candid documentary photograph — absolutely NOT a studio portrait, NOT a
3D render, NOT stock. 26mm lens, slight barrel distortion, wide DoF, chromatic aberration,
luminance grain, phone processing halo. Early morning light, low golden sun behind him,
long soft shadows on the ground, slight lens flare. Open road or park path, empty and quiet,
suggesting clarity and calm after mental noise.

He wears simple black running gear (fitted black t-shirt, black joggers or shorts, running
shoes) — NOT the suit, NOT the black t-shirt/jeans from the sheet. His body is captured mid-run:
one knee driving up, arms bent and swinging naturally, torso leaning slightly forward, focused
determined expression, slightly out of breath. Motion energy in the pose, but the image itself
is sharp (fast shutter, no motion blur smear).

Visible pores, sebum sheen from exertion, natural sweat on forehead and neck, uneven skin tone,
loose hairs moving with the motion. Never smooth, waxy or airbrushed. Slightly desaturated,
like an unedited phone photo, natural film-like contrast, no HDR.

TALL VERTICAL 9:16 PORTRAIT ORIENTATION, much taller than wide. Full body visible, running
directly across the frame or angled toward camera."""


def dataurl(p: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()


def pide(url, cuerpo=None, llave=""):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    r = urllib.request.Request(url, data=datos, method="POST" if datos else "GET",
                               headers={"Authorization": f"Bearer {llave}",
                                        "Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=180) as resp:
        return json.loads(resp.read())


def main():
    llave = os.environ.get("WAVESPEED_API_KEY", "").strip()
    if not llave:
        sys.exit("falta WAVESPEED_API_KEY (¿cargaste .env?)")
    if not REF.exists():
        sys.exit(f"no está la referencia: {REF}")

    cuerpo = {
        "images": [dataurl(REF)],
        "prompt": PROMPT,
        "size": "1024*1536",
        "quality": "high",
    }
    print(f"pidiendo a {MODELO} …  (~$0.11)")
    r = pide(f"{BASE}/{MODELO}", cuerpo, llave)
    jid = r["data"]["id"]
    print("  job:", jid)

    for i in range(120):
        time.sleep(4)
        s = pide(f"{BASE}/predictions/{jid}/result", None, llave)["data"]
        est = s.get("status")
        if est == "completed":
            salida = s["outputs"][0]
            print("  listo:", salida)
            with urllib.request.urlopen(salida, timeout=180) as resp:
                SALIDA.write_bytes(resp.read())
            print(f"  guardado: {SALIDA}")
            print(f"  md5: {hashlib.md5(SALIDA.read_bytes()).hexdigest()}")
            return
        if est == "failed":
            sys.exit(f"falló: {s.get('error')}")
        print(f"  … {est} ({(i+1)*4}s)")
    sys.exit("se acabó el tiempo")


if __name__ == "__main__":
    main()
