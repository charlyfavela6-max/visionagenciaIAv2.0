"""Saca frames de la Catania con el Blender del Codespace, sin tocar el Mac.

    blender -b <archivo>.blend -P render_local.py -- <frame> <salida.png> [w] [h]

Mismo trato que por el conector: AA 8 y la resolucion que se pida. Como aqui el
archivo se abre de solo lectura y nunca se guarda, no hace falta restaurar nada.
"""
import sys
import bpy

arg = sys.argv[sys.argv.index("--") + 1:]
frame, sal = int(arg[0]), arg[1]
w = int(arg[2]) if len(arg) > 2 else 810
h = int(arg[3]) if len(arg) > 3 else 1440

sc = bpy.context.scene
r = sc.render
sc.frame_set(frame)
bpy.context.view_layer.update()
r.resolution_x, r.resolution_y, r.resolution_percentage = w, h, 100
r.image_settings.file_format = 'PNG'
r.filepath = sal
sc.display.render_aa = '8'

bpy.ops.render.render()
bpy.data.images["Render Result"].save_render(filepath=sal)
print(f"OK {sal} f{frame} {w}x{h}")
