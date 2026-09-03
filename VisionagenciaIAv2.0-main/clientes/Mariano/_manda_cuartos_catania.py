#!/usr/bin/env python3
"""Manda a Carlos los frames de los cuartos del recorrido de la Catania, para
que los vaya autorizando por WhatsApp antes de pasarlos a GPT Image.

    python3 clientes/Mariano/_manda_cuartos_catania.py            # todos
    python3 clientes/Mariano/_manda_cuartos_catania.py 13_estudio # sueltos

Mismo camino que `_manda_referencias_catania.py`: WAAPI, base64, a CARLOS_TEL.
Como la instancia ES el telefono de Carlos, todo le llega `fromMe`; por eso el
pie lleva la marca.
"""
import base64, json, os, sys, time, urllib.request

RAIZ = "/workspaces/visionagenciaIAv2.0/VisionagenciaIAv2.0-main"
DIR = os.path.join(RAIZ, "clientes/Mariano/referencias_3d/cuartos")
MARCA = "🏠 Catania · cuarto "


def env(n, x=""):
    for l in open(os.path.join(RAIZ, ".env"), encoding="utf8", errors="replace"):
        if l.startswith(n + "="):
            return l.split("=", 1)[1].strip().strip('"').strip("'")
    return x


TOKEN, INST = env("WAAPI_TOKEN"), env("WAAPI_INSTANCE")
CHAT = "".join(c for c in env("CARLOS_TEL", "5216312470486") if c.isdigit()) + "@c.us"
API = f"https://waapi.app/api/v1/instances/{INST}/client/action"

# nombre de archivo -> (frame, segundo, como se llama el cuarto)
CUARTOS = [
    ("01_establecimiento",      1,   "la casa desde fuera, el establecimiento"),
    ("02_cochera-2carros",      87,  "la cochera, entras y caben 2 carros"),
    ("03_subes-escalones",      191, "los escalones de la entrada"),
    ("04_sala-comedor",         224, "sala-comedor"),
    ("05_cocina",               255, "cocina"),
    ("06_hasta-arriba",         287, "el tiro hasta arriba"),
    ("07_puerta-abre",          325, "la puerta que abre"),
    ("08_roof-garden",          359, "roof garden"),
    ("09_recamara-principal",   479, "recámara principal"),
    ("10_vestidor-bano-propio", 505, "vestidor y baño propio"),
    ("11_piso-abajo-speedramp", 565, "bajada al piso de abajo"),
    ("12_dos-recamaras",        601, "las dos recámaras"),
    ("13_estudio",              637, "estudio"),
    ("14_cuarto-lavado",        668, "cuarto de lavado (el acercamiento)"),
    ("15_jardin",               714, "jardín"),
    ("16_nadie-te-ve",          791, "el patio donde nadie te ve"),
]

INTRO = (
    "🏠 Catania · los 16 cuartos del recorrido\n\n"
    "Frames sacados de tu Blender ahorita mismo, uno por cuarto, en el cuadro "
    "exacto en el que la cámara se para ahí.\n\n"
    "Contéstame sobre cada uno:\n"
    "  ✅ va — lo paso a GPT Image para el fotorrealista\n"
    "  ❌ no — dime qué le falta y lo reencuadro antes\n\n"
    "Van en 9:16 a 810x1440, que es el formato del video."
)


def pide(ruta, cuerpo, espera=240):
    req = urllib.request.Request(
        f"{API}/{ruta}", data=json.dumps(cuerpo).encode(),
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=espera) as r:
        return json.loads(r.read())


def manda(nombre, frame, seg, pie):
    ruta = os.path.join(DIR, nombre + ".png")
    r = pide("send-media", {
        "chatId": CHAT,
        "mediaBase64": base64.b64encode(open(ruta, "rb").read()).decode(),
        "mediaName": nombre + ".png",
        "mediaCaption": f"{MARCA}{pie}  ·  f{frame} ({seg:.1f} s)",
    })
    return (r.get("data") or {}).get("status") or r.get("status") or "?"


if __name__ == "__main__":
    solo = sys.argv[1:]
    print("chat:", CHAT)
    if not solo:
        pide("send-message", {"chatId": CHAT, "message": INTRO})
        time.sleep(2)
    for nombre, frame, pie in CUARTOS:
        if solo and nombre not in solo:
            continue
        ruta = os.path.join(DIR, nombre + ".png")
        if not os.path.exists(ruta):
            print(f"  {nombre:26} SIN ARCHIVO todavía")
            continue
        try:
            kb = os.path.getsize(ruta) // 1024
            est = manda(nombre, frame, frame / 24.0, pie)
            print(f"  {nombre:26} f{frame:<5} {kb:5} KB  {est}")
        except Exception as e:
            print(f"  {nombre:26} FALLO {str(e)[:80]}")
        time.sleep(2.5)
