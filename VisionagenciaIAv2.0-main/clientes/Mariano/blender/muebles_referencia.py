"""Los muebles, pintados y completados segun los clips REALES de la Catania.

De donde sale cada color: de los frames que mando Mariano el 12 Ago
(`clientes/Mariano/escenas_wa/`, clips 10 a 19 = Catania). En Workbench no hay
textura ni luz, asi que lo unico que separa una pieza de otra es el COLOR y el
VALOR. Por eso el problema no era que faltara detalle: era que 89 piezas
compartian una madera y 77 el mismo crema, y todo se leia como un bloque.

Tres cosas hace este archivo:

  1. `pintar()`  — paleta nueva por PIEZA (no por material compartido), sacada
     de las fotos: cabecera beige, edredon chocolate, almohadas blancas contra
     sabana crema, closets de roble claro, buros de nogal, patas negras.
     Se asigna con `slot.link = 'OBJECT'`, que es la unica forma de pintar una
     pieza sin pintar a todas las que comparten su malla (las 6 sillas del
     comedor son la misma malla instanciada).

  2. `amueblar_estudio()` — el estudio tenia UN escritorio y UNA silla, nada
     mas: por eso se veia "puros paneles". Se le pone librero con repisas y
     libros, monitor, teclado, lampara, tapete y planta. Todo cuelga del mismo
     empty `AP_n1_escritorio`, asi que brota del piso con el resto.

  3. `mirar_el_estudio()` — el punto del recorrido miraba al escritorio DESDE
     FUERA del cuarto, con el muro este justo en medio. Se mete la camara
     adentro.

    pintar()  ·  amueblar_estudio()  ·  mirar_el_estudio()  ·  todo()
    deshacer_estudio()
"""
import math

import bpy
from mathutils import Vector

# Las piezas nuevas NO llevan prefijo propio: se llaman como el mueble al que
# pertenecen (`n1_escritorio_monitor`, `n1_librero_repisa0`) porque
# `muebles_aparecen._grupos()` agrupa por prefijo comun — asi el monitor brota
# CON el escritorio y el librero brota como pieza aparte. Para poder quitarlas
# despues se marcan con una propiedad, no con el nombre.
MARCA = "es_referencia"
COL_MUEBLES = "MUEBLES"


# ------------------------------------------------------------------ paleta ---
# (nombre, RGB). Valores leidos de los clips, ya en el rango de Workbench.
PALETA = {
    "ref_cabecera":  (0.66, 0.56, 0.44, 1.0),   # clip 12: panel beige tejido
    "ref_edredon":   (0.30, 0.19, 0.13, 1.0),   # clip 12: el pie de cama chocolate
    "ref_sabana":    (0.88, 0.87, 0.84, 1.0),   # clip 12: la cama, crema, NO blanco
    "ref_almohada":  (0.97, 0.97, 0.96, 1.0),   # para que resalten contra la sabana
    "ref_roble":     (0.60, 0.46, 0.30, 1.0),   # clip 11: el vestidor
    "ref_nogal":     (0.28, 0.19, 0.13, 1.0),   # buros y patas de cama
    "ref_negro":     (0.05, 0.05, 0.055, 1.0),  # clip 18: la TV, patas finas
    "ref_taupe":     (0.40, 0.37, 0.33, 1.0),   # clip 04: los gabinetes de cocina
    "ref_travertino":(0.80, 0.76, 0.69, 1.0),   # clip 15: mesa de centro
    "ref_terracota": (0.55, 0.26, 0.17, 1.0),   # clip 19: la cabecera redonda
    "ref_verde":     (0.16, 0.34, 0.17, 1.0),   # las plantas de todos los clips
    "ref_tapete":    (0.72, 0.68, 0.60, 1.0),   # clip 15: el tapete claro
    "ref_libro_a":   (0.52, 0.24, 0.18, 1.0),
    "ref_libro_b":   (0.20, 0.30, 0.42, 1.0),
    "ref_libro_c":   (0.78, 0.72, 0.58, 1.0),
}

# Reglas por nombre de pieza, EN ORDEN: gana la primera que casa.
REGLAS = [
    ("almohada",   "ref_almohada"),
    ("edredon",    "ref_edredon"),
    ("colchon",    "ref_sabana"),
    ("cabecera",   "ref_cabecera"),
    ("buro",       "ref_nogal"),
    ("pata",       "ref_negro"),
    ("closet",     "ref_roble"),
    ("vestidor",   "ref_roble"),
    ("librero",    "ref_roble"),
    ("aparador",   "ref_roble"),
    ("alacena",    "ref_taupe"),
    ("barra",      "ref_taupe"),
    ("tablero",    "ref_roble"),
    ("planta",     "ref_verde"),
    ("mata",       "ref_verde"),
    ("tapete",     "ref_tapete"),
    ("mesa",       "ref_travertino"),
]


def _mat(nombre):
    m = bpy.data.materials.get(nombre)
    if m is None:
        m = bpy.data.materials.new(nombre)
    m.diffuse_color = PALETA[nombre]
    if m.use_nodes:
        for n in m.node_tree.nodes:
            if "Base Color" in getattr(n, "inputs", {}):
                n.inputs["Base Color"].default_value = PALETA[nombre]
    return m


def _pintar_pieza(ob, nombre_mat):
    """Pinta SOLO este objeto. `link='OBJECT'` es la clave: sin eso el material
    vive en la malla y se lleva por delante a todas sus instancias."""
    if not ob.material_slots:
        ob.data.materials.append(None)
    ob.material_slots[0].link = 'OBJECT'
    ob.material_slots[0].material = _mat(nombre_mat)


def _muebles():
    """Los muebles son los de la coleccion MUEBLES. Antes esto se preguntaba
    por el padre `AP_*`, pero `muebles_aparecen.deshacer()` borra esos empties
    y entonces no encontraba ni una pieza."""
    col = bpy.data.collections.get(COL_MUEBLES)
    return [o for o in col.objects if o.type == 'MESH'] if col else []


def pintar():
    for n in PALETA:
        _mat(n)
    tocados, por_mat = 0, {}
    for ob in _muebles():
        bajo = ob.name.lower()
        for clave, mat in REGLAS:
            if clave in bajo:
                _pintar_pieza(ob, mat)
                por_mat[mat] = por_mat.get(mat, 0) + 1
                tocados += 1
                break
    bpy.context.scene.display.shading.color_type = 'MATERIAL'
    return {"piezas_pintadas": tocados, "por_material": por_mat}


# -------------------------------------------------------- amueblar estudio ---
def _caja(ob):
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return (Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))),
            Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))))


def _cubo(nombre, centro, tam, mat):
    """Una caja simple, ya pintada y marcada como agregada por este archivo."""
    me = bpy.data.meshes.new(nombre)
    ob = bpy.data.objects.new(nombre, me)
    bpy.data.collections.get(COL_MUEBLES, bpy.context.scene.collection).objects.link(ob)
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(me)
    bm.free()
    ob.scale = tam
    ob.location = centro
    ob[MARCA] = True
    _pintar_pieza(ob, mat)
    return ob


def deshacer_estudio():
    fuera = [o for o in bpy.data.objects if o.get(MARCA)]
    for o in fuera:
        bpy.data.objects.remove(o, do_unlink=True)
    return {"quitados": len(fuera)}


def amueblar_estudio(frame=None):
    """Mide el escritorio YA BROTADO (por eso hay que pararse en su frame) y
    le arma el resto del cuarto alrededor."""
    esc = bpy.context.scene
    tablero = bpy.data.objects.get("n1_escritorio_tablero")
    if tablero is None:
        return {"error": "no esta el escritorio"}

    guarda = esc.frame_current
    if frame is not None:
        esc.frame_set(frame)
    bpy.context.view_layer.update()
    mn, mx = _caja(tablero)
    esc.frame_set(guarda)

    x0, x1 = mn.x, mx.x
    y0, y1 = mn.y, mx.y
    z_mesa = mx.z
    piso = -2.70

    # Los limites REALES del cuarto, medidos del muro que lo cierra. El estudio
    # es chico —2.1 x 2.85 m— y la primera version puso el librero en y 12.3 a
    # 13.9: medio librero se metia al cuarto de lavado.
    muro = bpy.data.objects.get("n1_muro_este_estudio")
    if muro is not None:
        mmn, mmx = _caja(muro)
        cuarto_x, cuarto_y = (mmx.x, 7.00), (mmn.y, mmx.y)
    else:
        cuarto_x, cuarto_y = (4.90, 7.00), (10.32, 13.17)
    nuevos = []

    # librero contra el muro, en el hueco que queda DETRAS del escritorio
    ly0 = min(y1 + 0.17, cuarto_y[1] - 0.90)
    ly1 = min(ly0 + 0.72, cuarto_y[1] - 0.12)
    fondo = 0.30
    # Contra el muro del FONDO, no contra el de la camara: pegado al muro oeste
    # el librero le daba la espalda al recorrido y se veia como un bloque liso.
    cx = cuarto_x[1] - fondo / 2 - 0.04
    alto = 1.90
    nuevos.append(_cubo("n1_librero_cuerpo", (cx, (ly0+ly1)/2, piso + alto/2),
                        (fondo, ly1-ly0, alto), "ref_roble"))
    for i in range(4):                  # repisas con libros de colores
        z = piso + 0.42 + i * 0.46
        nuevos.append(_cubo("n1_librero_repisa%d" % i, (cx - 0.03, (ly0+ly1)/2, z),
                            (fondo - 0.05, ly1-ly0-0.06, 0.035), "ref_sabana"))
        for j, (mat, ancho) in enumerate((("ref_libro_a", 0.18), ("ref_libro_b", 0.14),
                                          ("ref_libro_c", 0.16))):
            y = ly0 + 0.14 + j * 0.22
            nuevos.append(_cubo("n1_librero_libros%d_%d" % (i, j),
                                (cx - 0.03, y, z + 0.14), (fondo - 0.10, ancho, 0.26), mat))

    # monitor, teclado y lampara sobre el escritorio
    cx_mesa, cy_mesa = (x0 + x1) / 2, (y0 + y1) / 2
    nuevos.append(_cubo("n1_escritorio_monitor_pie", (cx_mesa, cy_mesa, z_mesa + 0.05),
                        (0.16, 0.22, 0.10), "ref_negro"))
    nuevos.append(_cubo("n1_escritorio_monitor", (cx_mesa - 0.02, cy_mesa, z_mesa + 0.34),
                        (0.04, 0.60, 0.38), "ref_negro"))
    nuevos.append(_cubo("n1_escritorio_teclado", (cx_mesa + 0.26, cy_mesa, z_mesa + 0.015),
                        (0.16, 0.40, 0.02), "ref_negro"))
    nuevos.append(_cubo("n1_escritorio_lampara_base", (cx_mesa - 0.05, y0 + 0.14, z_mesa + 0.02),
                        (0.13, 0.13, 0.03), "ref_negro"))
    nuevos.append(_cubo("n1_escritorio_lampara_brazo", (cx_mesa - 0.05, y0 + 0.14, z_mesa + 0.22),
                        (0.03, 0.03, 0.40), "ref_negro"))
    nuevos.append(_cubo("n1_escritorio_lampara_pantalla", (cx_mesa + 0.06, y0 + 0.14, z_mesa + 0.42),
                        (0.20, 0.13, 0.10), "ref_libro_c"))

    # planta en la esquina libre y tapete bajo la silla, los dos DENTRO
    ex, ey = cuarto_x[1] - 0.40, cuarto_y[0] + 0.42
    nuevos.append(_cubo("n1_planta_estudio_maceta", (ex, ey, piso + 0.16),
                        (0.30, 0.30, 0.32), "ref_travertino"))
    nuevos.append(_cubo("n1_planta_estudio_hojas", (ex, ey, piso + 0.64),
                        (0.46, 0.46, 0.64), "ref_verde"))
    ty = (cuarto_y[0] + y0) / 2
    nuevos.append(_cubo("n1_tapete_estudio", ((cuarto_x[0] + cuarto_x[1]) / 2, ty, piso + 0.008),
                        (min(1.5, cuarto_x[1] - cuarto_x[0] - 0.35), 1.20, 0.012), "ref_tapete"))

    # No se emparentan a mano: van en MUEBLES con el nombre del mueble al que
    # pertenecen, y `muebles_aparecen.aplicar()` les arma su empty y su brote.
    fuera = [o.name for o in nuevos
             if not (cuarto_x[0] - 0.05 <= o.location.x <= cuarto_x[1] + 0.05
                     and cuarto_y[0] - 0.05 <= o.location.y <= cuarto_y[1] + 0.05)]
    return {"piezas_nuevas": len(nuevos), "se_salen_del_cuarto": fuera,
            "cuarto_x": [round(v,2) for v in cuarto_x], "cuarto_y": [round(v,2) for v in cuarto_y],
            "escritorio_medido_en_frame": frame,
            "tablero": [round(v, 2) for v in (x0, y0, z_mesa)]}


def mirar_el_estudio(nota="estudio", adentro_x=2.6):
    """El punto miraba al escritorio desde el pasillo, con el muro este en
    medio. Se mete la camara al cuarto y se apunta al escritorio."""
    aj = bpy.context.scene.spline_audio
    tablero = bpy.data.objects.get("n1_escritorio_tablero")
    if tablero is None:
        return {"error": "no esta el escritorio"}
    mn, mx = _caja(tablero)
    objetivo = ((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mx.z + 0.35)
    for p in aj.puntos:
        if p.nota == nota:
            antes = [round(p.x, 2), round(p.y, 2), round(p.altura, 2), p.zoom]
            p.x = objetivo[0] - adentro_x
            p.y = objetivo[1] - 0.9
            p.altura = -1.35
            p.zoom = 24.0
            p.mira_automatica = False
            p.mira_x, p.mira_y, p.mira_z = objetivo
            if len(aj.puntos) >= 2:
                bpy.ops.splineaudio.construir()
            return {"antes": antes, "ahora": [round(p.x,2), round(p.y,2), round(p.altura,2), p.zoom],
                    "mira": [round(v,2) for v in objetivo]}
    return {"error": "no hay punto con nota %r" % nota}


def todo(frame_estudio=637):
    deshacer_estudio()
    return {"pintar": pintar(),
            "estudio": amueblar_estudio(frame=frame_estudio),
            "camara": mirar_el_estudio()}


# ------------------------------------------------------- muros que no entran --
# `paredes_y_ritmo.solo_muros()` decide solo cuando desvanecer cada muro, pero
# usa `CUARTO_M = 6.0`: si la camara mira el cuarto desde MAS lejos, ese muro
# nunca entra en la lista y se queda opaco. Le pasa a los dos muros "este" del
# nivel 1 — el del estudio y el del lavado — porque la camara los mira desde
# x = -1.9, o sea a 6.7 m. Ese, y no los muebles, era el panel blanco que tapaba
# el estudio entero.
MUROS_A_MANO = {"n1_muro_este_estudio": 25.9, "n1_muro_este_lavado": 27.2}


def _bsdf(m):
    if not m.use_nodes:
        return None
    for n in m.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            return n
    return None


def desvanecer_muro(nombre, t, dur=0.5):
    """Anima el alpha de un muro para que se disuelva en el segundo `t`."""
    esc = bpy.context.scene
    ob = bpy.data.objects.get(nombre)
    if ob is None:
        return {"error": "no esta " + nombre}
    fps = esc.render.fps / esc.render.fps_base
    f0 = max(esc.frame_start + 1, int(round(t * fps)) + 1)
    f1 = int(f0 + dur * fps)
    hechos = []
    for slot in ob.material_slots:
        m = slot.material
        if not m:
            continue
        b = _bsdf(m)
        if b is not None:
            a = b.inputs["Alpha"]
            a.default_value = 1.0
            m.node_tree.keyframe_insert(a.path_from_id("default_value"), frame=f0)
            a.default_value = 0.0
            m.node_tree.keyframe_insert(a.path_from_id("default_value"), frame=f1)
            try:
                m.blend_method = 'BLEND'
            except AttributeError:
                pass
        # Workbench ignora el nodo: lo que obedece es el alpha de Viewport Display
        m.diffuse_color[3] = 1.0
        m.keyframe_insert("diffuse_color", index=3, frame=f0)
        m.diffuse_color[3] = 0.0
        m.keyframe_insert("diffuse_color", index=3, frame=f1)
        for datos in (m.animation_data, getattr(m.node_tree, "animation_data", None)):
            if datos and datos.action:
                for fc in datos.action.fcurves:
                    for k in fc.keyframe_points:
                        k.interpolation = 'BEZIER'
                        k.easing = 'EASE_IN_OUT'
        hechos.append(m.name)
    return {"muro": nombre, "se_va_en": f0, "termina": f1, "materiales": hechos}


def muros_que_faltan(cuales=None):
    esc = bpy.context.scene
    esc.display.shading.color_type = 'MATERIAL'
    return [desvanecer_muro(n, t) for n, t in (cuales or MUROS_A_MANO).items()]


# ----------------------------------------------------- las vecinas estorban --
# Las vecinas se prendieron para que la calle se viera como la foto de
# EasyBroker, y para la fachada y el remate son justo lo que hace falta. Pero
# el recorrido MIRA LOS CUARTOS DESDE EL OESTE, desde x = -1.9, y las casas van
# cada 7 m: ese punto cae DENTRO de la vecina de la izquierda. O sea que en
# todos los interiores hay una casa entera meti da entre la camara y la escena.
# Ese era el "panel blanco" del estudio, no un muro de la A2.
#
# Se apagan mientras la camara esta adentro y se vuelven a prender para el
# remate. Con llaves CONSTANT: una visibilidad no se interpola.
def _es_vecina(nombre):
    if nombre.startswith(("VEC_", "COLONIA_", "TER_")):
        return nombre.startswith("VEC_")
    return nombre.endswith(("_v-1", "_v-2", "_v1", "_v2"))


def vecinas_fuera(entra=5.0, sale=34.4, fundido=0.4):
    """Ocultas entre `entra` y `sale` (segundos); visibles fuera de ese rango.

    `sale` tiene que caer ANTES de que arranque el alejamiento (t 34.6): en
    cuanto la camara se despega del jardin ya se esta viendo la calle entera, y
    si las vecinas siguen apagadas la colonia aparece hueca — solo con el
    relleno de OSM, sin las casas de la propia calle Catania.
    """
    esc = bpy.context.scene
    fps = esc.render.fps / esc.render.fps_base
    f_off = int(round(entra * fps)) + 1
    f_on = int(round(sale * fps)) + 1
    tocados = []
    for ob in bpy.data.objects:
        if ob.type not in ('MESH', 'CURVE') or not _es_vecina(ob.name):
            continue
        ob.animation_data_clear()
        for prop in ("hide_viewport", "hide_render"):
            setattr(ob, prop, False)
            ob.keyframe_insert(prop, frame=max(1, f_off - 1))
            setattr(ob, prop, True)
            ob.keyframe_insert(prop, frame=f_off)
            ob.keyframe_insert(prop, frame=f_on - 1)
            setattr(ob, prop, False)
            ob.keyframe_insert(prop, frame=f_on)
        if ob.animation_data and ob.animation_data.action:
            for fc in ob.animation_data.action.fcurves:
                for k in fc.keyframe_points:
                    k.interpolation = 'CONSTANT'
        ob.hide_viewport = ob.hide_render = False
        tocados.append(ob.name)
    return {"vecinas": len(tocados), "se_apagan_en": f_off, "vuelven_en": f_on,
            "ejemplos": tocados[:8]}


def vecinas_siempre():
    """Deshace lo de arriba: las vecinas visibles todo el video."""
    n = 0
    for ob in bpy.data.objects:
        if _es_vecina(ob.name):
            ob.animation_data_clear()
            ob.hide_viewport = ob.hide_render = False
            n += 1
    return {"vecinas": n}


def desvanecer_objeto(nombre, t, dur=0.5):
    """Como `desvanecer_muro`, pero para un mueble que se atraviesa.

    Antes de animar le da al objeto una COPIA de su material: los closets
    comparten material, y animar el compartido desvanece todos los closets de
    la casa a la vez.
    """
    ob = bpy.data.objects.get(nombre)
    if ob is None:
        return {"error": "no esta " + nombre}
    for slot in ob.material_slots:
        m = slot.material
        if m is not None and m.users > 1:
            slot.link = 'OBJECT'
            slot.material = m.copy()
            slot.material.name = m.name + "_" + nombre
    return desvanecer_muro(nombre, t, dur)


# Lo que se atraviesa entre la camara y el cuarto que toca ver, con el segundo
# en que estorba. No son muros: son muebles de OTRO cuarto que quedan en la
# linea de vista, y por eso `solo_muros()` ni los mira.
ESTORBOS = {"n1_closet_rec1": 25.9}


def quitar_estorbos(cuales=None):
    return [desvanecer_objeto(n, t) for n, t in (cuales or ESTORBOS).items()]


# ------------------------------------------------- muebles que brotan tarde --
# `muebles_aparecen.aplicar()` decide cuando brota cada mueble por lo que la
# camara alcanza a ver. Los que no logra "ver" (los devuelve en `sin_ver`) se
# van al final del recorrido: el escritorio brotaba en el cuadro 943 —t 39 s—
# cuando el estudio se enseña en el 637. Por eso el cuarto salia vacio.
#
# Aqui se les dice a mano en que segundo brotan, que es el segundo del punto
# del recorrido donde se enseña su cuarto.
BROTES = {
    "AP_n1_librero":         25.85,   # estudio, t 26.5
    "AP_n1_escritorio":      26.00,
    "AP_n1_tapete_estudio":  26.10,
    "AP_n1_silla_estudio":   26.25,
    "AP_n1_planta_estudio":  26.40,
    "AP_n1_lavadora":        27.55,   # cuarto de lavado, t 27.8
    "AP_n1_secadora":        27.70,
    "AP_pb_lavabo_ppal":     21.10,   # bano de la principal, t 21.0
    "AP_pa_alacena_alta":    10.55,   # cocina, t 10.6
    "AP_pa_silla3":          10.80,
    "AP_pa_silla4":          10.90,
    "AP_pa_maceta":          11.10,
    "AP_rg_sillon_1":        14.95,   # roof garden, t 14.9
    "AP_rg_sillon_1_brazo":  15.05,
    "AP_rg_sillon_2":        15.15,
    "AP_rg_sillon_2_brazo":  15.25,
}


def brotar(nombre_ap, t, dur=0.30):
    """Reescribe el brote de un empty AP_: aplastado en Z y creciendo, igual
    que los que arma `muebles_aparecen` (0.02 -> 1.05 -> 1.00)."""
    esc = bpy.context.scene
    ob = bpy.data.objects.get(nombre_ap)
    if ob is None:
        return {"error": "no esta " + nombre_ap}
    fps = esc.render.fps / esc.render.fps_base
    f0 = max(esc.frame_start + 1, int(round(t * fps)) + 1)
    f1 = int(f0 + dur * fps / 2)
    f2 = int(f0 + dur * fps)
    if ob.animation_data:
        ob.animation_data_clear()
    for frame, esc_xy, esc_z in ((f0, 0.88, 0.02), (f1, 1.02, 1.05), (f2, 1.0, 1.0)):
        ob.scale = (esc_xy, esc_xy, esc_z)
        ob.keyframe_insert("scale", frame=frame)
    for fc in ob.animation_data.action.fcurves:
        fc.extrapolation = 'CONSTANT'
        for k in fc.keyframe_points:
            k.interpolation = 'BEZIER'
            k.easing = 'EASE_OUT'
    ob.scale = (1.0, 1.0, 1.0)
    return {"empty": nombre_ap, "brota_en": f0, "listo_en": f2}


def brotes(cuales=None):
    return [brotar(n, t) for n, t in (cuales or BROTES).items()]


# ------------------------------------------------ los cuartos, mas abiertos --
# El recorrido se compuso en 3:2, donde los 36 mm del sensor caian a lo ANCHO.
# Al pasar a 9:16 se van a lo alto y el ancho se queda con 20.25 mm: el mismo
# lente encuadra casi la mitad. Medido en los puntos del recorrido, el campo
# horizontal se cayo de ~60 a ~35 grados — de ahi que todo se vea cerrado.
#
# Recuperarlo del todo pediria multiplicar el lente por 0.5625, y eso mete
# distorsion de gran angular en cuartos chicos. Sale mejor repartir: un poco de
# lente y un poco de alejar la camara.
def abrir_interiores(factor=0.70, atras=1.4, minimo=15.0, saltar="remate al mar"):
    aj = bpy.context.scene.spline_audio
    puntos = sorted(aj.puntos, key=lambda p: p.tiempo)
    cambios = []
    for i, p in enumerate(puntos):
        if saltar in p.nota:
            continue
        if p.mira_automatica:
            if i + 1 >= len(puntos):
                continue
            q = puntos[i + 1]
            hacia = Vector((q.x - p.x, q.y - p.y, q.altura - p.altura))
        else:
            hacia = Vector((p.mira_x - p.x, p.mira_y - p.y, p.mira_z - p.altura))
        if hacia.length < 1e-3:
            continue
        hacia.normalize()
        antes = (round(p.x, 2), round(p.y, 2), round(p.altura, 2), round(p.zoom, 1))
        p.x -= hacia.x * atras
        p.y -= hacia.y * atras
        p.altura -= hacia.z * atras * 0.35      # se aleja casi horizontal
        p.zoom = max(minimo, p.zoom * factor)
        cambios.append({"cuarto": p.nota or "-", "t": round(p.tiempo, 2), "antes": antes,
                        "ahora": (round(p.x, 2), round(p.y, 2), round(p.altura, 2),
                                  round(p.zoom, 1))})
    if len(aj.puntos) >= 2:
        bpy.ops.splineaudio.construir()
    return cambios


# ------------------------------------------- apuntar a lo que hay que ver ---
# Al alejar las camaras 1.4 m, la mira se quedo donde estaba y el encuadre se
# fue hacia arriba: entraba el techo y las macetas del roof en vez del cuarto.
# Esto reapunta cada punto al CENTRO DE LOS MUEBLES que tiene delante, que es
# lo que de verdad hay que ver. Usa la misma mira fija que el giroscopio del
# addon, asi que despues se puede seguir ajustando a mano con los sliders.
def apuntar_a_los_muebles(solo=None, cono=45.0, alcance=14.0, saltar="remate al mar"):
    """Para cada punto, busca el mueble mas cercano dentro del cono de vision
    y apunta ahi. `solo` limita a los puntos cuya nota contenga ese texto."""
    aj = bpy.context.scene.spline_audio
    puntos = sorted(aj.puntos, key=lambda p: p.tiempo)
    muebles = _muebles()
    if not muebles:
        return {"error": "no hay muebles"}

    centros = []
    for ob in muebles:
        mn, mx = _caja(ob)
        centros.append((ob.name, (mn + mx) / 2.0))

    cambios = []
    for i, p in enumerate(puntos):
        if saltar in p.nota or (solo and solo not in p.nota):
            continue
        pos = Vector((p.x, p.y, p.altura))
        if p.mira_automatica:
            if i + 1 >= len(puntos):
                continue
            q = puntos[i + 1]
            hacia = Vector((q.x, q.y, q.altura)) - pos
        else:
            hacia = Vector((p.mira_x, p.mira_y, p.mira_z)) - pos
        if hacia.length < 1e-3:
            continue
        hacia.normalize()

        # los muebles que caen adelante y dentro del cono, ponderando por
        # cercania: el mueble ancla de un cuarto es el que esta mas al centro
        cerca, mejor = None, 1e9
        for nombre, c in centros:
            d = c - pos
            dist = d.length
            if dist > alcance or dist < 0.6:
                continue
            ang = math.degrees(d.normalized().angle(hacia))
            if ang > cono:
                continue
            puntaje = dist * (1.0 + ang / 90.0)
            if puntaje < mejor:
                mejor, cerca = puntaje, (nombre, c)
        if cerca is None:
            continue

        antes = (round(p.mira_x, 2), round(p.mira_y, 2), round(p.mira_z, 2))
        # se apunta un poco por encima del mueble: a la altura de la vista, no
        # al suelo, que es lo que hace que un cuarto se vea "de frente"
        destino = cerca[1] + Vector((0.0, 0.0, 0.35))
        p.mira_automatica = False
        p.mira_x, p.mira_y, p.mira_z = destino.x, destino.y, destino.z
        cambios.append({"t": round(p.tiempo, 2), "cuarto": p.nota or "-",
                        "apunta_a": cerca[0], "antes": antes,
                        "ahora": [round(v, 2) for v in destino]})
    if len(aj.puntos) >= 2:
        bpy.ops.splineaudio.construir()
    return cambios


# --------------------------------------------- apuntar por angulos, a mano --
# `apuntar_a_los_muebles()` resulto mala idea y se deja documentado por que:
# la casa se mira EN SECCION, asi que en el cono de vision de cada punto caen
# muebles de tres cuartos distintos. Eligiendo "el mas cercano" el estudio
# acabo apuntando al lavabo del baño y el jardin a una pata de cama.
#
# Lo que si sirve es esto: poner el giro y la inclinacion a mano, punto por
# punto, con los mismos numeros que muestra el giroscopio del panel.
def poner_angulos(tabla, construir=True):
    """tabla: {nota_del_punto: (giro, inclinacion, distancia)}. Cualquiera de
    los tres puede ser None para dejarlo como esta."""
    import math as _m
    aj = bpy.context.scene.spline_audio
    hechos = []
    for p in aj.puntos:
        if p.nota not in tabla:
            continue
        g, inc, dist = tabla[p.nota]
        d = Vector((p.mira_x - p.x, p.mira_y - p.y, p.mira_z - p.altura))
        actual = d.length or 5.0
        g = _m.radians(g if g is not None else
                       _m.degrees(_m.atan2(d.y, d.x)))
        inc = _m.radians(inc if inc is not None else
                         _m.degrees(_m.atan2(d.z, _m.hypot(d.x, d.y))))
        dist = dist if dist is not None else actual
        p.mira_automatica = False
        p.mira_x = p.x + dist * _m.cos(inc) * _m.cos(g)
        p.mira_y = p.y + dist * _m.cos(inc) * _m.sin(g)
        p.mira_z = p.altura + dist * _m.sin(inc)
        hechos.append({"cuarto": p.nota, "giro": round(_m.degrees(g), 1),
                       "incl": round(_m.degrees(inc), 1), "dist": round(dist, 1)})
    if construir and len(aj.puntos) >= 2:
        bpy.ops.splineaudio.construir()
    return hechos


# Los angulos que tenia cada punto ANTES de la prueba fallida. Sirven de
# respaldo y de punto de partida para ajustar con el giroscopio.
ANGULOS_BASE = {
    "establecimiento": (98.1, -6.1, 11.7),
    "entras-medio-2carros": (5.2, -1.6, 5.8),
    "subes-escalones": (0.3, -8.7, 9.1),
    "sala-comedor": (2.1, -13.3, 6.2),
    "cocina": (-0.4, -15.2, 5.5),
    "hasta-arriba": (0.0, -13.6, 6.3),
    "puerta-abre": (-0.3, -6.6, 7.1),
    "roof-garden": (20.6, -6.7, 7.4),
    "recamara-principal-izquierda": (6.1, -0.6, 5.5),
    "vestidor-bano-propio": (0.0, -1.1, 8.7),
    "piso-abajo-speedramp": (13.4, -2.1, 6.1),
    "dos-recamaras": (3.2, -3.9, 5.7),
    "estudio": (1.4, -3.3, 9.2),
    "cuarto-lavado-acercamiento": (4.0, -5.0, 8.6),
    "jardin": (13.4, -1.8, 6.9),
    "nadie-te-ve": (-3.8, -2.9, 6.5),
}
