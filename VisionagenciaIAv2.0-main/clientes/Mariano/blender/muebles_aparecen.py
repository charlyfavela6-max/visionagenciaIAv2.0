"""Los muebles aparecen cuarto por cuarto, al estilo del video de Jahaziel
Trevino (instagram.com/p/DWUDWyqjF-c): cada pieza **crece desde el piso**
—aplastada en Z y estirandose hasta su altura— escalonada una tras otra,
mientras la camara sigue avanzando. El mueble no se desvanece: brota.

Dos reglas que salen de mirar el video cuadro por cuadro:
  * la pieza ancla (sofa, cama) sale primero y tarda ~0.30 s en crecer;
  * los accesorios entran cada ~0.12 s, de lejos hacia cerca.

Esa ultima regla es tambien la respuesta a "el mueble que no deja ver": lo que
queda mas cerca de la camara es lo que tapa, y por eso es lo ultimo en salir.
Si ademas una pieza se le viene encima a la camara (mas cerca de CERCA_M) se
espera hasta que la camara la deja atras.

Se anima un Empty por mueble, no los objetos: asi crece la pieza completa
(patas, cojines y respaldo juntos) y no cada caja por su lado.

    aplicar()     construye todo (es re-ejecutable: primero deshace)
    deshacer()    quita empties, padres y llaves, y deja los muebles quietos
"""
import bpy
from mathutils import Vector

COL_AP    = "APARICION"
PREFIJO   = "AP_"
CERCA_M   = 2.2      # mas cerca que esto, tapa la vista
CUARTO_M  = 11.0     # la camara ve el cuarto completo desde fuera del muro oeste
PISO_MIN, PISO_MAX = 0.2, 2.6   # la camara va ~1.5 m arriba del piso del cuarto
CRECER_S  = 0.30     # lo que tarda una pieza en levantarse
ESCALON_S = 0.12     # separacion entre pieza y pieza
ESPERA_S  = 0.20     # respiro despues de que la camara llega al cuarto
PASO      = 2        # cada cuantos cuadros se muestrea el recorrido
QUIETA    = 0.20     # m por cuadro: mas rapido que esto, la camara va de paso


def _fps():
    r = bpy.context.scene.render
    return r.fps / r.fps_base


def _grupos():
    """Junta los objetos de MUEBLES por pieza: rg_sillon_1_cojin2 -> rg_sillon_1."""
    col = bpy.data.collections.get("MUEBLES")
    if not col:
        return {}
    obs = [o for o in col.objects if o.type == 'MESH']
    nombres = [o.name for o in obs]
    def clave(n):
        p = n.split("_")
        for corte in range(len(p) - 1, 1, -1):
            cand = "_".join(p[:corte])
            if any(x != n and x.startswith(cand + "_") for x in nombres):
                return cand
        return n
    g = {}
    for o in obs:
        g.setdefault(clave(o.name), []).append(o)
    return g


def _caja(obs):
    pts = [o.matrix_world @ Vector(c) for o in obs for c in o.bound_box]
    mn = Vector([min(p[i] for p in pts) for i in range(3)])
    mx = Vector([max(p[i] for p in pts) for i in range(3)])
    return mn, mx


def _recorrido(cam, esc):
    """[(cuadro, matriz, inversa, lente, velocidad)] muestreado UNA vez.

    La inversa y el lente se guardan aqui a proposito: antes se calculaba el
    encuadre moviendo el objeto camara y llamando world_to_camera_view, o sea
    una evaluacion del depsgraph por mueble y por muestra —37 mil sobre una
    escena de 1129 objetos— y eso fue lo que dejo Blender clavado.
    """
    guarda = esc.frame_current
    sal, ant = [], None
    for f in range(esc.frame_start, esc.frame_end + 1, PASO):
        esc.frame_set(f)
        M = cam.matrix_world.copy()
        v = 99.0 if ant is None else (M.translation - ant).length / PASO
        sal.append((f, M, M.inverted(), cam.data.lens, v))
        ant = M.translation.copy()
    esc.frame_set(guarda)
    return sal


def _visibilidad(centro, piso, camino, cam_data, esc):
    """Cuando entra al cuadro, y hasta cuando lo tiene encima.

    El encuadre se calcula proyectando a mano: en coordenadas de camara, un
    punto cae dentro si |x| y |y| no pasan de la mitad del sensor escalada por
    profundidad/lente. Nada de mover objetos.
    """
    sx = cam_data.sensor_width
    r = esc.render
    aspecto = (r.resolution_y * r.pixel_aspect_y) / float(r.resolution_x * r.pixel_aspect_x)
    sy = sx * aspecto                      # sensor ajustado a lo ancho (AUTO horizontal)
    entra, ultimo_cerca, dist_entra = None, None, None
    for f, M, Minv, lente, vel in camino:
        rel = Minv @ centro
        prof = -rel.z
        if prof <= 0.1:
            continue
        mitad_x = prof * (sx / 2.0) / lente
        mitad_y = prof * (sy / 2.0) / lente
        dentro = abs(rel.x) < mitad_x and abs(rel.y) < mitad_y
        mismo_piso = PISO_MIN < (M.translation.z - piso) < PISO_MAX
        if dentro and prof < CUARTO_M and mismo_piso and vel < QUIETA and entra is None:
            entra, dist_entra = f, prof
        if dentro and prof < CERCA_M:
            ultimo_cerca = f
    return entra, ultimo_cerca, dist_entra


def deshacer():
    """Suelta los muebles de sus empties SIN hornearles el aplastamiento.

    Aqui estuvo el destrozo: `h.matrix_world = M` lee la matriz **del cuadro
    actual**, y si el Empty estaba en (0.88, 0.88, 0.02) —que es como arranca
    la animacion— esa escala se le quedaba grabada al mueble. Dos o tres
    re-corridas y los muebles quedaron en escala cero. Por eso ahora, antes de
    soltar a nadie, al Empty se le quita la animacion y se le pone escala 1.
    """
    n = 0
    for ob in list(bpy.data.objects):
        if not (ob.name.startswith(PREFIJO) and ob.type == 'EMPTY'):
            continue
        ob.animation_data_clear()
        ob.scale = (1.0, 1.0, 1.0)
        ob.hide_viewport = ob.hide_render = False
    bpy.context.view_layer.update()          # sin esto, la matriz sigue vieja
    for ob in list(bpy.data.objects):
        if not (ob.name.startswith(PREFIJO) and ob.type == 'EMPTY'):
            continue
        for h in list(ob.children):
            M = h.matrix_world.copy()
            h.parent = None
            h.matrix_world = M
            h.animation_data_clear()
            h.hide_viewport = h.hide_render = False
        bpy.data.objects.remove(ob, do_unlink=True)
        n += 1
    col = bpy.data.collections.get(COL_AP)
    if col and not col.objects:
        bpy.data.collections.remove(col)
    return n


def aplicar(dry=False):
    esc = bpy.context.scene
    cam = bpy.data.objects.get("CAM_RECORRIDO") or esc.camera
    if cam is None:
        return {"error": "no hay camara"}
    # ya no hace falta cambiar esc.camera: el encuadre se calcula con la matriz
    fps = _fps()
    grupos = _grupos()
    if not grupos:
        return {"error": "no encontre la coleccion MUEBLES"}
    camino = _recorrido(cam, esc)

    plan = []
    for nombre, obs in grupos.items():
        mn, mx = _caja(obs)
        centro = (mn + mx) / 2.0
        entra, cerca, prof = _visibilidad(centro, mn.z, camino, cam.data, esc)
        plan.append({"g": nombre, "obs": obs, "mn": mn, "mx": mx, "centro": centro,
                     "entra": entra, "cerca": cerca, "prof": prof})

    # las que nunca se ven salen al arranque de su nivel, no estorban a nadie
    vistos = [p for p in plan if p["entra"] is not None]
    ciegos = [p for p in plan if p["entra"] is None]
    for p in ciegos:
        piso = p["mn"].z
        mismos = [q for q in vistos if abs(q["mn"].z - piso) < 1.2]
        if mismos:
            # el de al lado: asi el bano sale cuando sale la recamara y no a
            # media casa de distancia. Con la mediana, el sofa de planta baja
            # salia en el cuadro 574 — a 20 segundos de cuando se ve.
            cerca = min(mismos, key=lambda q: (q["centro"].xy - p["centro"].xy).length)
            p["entra"] = cerca["entra"]
        else:
            p["entra"] = esc.frame_start
        p["prof"] = None

    # cuartos: se agrupan las piezas que entran a cuadro casi al mismo tiempo
    vistos_ord = sorted(plan, key=lambda p: p["entra"])
    cuartos, actual = [], []
    for p in vistos_ord:
        if actual and p["entra"] - actual[-1]["entra"] > 2.5 * fps:
            cuartos.append(actual); actual = []
        actual.append(p)
    if actual:
        cuartos.append(actual)

    salida = []
    if not dry:
        deshacer()
        col = bpy.data.collections.get(COL_AP) or bpy.data.collections.new(COL_AP)
        if col.name not in {c.name for c in esc.collection.children}:
            esc.collection.children.link(col)

    for cuarto in cuartos:
        base = min(p["entra"] for p in cuarto) + ESPERA_S * fps
        # de lejos a cerca: lo que tapa es lo ultimo en brotar
        orden = sorted(cuarto, key=lambda p: -(p["prof"] or 99))
        for i, p in enumerate(orden):
            f0 = base + i * ESCALON_S * fps
            if p["cerca"]:                      # se le vino encima a la camara
                f0 = max(f0, p["cerca"] + 0.15 * fps)
            f0 = int(round(min(f0, esc.frame_end - CRECER_S * fps - 2)))
            p["f0"] = f0
            salida.append({"mueble": p["g"], "piezas": len(p["obs"]), "cuadro": f0,
                           "prof_m": round(p["prof"], 1) if p["prof"] else None,
                           "tapaba": bool(p["cerca"])})
            if dry:
                continue
            # --- el empty que hace crecer la pieza ---
            e = bpy.data.objects.new(PREFIJO + p["g"], None)
            e.empty_display_type = 'PLAIN_AXES'
            e.empty_display_size = 0.2
            col.objects.link(e)
            e.location = ((p["mn"].x + p["mx"].x) / 2, (p["mn"].y + p["mx"].y) / 2, p["mn"].z)
            bpy.context.view_layer.update()
            for ob in p["obs"]:
                M = ob.matrix_world.copy()
                ob.parent = e
                ob.matrix_parent_inverse = e.matrix_world.inverted()
                ob.matrix_world = M
            crece = CRECER_S * fps
            claves = [(f0 - 1,           (0.88, 0.88, 0.02)),
                      (f0 + crece * 0.75, (1.02, 1.02, 1.05)),
                      (f0 + crece * 1.5,  (1.0, 1.0, 1.0))]
            for f, s in claves:
                e.scale = s
                e.keyframe_insert("scale", frame=int(round(f)))
            # antes de su cuadro no existe (asi no se ve la tortilla en el piso)
            for f, v in ((esc.frame_start, True), (f0 - 2, True), (f0 - 1, False)):
                e.hide_viewport = e.hide_render = v
                e.keyframe_insert("hide_viewport", frame=f)
                e.keyframe_insert("hide_render", frame=f)
            for fc in e.animation_data.action.fcurves:
                for k in fc.keyframe_points:
                    k.interpolation = 'CONSTANT' if "hide" in fc.data_path else 'BEZIER'
                    if "hide" not in fc.data_path:
                        k.easing = 'EASE_OUT'

    return {"fps": round(fps, 2), "grupos": len(grupos), "cuartos": len(cuartos),
            "sin_ver": [p["g"] for p in ciegos][:12],
            "orden": sorted(salida, key=lambda d: d["cuadro"])}


if __name__ == "__main__":
    print(aplicar(dry=True))
