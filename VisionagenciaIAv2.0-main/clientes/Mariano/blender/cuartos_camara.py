"""Un cuadro por CUARTO, con la camara DENTRO del cuarto — y en dos pases.

    blender -b catania_LIGERA.blend -P cuartos_camara.py -- <cuarto> <salida.png> \
            [ancho] [alto] [pase]

    pase: "gris"   (Workbench solido: pone la luz y el volumen)
          "blanco" (todo blanco y plano, solo geometria) — de este sale el
                   plano de LINEAS por fuera, con un Sobel en ffmpeg, que es
                   lo que amarra la estructura. Ver `_tanda_cuartos.sh`.

POR QUE EXISTE. Los 21 keyframes de `CAM_RECORRIDO` NO son los 16 cuartos:
esa camara vive siempre en el mismo sitio (x ~ -3, mirando al este) y solo se
desliza en Y y cambia de nivel. Mira la casa EN SECCION DESDE FUERA, asi que en
cada punto le caen tres o cuatro cuartos en el cuadro. Por eso al sacar "cuartos"
del recorrido salian repetidos — 02/03/05/06 eran el mismo recibidor. Ningun
frame del recorrido aisla un cuarto. La unica forma es meter la camara dentro.

LOS DOS PASES, y por que dos. A la IA se le dan las DOS imagenes del mismo
cuadro. El gris solo no basta: con un render plano se despega de la estructura e
inventa muros. El plano de lineas es del MISMO encuadre, y es lo que la
obliga a respetar donde va cada pared, cada ventana y cada mueble.

El de lineas NO sale de Blender: sale de pasarle un Sobel al pase blanco. Se
intento con `shading.type = 'WIREFRAME'` y NO SIRVE — es una opcion del VISOR y
el motor Workbench al renderizar se la salta en silencio; salio un solido con
materiales, con la cama cafe y la pared verde, ni una linea. El pase blanco
(plano, sin sombras, con cavidad y contorno) es ademas la entrada perfecta para
el Sobel: pura geometria, cero ruido de textura. Y por venir del mismo render,
cuadra pixel a pixel con el gris sin tener que alinear nada.

EL CUADRO ES EL 1021, no el 1. La escena tiene 584 objetos animados: los muebles
BROTAN del piso a lo largo del recorrido. En el cuadro 1 la cama del n1 esta a
z -2.69 (hundida en el piso) y en el 1021 a -2.29, que es su sitio. Sacar los
cuartos del cuadro 1 da cuartos a medio amueblar.
"""
import os
import sys

import bpy
from mathutils import Vector

CUADRO = 1021          # todo ya brotado; ver el docstring
CLIP_CERCA = 0.01      # la camara va pegada a un rincon: el 0.1 de fabrica recorta

# cuarto -> (posicion de la camara, a donde mira, lente en mm, que es)
#
# Los numeros salen de los muros del propio archivo, no de ojo:
#   n1  piso z -2.75  techo -0.20     ojo a -1.35
#   pb  piso z -0.05  techo  2.60     ojo a  1.52
#   pa  piso z  2.80  techo  5.60     ojo a  4.35
# y en planta la casa va de x 1.10 a 6.90 y de y 6.67 a 15.52. Las divisiones
# (`div_*`) y los `muro_*` son los que parten cada nivel en cuartos.
CUARTOS = {
    # --- nivel -1 ---------------------------------------------------------
    "n1_recamara2":   ((4.30,  9.90, -1.35), (2.30,  7.60,  -1.68), 18,
                       "the front secondary bedroom, floor-to-ceiling sliding window"),
    "n1_bano":        ((4.45, 11.85, -1.40), (1.80, 10.90,  -1.63), 16,
                       "the lower bathroom, with shower, washbasin and WC"),
    "n1_recamara1":   ((4.35, 12.35, -1.35), (2.40, 14.60,  -1.68), 18,
                       "the back secondary bedroom"),
    "n1_bodega":      ((6.70,  9.95, -1.35), (5.60,  7.40,  -1.58), 18,
                       "the storage room on the lower floor"),
    "n1_estudio":     ((5.10, 10.55, -1.35), (6.30, 12.30,  -1.58), 18,
                       "the study, with the desk, the monitor, the bookshelf and a plant"),
    "n1_lavado":      ((6.70, 13.50, -1.35), (5.30, 15.00,  -1.63), 16,
                       "the laundry room, with washer and dryer"),
    # --- planta baja ------------------------------------------------------
    "pb_sala":        ((4.45, 10.05,  1.52), (2.20,  7.40,   1.12), 18,
                       "the ground-floor living room, with the camel leather armchair "
                       "and the square travertine coffee table"),
    "pb_mediobano":   ((4.45, 11.85,  1.50), (1.80, 10.80,   1.17), 16,
                       "the guest half-bath, washbasin and WC only"),
    "pb_recamara_ppal": ((4.40, 12.40, 1.52), (2.60, 14.60,   1.12), 18,
                       "the master bedroom, with the beige upholstered headboard and the "
                       "chocolate throw at the foot of the bed"),
    "pb_escalera":    ((6.70,  6.90,  1.52), (5.60,  9.60,   1.02), 18,
                       "the wooden staircase going up between floors"),
    "pb_vestidor":    ((5.05, 10.55,  1.50), (6.40, 12.40,   1.22), 16,
                       "the walk-in closet in pale oak, open shelves and drawers"),
    "pb_bano_ppal":   ((6.70, 13.50,  1.50), (5.30, 14.90,   1.22), 16,
                       "the master bathroom"),
    # --- planta alta (una sola pieza; tres tomas) --------------------------
    "pa_cocina":      ((5.80,  8.20,  4.35), (1.60, 10.50,   3.97), 20,
                       "the kitchen along the far wall, taupe cabinets, stone countertop "
                       "and the window over the sink"),
    "pa_sala":        ((6.60,  7.10,  4.35), (3.20, 10.40,   3.92), 20,
                       "the upper living room, with the sofa and the low coffee table"),
    "pa_comedor":     ((2.20,  7.30,  4.35), (5.60, 10.40,   3.97), 20,
                       "the dining area, with the table and six chairs"),
    # --- azotea -----------------------------------------------------------
    "rg_terraza":     ((6.40, 12.70,  4.40), (3.30, 14.60,   3.72), 20,
                       "the roof terrace: BARE, pale floor tile, low white parapet and one "
                       "teak table with chairs, no planters"),
}


def limpia():
    """Esconde lo que estorba: los muros clonados, los vecinos de mentira y las
    jardineras del roof garden.

    Los `*_fantasma` son copias del mismo muro en el mismo sitio, para el efecto
    de desvanecido del recorrido. Vistas desde dentro no aportan nada y pelean
    por el mismo pixel. Las `rg_jardinera_*` son cilindros verdes que la casa
    REAL no tiene: si se dejan, la IA los copia como macetas.
    """
    fuera = 0
    for o in bpy.data.objects:
        n = o.name
        if n.endswith("_fantasma") or n.startswith("rg_jardinera"):
            o.hide_render = o.hide_viewport = True
            fuera += 1
    for c in ("FANTASMAS", "CEBOLLA_muros", "ROTULOS"):
        col = bpy.data.collections.get(c)
        if col:
            for o in col.objects:
                o.hide_render = o.hide_viewport = True
                fuera += 1
    return fuera


def pon_camara(pos, mira, lente):
    cam = bpy.data.objects.get("CAM_CUARTO")
    if cam is None:
        cam = bpy.data.objects.new("CAM_CUARTO", bpy.data.cameras.new("CAM_CUARTO"))
        bpy.context.scene.collection.objects.link(cam)
    cam.location = Vector(pos)
    cam.data.lens = lente
    cam.data.clip_start = CLIP_CERCA
    # apuntar: -Z de la camara hacia el objetivo, +Y arriba
    cam.rotation_euler = (Vector(mira) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = cam
    return cam


def modo(pase):
    """El pase gris y el pase de aristas salen del MISMO Workbench y de la misma
    camara. Cambia solo el sombreado, asi que los dos cuadran pixel a pixel —
    que es justo lo que hace que el de lineas sirva de amarre."""
    d = bpy.context.scene.display.shading
    w = bpy.context.scene.world
    if pase == "blanco":
        # OJO: `type = 'WIREFRAME'` NO SIRVE aqui. Es una opcion del VISOR; el
        # motor Workbench al renderizar (F12) solo dibuja SOLID y se la salta
        # en silencio — el primer intento salio como un solido con materiales,
        # con la cama cafe y la pared verde, ni una linea.
        # Lo que si respeta el render es el CONTORNO de objeto y la CAVIDAD.
        # Con todo blanco y plano, el contorno da la silueta de cada pieza y la
        # cavidad saca las aristas de dentro: sale un plano de lineas.
        d.type = 'SOLID'
        d.light = 'FLAT'
        d.color_type = 'SINGLE'
        d.single_color = (1.0, 1.0, 1.0)
        d.show_shadows = False
        d.show_specular_highlight = False
        d.show_cavity = True
        d.cavity_type = 'BOTH'
        d.curvature_ridge_factor = 2.0
        d.curvature_valley_factor = 2.0
        d.cavity_ridge_factor = 2.5
        d.cavity_valley_factor = 2.5
        d.show_object_outline = True
        d.object_outline_color = (0.0, 0.0, 0.0)
        d.background_type = 'VIEWPORT'
        d.background_color = (1.0, 1.0, 1.0)
    else:
        d.type = 'SOLID'
        d.light = 'STUDIO'
        d.color_type = 'SINGLE'
        d.single_color = (0.62, 0.62, 0.62)
        d.show_shadows = True
        d.show_cavity = True
        d.cavity_type = 'BOTH'
        d.show_specular_highlight = False
        d.show_object_outline = False
        d.background_type = 'VIEWPORT'
        d.background_color = (0.82, 0.86, 0.92)
    if w:
        w.use_nodes = False


# --- de aqui para abajo, solo cuando se corre como guion suelto ------------
# `corte_mascaras.py` IMPORTA este archivo para reusar CUARTOS y limpia().
# Sin este guard, importarlo disparaba un render. Blender corre los -P como
# __main__, asi que `_tanda_cuartos.sh` no cambia.
if __name__ == "__main__":
    arg = sys.argv[sys.argv.index("--") + 1:]
    cuarto = arg[0]
    salida = arg[1]
    ancho = int(arg[2]) if len(arg) > 2 else 810
    alto = int(arg[3]) if len(arg) > 3 else 1440
    pase = arg[4] if len(arg) > 4 else "gris"

    if cuarto not in CUARTOS:
        raise SystemExit("cuarto desconocido: %s\nhay: %s" % (cuarto, ", ".join(CUARTOS)))
    pos, mira, lente, _que = CUARTOS[cuarto]

    sc = bpy.context.scene
    sc.frame_set(CUADRO)
    bpy.context.view_layer.update()
    n = limpia()
    pon_camara(pos, mira, lente)
    modo(pase)

    r = sc.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = ancho, alto, 100
    r.image_settings.file_format = 'PNG'
    r.film_transparent = False
    r.filepath = salida
    sc.display.render_aa = '8'

    os.makedirs(os.path.dirname(os.path.abspath(salida)), exist_ok=True)
    bpy.ops.render.render()
    bpy.data.images["Render Result"].save_render(filepath=salida)
    print("OK %s %s f%d %dx%d (%d escondidos)" % (cuarto, pase, CUADRO, ancho, alto, n))
