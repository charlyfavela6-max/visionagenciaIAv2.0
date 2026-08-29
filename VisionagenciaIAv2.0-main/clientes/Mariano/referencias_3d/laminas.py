"""Laminas de referencia: cada frame del recorrido real, etiquetado con el
punto de la spline 3D al que le toca."""
import glob, os, sys
from PIL import Image, ImageDraw, ImageFont

ESC = "/workspaces/visionagenciaIAv2.0/VisionagenciaIAv2.0-main/clientes/Mariano/escenas_wa"
SAL = sys.argv[1]
TTF = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def f(px): return ImageFont.truetype(TTF, px)


# (numero de escena, cuarto en el 3D, segundo del recorrido)
CATANIA = [
    ("10", "FACHADA", "t 0.0 s · establecimiento"),
    ("14", "ESCALERA", "t 7.9 y 23.5 s"),
    ("15", "SALA", "t 9.3 s · sala-comedor"),
    ("18", "ESTANCIA TV", "t 9.3 s · sala-comedor"),
    ("17", "ROOF GARDEN", "t 14.9 s · ya se ve el mar"),
    ("12", "RECAMARA PRINCIPAL",             "t 19.9 s"),
    ("11", "VESTIDOR",                       "t 21.0 s"),
    ("13", "RECAMARA ventanal", "t 25.0 s"),
    ("19", "SEGUNDA RECAMARA",               "t 25.0 s"),
    ("16", "JARDIN", "t 29.7 y 32.9 s"),
]
OTROS = [
    ("04", "COCINA (Siena)", "t 10.6 s · falta en Catania"),
    ("05", "BANO (Siena)", "t 21.0 s · mismo acabado"),
    ("07", "PASILLO (Siena)", "t 13.5 s · puerta-abre"),
    ("26", "ESCALERA (Brescia)",             "t 7.9 / 23.5 s"),
    ("27", "SALA (Brescia)",                 "t 9.3 s"),
    ("23", "AZOTEA / lavado", "t 27.8 s"),
    ("28", "FACHADA + MAR", "el remate, como se ve real"),
]


def lamina(items, titulo, salida, cols=5):
    W, H, PIE = 300, 534, 78
    filas = (len(items) + cols - 1) // cols
    im = Image.new("RGB", (W * cols, 92 + filas * (H + PIE)), (16, 16, 16))
    d = ImageDraw.Draw(im)
    d.text((22, 22), titulo, fill=(255, 220, 0), font=f(38))
    d.text((22, 64), "numero = clip que mando Mariano · abajo, el punto del recorrido 3D",
           fill=(190, 190, 190), font=f(20))
    for i, (num, cuarto, cuando) in enumerate(items):
        arch = sorted(glob.glob(os.path.join(ESC, num + "_*.jpg")))
        if not arch:
            continue
        foto = Image.open(arch[0]).resize((W - 10, H - 10))
        x = (i % cols) * W + 5
        y = 92 + (i // cols) * (H + PIE) + 5
        im.paste(foto, (x, y))
        d.text((x + 10, y + 8), num, fill=(255, 230, 0), font=f(34),
               stroke_width=3, stroke_fill=(0, 0, 0))
        d.text((x, y + H), cuarto, fill=(255, 255, 255), font=f(19))
        d.text((x, y + H + 28), cuando, fill=(120, 220, 255), font=f(20))
    im.save(salida, quality=86)
    return salida, im.size


print(lamina(CATANIA, "CATANIA — referencia por cuarto (clips de Mariano)",
             SAL + "/ref_1_catania_por_cuarto.jpg"))
print(lamina(OTROS, "LO QUE FALTA EN CATANIA — otros modelos",
             SAL + "/ref_2_faltantes_otros_modelos.jpg", cols=4))
