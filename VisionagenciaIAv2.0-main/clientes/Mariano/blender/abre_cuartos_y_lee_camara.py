"""Corre en el Blender de Carlos: lee su encuadre y le quita los muros que tapan.

Se manda por el conector con `enviar_abre_cuartos.py`. Hace dos cosas y no
toca nada mas:

1. LEE EL ANGULO QUE EL TIENE PUESTO. No inventa camara: saca la del VISOR
   (el `region_3d` del primer View 3D) y tambien la de la escena si hay. De ahi
   salen los numeros que aqui en el Codespace se usan para renderizar el corte
   y las mascaras EXACTAMENTE con su encuadre.

2. ESCONDE LOS MUROS QUE TAPAN, para que se vea cada cuarto. No los borra:
   `hide_render` y `hide_viewport`, y devuelve la lista, asi que
   `restaurar()` los regresa.

   Cuales tapa: los que estan ENTRE su ojo y el centro de la casa. Se decide
   por geometria, no por nombre — un muro es algo delgado en planta
   (min(dx,dy) < 0.40 m) y alto (dz > 1.5 m) dentro de la huella de la casa.
   De esos, se apagan los que caen del lado del ojo, proyectando el centro de
   cada muro sobre la direccion de vista.

   Ojo con lo que YA se sabe de este archivo:
   · los `*_fantasma` son copias del mismo muro en el mismo sitio (el efecto de
     desvanecido) — se apagan siempre, porque pelean por el pixel;
   · los `_v1`, `_v-1`, `_v2`... son las casas VECINAS clonadas a +-7 m en x;
   · `limpia()` esconde `CEBOLLA_muros`, que son 12 muros REALES de la casa.
"""
import json

import bpy
from mathutils import Vector

CASA = (1.10, 6.90, 6.67, 15.52)          # x0 x1 y0 y1
CENTRO = Vector((4.00, 11.10, 1.40))
GRUESO_MAX = 0.40
ALTO_MIN = 1.50


def es_vecina(nombre):
    cola = nombre.rsplit("_", 1)[-1]
    return cola.startswith("v") and cola[1:].lstrip("-").isdigit()


def encuadre():
    """El angulo que Carlos tiene puesto, del visor y de la camara de escena."""
    fuera = {}
    for area in bpy.context.screen.areas:
        if area.type != 'VIEW_3D':
            continue
        esp = area.spaces[0]
        r3d = esp.region_3d
        ojo = r3d.view_matrix.inverted().translation
        fuera["visor"] = {
            "ojo": [round(v, 3) for v in ojo],
            "mira": [round(v, 3) for v in r3d.view_location],
            "distancia": round(r3d.view_distance, 3),
            "lente_mm": round(esp.lens, 2),
            "tipo": r3d.view_perspective,
            "clip": [round(esp.clip_start, 3), round(esp.clip_end, 1)],
        }
        break
    cam = bpy.context.scene.camera
    if cam:
        fuera["camara_escena"] = {
            "nombre": cam.name,
            "sitio": [round(v, 3) for v in cam.matrix_world.translation],
            "euler": [round(v, 4) for v in cam.matrix_world.to_euler()],
            "lente_mm": round(getattr(cam.data, "lens", 0.0), 2),
        }
    fuera["cuadro"] = bpy.context.scene.frame_current
    return fuera


def muros():
    """Los muros de la casa, por geometria. Devuelve [(objeto, centro)]."""
    x0, x1, y0, y1 = CASA
    fuera = []
    for o in bpy.data.objects:
        if o.type != 'MESH' or es_vecina(o.name):
            continue
        b = [o.matrix_world @ Vector(v) for v in o.bound_box]
        ax, bx = min(v.x for v in b), max(v.x for v in b)
        ay, by = min(v.y for v in b), max(v.y for v in b)
        az, bz = min(v.z for v in b), max(v.z for v in b)
        if bx < x0 - 0.3 or ax > x1 + 0.3 or by < y0 - 0.3 or ay > y1 + 0.3:
            continue
        if bz - az < ALTO_MIN or min(bx - ax, by - ay) > GRUESO_MAX:
            continue
        fuera.append((o, Vector(((ax + bx) / 2, (ay + by) / 2, (az + bz) / 2))))
    return fuera


def abrir(margen=0.0):
    """Apaga los muros que quedan entre el ojo y el centro de la casa."""
    enc = encuadre()
    if "visor" not in enc:
        return {"error": "no encontre un View 3D abierto", "encuadre": enc}
    ojo = Vector(enc["visor"]["ojo"])
    hacia = (CENTRO - ojo)
    hacia.z = 0.0
    if hacia.length < 1e-6:
        hacia = Vector((1.0, 0.0, 0.0))
    hacia.normalize()

    apagados = []
    for o, c in muros():
        plano = Vector((c.x - CENTRO.x, c.y - CENTRO.y, 0.0))
        # proyeccion negativa = esta del lado del ojo, o sea tapa
        if o.name.endswith("_fantasma") or plano.dot(hacia) < -margen:
            if not o.hide_viewport or not o.hide_render:
                o.hide_viewport = True
                o.hide_render = True
                apagados.append(o.name)
    bpy.context.view_layer.update()
    return {"encuadre": enc, "apagados": apagados, "cuantos": len(apagados)}


def restaurar(nombres):
    n = 0
    for nom in nombres:
        o = bpy.data.objects.get(nom)
        if o:
            o.hide_viewport = False
            o.hide_render = False
            n += 1
    return n


RESULTADO = json.dumps(abrir(), ensure_ascii=False)
print("RESULTADO_JSON " + RESULTADO)
