"""La vecina del oeste (unidad v-1) estorba: el recorrido entero pasa DENTRO de
su lote (la camara vive en X = -1.5, y esa casa ocupa de X -7 a 0). Por eso
estaba oculta en el archivo LIGERA.

Pero al inicio, con la camara a 56 m, esa casa **si** tiene que estar: sin ella
la fila tiene un hueco. Asi que en vez de ocultarla para siempre:

    se ve  ->  se disuelve justo antes de que la camara entre a su lote
           ->  vuelve a aparecer en el remate, cuando la camara ya salio

Sus materiales los comparte con la casa del cliente (BK_aplanado_crema.001,
mb_vidrio...), asi que animarles el Alpha borraria tambien la casa buena. Por eso
a esta unidad se le hace **copia propia** de cada material compartido.

    aplicar()     /  deshacer()
"""
import bpy
from mathutils import Vector

SUF = "_vOeste"
LOTE = (-7.2, 0.2, 5.8, 16.2)        # X0, X1, Y0, Y1 del lote de la v-1
FUNDIDO_S = 0.42
ANTES_S = 0.12                        # margen antes de que la camara entre
VUELVE_S = None                       # segundo en que reaparece; None = al salir del lote
PASO = 2


def _fps():
    r = bpy.context.scene.render
    return r.fps / r.fps_base


def _bsdf(m):
    return next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if m.use_nodes else None


def objetos():
    """Todo lo de la unidad v-1: fachada clonada y cuerpo."""
    obs = []
    col = bpy.data.collections.get("VECINAS_FACHADA")
    if col:
        obs += [o for o in col.objects if o.name.endswith("_v-1")]
    col = bpy.data.collections.get("VECINAS")
    if col:
        obs += [o for o in col.objects if o.name.startswith("VEC_fila-1")]
    return obs


def deshacer():
    obs = objetos()
    n = 0
    for ob in obs:
        for slot in ob.material_slots:
            m = slot.material
            if m and m.name.endswith(SUF):
                orig = bpy.data.materials.get(m.name[:-len(SUF)])
                if orig:
                    slot.material = orig
                bpy.data.materials.remove(m)
                n += 1
        ob.animation_data_clear()
        ob.hide_viewport = ob.hide_render = False
    return n


def aplicar(vuelve_s=None):
    esc = bpy.context.scene
    cam = bpy.data.objects.get("CAM_RECORRIDO") or esc.camera
    fps = _fps()
    obs = objetos()
    if not obs:
        return {"error": "no encontre la unidad v-1"}

    # --- cuando la camara entra al lote de la vecina, y cuando sale ---------
    guarda = esc.frame_current
    ult = max(int(k.co[0]) for fc in cam.animation_data.action.fcurves
              for k in fc.keyframe_points)
    dentro = []
    for f in range(esc.frame_start, ult + 1, PASO):
        esc.frame_set(f)
        p = cam.matrix_world.translation
        if LOTE[0] < p.x < LOTE[1] and LOTE[2] < p.y < LOTE[3]:
            dentro.append(f)
    esc.frame_set(guarda)
    if not dentro:
        return {"error": "la camara nunca entra al lote; no hace falta tocar nada"}
    entra, sale = dentro[0], dentro[-1]

    f_ap0 = max(esc.frame_start + 1, int(entra - (ANTES_S + FUNDIDO_S) * fps))
    f_ap1 = max(f_ap0 + 2, int(entra - ANTES_S * fps))
    vs = vuelve_s if vuelve_s is not None else VUELVE_S
    if vs is not None:                 # reaparece a un segundo dado (el remate)
        f_vu0 = max(int(sale + 0.4 * fps), int(vs * fps) - 30)
    else:
        f_vu0 = int(sale + 0.4 * fps)
    f_vu1 = int(f_vu0 + FUNDIDO_S * fps)

    # --- copia propia de los materiales compartidos ------------------------
    mios = {o.name for o in obs}
    copias = {}
    for ob in obs:
        for slot in ob.material_slots:
            m = slot.material
            if not m or m.name.endswith(SUF):
                continue
            compartido = any(u.name not in mios for u in bpy.data.objects
                             if u.type == 'MESH' and m.name in [s.name for s in u.material_slots])
            if not compartido:
                copias.setdefault(m.name, m)
                continue
            nuevo = copias.get(m.name + SUF)
            if nuevo is None:
                nuevo = m.copy()
                nuevo.name = m.name + SUF
                copias[m.name + SUF] = nuevo
            slot.material = nuevo

    # --- animar el alpha de esas copias ------------------------------------
    tocados = []
    for m in set(list(copias.values())):
        b = _bsdf(m)
        try:
            m.blend_method = 'BLEND'
            m.shadow_method = 'NONE'
        except AttributeError:
            pass
        for f, a in ((f_ap0, 1.0), (f_ap1, 0.0), (f_vu0, 0.0), (f_vu1, 1.0)):
            if b:
                b.inputs["Alpha"].default_value = a
                m.node_tree.keyframe_insert(b.inputs["Alpha"].path_from_id("default_value"), frame=f)
            m.diffuse_color[3] = a       # esto es lo que obedece Workbench
            m.keyframe_insert("diffuse_color", index=3, frame=f)
        for datos in (m.node_tree.animation_data if b else None, m.animation_data):
            if datos and datos.action:
                for fc in datos.action.fcurves:
                    for k in fc.keyframe_points:
                        k.interpolation = 'BEZIER'
                        k.easing = 'EASE_IN_OUT'
        tocados.append(m.name)

    for ob in obs:
        ob.hide_viewport = ob.hide_render = False

    return {"objetos": len(obs), "materiales": sorted(tocados),
            "camara_dentro_del_lote": [entra, sale],
            "se_disuelve": [f_ap0, f_ap1], "vuelve": [f_vu0, f_vu1],
            "segundos": [round(f_ap0 / fps, 1), round(f_vu1 / fps, 1)]}
