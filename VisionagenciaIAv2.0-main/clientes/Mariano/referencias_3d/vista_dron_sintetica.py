"""Vistas de dron de la Catania: el satelite proyectado sobre el terreno real.

Google no da vistas oblicuas sin llave, asi que se arman aqui: se baja el
mosaico satelital, se lee el MISMO DEM que uso `terreno_mar.py` (SRTM de 25 m)
y se traza un rayo por pixel contra ese relieve. Sale la vista en perspectiva
que se ve desde un dron, con la textura real y las alturas reales — o sea, la
misma geometria que tiene la escena de Blender.

Coordenadas de ESCENA (las de Blender):  X = x_real+3.5, Y = y_real-4.5,
Z = z_real-37. La casa esta en el origen y el Pacifico en +Y a 461 m.
"""
import ast, io, math, os, re, sys, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
TERRENO = ("/workspaces/visionagenciaIAv2.0/VisionagenciaIAv2.0-main/"
           "clientes/Mariano/blender/terreno_mar.py")
CASA = (32.4164301, -117.0912259)
ORIG_X, ORIG_Y, Z_CASA = 3.5, -4.5, 37.0
TILES = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/%d/%d/%d"
UA = {"User-Agent": "Mozilla/5.0 (recorrido-catania)"}
ZOOM = 17                      # ~1 m/px
LADO = 2048                    # px del mosaico -> ~2 km de lado


# --------------------------------------------------------------- el terreno --
def lee_dem():
    """XS, YS y Z del propio terreno_mar.py, sin ejecutarlo (importa bpy)."""
    txt = open(TERRENO, encoding="utf8").read()
    xs = ast.literal_eval(re.search(r"^XS = (\[.*?\])$", txt, re.M).group(1))
    ys = ast.literal_eval(re.search(r"^YS = (\[.*?\])$", txt, re.M).group(1))
    zz = ast.literal_eval(re.search(r"^Z  = (\{.*?\})$", txt, re.M).group(1))
    rej = np.zeros((len(ys), len(xs)), np.float32)
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            rej[j, i] = zz["%d,%d" % (x, y)] - Z_CASA      # a Z de escena
    return np.array(xs, np.float32) + ORIG_X, np.array(ys, np.float32) + ORIG_Y, rej


XS, YS, DEM = lee_dem()
PASO_DEM = 25.0


NIVEL_MAR = -Z_CASA          # z de escena del agua (z_real = 0)


def altura(x, y):
    """Z de escena del terreno, bilineal. Fuera del DEM es mar, no borde repetido."""
    dentro = ((x >= XS[0]) & (x <= XS[-1]) & (y >= YS[0]) & (y <= YS[-1]))
    fx = np.clip((x - XS[0]) / PASO_DEM, 0, len(XS) - 1.001)
    fy = np.clip((y - YS[0]) / PASO_DEM, 0, len(YS) - 1.001)
    i, j = fx.astype(np.int32), fy.astype(np.int32)
    tx, ty = fx - i, fy - j
    z00, z10 = DEM[j, i], DEM[j, i + 1]
    z01, z11 = DEM[j + 1, i], DEM[j + 1, i + 1]
    z = (z00 * (1 - tx) * (1 - ty) + z10 * tx * (1 - ty)
         + z01 * (1 - tx) * ty + z11 * tx * ty)
    return np.where(dentro, z, NIVEL_MAR)


# -------------------------------------------------------------- la textura ---
def _xy(lat, lon, z):
    n = 2.0 ** z
    return ((lon + 180.0) / 360.0 * n,
            (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n)


def mosaico():
    cache = os.path.join(AQUI, "sat_z%d_%d.jpg" % (ZOOM, LADO))
    if os.path.exists(cache):
        return Image.open(cache).convert("RGB")
    cx, cy = _xy(*CASA, ZOOM)
    x0, y0 = cx - LADO / 512.0, cy - LADO / 512.0
    im = Image.new("RGB", (LADO, LADO))
    tx0, ty0 = int(math.floor(x0)), int(math.floor(y0))
    for tx in range(tx0, int(math.floor(x0 + LADO / 256.0)) + 1):
        for ty in range(ty0, int(math.floor(y0 + LADO / 256.0)) + 1):
            try:
                req = urllib.request.Request(TILES % (ZOOM, ty, tx), headers=UA)
                with urllib.request.urlopen(req, timeout=30) as r:
                    t = Image.open(io.BytesIO(r.read())).convert("RGB")
            except Exception:
                t = Image.new("RGB", (256, 256), (60, 60, 60))
            im.paste(t, (int((tx - x0) * 256), int((ty - y0) * 256)))
    im.save(cache, quality=90)
    return im


SAT = np.asarray(mosaico(), np.uint8)
M_POR_PX = 156543.03392 * math.cos(math.radians(CASA[0])) / (2 ** ZOOM)


def color(x, y):
    """Color satelital en un punto de escena. El centro del mosaico es la casa."""
    px = np.clip(SAT.shape[1] / 2 + (x - ORIG_X) / M_POR_PX, 0, SAT.shape[1] - 1)
    py = np.clip(SAT.shape[0] / 2 - (y - ORIG_Y) / M_POR_PX, 0, SAT.shape[0] - 1)
    col = SAT[py.astype(np.int32), px.astype(np.int32)].astype(np.float32)
    fuera = ((np.abs(x - ORIG_X) > SAT.shape[1] / 2 * M_POR_PX - 4)
             | (np.abs(y - ORIG_Y) > SAT.shape[0] / 2 * M_POR_PX - 4))
    return np.where(fuera[..., None], np.array([38., 74., 96.], np.float32), col)


# ------------------------------------------------------------------ render ---
def vista(cam, mira, lente=35.0, w=1000, h=562, pasos=340, largo=3600.0):
    cam = np.array(cam, np.float64)
    ade = np.array(mira, np.float64) - cam
    ade /= np.linalg.norm(ade)
    der = np.cross(ade, (0, 0, 1.0)); der /= np.linalg.norm(der)
    arr = np.cross(der, ade)

    u = (np.arange(w) - w / 2 + 0.5) * (36.0 / lente) / w
    v = (np.arange(h) - h / 2 + 0.5) * (36.0 / lente) / w
    uu, vv = np.meshgrid(u, -v)
    d = (ade[None, None, :] + uu[..., None] * der + vv[..., None] * arr)
    d /= np.linalg.norm(d, axis=2, keepdims=True)

    # Marcha con paso CRECIENTE: cerca hace falta detalle, lejos no. Con paso
    # fijo hacian falta ~900 vueltas sobre un millon de rayos y no terminaba.
    t = np.full((h, w), 2.0, np.float32)
    golpeo = np.zeros((h, w), bool)
    d = d.astype(np.float32)
    cam32 = cam.astype(np.float32)
    dt, factor = np.float32(2.5), np.float32(1.011)
    for _ in range(pasos):
        t_v = t + dt
        p = cam32[None, None, :] + d * t_v[..., None]
        bajo = p[..., 2] <= altura(p[..., 0], p[..., 1])
        golpeo |= (~golpeo) & bajo
        t = np.where(golpeo, t, t_v)
        dt = dt * factor

    p = cam[None, None, :] + d * t[..., None]
    img = color(p[..., 0], p[..., 1]).astype(np.float32)

    # cielo donde el rayo se fue de largo, con neblina hacia el horizonte
    cielo = np.stack(np.broadcast_arrays(
        np.linspace(120, 205, h)[:, None], np.linspace(165, 220, h)[:, None],
        np.linspace(215, 240, h)[:, None]), -1).astype(np.float32)
    cielo = np.broadcast_to(cielo, (h, w, 3))
    niebla = np.clip((t / largo) ** 0.8, 0, 1)[..., None]
    img = img * (1 - niebla) + np.array([205., 220., 235.]) * niebla
    img = np.where(golpeo[..., None], img, cielo)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


def rotula(im, titulo, pie):
    d = ImageDraw.Draw(im)
    f = lambda n: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", n)
    d.rectangle([0, 0, im.width, 78], fill=(0, 0, 0))
    d.text((20, 10), titulo, fill=(255, 220, 0), font=f(30))
    d.text((20, 46), pie, fill=(225, 225, 225), font=f(19))
    return im


if __name__ == "__main__":
    sal = sys.argv[1] if len(sys.argv) > 1 else AQUI
    ORILLA = (3.5, 490.0, -35.0)
    tomas = [
        ("dron_1_sobre_la_casa.jpg", (3.5, -60.0, 35.0), (3.5, 300.0, -20.0), 30.0,
         "1/4  DRON SOBRE LA CASA — 35 m de altura",
         "mirando al Pacifico: los 461 m de colonia se ven de un jalon"),
        ("dron_2_el_remate.jpg", (3.5, -150.0, 60.0), ORILLA, 42.0,
         "2/4  EL CUADRO DEL REMATE — 60 m, lente 42",
         "esta es la posicion exacta que quedo en el .blend (frame 1153)"),
        ("dron_3_alto.jpg", (3.5, -260.0, 150.0), (3.5, 520.0, -35.0), 35.0,
         "3/4  MAS ALTO — 150 m",
         "el que sacaba el borde del mapa en Blender; aqui se ve completo"),
        ("dron_4_desde_el_mar.jpg", (3.5, 620.0, 70.0), (3.5, -20.0, 5.0), 40.0,
         "4/4  CONTRAPLANO desde el mar hacia la casa",
         "para ver como sube el terreno los 37 m hasta la calle Catania"),
    ]
    for nombre, cam, mira, lente, tit, pie in tomas:
        im = rotula(vista(cam, mira, lente), tit, pie)
        ruta = os.path.join(sal, nombre)
        im.save(ruta, quality=88)
        print("%-28s %d KB" % (nombre, os.path.getsize(ruta) // 1024))
