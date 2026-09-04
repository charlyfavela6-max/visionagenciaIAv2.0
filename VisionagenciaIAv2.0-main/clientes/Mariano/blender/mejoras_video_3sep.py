"""Lo que el video de Mariano del 3 sep 2026 destapo que le faltaba al modelo.

    blender -b <blend> -P mejoras_video_3sep.py            # aplica y guarda
    blender -b <blend> -P mejoras_video_3sep.py -- nosave  # solo aplica

Todo lo que crea va a la coleccion `MEJORAS_VIDEO_3SEP`, asi que se quita
borrando la coleccion. No toca nada de lo que ya existia.

LO QUE SE DESCUBRIO, mirando el video contra el inventario del archivo:

1. LA BODEGA (`n1_bodega`) ESTABA COMPLETAMENTE VACIA — ni un objeto. En el
   video se ve con repisas abiertas, iguales a las del vestidor.

2. LA RECAMARA PRINCIPAL no tenia la CABECERA CAPITONADA ARQUEADA ni el MURO
   CHOCOLATE del cuadro g15. Solo la cama king con cabecera plana. El muro se
   pone como tablero delgado pegado al muro y NO se repinta el muro real, que
   es compartido con el otro cuarto.

3. El sofa de la planta alta era `mb_terracota` y en el video es ROJO VINO.
   Eso va aparte, repintando el material (`mb_vino`).

Y una cuarta, que no es geometria sino un error de los guiones: las
`rg_jardinera_*` SI existen — son dos jardineras rectangulares de concreto con
19 matas — y `limpia()` las escondia creyendolas placeholder. Por eso la IA
sacaba la azotea pelada. Corregido en `cuartos_camara.py`.

OJO CON LOS NIVELES: la terraza NO esta arriba de la planta alta, esta EN la
misma losa (z 2.80). La casa tiene TRES losas, no cuatro.
"""
import math
import sys

import bpy
from mathutils import Vector


def caja(pref):
    b = []
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.startswith(pref) and "_v" not in o.name[len(pref):][:3]:
            b += [o.matrix_world @ Vector(v) for v in o.bound_box]
    if not b:
        return None
    return (min(v.x for v in b), max(v.x for v in b),
            min(v.y for v in b), max(v.y for v in b),
            min(v.z for v in b), max(v.z for v in b))


def mat(nombre, rgb, rug=0.7):
    m = bpy.data.materials.get(nombre)
    if m is None:
        m = bpy.data.materials.new(nombre)
        m.use_nodes = True
        b = m.node_tree.nodes.get("Principled BSDF")
        if b:
            b.inputs["Base Color"].default_value = (*rgb, 1.0)
            if "Roughness" in b.inputs:
                b.inputs["Roughness"].default_value = rug
    m.diffuse_color = (*rgb, 1.0)      # Workbench pinta con ESTO, no con el nodo
    return m


def coleccion():
    c = bpy.data.collections.get("MEJORAS_VIDEO_3SEP")
    if c is None:
        c = bpy.data.collections.new("MEJORAS_VIDEO_3SEP")
        bpy.context.scene.collection.children.link(c)
    return c


def bloque(col, nombre, x0, x1, y0, y1, z0, z1, material):
    vieja = bpy.data.objects.get(nombre)
    if vieja:
        bpy.data.objects.remove(vieja, do_unlink=True)
    me = bpy.data.meshes.new(nombre)
    ver = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
           (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    car = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4),
           (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me.from_pydata(ver, [], car)
    me.update()
    o = bpy.data.objects.new(nombre, me)
    o.data.materials.append(material)
    col.objects.link(o)
    return o


def aplica():
    col = coleccion()
    roble = mat("mb_roble_claro", (0.72, 0.58, 0.42))
    choco = mat("mb_chocolate", (0.20, 0.12, 0.09), 0.85)
    tela = mat("mb_cabecera_crema", (0.86, 0.82, 0.74), 0.9)
    hecho = {}

    # 1) la bodega, que estaba vacia
    x0, x1, y1, piso = 4.90, 6.80, 8.60, -2.70
    n = 0
    for k, z in enumerate((0.35, 0.85, 1.35, 1.85, 2.35)):
        bloque(col, "n1_bodega_repisa_%d" % k, x0, x1, y1 - 0.42, y1,
               piso + z, piso + z + 0.03, roble); n += 1
    for k, x in enumerate((x0, (x0 + x1) / 2, x1 - 0.03)):
        bloque(col, "n1_bodega_costado_%d" % k, x, x + 0.03, y1 - 0.42, y1,
               piso, piso + 2.40, roble); n += 1
    hecho["bodega"] = n

    # 2) la recamara principal: cabecera arqueada y muro chocolate
    c = caja("pb_cama_king")
    if c:
        bx0, bx1, _by0, by1, bz0, _bz1 = c
        ancho = bx1 - bx0
        py = by1 + 0.02
        bloque(col, "pb_muro_chocolate", bx0 - 0.55, bx1 + 0.55, py, py + 0.04,
               bz0 - 0.42, bz0 + 2.35, choco)
        bloque(col, "pb_cabecera_ppal", bx0 - 0.10, bx1 + 0.10, py - 0.10, py,
               bz0 - 0.35, bz0 + 0.85, tela)
        pasos = 7
        for i in range(pasos):
            t = (i + 0.5) / pasos
            alto = 0.34 * math.sin(math.pi * t)        # el arco de la cabecera
            px0 = bx0 - 0.10 + (ancho + 0.20) * i / pasos
            px1 = bx0 - 0.10 + (ancho + 0.20) * (i + 1) / pasos
            bloque(col, "pb_cabecera_arco_%d" % i, px0, px1, py - 0.10, py,
                   bz0 + 0.85, bz0 + 0.85 + alto, tela)
        hecho["cabecera"] = pasos
    else:
        hecho["cabecera"] = "sin pb_cama_king"

    # 3) el sofa de arriba, que en el video es rojo vino y no terracota
    vino = mat("mb_vino", (0.36, 0.07, 0.09), 0.75)
    tocados = 0
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.startswith("pa_sofa"):
            if o.material_slots:
                for i in range(len(o.material_slots)):
                    o.material_slots[i].material = vino
            else:
                o.data.materials.append(vino)
            tocados += 1
    hecho["sofa_vino"] = tocados

    # 4) las jardineras del roof NO son placeholder: que nunca queden escondidas
    vueltas = 0
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.startswith(("rg_jardinera", "rg_mata")):
            if o.hide_render or o.hide_viewport:
                o.hide_render = o.hide_viewport = False
                vueltas += 1
    hecho["jardineras_devueltas"] = vueltas

    bpy.context.view_layer.update()
    return hecho


if __name__ == "__main__":
    print("MEJORAS:", aplica())
    arg = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "nosave" not in arg:
        bpy.ops.wm.save_mainfile()
        print("guardado", bpy.data.filepath)
