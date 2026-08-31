"""Una foto del sello 9511 desde el Blender de Carlos. UN cuadro por trabajo.

    python3 bench-blender/foto_sello_9511.py 100 _vistas/sello_f100.png

Por que un cuadro por trabajo: mandar una tanda de renders por el puente ya
tumbo Blender una vez. Si hacen falta tres vistas, son tres corridas.

Por que no `write_still=True`: por el puente ese flag no deja el archivo en
disco y el `open()` de despues truena, asi que el conector reintenta y salen
tres renders. Lo que si funciona es render() y luego save_render().
"""

import base64
import json
import os
import sys
import urllib.request

CONECTOR = os.environ.get("BLENDER_CONECTOR", "https://conectorblender.onrender.com")
AQUI = os.path.dirname(os.path.abspath(__file__))

# Encuadres pensados para lo que cada cuadro tiene que contar
VISTAS = {
    1:   dict(cam=(0.085, -0.16, 0.085), mira=(0.0, 0.0, 0.012), lente=52.0),
    50:  dict(cam=(-0.045, -0.115, 0.20), mira=(-0.048, 0.0, 0.012), lente=42.0),
    100: dict(cam=(0.12, -0.30, 0.185), mira=(0.045, 0.0, 0.006), lente=40.0),
}

GUION = r'''
import os
import bpy
from mathutils import Vector

def _foto():
    esc = bpy.context.scene
    col = bpy.data.collections.get("SELLO_9511")
    if not col:
        return {"error": "no existe la coleccion SELLO_9511"}

    prev = {"cam": esc.camera, "motor": esc.render.engine, "fr": esc.frame_current,
            "rx": esc.render.resolution_x, "ry": esc.render.resolution_y,
            "pct": esc.render.resolution_percentage,
            "ft": esc.render.image_settings.file_format}

    cd = bpy.data.cameras.get("CAM_SELLO") or bpy.data.cameras.new("CAM_SELLO")
    cam = bpy.data.objects.get("CAM_SELLO")
    if not cam:
        cam = bpy.data.objects.new("CAM_SELLO", cd)
        col.objects.link(cam)
    cam.data = cd
    cam.location = Vector(%(cam)r)
    cam.rotation_euler = (Vector(%(mira)r) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cd.lens = %(lente)r

    esc.camera = cam
    esc.render.engine = 'BLENDER_WORKBENCH'
    esc.display.shading.color_type = 'MATERIAL'
    esc.display.shading.light = 'STUDIO'
    esc.display.shading.show_shadows = True
    esc.display.shading.show_cavity = True
    esc.render.film_transparent = False
    esc.render.resolution_x, esc.render.resolution_y = 1200, 700
    esc.render.resolution_percentage = 100
    esc.render.image_settings.file_format = 'PNG'
    esc.frame_set(%(cuadro)d)
    bpy.context.view_layer.update()

    bpy.ops.render.render()
    salida = os.path.join(bpy.app.tempdir, "sello_9511_f%(cuadro)d.png")
    bpy.data.images["Render Result"].save_render(filepath=salida)

    esc.camera = prev["cam"]
    esc.render.engine = prev["motor"]
    esc.render.resolution_x, esc.render.resolution_y = prev["rx"], prev["ry"]
    esc.render.resolution_percentage = prev["pct"]
    esc.render.image_settings.file_format = prev["ft"]
    esc.frame_set(prev["fr"])

    import base64 as b64
    with open(salida, "rb") as f:
        return {"png_b64": b64.b64encode(f.read()).decode(), "cuadro": %(cuadro)d}

responder(_foto())
'''


def foto(cuadro, destino, timeout=780):
    v = VISTAS.get(cuadro, VISTAS[100])
    codigo = GUION % {"cam": v["cam"], "mira": v["mira"], "lente": v["lente"],
                      "cuadro": cuadro}
    datos = json.dumps({"python": codigo,
                        "meta": {"tipo": "render", "invento": "sello_trodat_9511"}}).encode()
    req = urllib.request.Request(CONECTOR + "/api/blender/execute", data=datos,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        res = (json.load(r) or {}).get("resultado") or {}
    if not res.get("png_b64"):
        return {"error": res or "sin imagen"}
    ruta = destino if os.path.isabs(destino) else os.path.join(AQUI, destino)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "wb") as f:
        f.write(base64.b64decode(res["png_b64"]))
    return {"archivo": ruta, "bytes": os.path.getsize(ruta), "cuadro": cuadro}


if __name__ == "__main__":
    cuadro = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    destino = sys.argv[2] if len(sys.argv) > 2 else "_vistas/sello_9511_f%d.png" % cuadro
    print(json.dumps(foto(cuadro, destino), ensure_ascii=False))
