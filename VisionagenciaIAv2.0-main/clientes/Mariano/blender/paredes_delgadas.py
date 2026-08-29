"""Paredes finas, para que dejen de leerse como bloques.

Los muros ya median 15 cm y las divisiones 10, que es lo que miden de verdad.
El problema no es que esten mal: es que Workbench sombrea plano y el CANTO de
un muro agarra un tono distinto a su cara, asi que cada pared se ve como un
tabique de canto grueso. En una maqueta que se mira en seccion —que es lo que
es este recorrido— las paredes se leen mejor finas, como carton.

Se adelgaza la MALLA, no el objeto: escalar el objeto depende de donde este su
origen (varios muros lo tienen en una esquina y se moverian). Y se escala
respecto al centro geometrico de la caja, asi que el muro se queda donde estaba
y solo pierde grosor por sus dos caras por igual.

Cada objeto guarda su espesor anterior en una propiedad, asi que
`engordar()` lo devuelve exactamente a como estaba.

    adelgazar()              muros y divisiones a 7 cm, losas a 10
    adelgazar(dry=True)      solo dice que tocaria
    engordar()               lo deja como estaba
"""
import bpy
from mathutils import Vector

PREV = "espesor_previo"

# que se adelgaza y a cuanto (metros)
MUROS = 0.07
LOSAS = 0.10
CLAVES_MURO = ("muro", "_div_", "pretil", "barda", "bardita", "faldon", "antepecho")
CLAVES_LOSA = ("_piso", "losa", "plafon", "balcon")
# lo que NUNCA se toca aunque el nombre despiste
# `contencion` y `talud` se quedan gordos a proposito: no son paredes de la
# casa, aguantan terreno, y al afinarlos asoma el relleno por detras.
SALTAR = ("cama", "closet", "tapete", "mesa", "cabecera", "ESPUMA", "MAR",
          "TER_", "COLONIA", "VEC_", "AP_", "contencion", "talud")


def _eje_corto(ob):
    d = list(ob.dimensions)
    i = d.index(min(d))
    return i, d[i]


def _cuales():
    fuera = []
    for ob in bpy.context.view_layer.objects:
        if ob.type != 'MESH' or any(k in ob.name for k in SALTAR):
            continue
        bajo = ob.name.lower()
        es_muro = any(k in bajo for k in CLAVES_MURO)
        es_losa = any(k in bajo for k in CLAVES_LOSA)
        if not (es_muro or es_losa):
            continue
        i, esp = _eje_corto(ob)
        objetivo = MUROS if es_muro else LOSAS
        if esp <= objetivo + 0.005 or esp > 0.60:
            continue          # ya es fino, o es un volumen (no una pared)
        fuera.append((ob, i, esp, objetivo))
    return fuera


def adelgazar(dry=False):
    tocados, saltados = [], 0
    mallas = set()
    for ob, i, esp, objetivo in _cuales():
        if ob.data.name in mallas:
            saltados += 1     # malla compartida: ya se adelgazo con su gemelo
            continue
        tocados.append({"obj": ob.name, "de": round(esp, 3), "a": objetivo})
        if dry:
            continue
        mallas.add(ob.data.name)
        if PREV not in ob.data:
            ob.data[PREV] = esp
        f = objetivo / esp
        me = ob.data
        centro = sum((Vector(c) for c in ob.bound_box), Vector()) / 8.0
        for v in me.vertices:
            v.co[i] = centro[i] + (v.co[i] - centro[i]) * f
        me.update()
    return {"paredes": len(tocados), "mallas_compartidas_saltadas": saltados,
            "detalle": tocados[:14]}


def engordar():
    vueltos = []
    for ob in bpy.context.view_layer.objects:
        if ob.type != 'MESH' or PREV not in ob.data:
            continue
        i, esp = _eje_corto(ob)
        if esp < 1e-6:
            continue
        f = ob.data[PREV] / esp
        centro = sum((Vector(c) for c in ob.bound_box), Vector()) / 8.0
        for v in ob.data.vertices:
            v.co[i] = centro[i] + (v.co[i] - centro[i]) * f
        ob.data.update()
        del ob.data[PREV]
        vueltos.append(ob.name)
    return {"devueltos": len(vueltos)}
