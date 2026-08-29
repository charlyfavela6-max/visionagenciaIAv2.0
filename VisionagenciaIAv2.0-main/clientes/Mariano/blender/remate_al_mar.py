"""El remate: la camara se despega del patio, sube de golpe y ENSENA DE UN
JALON que tan lejos esta el mar.

Que cambio (v2):

1) Ya NO pone llaves sueltas sobre CAM_RECORRIDO. Ahora agrega PUNTOS a la
   herramienta de camara del addon activo (`seedance_blender.py`, pestana
   Seedance > Spline por Audio) y le da "Construir". Antes las llaves se
   perdian cada vez que se apretaba "Construir / actualizar" — la trampa #2
   del ESTADO. Como puntos, el remate sobrevive.

2) El remate es RAPIDO: ~3 s de vuelo + ~1.2 s de quietud, contra los 12.9 s
   de antes. Y en vez de irse volando hasta la orilla (que tardaba y ademas
   sacaba el borde del mapa por los lados), la camara sube y RETROCEDE hasta
   un encuadre donde caben las tres cosas a la vez: la casa hasta abajo, los
   461 m de colonia en medio y el Pacifico arriba. La distancia se lee de un
   golpe de vista, sin tener que recorrerla.

El encuadre final esta calculado para NO sacar el borde del terreno: el DEM
llega a x = +-300 m, y a 42 mm el cuadro mide 277 m de medio ancho alla en la
orilla (640 m adelante). Con lente mas corto o mas altura, se ve el corte.

    listar()                 # que puntos hay ahorita y en que segundo
    al_mar()                 # arma el remate y construye
    al_mar(desde_t=42.0)     # tira lo que haya despues de 42 s y rearma
    deshacer()               # quita SOLO los puntos del remate y reconstruye

Se manda por el conector igual que los demas; el addon ya esta registrado en
ese mismo Blender, asi que bpy.ops.splineaudio.* corre sin instalar nada.

OJO: como esto llama a "Construir", despues hay que volver a correr
`paredes_y_ritmo.solo_muros()` y `muebles_aparecen.aplicar()` — sus tiempos se
calculan a partir del recorrido. Y guardar, que Ctrl+Z se lo lleva todo.
"""
import bpy
from mathutils import Vector

MARCA = "remate al mar"          # con esto se reconocen los puntos de aqui

# El cuadro final, en coordenadas de escena (escena Z = z_real - 37).
#
# v3 — medido contra las tomas de dron que mando Mariano (video del 28 Ago,
# segundo 46.4): ahi el cielo ocupa solo el 15% de arriba, la costa cruza por
# el tercio superior y todo lo demas es tierra. El remate v2 tenia 23% de cielo
# y la orilla a la mitad del cuadro: se veia mas "postal" que dron. Con la
# camara 12 m mas baja, 55 m mas cerca y 2.7 grados mas de picada sale la
# misma reparticion que la referencia:
#
#     cielo 15%  ·  mar+playa 15-39%  ·  colonia 39-87%  ·  la casa al 87%
#
# El lente no baja mas de 40 mm por el DEM: a 40 el cuadro mide 266 m de medio
# ancho en la orilla y el terreno solo llega a 300. Con 35 mm ya se asoma el
# corte por las esquinas.
# v5 — AHORA SE VE DESDE EL MAR, como la toma de dron de Mariano (segundo
# 46.4 del video del 28 Ago): el dron esta sobre el agua MIRANDO A TIERRA, con
# el oleaje en primer plano abajo, la playa cruzando el tercio bajo, la colonia
# en medio y solo una franja de cielo arriba.
#
# El movimiento es un PULL-BACK: la camara se voltea hacia la casa y retrocede
# volando los 461 m de espaldas al mar, sin dejar de mirarla. Asi no hay ningun
# giro brusco (dar la vuelta 180 grados en un segundo se veria como un latigazo)
# y la casa se va haciendo chica mientras entra todo el contexto — que es
# justamente lo que cuenta la distancia.
#
# El cuadro final, medido: cielo 15% · la casa al 22% · la orilla al 65% ·
# oleaje de ahi para abajo. La camara queda a 100 m sobre el nivel del mar y a
# 623 m de la casa; a 24 mm eso mide 263 m de medio ancho alla en la casa, y el
# DEM llega a 300: entra justo.
X_FIN, Y_FIN, Z_FIN = 3.5, 620.0, 63.0
LENTE_FIN = 24.0
MIRA_FIN = (3.5, 260.0, -111.0)   # 25.8 grados de picada, hacia tierra

# La deriva final ya no puede abrirse mucho de lado: a 663 m el cuadro mide
# 280 m de medio ancho y el terreno se acaba en 300.
DERIVA = (18.0, 40.0, 7.0)
DERIVA_MIRA = (18.0, 40.0, 7.0)

# frac_t, posicion, lente, hacia donde mira, movimiento, nota.
# La mira va ABSOLUTA por punto: interpolandola se descontrolaba el picado
# (en el tramo de en medio salia mirando casi al suelo, a -60 grados).
TRAMOS = [
    # El vuelo se lleva tambien el punto del jardin (t 34.6, "137m2
    # construidos"): desde ahi la camara ya voltea al mar y arranca el
    # retroceso, para que en el 38.0 —"te la enseño cuando quieras"— el cuadro
    # ya sea el del oceano.
    (0.00, (-1.8, 18.6, -0.8), 18.0, (3.5, 60.0, -6.0),    'DERIVA',
     "0/3 en el jardin, ya volteando al mar"),
    (0.28, (3.5, 80.0, 22.0),  20.0, (3.5, 5.0, 0.0),      'DERIVA',
     "1/3 se voltea y despega de espaldas"),
    (0.62, (3.5, 300.0, 42.0), 22.0, (3.5, 60.0, -38.0),   'DERIVA',
     "2/3 cruza la colonia, la casa ya es chica"),
    (1.00, (X_FIN, Y_FIN, Z_FIN), LENTE_FIN, MIRA_FIN,     'FLOTAR',
     "3/3 sobre el mar, mirando la casa a 623 m"),
]

def _ajustes():
    esc = bpy.context.scene
    if not hasattr(esc, "spline_audio"):
        raise RuntimeError(
            "la herramienta de camara no esta cargada: abre seedance_blender.py "
            "en la pestana Scripting y dale Run Script (o activa el add-on)")
    return esc.spline_audio


def _mezcla(a, b, f):
    return a + (b - a) * f


def listar():
    """Los puntos que tiene la spline ahorita, para decidir desde donde cortar."""
    aj = _ajustes()
    return [{"i": i, "t": round(p.tiempo, 2), "nota": p.nota,
             "pos": [round(p.x, 1), round(p.y, 1), round(p.altura, 1)],
             "mm": round(p.zoom, 1)}
            for i, p in enumerate(sorted(aj.puntos, key=lambda q: q.tiempo))]


def deshacer(desde_t=None, salida_previa='DERIVA', construir=True):
    """Quita los puntos del remate. Con `desde_t` quita ademas TODO punto
    posterior a ese segundo (para tirar un remate viejo hecho a mano)."""
    aj = _ajustes()
    fuera = []
    for i in range(len(aj.puntos) - 1, -1, -1):
        p = aj.puntos[i]
        if MARCA in p.nota or (desde_t is not None and p.tiempo > desde_t):
            fuera.append(round(p.tiempo, 2))
            aj.puntos.remove(i)
    if fuera and aj.puntos:
        # el punto que quedo al final vuelve a su salida normal
        ultimo = max(aj.puntos, key=lambda q: q.tiempo)
        ultimo.movimiento = salida_previa
    aj.activo = max(0, len(aj.puntos) - 1)
    if construir and len(aj.puntos) >= 2:
        bpy.ops.splineaudio.construir()
    return {"quitados": sorted(fuera)}


def al_mar(duracion=3.4, espera=4.5, desde_t=None, salida='DERIVA', arranca_en=None):
    """Arma el remate como puntos de la spline y construye.

    duracion: segundos de vuelo hasta quedar sobre el mar.
    espera:   segundos de deriva sobre el agua despues de llegar.
    desde_t:  si se pasa, primero tira todo punto posterior a ese segundo.
    arranca_en: segundo en que empieza el vuelo. Sin esto se toma el ultimo
              punto que quede, que no siempre es el que uno quiere.
    salida:   con que movimiento arranca el ultimo punto del recorrido. Era
              'ARRANQUE' (exponencial), que salia de golpe y se sentia un
              tiron; 'DERIVA' acelera parejo y se ve fluido.

    El vuelo tiene que estar TERMINADO cuando la voz dice "te la enseño cuando
    quieras" (segundo 38.0): a esa altura el cuadro ya es el del mar.
    """
    aj = _ajustes()
    quitados = deshacer(desde_t=desde_t, construir=False)["quitados"]
    if len(aj.puntos) < 1:
        return {"error": "no hay recorrido al cual pegarle el remate"}

    patio = max(aj.puntos, key=lambda p: p.tiempo)
    t0 = patio.tiempo if arranca_en is None else arranca_en
    px, py, pz = patio.x, patio.y, patio.altura
    salida_previa = patio.movimiento
    patio.movimiento = salida

    # activo fuera de rango a proposito: el callback 'update' de X/Y/Altura
    # reconstruye la escena entera cada vez que se toca el punto ACTIVO, y
    # eso serian ~12 reconstrucciones aqui adentro.
    aj.activo = -1

    puestos = []
    for frac_t, pos, lente, mira, movimiento, nota in TRAMOS:
        p = aj.puntos.add()
        p.tiempo = t0 + duracion * frac_t
        p.x, p.y, p.altura = pos
        p.zoom = lente
        p.mira_automatica = False
        p.mira_x, p.mira_y, p.mira_z = mira
        p.movimiento = movimiento
        p.nota = MARCA + " - " + nota
        puestos.append(round(p.tiempo, 2))

    if espera > 0:
        q = aj.puntos.add()                 # sigue volando: deriva de dron
        ultimo = aj.puntos[len(aj.puntos) - 2]
        q.tiempo = t0 + duracion + espera
        q.x = ultimo.x + DERIVA[0]
        q.y = ultimo.y + DERIVA[1]
        q.altura = ultimo.altura + DERIVA[2]
        q.zoom = ultimo.zoom
        q.mira_automatica = False
        q.mira_x = ultimo.mira_x + DERIVA_MIRA[0]
        q.mira_y = ultimo.mira_y + DERIVA_MIRA[1]
        q.mira_z = ultimo.mira_z + DERIVA_MIRA[2]
        q.movimiento = 'FLOTAR'
        q.nota = MARCA + " - deriva de dron mientras se lee la distancia"
        puestos.append(round(q.tiempo, 2))

    aj.activo = len(aj.puntos) - 1
    bpy.ops.splineaudio.construir()

    esc = bpy.context.scene
    return {"quitados": quitados, "puntos_nuevos": puestos,
            "arranca_en_s": round(t0, 2), "termina_en_s": puestos[-1],
            "dura_s": round(duracion + espera, 2),
            "salida_previa_del_patio": salida_previa,
            "frame_end": esc.frame_end,
            "camara_final": [X_FIN, Y_FIN, Z_FIN], "lente_final_mm": LENTE_FIN,
            "mira_final": list(MIRA_FIN),
            "reparticion_del_cuadro": {"formato": "9:16", "visto_desde": "el mar",
                                       "cielo_%": 15, "la_casa_en_%": 22,
                                       "la_orilla_en_%": 65, "oleaje_%": "65-100"},
            "altura_sobre_el_mar_m": round(Z_FIN + 37),
            "distancia_a_la_casa_m": 623,
            "nota": "el cuadro final es la toma del dron: el mar en primer "
                    "plano, la playa, la colonia y la casa alla al fondo. "
                    "Vuelve a correr "
                    "paredes_y_ritmo.solo_muros() y muebles_aparecen.aplicar(), "
                    "y GUARDA."}


# ----------------------------------------------------------------- ambiente --
# En la referencia de dron el agua es turquesa y el cielo azul fuerte de
# mediodia. El MAR de la escena estaba gris azulado y el fondo gris claro, asi
# que el remate se veia apagado aunque el encuadre fuera el correcto. Esto lo
# unico que toca son DOS colores, y devuelve los de antes para poder volver.
MAR_TURQUESA = (0.055, 0.32, 0.36, 1.0)
CIELO = (0.34, 0.58, 0.86)
# La tierra de la referencia es arena seca, no cafe oscuro. Los objetos del
# terreno lejano estaban tan bajos de valor que el remate salia sucio.
TIERRA = {"TER_real": (0.30, 0.24, 0.15, 1.0),
          "TER_escenica": (0.22, 0.21, 0.20, 1.0),
          "COLONIA_relleno": (0.42, 0.38, 0.32, 1.0),
          "COLONIA_osm": (0.52, 0.50, 0.47, 1.0),
          "COLONIA_calles": (0.16, 0.16, 0.17, 1.0)}


def ambiente(mar=MAR_TURQUESA, cielo=CIELO, tierra=None):
    esc = bpy.context.scene
    sh = esc.display.shading
    previo = {"background_type": sh.background_type,
              "background_color": list(sh.background_color),
              "color_type": sh.color_type}

    # El fondo del RENDER en Workbench no sale de `background_color` (eso es
    # solo el viewport): sale del World. Costo un render descubrirlo.
    mundo = esc.world or bpy.data.worlds.get("World")
    if mundo is None:
        mundo = bpy.data.worlds.new("World")
        esc.world = mundo
    previo["world"] = [mundo.name, list(mundo.color)]
    mundo.color = cielo
    if mundo.use_nodes:
        for n in mundo.node_tree.nodes:
            if n.type == 'BACKGROUND':
                previo["world_nodo"] = list(n.inputs[0].default_value)
                n.inputs[0].default_value = (cielo[0], cielo[1], cielo[2], 1.0)

    for nombre, col in (TIERRA if tierra is None else tierra).items():
        ob = bpy.data.objects.get(nombre)
        if not ob:
            continue
        for ranura in ob.material_slots:
            mt = ranura.material
            if mt:
                previo.setdefault("materiales", {})[mt.name] = list(mt.diffuse_color)
                mt.diffuse_color = col

    # Workbench pinta por `diffuse_color` del material, no por el nodo: es la
    # misma trampa del alpha de los muros.
    tocados = []
    ob = bpy.data.objects.get("MAR")
    if ob:
        for ranura in ob.material_slots:
            m = ranura.material
            if not m:
                continue
            previo.setdefault("materiales", {})[m.name] = list(m.diffuse_color)
            m.diffuse_color = mar
            if m.use_nodes:
                for n in m.node_tree.nodes:
                    if "Base Color" in getattr(n, "inputs", {}):
                        n.inputs["Base Color"].default_value = mar
            tocados.append(m.name)

    sh.color_type = 'MATERIAL'
    sh.background_type = 'WORLD'
    sh.background_color = cielo
    return {"materiales_del_mar": tocados, "cielo": list(cielo), "previo": previo}


def ambiente_deshacer(previo):
    esc = bpy.context.scene
    sh = esc.display.shading
    sh.background_type = previo["background_type"]
    sh.background_color = previo["background_color"]
    sh.color_type = previo["color_type"]
    if previo.get("world"):
        mundo = bpy.data.worlds.get(previo["world"][0])
        if mundo:
            mundo.color = previo["world"][1]
            if previo.get("world_nodo") and mundo.use_nodes:
                for n in mundo.node_tree.nodes:
                    if n.type == 'BACKGROUND':
                        n.inputs[0].default_value = previo["world_nodo"]
    for nombre, col in (previo.get("materiales") or {}).items():
        m = bpy.data.materials.get(nombre)
        if m:
            m.diffuse_color = col
    return {"revertido": True}


def vertical(ancho=1080, alto=1920):
    """Pone la escena en 9:16, que es como se entrega el video. No es un
    detalle de salida: con sensor_fit AUTO el formato CAMBIA el encuadre, asi
    que hay que fijarlo ANTES de componer nada."""
    r = bpy.context.scene.render
    previo = [r.resolution_x, r.resolution_y]
    r.resolution_x, r.resolution_y = ancho, alto
    r.pixel_aspect_x = r.pixel_aspect_y = 1.0
    return {"antes": previo, "ahora": [ancho, alto]}


# ------------------------------------------------------------------ oleaje --
# En la toma del dron el tercio de abajo NO es agua lisa: son lineas de espuma
# rompiendo, y eso es lo que hace que se lea "mar" y no "plano azul". El MAR de
# la escena es un plano de un solo color, asi que se le ponen unas bandas
# blancas paralelas a la costa. Son planos, no simulacion: pesan nada.
ESPUMA = "ESPUMA_"
NIVEL_MAR = -37.0
# (y del centro, ancho en metros, blancura). Tres, no cinco: con cinco lineas
# igual de largas y a la misma distancia el mar parecia una persiana. El
# rompiente de verdad se amontona junto a la orilla y se apaga rapido.
LINEAS = [(496.0, 3.6, 0.92), (503.0, 2.4, 0.78), (512.0, 1.6, 0.62)]
LARGO_X = (-290.0, 297.0)          # sin pasarse del DEM
# La playa: sin esta franja el agua pegaba con la tierra en un corte seco.
PLAYA = (484.0, 497.0, (0.74, 0.69, 0.58, 1.0))


def espuma_fuera():
    fuera = [o for o in bpy.data.objects if o.name.startswith(ESPUMA)]
    for o in fuera:
        bpy.data.objects.remove(o, do_unlink=True)
    for m in [m for m in bpy.data.materials if m.name.startswith(ESPUMA)]:
        bpy.data.materials.remove(m)
    return {"quitadas": len(fuera)}


def espuma():
    """Bandas de espuma paralelas a la orilla, sobre el agua."""
    import bmesh
    espuma_fuera()
    esc = bpy.context.scene
    col = bpy.data.collections.get("TERRENO_MAR") or esc.collection
    hechas = []

    def banda(nombre, y0, y1, z, color):
        me = bpy.data.meshes.new(nombre)
        ob = bpy.data.objects.new(nombre, me)
        col.objects.link(ob)
        bm = bmesh.new()
        v = [bm.verts.new(q) for q in ((LARGO_X[0], y0, 0.0), (LARGO_X[1], y0, 0.0),
                                       (LARGO_X[1], y1, 0.0), (LARGO_X[0], y1, 0.0))]
        bm.faces.new(v)
        bm.to_mesh(me)
        bm.free()
        ob.location = (0.0, 0.0, z)
        mat = bpy.data.materials.new(nombre)
        mat.diffuse_color = color
        ob.data.materials.append(mat)
        hechas.append(ob.name)
        return ob

    banda(ESPUMA + "playa", PLAYA[0], PLAYA[1], NIVEL_MAR + 1.60, PLAYA[2])
    for i, (y, ancho, blanco) in enumerate(LINEAS):
        # 6 cm sobre el agua: menos que eso y el z-fighting la hace parpadear
        # bajan hacia mar adentro: la primera casi en la berma, la ultima
        # rozando el agua. Antes iban a 6 cm y el oleaje se las tragaba.
        banda(ESPUMA + "%02d" % i, y - ancho / 2, y + ancho / 2,
              NIVEL_MAR + 1.55 - i * 0.30,
              (blanco, blanco * 0.99, blanco * 0.97, 1.0))
    return {"lineas": hechas, "nivel_mar": NIVEL_MAR}


# ------------------------------------------------- el DEM que sale del agua --
# El SRTM sobre el oceano no da 0: da ruido de 0 a 5 m. Traducido a la escena
# eso es z de -37 a -32, o sea POR ENCIMA del nivel del mar (-37). Mientras la
# camara miraba desde tierra no se notaba —el agua quedaba lejos—, pero al
# ponerla sobre el mar el primer plano entero salio de tierra cafe en vez de
# agua. Hay que hundir el terreno donde ya es oceano.
Y_AGUA = 500.0        # de aqui para el mar ya no hay playa
Y_PLAYA = 486.0       # y aqui empieza a bajar, para que la orilla no sea un escalon
Z_FONDO = -39.5       # bien por debajo del plano del MAR (-37)


def hundir_el_oceano(objetos=("TER_real", "TER_escenica"), y_agua=Y_AGUA,
                     y_playa=Y_PLAYA, z_fondo=Z_FONDO):
    """Baja bajo el agua los vertices del terreno que ya caen en el oceano.

    Se puede volver a correr sin acumular error: nunca SUBE un vertice, solo
    lo baja, y lo que ya esta hundido se queda igual. Para deshacerlo del todo
    hay que rehacer la malla con `terreno_mar.py`.
    """
    tocados = {}
    for nombre in objetos:
        ob = bpy.data.objects.get(nombre)
        if ob is None or ob.type != 'MESH':
            continue
        M = ob.matrix_world
        Mi = M.inverted()
        n = 0
        for v in ob.data.vertices:
            p = M @ v.co
            if p.y < y_playa:
                continue
            # entre la playa y el agua se baja de a poco; mas alla, al fondo
            f = 1.0 if p.y >= y_agua else (p.y - y_playa) / (y_agua - y_playa)
            objetivo = p.z + (z_fondo - p.z) * f
            if objetivo < p.z - 1e-4:
                p.z = objetivo          # `p` ya es un Vector: se reusa y se devuelve
                v.co = Mi @ p
                n += 1
        ob.data.update()
        tocados[nombre] = n
    return {"vertices_hundidos": tocados, "y_agua": y_agua, "z_fondo": z_fondo}
