"""Sello Trodat Pocket Printy 9511 en Blender, con el pliegue animado.

Se manda a la escena en su propia coleccion `SELLO_9511`, sin borrar nada mas.

    python3 bench-blender/check_sello_trodat_9511.py   # SIEMPRE primero
    python3 bench-blender/sello_trodat_9511.py

De donde salen los numeros
--------------------------
De `sello_trodat_9511_mec.py`, que separa lo CERTIFICADO (ficha de Trodat: cuerpo
77 x 28 x 23, huella 38 x 14, placa maxima 37 x 13, cartucho 6/9511 de 47 x 21 x 7)
de lo DEDUCIDO (reparto de las hojas, pared, radios, bisagra). Si el plano en la
mano contradice algo, se corrige en el `_mec` y esta escena se rehace sola.

Lo que cuenta la animacion, en tres tiempos
-------------------------------------------
  1-50   la tapa gira 180 grados sobre la bisagra. Cerrado, la goma estaba
         besando el fieltro: por eso el sello siempre sale entintado y no hay
         tampon aparte que buscar.
  50-80  el aparato se voltea en la mano. Al desdoblarse la placa quedo mirando
         arriba: hay que darle la vuelta, y el cuerpo se vuelve el mango.
  80-100 baja y estampa. El relieve de 0.9 mm es lo unico que toca el papel.

El espejo de la goma, que es facil de poner al reves
---------------------------------------------------
Cuando el sello aprieta, cada punto de la goma toca el papel en su MISMO (x, y):
el contacto no invierte nada. Entonces la goma tiene que estar puesta como se
quiere leer la huella, mirandola desde arriba — no en espejo.

Lo que si se ve al reves es la CARA de la goma, porque para mirarla de frente
hay que ponerse debajo. Por eso en el cuadro 50, con la placa ya volteada hacia
arriba, el texto sale invertido en pantalla: ahi estas viendo la cara que
imprime. En el cuadro 100 la placa volvio a su orientacion (dos giros de 180 son
un giro de 360) y la huella del papel se lee bien.

Ese par es la prueba: cuadro 50 al reves, papel al derecho. Si los dos salen
iguales, el espejo esta mal puesto y el sello imprimiria del reves.
"""

import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sello_trodat_9511_mec as M

CONECTOR = os.environ.get("BLENDER_CONECTOR", "https://conectorblender.onrender.com")

# El texto del sello. Tres renglones porque la ficha dice tres.
LINEAS = ["VISION AGENCIA", "NOGALES, SON.", "31 AGO 2026"]

GUION = r'''
import math
import bmesh
import bpy
from mathutils import Vector

# ---- los numeros, en metros (calcados de sello_trodat_9511_mec.py) ----------
CUERPO_LARGO, CUERPO_ANCHO, CUERPO_GRUESO = %(largo)r, %(ancho)r, %(grueso)r
HOJA_TINTA, HOJA_PLACA = %(hoja_tinta)r, %(hoja_placa)r
PLACA_X, PLACA_Y = %(placa_x)r, %(placa_y)r
HUELLA_X, HUELLA_Y = %(huella_x)r, %(huella_y)r
CART_X, CART_Y, CART_Z = %(cart_x)r, %(cart_y)r, %(cart_z)r
GOMA_ALTO, RELIEVE, PORTAPLACA = %(goma)r, %(relieve)r, %(portaplaca)r
RADIO_CANTO, PARED = %(radio)r, %(pared)r
BISAGRA_R, BISAGRA_X, BISAGRA_Z = %(bis_r)r, %(bis_x)r, %(bis_z)r
CORDON_D, CORDON_BORDE = %(cordon_d)r, %(cordon_borde)r
JUNTA = %(junta)r
ALTO_LINEA = %(alto_linea)r
LINEAS = %(lineas)r
CUADROS = 100
F_ABRE, F_VOLTEA, F_BAJA = 50, 80, 100

esc = bpy.context.scene
esc.frame_start, esc.frame_end = 1, CUADROS
esc.unit_settings.system = 'METRIC'
esc.unit_settings.length_unit = 'MILLIMETERS'

col = bpy.data.collections.get("SELLO_9511")
if col:
    for o in list(col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
else:
    col = bpy.data.collections.new("SELLO_9511")
    bpy.context.scene.collection.children.link(col)


def mat(nombre, color, metal=0.0, rug=0.5):
    m = bpy.data.materials.get(nombre)
    if m:
        return m
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    def pon(cs, v):
        for c in cs:
            if c in p.inputs:
                p.inputs[c].default_value = v
                return
    pon(["Base Color"], (color[0], color[1], color[2], 1.0))
    pon(["Metallic"], metal)
    pon(["Roughness"], rug)
    # Workbench no mira el Principled: el color solido va aparte
    m.diffuse_color = (color[0], color[1], color[2], 1.0)
    return m

NEGRO   = mat("S9_cuerpo",   (0.020, 0.020, 0.022), rug=0.52)
GRIS    = mat("S9_tapa",     (0.055, 0.055, 0.060), rug=0.45)
GOMA    = mat("S9_goma",     (0.38, 0.055, 0.075), rug=0.72)
FIELTRO = mat("S9_fieltro",  (0.045, 0.055, 0.16), rug=0.95)
METAL   = mat("S9_metal",    (0.62, 0.63, 0.65), metal=1.0, rug=0.30)
PAPEL   = mat("S9_papel",    (0.86, 0.855, 0.83), rug=0.88)
TINTA   = mat("S9_tinta",    (0.035, 0.035, 0.045), rug=0.60)


def caja(nombre, dx, dy, dz, centro, material=None, bisel=0.0, seg=3):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((dx, dy, dz)), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(centro), verts=bm.verts)
    me = bpy.data.meshes.new(nombre)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(nombre, me)
    col.objects.link(ob)
    if material:
        ob.data.materials.append(material)
    if bisel:
        b = ob.modifiers.new("bisel", 'BEVEL')
        b.width = bisel
        b.segments = seg
        b.limit_method = 'ANGLE'
        b.angle_limit = math.radians(40)
    return ob


def cilindro(nombre, r, largo, centro, eje='Y', material=None, seg=32):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg,
                          radius1=r, radius2=r, depth=largo)
    rot = {'X': (0, math.pi / 2, 0), 'Y': (math.pi / 2, 0, 0), 'Z': (0, 0, 0)}[eje]
    me = bpy.data.meshes.new(nombre)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(nombre, me)
    ob.rotation_euler = rot
    ob.location = Vector(centro)
    col.objects.link(ob)
    if material:
        ob.data.materials.append(material)
    return ob


def renglon(nombre, texto, i, espejo, z, material):
    cu = bpy.data.curves.new(nombre, type='FONT')
    cu.body = texto
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    cu.size = ALTO_LINEA * 0.70
    cu.extrude = RELIEVE / 2.0
    ob = bpy.data.objects.new(nombre, cu)
    col.objects.link(ob)
    ob.data.materials.append(material)
    bpy.context.view_layer.update()
    ancho = ob.dimensions.x or PLACA_X
    ajuste = min(1.0, PLACA_X / ancho)
    ob.scale = Vector((-ajuste if espejo else ajuste, ajuste, 1.0))
    ob.location = Vector((0.0, PLACA_Y / 2 - (i + 0.5) * ALTO_LINEA, z))
    return ob


# ---- hoja del cartucho: el cuerpo que se queda quieto ----------------------
hoja_tinta = caja("sh_hoja_tinta", CUERPO_LARGO, CUERPO_ANCHO, HOJA_TINTA,
                  (0, 0, HOJA_TINTA / 2), NEGRO, bisel=RADIO_CANTO)
cart = caja("sh_cartucho", CART_X, CART_Y, CART_Z,
            (0, 0, JUNTA - CART_Z / 2), FIELTRO, bisel=0.4 * 0.001)
# el borde que rodea al fieltro: lo que hace de capuchon cuando esta cerrado
marco = caja("sh_marco_fieltro", CART_X + 2 * PARED, CART_Y + 2 * PARED, 0.8 * 0.001,
             (0, 0, JUNTA - 0.4 * 0.001), GRIS)
cordon = cilindro("sh_ojal_cordon", CORDON_D / 2, HOJA_TINTA * 1.02,
                  (CUERPO_LARGO / 2 - CORDON_BORDE, 0, HOJA_TINTA / 2), 'Z', METAL, seg=24)

# ---- todo lo que gira, colgado de un vacio puesto EN el eje ----------------
piv = bpy.data.objects.new("sh_pivote", None)
piv.empty_display_type = 'PLAIN_AXES'
piv.empty_display_size = 0.012
piv.location = Vector((BISAGRA_X, 0, BISAGRA_Z))
col.objects.link(piv)

tapa = caja("sh_hoja_placa", CUERPO_LARGO, CUERPO_ANCHO, HOJA_PLACA,
            (0, 0, JUNTA + HOJA_PLACA / 2), GRIS, bisel=RADIO_CANTO)
porta = caja("sh_portaplaca", HUELLA_X, HUELLA_Y, PORTAPLACA,
             (0, 0, JUNTA + GOMA_ALTO + PORTAPLACA / 2), NEGRO)
goma = caja("sh_goma", HUELLA_X, HUELLA_Y, GOMA_ALTO,
            (0, 0, JUNTA + GOMA_ALTO / 2), GOMA)
eje = cilindro("sh_eje_bisagra", BISAGRA_R, CUERPO_ANCHO * 0.96,
               (BISAGRA_X, 0, BISAGRA_Z), 'Y', METAL)

# el relieve: hacia ABAJO desde la cara de la goma, que es la que besa el fieltro
# Sin espejo: el contacto goma->papel es la identidad en (x, y). Ver el
# encabezado — poner True aqui es el error clasico y sale un sello invertido.
letras = [renglon("sh_letra_%%d" %% i, t, i, False, JUNTA - RELIEVE / 2.0, GOMA)
          for i, t in enumerate(LINEAS)]

bpy.context.view_layer.update()
for o in [tapa, porta, goma, eje] + letras:
    o.parent = piv
    o.matrix_parent_inverse = piv.matrix_world.inverted()

# ---- raiz: la mano que voltea y baja el aparato ----------------------------
raiz = bpy.data.objects.new("sh_raiz", None)
raiz.empty_display_type = 'ARROWS'
raiz.empty_display_size = 0.02
col.objects.link(raiz)
bpy.context.view_layer.update()
for o in (hoja_tinta, cart, marco, cordon, piv):
    o.parent = raiz
    o.matrix_parent_inverse = raiz.matrix_world.inverted()

# La punta del relieve, despues de que la tapa dio los 180 grados, queda a
# JUNTA + RELIEVE por encima del plano de la junta. Al voltear la raiz 180
# grados esa punta pasa a -(JUNTA + RELIEVE): hay que subir la raiz eso mismo
# para que aterrice justo en el papel, en z = 0.
PUNTA = 2 * BISAGRA_Z - (JUNTA - RELIEVE)   # = 14.9 mm con la bisagra en la junta
ESTAMPA_X = -2 * BISAGRA_X                  # donde cae la huella sobre el papel
ALTO_ANTES = 0.006                          # 6 mm de aproximacion antes de apretar


def llave(ob, campo, cuadro, valor, indice=-1):
    if indice >= 0:
        getattr(ob, campo)[indice] = valor
    else:
        setattr(ob, campo, valor)
    ob.keyframe_insert(data_path=campo, frame=cuadro, index=indice)


def suave(t):
    return t * t * (3 - 2 * t)


# 1) la tapa se abre
for fr in range(1, F_ABRE + 1):
    t = (fr - 1) / float(F_ABRE - 1)
    llave(piv, "rotation_euler", fr, math.pi * suave(t), 1)
# 2) el aparato se voltea en la mano
for fr in range(F_ABRE, F_VOLTEA + 1):
    t = (fr - F_ABRE) / float(F_VOLTEA - F_ABRE)
    llave(raiz, "rotation_euler", fr, math.pi * suave(t), 1)
    llave(raiz, "location", fr, PUNTA * suave(t) + ALTO_ANTES * suave(t), 2)
# 3) baja y estampa
for fr in range(F_VOLTEA, F_BAJA + 1):
    t = (fr - F_VOLTEA) / float(F_BAJA - F_VOLTEA)
    llave(raiz, "location", fr, PUNTA + ALTO_ANTES * (1 - suave(t)), 2)

for ob in (piv, raiz):
    if ob.animation_data and ob.animation_data.action:
        for fc in ob.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'

# ---- papel y la huella legible, para comparar ------------------------------
papel = caja("sh_papel", 0.22, 0.14, 0.0004, (0.03, 0, -0.0002), PAPEL)
papel.parent = None
for i, t in enumerate(LINEAS):
    h = renglon("sh_huella_legible_%%d" %% i, t, i, False, 0.00005, TINTA)
    h.location = Vector((ESTAMPA_X, h.location.y - 0.040, 0.00005))
    h.data.extrude = 0.0

print("SELLO_9511 listo: %%d objetos, %%d cuadros" %% (len(col.objects), CUADROS))
''' % {
    "largo": M.CUERPO_LARGO, "ancho": M.CUERPO_ANCHO, "grueso": M.CUERPO_GRUESO,
    "hoja_tinta": M.HOJA_TINTA, "hoja_placa": M.HOJA_PLACA,
    "placa_x": M.PLACA_X, "placa_y": M.PLACA_Y,
    "huella_x": M.HUELLA_X, "huella_y": M.HUELLA_Y,
    "cart_x": M.CART_X, "cart_y": M.CART_Y, "cart_z": M.CART_Z,
    "goma": M.GOMA_ALTO, "relieve": M.RELIEVE, "portaplaca": M.PORTAPLACA,
    "radio": M.RADIO_CANTO, "pared": M.PARED,
    "bis_r": M.BISAGRA_R, "bis_x": M.BISAGRA_X, "bis_z": M.BISAGRA_Z,
    "cordon_d": M.CORDON_D, "cordon_borde": M.CORDON_BORDE,
    "junta": M.junta_z(), "alto_linea": M.alto_por_linea(),
    "lineas": LINEAS,
}


def ejecuta(codigo, timeout=900):
    d = json.dumps({"python": codigo, "meta": {"tipo": "invento",
                                               "invento": "sello_trodat_9511"}}).encode()
    req = urllib.request.Request(CONECTOR + "/api/blender/execute", data=d,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as x:
        r = json.loads(x.read())
    r.pop("python", None)
    return r


if __name__ == "__main__":
    compile(GUION, "<guion>", "exec")          # que no salga con un error de sintaxis
    print(json.dumps(ejecuta(GUION), indent=1, ensure_ascii=False)[:3000])
