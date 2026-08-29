"""El remate: la camara se despega de la casa y sube hasta que caben en cuadro
el fraccionamiento entero y el Pacifico.

Se agregan llaves DESPUES del ultimo cuadro del recorrido (no se toca ni una de
las que ya estaban) y se alarga el rango de la escena. La altura y el encuadre
salen de la medicion real: la calle esta a 37 m sobre el mar y la orilla a
461 m, asi que hay que subir ~150 m para que el mar entre en un 9:16.

    alejar()      agrega el remate
    deshacer()    borra solo las llaves que agrego este script
"""
import bpy
from mathutils import Vector

CAM = "CAM_RECORRIDO"
DUR_S = 6.0          # lo que dura el alejamiento
MIRA_FIN = Vector((3.5, 520.0, -34.0))     # el agua, a 520 m de la calle


def _fps():
    r = bpy.context.scene.render
    return r.fps / r.fps_base


def _mirando(desde, hacia):
    return (hacia - desde).to_track_quat('-Z', 'Y').to_euler()


def deshacer(desde=None):
    esc = bpy.context.scene
    cam = bpy.data.objects[CAM]
    if not (cam.animation_data and cam.animation_data.action):
        return 0
    corte = desde if desde is not None else esc.get("recorrido_fin", esc.frame_end)
    n = 0
    for fc in cam.animation_data.action.fcurves:
        for k in [k for k in fc.keyframe_points if k.co[0] > corte]:
            fc.keyframe_points.remove(k)
            n += 1
    esc.frame_end = int(corte)
    return n


def alejar():
    esc = bpy.context.scene
    cam = bpy.data.objects.get(CAM)
    if cam is None:
        return {"error": "no esta " + CAM}
    fps = _fps()
    if "recorrido_fin" not in esc:
        esc["recorrido_fin"] = esc.frame_end          # para poder deshacer
    f_ini = int(esc["recorrido_fin"])
    deshacer(f_ini)

    esc.frame_set(f_ini)
    p0 = cam.matrix_world.translation.copy()
    lente0 = cam.data.lens

    # el arco: se despega de espaldas a la casa, gira al mar y sube
    pasos = [
        (0.00, p0,                                  Vector((3.5, 11.0, 1.0))),
        (0.22, Vector((p0.x - 2, p0.y + 6, 6.0)),   Vector((3.5, 11.0, 1.0))),
        (0.48, Vector((3.5, -35.0, 34.0)),          Vector((3.5, 60.0, -6.0))),
        (0.74, Vector((3.5, -160.0, 82.0)),         Vector((3.5, 260.0, -20.0))),
        (1.00, Vector((3.5, -300.0, 150.0)),        MIRA_FIN),
    ]
    dur = DUR_S * fps
    for t, pos, mira in pasos:
        f = int(round(f_ini + t * dur))
        cam.location = pos
        cam.rotation_euler = _mirando(pos, mira)
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_euler", frame=f)
    esc.frame_end = int(round(f_ini + dur))

    act = cam.animation_data.action
    for fc in act.fcurves:
        for k in fc.keyframe_points:
            if k.co[0] >= f_ini:
                k.interpolation = 'BEZIER'
                k.easing = 'EASE_IN_OUT'
    esc.frame_set(1)
    return {"desde": f_ini, "hasta": esc.frame_end, "segundos": round(DUR_S, 1),
            "fps": round(fps, 2), "altura_final_m": 150,
            "altura_sobre_el_mar_m": 150 + 37,
            "lente": lente0,
            "mira_final": [round(v, 1) for v in MIRA_FIN]}
