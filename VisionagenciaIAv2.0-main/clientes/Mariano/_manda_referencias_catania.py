#!/usr/bin/env python3
"""Manda a Carlos las referencias del recorrido 3D de la Catania.

    python3 clientes/Mariano/_manda_referencias_catania.py

Van dos laminas de referencia por cuarto (frames de los clips que mando
Mariano, ya emparejados con el segundo del recorrido) y las satelitales del
alejamiento. Igual que `_manda_flyers_carlos.py`: por WAAPI, en base64, y como
la instancia ES el telefono de Carlos todo le llega `fromMe` — por eso cada pie
lleva la marca, para distinguirlo de lo que escribe el.
"""
import base64, json, os, sys, time, urllib.request

RAIZ = "/workspaces/visionagenciaIAv2.0/VisionagenciaIAv2.0-main"
REF = os.path.join(RAIZ, "clientes/Mariano/referencias_3d")
MARCA = "🏠 Catania 3D · "


def env(n, x=""):
    for l in open(os.path.join(RAIZ, ".env"), encoding="utf8", errors="replace"):
        if l.startswith(n + "="):
            return l.split("=", 1)[1].strip().strip('"').strip("'")
    return x


TOKEN, INST = env("WAAPI_TOKEN"), env("WAAPI_INSTANCE")
CHAT = "".join(c for c in env("CARLOS_TEL", "5216312470486") if c.isdigit()) + "@c.us"
API = f"https://waapi.app/api/v1/instances/{INST}/client/action"

INTRO = (
    "🏠 Catania 3D · Referencias para el recorrido\n\n"
    "1) Frames de los clips que mandó Mariano, emparejados con cada cuarto del 3D "
    "(sale el segundo del recorrido en el que va).\n"
    "2) Lo que Catania NO tiene en video: cocina, baño, pasillo y escalera van de "
    "Siena/Brescia — misma constructora, mismo acabado.\n"
    "3) Satelitales para armar el alejamiento, de la casa hasta el Pacífico.\n\n"
    "⚠️ No hay referencia de ESTUDIO (t 26.5 s) ni de la COCHERA con 2 carros "
    "(t 3.6 s) en ningún lote. Si Mariano tiene esos dos clips, se cierra la casa."
)

ENVIOS = [
    ("ref_1_catania_por_cuarto.jpg",
     "1/8 · los 10 clips de Catania, cada uno con su cuarto y su segundo del recorrido"),
    ("ref_2_faltantes_otros_modelos.jpg",
     "2/8 · lo que falta en Catania, tomado de Siena y Brescia (mismos acabados)"),
    ("ref_3_dron_real_mariano.jpg",
     "3/9 · las tomas de dron de TU video (28 Ago 21:33). La de 46.4 s es "
     "exactamente el remate: colonia, playa y mar en un cuadro"),
    ("mapa_1_z19_la_casa.jpg", "3/8 · la casa, donde arranca el remate (0.25 m/px)"),
    ("mapa_2_z18_la_manzana.jpg", "4/8 · la manzana y la calle Catania"),
    ("mapa_3_z17_la_colonia.jpg", "5/8 · la colonia: esto es lo que pasa por debajo"),
    ("mapa_4_z16_hasta_la_playa.jpg",
     "6/8 · ya cabe la playa. La línea amarilla son los 461 m exactos casa→orilla"),
    ("mapa_5_z15_el_pacifico.jpg", "7/8 · el encuadre del cuadro final: casa + colonia + Pacífico"),
    ("ref_4_simulacion_del_remate.jpg",
     "9/9 · el mismo cuadro del remate pero con el satélite pegado sobre el "
     "terreno real: así se vería con textura, comparado contra el dron de Mariano"),
    ("casa_entera_de_lado.jpg",
     "LA CASA ENTERA DE LADO: los 3 niveles en corte con todos los muebles, y "
     "debajo las 8 fotos reales que la alimentan. Ya con el balcón con barandal, "
     "el talud detrás del patio (había un agujero de 3 m) y las vecinas "
     "encendiéndose en el frame 827, justo cuando arranca el alejamiento"),
    ("frames_vs_referencias.jpg",
     "CORREGIDA: la vista de dron SÍ tiene referencia (tu video, 46.4 s) — la "
     "había dejado en rojo por error. Arriba el 3D de hoy, abajo la foto real. "
     "Verde = alcanza · amarillo = es de otro modelo · rojo = no hay nada. "
     "El único sin nada es el ESTUDIO"),
    ("balcon_referencia.jpg",
     "EL BALCON: el modelo tenía justo lo contrario de lo real — una losa "
     "volada de 1.05 m y SIN barandal. En el clip 13 el barandal va pegado al "
     "vidrio y en el clip 10 la fachada es plana: es un balcón francés, no un "
     "balcón. Ya corregido en las 5 casas"),
    ("giroscopio_apuntada_a_la_casa.png",
     "Ya apunté ese punto (t 34.6, arranque del remate) a lo que tenías "
     "seleccionado. La herramienta sí servía: estaba girando el punto #20, el "
     "del remate sobre el mar, porque era el activo en la lista. Ya no: ahora "
     "trabaja sobre el punto del CUADRO en el que estás parado"),
    ("giroscopio_recamara.png",
     "GIROSCOPIO listo en tu panel (N > Seedance > el punto > Hacia donde mira). "
     "Sliders de Giro e Inclinación que mueven la cámara EN VIVO, flechas de "
     "±12° y ±8°, y un botón para apuntar a lo que tengas seleccionado. Esta "
     "recámara ya la bajé a -9° de inclinación"),
    ("paredes_finas.jpg",
     "PAREDES: no estaban mal medidas (15 cm es lo real), pero en Workbench el "
     "canto agarra otro tono y cada muro se leía como tabique. A 7 cm, y las "
     "losas de 20 a 10, se ven como lámina. Reversible con engordar()"),
    ("mar_con_olas.jpg",
     "EL MAR simulado: ya no es un plano azul. Olas de 1.9 m avanzando hacia la "
     "playa, color por profundidad (turquesa al romper, azul mar adentro) y el "
     "terreno pintado como en tu video: ocre, seco, manchas verdes y arena"),
    ("cuartos_mas_abiertos.jpg",
     "LOS CUARTOS: en 9:16 el sensor se va a lo alto y el ancho se cae de 60 a "
     "35 grados — por eso se veían cerrados. Bajé los lentes 30% y alejé la "
     "cámara 1.4 m en los 16 puntos de interiores"),
    ("vista_desde_el_mar.jpg",
     "LA VISTA DESDE EL MAR, al lado de tu referencia. El vuelo ya termina en "
     "t 38.0 (\"te la enseño cuando quieras\") en vez de a los 46.4, y el video "
     "baja de 48 a 42.5 s: 5.5 s menos de silencio"),
    ("estudio_antes_despues.jpg",
     "EL ESTUDIO: antes eran puros paneles porque (1) un closet de la recámara "
     "tapaba la vista, (2) el muro no se desvanecía y (3) el escritorio brotaba "
     "en el frame 943, o sea 13 s DESPUÉS de que se enseña el cuarto. Ya tiene "
     "librero con libros, monitor, teclado, lámpara, tapete y planta"),
    ("blender_remate_v4_916.png",
     "EL REMATE NUEVO en 9:16, calcado del dron de Mariano: cielo 15%, mar y "
     "playa hasta el 30%, la colonia en medio y la casa al 86%. Ya con mar "
     "turquesa, cielo azul y el terreno en arena. La escena quedó en 1080x1920"),
    ("blender_remate_frame1153.png",
     "8/8 · así quedó YA en tu Blender (frame 1153). Casa abajo, 461 m de colonia, "
     "mar arriba. Falta la luz: sigue en modo noche"),
]


def pide(ruta, cuerpo, espera=240):
    req = urllib.request.Request(
        f"{API}/{ruta}", data=json.dumps(cuerpo).encode(),
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=espera) as r:
        return json.loads(r.read())


def manda(nombre, pie):
    ruta = os.path.join(REF, nombre)
    r = pide("send-media", {
        "chatId": CHAT,
        "mediaBase64": base64.b64encode(open(ruta, "rb").read()).decode(),
        "mediaName": nombre,
        "mediaCaption": MARCA + pie,
    })
    return (r.get("data") or {}).get("status") or r.get("status") or "?"


if __name__ == "__main__":
    solo = sys.argv[1:]                       # opcional: nombres sueltos a mandar
    print("chat:", CHAT)
    if not solo:
        pide("send-message", {"chatId": CHAT, "message": INTRO})
        time.sleep(2)
    for nombre, pie in ENVIOS:
        if solo and nombre not in solo:
            continue
        try:
            kb = os.path.getsize(os.path.join(REF, nombre)) // 1024
            print(f"  {nombre:38} {kb:4} KB  {manda(nombre, pie)}")
        except Exception as e:
            print(f"  {nombre:38} FALLO {str(e)[:90]}")
        time.sleep(2.5)
