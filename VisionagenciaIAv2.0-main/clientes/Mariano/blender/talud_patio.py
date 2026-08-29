"""El talud detras de los patios: cose el agujero entre el jardin y el cerro.

Medido: el pasto del jardin llega a y = 19 con z = -2.85, y el DEM del cerro no
vuelve a aparecer hasta y = 22, ya en z = -0.47. O sea tres metros sin NADA y,
donde reaparece, dos metros y medio mas arriba. Por eso se veia un agujero
detras del patio: literalmente no habia suelo.

El hueco existe por construccion — `terreno_mar.py` deja sin DEM la franja
`HUECO = (-24, 24, -27, 18)` para no pisar el terreno modelado a mano — pero
nadie cosio el borde. Esto lo cose: una rampa que arranca en la coronacion del
muro de contencion y sube hasta empalmar con la altura real del cerro, medida
con un rayo en cada columna para que pegue exacto aunque el DEM ondule.

    rellenar()    ·  deshacer()
"""
import bpy
import bmesh
from mathutils import Vector

NOMBRE = "TALUD_patio"
X = (-26.0, 26.0)        # cubre la casa A2 y las cuatro vecinas
Y_PIE = 18.95            # justo detras del muro de contencion del fondo
Y_CIMA = 27.0            # donde el DEM ya es firme
PASO_X, PASO_Y = 2.0, 1.0
Z_PIE = -1.35            # coronacion del muro de contencion
MATERIAL = "DRON_seco"


def deshacer():
    ob = bpy.data.objects.get(NOMBRE)
    if ob is None:
        return {"quitado": False}
    bpy.data.objects.remove(ob, do_unlink=True)
    return {"quitado": True}


def _z_del_cerro(esc, dg, x, y, ignorar=NOMBRE):
    """Altura del terreno en (x, y), tirando un rayo desde arriba."""
    origen = Vector((x, y, 80.0))
    for _ in range(6):
        ok, loc, _n, _i, ob, _m = esc.ray_cast(dg, origen, Vector((0, 0, -1)), distance=200)
        if not ok:
            return None
        if ob is None or ob.name != ignorar:
            return loc.z
        origen = loc + Vector((0, 0, -0.05))
    return None


def rellenar(y_pie=Y_PIE, y_cima=Y_CIMA, z_pie=Z_PIE):
    deshacer()
    esc = bpy.context.scene
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()

    nx = int((X[1] - X[0]) / PASO_X)
    ny = int((y_cima - y_pie) / PASO_Y)

    # la altura del cerro en la cima, columna por columna: asi el remate del
    # talud empalma con el DEM real y no con un promedio
    cima = []
    for i in range(nx + 1):
        x = X[0] + i * PASO_X
        z = _z_del_cerro(esc, dg, x, y_cima + 1.0)
        cima.append(z if z is not None else -0.5)

    me = bpy.data.meshes.new(NOMBRE)
    ob = bpy.data.objects.new(NOMBRE, me)
    col = bpy.data.collections.get("TERRENO_MAR") or esc.collection
    col.objects.link(ob)

    bm = bmesh.new()
    verts = {}
    for j in range(ny + 1):
        t = j / ny
        suave = t * t * (3.0 - 2.0 * t)      # arranca y remata sin quiebre
        y = y_pie + j * PASO_Y
        for i in range(nx + 1):
            x = X[0] + i * PASO_X
            z = z_pie + (cima[i] - z_pie) * suave
            verts[(i, j)] = bm.verts.new((x, y, z))
    bm.verts.ensure_lookup_table()
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((verts[(i, j)], verts[(i + 1, j)],
                          verts[(i + 1, j + 1)], verts[(i, j + 1)]))
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:
        poly.use_smooth = True

    mat = bpy.data.materials.get(MATERIAL)
    if mat is None:
        mat = bpy.data.materials.new(MATERIAL)
        mat.diffuse_color = (0.52, 0.45, 0.31, 1.0)
    me.materials.append(mat)
    return {"objeto": NOMBRE, "caras": len(me.polygons),
            "de_y": y_pie, "a_y": y_cima,
            "sube_de": z_pie, "a_z": [round(min(cima), 2), round(max(cima), 2)]}
