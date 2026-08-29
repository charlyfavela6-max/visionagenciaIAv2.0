"""Serie satelital del alejamiento de la Catania hacia el Pacifico.

Sin llave de Google en .env, asi que se usan los tiles publicos de Esri World
Imagery (mismo satelite que se ve en muchos visores). Cada imagen sale centrada
en la casa, con el mar marcado y la distancia real anotada.
"""
import math, os, urllib.request
from PIL import Image, ImageDraw, ImageFont

CASA = (32.4164301, -117.0912259)
RUMBO_MAR = 261.0          # grados, medido con OSM
DIST_MAR = 461.0           # metros a la orilla
TILE = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/%d/%d/%d"
AQUI = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (recorrido-catania)"}
TTF = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def fuente(px):
    try:
        return ImageFont.truetype(TTF, px)
    except Exception:
        return ImageFont.load_default()


def xy(lat, lon, z):
    n = 2.0 ** z
    x = (lon + 180.0) / 360.0 * n
    lr = math.radians(lat)
    y = (1.0 - math.asinh(math.tan(lr)) / math.pi) / 2.0 * n
    return x, y


def destino(lat, lon, rumbo, metros):
    R = 6371000.0
    b, d = math.radians(rumbo), metros / R
    l1, o1 = math.radians(lat), math.radians(lon)
    l2 = math.asin(math.sin(l1) * math.cos(d) + math.cos(l1) * math.sin(d) * math.cos(b))
    o2 = o1 + math.atan2(math.sin(b) * math.sin(d) * math.cos(l1),
                         math.cos(d) - math.sin(l1) * math.sin(l2))
    return math.degrees(l2), math.degrees(o2)


def mapa(z, lado=900):
    """Imagen cuadrada de `lado` px centrada en la casa, al zoom z."""
    cx, cy = xy(*CASA, z)
    x0, y0 = cx - lado / 512.0, cy - lado / 512.0      # en tiles de 256
    im = Image.new("RGB", (lado, lado))
    tx0, ty0 = int(math.floor(x0)), int(math.floor(y0))
    tx1, ty1 = int(math.floor(x0 + lado / 256.0)), int(math.floor(y0 + lado / 256.0))
    for tx in range(tx0, tx1 + 1):
        for ty in range(ty0, ty1 + 1):
            try:
                req = urllib.request.Request(TILE % (z, ty, tx), headers=UA)
                with urllib.request.urlopen(req, timeout=30) as r:
                    t = Image.open(__import__("io").BytesIO(r.read())).convert("RGB")
            except Exception:
                t = Image.new("RGB", (256, 256), (40, 40, 40))
            im.paste(t, (int((tx - x0) * 256), int((ty - y0) * 256)))
    return im, (x0, y0)


def a_pixel(lat, lon, z, org):
    x, y = xy(lat, lon, z)
    return (x - org[0]) * 256.0, (y - org[1]) * 256.0


def metros_por_pixel(z):
    return 156543.03392 * math.cos(math.radians(CASA[0])) / (2 ** z)


def dibuja(z, nombre, titulo):
    im, org = mapa(z)
    d = ImageDraw.Draw(im)
    pc = a_pixel(*CASA, z=z, org=org)
    pm = a_pixel(*destino(*CASA, rumbo=RUMBO_MAR, metros=DIST_MAR), z=z, org=org)

    # la linea casa -> orilla, que es justo lo que la camara recorre al final
    d.line([pc, pm], fill=(255, 210, 0), width=4)
    r = 9
    d.ellipse([pc[0]-r, pc[1]-r, pc[0]+r, pc[1]+r], outline=(255, 60, 60), width=4)
    d.ellipse([pm[0]-r, pm[1]-r, pm[0]+r, pm[1]+r], outline=(0, 200, 255), width=4)

    # barra de escala de 100 m
    mpp = metros_por_pixel(z)
    largo = 100.0 / mpp
    etq = "100 m"
    if largo > im.width * 0.55:
        largo, etq = 25.0 / mpp, "25 m"
    f_chica, f_grande = fuente(20), fuente(26)
    x, y = 26, im.height - 46
    d.rectangle([x - 12, y - 30, x + largo + 70, y + 14], fill=(0, 0, 0))
    d.line([(x, y), (x + largo, y)], fill=(255, 255, 255), width=6)
    d.text((x + largo + 10, y - 12), etq, fill=(255, 255, 255), font=f_chica)

    # titulo con banda negra, que sobre satelite el texto suelto no se lee
    d.rectangle([0, 0, im.width, 84], fill=(0, 0, 0))
    d.text((22, 12), titulo, fill=(255, 220, 0), font=f_grande)
    d.text((22, 50), "casa (rojo) -> orilla (azul): 461 m  ·  la calle esta a 37 m sobre el mar",
           fill=(235, 235, 235), font=f_chica)
    d.text((pc[0] + 14, pc[1] - 26), "CASA", fill=(255, 90, 90), font=f_chica,
           stroke_width=3, stroke_fill=(0, 0, 0))
    d.text((pm[0] - 4, pm[1] + 16), "ORILLA", fill=(90, 220, 255), font=f_chica,
           stroke_width=3, stroke_fill=(0, 0, 0))
    ruta = os.path.join(AQUI, nombre)
    im.save(ruta, quality=88)
    return ruta, round(mpp, 2)


if __name__ == "__main__":
    plan = [
        (19, "mapa_1_z19_la_casa.jpg",     "1/5  la casa — donde arranca el remate"),
        (18, "mapa_2_z18_la_manzana.jpg",  "2/5  la manzana y la calle Catania"),
        (17, "mapa_3_z17_la_colonia.jpg",  "3/5  la colonia (lo que pasa por debajo)"),
        (16, "mapa_4_z16_hasta_la_playa.jpg", "4/5  ya cabe la playa: 461 m"),
        (15, "mapa_5_z15_el_pacifico.jpg", "5/5  el cuadro final: casa + colonia + Pacifico"),
    ]
    for z, n, t in plan:
        ruta, mpp = dibuja(z, n, t)
        print("%-34s z%-3d %6.2f m/px  %d KB" % (os.path.basename(ruta), z, mpp,
                                                 os.path.getsize(ruta) // 1024))
