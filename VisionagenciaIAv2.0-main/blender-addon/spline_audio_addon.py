bl_info = {
    "name": "Spline por Audio",
    "author": "Seedance Studio",
    "version": (1, 2, 0),
    "blender": (3, 0, 0),
    "location": "Vista 3D > barra lateral (N) > Seedance > Spline por Audio",
    "description": "Recorrido de camara (spline) sincronizado a audio: posicion, mira, zoom, catalogo de movimientos y rodeos (orbit).",
    "category": "Animation",
}

# Complementa a seedance_blender.py: aquel jala ORDENES del backend, este da
# control LOCAL sobre el recorrido de camara — el mismo tipo de curva que
# arma pyRecorridoLateral()/pyRecorridoAudio() en blender-connector.js, pero
# aqui con tantos puntos como haga falta y cada uno con su propio instante de
# audio, altura, zoom, hacia donde mira y que tan brusco llega, para que el
# vuelo siga lo que la voz va diciendo.
#
# v1.1 — CAMBIO IMPORTANTE: antes la camara rotaba siguiendo la tangente de
# la curva (Follow Path con use_curve_follow=True). Eso es lo que hacia que
# al bajar de piso la camara apuntara hacia abajo: el "frente" de la camara
# era literalmente la direccion en la que viaja la curva, no hacia donde
# conviene que el espectador vea. Ahora la curva SOLO mueve la posicion; la
# rotacion se calcula punto por punto con una "mira" (hacia donde ve la
# camara, en linea recta), igual que un dolly de cine con operador aparte
# apuntando el lente. Por default cada punto sigue mirando hacia el punto
# siguiente (se ve igual que antes en la mayoria de los casos), pero se
# puede fijar a mano con "Apuntar aqui" para el resto de tramos.
#
# Tambien cada punto tiene su propia aceleracion (antes era un unico switch
# suave/lineal para TODA la curva). Asi un tramo puede llegar con un frenon
# (speed ramp) y el siguiente salir lento, en la misma curva.
#
# Flujo tipico:
#   1) Importar los tiempos de palabras clave — el mismo palabras.json que usa
#      _tap_en_palabras.py: [{"w": "cocina", "t": 4.2}, ...] — o agregarlos a mano.
#   2) Para cada punto: mover la camara al lugar que se quiere mostrar y darle
#      "Tomar de la camara" (copia posicion, altura y lente actuales).
#   3) Si la mira automatica no basta (por ejemplo al bajar de piso, o para
#      acercarse a una recamara sin cruzar el umbral): selecciona el objeto
#      o pon el cursor 3D donde debe quedar viendo la camara, y dale
#      "Apuntar aqui". Eso desactiva la mira automatica de ese punto.
#   4) Ajusta "Aceleracion" / "Remate" del punto si quieres un speed ramp
#      (por ejemplo EXPONENCIAL + "Al salir" para que arranque de un jalon).
#   5) "Construir / actualizar" arma la curva Bezier, mete la camara en un
#      Follow Path (solo posicion) y anima lente + mira + offset en los
#      frames que tocan segun el fps de la escena.
#   6) Se puede seguir ajustando los puntos de la curva a mano en Edit Mode;
#      "Leer curva" trae esas posiciones de vuelta a esta lista (tiempo, zoom,
#      mira y nota no viven en el objeto curva, asi que no se pierden).

import json
import math

import bpy
from bpy_extras.io_utils import ImportHelper
from mathutils import Vector


def _fps(context):
    r = context.scene.render
    return r.fps / (r.fps_base or 1.0)


def _frame(tiempo, fps):
    # Frame 1 = segundo 0, que es donde Blender arranca por default.
    return max(1, round(tiempo * fps) + 1)


def _muestrear_curva(context, nombre, n):
    """Si ya existe una curva con ese nombre, regresa n posiciones (mundo)
    repartidas a lo largo de ella. Si no existe, regresa None — asi los
    puntos importados no quedan todos amontonados en el origen."""
    obj = bpy.data.objects.get(nombre)
    if obj is None or obj.type != 'CURVE' or n <= 0:
        return None
    dg = context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(dg)
    try:
        malla = obj_eval.to_mesh()
        if not malla or not malla.vertices or len(malla.vertices) < 2:
            return None
        verts = [obj.matrix_world @ v.co for v in malla.vertices]
    finally:
        obj_eval.to_mesh_clear()
    out = []
    for i in range(n):
        frac = i / max(1, n - 1)
        idx = min(len(verts) - 1, round(frac * (len(verts) - 1)))
        v = verts[idx]
        out.append((v.x, v.y, v.z))
    return out


_ITEMS_INTERPOLACION = [
    ('BEZIER', "Suave", "Aceleracion/desaceleracion normal"),
    ('LINEAR', "Lineal", "Velocidad constante, sin suavizado"),
    ('SINE', "Seno", "Suavizado ligero"),
    ('QUAD', "Cuadratica", "Aceleracion media"),
    ('CUBIC', "Cubica", "Aceleracion fuerte"),
    ('EXPO', "Exponencial (speed ramp)", "Arranque o frenado muy brusco — el tipico 'speed ramp' de reels"),
    ('BACK', "Con impulso", "Un pequeno retroceso antes de salir disparada"),
]

_ITEMS_REMATE = [
    ('EASE_IN_OUT', "Ambos lados", "La aceleracion se nota llegando y saliendo"),
    ('EASE_IN', "Al llegar", "Se nota al llegar a este punto (frena)"),
    ('EASE_OUT', "Al salir", "Se nota al salir de este punto (arranca)"),
    ('AUTO', "Automatico", "Lo decide Blender"),
]

# Catalogo de movimientos con nombre de director en vez de jerga de easing.
# Cada uno es nomas una combinacion ya probada de interpolacion + remate,
# para el tramo que SALE de este punto hacia el siguiente. 'PERSONALIZADO'
# deja los dos campos crudos (Aceleracion/Remate) editables a mano.
_CATALOGO_MOVIMIENTOS = {
    'DERIVA':     ("Deriva (dolly suave)",       'BEZIER', 'EASE_IN_OUT', "Avance parejo, suaviza igual al entrar y al salir. Para recorrer un cuarto sin prisa."),
    'FLOTAR':     ("Flotar (constante lento)",   'SINE',   'EASE_IN_OUT', "Casi sin aceleracion, ideal para rodeos/orbitas y tomas contemplativas."),
    'EMPUJE':     ("Empuje (push-in)",           'CUBIC',  'EASE_IN',     "Ya viene tomando velocidad y frena justo al llegar — un acercamiento con intencion."),
    'ARRANQUE':   ("Arranque (sale disparada)",  'EXPO',   'EASE_OUT',    "Sale de golpe desde este punto, como si algo la empujara."),
    'FRENON':     ("Frenon / speed ramp",        'EXPO',   'EASE_IN',     "Llega MUY rapido y frena en seco — el speed ramp clasico de reels."),
    'IMPULSO':    ("Impulso con anticipacion",   'BACK',   'EASE_OUT',    "Un pequeno retroceso antes de salir disparada, como tomando vuelo."),
    'CONSTANTE':  ("Velocidad constante",        'LINEAR', 'AUTO',        "Sin suavizado, velocidad pareja de principio a fin del tramo."),
}
_ITEMS_MOVIMIENTO = [
    (clave, datos[0], datos[3]) for clave, datos in _CATALOGO_MOVIMIENTOS.items()
] + [('PERSONALIZADO', "Personalizado", "Ajusta Aceleracion/Remate a mano, abajo")]


class SPLINEAUDIO_Punto(bpy.types.PropertyGroup):
    tiempo: bpy.props.FloatProperty(
        name="Tiempo (s)", description="Segundo del audio en el que la camara debe estar aqui",
        default=0.0, min=0.0, precision=2,
    )
    x: bpy.props.FloatProperty(name="X", default=0.0)
    y: bpy.props.FloatProperty(name="Y", default=0.0)
    altura: bpy.props.FloatProperty(name="Altura (Z)", default=1.6)
    zoom: bpy.props.FloatProperty(
        name="Zoom (mm)", description="Distancia focal de la camara en ese punto (mas bajo = zoom out)",
        default=50.0, min=1.0, max=300.0,
    )
    nota: bpy.props.StringProperty(
        name="Nota", default="", description="Palabra o escena de referencia (opcional)",
    )
    mira_automatica: bpy.props.BoolProperty(
        name="Mira automatica", default=True,
        description=(
            "Activo: la camara mira hacia el punto siguiente (como antes). "
            "Desactivalo y usa 'Apuntar aqui' para fijar la mira a mano — "
            "asi se evita que la camara apunte al piso al bajar de nivel, o "
            "para acercarse a un cuarto sin cruzar el umbral (walkthrough)"
        ),
    )
    mira_x: bpy.props.FloatProperty(name="Mira X", default=0.0)
    mira_y: bpy.props.FloatProperty(name="Mira Y", default=0.0)
    mira_z: bpy.props.FloatProperty(name="Mira Z", default=1.6)
    movimiento: bpy.props.EnumProperty(
        name="Movimiento",
        description="Catalogo de movimientos de camara para el tramo que SALE de este punto",
        items=_ITEMS_MOVIMIENTO, default='DERIVA',
    )
    interpolacion: bpy.props.EnumProperty(
        name="Aceleracion",
        description="Solo si 'Movimiento' = Personalizado. Como se mueve la camara AL SALIR de este punto",
        items=_ITEMS_INTERPOLACION,
        default='BEZIER',
    )
    remate: bpy.props.EnumProperty(
        name="Remate", description="Solo si 'Movimiento' = Personalizado. En que parte del tramo se nota la aceleracion",
        items=_ITEMS_REMATE, default='EASE_IN_OUT',
    )


class SPLINEAUDIO_Evento(bpy.types.PropertyGroup):
    """Animacion de un objeto (tipicamente una puerta) disparada en un
    instante del audio — independiente del recorrido de camara, pero se
    construye en el mismo boton para que todo quede sincronizado a la vez."""
    tiempo: bpy.props.FloatProperty(
        name="Tiempo (s)", description="Segundo del audio en el que arranca la animacion",
        default=0.0, min=0.0, precision=2,
    )
    objeto: bpy.props.StringProperty(
        name="Objeto", description="Nombre exacto del objeto en la escena (la puerta, etc.)", default="",
    )
    tipo: bpy.props.EnumProperty(
        name="Tipo",
        items=[
            ('DESLIZAR', "Deslizar", "Se mueve en linea recta sobre su propio eje (puerta corrediza)"),
            ('ROTAR', "Rotar", "Gira sobre su propio eje (puerta con bisagra)"),
        ],
        default='DESLIZAR',
    )
    eje: bpy.props.EnumProperty(name="Eje", items=[('X', "X", ""), ('Y', "Y", ""), ('Z', "Z", "")], default='X')
    distancia: bpy.props.FloatProperty(name="Distancia (m)", description="Cuanto se desliza (DESLIZAR)", default=1.0)
    angulo: bpy.props.FloatProperty(name="Angulo (°)", description="Cuanto gira (ROTAR)", default=90.0)
    duracion: bpy.props.FloatProperty(
        name="Duracion (s)", description="Cuanto tarda en abrir desde que arranca", default=1.0, min=0.05,
    )


class SPLINEAUDIO_Ajustes(bpy.types.PropertyGroup):
    puntos: bpy.props.CollectionProperty(type=SPLINEAUDIO_Punto)
    activo: bpy.props.IntProperty(default=0)
    eventos: bpy.props.CollectionProperty(type=SPLINEAUDIO_Evento)
    evento_activo: bpy.props.IntProperty(default=0)
    nombre_curva: bpy.props.StringProperty(name="Curva", default="RecorridoAudio")
    suave: bpy.props.BoolProperty(
        name="Puntos nuevos: suave por default", default=True,
        description="Solo afecta a los puntos que agregues de aqui en adelante (cada punto ya tiene su propia aceleracion editable)",
    )


class SPLINEAUDIO_UL_puntos(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.label(text=f"{item.tiempo:.2f}s")
        row.label(text=item.nota or "—")
        row.label(text=f"{item.zoom:.0f}mm")
        row.label(text="" if item.mira_automatica else "◎mira")


class SPLINEAUDIO_UL_eventos(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.label(text=f"{item.tiempo:.2f}s")
        row.label(text=item.objeto or "—")
        row.label(text=item.tipo.title())


class SPLINEAUDIO_OT_agregar(bpy.types.Operator):
    bl_idname = "splineaudio.agregar"
    bl_label = "Agregar punto"
    bl_description = "Agrega un punto nuevo al final de la lista"

    def execute(self, context):
        ajustes = context.scene.spline_audio
        p = ajustes.puntos.add()
        if not ajustes.suave:
            p.interpolacion = 'LINEAR'
        if len(ajustes.puntos) > 1:
            anterior = ajustes.puntos[-2]
            p.tiempo = anterior.tiempo + 1.0
            p.x, p.y, p.altura, p.zoom = anterior.x, anterior.y, anterior.altura, anterior.zoom
        else:
            cam = context.scene.camera
            if cam:
                p.x, p.y, p.altura = cam.location.x, cam.location.y, cam.location.z
                if cam.data and hasattr(cam.data, "lens"):
                    p.zoom = cam.data.lens
        ajustes.activo = len(ajustes.puntos) - 1
        return {'FINISHED'}


class SPLINEAUDIO_OT_quitar(bpy.types.Operator):
    bl_idname = "splineaudio.quitar"
    bl_label = "Quitar punto"
    bl_description = "Quita el punto seleccionado"

    def execute(self, context):
        ajustes = context.scene.spline_audio
        if ajustes.puntos:
            ajustes.puntos.remove(ajustes.activo)
            ajustes.activo = max(0, ajustes.activo - 1)
        return {'FINISHED'}


class SPLINEAUDIO_OT_mover(bpy.types.Operator):
    bl_idname = "splineaudio.mover"
    bl_label = "Mover punto"
    direccion: bpy.props.EnumProperty(items=[('ARRIBA', "Arriba", ""), ('ABAJO', "Abajo", "")])

    def execute(self, context):
        ajustes = context.scene.spline_audio
        i = ajustes.activo
        j = i - 1 if self.direccion == 'ARRIBA' else i + 1
        if 0 <= j < len(ajustes.puntos):
            ajustes.puntos.move(i, j)
            ajustes.activo = j
        return {'FINISHED'}


class SPLINEAUDIO_OT_agregar_evento(bpy.types.Operator):
    bl_idname = "splineaudio.agregar_evento"
    bl_label = "Agregar evento"
    bl_description = "Agrega una animacion de objeto (puerta, etc.) al final de la lista"

    def execute(self, context):
        ajustes = context.scene.spline_audio
        e = ajustes.eventos.add()
        if len(ajustes.eventos) > 1:
            e.tiempo = ajustes.eventos[-2].tiempo + 1.0
        if context.active_object:
            e.objeto = context.active_object.name
        ajustes.evento_activo = len(ajustes.eventos) - 1
        return {'FINISHED'}


class SPLINEAUDIO_OT_quitar_evento(bpy.types.Operator):
    bl_idname = "splineaudio.quitar_evento"
    bl_label = "Quitar evento"

    def execute(self, context):
        ajustes = context.scene.spline_audio
        if ajustes.eventos:
            ajustes.eventos.remove(ajustes.evento_activo)
            ajustes.evento_activo = max(0, ajustes.evento_activo - 1)
        return {'FINISHED'}


class SPLINEAUDIO_OT_tomar_camara(bpy.types.Operator):
    bl_idname = "splineaudio.tomar_camara"
    bl_label = "Tomar de la camara"
    bl_description = "Copia posicion, altura y zoom actuales de la camara activa al punto seleccionado"

    def execute(self, context):
        ajustes = context.scene.spline_audio
        cam = context.scene.camera
        if not cam:
            self.report({'ERROR'}, "No hay camara activa en la escena")
            return {'CANCELLED'}
        if not ajustes.puntos:
            self.report({'ERROR'}, "Agrega un punto primero")
            return {'CANCELLED'}
        p = ajustes.puntos[ajustes.activo]
        p.x, p.y, p.altura = cam.location.x, cam.location.y, cam.location.z
        if cam.data and hasattr(cam.data, "lens"):
            p.zoom = cam.data.lens
        return {'FINISHED'}


class SPLINEAUDIO_OT_tomar_mira(bpy.types.Operator):
    bl_idname = "splineaudio.tomar_mira"
    bl_label = "Apuntar aqui"
    bl_description = (
        "Fija hacia donde mira la camara en este punto: usa el objeto activo "
        "de la escena si hay uno seleccionado, o si no el cursor 3D. "
        "Desactiva la mira automatica de este punto"
    )

    def execute(self, context):
        ajustes = context.scene.spline_audio
        if not ajustes.puntos:
            self.report({'ERROR'}, "Agrega un punto primero")
            return {'CANCELLED'}
        p = ajustes.puntos[ajustes.activo]
        obj = context.view_layer.objects.active
        if obj is not None and obj.type != 'CAMERA' and obj.name != ajustes.nombre_curva:
            destino = obj.matrix_world.translation
        else:
            destino = context.scene.cursor.location
        p.mira_x, p.mira_y, p.mira_z = destino.x, destino.y, destino.z
        p.mira_automatica = False
        return {'FINISHED'}


class SPLINEAUDIO_OT_generar_rodeo(bpy.types.Operator):
    bl_idname = "splineaudio.generar_rodeo"
    bl_label = "Generar rodeo (orbit)"
    bl_description = (
        "Agrega una serie de puntos en arco alrededor de un centro (objeto activo "
        "o cursor 3D) — para rodear un jardin o fachada de un lado al otro sin "
        "tener que colocar cada punto a mano"
    )

    tiempo_inicio: bpy.props.FloatProperty(name="Tiempo inicio (s)", default=0.0, min=0.0)
    tiempo_fin: bpy.props.FloatProperty(name="Tiempo fin (s)", default=3.0, min=0.0)
    radio: bpy.props.FloatProperty(name="Radio (m)", default=5.0, min=0.1)
    altura: bpy.props.FloatProperty(name="Altura (Z)", default=1.6)
    angulo_inicio: bpy.props.FloatProperty(
        name="Angulo inicio (°)", default=-70.0,
        description="0° = frente al centro sobre +X. Negativo = lado derecho, positivo = lado izquierdo (ajusta segun tu escena)",
    )
    angulo_fin: bpy.props.FloatProperty(name="Angulo fin (°)", default=70.0)
    num_puntos: bpy.props.IntProperty(name="Puntos", default=5, min=2, max=30)
    zoom: bpy.props.FloatProperty(name="Zoom (mm)", default=35.0, min=1.0, max=300.0)
    movimiento: bpy.props.EnumProperty(name="Movimiento", items=_ITEMS_MOVIMIENTO, default='FLOTAR')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        ajustes = context.scene.spline_audio
        obj = context.view_layer.objects.active
        if obj is not None and obj.type != 'CAMERA' and obj.name != ajustes.nombre_curva:
            centro = obj.matrix_world.translation.copy()
        else:
            centro = context.scene.cursor.location.copy()

        n = self.num_puntos
        for i in range(n):
            frac = i / max(1, n - 1)
            ang = math.radians(self.angulo_inicio + (self.angulo_fin - self.angulo_inicio) * frac)
            p = ajustes.puntos.add()
            p.tiempo = self.tiempo_inicio + (self.tiempo_fin - self.tiempo_inicio) * frac
            p.x = centro.x + self.radio * math.cos(ang)
            p.y = centro.y + self.radio * math.sin(ang)
            p.altura = self.altura
            p.zoom = self.zoom
            p.nota = "rodeo"
            p.mira_automatica = False
            p.mira_x, p.mira_y, p.mira_z = centro.x, centro.y, centro.z
            p.movimiento = self.movimiento
        ajustes.activo = len(ajustes.puntos) - 1
        self.report({'INFO'}, f"{n} puntos de rodeo agregados alrededor de ({centro.x:.2f}, {centro.y:.2f}, {centro.z:.2f})")
        return {'FINISHED'}


class SPLINEAUDIO_OT_ir_a_frame(bpy.types.Operator):
    bl_idname = "splineaudio.ir_a_frame"
    bl_label = "Ir al frame del punto"
    bl_description = "Mueve el cabezal de tiempo al frame del punto seleccionado"

    def execute(self, context):
        ajustes = context.scene.spline_audio
        if not ajustes.puntos:
            return {'CANCELLED'}
        p = ajustes.puntos[ajustes.activo]
        context.scene.frame_set(_frame(p.tiempo, _fps(context)))
        return {'FINISHED'}


class SPLINEAUDIO_OT_importar_palabras(bpy.types.Operator, ImportHelper):
    bl_idname = "splineaudio.importar_palabras"
    bl_label = "Importar tiempos de audio"
    bl_description = 'Lee un palabras.json ([{"w": palabra, "t": segundos}, ...]) y agrega un punto por cada palabra clave'

    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(default="*.json", options={'HIDDEN'})
    palabras_clave: bpy.props.StringProperty(
        name="Palabras clave",
        description="Separadas por coma. Vacio = una marca cada ~2 segundos",
        default="",
    )

    def execute(self, context):
        ajustes = context.scene.spline_audio
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                palabras = json.load(f)
        except Exception as e:
            self.report({'ERROR'}, f"No se pudo leer el archivo: {e}")
            return {'CANCELLED'}

        claves = [w.strip().lower() for w in self.palabras_clave.split(",") if w.strip()]
        elegidas = []
        if claves:
            vistas = set()
            for entrada in palabras:
                w = str(entrada.get("w", "")).strip(" ,.;:!?¡¿").lower()
                if w in claves and w not in vistas:
                    vistas.add(w)
                    elegidas.append(entrada)
        else:
            # Sin filtro: una marca cada ~2s para no saturar la lista de puntos.
            ultimo = -999.0
            for entrada in palabras:
                t = float(entrada.get("t", 0.0))
                if t - ultimo >= 2.0:
                    elegidas.append(entrada)
                    ultimo = t

        if not elegidas:
            self.report({'WARNING'}, "Ninguna palabra clave encontrada en el archivo")
            return {'CANCELLED'}

        base = _muestrear_curva(context, ajustes.nombre_curva, len(elegidas))

        for i, entrada in enumerate(elegidas):
            p = ajustes.puntos.add()
            p.tiempo = float(entrada.get("t", 0.0))
            p.nota = str(entrada.get("w", ""))[:40]
            p.zoom = 50.0
            if not ajustes.suave:
                p.interpolacion = 'LINEAR'
            if base:
                p.x, p.y, p.altura = base[i]
        ajustes.activo = len(ajustes.puntos) - 1
        self.report({'INFO'}, f"{len(elegidas)} puntos agregados")
        return {'FINISHED'}


class SPLINEAUDIO_OT_construir(bpy.types.Operator):
    bl_idname = "splineaudio.construir"
    bl_label = "Construir / actualizar"
    bl_description = "Arma la curva y anima la camara (posicion, altura, mira, zoom, aceleracion) segun los puntos de la lista"

    def execute(self, context):
        ajustes = context.scene.spline_audio
        puntos = list(ajustes.puntos)
        if len(puntos) < 2 and not ajustes.eventos:
            self.report({'ERROR'}, "Se necesitan al menos 2 puntos, o algun evento")
            return {'CANCELLED'}

        fps = _fps(context)
        interp_eventos = 'BEZIER' if ajustes.suave else 'LINEAR'
        resumen = []

        if len(puntos) < 2:
            if puntos:
                self.report({'WARNING'}, "Se necesitan al menos 2 puntos para el recorrido de camara; se omitio")
        else:
            resumen.append(self._construir_camara(context, ajustes, puntos, fps))

        if ajustes.eventos:
            resumen.append(self._construir_eventos(ajustes, fps, interp_eventos))

        self.report({'INFO'}, " | ".join(r for r in resumen if r) or "nada que construir")
        return {'FINISHED'}

    @staticmethod
    def _objetivo_mira(posiciones, i, p):
        """Hacia donde ve la camara en el punto i. Si el punto no fija su
        propia mira, se ve hacia el siguiente punto de la lista (aproxima el
        viejo comportamiento de seguir la tangente de la curva); en el ultimo
        punto se extrapola la direccion del ultimo tramo para no quedarse
        viendo hacia atras."""
        if not p.mira_automatica:
            return Vector((p.mira_x, p.mira_y, p.mira_z))
        pos = posiciones[i]
        if i + 1 < len(posiciones):
            return posiciones[i + 1]
        if i > 0:
            return pos + (pos - posiciones[i - 1])
        return pos + Vector((0.0, -1.0, 0.0))

    def _construir_camara(self, context, ajustes, puntos, fps):
        orden = sorted(puntos, key=lambda p: p.tiempo)
        if orden != puntos:
            self.report({'WARNING'}, "Los puntos no estaban en orden de tiempo; se construyo por tiempo (la lista no se reordeno)")

        esc = context.scene
        cam = esc.camera
        if cam is None:
            cd = bpy.data.cameras.new("CamRecorridoAudio")
            cam = bpy.data.objects.new("CamRecorridoAudio", cd)
            esc.collection.objects.link(cam)
            esc.camera = cam
        if cam.type != 'CAMERA':
            self.report({'ERROR'}, "La camara activa de la escena no es una CAMERA")
            return None

        nombre = ajustes.nombre_curva or "RecorridoAudio"

        datos_curva = bpy.data.curves.get(nombre) or bpy.data.curves.new(nombre, 'CURVE')
        datos_curva.dimensions = '3D'
        datos_curva.splines.clear()
        spline = datos_curva.splines.new('BEZIER')
        spline.bezier_points.add(len(orden) - 1)
        # El handle de la curva es SOLO para la forma del camino (posicion);
        # ya no gobierna hacia donde mira la camara, asi que puede quedarse
        # en AUTO siempre para un recorrido bonito sin importar la mira.
        for bp, p in zip(spline.bezier_points, orden):
            bp.co = (p.x, p.y, p.altura)
            bp.handle_left_type = 'AUTO'
            bp.handle_right_type = 'AUTO'

        curva_obj = bpy.data.objects.get(nombre)
        if curva_obj is None:
            curva_obj = bpy.data.objects.new(nombre, datos_curva)
            esc.collection.objects.link(curva_obj)
        else:
            curva_obj.data = datos_curva

        frames = [_frame(p.tiempo, fps) for p in orden]
        datos_curva.path_duration = max(1, frames[-1] - frames[0])

        # Distancia acumulada entre puntos consecutivos como aproximacion del
        # largo de arco: un offset_factor proporcional a esto sigue mucho mejor
        # la velocidad real que repartir 0..1 por indice cuando los puntos no
        # estan parejos entre si. La ACELERACION real dentro de cada tramo la
        # da la interpolacion/easing de cada punto (ver mas abajo), no esto.
        posiciones = [Vector((p.x, p.y, p.altura)) for p in orden]
        acumulado = [0.0]
        for a, b in zip(posiciones, posiciones[1:]):
            acumulado.append(acumulado[-1] + (b - a).length)
        total = acumulado[-1] or 1.0
        fracciones = [d / total for d in acumulado]

        # Limpia constraint y animacion previa de ESTE recorrido antes de
        # reconstruir: si no, puntos que ya no existen dejan keyframes
        # huerfanos en frames que la lista nueva ya no cubre.
        for c in list(cam.constraints):
            if c.type == 'FOLLOW_PATH' and c.name == nombre:
                cam.constraints.remove(c)
        con = cam.constraints.new('FOLLOW_PATH')
        con.name = nombre
        con.target = curva_obj
        con.use_fixed_location = True
        # SOLO posicion: la rotacion ya no la decide el Follow Path (por eso
        # antes la camara apuntaba hacia donde bajaba la curva). Ahora se
        # keyframea aparte, punto por punto, con la "mira" de cada uno.
        con.use_curve_follow = False

        ruta_offset = 'constraints["%s"].offset_factor' % nombre
        if cam.animation_data and cam.animation_data.action:
            accion = cam.animation_data.action
            for fc in list(accion.fcurves):
                if fc.data_path in (ruta_offset, 'rotation_quaternion', 'rotation_euler'):
                    accion.fcurves.remove(fc)

        # Se fuerza mm para que "zoom" sea el mismo numero en el panel y en la
        # camara — si la camara viniera en modo FOV los valores no coincidirian.
        cam.data.lens_unit = 'MILLIMETERS'
        if cam.data.animation_data and cam.data.animation_data.action:
            accion_datos = cam.data.animation_data.action
            for fc in list(accion_datos.fcurves):
                if fc.data_path == 'lens':
                    accion_datos.fcurves.remove(fc)

        cam.rotation_mode = 'QUATERNION'

        for i, (frame, frac, p) in enumerate(zip(frames, fracciones, orden)):
            con.offset_factor = frac
            con.keyframe_insert(data_path="offset_factor", frame=frame)

            cam.data.lens = p.zoom
            cam.data.keyframe_insert(data_path="lens", frame=frame)

            objetivo = self._objetivo_mira(posiciones, i, p)
            direccion = objetivo - posiciones[i]
            if direccion.length < 1e-6:
                direccion = Vector((0.0, -1.0, 0.0))
            cam.rotation_quaternion = direccion.to_track_quat('-Z', 'Y')
            cam.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Cada keyframe usa la aceleracion/remate DE SU PROPIO punto — asi un
        # tramo puede llegar con speed ramp (p.ej. EXPONENCIAL + "Al salir")
        # y el siguiente salir lento, en la misma curva.
        ajustes_por_frame = {frame: p for frame, p in zip(frames, orden)}
        rutas_y_acciones = [(ruta_offset, cam.animation_data.action), ('lens', cam.data.animation_data.action)]
        if cam.animation_data and cam.animation_data.action:
            rutas_y_acciones.append(('rotation_quaternion', cam.animation_data.action))
        for ruta, accion in rutas_y_acciones:
            for fc in accion.fcurves:
                if fc.data_path != ruta:
                    continue
                for kp in fc.keyframe_points:
                    p = ajustes_por_frame.get(round(kp.co.x))
                    if p is None:
                        continue
                    if p.movimiento == 'PERSONALIZADO':
                        interp, remate = p.interpolacion, p.remate
                    else:
                        _, interp, remate, _ = _CATALOGO_MOVIMIENTOS[p.movimiento]
                    kp.interpolation = interp
                    if interp != 'LINEAR':
                        kp.easing = remate

        esc.frame_start = frames[0]
        esc.frame_end = frames[-1]

        return f"camara '{nombre}': {len(orden)} puntos, frames {frames[0]}-{frames[-1]}"

    def _construir_eventos(self, ajustes, fps, interp):
        """Anima cada objeto de la lista de eventos: dos keyframes — cerrado en
        `tiempo`, abierto en `tiempo + duracion` — con extrapolacion constante,
        asi que se queda cerrado antes y abierto despues sin necesitar mas keys.

        Si hay MAS de un evento sobre el mismo objeto, cada uno parte de la
        misma pose de reposo original (no se encadena uno sobre el resultado
        del otro) — para una sola puerta que abre una vez, que es el caso de
        uso normal, esto no importa."""
        ejes = {'X': 0, 'Y': 1, 'Z': 2}
        ok, problemas = 0, []
        for ev in ajustes.eventos:
            obj = bpy.data.objects.get(ev.objeto)
            if obj is None:
                problemas.append(f"'{ev.objeto}' no existe en la escena")
                continue

            f_ini = _frame(ev.tiempo, fps)
            f_fin = _frame(ev.tiempo + max(0.05, ev.duracion), fps)

            if ev.tipo == 'DESLIZAR':
                eje_local = Vector((1, 0, 0) if ev.eje == 'X' else (0, 1, 0) if ev.eje == 'Y' else (0, 0, 1))
                direccion = (obj.matrix_world.to_3x3() @ eje_local).normalized()
                base = obj.location.copy()
                obj.keyframe_insert(data_path="location", frame=f_ini)
                obj.location = base + direccion * ev.distancia
                obj.keyframe_insert(data_path="location", frame=f_fin)
                obj.location = base
                data_path = "location"
            else:
                idx = ejes[ev.eje]
                base_rot = obj.rotation_euler[idx]
                obj.keyframe_insert(data_path="rotation_euler", index=idx, frame=f_ini)
                obj.rotation_euler[idx] = base_rot + math.radians(ev.angulo)
                obj.keyframe_insert(data_path="rotation_euler", index=idx, frame=f_fin)
                obj.rotation_euler[idx] = base_rot
                data_path = "rotation_euler"

            if obj.animation_data and obj.animation_data.action:
                for fc in obj.animation_data.action.fcurves:
                    if fc.data_path == data_path:
                        fc.extrapolation = 'CONSTANT'
                        for kp in fc.keyframe_points:
                            kp.interpolation = interp
                            if interp == 'BEZIER':
                                kp.easing = 'EASE_IN_OUT'
            ok += 1

        if problemas:
            self.report({'WARNING'}, "Eventos con problemas: " + "; ".join(problemas))
        return f"eventos: {ok}/{len(ajustes.eventos)}" if ok or problemas else None


class SPLINEAUDIO_OT_leer_curva(bpy.types.Operator):
    bl_idname = "splineaudio.leer_curva"
    bl_label = "Leer curva"
    bl_description = "Trae la posicion actual de los puntos de la curva de vuelta a esta lista (tiempo/zoom/mira/nota no cambian)"

    def execute(self, context):
        ajustes = context.scene.spline_audio
        obj = bpy.data.objects.get(ajustes.nombre_curva)
        if obj is None or obj.type != 'CURVE':
            self.report({'ERROR'}, f"No existe la curva '{ajustes.nombre_curva}'. Usa Construir primero.")
            return {'CANCELLED'}
        spline = obj.data.splines[0] if obj.data.splines else None
        if spline is None or spline.type != 'BEZIER':
            self.report({'ERROR'}, "La curva no tiene una spline Bezier valida")
            return {'CANCELLED'}
        orden = sorted(ajustes.puntos, key=lambda p: p.tiempo)
        if len(orden) != len(spline.bezier_points):
            self.report({'ERROR'}, f"La curva tiene {len(spline.bezier_points)} puntos y la lista {len(orden)}; deben coincidir (Construir de nuevo si cambio la cantidad)")
            return {'CANCELLED'}
        for p, bp in zip(orden, spline.bezier_points):
            mundo = obj.matrix_world @ bp.co
            p.x, p.y, p.altura = mundo.x, mundo.y, mundo.z
        self.report({'INFO'}, "Posiciones actualizadas desde la curva")
        return {'FINISHED'}


class SPLINEAUDIO_PT_panel(bpy.types.Panel):
    bl_label = "Spline por Audio"
    bl_idname = "SPLINEAUDIO_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Seedance"

    def draw(self, context):
        ajustes = context.scene.spline_audio
        col = self.layout.column()
        col.prop(ajustes, "nombre_curva")
        col.prop(ajustes, "suave")
        col.separator()

        col.template_list("SPLINEAUDIO_UL_puntos", "", ajustes, "puntos", ajustes, "activo", rows=4)

        fila = col.row(align=True)
        fila.operator("splineaudio.agregar", icon='ADD', text="")
        fila.operator("splineaudio.quitar", icon='REMOVE', text="")
        fila.operator("splineaudio.mover", icon='TRIA_UP', text="").direccion = 'ARRIBA'
        fila.operator("splineaudio.mover", icon='TRIA_DOWN', text="").direccion = 'ABAJO'
        fila.operator("splineaudio.ir_a_frame", icon='PLAY', text="")

        if 0 <= ajustes.activo < len(ajustes.puntos):
            p = ajustes.puntos[ajustes.activo]
            box = col.box()
            box.prop(p, "tiempo")
            box.prop(p, "x")
            box.prop(p, "y")
            box.prop(p, "altura")
            box.prop(p, "zoom")
            box.prop(p, "nota")
            box.operator("splineaudio.tomar_camara", icon='CAMERA_DATA')

            box.separator()
            box.label(text="Hacia donde mira")
            box.prop(p, "mira_automatica")
            if not p.mira_automatica:
                box.prop(p, "mira_x")
                box.prop(p, "mira_y")
                box.prop(p, "mira_z")
            box.operator("splineaudio.tomar_mira", icon='TRACKING')

            box.separator()
            box.label(text="Movimiento (catalogo cinematografico)")
            box.prop(p, "movimiento", text="")
            if p.movimiento != 'PERSONALIZADO':
                box.label(text=_CATALOGO_MOVIMIENTOS[p.movimiento][3], icon='INFO')
            else:
                box.prop(p, "interpolacion")
                if p.interpolacion != 'LINEAR':
                    box.prop(p, "remate")

        col.separator()
        col.operator("splineaudio.importar_palabras", icon='IMPORT')
        col.operator("splineaudio.generar_rodeo", icon='MOD_CURVE')

        col.separator()
        col.label(text="Eventos (puertas, etc.)")
        col.template_list("SPLINEAUDIO_UL_eventos", "", ajustes, "eventos", ajustes, "evento_activo", rows=3)

        filaev = col.row(align=True)
        filaev.operator("splineaudio.agregar_evento", icon='ADD', text="")
        filaev.operator("splineaudio.quitar_evento", icon='REMOVE', text="")

        if 0 <= ajustes.evento_activo < len(ajustes.eventos):
            ev = ajustes.eventos[ajustes.evento_activo]
            box = col.box()
            box.prop(ev, "tiempo")
            box.prop_search(ev, "objeto", context.scene, "objects")
            box.prop(ev, "tipo")
            box.prop(ev, "eje")
            if ev.tipo == 'DESLIZAR':
                box.prop(ev, "distancia")
            else:
                box.prop(ev, "angulo")
            box.prop(ev, "duracion")

        col.separator()
        fila2 = col.row(align=True)
        fila2.operator("splineaudio.construir", icon='CURVE_BEZCURVE')
        fila2.operator("splineaudio.leer_curva", icon='FILE_REFRESH')


CLASES = (
    SPLINEAUDIO_Punto, SPLINEAUDIO_Evento, SPLINEAUDIO_Ajustes,
    SPLINEAUDIO_UL_puntos, SPLINEAUDIO_UL_eventos,
    SPLINEAUDIO_OT_agregar, SPLINEAUDIO_OT_quitar, SPLINEAUDIO_OT_mover,
    SPLINEAUDIO_OT_agregar_evento, SPLINEAUDIO_OT_quitar_evento,
    SPLINEAUDIO_OT_tomar_camara, SPLINEAUDIO_OT_tomar_mira, SPLINEAUDIO_OT_generar_rodeo,
    SPLINEAUDIO_OT_ir_a_frame, SPLINEAUDIO_OT_importar_palabras, SPLINEAUDIO_OT_construir,
    SPLINEAUDIO_OT_leer_curva, SPLINEAUDIO_PT_panel,
)


def register():
    for c in CLASES:
        bpy.utils.register_class(c)
    bpy.types.Scene.spline_audio = bpy.props.PointerProperty(type=SPLINEAUDIO_Ajustes)


def unregister():
    del bpy.types.Scene.spline_audio
    for c in reversed(CLASES):
        bpy.utils.unregister_class(c)


# Se puede usar de DOS formas, igual que seedance_blender.py:
#
#   A) Como add-on:  Editar > Preferencias > Add-ons > Install, elegir este
#      archivo, y MARCAR LA CASILLA (instalarlo no lo activa).
#
#   B) Sin instalar nada: pestaña "Scripting", abrir este archivo (Text > Open)
#      y darle PLAY. El panel aparece de inmediato en la vista 3D con tecla N,
#      en la misma pestaña "Seedance", debajo del conector.
if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()
    print("Spline por Audio cargado. Vista 3D > tecla N > pestaña Seedance")
