"""Rescate: devolverle a los muebles su tamano.

Los muebles son cubos unitarios (la malla va de -0.5 a 0.5); su forma real vive
en `scale`. `muebles_aparecen.deshacer()` desemparentaba con
`h.matrix_world = M`, y esa M se lee **en el cuadro actual** — donde el Empty
estaba aplastado (0.88, 0.88, 0.02). Cada re-corrida horneaba ese aplastamiento
en el hijo: dos o tres pasadas y la escala en Z llego a cero.

De la escala no se vuelve dividiendo (0.02^3 = 8e-6: la precision ya no da), pero
el .blend en disco nunca se sobreescribio, asi que ahi siguen las buenas. Esto
las lee de ahi y se las pone a los objetos vivos, por nombre.

    reparar()                     lee de /Users/juancarlos/catania_LIGERA.blend
    reparar("/otra/ruta.blend")
"""
import bpy
import os

# OJO: nunca el archivo que esta abierto — leerse a si mismo trono Blender.
# catania.blend es el archivo sano del que salio la version LIGERA.
ORIGEN = "/Users/juancarlos/catania.blend"
LOTE = 40


def reparar(ruta=None, coleccion="MUEBLES"):
    ruta = ruta or ORIGEN
    if not os.path.exists(ruta):
        return {"error": "no existe " + ruta}
    if os.path.normpath(ruta) == os.path.normpath(bpy.data.filepath):
        return {"error": "ese es el archivo abierto; leerlo desde si mismo truena"}
    col = bpy.data.collections.get(coleccion)
    if not col:
        return {"error": "no existe la coleccion " + coleccion}
    vivos = {o.name: o for o in col.objects}

    # soltar de los empties SIN conservar matriz: el tamano bueno viene del disco
    for ob in vivos.values():
        ob.parent = None
    for e in [o for o in bpy.data.objects if o.name.startswith("AP_")]:
        bpy.data.objects.remove(e, do_unlink=True)
    ap = bpy.data.collections.get("APARICION")
    if ap and not ap.objects:
        bpy.data.collections.remove(ap)
    bpy.context.view_layer.update()

    nombres = sorted(vivos)
    reparados, faltantes = [], []
    for i in range(0, len(nombres), LOTE):
        pedazo = nombres[i:i + LOTE]
        with bpy.data.libraries.load(ruta, link=True) as (dentro, fuera):
            hay = [n for n in pedazo if n in dentro.objects]
            faltantes.extend(n for n in pedazo if n not in dentro.objects)
            fuera.objects = hay
        traidos = [o for o in fuera.objects if o is not None]
        for src in traidos:
            dst = vivos.get(src.name)
            if dst is None:
                continue
            dst.location = src.location.copy()
            dst.rotation_mode = src.rotation_mode
            if src.rotation_mode == 'QUATERNION':
                dst.rotation_quaternion = src.rotation_quaternion.copy()
            else:
                dst.rotation_euler = src.rotation_euler.copy()
            dst.scale = src.scale.copy()
            dst.delta_location = src.delta_location.copy()
            dst.delta_scale = src.delta_scale.copy()
            dst.hide_viewport = dst.hide_render = False
            reparados.append(dst.name)
        for o in traidos:
            bpy.data.objects.remove(o, do_unlink=True)
        for lib in list(bpy.data.libraries):
            if os.path.normpath(bpy.path.abspath(lib.filepath)) == os.path.normpath(ruta):
                bpy.data.libraries.remove(lib)

    bpy.context.view_layer.update()
    ejemplo = bpy.data.objects.get("n1_cama_1_base")
    return {"origen": ruta, "reparados": len(reparados), "faltantes": faltantes[:10],
            "n_faltantes": len(faltantes),
            "cama_ahora": [round(v, 3) for v in ejemplo.scale] if ejemplo else None,
            "cama_alto_m": round(ejemplo.dimensions.z, 3) if ejemplo else None}
