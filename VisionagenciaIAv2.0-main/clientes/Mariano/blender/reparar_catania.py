# reparar_catania.py — arregla el .blend SIN interfaz gráfica.
#
#   blender -b catania_LIGERA.blend --python reparar_catania.py
#
# Corre en headless a propósito. La mayoría de las caídas de este archivo pasan
# en la interfaz: EEVEE sobre OpenGL en Mac, el timer del addon, el visor 3D
# redibujando 1306 objetos. Sin ventana no hay nada de eso, así que si algo
# truena aquí es el archivo, y se ve el error exacto en vez de un cierre seco.
#
# Al terminar guarda `catania_REPARADA.blend` al lado y RENDEA UN CUADRO para
# comprobar que de verdad se puede rendear. Si el render no sale, el script
# falla ruidosamente: no sirve devolver un archivo que "parece" bueno.

import bpy
import os
import re
import sys
import time

T0 = time.time()
R = []


def log(t):
    R.append(t)
    print("[reparar] " + t, flush=True)


log("archivo: %s" % (bpy.data.filepath or "(ninguno)"))
log("objetos: %d · mallas: %d · materiales: %d · imágenes: %d"
    % (len(bpy.data.objects), len(bpy.data.meshes),
       len(bpy.data.materials), len(bpy.data.images)))

sc = bpy.context.scene

# ── 1. MODIFICADORES VIVOS ───────────────────────────────────────────────
# Un modificador se re-evalúa en CADA cuadro y sobre CADA objeto. 400 BEVEL
# fue lo que tumbó la máquina la primera vez. Aquí se aplican de una vez: la
# geometría queda con el chaflán y el costo por cuadro baja a cero.
COPIA = re.compile(r"(_v-?\d+)$|_fantasma")
aplicados = quitados = 0

for o in list(bpy.data.objects):
    mods = [m for m in o.modifiers if m.type == "BEVEL"]
    if not mods:
        continue
    # Las copias de las casas vecinas nunca se ven de cerca: fuera.
    if o.type != "MESH" or COPIA.search(o.name):
        for m in mods:
            o.modifiers.remove(m)
            quitados += 1
        continue
    for m in mods:
        m.segments = 1
        m.width = min(m.width, 0.008)
    # Aplicar necesita que el objeto sea el activo y esté seleccionable.
    try:
        oculto = o.hide_get()
        o.hide_set(False)
        bpy.context.view_layer.objects.active = o
        for m in list(o.modifiers):
            if m.type == "BEVEL":
                bpy.ops.object.modifier_apply(modifier=m.name)
                aplicados += 1
        o.hide_set(oculto)
    except Exception as e:
        for m in [m for m in o.modifiers if m.type == "BEVEL"]:
            o.modifiers.remove(m)
            quitados += 1
        log("  no se pudo aplicar en %s (%s) — se quitó" % (o.name, type(e).__name__))

log("chaflanes aplicados: %d · quitados: %d" % (aplicados, quitados))

vivos = sum(1 for o in bpy.data.objects for m in o.modifiers)
log("modificadores vivos que quedan (de cualquier tipo): %d" % vivos)

# ── 2. AJUSTES DE RENDER SEGUROS ─────────────────────────────────────────
# Los renders que SÍ salieron fueron Workbench a 1080x1350 con el AA de
# fábrica. Yo mismo había subido render_aa a '16' (el doble) y la resolución a
# 1080x1920 (42% más píxeles); esa combinación fue la que dejó de terminar.
log("antes — motor:%s AA:%s res:%dx%d"
    % (sc.render.engine, sc.display.render_aa,
       sc.render.resolution_x, sc.render.resolution_y))

sc.render.engine = "BLENDER_WORKBENCH"
sc.display.render_aa = "5"
sc.display.viewport_aa = "5"
sc.render.resolution_x, sc.render.resolution_y = 1080, 1350
sc.render.resolution_percentage = 100
sc.render.use_persistent_data = False

ds = sc.display.shading
ds.light = "STUDIO"
ds.color_type = "MATERIAL"      # respeta el alpha animado de los muros
ds.show_cavity = True
ds.cavity_type = "BOTH"
ds.cavity_ridge_factor = 0.55
ds.cavity_valley_factor = 1.25
ds.show_shadows = True
ds.shadow_intensity = 0.28
ds.show_object_outline = False
log("después — Workbench · AA 5 · 1080x1350 · cavidad y sombra")

# ── 3. EL PISO DE PLANTA ALTA ────────────────────────────────────────────
# Nivel -1 y Planta Baja tienen su losa de 51.3 m²; Planta Alta no tenía nada
# entre y 6.7 y 12.5, que es donde van sala, comedor y cocina. De ahí el hueco
# gris bajo el sillón, y Planta Baja sin techo.
if not bpy.data.objects.get("pa_piso"):
    X0, X1, Y0, Y1, Z0, Z1 = 1.10, 6.90, 6.70, 12.50, 2.70, 2.80
    verts = [(X0, Y0, Z0), (X1, Y0, Z0), (X1, Y1, Z0), (X0, Y1, Z0),
             (X0, Y0, Z1), (X1, Y0, Z1), (X1, Y1, Z1), (X0, Y1, Z1)]
    faces = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    me = bpy.data.meshes.new("pa_piso")
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    piso = bpy.data.objects.new("pa_piso", me)
    ref = bpy.data.objects.get("pb_piso")
    if ref and ref.material_slots and ref.material_slots[0].material:
        piso.data.materials.append(ref.material_slots[0].material)
    (bpy.data.collections.get("PLANTA_ALTA") or sc.collection).objects.link(piso)
    log("pa_piso creado — 33.6 m²")
else:
    log("pa_piso ya estaba")

# ── 4. EL OJITO NO APAGA LA CAMARITA ─────────────────────────────────────
# hide_viewport (el ojo del outliner) NO toca hide_render. Un objeto escondido
# para trabajar sigue saliendo en el render: así fue como `vecina_oeste` tapaba
# la sala entera con una pared gris.
sync = 0
for o in bpy.data.objects:
    if o.hide_viewport and not o.hide_render:
        o.hide_render = True
        sync += 1
log("objetos escondidos que aún renderizaban: %d" % sync)

# ── 5. RÓTULOS DEL PISO ──────────────────────────────────────────────────
# "SALA-COMEDOR", "COCINA"… escritos sobre la loseta. Si ese cuadro va a GPT
# Image, el modelo intenta redibujar el texto y sale basura.
col = bpy.data.collections.get("ROTULOS")
n = 0
if col:
    for o in col.all_objects:
        if not o.hide_render:
            o.hide_render = True
            n += 1
log("rótulos apagados: %d" % n)

# ── 6. TIRAR LA BASURA ───────────────────────────────────────────────────
antes = (len(bpy.data.meshes), len(bpy.data.materials), len(bpy.data.images))
try:
    for _ in range(3):
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True,
                                       do_recursive=True)
    log("purga — mallas %d→%d · materiales %d→%d · imágenes %d→%d"
        % (antes[0], len(bpy.data.meshes), antes[1], len(bpy.data.materials),
           antes[2], len(bpy.data.images)))
except Exception as e:
    log("purga no disponible en headless (%s) — se sigue" % type(e).__name__)

# ── 7. GUARDAR ───────────────────────────────────────────────────────────
origen = bpy.data.filepath
destino = os.path.join(os.path.dirname(origen) or ".", "catania_REPARADA.blend")
bpy.ops.wm.save_as_mainfile(filepath=destino, compress=True)
log("guardado: %s (%.1f MB)" % (destino, os.path.getsize(destino) / 1e6))

# ── 8. LA PRUEBA DE FUEGO ────────────────────────────────────────────────
# No sirve devolver un archivo que "parece" bueno: hay que probar que rendea.
t = time.time()
sc.frame_set(111)
sc.render.image_settings.file_format = "JPEG"
sc.render.image_settings.quality = 90
sc.render.filepath = os.path.join(os.path.dirname(destino) or ".",
                                  "prueba_f111.jpg")
bpy.ops.render.render(write_still=True)
seg = time.time() - t
log("RENDER DE PRUEBA OK — frame 111 en %.1f s" % seg)

log("total: %.1f s" % (time.time() - T0))
print("\n".join(["", "=" * 50] + R + ["=" * 50]), flush=True)
