"""Lo que el video del 3 sep enseña y al modelo le faltaba, cuarto por cuarto.

    blender -b <blend> -P detalles_video_4sep.py            # aplica y guarda
    blender -b <blend> -P detalles_video_4sep.py -- nosave

Todo va a la coleccion `DETALLES_VIDEO`, asi que se quita borrandola.

QUE SE CONFIRMO EN EL VIDEO, segundo por segundo
------------------------------------------------
COMEDOR (t 53.5-54 s) — el modelo tenia TRES lamparas de campana; la real es
  UNA sola, un lazo de LED curvo. Y le faltaba todo lo de la mesa:
    · lampara de LAZO colgante sobre la mesa
    · DOS velas blancas gruesas sobre una charola negra
    · un florero de vidrio con planta verde
    · DOS cuadros/paneles beige grandes en la pared del fondo
    · un jarron alto de ceramica con ramas secas junto a la ventana

COCINETA (t 55 s) — es CHICA y en L, no la cocina larga del modelo:
    · isla de MADERA con cubierta BLANCA delgada
    · gabinetes superiores BLANCOS
    · una repisa flotante blanca
    · parrilla negra empotrada
    · VENTANA HORIZONTAL sobre la cubierta — la del modelo era vertical

BANOS (t 12 s y las fotos) — el modelo solo tenia lavabo, WC y plato de
  regadera. Faltaba lo que se ve:
    · mueble de madera flotante bajo el lavabo
    · espejo
    · mampara de vidrio de la regadera
    · la regadera misma

TERRAZA (t 56-61 s) — habia banca y mesa de teca; faltaba:
    · sofa blanco de exterior con cojines grises
    · dos sillones individuales blancos
    · mesa baja BLANCA de listones

ESCALERA (t 26-28 s) — un cuadro abstracto grande y una lampara de pared.

Ojo: las jardineras del roof SI existen y estan bien (dos de concreto con 19
matas). El error era de `limpia()`, que las escondia.
"""
import sys

import bpy

COL = "DETALLES_VIDEO"


def mat(nombre, rgb, rug=0.7):
    m = bpy.data.materials.get(nombre)
    if m is None:
        m = bpy.data.materials.new(nombre)
        m.use_nodes = True
        b = m.node_tree.nodes.get("Principled BSDF")
        if b:
            b.inputs["Base Color"].default_value = (*rgb, 1.0)
            if "Roughness" in b.inputs:
                b.inputs["Roughness"].default_value = rug
    m.diffuse_color = (*rgb, 1.0)      # Workbench pinta con ESTO
    return m


def coleccion():
    c = bpy.data.collections.get(COL)
    if c is None:
        c = bpy.data.collections.new(COL)
        bpy.context.scene.collection.children.link(c)
    return c


def caja(col, nombre, x0, x1, y0, y1, z0, z1, material):
    v = bpy.data.objects.get(nombre)
    if v:
        bpy.data.objects.remove(v, do_unlink=True)
    me = bpy.data.meshes.new(nombre)
    ver = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
           (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    car = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4),
           (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me.from_pydata(ver, [], car)
    me.update()
    o = bpy.data.objects.new(nombre, me)
    o.data.materials.append(material)
    col.objects.link(o)
    return o


def cilindro(col, nombre, cx, cy, z0, z1, r, material, lados=16):
    import math
    v = bpy.data.objects.get(nombre)
    if v:
        bpy.data.objects.remove(v, do_unlink=True)
    ver, car = [], []
    for i in range(lados):
        a = 2 * math.pi * i / lados
        ver.append((cx + r * math.cos(a), cy + r * math.sin(a), z0))
    for i in range(lados):
        a = 2 * math.pi * i / lados
        ver.append((cx + r * math.cos(a), cy + r * math.sin(a), z1))
    for i in range(lados):
        j = (i + 1) % lados
        car.append((i, j, lados + j, lados + i))
    car.append(tuple(range(lados)))
    car.append(tuple(range(lados, 2 * lados)))
    me = bpy.data.meshes.new(nombre)
    me.from_pydata(ver, [], car)
    me.update()
    o = bpy.data.objects.new(nombre, me)
    o.data.materials.append(material)
    col.objects.link(o)
    return o


def aplica():
    col = coleccion()
    hecho = {}
    madera = mat("dv_madera", (0.70, 0.56, 0.40))
    blanco = mat("dv_blanco", (0.93, 0.93, 0.92))
    negro = mat("dv_negro", (0.09, 0.09, 0.10), 0.5)
    vidrio = mat("dv_vidrio", (0.78, 0.85, 0.88), 0.15)
    verde = mat("dv_verde", (0.24, 0.45, 0.22))
    beige = mat("dv_beige", (0.80, 0.74, 0.64))
    cera = mat("dv_cera", (0.96, 0.95, 0.92))
    latón = mat("dv_laton", (0.78, 0.66, 0.38), 0.35)

    # ---------------------------------------------------------- COMEDOR
    # La mesa del modelo esta en pa_mesa_comedor_tablero; se le pone encima lo
    # que trae la real: charola negra con DOS velas y un florero con planta.
    t = bpy.data.objects.get("pa_mesa_comedor_tablero")
    if t:
        from mathutils import Vector
        b = [t.matrix_world @ Vector(v) for v in t.bound_box]
        cx = (min(v.x for v in b) + max(v.x for v in b)) / 2
        cy = (min(v.y for v in b) + max(v.y for v in b)) / 2
        zt = max(v.z for v in b)
        caja(col, "pa_comedor_charola", cx - 0.22, cx + 0.22, cy - 0.16, cy + 0.16,
             zt, zt + 0.02, negro)
        cilindro(col, "pa_comedor_vela1", cx - 0.10, cy, zt + 0.02, zt + 0.20, 0.045, cera)
        cilindro(col, "pa_comedor_vela2", cx + 0.08, cy - 0.04, zt + 0.02, zt + 0.15, 0.04, cera)
        cilindro(col, "pa_comedor_florero", cx + 0.02, cy + 0.20, zt, zt + 0.22, 0.05, vidrio)
        for i in range(5):
            cilindro(col, "pa_comedor_planta_h%d" % i, cx + 0.02 + (i - 2) * 0.04,
                     cy + 0.20 + (i % 2) * 0.03, zt + 0.20, zt + 0.36, 0.025, verde, 6)
        # la lampara de LAZO: un aro partido en segmentos, no una campana
        import math
        for i in range(14):
            a = 2 * math.pi * i / 14
            cilindro(col, "pa_comedor_lazo_%d" % i,
                     cx + 0.34 * math.cos(a), cy + 0.20 * math.sin(a),
                     zt + 1.02, zt + 1.06, 0.022, cera, 6)
        hecho["comedor"] = "charola, 2 velas, florero, planta, lazo"

        # dos cuadros grandes en el muro del fondo (x mayor)
        caja(col, "pa_comedor_cuadro1", 6.80, 6.83, cy - 0.95, cy - 0.10,
             zt + 0.35, zt + 1.35, beige)
        caja(col, "pa_comedor_cuadro2", 6.80, 6.83, cy + 0.02, cy + 0.72,
             zt + 0.30, zt + 1.15, beige)
        # jarron alto de ceramica con ramas, junto a la ventana
        cilindro(col, "pa_comedor_jarron", 1.55, cy + 1.35, 2.80, 3.35, 0.20, beige)
        for i in range(4):
            cilindro(col, "pa_comedor_rama%d" % i, 1.55 + (i - 1.5) * 0.05,
                     cy + 1.35 + (i % 2) * 0.05, 3.35, 3.95, 0.012, madera, 5)

    # ---------------------------------------------------------- COCINETA
    # CORREGIDO contra el video (t 54.5-56 s). El primer intento la puso contra
    # el muro OESTE y con ventana propia: mal. La cocineta real es en L y va
    # contra la FACHADA (y 6.7), que es donde YA EXISTE la ventana horizontal
    # `a2_vtn_pa` (x 3.29-5.80, apaisada). No hay que inventarle ventana.
    #
    #   · CONTRABARRA de madera con cubierta BLANCA a lo largo de la fachada,
    #     con la parrilla negra empotrada
    #   · GABINETES ALTOS BLANCOS encima, a los lados de la ventana
    #   · DOS REPISAS FLOTANTES de madera bajo la ventana
    #   · la ISLA que ya existe (`pa_barra_*`) se queda
    for muerto in ("vtn_pa_cocina_horiz_marco", "vtn_pa_cocina_horiz_vidrio",
                   "pa_cocina_gabinete_alto", "pa_cocina_repisa_flot"):
        v = bpy.data.objects.get(muerto)
        if v:
            bpy.data.objects.remove(v, do_unlink=True)
    PISO_PA = 2.80
    Y_FACH = 6.72                       # cara interior de la fachada
    CUB = PISO_PA + 0.90                # cubierta a 90 cm del piso
    caja(col, "pa_cocina_contrabarra", 2.90, 6.30, Y_FACH, Y_FACH + 0.62,
         PISO_PA, CUB - 0.04, madera)
    caja(col, "pa_cocina_cubierta2", 2.86, 6.34, Y_FACH - 0.03, Y_FACH + 0.66,
         CUB - 0.04, CUB, blanco)
    caja(col, "pa_cocina_parrilla", 4.35, 5.05, Y_FACH + 0.10, Y_FACH + 0.48,
         CUB, CUB + 0.015, negro)
    caja(col, "pa_cocina_gab_alto", 5.05, 6.30, Y_FACH, Y_FACH + 0.36,
         CUB + 0.62, PISO_PA + 2.62, blanco)
    caja(col, "pa_cocina_gab_alto2", 2.90, 3.35, Y_FACH, Y_FACH + 0.36,
         CUB + 0.62, PISO_PA + 2.62, blanco)
    for k, dz in enumerate((0.62, 0.94)):
        caja(col, "pa_cocina_repisa%d" % k, 3.45, 4.55, Y_FACH, Y_FACH + 0.22,
             CUB + dz, CUB + dz + 0.04, madera)
    hecho["cocineta"] = "contrabarra, cubierta blanca, parrilla, gabinetes, 2 repisas"

    # ---------------------------------------------------------- BANOS
    # CORREGIDO contra las fotos reales (bano_1_09, bano_2_10, bano_4_21):
    #   · la regadera es ABIERTA, a nivel de piso — NO lleva mampara de vidrio.
    #     El primer intento le puso una y no existe.
    #   · el muro es azulejo tipo MADERA con una CENEFA horizontal cafe oscuro
    #     a media altura
    #   · hay una VENTANA HORIZONTAL chica de dos hojas, arriba, en el muro de
    #     la regadera
    #   · mueble de madera FLOTANTE de dos cajones bajo el lavabo
    #   · espejo grande sin marco
    for muerto in ("pb_bano_mampara", "n1_bano_mampara"):
        v = bpy.data.objects.get(muerto)
        if v:
            bpy.data.objects.remove(v, do_unlink=True)
    cafe = mat("dv_cafe_cenefa", (0.29, 0.20, 0.13))
    from mathutils import Vector
    n = 0
    for pre, nlav, nreg in (("pb", "pb_lavabo_ppal", "pb_regadera_plato"),
                            ("n1", "n1_lavabo", "n1_regadera_plato")):
        lav = bpy.data.objects.get(nlav)
        reg = bpy.data.objects.get(nreg)
        if lav:
            b2 = [lav.matrix_world @ Vector(v) for v in lav.bound_box]
            lx0, lx1 = min(v.x for v in b2), max(v.x for v in b2)
            ly0, ly1 = min(v.y for v in b2), max(v.y for v in b2)
            lz = min(v.z for v in b2)
            caja(col, pre + "_bano_mueble", lx0, lx1, ly0, ly1, lz - 0.46, lz - 0.03, madera)
            caja(col, pre + "_bano_tirador", lx0 - 0.015, lx0 + 0.005, ly0 + 0.03, ly1 - 0.03,
                 lz - 0.26, lz - 0.235, negro)
            caja(col, pre + "_bano_espejo", lx0 + 0.05, lx0 + 0.08, ly0 + 0.03, ly1 - 0.03,
                 lz + 0.22, lz + 1.24, vidrio)
            n += 3
        if reg:
            b2 = [reg.matrix_world @ Vector(v) for v in reg.bound_box]
            rx0, rx1 = min(v.x for v in b2), max(v.x for v in b2)
            ry0, ry1 = min(v.y for v in b2), max(v.y for v in b2)
            rz = max(v.z for v in b2)
            cy2 = (ry0 + ry1) / 2
            caja(col, pre + "_bano_cenefa", rx1 - 0.05, rx1 - 0.02, ry0, ry1,
                 rz + 1.05, rz + 1.35, cafe)
            caja(col, pre + "_bano_vtn_marco", rx1 - 0.07, rx1 - 0.02,
                 cy2 - 0.34, cy2 + 0.34, rz + 1.62, rz + 2.02, negro)
            caja(col, pre + "_bano_vtn_vidrio", rx1 - 0.055, rx1 - 0.045,
                 cy2 - 0.30, cy2 + 0.30, rz + 1.66, rz + 1.98, vidrio)
            caja(col, pre + "_bano_regadera", rx1 - 0.34, rx1 - 0.14,
                 cy2 - 0.09, cy2 + 0.09, rz + 2.05, rz + 2.10, blanco)
            caja(col, pre + "_bano_reg_brazo", rx1 - 0.16, rx1 - 0.03,
                 cy2 - 0.02, cy2 + 0.02, rz + 2.06, rz + 2.09, blanco)
            n += 5
    hecho["banos"] = n

    # ---------------------------------------------------------- TERRAZA
    # CORREGIDO (t 61.3-61.6 s): son TRES asientos, no un sofa de 3 plazas —
    # un SILLON individual, un SOFA DE DOS PLAZAS y otro SILLON, acomodados en
    # U mirando a la mesa baja. Estructura blanca de aluminio, cojines GRISES.
    # Enfrente, la mesa baja blanca de listones. La mesa de teca y la banca ya
    # estaban en el modelo.
    for k in range(9):
        for pre in ("rg_sofa_ext_cojin", "rg_sillon_ext"):
            for suf in ("", "_base", "_resp"):
                v = bpy.data.objects.get("%s%d%s" % (pre, k, suf))
                if v:
                    bpy.data.objects.remove(v, do_unlink=True)
    for muerto in ("rg_sofa_ext_base", "rg_sofa_ext_respaldo"):
        v = bpy.data.objects.get(muerto)
        if v:
            bpy.data.objects.remove(v, do_unlink=True)
    gris = mat("dv_gris_cojin", (0.68, 0.69, 0.70))
    PISO = 2.80
    Y0, Y1 = 14.62, 15.34               # fondo, contra el pretil
    def asiento(nom, x0, x1, plazas):
        caja(col, nom + "_marco", x0, x1, Y0, Y1, PISO + 0.14, PISO + 0.20, blanco)
        for lx in (x0, x1 - 0.06):      # patas / costados
            caja(col, nom + "_pata%d" % int(lx * 100), lx, lx + 0.06, Y0, Y1,
                 PISO, PISO + 0.42, blanco)
        caja(col, nom + "_resp", x0, x1, Y1 - 0.10, Y1, PISO + 0.20, PISO + 0.62, blanco)
        an = (x1 - x0 - 0.12) / plazas
        for i in range(plazas):
            a = x0 + 0.06 + i * an
            caja(col, nom + "_coj%d" % i, a + 0.02, a + an - 0.02, Y0 + 0.06, Y1 - 0.12,
                 PISO + 0.20, PISO + 0.34, gris)
            caja(col, nom + "_cojr%d" % i, a + 0.02, a + an - 0.02, Y1 - 0.14, Y1 - 0.10,
                 PISO + 0.34, PISO + 0.60, gris)
    asiento("rg_sillon_izq", 1.55, 2.34, 1)
    asiento("rg_sofa_2p", 2.50, 3.94, 2)
    asiento("rg_sillon_der", 4.10, 4.89, 1)
    # mesa baja blanca de listones, enfrente
    for i in range(8):
        caja(col, "rg_mesa_baja_t%d" % i, 2.28 + i * 0.16, 2.40 + i * 0.16,
             13.42, 14.18, 3.14, 3.18, blanco)
    caja(col, "rg_mesa_baja_borde1", 2.24, 3.62, 13.38, 13.44, 3.10, 3.18, blanco)
    caja(col, "rg_mesa_baja_borde2", 2.24, 3.62, 14.16, 14.22, 3.10, 3.18, blanco)
    for x in (2.26, 3.54):
        for y in (13.40, 14.14):
            caja(col, "rg_mesa_baja_p_%d_%d" % (int(x * 100), int(y * 100)),
                 x, x + 0.06, y, y + 0.06, PISO, 3.14, blanco)
    hecho["terraza"] = "sillon + sofa 2 plazas + sillon, mesa baja"

    # ---------------------------------------------------- SALA DE ARRIBA
    # Subiendo la escalera: sofa rojizo, butaca de una plaza, mesa ovalada y
    # una TV sobre PANEL DE MADERA con paneles arriba y abajo. El modelo no
    # tenia NI UNA TV en toda la casa — por eso la IA la inventaba distinta
    # cada vez. El muro es el este (x 6.90) de la zona de sala.
    gris_p = mat("dv_gris_panel", (0.55, 0.52, 0.48))
    caja(col, "pa_tv_panel_medio", 6.78, 6.86, 9.75, 12.05, 3.55, 4.30, madera)
    caja(col, "pa_tv_panel_alto", 6.78, 6.86, 9.75, 12.05, 4.30, 5.15, madera)
    caja(col, "pa_tv_panel_bajo", 6.74, 6.90, 9.75, 12.05, 2.80, 3.55, madera)
    caja(col, "pa_tv_pantalla", 6.70, 6.78, 10.10, 11.70, 3.72, 4.62, negro)
    caja(col, "pa_tv_repisa", 6.62, 6.90, 9.75, 12.05, 3.50, 3.58, madera)
    cilindro(col, "pa_tv_maceta", 6.72, 10.00, 3.58, 3.75, 0.11, blanco)
    for i in range(5):
        cilindro(col, "pa_tv_planta_h%d" % i, 6.72 + (i - 2) * 0.03, 10.00,
                 3.75, 3.99, 0.022, verde, 5)
    # mesa OVALADA de centro, frente al sofa rojizo
    import math as _m
    for i in range(14):
        a2 = 2 * _m.pi * i / 14
        cilindro(col, "pa_mesa_oval_b%d" % i, 3.55 + 0.42 * _m.cos(a2),
                 10.90 + 0.28 * _m.sin(a2), 3.12, 3.18, 0.06, madera, 6)
    caja(col, "pa_mesa_oval_pie", 3.44, 3.66, 10.80, 11.00, 2.80, 3.12, madera)
    hecho["sala_arriba"] = "TV, panel de madera, planta, mesa ovalada"

    # ------------------------------------------------- ROOF: 3 MACETEROS
    # Carlos, 4 sep: «solo van 3 maceteros al frente». El modelo tenia UNA
    # jardinera corrida de 5 m (`rg_jardinera_fondo`) con 19 matas encima. La
    # foto ensena TRES maceteros de concreto SUELTOS, con separacion entre
    # ellos, y la mesita larga de madera contra el pretil.
    for viejo in ("rg_jardinera_fondo", "rg_jardinera_oeste"):
        v = bpy.data.objects.get(viejo)
        if v:
            v.hide_render = v.hide_viewport = True
    for o in bpy.data.objects:
        if o.name.startswith("rg_mata_"):
            o.hide_render = o.hide_viewport = True
    concreto = mat("dv_concreto", (0.62, 0.60, 0.57))
    PISO_RG = 2.80
    for k, x0 in enumerate((2.05, 3.45, 4.85)):
        x1 = x0 + 1.15
        caja(col, "rg_macetero%d" % k, x0, x1, 14.86, 15.34,
             PISO_RG, PISO_RG + 0.52, concreto)
        caja(col, "rg_macetero%d_tierra" % k, x0 + 0.05, x1 - 0.05, 14.91, 15.29,
             PISO_RG + 0.46, PISO_RG + 0.50, mat("dv_tierra", (0.22, 0.17, 0.13)))
        for i in range(5):
            cx = x0 + 0.16 + i * (x1 - x0 - 0.32) / 4
            cilindro(col, "rg_macetero%d_planta%d" % (k, i), cx, 15.10,
                     PISO_RG + 0.50, PISO_RG + 0.50 + 0.30 + (i % 3) * 0.08,
                     0.13, verde, 6)
    hecho["roof_maceteros"] = 3

    # ------------------------------------------------- WALK-IN CLOSET
    # La foto que mando Carlos: mueble de madera clara empotrado, con CUATRO
    # huecos abiertos arriba (dos columnas por dos filas) y OCHO CAJONES abajo
    # (dos columnas por cuatro filas), con tiradores metalicos delgados.
    # El modelo solo tenia 4 repisas y 3 cajones aplastados.
    for k in range(1, 6):
        for nom in ("pb_vestidor_repisa%d" % k, "pb_vestidor_cajon%d" % k):
            v = bpy.data.objects.get(nom)
            if v:
                v.hide_render = v.hide_viewport = True
    PISO_PB = 0.0
    X0, X1 = 6.42, 6.86                 # fondo del mueble, contra el muro este
    Y0, Y1 = 10.60, 12.80
    YM = (Y0 + Y1) / 2
    caja(col, "pb_vestidor_carcasa", X0, X1, Y0, Y1, PISO_PB, PISO_PB + 2.35, madera)
    # ocho cajones: dos columnas, cuatro filas
    for c2, (ya, yb) in enumerate(((Y0 + 0.04, YM - 0.02), (YM + 0.02, Y1 - 0.04))):
        for f in range(4):
            z = PISO_PB + 0.06 + f * 0.28
            caja(col, "pb_vest_cajon_%d_%d" % (c2, f), X0 - 0.02, X0, ya, yb,
                 z, z + 0.24, madera)
            caja(col, "pb_vest_tirador_%d_%d" % (c2, f), X0 - 0.035, X0 - 0.02,
                 (ya + yb) / 2 - 0.12, (ya + yb) / 2 + 0.12, z + 0.11, z + 0.13, blanco)
    # cuatro huecos arriba: dos columnas por dos filas
    for z in (PISO_PB + 1.22, PISO_PB + 1.80):
        caja(col, "pb_vest_repisa_%d" % int(z * 100), X0 - 0.02, X1, Y0, Y1,
             z, z + 0.04, madera)
    caja(col, "pb_vest_divisor", X0 - 0.02, X1, YM - 0.02, YM + 0.02,
         PISO_PB + 1.18, PISO_PB + 2.35, madera)
    hecho["vestidor"] = "4 huecos arriba, 8 cajones abajo"

    # ------------------------------------------------- LO QUE SEGUIA FALTANDO
    # Auditoria del 4 sep, cuarto por cuarto contra el video:
    #
    # 1. EL MEDIO BANO solo tenia `pb_medio_lavabo` y `pb_medio_wc` — dos
    #    piezas sueltas. La foto `mediobano_1_06` ensena mueble de madera
    #    flotante, espejo y una plantita. Se le habia puesto mueble a los dos
    #    banos COMPLETOS y a este no.
    # 2. `n1_recamara2` no tenia BURO, y la recamara1 si. En el video las dos
    #    lo traen (h28: buro de madera junto a la cama).
    # 3. LA BODEGA quedaba con dos piezas: se le agregan cajas en las repisas,
    #    que es lo que se ve.
    lav = bpy.data.objects.get("pb_medio_lavabo")
    if lav:
        from mathutils import Vector
        b2 = [lav.matrix_world @ Vector(v) for v in lav.bound_box]
        lx0, lx1 = min(v.x for v in b2), max(v.x for v in b2)
        ly0, ly1 = min(v.y for v in b2), max(v.y for v in b2)
        lz = min(v.z for v in b2)
        caja(col, "pb_medio_mueble", lx0, lx1, ly0, ly1, lz - 0.44, lz - 0.03, madera)
        caja(col, "pb_medio_tirador", lx0 - 0.03, lx0 - 0.015, ly0 + 0.04, ly1 - 0.04,
             lz - 0.24, lz - 0.22, blanco)
        caja(col, "pb_medio_espejo", lx0 + 0.05, lx0 + 0.08, ly0 + 0.04, ly1 - 0.04,
             lz + 0.20, lz + 1.10, vidrio)
        cilindro(col, "pb_medio_maceta", (lx0 + lx1) / 2, ly1 - 0.14,
                 lz + 0.04, lz + 0.16, 0.07, blanco)
        for i in range(4):
            cilindro(col, "pb_medio_planta%d" % i, (lx0 + lx1) / 2 + (i - 1.5) * 0.035,
                     ly1 - 0.14, lz + 0.16, lz + 0.34, 0.02, verde, 5)
        hecho["mediobano"] = "mueble, espejo, planta"

    # el buro que le faltaba a la recamara 2
    cama = bpy.data.objects.get("n1_cama_2_base")
    if cama:
        from mathutils import Vector
        b2 = [cama.matrix_world @ Vector(v) for v in cama.bound_box]
        bx1 = max(v.x for v in b2)
        by1 = max(v.y for v in b2)
        bz0 = min(v.z for v in b2)
        caja(col, "n1_buro_2", bx1 + 0.06, bx1 + 0.50, by1 - 0.46, by1 - 0.02,
             bz0, bz0 + 0.48, madera)
        caja(col, "n1_buro_2_tirador", bx1 + 0.04, bx1 + 0.07, by1 - 0.34, by1 - 0.14,
             bz0 + 0.30, bz0 + 0.32, negro)
        hecho["buro_recamara2"] = 1

    # cajas en las repisas de la bodega
    for k, (z, y0b) in enumerate(((-2.35, 6.95), (-1.85, 7.35), (-1.35, 7.05))):
        caja(col, "n1_bodega_caja%d" % k, 5.05 + (k % 2) * 0.75, 5.65 + (k % 2) * 0.75,
             y0b, y0b + 0.36, z, z + 0.28, beige)
    hecho["bodega_cajas"] = 3

    # ---------------------------------------------------------- ESCALERA
    caja(col, "pb_escalera_cuadro", 6.80, 6.83, 7.60, 8.75, 1.35, 2.35, beige)
    caja(col, "pb_escalera_lampara", 6.72, 6.80, 8.95, 9.10, 1.95, 2.05, latón)
    hecho["escalera"] = "cuadro y lampara de pared"

    bpy.context.view_layer.update()
    hecho["objetos"] = len(col.objects)
    return hecho


if __name__ == "__main__":
    print("DETALLES:", aplica())
    arg = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "nosave" not in arg:
        bpy.ops.wm.save_mainfile()
        print("guardado", bpy.data.filepath)
