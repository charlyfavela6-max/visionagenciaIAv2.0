"""El balcon del segundo piso: losa VOLADA con barandal alrededor.

Lo que estaba mal en el modelo era una sola cosa: la losa no tenia barandal.
Un metro de repisa colgando de la fachada, sin nada alrededor — de ahi que se
viera raro.

Primero se corrigio al reves: leyendo el clip 13 (el ventanal con un barandal
detras del vidrio) y el 10 (fachada trasera, que se ve plana) se concluyo que
era un balcon frances y se recorto la losa. **Estaba mal, lo corrigio Carlos,
que conoce la casa.** La prueba esta en el clip 16: esa toma esta grabada DESDE
el balcon —se ve el barandal negro en primer plano y el jardin abajo—, asi que
si hay piso y si se puede salir. El clip 10 no lo desmiente: la fachada que
enseña es la de la planta baja, y el volado queda fuera de cuadro.

Leccion, por si vuelve a pasar: una foto que NO enseña algo no prueba que no
exista. Preguntar antes de recortar geometria.

    arreglar()    devuelve el vuelo a la losa y le pone barandal alrededor
    deshacer()    quita los barandales (la losa se queda como este)
"""
import bpy
import bmesh
from mathutils import Vector

MARCA = "barandal_frances"
VUELO = None          # None = se respeta el vuelo que tenga la losa
ALTO = 1.05           # pasamanos, altura de norma
MEDIO = 0.55          # travesaño intermedio
TUBO = 0.045          # seccion del pasamanos
POSTE = 0.035
SEPARACION = 0.85     # entre postes
BORDE = 0.06          # el barandal se mete esto hacia dentro del filo de la losa
MAT = "mb_marco"      # el mismo negro del marco del ventanal


def _caja(ob):
    p = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return (Vector((min(q.x for q in p), min(q.y for q in p), min(q.z for q in p))),
            Vector((max(q.x for q in p), max(q.y for q in p), max(q.z for q in p))))


def _material():
    m = bpy.data.materials.get(MAT)
    if m is None:
        m = bpy.data.materials.new(MAT)
        m.diffuse_color = (0.045, 0.045, 0.05, 1.0)
    return m


def _barra(nombre, centro, tam, col):
    me = bpy.data.meshes.new(nombre)
    ob = bpy.data.objects.new(nombre, me)
    col.objects.link(ob)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(me)
    bm.free()
    ob.scale = tam
    ob.location = centro
    ob.data.materials.append(_material())
    ob[MARCA] = True
    return ob


def deshacer():
    fuera = [o for o in bpy.data.objects if o.get(MARCA)]
    for o in fuera:
        bpy.data.objects.remove(o, do_unlink=True)
    # la losa, de vuelta a su vuelo de antes
    devueltas = 0
    for ob in bpy.data.objects:
        if "balcon_losa" in ob.name and "vuelo_previo" in ob.data:
            prev = ob.data["vuelo_previo"]
            mn, mx = _caja(ob)
            actual = mx.y - mn.y
            if actual > 1e-4:
                f = prev / actual
                c = sum((Vector(c) for c in ob.bound_box), Vector()) / 8.0
                for v in ob.data.vertices:
                    v.co.y = c.y + (v.co.y - c.y) * f
                ob.data.update()
                del ob.data["vuelo_previo"]
                devueltas += 1
    return {"barandales_quitados": len(fuera), "losas_devueltas": devueltas}


def arreglar(vuelo=VUELO):
    """Barandal en los TRES lados libres de la losa: frente y dos costados.

    Se apoya en la caja de la propia losa, asi que si el balcon se hace mas
    grande o mas chico el barandal lo sigue sin tocar nada.
    """
    deshacer()
    hechos = []
    losas = [o for o in bpy.data.objects
             if o.type == 'MESH' and "balcon_losa" in o.name]
    for losa in losas:
        col = losa.users_collection[0] if losa.users_collection else bpy.context.scene.collection
        sufijo = losa.name.replace("pb_balcon_losa", "")

        # si en la pasada anterior se recorto el vuelo, se devuelve
        if "vuelo_previo" in losa.data:
            mn, mx = _caja(losa)
            actual = mx.y - mn.y
            objetivo = vuelo if vuelo else losa.data["vuelo_previo"]
            if actual > 1e-4 and abs(objetivo - actual) > 1e-3:
                f = objetivo / actual
                borde = mn.y
                Mi = losa.matrix_world.inverted()
                for v in losa.data.vertices:
                    p = losa.matrix_world @ v.co
                    p.y = borde + (p.y - borde) * f
                    v.co = Mi @ p
                losa.data.update()
            del losa.data["vuelo_previo"]

        bpy.context.view_layer.update()
        mn, mx = _caja(losa)
        piso = mx.z
        x0, x1 = mn.x + BORDE, mx.x - BORDE
        y0, y1 = mn.y + BORDE, mx.y - BORDE
        nombre = "pb_balcon_barandal" + sufijo
        hechos.append(nombre)

        # los dos tubos horizontales, en los tres lados libres
        for z, grosor in ((piso + ALTO, TUBO), (piso + MEDIO, TUBO * 0.8)):
            _barra("%s_frente_%d" % (nombre, int(z*100)),
                   ((x0+x1)/2, y1, z), (x1-x0, grosor, grosor), col)
            for lado, x in (("izq", x0), ("der", x1)):
                _barra("%s_%s_%d" % (nombre, lado, int(z*100)),
                       (x, (y0+y1)/2, z), (grosor, y1-y0, grosor), col)

        # postes: en las esquinas y repartidos por el frente
        n = max(2, int(round((x1-x0) / SEPARACION)) + 1)
        for i in range(n):
            x = x0 + (x1-x0) * i / (n - 1)
            _barra("%s_poste%d" % (nombre, i), (x, y1, piso + ALTO/2),
                   (POSTE, POSTE, ALTO), col)
        for lado, x in (("izq", x0), ("der", x1)):
            _barra("%s_poste_%s" % (nombre, lado), (x, y0 + 0.06, piso + ALTO/2),
                   (POSTE, POSTE, ALTO), col)
    return {"balcones": len(hechos), "cuales": hechos}
