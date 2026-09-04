"""El corte de la casa entera MAS una mascara por cuarto, desde la misma camara.

    blender -b <blend> -P corte_mascaras.py -- <atras> <arriba> <lente> <dir> [w] [h] [que]

    que: "gris" | "blanco" | "mascaras" | "todo"   (por omision: todo)

POR QUE EXISTE
--------------
`casa_seedream_v2.png` salio preciosa y ES OTRA CASA: patio central que no
existe, el programa movido, tres camas donde no van. Un solo *edit* sobre el
render gris no amarra nada — el modelo lo toma de inspiracion y redibuja la
planta. Comprobado el 30 ago y el 2 sep, con dos modelos distintos.

La salida son TRES cosas del MISMO encuadre:

  corte_gris.png     — Workbench solido, para que se lea el volumen
  corte_blanco.png   — plano y blanco; de ahi sale `corte_aristas.png` con un
                       Sobel de ffmpeg (Blender NO da lineas al renderizar:
                       `shading.type='WIREFRAME'` es del VISOR y el motor se la
                       salta EN SILENCIO)
  mascara_<cuarto>.png — blanco donde se ve ESE cuarto, negro en todo lo demas

Con eso el vestido ya no es un ruego, es una restriccion:
  1. las aristas van a un ControlNet de verdad
     (`wavespeed-ai/flux-controlnet-union-pro-2.0`) y fijan la geometria;
  2. cada cuarto se viste por separado con `bria/fibo-edit/genfill`, que recibe
     `mask_image` — vestir la cocina ya no le puede mover la recamara.

COMO SALEN LAS MASCARAS, y por que no a ojo
-------------------------------------------
No se dibujan: se DEDUCEN del archivo, igual que las camaras de
`cuartos_camara.py`.

  1. Se cuadricula la planta de la casa (x 1.10-6.90, y 6.67-15.52) a 15 cm.
  2. Se marcan como ocupadas las celdas que caen dentro de un muro del nivel
     (`muro_*`, `div_*`, sin el sufijo `_v1/_v-1/...` de las vecinas clonadas).
  3. Se rellena por inundacion: cada mancha libre y cerrada ES un cuarto.
  4. Cada cuarto se reconoce por la CAMARA que ya tiene en `cuartos_camara.py`:
     esa camara esta dentro de su cuarto, asi que la mancha que la contiene es
     la suya. Cero coordenadas nuevas que mantener.
  5. Con las celdas de la mancha se levanta una caja del piso al techo, se
     pinta de BLANCO y todo lo demas de NEGRO, y se renderiza con Workbench en
     `color_type='OBJECT'`. El z-buffer hace el resto: si un muro tapa el
     cuarto, la mascara sale tapada tambien. Es la silueta exacta de lo que se
     ve de ese cuarto en el corte.

El cuadro es el 1021, no el 1: hay 584 objetos animados y los muebles BROTAN
del piso durante el recorrido.
"""
import os
import sys
from collections import deque

import bmesh
import bpy
from mathutils import Vector

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from cuartos_camara import CUARTOS, limpia  # noqa: E402  (mismas camaras, misma limpieza)

CUADRO = 1021
CASA = (1.10, 6.90, 6.67, 15.52)      # x0 x1 y0 y1, del propio archivo
CELDA = 0.15

# nivel -> (piso, techo).
#
# OJO CON EL rg: LA TERRAZA NO ESTA ARRIBA DE LA PLANTA ALTA, esta EN LA MISMA.
# Se vio en el inventario del 3 sep: `rg_jardinera_fondo` va de z 2.80 a 3.22 y
# `pa_sofa_asiento` de 2.96 a 3.26 — el mismo piso. La casa tiene TRES losas
# (n1, pb, pa), y la azotea es la parte descubierta de la de arriba, no un
# cuarto nivel. Dandole (5.60, 6.70) la mascara del rg no encontraba un solo
# muro y salia del tamano de la planta entera.
NIVELES = {
    "n1": (-2.75, -0.20),
    "pb": (-0.05,  2.60),
    "pa": ( 2.80,  5.60),
    "rg": ( 2.80,  5.60),
}


_VECINA = __import__("re").compile(r"_v-?\d+(\.\d+)?$")


def es_vecina(nombre):
    """Las casas clonadas a +-7 m llevan sufijo `_v1`, `_v-1`, `_v2`... La de
    verdad es la que NO lo lleva.

    Con regex y no con `rsplit`: Blender le agrega `.001` a los duplicados, y
    `pb_muro_oeste_sala_v-1.001` partido por el ultimo `_` da `v-1.001`, que no
    es digito, asi que la copia se colaba. Salian a UN METRO de la camara y el
    render entero era gris plano."""
    return bool(_VECINA.search(nombre))


MUROS = []          # se llena una sola vez, ANTES de que la camara del corte
                    # esconda la fachada: para partir cuartos hacen falta TODOS
                    # los muros, tambien el que se quita para ver el corte.


# Que cuenta como muro. NO se filtra por nombre: probandolo, `muro`/`div` solo
# agarraba 22 de los ~158 que hay, porque la casa tambien se parte con `ext_*`,
# `a2_muro_*`, `esc_*` y los marcos de puerta. Con 22 la planta baja daba 2
# manchas para 6 cuartos. Se filtra por GEOMETRIA, que es lo que de verdad corta
# el paso: algo delgado en planta y alto.
GRUESO_MAX = 0.40      # los muros van de 7 a 15 cm; las puertas y marcos, menos
ALTO_MIN = 1.50        # tiene que llegar arriba del ojo, o no separa nada


def apunta_muros():
    """OJO: NO se mira `hide_render`. `limpia()` esconde la coleccion
    `CEBOLLA_muros` — que son EXACTAMENTE los 12 muros divisorios de la casa
    (pb_muro_oeste_sala, pb_muro_este_vestidor, n1_muro_este_estudio...) — y
    saltandolos las manchas se filtraban de un cuarto a otro: la planta baja
    daba 2 manchas de 27 y 18 m2 para SEIS cuartos. Para partir la planta hacen
    falta todos los muros, se vean o no en el render.

    Si se saltan los `_fantasma` (copias en el mismo sitio, no aportan) y los
    ROTULOS (letreros delgados y altos que si estorbarian)."""
    x0, x1, y0, y1 = CASA
    rotulos = bpy.data.collections.get("ROTULOS")
    letreros = {o.name for o in rotulos.objects} if rotulos else set()
    for o in bpy.data.objects:
        if o.type != 'MESH' or es_vecina(o.name):
            continue
        if o.name.endswith("_fantasma") or o.name in letreros:
            continue
        c = [o.matrix_world @ Vector(v) for v in o.bound_box]
        ax, bx = min(v.x for v in c), max(v.x for v in c)
        ay, by = min(v.y for v in c), max(v.y for v in c)
        az, bz = min(v.z for v in c), max(v.z for v in c)
        if bx < x0 - 0.3 or ax > x1 + 0.3 or by < y0 - 0.3 or ay > y1 + 0.3:
            continue                                  # fuera de la casa
        if bz - az < ALTO_MIN:
            continue                                  # bajito: es mueble
        if min(bx - ax, by - ay) > GRUESO_MAX:
            continue                                  # gordo en planta: no es muro
        MUROS.append((ax, bx, ay, by, az, bz))
    print("muros apuntados:", len(MUROS))


def muros_del_nivel(nivel):
    """Los muros de ESE nivel, con su huella en planta ya en coordenadas de mundo."""
    piso, techo = NIVELES[nivel]
    medio = (piso + techo) / 2.0
    return [(a, b, c, d) for a, b, c, d, z0, z1 in MUROS if z0 <= medio <= z1]


def _sin_uso(nivel):
    piso, techo = NIVELES[nivel]
    medio = (piso + techo) / 2.0
    fuera = []
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.hide_render or es_vecina(o.name):
            continue
        n = o.name
        if not (n.startswith("muro") or n.startswith("div") or "_muro_" in n
                or "_div_" in n):
            continue
        c = [o.matrix_world @ Vector(v) for v in o.bound_box]
        z0, z1 = min(v.z for v in c), max(v.z for v in c)
        if z1 < medio or z0 > medio:        # no cruza la altura del ojo del nivel
            continue
        fuera.append((min(v.x for v in c), max(v.x for v in c),
                      min(v.y for v in c), max(v.y for v in c)))
    return fuera


def manchas(nivel):
    """Cuadricula el nivel, tapa los muros e inunda. Devuelve (cols, filas, etiqueta)
    donde `etiqueta[i]` es el numero de mancha de la celda, o -1 si es muro."""
    x0, x1, y0, y1 = CASA
    cols = int((x1 - x0) / CELDA) + 1
    filas = int((y1 - y0) / CELDA) + 1
    cajas = muros_del_nivel(nivel)
    et = [-1] * (cols * filas)
    for j in range(filas):
        cy = y0 + (j + 0.5) * CELDA
        for i in range(cols):
            cx = x0 + (i + 0.5) * CELDA
            # OJO: los muros son de 7 cm y la celda de 15. Preguntando si el
            # CENTRO de la celda cae dentro del muro, casi ninguno caia: en la
            # planta baja solo 39 celdas de 2340 salian tapadas y las manchas
            # no cerraban — los 16 cuartos daban el mismo nivel entero (52 m2).
            # Se pregunta si la CELDA CRUZA el muro, que es lo que de verdad
            # corta el paso.
            h = CELDA / 2.0
            tapada = any(a <= cx + h and b >= cx - h and c <= cy + h and d >= cy - h
                         for a, b, c, d in cajas)
            et[j * cols + i] = -2 if tapada else -1     # -2 muro, -1 libre sin marcar

    n = 0
    for arranque in range(cols * filas):
        if et[arranque] != -1:
            continue
        cola = deque([arranque])
        et[arranque] = n
        while cola:
            k = cola.popleft()
            i, j = k % cols, k // cols
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                a, b = i + di, j + dj
                if 0 <= a < cols and 0 <= b < filas and et[b * cols + a] == -1:
                    et[b * cols + a] = n
                    cola.append(b * cols + a)
        n += 1
    return cols, filas, et


# Niveles que son UNA SOLA PIEZA en el modelo. La planta alta no tiene muros
# entre cocina, comedor y sala — son tres TOMAS del mismo espacio, no tres
# cuartos. Repartirla por camara mas cercana daba un disparate: la sala se
# quedaba con 1.35 m2, porque las tres camaras estan pegadas al mismo borde sur
# mirando hacia adentro. Sale UNA mascara para todo el nivel y el prompt dice
# donde va cada cosa.
ABIERTOS = {"pa", "rg"}

_CACHE = {}


def _manchas(nivel):
    if nivel not in _CACHE:
        _CACHE[nivel] = manchas(nivel)
    return _CACHE[nivel]


def _celda_de(pos, cols, filas, et):
    """La mancha donde cae una camara. Si cayo justo sobre un muro, la de al lado."""
    x0, y0 = CASA[0], CASA[2]
    i, j = int((pos[0] - x0) / CELDA), int((pos[1] - y0) / CELDA)
    if not (0 <= i < cols and 0 <= j < filas):
        return -1
    if et[j * cols + i] >= 0:
        return et[j * cols + i]
    for r in (1, 2, 3):
        for dj in range(-r, r + 1):
            for di in range(-r, r + 1):
                a, b = i + di, j + dj
                if 0 <= a < cols and 0 <= b < filas and et[b * cols + a] >= 0:
                    return et[b * cols + a]
    return -1


def caja_del_cuarto(cuarto):
    """La malla blanca que ocupa el volumen del cuarto. None si no se pudo ubicar.

    UNA MANCHA NO ES SIEMPRE UN CUARTO. Dos casos reales:
      · la PLANTA ALTA es una sola pieza — cocina, sala y comedor comparten el
        espacio, y asi esta en el modelo;
      · abajo quedan pares que se comunican sin puerta (sala y escalera, bano y
        recamara1).
    Cuando en una mancha caen VARIAS camaras, la mancha se reparte: cada celda
    se va con la camara mas cercana. Sale un corte limpio entre cuartos vecinos
    y, en la planta alta, separa cocina / sala / comedor, que es justo lo que
    hace falta para vestirlos por separado.
    """
    nivel = cuarto.split("_", 1)[0]
    piso, techo = NIVELES[nivel]
    cols, filas, et = _manchas(nivel)
    x0, y0 = CASA[0], CASA[2]

    pos = CUARTOS[cuarto][0]                      # la camara vive DENTRO del cuarto
    mancha = _celda_de(pos, cols, filas, et)
    if mancha < 0:
        return None

    vecinos = [(c, CUARTOS[c][0]) for c in CUARTOS
               if c.split("_", 1)[0] == nivel
               and _celda_de(CUARTOS[c][0], cols, filas, et) == mancha]

    def mia(i, j):
        if nivel in ABIERTOS or len(vecinos) < 2:
            return True
        cx = x0 + (i + 0.5) * CELDA
        cy = y0 + (j + 0.5) * CELDA
        cerca = min(vecinos, key=lambda v: (v[1][0] - cx) ** 2 + (v[1][1] - cy) ** 2)
        return cerca[0] == cuarto

    bm = bmesh.new()
    celdas = 0
    for k, v in enumerate(et):
        if v != mancha:
            continue
        i, j = k % cols, k // cols
        if not mia(i, j):
            continue
        a, b = x0 + i * CELDA, y0 + j * CELDA
        bmesh.ops.create_cube(bm, size=1.0, matrix=(
            __import__("mathutils").Matrix.Translation(
                (a + CELDA / 2, b + CELDA / 2, (piso + techo) / 2)) @
            __import__("mathutils").Matrix.Diagonal(
                (CELDA, CELDA, techo - piso, 1.0))))
        celdas += 1
    if not celdas:
        return None
    me = bpy.data.meshes.new("MASCARA_" + cuarto)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("MASCARA_" + cuarto, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.color = (1.0, 1.0, 1.0, 1.0)
    print("  %s: %d celdas (%.2f m2)" % (cuarto, celdas, celdas * CELDA * CELDA))
    return ob


# ------------------------------------------------------------------ camara
CENTRO = (4.00, 11.10, 1.40)      # el medio de la casa: x 1.10-6.90, y 6.67-15.52
DESVIO_Y = float(os.environ.get("DESVIO_Y", "0.30"))


# EL ENCUADRE ES EL DE CARLOS, leido de su Blender por el conector el 3 sep
# 2026 a las 22:05. No se invento: el lo puso en pantalla y se saco del
# `region_3d` del visor. Se puede pisar con variables de entorno.
OJO = [float(v) for v in os.environ.get("OJO", "-6.461,11.858,1.785").split(",")]
MIRA = [float(v) for v in os.environ.get("MIRA", "5.126,11.012,0.74").split(",")]
LENTE = float(os.environ.get("LENTE", "50"))


def camara_del_corte(_dist, _alt, _lente):
    """La camara de Carlos, tal cual, y la casa sola.

    Los tres argumentos ya no se usan: quedaron por compatibilidad con la linea
    de comandos. El encuadre viene de OJO / MIRA / LENTE.

    Que se apaga, y por que:
      · TODO lo que no sea la casa. Su ojo esta en x -6.46, o sea DENTRO de la
        vecina clonada del poniente (`_v-1` va de x -5.9 a -0.1). Con la fila
        puesta, la toma es una hilera de casas y no un corte.
      · La piel PONIENTE de la casa, que es la tapa del corte: los muros que
        quedan entre el ojo y el centro. Se decide proyectando el centro de
        cada muro sobre la direccion de vista, igual que en el Blender de
        Carlos — asi lo que se renderiza aqui es lo mismo que el esta viendo.
      · El terreno: el nivel n1 esta enterrado y el cerro se lo come.
    """
    sc = bpy.context.scene
    ojo, mira = Vector(OJO), Vector(MIRA)

    cd = bpy.data.cameras.new("CAM_CORTE")
    cd.lens = LENTE
    cd.clip_start, cd.clip_end = 0.05, 3000.0
    c2 = bpy.data.objects.new("CAM_CORTE", cd)
    sc.collection.objects.link(c2)
    c2.location = ojo
    c2.rotation_euler = (mira - ojo).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = c2

    hacia = Vector((mira.x - ojo.x, mira.y - ojo.y, 0.0)).normalized()
    x0, x1, y0, y1 = CASA
    m = 1.2
    PISO = ("TER", "MAR", "ESPUMA", "tierra", "TALUD")
    n = 0
    for o in sc.objects:
        if o.type != 'MESH':
            continue
        if o.name.startswith(PISO):
            if not o.hide_render:
                o.hide_render = True
                n += 1
            continue
        b = [o.matrix_world @ Vector(v) for v in o.bound_box]
        ax, bx = min(v.x for v in b), max(v.x for v in b)
        ay, by = min(v.y for v in b), max(v.y for v in b)
        cx, cy = (ax + bx) / 2, (ay + by) / 2
        # tiene que CABER en la casa: `VEC_fila_extra` es una sola malla de
        # x -56 a 63 centrada justo sobre ella, y pasaba cualquier prueba de
        # centro
        cabe = (bx - ax) <= (x1 - x0) + 3.0 and (by - ay) <= (y1 - y0) + 3.0
        dentro = cabe and (x0 - m <= cx <= x1 + m) and (y0 - m <= cy <= y1 + m)
        # la tapa del corte: delgado, alto y del lado del ojo
        delgado = min(bx - ax, by - ay) < 0.40 and (max(v.z for v in b) - min(v.z for v in b)) > 1.5
        tapa = delgado and Vector((cx - CENTRO[0], cy - CENTRO[1], 0.0)).dot(hacia) < 0.0
        if dentro and not tapa and not es_vecina(o.name) and not o.name.endswith("_fantasma"):
            continue
        if not o.hide_render:
            o.hide_render = True
            n += 1
    print("escondidos:", n, "· ojo", OJO, "· mira", MIRA, "· lente", LENTE)
    sc.frame_set(CUADRO)
    bpy.context.view_layer.update()
    return c2


# ------------------------------------------------------------------ sombreado
def modo(pase):
    d = bpy.context.scene.display.shading
    d.type = 'SOLID'
    d.show_specular_highlight = False
    d.background_type = 'VIEWPORT'
    if pase == "gris":
        d.light = 'STUDIO'
        d.color_type = 'SINGLE'
        d.single_color = (0.62, 0.62, 0.62)
        d.show_shadows = True
        d.show_cavity = True
        d.cavity_type = 'BOTH'
        d.show_object_outline = False
        d.background_color = (0.82, 0.86, 0.92)
    elif pase == "blanco":
        d.light = 'FLAT'
        d.color_type = 'SINGLE'
        d.single_color = (1.0, 1.0, 1.0)
        d.show_shadows = False
        d.show_cavity = True
        d.cavity_type = 'BOTH'
        d.curvature_ridge_factor = 2.0
        d.curvature_valley_factor = 2.0
        d.cavity_ridge_factor = 2.5
        d.cavity_valley_factor = 2.5
        d.show_object_outline = True
        d.object_outline_color = (0.0, 0.0, 0.0)
        d.background_color = (1.0, 1.0, 1.0)
    else:                                   # mascara: plano, por color de objeto
        d.light = 'FLAT'
        d.color_type = 'OBJECT'
        d.show_shadows = False
        d.show_cavity = False
        d.show_object_outline = False
        d.background_color = (0.0, 0.0, 0.0)
        # el cielo salia BLANCO y la mascara se comia media imagen: con
        # `background_type='VIEWPORT'` el color de fondo manda, pero el mundo
        # todavia pinta encima si tiene nodos. Se apaga y se pone negro.
        w = bpy.context.scene.world
        if w:
            w.use_nodes = False
            w.color = (0.0, 0.0, 0.0)
        bpy.context.scene.render.film_transparent = False
    if bpy.context.scene.world:
        bpy.context.scene.world.use_nodes = False


def saca(ruta):
    bpy.ops.render.render()
    bpy.data.images["Render Result"].save_render(filepath=ruta)
    print("  ->", ruta, flush=True)


# --- de aqui abajo, solo como guion suelto ---------------------------------
# `camaras_auto.py` IMPORTA este archivo para reusar las manchas por nivel.
# Blender corre los -P como __main__, asi que la linea de comandos no cambia.
if __name__ == "__main__":
    a = sys.argv[sys.argv.index("--") + 1:]
    # OJO: no se llaman LENTE ni nada que pise las constantes de arriba — la
    # primera vez el `LENTE` de la linea de comandos machaco el de OJO/MIRA/LENTE
    # y la camara salio con lente 0.
    _A, _B, _C, DIR = float(a[0]), float(a[1]), float(a[2]), a[3]
    W = int(a[4]) if len(a) > 4 else 1536
    H = int(a[5]) if len(a) > 5 else 1152
    QUE = a[6] if len(a) > 6 else "todo"

    os.makedirs(DIR, exist_ok=True)
    sc = bpy.context.scene
    sc.frame_set(CUADRO)
    bpy.context.view_layer.update()
    print("escondidos por limpia():", limpia())
    apunta_muros()
    camara_del_corte(_A, _B, _C)

    r = sc.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100
    r.image_settings.file_format = 'PNG'
    sc.display.render_aa = '8'

    if QUE in ("gris", "todo"):
        modo("gris")
        saca(os.path.join(DIR, "corte_gris.png"))

    if QUE in ("blanco", "todo"):
        modo("blanco")
        saca(os.path.join(DIR, "corte_blanco.png"))

    if QUE in ("mascaras", "todo"):
        # todo negro; cada mascara se enciende sola
        for o in bpy.data.objects:
            if o.type == 'MESH':
                o.color = (0.0, 0.0, 0.0, 1.0)
        modo("mascara")
        sc.display.render_aa = 'OFF'            # la mascara se quiere dura, sin gris
        hechos = set()
        for cuarto in CUARTOS:
            nivel = cuarto.split("_", 1)[0]
            if nivel in ABIERTOS:
                if nivel in hechos:
                    continue
                hechos.add(nivel)
            ob = caja_del_cuarto(cuarto)
            if ob is None:
                print("  SIN MANCHA:", cuarto, flush=True)
                continue
            clave = nivel if nivel in ABIERTOS else cuarto
            saca(os.path.join(DIR, "mascara_%s.png" % clave))
            bpy.data.objects.remove(ob, do_unlink=True)

    print("LISTO", DIR)
