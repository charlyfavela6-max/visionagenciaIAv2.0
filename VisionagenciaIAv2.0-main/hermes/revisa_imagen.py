#!/usr/bin/env python3
"""Le da imagenes a un modelo que VE y le pide que las compare.

    python3 hermes/revisa_imagen.py "<que preguntar>" img1.png [img2.png ...]

Por que existe y no se usa `hermes -z` a secas: Hermes toma imagenes por sus
herramientas, no por la linea de comandos, y para una revision suelta eso es dar
un rodeo. Esto habla directo con OpenRouter usando la MISMA llave y el MISMO
modelo que Hermes tiene de primario, asi que lo que conteste aqui es lo que
contestaria Hermes.

De los modelos gratis que responden, `minimax-m3` es **el unico que ve
imagenes**; `dots-3-note-preview` tambien pero es mas flojo. Los nemotron y el
ling son solo texto: a esos no tiene caso mandarles una foto.

Las imagenes se reducen a 1024 px de lado antes de mandarlas — una PNG de 2k en
base64 son varios MB y el modelo no necesita tanto para decir que esta mal.
"""
import base64, io, json, os, sys, urllib.request

MODELO = os.environ.get("REVISA_MODELO", "minimax/minimax-m3:free")
LADO = 1024


def llave():
    p = os.path.expanduser("~/.hermes/.env")
    for l in io.open(p, encoding="utf-8", errors="replace"):
        if l.startswith("OPENROUTER_API_KEY="):
            return l.split("=", 1)[1].strip()
    raise SystemExit("no encuentro OPENROUTER_API_KEY en ~/.hermes/.env")


def encoge(ruta):
    """A 1024 px de lado y a JPEG. Sin PIL tambien funciona: manda el original."""
    try:
        from PIL import Image
        im = Image.open(ruta).convert("RGB")
        im.thumbnail((LADO, LADO))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=88)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    except ImportError:
        crudo = open(ruta, "rb").read()
        tipo = "png" if ruta.lower().endswith(".png") else "jpeg"
        return "data:image/%s;base64,%s" % (tipo, base64.b64encode(crudo).decode())


def pregunta(texto, rutas, modelo=MODELO):
    partes = [{"type": "text", "text": texto}]
    for r in rutas:
        partes.append({"type": "text", "text": "\n[%s]" % os.path.basename(r)})
        partes.append({"type": "image_url", "image_url": {"url": encoge(r)}})
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps({"model": modelo,
                         "messages": [{"role": "user", "content": partes}],
                         "max_tokens": 1600}).encode(),
        headers={"Authorization": "Bearer " + llave(),
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.loads(r.read())
    if "error" in d:
        raise SystemExit("%s: %s" % (d["error"].get("code"), d["error"].get("message")))
    return d["choices"][0]["message"]["content"]


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    for r in sys.argv[2:]:
        if not os.path.exists(r):
            raise SystemExit("no existe: " + r)
    print(pregunta(sys.argv[1], sys.argv[2:]))
