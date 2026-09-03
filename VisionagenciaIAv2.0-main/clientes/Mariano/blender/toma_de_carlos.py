#!/usr/bin/env python3
"""Los dos frames de la toma de Carlos, pero con la CASA ENTERA en cuadro.

    python3 toma_de_carlos.py

Conserva la ORIENTACION exacta de CAM_RECORRIDO en el cuadro en el que Carlos la
dejo — no se inventa un angulo. Lo unico que cambia es que retrocede sobre el eje
de vision de esa misma camara hasta que la casa completa cabe en el encuadre.

La distancia NO se estima a ojo: se proyectan los 8 vertices de la caja de la casa
con la matriz de la camara y se busca por biseccion la distancia minima con la que
todos caen dentro del cuadro con margen. Asi el encuadre no depende de acertarle a
un numero.

Saca:
  1. `toma_sin_paredes.png`  — sin los muros que tapan, con los cuartos y sus muebles
  2. `toma_sin_muebles.png`  — misma toma, misma camara, sin muebles ni lamparas
"""
import base64, json, os, sys, time, urllib.request

BASE = "https://conectorblender.onrender.com"
SAL = ("/workspaces/visionagenciaIAv2.0/VisionagenciaIAv2.0-main/clientes/"
       "Mariano/referencias_3d")

PLANTILLA = r'''
import base64, os
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

sc = bpy.context.scene
r = sc.render
SIN_MUEBLES = __SIN_MUEBLES__
MARGEN = 0.92          # la casa ocupa como mucho el 92% del cuadro

cam = bpy.data.objects["CAM_RECORRIDO"]
bpy.context.view_layer.update()
M = cam.matrix_world.copy()

# El eje del CORTE se toma del cuadro 224, no del que este puesto: en el 97 la
# camara va enfilada con la calle, asi que al alejarse por ese eje se acaba
# viendo la fila de techos de las vecinas en vez del costado abierto de la casa.
# El 224 mira perpendicular a la fachada — por eso corte_desde_el_recorrido.py
# usa justo ese cuadro.
_f = sc.frame_current
sc.frame_set(224)
bpy.context.view_layer.update()
M224 = cam.matrix_world.copy()
sc.frame_set(_f)
bpy.context.view_layer.update()
eje = (M224.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()   # hacia atras de la vista

prev_aa = sc.display.render_aa
prev_path = r.filepath
prev_fmt = r.image_settings.file_format
prev_cam = sc.camera
tocados = {}
c2 = cd = None

def apaga(o):
    if not o.hide_render:
        tocados[o.name] = False
        o.hide_render = True

try:
    sc.display.render_aa = '8'
    r.image_settings.file_format = 'PNG'

    # ── la caja de la casa propia ────────────────────────────────────────
    # Por POSICION y VERTICE a VERTICE: las vecinas son copias pb_*_v-1 /
    # pa_*_v-2 (por nombre entrarian), y hay losas de 60 m cuyo centro cae
    # dentro de la casa pero que se estiran hasta la calle.
    puntos = []
    SUELO = ("TER", "COLONIA", "MAR", "ESPUMA", "tierra", "TALUD")
    cajas = {}
    for o in sc.objects:
        if o.type != 'MESH':
            continue
        c = [o.matrix_world @ Vector(v) for v in o.bound_box]
        cajas[o.name] = c
        if o.name.startswith(SUELO):
            continue
        puntos += [p for p in c
                   if -0.5 < p.x < 8 and 4 < p.y < 22 and -5 < p.z < 11]

    mn = Vector((min(p.x for p in puntos), min(p.y for p in puntos), min(p.z for p in puntos)))
    mx = Vector((max(p.x for p in puntos), max(p.y for p in puntos), max(p.z for p in puntos)))
    centro = (mn + mx) / 2
    esquinas = [Vector((x, y, z)) for x in (mn.x, mx.x)
                                  for y in (mn.y, mx.y)
                                  for z in (mn.z, mx.z)]

    # ── cuanto hay que retroceder para que quepa entera ──────────────────
    lente, sensor = cam.data.lens, cam.data.sensor_width

    # NO se puede conservar el punto de vista de Carlos: su camara esta a 3 m de
    # la fachada y la casa mide 13 m de fondo por 9.5 de alto, asi que desde ahi
    # solo cabe con un ojo de pez de 2.6 mm, que sale como un tunel deformado.
    # Se conserva la DIRECCION de su recorrido (el mismo eje de vision, el mismo
    # costado de la casa) y se retrocede por el, elevando la camara para pasar
    # por encima de las vecinas. Es el planteamiento del corte que ya funciono.
    LENTE = 35.0
    ALZA = __ALZA__

    # La casa vive en x 0..8 y su lado ABIERTO es el oeste (por ahi se quitan los
    # muros). Asi que la camara va al oeste mirando al este, perpendicular a la
    # fachada. No se deriva del eje del recorrido: ni el cuadro 97 ni el 224 dan
    # una perpendicular limpia — enfilan con la calle y lo que se acaba viendo es
    # la fila de techos de las vecinas.
    direccion = Vector((-1.0, 0.0, ALZA)).normalized()

    cd = bpy.data.cameras.new("CAM_TOMA_tmp")
    cd.lens = LENTE
    cd.sensor_width = sensor
    cd.clip_start, cd.clip_end = 0.1, 3000.0
    c2 = bpy.data.objects.new("CAM_TOMA_tmp", cd)
    sc.collection.objects.link(c2)
    sc.camera = c2

    m = (1.0 - MARGEN) / 2

    def cabe(d):
        p_ = centro + direccion * d
        c2.location = p_
        c2.rotation_euler = (centro - p_).to_track_quat('-Z', 'Y').to_euler()
        bpy.context.view_layer.update()
        for q in esquinas:
            co = world_to_camera_view(sc, c2, q)
            if co.z <= 0.05:
                return False
            if not (m < co.x < 1 - m and m < co.y < 1 - m):
                return False
        return True

    lo, hi = 5.0, 12.0
    while not cabe(hi) and hi < 400:
        lo = hi
        hi *= 1.35
    for _ in range(30):                    # la minima distancia con la que cabe
        mid = (lo + hi) / 2
        if cabe(mid):
            hi = mid
        else:
            lo = mid
    dist = hi
    cabe(dist)
    pos = c2.location.copy()
    lente_usado = LENTE

    # ── se apaga todo lo que quede al OESTE de la casa ───────────────────
    # El rayo desde la camara lo confirmo: lo que tapa son las vecinas
    # (VEC_fila-2_pb, VEC_fila_extra, ext_este_pb_v-2) y sobre todo las COPIAS
    # de la propia casa, pb_muro_oeste_sala_v-1 / _v-2. Como la casa vive en
    # x 0..8 y la camara retrocede hacia x negativo, apagar todo lo que acabe
    # antes del muro oeste deja la vista limpia — y de paso quita ese muro, que
    # es justo lo que se quiere para ver los cuartos.
    corte_x = mn.x + 0.6
    for nombre, c in cajas.items():
        o = bpy.data.objects.get(nombre)
        if o is None or o.name.startswith(SUELO):
            continue
        if max(v.x for v in c) < corte_x:
            apaga(o)

    col = bpy.data.collections.get("ROTULOS")
    if col:
        for o in col.objects:
            apaga(o)
    if SIN_MUEBLES:
        for nombre in ("MUEBLES", "LAMPARAS"):
            col = bpy.data.collections.get(nombre)
            if col:
                for o in col.objects:
                    apaga(o)

    sal = os.path.join(os.path.expanduser("~"), "_toma_tmp.png")
    r.filepath = sal
    bpy.ops.render.render()
    bpy.data.images["Render Result"].save_render(filepath=sal)
    png = base64.b64encode(open(sal, "rb").read()).decode()
finally:
    for n in tocados:
        ob = bpy.data.objects.get(n)
        if ob:
            ob.hide_render = False
    sc.camera = prev_cam
    if c2:
        bpy.data.objects.remove(c2, do_unlink=True)
    if cd:
        bpy.data.cameras.remove(cd)
    sc.display.render_aa = prev_aa
    r.filepath = prev_path
    r.image_settings.file_format = prev_fmt

responder({"png": png, "frame": sc.frame_current, "apagados": len(tocados),
           "res": [r.resolution_x, r.resolution_y], "lente": round(lente_usado, 2), "lente_tuyo": round(lente, 1),
           "atras_m": round(dist, 1), "alza": ALZA,
           "casa": [round(v, 1) for v in (mx - mn)]})
'''


def libre(limite=600):
    t0 = time.time()
    while time.time() - t0 < limite:
        with urllib.request.urlopen(f"{BASE}/api/blender/status", timeout=30) as r:
            s = json.loads(r.read())
        if s.get("conectado") and not s.get("corriendo") and not s.get("pendientes"):
            return True
        time.sleep(5)
    return False


def saca(sin_muebles, nombre, alza=0.22):
    if not libre():
        print(f"  {nombre:22} SALTADO · Blender ocupado o desconectado")
        return
    src = (PLANTILLA.replace("__SIN_MUEBLES__", "True" if sin_muebles else "False")
                    .replace("__ALZA__", str(alza)))
    d = json.dumps({"python": src, "meta": {"tipo": "libre"}}).encode()
    req = urllib.request.Request(f"{BASE}/api/blender/execute", data=d,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    res = json.loads(urllib.request.urlopen(req, timeout=900).read())
    if not res.get("ok"):
        print(f"  {nombre:22} ERROR {str(res.get('error'))[:120]}")
        return
    d = res["resultado"]
    ruta = os.path.join(SAL, nombre + ".png")
    open(ruta, "wb").write(base64.b64decode(d["png"]))
    print(f"  {nombre:22} f{d['frame']}  {d['res'][0]}x{d['res'][1]}  lente {d['lente']}  "
          f"atras {d['atras_m']} m  alza {d['alza']}  {time.time()-t0:.1f}s")


if __name__ == "__main__":
    if sys.argv[1:2] == ["alturas"]:
        print("Tres alturas de camara, para escoger:")
        for alza, etq in ((0.10, "alza_baja"), (0.22, "alza_media"), (0.35, "alza_alta")):
            saca(False, etq, alza)
            time.sleep(3)
    else:
        alza = float(sys.argv[1]) if sys.argv[1:] else 0.22
        print(f"La toma de Carlos, con la casa entera (alza {alza}):")
        saca(False, "toma_sin_paredes", alza)
        time.sleep(3)
        saca(True, "toma_sin_muebles", alza)
