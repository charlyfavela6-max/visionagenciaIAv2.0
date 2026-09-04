"""Los muebles brotan CUARTO POR CUARTO, cuando la camara llega a ese cuarto.

    aplicar()   reescribe las llaves de los empties AP_*
    informe()   solo dice en que cuadro entraria cada cuarto, sin tocar nada

QUE TENIA DE MALO LO DE ANTES
-----------------------------
`muebles_aparecen.py` dispara PIEZA POR PIEZA, en el cuadro en que esa pieza
entra al encuadre y la camara va despacio. Suena bien y en el papel lo es, pero
en este recorrido falla por dos lados:

1. **Se desperdiga.** La camara de interiores va siempre por fuera del muro
   poniente deslizandose en Y, asi que ve el cuarto en diagonal: el buro entra
   al cuadro dos segundos antes que la cama del mismo cuarto. El cuarto no
   "se arma", parpadea.

2. **Deja piezas para el final.** Si una pieza nunca cumple las tres
   condiciones a la vez (dentro del cuadro, mismo piso, camara lenta), no le
   toca cuadro de entrada. Por eso hubo que agregar `brotes()` a mano en
   `muebles_referencia.py` — un parche a un sintoma.

COMO LO HACE ESTE
-----------------
La camara entra a un CUARTO, no a un mueble. Con las cajas de
`camaras_auto.CAJAS` (los limites reales de los muros divisorios) se mira el
recorrido cuadro por cuadro y se anota cuando la camara **esta a la altura de
ese cuarto**: mismo nivel en Z, y su Y dentro del tramo del cuarto. Ese es el
cuadro de entrada del cuarto entero.

Dentro del cuarto sigue mandando la regla que salio del video de Jahaziel:
la pieza ancla primero, los accesorios detras, **de lejos hacia cerca**, para
que lo que tapa sea lo ultimo en aparecer.

Asi ningun mueble sale antes de que su cuarto se vea, ninguno se queda para el
final, y el cuarto se arma de una pieza.
"""
import os
import sys

import bpy
from mathutils import Vector

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

PREFIJO = "AP_"
CRECER_S = 0.32       # lo que tarda una pieza en levantarse
ESCALON_S = 0.10      # separacion entre pieza y pieza dentro del cuarto
ANTES_S = 0.25        # arranca un pelo antes de que la camara encare el cuarto
PASO = 2

# Las cajas y las alturas salen de `camaras_auto.py`, que a su vez las saca de
# los muros divisorios del archivo. Se copian aqui para no importar Blender
# dentro de Blender.
CAJAS = {
    "n1_recamara2":     ("n1", 6.67, 10.24),
    "n1_bano":          ("n1", 10.31, 11.99),
    "n1_recamara1":     ("n1", 12.06, 15.52),
    "n1_bodega":        ("n1", 6.67, 10.00),
    "n1_estudio":       ("n1", 10.00, 12.80),
    "n1_lavado":        ("n1", 12.80, 15.52),
    "pb_sala":          ("pb", 6.67, 10.24),
    "pb_mediobano":     ("pb", 10.31, 11.99),
    "pb_recamara_ppal": ("pb", 12.06, 15.52),
    "pb_escalera":      ("pb", 6.67, 10.00),
    "pb_vestidor":      ("pb", 10.00, 12.80),
    "pb_bano_ppal":     ("pb", 12.80, 15.52),
    "pa_cocina":        ("pa", 6.67, 9.60),
    "pa_comedor":       ("pa", 9.60, 12.20),
    "pa_sala":          ("pa", 9.40, 12.60),
    "rg_terraza":       ("rg", 12.20, 15.52),
}
NIVELES = {"n1": (-2.75, -0.20), "pb": (-0.05, 2.60),
           "pa": (2.80, 5.60), "rg": (2.80, 5.60)}


def _fps():
    r = bpy.context.scene.render
    return r.fps / r.fps_base


def _recorrido(cam, esc):
    guarda = esc.frame_current
    sal = []
    for f in range(esc.frame_start, esc.frame_end + 1, PASO):
        esc.frame_set(f)
        sal.append((f, cam.matrix_world.translation.copy()))
    esc.frame_set(guarda)
    return sal


def entradas(camino):
    """Cuadro en que la camara llega a cada cuarto."""
    fuera = {}
    for cuarto, (nivel, y0, y1) in CAJAS.items():
        piso, techo = NIVELES[nivel]
        for f, p in camino:
            # la camara de interiores va ~1.5 m sobre el piso del nivel
            if not (piso + 0.4 < p.z < techo + 0.8):
                continue
            if y0 - 0.6 <= p.y <= y1 + 0.6:
                fuera[cuarto] = f
                break
    return fuera


def _cuarto_de(centro):
    for cuarto, (nivel, y0, y1) in CAJAS.items():
        piso, techo = NIVELES[nivel]
        if piso - 0.15 <= centro.z <= techo + 0.15 and y0 <= centro.y <= y1:
            return cuarto
    return None


def informe():
    esc = bpy.context.scene
    cam = bpy.data.objects.get("CAM_RECORRIDO")
    if cam is None:
        return {"error": "no hay CAM_RECORRIDO"}
    camino = _recorrido(cam, esc)
    ent = entradas(camino)
    fps = _fps()
    empties = [o for o in bpy.data.objects
               if o.name.startswith(PREFIJO) and o.type == 'EMPTY']
    reparto = {}
    for e in empties:
        c = _cuarto_de(e.matrix_world.translation)
        reparto.setdefault(c, []).append(e.name)
    return {"entradas": {k: (v, round(v / fps, 1)) for k, v in sorted(ent.items(),
                                                                     key=lambda kv: kv[1])},
            "empties": len(empties),
            "por_cuarto": {k: len(v) for k, v in sorted(reparto.items(),
                                                        key=lambda kv: -len(kv[1]))},
            "sin_cuarto": reparto.get(None, [])[:10],
            "rango": [esc.frame_start, esc.frame_end]}


def aplicar():
    esc = bpy.context.scene
    cam = bpy.data.objects.get("CAM_RECORRIDO")
    if cam is None:
        return {"error": "no hay CAM_RECORRIDO"}
    fps = _fps()
    camino = _recorrido(cam, esc)
    ent = entradas(camino)
    crecer = max(1, int(CRECER_S * fps))
    escalon = max(1, int(ESCALON_S * fps))
    antes = int(ANTES_S * fps)

    empties = [o for o in bpy.data.objects
               if o.name.startswith(PREFIJO) and o.type == 'EMPTY']
    porc = {}
    for e in empties:
        porc.setdefault(_cuarto_de(e.matrix_world.translation), []).append(e)

    tocados, sin_entrada = 0, []
    for cuarto, lista in porc.items():
        f0 = ent.get(cuarto)
        if f0 is None:
            # sin cuadro de entrada: se deja para el arranque del nivel, nunca
            # para el final — que era la falla vieja
            sin_entrada.append(cuarto)
            f0 = esc.frame_start + 12
        f0 = max(esc.frame_start + 1, f0 - antes)
        # de lejos hacia cerca: lo que tapa, al final
        ojo = None
        for f, p in camino:
            if f >= f0:
                ojo = p
                break
        if ojo is None:
            ojo = camino[0][1]
        lista.sort(key=lambda e: -(e.matrix_world.translation - ojo).length)
        for i, e in enumerate(lista):
            e.animation_data_clear()
            a = f0 + i * escalon
            b = a + crecer
            e.scale = (1.0, 1.0, 0.02)
            e.keyframe_insert("scale", frame=max(esc.frame_start, a - 1))
            e.scale = (1.0, 1.0, 0.02)
            e.keyframe_insert("scale", frame=a)
            e.scale = (1.0, 1.0, 1.0)
            e.keyframe_insert("scale", frame=b)
            if e.animation_data and e.animation_data.action:
                for fc in e.animation_data.action.fcurves:
                    for k in fc.keyframe_points:
                        k.interpolation = 'BACK' if k.co[0] == b else 'LINEAR'
                        k.easing = 'EASE_OUT'
            tocados += 1
    bpy.context.view_layer.update()
    return {"empties_animados": tocados,
            "cuartos": len(porc),
            "sin_cuadro_de_entrada": sin_entrada,
            "entradas": {k: v for k, v in sorted(ent.items(), key=lambda kv: kv[1])}}
