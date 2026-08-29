"""El mar y el terreno, como en el video de dron de Mariano (28 Ago, 46.4 s).

En Workbench no hay reflejos, ni refraccion, ni texturas: el motor sombrea por
NORMAL y por color de material, y ya. De ahi salen las dos reglas de este
archivo:

  * El agua tiene que ser GEOMETRIA. Un plano liso siempre se vera como una
    cartulina azul por muy bonito que sea el color. Con una rejilla y dos
    modificadores Wave cruzados, cada cresta agarra distinta luz y el mar se
    mueve solo — sin simulacion, sin cache y sin peso de render.
  * El color va por ZONAS, no uniforme. En la foto el agua es turquesa claro en
    la rompiente y azul profundo mar adentro; el cerro es ocre seco con manchas
    verdes. Como no hay textura, esa variacion se pinta por poligono.

    mar_de_verdad()   ·  terreno_como_el_dron()  ·  todo()
    mar_liso()        vuelve al plano de antes
"""
import math

import bpy
import bmesh
from mathutils import Vector

MAR = "MAR"
NIVEL = -37.0                      # z de escena del nivel del mar
AREA_X = (-300.0, 305.0)
AREA_Y = (486.0, 760.0)            # de la orilla al horizonte
CELDA = 4.0                        # m por cuadro de la rejilla

# (hasta que Y, color) — de la orilla hacia afuera
FRANJAS_MAR = [
    (516.0, (0.115, 0.470, 0.470, 1.0)),   # rompiente, turquesa claro
    (560.0, (0.070, 0.360, 0.400, 1.0)),
    (640.0, (0.040, 0.250, 0.330, 1.0)),
    (9999.0, (0.022, 0.160, 0.260, 1.0)),  # mar adentro, azul profundo
]
# Workbench sombrea plano: una ola de 2 m vista desde 100 m no cambia casi nada
# de luz y el mar se ve liso aunque el relieve este ahi (medido: la malla si
# ondula 2.3 m). Lo que SI se ve es el color, asi que las caras que suben y las
# que bajan se pintan distinto — es el contraste del oleaje, pintado a mano.
# Sutil: con el contraste alto y celdas de 6 m el mar salia a cuadros, como
# una colcha de retazos. El swell real son bandas LARGAS y paralelas a la
# costa, con poca diferencia de tono entre la cara que sube y la que baja.
CRESTA = (0.150, 0.480, 0.485, 1.0)
VALLE = (0.045, 0.245, 0.320, 1.0)
PENDIENTE = 0.20

# El cerro de la referencia: ocre seco, con manchas verdes y arena junto al mar.
TIERRA = {
    "DRON_ocre":  (0.44, 0.36, 0.22, 1.0),
    "DRON_seco":  (0.52, 0.45, 0.31, 1.0),
    "DRON_verde": (0.24, 0.31, 0.17, 1.0),
    "DRON_arena": (0.70, 0.64, 0.50, 1.0),
}


def _mat(nombre, color):
    m = bpy.data.materials.get(nombre) or bpy.data.materials.new(nombre)
    m.diffuse_color = color
    if m.use_nodes:
        for n in m.node_tree.nodes:
            if "Base Color" in getattr(n, "inputs", {}):
                n.inputs["Base Color"].default_value = color
    return m


# ---------------------------------------------------------------- el agua ---
def mar_de_verdad(celda=CELDA, avance=42.0):
    """Cambia el plano del MAR por una rejilla con oleaje de verdad.

    El oleaje va HORNEADO en la malla (senos cruzados) y lo que se anima es el
    objeto entero deslizandose hacia la playa. Suena a truco y lo es, pero es
    el truco correcto: un tren de olas de swell avanza justo asi, sin cambiar
    de forma. Y evita el modificador Wave, que esta hecho para "gota que cae":
    con height 1.9 solo levantaba 0.64 m —medido en la malla evaluada— porque
    su envolvente amortigua todo lo que no sea el frente del pulso.

    `avance` son los metros que recorren las olas a lo largo del video.
    """
    esc = bpy.context.scene
    ob = bpy.data.objects.get(MAR)
    col = (ob.users_collection[0] if ob else
           bpy.data.collections.get("TERRENO_MAR") or esc.collection)
    if ob is not None:
        bpy.data.objects.remove(ob, do_unlink=True)

    # se extiende hacia el mar lo que va a recorrer, para que al deslizarse no
    # aparezca el borde de la rejilla por arriba
    y0, y1 = AREA_Y[0] - 4.0, AREA_Y[1] + avance + 10.0
    nx = int((AREA_X[1] - AREA_X[0]) / celda)
    ny = int((y1 - y0) / celda)

    def altura(x, y):
        # swell principal hacia la playa (periodo ~44 m) y un tren cruzado
        # suave. El rizado corto se quito: con celdas de 4 m no lo resuelve y
        # solo producia el moteado de cuadros.
        h = 1.60 * math.sin(y / 7.0) + 0.38 * math.sin((x * 0.25 + y) / 5.5)
        # las olas crecen al acercarse a la orilla y se planchan mar adentro
        f = max(0.35, min(1.0, (620.0 - y) / 110.0 + 0.55))
        return h * f

    me = bpy.data.meshes.new(MAR)
    ob = bpy.data.objects.new(MAR, me)
    col.objects.link(ob)
    bm = bmesh.new()
    verts = {}
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = AREA_X[0] + i * celda
            y = y0 + j * celda
            verts[(i, j)] = bm.verts.new((x, y, altura(x, y)))
    bm.verts.ensure_lookup_table()
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((verts[(i, j)], verts[(i + 1, j)],
                          verts[(i + 1, j + 1)], verts[(i, j + 1)]))
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:
        poly.use_smooth = True         # sin esto se ve cada cuadro de la rejilla

    # color por profundidad: un material por franja, asignado por poligono
    for k, (_, color) in enumerate(FRANJAS_MAR):
        me.materials.append(_mat("MAR_franja%d" % k, color))
    i_cresta = len(me.materials)
    me.materials.append(_mat("MAR_cresta", CRESTA))
    me.materials.append(_mat("MAR_valle", VALLE))
    for poly in me.polygons:
        y = poly.center.y
        idx = len(FRANJAS_MAR) - 1
        for k, (hasta, _) in enumerate(FRANJAS_MAR):
            if y < hasta:
                idx = k
                break
        # mar adentro las olas se aplanan: alla manda la profundidad
        if y < 640.0 and abs(poly.normal.y) > PENDIENTE:
            idx = i_cresta if poly.normal.y > 0 else i_cresta + 1
        poly.material_index = idx

    # y el tren avanza: dos llaves, principio y fin del video
    ob.animation_data_clear()
    ob.location = (0.0, avance, NIVEL)
    ob.keyframe_insert("location", frame=esc.frame_start)
    ob.location = (0.0, 0.0, NIVEL)
    ob.keyframe_insert("location", frame=esc.frame_end)
    for fc in ob.animation_data.action.fcurves:
        for k in fc.keyframe_points:
            k.interpolation = 'LINEAR'   # el mar no acelera ni frena

    esc.display.shading.color_type = 'MATERIAL'
    return {"objeto": ob.name, "caras": len(me.polygons), "rejilla": [nx, ny],
            "avance_m": avance, "olas_m": 1.9,
            "franjas": len(FRANJAS_MAR)}


def mar_liso():
    """Deja el agua quieta (por si el deslizamiento estorba)."""
    ob = bpy.data.objects.get(MAR)
    if ob is None:
        return {"error": "no hay MAR"}
    ob.animation_data_clear()
    ob.location = (0.0, 0.0, NIVEL)
    return {"animacion": "quitada"}


# -------------------------------------------------------------- el terreno --
def terreno_como_el_dron(objeto="TER_real"):
    """Pinta el terreno por zonas: arena junto al agua, ocre en los cerros,
    seco en medio y manchas verdes salpicadas. Es lo mas cerca de una textura
    que se puede tener en Workbench."""
    ob = bpy.data.objects.get(objeto)
    if ob is None or ob.type != 'MESH':
        return {"error": "no esta " + objeto}
    me = ob.data
    me.materials.clear()
    orden = ["DRON_arena", "DRON_seco", "DRON_ocre", "DRON_verde"]
    for n in orden:
        me.materials.append(_mat(n, TIERRA[n]))

    M = ob.matrix_world
    cuenta = dict.fromkeys(orden, 0)
    for poly in me.polygons:
        c = M @ poly.center
        # una mancha estable (no aleatoria: asi se puede volver a correr igual)
        mancha = ((int(c.x) // 37) * 7 + (int(c.y) // 41) * 13) % 11
        if c.z < -34.0:
            i = 0                       # a ras del mar: arena
        elif c.z > -14.0:
            i = 2                       # lo alto de los cerros: ocre
        elif mancha < 2:
            i = 3                       # manchas verdes
        else:
            i = 1
        poly.material_index = i
        cuenta[orden[i]] += 1
    me.update()
    return {"objeto": objeto, "caras": len(me.polygons), "reparto": cuenta}


def todo():
    return {"mar": mar_de_verdad(), "terreno": terreno_como_el_dron()}
