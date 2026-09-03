"""La casa entera en corte, con el Blender del Codespace.

    blender -b <blend> -P corte_casa_local.py -- <atras> <arriba> <lente> <salida> [w] [h]

Mismo criterio que `corte_desde_el_recorrido.py`: se toma la matriz de
CAM_RECORRIDO en el cuadro de la sala (f224), se retrocede sobre su propio eje
de vision y se abre el lente, para que el angulo sea el del recorrido pero desde
mas lejos. Se apaga todo lo que quede del lado de la camara (x < 1.25) porque al
retroceder cae DENTRO de las vecinas — filtrado por POSICION, que las copias se
llaman pb_*_v-1 y no VEC_*.
"""
import sys
import bpy
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
ATRAS, ARRIBA, LENTE, SAL = float(a[0]), float(a[1]), float(a[2]), a[3]
W = int(a[4]) if len(a) > 4 else 1080
H = int(a[5]) if len(a) > 5 else 1350
FRAME = 224

sc = bpy.context.scene
r = sc.render
cam = bpy.data.objects["CAM_RECORRIDO"]
sc.frame_set(FRAME)
bpy.context.view_layer.update()

M = cam.matrix_world.copy()
eje = (M.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()
cd = bpy.data.cameras.new("CAM_CORTE_tmp")
cd.lens = LENTE
cd.clip_start, cd.clip_end = 0.1, 3000.0
c2 = bpy.data.objects.new("CAM_CORTE_tmp", cd)
sc.collection.objects.link(c2)
c2.matrix_world = M
c2.location = M.translation + eje * ATRAS + Vector((0.0, 0.0, ARRIBA))
sc.camera = c2

SUELO = ("TER", "COLONIA", "MAR", "ESPUMA", "tierra", "TALUD", "jardin")
n_off = n_on = 0
for o in sc.objects:
    if o.type != 'MESH' or o.name.startswith(SUELO):
        continue
    c = [o.matrix_world @ Vector(v) for v in o.bound_box]
    if "muro_oeste" in o.name or max(v.x for v in c) < 1.25:
        if not o.hide_render:
            o.hide_render = True; n_off += 1
    elif o.hide_render and o.name.startswith(("VEC", "vecina")):
        o.hide_render = False; n_on += 1

r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100
sc.display.render_aa = '8'
r.image_settings.file_format = 'PNG'
r.filepath = SAL
bpy.ops.render.render()
bpy.data.images["Render Result"].save_render(filepath=SAL)
print(f"OK {SAL}  atras={ATRAS} arriba={ARRIBA} lente={LENTE}  apagados={n_off} encendidos={n_on}")
