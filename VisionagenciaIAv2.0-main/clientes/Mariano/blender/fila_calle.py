"""Las casas que faltaban en la propia calle Catania.

La escena tenia vecinas hasta la +2/-2 (X de -12.9 a 20.9) y luego un hueco de
~15 m hasta donde arranca la colonia de relleno. Aqui se sigue la fila para los
dos lados —y la de enfrente— con el mismo despiece y el mismo paso de 7 m que
usan las vecinas que ya estaban:

    cuerpo de la unidad k  ->  X de 7k+1.1 a 7k+6.9

Todo en UNA malla por lado (cajas de 8 verts), asi que el visor no carga con
cientos de objetos nuevos. Tambien se alarga la franja de losetas con pasto del
frente, que se acababa en X +-24.5.

    aplicar()     construye
    deshacer()    borra lo que agrego
"""
import bpy

PASO = 7.0
NUEVAS = [k for k in range(-8, 9) if abs(k) >= 3]      # las +-1 y +-2 ya existen
COL = "VECINAS"
BLANCO = (0.900, 0.892, 0.868, 1.0)

# La calle va en bajada: 16 m de desnivel entre las puntas de la fila. Alturas
# reales (SRTM) sobre el eje del lote, ya pasadas a Z de escena.
PERFIL = {-300: 1.65, -275: 2.65, -250: 5.65, -225: 7.65, -200: 9.65, -175: 10.65, -150: 11.65, -125: 10.65, -100: 8.65, -75: 6.65, -50: 4.65, -25: 1.65, 0: -0.35, 25: -2.35, 50: -4.35, 75: -4.35, 100: -4.35, 125: -4.35, 150: -4.35, 175: -3.35, 200: -3.35, 225: -3.35, 250: -3.35, 275: -3.35, 300: -2.35}
MEZCLA = (21.0, 35.0)    # el escalon entra poco a poco, no en el borde del lote


def _mat(nombre, color, rough=0.85):
    m = bpy.data.materials.get(nombre)
    if m is None:
        m = bpy.data.materials.new(nombre); m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    if not b.inputs["Base Color"].links:
        b.inputs["Base Color"].default_value = color
        b.inputs["Roughness"].default_value = rough
    m.diffuse_color = color
    return m


def suelo(x):
    """Altura del terreno real en ese punto de la calle, suavizada cerca del
    lote para que no salga un escalon donde acaba el terreno modelado a mano."""
    xs = sorted(PERFIL)
    x = min(max(x, xs[0]), xs[-1])
    i = max(k for k in range(len(xs)) if xs[k] <= x)
    j = min(i + 1, len(xs) - 1)
    t = 0.0 if xs[j] == xs[i] else (x - xs[i]) / float(xs[j] - xs[i])
    z = PERFIL[xs[i]] * (1 - t) + PERFIL[xs[j]] * t
    a, b = MEZCLA
    k = 0.0 if abs(x) <= a else min(1.0, (abs(x) - a) / (b - a))
    return z * k


def _caja(v, c, x0, y0, z0, x1, y1, z1):
    b = len(v)
    v += [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
          (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    c += [(b, b+1, b+2, b+3), (b+4, b+5, b+6, b+7), (b, b+1, b+5, b+4),
          (b+1, b+2, b+6, b+5), (b+2, b+3, b+7, b+6), (b+3, b, b+4, b+7)]


def _objeto(nombre, verts, caras, mat, coleccion):
    ant = bpy.data.objects.get(nombre)
    if ant:
        me = ant.data
        bpy.data.objects.remove(ant, do_unlink=True)
        if me.users == 0:
            bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(nombre)
    me.from_pydata(verts, [], caras)
    me.update()
    ob = bpy.data.objects.new(nombre, me)
    bpy.context.scene.collection.objects.link(ob)
    col = bpy.data.collections.get(coleccion)
    if col:
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        col.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


def fila():
    """Mi lado de la calle: el mismo despiece que VEC_fila-1."""
    v, c = [], []
    for k in NUEVAS:
        x0, x1 = PASO * k + 1.1, PASO * k + 6.9
        dz = suelo((x0 + x1) / 2)                          # la fila escalona
        _caja(v, c, x0, 6.67, -2.9 + dz, x1, 15.52, -0.2 + dz)   # nivel -1
        _caja(v, c, x0, 6.67, -0.2 + dz, x1, 15.52, 2.8 + dz)   # planta baja
        _caja(v, c, x0, 6.67, 2.8 + dz, x1, 12.47, 5.4 + dz)    # planta alta
        _caja(v, c, x0, 6.67, 5.4 + dz, x1, 12.47, 5.6 + dz)    # pretil
        _caja(v, c, x0, 12.47, 2.6 + dz, x1, 15.52, 2.8 + dz)   # losa del roof
        _caja(v, c, x0, 12.47, 2.8 + dz, x0 + 0.15, 15.52, 3.9 + dz)
        _caja(v, c, x1 - 0.15, 12.47, 2.8 + dz, x1, 15.52, 3.9 + dz)
        _caja(v, c, x0, 12.47, 2.8 + dz, x1, 12.62, 3.9 + dz)
        _caja(v, c, x0, 15.37, 2.8 + dz, x1, 15.52, 3.9 + dz)
        _caja(v, c, x0 - 1.1, 18.85, -2.85 + dz, x1 + 0.1, 19.0, -1.35 + dz)  # barda
        # las aletas blancas del frente, como en la foto
        _caja(v, c, x0 - 1.07, 6.52, -0.1 + dz, x0 - 0.12, 6.67, 0.9 + dz)
    return _objeto("VEC_fila_extra", v, c, _mat("VEC_muro", BLANCO), COL), len(NUEVAS)


def enfrente():
    """La acera de enfrente: cuerpo simple, como VEC_enfrente+0."""
    v, c = [], []
    for k in NUEVAS:
        x0, x1 = PASO * k + 1.1, PASO * k + 6.9
        dz = suelo((x0 + x1) / 2)
        _caja(v, c, x0, -24.52, -0.2 + dz, x1, -15.67, 5.6 + dz)
        _caja(v, c, x0, -24.52, 5.6 + dz, x1, -15.67, 5.8 + dz)
    return _objeto("VEC_enfrente_extra", v, c,
                   _mat("VEC_enfrente_extra", (0.870, 0.862, 0.840, 1.0)), COL), len(NUEVAS)


def frente():
    """Sigue la franja de losetas con pasto mas alla de X +-24.5."""
    v, c = [], []                      # el pasto, tramo por tramo, en bajada
    x = -62.0
    while x < 62.0:
        if abs(x) > 24.0:
            dz = suelo(x + 0.75)
            _caja(v, c, x, 0.0, -0.24 + dz, x + 1.5, 6.67, -0.14 + dz)
        x += 1.5
    pasto = _objeto("frente_pasto_extra", v, c,
                    _mat("frente_pasto", (0.205, 0.445, 0.145, 1.0), 0.92), "TERRENO")
    v, c = [], []                      # y las losetas encima
    x = -62.0
    while x < 62.0:
        if abs(x) > 24.0:
            dz = suelo(x + 0.47)
            _caja(v, c, x, 0.0, -0.2 + dz, x + 0.95, 6.67, -0.1 + dz)
        x += 1.5
    losa = _objeto("frente_losa_extra", v, c,
                   _mat("frente_loseta", (0.720, 0.710, 0.685, 1.0), 0.65), "TERRENO")
    return losa, pasto


def deshacer():
    n = 0
    for nom in ("VEC_fila_extra", "VEC_enfrente_extra", "frente_losa_extra",
                "frente_pasto_extra"):
        ob = bpy.data.objects.get(nom)
        if ob:
            me = ob.data
            bpy.data.objects.remove(ob, do_unlink=True)
            if me.users == 0:
                bpy.data.meshes.remove(me)
            n += 1
    return n


def aplicar():
    of, nf = fila()
    oe, ne = enfrente()
    ol, op = frente()
    tris = lambda o: sum(len(p.vertices) - 2 for p in o.data.polygons)
    return {"unidades_mi_lado": nf, "unidades_enfrente": ne,
            "desde_hasta_X": [round(PASO * NUEVAS[0] + 1.1, 1), round(PASO * NUEVAS[-1] + 6.9, 1)],
            "escalon_m": [round(suelo(PASO * NUEVAS[0] + 4), 1), round(suelo(PASO * NUEVAS[-1] + 4), 1)],
            "tris": {"fila": tris(of), "enfrente": tris(oe), "losetas": tris(ol), "pasto": tris(op)}}
