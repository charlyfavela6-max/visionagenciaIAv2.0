"""Dos arreglos del recorrido:

1. **La pared si esta, y se quita con transparencia.** Los muros de
   CEBOLLA_muros estaban escondidos y desplazados (se abrian como cebolla).
   Aqui se regresan a su sitio real —el que marcan sus FANTASMAS— y en vez de
   moverse se **desvanecen** justo antes de que la camara entre al cuarto.
   Cada muro tiene su propio material (un usuario cada uno), asi que animar el
   Alpha no le pega a nada mas.

2. **El acercamiento al cuarto de lavado va muy rapido.** La camara se le echa
   encima entre los cuadros 637 y 668 (de 8.2 m a 3.9 m en 1.3 s). Se estira ese
   tramo y se recorre todo lo que venia despues —camara, muebles y muros— para
   que nada se desacomode.

    aplicar()      hace las dos cosas
    solo_muros()   /  solo_ritmo(factor)
"""
import bpy
from mathutils import Vector

CUARTO_M, PISO_MIN, PISO_MAX = 6.0, 0.2, 2.6   # 6 m: que se vea el muro antes de irse
FUNDIDO_S = 0.5      # lo que tarda un muro en desaparecer
ESPERA_S = 0.4       # se deja ver un momento antes de disolverse
PASO = 2
QUIETA = 0.20        # m por cuadro; de paso no cuenta como 'llego al cuarto'


def _fps():
    r = bpy.context.scene.render
    return r.fps / r.fps_base


def _bsdf(m):
    return next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)


# ------------------------------------------------------ 1. muros que se van ---

def limpiar_muros():
    """Borra las llaves de Alpha que puso una corrida anterior."""
    n = 0
    col = bpy.data.collections.get("CEBOLLA_muros")
    for ob in (col.objects if col else []):
        for slot in ob.material_slots:
            m = slot.material
            if not m:
                continue
            if m.use_nodes and m.node_tree.animation_data:
                m.node_tree.animation_data_clear()
                b = _bsdf(m)
                if b:
                    b.inputs["Alpha"].default_value = 1.0
            if m.animation_data:
                m.animation_data_clear()
            m.diffuse_color[3] = 1.0
            n += 1
    return n


def solo_muros():
    esc = bpy.context.scene
    limpiar_muros()
    cam = bpy.data.objects.get("CAM_RECORRIDO") or esc.camera
    fps = _fps()
    col = bpy.data.collections.get("CEBOLLA_muros")
    if not col:
        return {"error": "no hay CEBOLLA_muros"}

    # a su sitio real: el que ocupa su fantasma
    puestos = []
    for ob in col.objects:
        f = bpy.data.objects.get(ob.name + "_fantasma")
        ob.animation_data_clear()
        if f:
            ob.matrix_world = f.matrix_world.copy()
            f.hide_viewport = f.hide_render = True
            puestos.append(ob.name)
        ob.hide_viewport = ob.hide_render = False

    # sin esto las cajas se leen en la posicion VIEJA y los tiempos salen mal
    bpy.context.view_layer.update()

    # cuando llega la camara a cada muro
    guarda = esc.frame_current
    camino = []
    ant = None
    ult = max(int(k.co[0]) for fc in cam.animation_data.action.fcurves
              for k in fc.keyframe_points) if cam.animation_data else esc.frame_end
    for fr in range(esc.frame_start, min(int(esc.get("recorrido_fin", ult)), ult) + 1, PASO):
        esc.frame_set(fr)
        M = cam.matrix_world.copy()
        v = 99.0 if ant is None else (M.translation - ant).length / PASO
        camino.append((fr, M, v))
        ant = M.translation.copy()
    esc.frame_set(guarda)

    # y que el visor y el render de Workbench muestren color de material
    esc.display.shading.color_type = 'MATERIAL'
    for w in bpy.data.workspaces:
        for sc in w.screens:
            for ar in sc.areas:
                if ar.type == 'VIEW_3D':
                    for sp in ar.spaces:
                        if sp.type == 'VIEW_3D':
                            sp.shading.color_type = 'MATERIAL'

    salida = []
    for ob in col.objects:
        pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        centro = sum(pts, Vector()) / 8.0
        piso = min(p.z for p in pts)
        llega = None
        for fr, M, vel in camino:
            rel = M.inverted() @ centro
            prof = -rel.z
            if not (0.1 < prof < CUARTO_M):
                continue
            if not (PISO_MIN < (M.translation.z - piso) < PISO_MAX):
                continue
            if vel >= QUIETA:          # solo va pasando, no llego
                continue
            llega = fr
            break
        if llega is None:
            continue
        f0 = max(esc.frame_start + 1, int(llega + ESPERA_S * fps))
        f1 = int(f0 + FUNDIDO_S * fps)
        for slot in ob.material_slots:
            m = slot.material
            if not m or not m.use_nodes:
                continue
            b = _bsdf(m)
            if not b:
                continue
            try:
                m.blend_method = 'BLEND'          # EEVEE; Cycles no lo necesita
                m.shadow_method = 'NONE'
            except AttributeError:
                pass                              # 4.2+ ya no tiene shadow_method
            a = b.inputs["Alpha"]
            a.default_value = 1.0
            m.node_tree.keyframe_insert(a.path_from_id("default_value"), frame=f0)
            a.default_value = 0.0
            m.node_tree.keyframe_insert(a.path_from_id("default_value"), frame=f1)
            # Workbench —que es el motor de esta escena— ni mira el nodo: lo que
            # obedece es el alpha de "Viewport Display". Se anima tambien.
            m.diffuse_color[3] = 1.0
            m.keyframe_insert("diffuse_color", index=3, frame=f0)
            m.diffuse_color[3] = 0.0
            m.keyframe_insert("diffuse_color", index=3, frame=f1)
            if m.animation_data:
                for fc in m.animation_data.action.fcurves:
                    for k in fc.keyframe_points:
                        k.interpolation = 'BEZIER'
                        k.easing = 'EASE_IN_OUT'
            for fc in m.node_tree.animation_data.action.fcurves:
                for k in fc.keyframe_points:
                    k.interpolation = 'BEZIER'
                    k.easing = 'EASE_IN_OUT'
        salida.append({"muro": ob.name, "se_va_en": f0, "termina": f1})
    return {"reubicados": len(puestos), "muros": sorted(salida, key=lambda d: d["se_va_en"])}


# ------------------------------------------------------- 2. ritmo del lavado ---

def _remap(x, a, b, k):
    if x <= a:
        return x
    if x <= b:
        return a + (x - a) * k
    return x + (b - a) * (k - 1.0)


def solo_ritmo(factor=2.0, a=637, b=668):
    esc = bpy.context.scene
    if esc.get("ritmo_lavado") is not None:
        return {"saltado": "ya se habia estirado", "factor_previo": esc["ritmo_lavado"]}
    n = 0
    for act in bpy.data.actions:
        for fc in act.fcurves:
            for k in fc.keyframe_points:
                k.co[0] = _remap(k.co[0], a, b, factor)
                k.handle_left[0] = _remap(k.handle_left[0], a, b, factor)
                k.handle_right[0] = _remap(k.handle_right[0], a, b, factor)
                n += 1
            fc.update()
    delta = int(round((b - a) * (factor - 1.0)))
    esc.frame_end += delta
    if "recorrido_fin" in esc:
        esc["recorrido_fin"] = int(esc["recorrido_fin"]) + delta
    esc["ritmo_lavado"] = factor
    return {"llaves_recorridas": n, "estirado": [a, b], "factor": factor,
            "cuadros_agregados": delta, "nuevo_fin": esc.frame_end}


def aplicar(factor=2.0):
    r = {"muros": solo_muros()}
    r["ritmo"] = solo_ritmo(factor)
    return r
