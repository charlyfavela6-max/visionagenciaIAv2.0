"""La casa entera en corte, DESDE EL EJE DE LA CAMARA DEL RECORRIDO.

Se toma la matriz de CAM_RECORRIDO en el cuadro de la sala (f224), se retrocede
sobre su propio eje de vision y se abre el lente: el angulo es literalmente el
del recorrido, solo que desde mas lejos para que quepan los tres niveles.

La camara del recorrido mira hacia +X, asi que al retroceder cae DENTRO de las
casas vecinas. Por eso se apaga todo edificio que quede del lado de la camara
(x < 0.8) y se encienden los del otro lado, que son los que dan la calle.
"""
import base64, os
import bpy
from mathutils import Vector

FRAME = 224
ATRAS = __ATRAS__
ARRIBA = __ARRIBA__
LENTE = __LENTE__

sc = bpy.context.scene
r = sc.render
cam = bpy.data.objects["CAM_RECORRIDO"]

prev_frame = sc.frame_current
prev_res = (r.resolution_x, r.resolution_y, r.resolution_percentage)
prev_path = r.filepath
prev_cam = sc.camera

sc.frame_set(FRAME)
bpy.context.view_layer.update()

M = cam.matrix_world.copy()
eje = (M.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()   # hacia atras de la vista
cd = bpy.data.cameras.new("CAM_CORTE_tmp")
cd.lens = LENTE
cd.clip_start, cd.clip_end = 0.1, 3000.0
c2 = bpy.data.objects.new("CAM_CORTE_tmp", cd)
sc.collection.objects.link(c2)
c2.matrix_world = M
c2.location = M.translation + eje * ATRAS + Vector((0.0, 0.0, ARRIBA))
sc.camera = c2
donde = [round(v, 2) for v in c2.location]

SUELO = ("TER", "COLONIA", "MAR", "ESPUMA", "tierra", "TALUD", "jardin")
tocados = {}
for o in sc.objects:
    if o.type != 'MESH' or o.name.startswith(SUELO):
        continue
    # OJO: las casas vecinas no solo son VEC_*, tambien son copias pb_*_v-1,
    # pa_*_v-2, etc. Por eso el filtro es por POSICION, no por nombre.
    # Los tres muros oeste son los que hacen de tapa del corte: son los de
    # CEBOLLA_muros y el rayo desde la camara contesta justo con ellos.
    c = [o.matrix_world @ Vector(v) for v in o.bound_box]
    if "muro_oeste" in o.name or max(v.x for v in c) < 1.25:
        if not o.hide_render:
            tocados[o.name] = False
            o.hide_render = True
    elif o.hide_render and o.name.startswith(("VEC", "vecina")):
        tocados[o.name] = True
        o.hide_render = False

r.resolution_x, r.resolution_y, r.resolution_percentage = 1024, 1280, 100
sal = os.path.join(os.path.expanduser("~"), "casa_completa.png")
r.filepath = sal
try:
    bpy.ops.render.render()
    bpy.data.images["Render Result"].save_render(filepath=sal)
    png = base64.b64encode(open(sal, "rb").read()).decode()
finally:
    for n, antes in tocados.items():
        bpy.data.objects[n].hide_render = antes
    sc.camera = prev_cam
    bpy.data.objects.remove(c2, do_unlink=True)
    bpy.data.cameras.remove(cd)
    r.resolution_x, r.resolution_y, r.resolution_percentage = prev_res
    r.filepath = prev_path
    sc.frame_set(prev_frame)

responder({"png": png, "camara": donde, "apagados": len(tocados)})
