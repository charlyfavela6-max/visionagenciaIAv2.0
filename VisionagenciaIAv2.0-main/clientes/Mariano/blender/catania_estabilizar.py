# catania_estabilizar.py — deja la Catania en un estado que NO tumba Blender.
#
# CÓMO SE USA (no hace falta el conector):
#   1. Abrir catania_LIGERA.blend en Blender
#   2. Pestaña Scripting → Abrir → elegir este archivo → Run Script (▶)
#   3. Al terminar imprime un reporte en la consola y guarda catania_SEGURA.blend
#      AL LADO del original. El original NO se toca.
#
# ─────────────────────────────────────────────────────────────────────────
# POR QUÉ SE CAÍA
#
# Tres cosas se acumularon, cada una multiplicando a la anterior:
#
#   1. 400 modificadores BEVEL. Blender los evalúa en CADA cuadro, sobre 400
#      objetos. Ese fue el golpe grande (se tumbó a los 10 min de render).
#   2. display.render_aa = '16'. Es el antialiasing más alto de Workbench, el
#      doble del que trae por defecto. En un render grande eso solo ya duplica.
#   3. Resolución 1080x1920 en vez de 1080x1350: 42% más píxeles.
#
# Los renders que SÍ salieron fueron a 1080x1350, con el AA de fábrica y sin
# chaflanes. Este script regresa a esa zona segura sin perder lo bueno.
# ─────────────────────────────────────────────────────────────────────────

import bpy
import re
import os

rep = []


def anota(t):
    rep.append(t)
    print("  " + t)


print("\n=== ESTABILIZANDO LA CATANIA ===\n")

# ── 1. CHAFLANES: aplicarlos de una vez en vez de dejarlos vivos ─────────
# Un modificador se recalcula en cada cuadro; aplicado, la geometría ya trae
# el chaflán y cuesta CERO por cuadro. Sobre pocos objetos el peso extra de
# malla es despreciable y el render deja de pagar el impuesto.
COPIA = re.compile(r"(_v-?\d+)$|_fantasma")
aplicados, quitados = 0, 0

for o in list(bpy.data.objects):
    bevels = [m for m in o.modifiers if m.type == "BEVEL"]
    if not bevels:
        continue
    # Las copias de las casas vecinas no se ven de cerca: no merecen chaflán.
    if COPIA.search(o.name) or o.type != "MESH":
        for m in bevels:
            o.modifiers.remove(m)
            quitados += 1
        continue
    for m in bevels:
        m.segments = 1              # 1 basta para que la arista atrape luz
        m.width = min(m.width, 0.008)
        try:
            bpy.context.view_layer.objects.active = o
            bpy.ops.object.modifier_apply(modifier=m.name)
            aplicados += 1
        except Exception as e:
            # Si no se puede aplicar (malla compartida, por ejemplo), se quita:
            # vale más un archivo estable que una arista bonita.
            try:
                o.modifiers.remove(m)
                quitados += 1
            except Exception:
                pass

anota("chaflanes aplicados: %d · quitados: %d" % (aplicados, quitados))

# ── 2. AJUSTES DE RENDER, de vuelta a la zona segura ────────────────────
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"          # lo estable en este Mac
sc.display.render_aa = "5"                      # antes 16: ahí estaba el costo
sc.display.viewport_aa = "5"
sc.render.resolution_x, sc.render.resolution_y = 1080, 1350
sc.render.resolution_percentage = 100
sc.render.use_persistent_data = False           # no acumular entre cuadros
anota("render: Workbench · AA 5 · 1080x1350")

# El sombreado que hace que los muros se lean; barato, se queda.
ds = sc.display.shading
ds.light = "STUDIO"
ds.color_type = "MATERIAL"                      # respeta el alpha animado
ds.show_cavity = True
ds.cavity_type = "BOTH"
ds.cavity_ridge_factor = 0.55
ds.cavity_valley_factor = 1.25
ds.show_shadows = True
ds.shadow_intensity = 0.28
ds.show_object_outline = False
anota("sombreado: cavidad + sombra (esto es barato, se queda)")

# ── 3. EL PISO DE PLANTA ALTA ───────────────────────────────────────────
# n1 y pb tienen su losa de 51.3 m2; planta alta no tenía NADA de y 6.7 a 12.5,
# que es justo donde van sala, comedor y cocina. Por eso se veía el hueco gris
# bajo el sillón, y planta baja se quedaba sin techo.
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
    col = bpy.data.collections.get("PLANTA_ALTA") or sc.collection
    col.objects.link(piso)
    anota("pa_piso creado (33.6 m2, travertino)")
else:
    anota("pa_piso ya estaba")

# ── 4. LA CAMARITA CONTRA EL OJITO ──────────────────────────────────────
# El ojo del outliner (hide_viewport) NO apaga la camarita (hide_render). Un
# objeto escondido para trabajar sigue saliendo en el render: así fue como
# vecina_oeste tapaba la sala con una pared gris.
sync = 0
for o in bpy.data.objects:
    if o.hide_viewport and not o.hide_render:
        o.hide_render = True
        sync += 1
anota("objetos escondidos que aún renderizaban: %d (corregidos)" % sync)

# ── 5. LOS RÓTULOS DEL PISO ─────────────────────────────────────────────
# "SALA-COMEDOR", "COCINA"... escritos en el piso. Sirven para revisar, pero si
# ese frame va a GPT Image el modelo intenta redibujar el texto y sale basura.
col = bpy.data.collections.get("ROTULOS")
n = 0
if col:
    for o in col.all_objects:
        if not o.hide_render:
            o.hide_render = True
            n += 1
anota("rótulos apagados para render: %d" % n)

# ── 6. TIRAR LA BASURA ──────────────────────────────────────────────────
# Mallas, materiales e imágenes que ya nadie usa siguen ocupando RAM.
antes = (len(bpy.data.meshes), len(bpy.data.materials), len(bpy.data.images))
for _ in range(3):
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True,
                                   do_recursive=True)
despues = (len(bpy.data.meshes), len(bpy.data.materials), len(bpy.data.images))
anota("purga — mallas %d→%d · materiales %d→%d · imágenes %d→%d"
      % (antes[0], despues[0], antes[1], despues[1], antes[2], despues[2]))

# ── 7. GUARDAR APARTE ───────────────────────────────────────────────────
# Copia nueva: si algo no gusta, el original sigue intacto.
origen = bpy.data.filepath or os.path.expanduser("~/catania.blend")
destino = os.path.join(os.path.dirname(origen), "catania_SEGURA.blend")
bpy.ops.wm.save_as_mainfile(filepath=destino)

print("\n=== LISTO ===")
print("  objetos: %d · chaflanes vivos: %d"
      % (len(bpy.data.objects),
         sum(1 for o in bpy.data.objects for m in o.modifiers if m.type == "BEVEL")))
print("  guardado en: %s" % destino)
print("\n  REGLAS PARA QUE NO SE VUELVA A CAER:")
print("  · un frame por vez, nunca una tanda")
print("  · 1080x1350 o menos; 1080x1920 es 42%% más píxeles")
print("  · display.render_aa en 5, nunca en 16")
print("  · no dejar modificadores vivos sobre cientos de objetos")
