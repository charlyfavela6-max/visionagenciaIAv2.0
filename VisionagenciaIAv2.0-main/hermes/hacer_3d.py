#!/usr/bin/env python3
"""Manda imagenes a WaveSpeed y baja el mesh 3D con textura.

    python3 hermes/hacer_3d.py salida.glb foto_frente.png
    python3 hermes/hacer_3d.py salida.glb frente.png izq.png espalda.png der.png

Con UNA imagen usa `tripo3d/h3.1/image-to-3d` ($0.20); con dos a cuatro usa
`multiview-to-3d` ($0.10, la mitad, y con la espalda resuelta). El orden del
multiview lo fija la API: **frente, izquierda, espalda, derecha**, y el frente
es obligatorio.

Detalle que ahorra montar un servidor: **los endpoints de 3D SI aceptan data
URI**, aunque los de video no (eso es lo que dice el CLAUDE.md y sigue siendo
cierto para video). Aqui se manda la imagen en base64 y WaveSpeed la sube sola.

Tarda mucho: con `geometry_quality=detailed` fueron 14 minutos. Por eso el
sondeo es cada 20 s y no cada 2.
"""
import base64, json, os, sys, time, urllib.request

RAIZ = "/workspaces/visionagenciaIAv2.0/VisionagenciaIAv2.0-main"
WS = "https://api.wavespeed.ai/api/v3"


def llave():
    for l in open(os.path.join(RAIZ, ".env"), encoding="utf8", errors="replace"):
        if l.startswith("WAVESPEED_API_KEY="):
            return l.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("no encuentro WAVESPEED_API_KEY en .env")


def uri(ruta):
    tipo = "png" if ruta.lower().endswith(".png") else "jpeg"
    return "data:image/%s;base64,%s" % (
        tipo, base64.b64encode(open(ruta, "rb").read()).decode())


def pide(ruta, cuerpo):
    req = urllib.request.Request(
        WS + ruta, data=json.dumps(cuerpo).encode(),
        headers={"Authorization": "Bearer " + llave(),
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())


def estado(ident):
    req = urllib.request.Request(
        "%s/predictions/%s/result" % (WS, ident),
        headers={"Authorization": "Bearer " + llave()})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read()).get("data") or {}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    destino, imgs = sys.argv[1], sys.argv[2:]
    for i in imgs:
        if not os.path.exists(i):
            raise SystemExit("no existe: " + i)
    if len(imgs) > 4:
        raise SystemExit("como mucho 4 imagenes: frente, izquierda, espalda, derecha")

    comun = {"geometry_quality": "detailed", "pbr": True, "texture": True}
    if len(imgs) == 1:
        ruta, cuerpo = "/tripo3d/h3.1/image-to-3d", dict(comun, image=uri(imgs[0]),
                                                         orientation="align_image")
    else:
        ruta, cuerpo = "/tripo3d/h3.1/multiview-to-3d", dict(
            comun, images=[uri(i) for i in imgs])

    ident = (pide(ruta, cuerpo).get("data") or {}).get("id")
    print("trabajo %s (%s)" % (ident, ruta), flush=True)

    while True:
        d = estado(ident)
        if d.get("status") == "completed":
            break
        if d.get("status") == "failed":
            raise SystemExit("fallo: " + str(d.get("error")))
        print("  ...", d.get("status"), flush=True)
        time.sleep(20)

    url = (d.get("outputs") or [None])[0]
    if not url:
        raise SystemExit("termino sin salida: " + json.dumps(d)[:300])
    os.makedirs(os.path.dirname(os.path.abspath(destino)), exist_ok=True)
    with urllib.request.urlopen(url, timeout=600) as r:
        open(destino, "wb").write(r.read())
    print("%s  %.1f MB" % (destino, os.path.getsize(destino) / 1e6))
