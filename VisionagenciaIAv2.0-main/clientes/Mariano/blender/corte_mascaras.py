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

# nivel -> (piso, techo). El rg no tiene techo: se le da altura de barandal.
NIVELES = {
    "n1": (-2.75, -0.20),
    "pb": (-0.05,  2.60),
    "pa": ( 2.80,  5.60),
    "rg": ( 5.60,  6.70),
}


def es_vecina(nombre):
    """Las casas clonadas a +-7 m llevan sufijo `_v1`, `_v-1`, `_v2`... La de
    verdad es la que NO lo lleva."""
    cola = nombre.rsplit("_", 1)[-1]
    return cola.startswith("v") and cola[1:].lstrip("-").isdigit()


MUROS = []          # se llena una sola vez, ANTES de que la camara del corte
                    # esconda la fachada: para partir cuartos hacen falta TODOS
                    # los muros, tambien el que se quita para ver el corte.


def apunta_muros():
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.hide_render or es_vecina(o.name):
            continue
        n = o.name
        if not (n.startswith("muro") or n.startswith("div") or "_muro_" in n
                or "_div_" in n):
            continue
        c = [o.matrix_world @ Vector(v) for v in o.bound_box]
        MUROS.append((min(v.x for v in c), max(v.x for v in c),
                      min(v.y for v in c), max(v.y for v in c),
                      min(v.z for v in c), max(v.z for v in c)))
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


def caja_del_cuarto(cuarto):
    """La malla blanca que ocupa el volumen del cuarto. None si no se pudo ubicar."""
    nivel = cuarto.split("_", 1)[0]
    piso, techo = NIVELES[nivel]
    cols, filas, et = manchas(nivel)
    x0, y0 = CASA[0], CASA[2]

    pos = CUARTOS[cuarto][0]                      # la camara vive DENTRO del cuarto
    i = int((pos[0] - x0) / CELDA)
    j = int((pos[1] - y0) / CELDA)
    if not (0 <= i < cols and 0 <= j < filas):
        return None
    mancha = et[j * cols + i]
    if mancha < 0:                                # la camara cayo pegada a un muro:
        for r in (1, 2, 3):                       # se busca la mancha mas cercana
            for dj in range(-r, r + 1):
                for di in range(-r, r + 1):
                    a, b = i + di, j + dj
                    if 0 <= a < cols and 0 <= b < filas and et[b * cols + a] >= 0:
                        mancha = et[b * cols + a]
                        break
                if mancha >= 0:
                    break
            if mancha >= 0:
                break
    if mancha < 0:
        return None

    bm = bmesh.new()
    celdas = 0
    for k, v in enumerate(et):
        if v != mancha:
            continue
        i, j = k % cols, k // cols
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
def camara_del_corte(atras, arriba, lente):
    """Igual que `corte_casa_local.py`: la matriz de CAM_RECORRIDO en el f224,
    retrocedida sobre su propio eje de vision y con el lente abierto."""
    sc = bpy.context.scene
    cam = bpy.data.objects["CAM_RECORRIDO"]
    sc.frame_set(224)
    bpy.context.view_layer.update()
    M = cam.matrix_world.copy()
    eje = (M.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()

    cd = bpy.data.cameras.new("CAM_CORTE")
    cd.lens = lente
    cd.clip_start, cd.clip_end = 0.1, 3000.0
    c2 = bpy.data.objects.new("CAM_CORTE", cd)
    sc.collection.objects.link(c2)
    c2.matrix_world = M
    c2.location = M.translation + eje * atras + Vector((0.0, 0.0, arriba))
    sc.camera = c2

    # lo que quede del lado de la camara cae DENTRO de las vecinas al retroceder
    SUELO = ("TER", "COLONIA", "MAR", "ESPUMA", "tierra", "TALUD", "jardin")
    for o in sc.objects:
        if o.type != 'MESH' or o.name.startswith(SUELO):
            continue
        c = [o.matrix_world @ Vector(v) for v in o.bound_box]
        if "muro_oeste" in o.name or max(v.x for v in c) < 1.25:
            o.hide_render = True
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
    if bpy.context.scene.world:
        bpy.context.scene.world.use_nodes = False


def saca(ruta):
    bpy.ops.render.render()
    bpy.data.images["Render Result"].save_render(filepath=ruta)
    print("  ->", ruta, flush=True)


a = sys.argv[sys.argv.index("--") + 1:]
ATRAS, ARRIBA, LENTE, DIR = float(a[0]), float(a[1]), float(a[2]), a[3]
W = int(a[4]) if len(a) > 4 else 1536
H = int(a[5]) if len(a) > 5 else 1152
QUE = a[6] if len(a) > 6 else "todo"

os.makedirs(DIR, exist_ok=True)
sc = bpy.context.scene
sc.frame_set(CUADRO)
bpy.context.view_layer.update()
print("escondidos por limpia():", limpia())
apunta_muros()
camara_del_corte(ATRAS, ARRIBA, LENTE)

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
    for cuarto in CUARTOS:
        ob = caja_del_cuarto(cuarto)
        if ob is None:
            print("  SIN MANCHA:", cuarto, flush=True)
            continue
        saca(os.path.join(DIR, "mascara_%s.png" % cuarto))
        bpy.data.objects.remove(ob, do_unlink=True)

print("LISTO", DIR)
