"""El terreno medido se acaba a 300 m a los lados y a 725 m hacia el mar: si la
camara sube mucho, se ve el borde y detras el vacio. Esto le cose una **falda**
al contorno de tierra —no a la orilla— que se va 2.5 km hacia afuera bajando de
a poco. Son ~120 caras: no pesa, y tapa el filo.

No toca el agua (el contorno de la playa se deja como esta) ni el hueco central
donde vive el terreno modelado a mano.

    aplicar()  /  deshacer()
"""
import bpy, bmesh
from mathutils import Vector

LEJOS = 2500.0        # cuanto se estira la falda
CAIDA = 45.0          # cuanto baja en ese trecho
MAR_Z = -37.0
HUECO = (-26.0, 34.0, -32.0, 22.0)     # el hueco central, con holgura


def deshacer():
    ob = bpy.data.objects.get("TER_faldon")
    if ob:
        me = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if me.users == 0:
            bpy.data.meshes.remove(me)
        return True
    return False


def aplicar():
    base = bpy.data.objects.get("TER_real")
    if base is None:
        return {"error": "no esta TER_real"}
    deshacer()
    bm = bmesh.new()
    bm.from_mesh(base.data)
    bm.edges.ensure_lookup_table()

    centro = Vector((0.0, 0.0))
    for v in bm.verts:
        centro += Vector((v.co.x, v.co.y))
    centro /= len(bm.verts)

    x0, x1, y0, y1 = HUECO
    aristas = []
    for e in bm.edges:
        if len(e.link_faces) != 1:
            continue
        a, b = e.verts
        # el borde del hueco central no cuenta
        if (x0 < a.co.x < x1 and y0 < a.co.y < y1) or (x0 < b.co.x < x1 and y0 < b.co.y < y1):
            continue
        # la orilla del mar tampoco: ahi el agua ya cubre
        if a.co.z < -33.0 and b.co.z < -33.0:
            continue
        aristas.append((a.co.copy(), b.co.copy()))
    bm.free()

    if not aristas:
        return {"error": "no encontre contorno de tierra"}

    def afuera(p):
        d = Vector((p.x, p.y)) - centro
        if d.length < 1e-6:
            d = Vector((1.0, 0.0))
        d.normalize()
        z = max(p.z - CAIDA, MAR_Z + 0.5)
        return Vector((p.x + d.x * LEJOS, p.y + d.y * LEJOS, z))

    bm2 = bmesh.new()
    n = 0
    for a, b in aristas:
        va, vb = bm2.verts.new(a), bm2.verts.new(b)
        vc, vd = bm2.verts.new(afuera(b)), bm2.verts.new(afuera(a))
        try:
            bm2.faces.new((va, vb, vc, vd))
            n += 1
        except ValueError:
            pass
    me = bpy.data.meshes.new("TER_faldon")
    bm2.to_mesh(me); bm2.free()
    me.update()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new("TER_faldon", me)
    bpy.context.scene.collection.objects.link(ob)
    col = bpy.data.collections.get("TERRENO_MAR")
    if col:
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        col.objects.link(ob)
    mat = bpy.data.materials.get("TER_cerro")
    if mat:
        ob.data.materials.append(mat)
    return {"caras": n, "verts": len(me.vertices),
            "tris": sum(len(p.vertices) - 2 for p in me.polygons)}
