#!/usr/bin/env python3
"""Revisa cuarto por cuarto que la imagen NO se haya despegado del modelo.

    python3 revisa_cuartos.py              # califica y saca la hoja de contacto
    python3 revisa_cuartos.py --rehacer    # y vuelve a pedir los que reprueban

QUE MIDE, y por que
-------------------
Mirarlas de a una es lento y se cuela lo obvio. Aqui van dos numeros duros:

1. ESTRUCTURA (`estruct`). El pase `<cuarto>_aristas.png` es el plano de lineas
   que salio de Blender: ahi estan los muros, las ventanas y las orillas de los
   muebles donde de verdad van. A la imagen generada se le saca su propio mapa
   de bordes y se pregunta **que tanto de la linea de Blender cayo encima de
   una linea de la imagen** (con 3 px de tolerancia, que es lo que se mueve un
   borde al pintarlo).

   Si la IA movio un muro o reencuadro, este numero se desploma. Es la misma
   falla que tenia seedream con la casa entera, pero medida en vez de opinada.

2. SIN PINTAR (`plano`). El sintoma clasico: deja cajas grises sin material.
   Se cuenta la fraccion de pixeles con saturacion casi nula Y vecindario liso
   — o sea gris parejo. Una foto de verdad casi no tiene de eso.

APRUEBA con estruct >= 0.55 y plano <= 0.12. Los umbrales salieron de comparar
`casa_nanobanana_v1` (que respeto la planta) contra `casa_seedream_v2` (que se
invento otra casa).

La hoja de contacto `_hoja_cuartos.jpg` deja el gris, las lineas y las dos
versiones lado a lado, para el ojo, que sigue siendo el ultimo juez.
"""
import os
import subprocess
import sys

from PIL import Image, ImageChops, ImageFilter

AQUI = os.path.dirname(os.path.abspath(__file__))
CAM = os.path.join(AQUI, "cuartos_cam")
NB = os.path.join(AQUI, "cuartos_nb")
MIN_ESTRUCT = 0.55
MAX_PLANO = 0.12


def bordes(im, umbral=60):
    """Mapa de bordes en blanco y negro, del tamano dado."""
    g = im.convert("L").filter(ImageFilter.FIND_EDGES)
    return g.point(lambda v: 255 if v > umbral else 0)


def estructura(aristas, generada):
    """Que fraccion de la linea de Blender cayo sobre una linea de la imagen."""
    n = (768, 1365)
    # el pase de aristas es linea NEGRA sobre blanco: se invierte
    ref = ImageChops.invert(aristas.convert("L").resize(n, Image.LANCZOS))
    ref = ref.point(lambda v: 255 if v > 40 else 0)
    gen = bordes(generada.resize(n, Image.LANCZOS))
    # se engorda la de la imagen 3 px: al pintar, un borde se mueve un poco
    gen = gen.filter(ImageFilter.MaxFilter(7))
    r, g = ref.load(), gen.load()
    total = coinciden = 0
    for y in range(0, n[1], 2):
        for x in range(0, n[0], 2):
            if r[x, y]:
                total += 1
                if g[x, y]:
                    coinciden += 1
    return (coinciden / total) if total else 0.0


def sin_pintar(im):
    """Fraccion de la imagen que es gris parejo — cajas sin material."""
    n = (384, 682)
    ch = im.convert("RGB").resize(n, Image.LANCZOS)
    hsv = ch.convert("HSV")
    liso = ch.filter(ImageFilter.FIND_EDGES).convert("L")
    h, l = hsv.load(), liso.load()
    malos = 0
    for y in range(n[1]):
        for x in range(n[0]):
            s = h[x, y][1]
            if s < 22 and l[x, y] < 14:
                malos += 1
    return malos / (n[0] * n[1])


def califica(cuarto):
    aris = os.path.join(CAM, cuarto + "_aristas.png")
    if not os.path.exists(aris):
        return None
    a = Image.open(aris)
    filas = []
    for v in (1, 2):
        p = os.path.join(NB, "%s_v%d.png" % (cuarto, v))
        if not os.path.exists(p):
            continue
        im = Image.open(p)
        filas.append((v, round(estructura(a, im), 3), round(sin_pintar(im), 3), p))
    return filas


def hoja(resultados):
    w, h = 300, 533
    filas = [r for r in resultados if r[1]]
    hoja = Image.new("RGB", (w * 4, h * len(filas) + 26 * len(filas)), "white")
    from PIL import ImageDraw, ImageFont
    d = ImageDraw.Draw(hoja)
    fu = ImageFont.truetype(
        "/workspaces/visionagenciaIAv2.0/VisionagenciaIAv2.0-main/fonts/Montserrat-Medium.ttf", 15)
    for k, (cuarto, notas) in enumerate(filas):
        y = k * (h + 26)
        for i, p in enumerate((os.path.join(CAM, cuarto + "_gris.png"),
                               os.path.join(CAM, cuarto + "_aristas.png"))):
            if os.path.exists(p):
                hoja.paste(Image.open(p).convert("RGB").resize((w, h)), (i * w, y + 26))
        for i, (v, e, pl, p) in enumerate(notas[:2]):
            hoja.paste(Image.open(p).convert("RGB").resize((w, h)), ((2 + i) * w, y + 26))
            d.text(((2 + i) * w + 6, y + 6),
                   "v%d  estruct %.2f  plano %.2f  %s" % (v, e, pl,
                        "OK" if (e >= MIN_ESTRUCT and pl <= MAX_PLANO) else "REPRUEBA"),
                   font=fu, fill="black")
        d.text((6, y + 6), cuarto, font=fu, fill="black")
    salida = os.path.join(AQUI, "_hoja_cuartos.jpg")
    hoja.save(salida, quality=85)
    return salida


if __name__ == "__main__":
    sys.path.insert(0, AQUI)
    from cuartos_nanobanana import CUARTOS

    resultados, reprueban = [], []
    for c in CUARTOS:
        notas = califica(c)
        resultados.append((c, notas))
        if not notas:
            print("  %-18s sin imagen todavia" % c)
            continue
        mejor = max(notas, key=lambda n: n[1] - n[2])
        ok = mejor[1] >= MIN_ESTRUCT and mejor[2] <= MAX_PLANO
        print("  %-18s mejor v%d · estructura %.2f · sin pintar %.2f  %s"
              % (c, mejor[0], mejor[1], mejor[2], "OK" if ok else "<<< REPRUEBA"))
        if not ok:
            reprueban.append(c)

    if any(n for _, n in resultados):
        print("\nhoja de contacto:", hoja(resultados))
    if reprueban:
        print("\nreprueban: " + ", ".join(reprueban))
        if "--rehacer" in sys.argv:
            for c in reprueban:
                for v in (1, 2):
                    p = os.path.join(NB, "%s_v%d.png" % (c, v))
                    if os.path.exists(p):
                        os.rename(p, p.replace(".png", "_rechazada.png"))
            subprocess.run([sys.executable,
                            os.path.join(AQUI, "cuartos_nanobanana.py")] + reprueban)
