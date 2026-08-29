"""Lamina 'todos los cuartos': las tres plantas del 3D vistas desde arriba,
con el nombre de cada cuarto y, debajo de cada planta, los clips reales de
Mariano que le corresponden."""
import glob, os, sys
from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
ESC = os.path.join(os.path.dirname(AQUI), "escenas_wa")
PLANTAS = sys.argv[1]                      # carpeta con planta_pa/pb/n1.png
SALIDA = sys.argv[2]
TTF = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
TTF_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# La camara del render: ortografica, cenital, centro (4.0, 13.0), 14.04 m de
# alto en 1280 px. Con eso se pasa de metros de escena a pixeles del panel.
PXM = 1280 / 14.04
CX, CY = 4.0, 13.0
W, H = 620, 1280
REC_ARR, REC_ABA = 292, 34          # aire negro que se recorta arriba y abajo
HP = H - REC_ARR - REC_ABA


def px(x, y):
    return (x - CX) * PXM + W / 2, H / 2 - (y - CY) * PXM - REC_ARR


def f(n, r=False):
    return ImageFont.truetype(TTF_R if r else TTF, n)


# (nivel, titulo, [(cuarto, x_escena, y_escena)], [(clip, pie)])
NIVELES = [
    ("pa", "PLANTA DE ACCESO", "se entra de la calle · z +2.8 m",
     [("SALA", 3.5, 11.2), ("COMEDOR", 5.7, 10.3), ("COCINA", 1.9, 8.6),
      ("ROOF GARDEN", 4.0, 14.3)],
     [("15", "SALA"), ("04", "COCINA (Siena)"), ("17", "ROOF GARDEN"),
      ("14", "ESCALERA")]),
    ("pb", "NIVEL INTERMEDIO", "recamara principal · z -0.15 m",
     [("RECAMARA PRINCIPAL", 2.6, 14.2), ("VESTIDOR", 6.5, 11.9),
      ("BANO PPAL", 5.3, 14.1), ("ESTANCIA TV", 2.3, 8.6),
      ("ESCALERA", 6.2, 8.3)],
     [("12", "RECAMARA PPAL"), ("11", "VESTIDOR"), ("18", "ESTANCIA TV"),
      ("05", "BANO (Siena)")]),
    ("n1", "NIVEL JARDIN", "dos recamaras y estudio · z -3.77 m",
     [("RECAMARA 2", 2.4, 14.4), ("LAVADO", 5.4, 14.9),
      ("ESTUDIO", 5.8, 11.9), ("BANO", 1.7, 11.2),
      ("RECAMARA 3", 2.4, 8.3), ("ESCALERA", 6.2, 8.3),
      ("JARDIN", 4.0, 16.7)],
     [("13", "RECAMARA 2"), ("19", "RECAMARA 3"),
      ("23", "LAVADO"), ("16", "JARDIN")]),
]

FOTO_W, FOTO_H, GAP = 145, 258, 12
MARGEN, HUECO = 40, 26
CAB = 150
TIT_P = 62
PIE_F = 46

ANCHO = MARGEN * 2 + W * 3 + HUECO * 2
ALTO = CAB + TIT_P + HP + 34 + FOTO_H + PIE_F + MARGEN

im = Image.new("RGB", (ANCHO, ALTO), (16, 16, 16))
d = ImageDraw.Draw(im)
d.text((MARGEN, 30), "CATANIA — todos los cuartos, planta por planta",
       fill=(255, 220, 0), font=f(46))
d.text((MARGEN, 84),
       "corte cenital del 3D · los muebles llevan los colores sacados de los "
       "clips reales de Mariano · abajo, la foto real de cada planta",
       fill=(190, 190, 190), font=f(21, r=True))

for i, (niv, titulo, sub, cuartos, clips) in enumerate(NIVELES):
    x0 = MARGEN + i * (W + HUECO)
    d.text((x0, CAB), titulo, fill=(255, 255, 255), font=f(30))
    d.text((x0, CAB + 34), sub, fill=(120, 220, 255), font=f(20, r=True))

    panel = Image.new("RGB", (W, H), (26, 26, 26))
    plano = Image.open(os.path.join(PLANTAS, "planta_%s.png" % niv)).convert("RGBA")
    panel.paste(plano, (0, 0), plano)
    panel = panel.crop((0, REC_ARR, W, H - REC_ABA))
    y0 = CAB + TIT_P
    im.paste(panel, (x0, y0))
    d.rectangle([x0, y0, x0 + W - 1, y0 + HP - 1], outline=(70, 70, 70))

    for nombre, mx, my in cuartos:
        cx, cy = px(mx, my)
        d.text((x0 + cx, y0 + cy), nombre, fill=(255, 255, 255), font=f(19),
               anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))

    yf = y0 + HP + 34
    d.text((x0, yf - 28), "las fotos reales de esta planta", fill=(150, 150, 150),
           font=f(18, r=True))
    for j, (num, pie) in enumerate(clips):
        arch = sorted(glob.glob(os.path.join(ESC, num + "_*.jpg")))
        if not arch:
            continue
        foto = Image.open(arch[0]).resize((FOTO_W, FOTO_H))
        fx = x0 + j * (FOTO_W + GAP)
        im.paste(foto, (fx, yf))
        d.text((fx + 7, yf + 6), num, fill=(255, 230, 0), font=f(26),
               stroke_width=3, stroke_fill=(0, 0, 0))
        d.text((fx, yf + FOTO_H + 8), pie, fill=(230, 230, 230), font=f(16))

im.save(SALIDA, quality=90)
print(SALIDA, im.size)
