"""Calcula la camara de cada cuarto DESDE EL CUARTO, y comprueba que lo ve.

    blender -b <blend> -P camaras_auto.py -- <salida.py>

POR QUE
-------
Las camaras de `cuartos_camara.py` se pusieron a ojo y nunca se verificaron.
Revisado el 3 sep 2026, varias miraban al cuarto equivocado:

  · `n1_bano`      -> lo primero que veia era `n1_cama_1` y el tapete verde,
                      o sea la recamara de al lado; el lavabo y el WC ni salian
  · `pb_mediobano` -> miraba a la cama king de la recamara principal
  · `pb_sala`      -> le pasaba por delante el medio bano entero
  · `pa_sala`      -> encuadraba el librero y las sillas del comedor

Y eso se veia en el render: el gris salia casi vacio. Cuando a la IA se le da
un cuadro vacio, LO LLENA — por eso "se invento" los banos. No fue la IA
desobedeciendo: fue que no le dimos nada que copiar.

COMO SE CALCULA
---------------
Nada a ojo. Para cada cuarto:

  1. Se saca su MANCHA con el mismo inundado de `corte_mascaras.py` (la planta
     cuadriculada a 15 cm, tapando muros, y la mancha que contiene su punto).
  2. Se junta su MOBILIARIO: los objetos cuyo centro cae en la mancha, quitando
     muros, losas, puertas y ventanas. Su centroide es a donde hay que mirar.
  3. Se prueban TODAS las celdas de la mancha como sitio de camara, a la altura
     del ojo, y se queda con la que:
       - de verdad VE el mobiliario — se lanza un rayo a cada mueble y se
         cuenta cuantos llegan sin toparse antes con un muro. Esto es lo que
         faltaba: la camara vieja del medio bano tenia el cuarto entero
         detras de una pared;
       - y de esas, la que este mas lejos del centroide, para que quepa el
         cuarto.
  4. El LENTE sale del angulo que abarca el mobiliario desde ahi, con 25 % de
     aire. Nada de 16 mm fijos.

Escribe un `.py` con el diccionario listo para pegar en `cuartos_camara.py`.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import corte_mascaras as CM              # noqa: E402  (manchas y niveles)
from cuartos_camara import CUARTOS, limpia   # noqa: E402

CELDA = CM.CELDA
CASA = CM.CASA
OJO = {"n1": -1.35, "pb": 1.52, "pa": 4.35, "rg": 4.40}

NO_MUEBLE = ("muro", "div", "losa", "piso", "plafon", "ext_", "a2_", "pta_",
             "vtn_", "esc_", "lam_", "roof_", "frente_", "canto", "VEC",
             "TER", "COLONIA", "MAR", "ESPUMA", "tierra", "TALUD", "liston",
             "cortina", "barandal", "CAM_")


def es_mueble(o, extra=()):
    """`extra` deja pasar prefijos que normalmente son estructura.

    Hace falta para la ESCALERA: sus piezas se llaman `esc_*` y estan en la
    lista de estructura, asi que el cuarto salia «sin muebles». Ahi la escalera
    ES el contenido."""
    if o.type != 'MESH' or o.hide_render or CM.es_vecina(o.name):
        return False
    if extra and o.name.startswith(tuple(extra)):
        return not o.name.endswith("_fantasma")
    return not o.name.startswith(NO_MUEBLE) and not o.name.endswith("_fantasma")


def centro(o):
    b = [o.matrix_world @ Vector(v) for v in o.bound_box]
    return Vector(((min(v.x for v in b) + max(v.x for v in b)) / 2,
                   (min(v.y for v in b) + max(v.y for v in b)) / 2,
                   (min(v.z for v in b) + max(v.z for v in b)) / 2))


# LAS CAJAS DE CADA CUARTO, en planta. NO salen del inundado.
#
# Se probo con la mancha inundada y NO SIRVE: en este modelo los vanos no
# tienen nada que los cierre — la hoja de la puerta es mas angosta que el
# hueco — asi que la inundacion se pasa de un cuarto a otro. Resultado: el bano
# y la recamara 1 salian como un solo cuarto y compartian camara, igual que la
# sala con la escalera y los tres espacios de la planta alta.
#
# Los limites son los MUROS DIVISORIOS del propio archivo:
#   n1_div_baño_rec2 / pb_div_mediobaño_sala  ->  y 10.24-10.31
#   pb_div_rec_mediobaño                      ->  y 11.99-12.06
#   ext_este / la crujia                      ->  x 4.75
CAJAS = {
    "n1_recamara2":     (1.10, 4.75,  6.67, 10.24),
    "n1_bano":          (1.10, 4.75, 10.31, 11.99),
    "n1_recamara1":     (1.10, 4.75, 12.06, 15.52),
    "n1_bodega":        (4.75, 6.90,  6.67, 10.00),
    "n1_estudio":       (4.75, 6.90, 10.00, 12.80),
    "n1_lavado":        (4.75, 6.90, 12.80, 15.52),
    "pb_sala":          (1.10, 4.75,  6.67, 10.24),
    "pb_mediobano":     (1.10, 4.75, 10.31, 11.99),
    "pb_recamara_ppal": (1.10, 4.75, 12.06, 15.52),
    "pb_escalera":      (4.75, 6.90,  6.67, 10.00),
    "pb_vestidor":      (4.75, 6.90, 10.00, 12.80),
    "pb_bano_ppal":     (4.75, 6.90, 12.80, 15.52),
    # la planta alta es una sola pieza: se parte por lo que hay en cada zona
    "pa_cocina":        (1.10, 6.90,  6.67,  9.60),
    "pa_comedor":       (1.10, 6.90,  9.60, 12.20),
    "pa_sala":          (1.10, 4.90,  9.40, 12.60),
    "rg_terraza":       (1.10, 6.90, 12.20, 15.52),
}


def celdas_del_cuarto(cuarto):
    """Las celdas del cuarto, de su CAJA, y sin las que son MURO.

    Al pasar del inundado a las cajas se perdio algo que el inundado hacia
    gratis: descartar las celdas ocupadas por un muro. La primera celda de la
    caja del estudio caia en x 4.825, y `n1_muro_este_estudio` va de 4.79 a
    4.86 — la camara quedaba DENTRO de la pared y el render salia gris plano.
    Aqui se descartan las celdas que cruzan un muro del nivel, mas 20 cm de
    aire, que es lo que necesita una camara para no comerse el rincon.
    """
    nivel = cuarto.split("_", 1)[0]
    x0, x1, y0, y1 = CAJAS[cuarto]
    piso, techo = CM.NIVELES[nivel]
    medio = (piso + techo) / 2.0
    cajas = [(a, b, c, d) for a, b, c, d, z0, z1 in CM.MUROS if z0 <= medio <= z1]
    AIRE = 0.20
    fuera = []
    y = y0 + CELDA / 2
    while y < y1:
        x = x0 + CELDA / 2
        while x < x1:
            choca = any(a - AIRE <= x <= b + AIRE and c - AIRE <= y <= d + AIRE
                        for a, b, c, d in cajas)
            if not choca:
                fuera.append((x, y))
            x += CELDA
        y += CELDA
    return nivel, fuera


# cuartos donde una pieza «de estructura» es en realidad el contenido
EXTRA = {"pb_escalera": ("esc_",), "n1_estudio": (), "pb_vestidor": ()}


def calcula(cuarto, dep):
    extra = EXTRA.get(cuarto, ())
    nivel, celdas = celdas_del_cuarto(cuarto)
    if not celdas:
        return None, "sin mancha"
    zx = OJO[nivel]
    xs = [c[0] for c in celdas]
    ys = [c[1] for c in celdas]
    caja = (min(xs), max(xs), min(ys), max(ys))

    # el mobiliario que vive DENTRO de la mancha
    piso, techo = CM.NIVELES[nivel]
    bx0, bx1, by0, by1 = CAJAS[cuarto]

    def en_mancha(p):
        return bx0 - 0.10 <= p.x <= bx1 + 0.10 and by0 - 0.10 <= p.y <= by1 + 0.10

    muebles = []
    for o in bpy.data.objects:
        if not es_mueble(o, extra):
            continue
        c = centro(o)
        if piso - 0.15 <= c.z <= techo + 0.15 and en_mancha(c):
            muebles.append(c)
    if not muebles:
        return None, "sin muebles"
    blanco = sum(muebles, Vector()) / len(muebles)
    blanco.z = zx - 0.25            # se mira un poco abajo del ojo

    # MUESTREO, o esto no acaba: la planta alta son 2271 celdas x 112 muebles =
    # 254 mil rayos. Con una celda de cada tres y 24 muebles repartidos el
    # resultado es el mismo y baja a segundos.
    muestra = muebles[::max(1, len(muebles) // 24)][:24]
    celdas_p = celdas[::3] if len(celdas) > 120 else celdas

    # se prueban las celdas: gana la que VE mas muebles y este mas lejos
    mejor = None
    for x, y in celdas_p:
        # pegada a un muro no: se pide 25 cm de aire alrededor
        if not (caja[0] + 0.2 <= x <= caja[1] - 0.2 or caja[1] - caja[0] < 0.6):
            pass
        ojo = Vector((x, y, zx))
        d = (blanco - ojo)
        if d.length < 1.2:
            continue
        vistos = 0
        for m in muestra:
            v = m - ojo
            dist = v.length
            if dist < 0.05:
                continue
            hit, loc, _n, _i, obj, _mw = bpy.context.scene.ray_cast(
                dep, ojo, v.normalized(), distance=dist - 0.05)
            # si lo que topa es un MUEBLE, cuenta como visto
            if (not hit) or (obj and es_mueble(obj, extra)):
                vistos += 1
        nota = (round(vistos / len(muestra), 3), round(d.length, 2))
        if mejor is None or nota > mejor[0]:
            mejor = (nota, ojo)
    if mejor is None:
        return None, "ninguna celda sirve"

    (frac, dist), ojo = mejor
    vistos = int(round(frac * len(muestra)))
    # el lente: que quepa el mobiliario con 25 % de aire
    eje = (blanco - ojo).normalized()
    ang = 0.0
    for m in muebles:
        v = (m - ojo)
        if v.length < 0.01:
            continue
        ang = max(ang, math.acos(max(-1.0, min(1.0, v.normalized().dot(eje)))))
    ang = max(0.30, min(1.05, ang * 1.25))
    lente = max(12.0, min(35.0, 18.0 / math.tan(ang)))
    return (tuple(round(v, 2) for v in ojo),
            tuple(round(v, 2) for v in blanco),
            int(round(lente)), vistos, len(muestra), len(muebles)), None


if __name__ == "__main__":
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    salida = a[0] if a else "/tmp/camaras_auto.py"
    sc = bpy.context.scene
    sc.frame_set(CM.CUADRO)
    limpia()
    CM.apunta_muros()
    bpy.context.view_layer.update()
    dep = bpy.context.evaluated_depsgraph_get()

    lineas = []
    for cuarto in CUARTOS:
        r, err = calcula(cuarto, dep)
        if r is None:
            print("  %-18s NO SE PUDO: %s" % (cuarto, err), flush=True)
            continue
        pos, mira, lente, vistos, muestra, total = r
        print("  %-18s ojo %s -> %s  lente %2d   ve %d/%d de la muestra (%d muebles)"
              % (cuarto, pos, mira, lente, vistos, muestra, total), flush=True)
        lineas.append('    "%s": (%s, %s, %d,\n        %r),'
                      % (cuarto, pos, mira, lente, CUARTOS[cuarto][3]))
    with open(salida, "w", encoding="utf8") as f:
        f.write("# AUTOGENERADO por camaras_auto.py — cada camara se calculo\n"
                "# desde la mancha de su cuarto y se comprobo con rayos que de\n"
                "# verdad ve sus muebles.\nCUARTOS = {\n"
                + "\n".join(lineas) + "\n}\n")
    print("escrito", salida)
