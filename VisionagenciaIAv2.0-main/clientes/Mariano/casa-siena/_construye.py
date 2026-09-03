#!/usr/bin/env python3
"""Arma la landing de la Siena metiendo todo el material adentro del HTML.

Por que va todo embebido y no con rutas: Carlos no copia archivos del Codespace
—lo que no viaja en un solo archivo o en un link, no llega. La pagina termina
siendo un HTML de ~3 MB que se abre igual en el celular sin servidor detras.

El material NO se genera aqui. Todo sale de clientes/Mariano, ya aprobado:

  casa.mp4      flyersaanimar/CASA_seedance_5s.mp4
  siena.mp4     recorte 9.10s-18.10s de mariano_KELSIE_v13.mp4  (el tramo que
                dice "Siena. Tres niveles, recamaras con ventanal y escalera
                abierta, desde 4.4 millones" — con sus subtitulos quemados)
  flyer.mp4     flyersaanimar/MARIANO_FLYER_ANIMADO.mp4
  kling.mp4     flyersaanimar/FLYER_kling_4s.mp4
  endcard.mp4   mariano_ENDCARD_v1_4s.mp4
  vo_*.mp3      vo/  (los seis tramos de la locucion)

Correr:  python3 clientes/Mariano/casa-siena/_construye.py
Salida:  clientes/Mariano/casa-siena-landing.html
"""
import base64
import json
import mimetypes
import os
import re
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
MARIANO = os.path.dirname(AQUI)
RAIZ = os.path.dirname(os.path.dirname(MARIANO))
MEDIA = os.path.join(AQUI, "media")
SALIDA = os.path.join(MARIANO, "casa-siena-landing.html")
ARTEFACTO = os.path.join(AQUI, "artefacto.html")

# Que se recomprime y como. Los originales pesan 60 MB entre todos; el limite
# util de un HTML que se manda por WhatsApp o se publica son ~15 MB, y el base64
# infla un 37% mas. Con estos ajustes el total queda en ~2.5 MB.
# Los que la pagina RECORRE con el dedo llevan `scroll=True`, y eso cambia como
# se comprimen. Ver `prepara()`: sin keyframes densos el scroll no responde.
RECETAS = [
    # (destino, fuente, corte, filtro de video, con voz, se recorre con el dedo)
    ("casa.mp4",    "flyersaanimar/CASA_seedance_5s.mp4",      None,            "scale=720:720",   False, False),
    ("siena.mp4",   "MARIANO_COMPLETO_v9.mp4",                 ("9.10", "18.10"), "scale=608:1080", True,  False),

    # El flyer va a 2.5x. Medido: de sus 10 s, 7 son un cuadro congelado —se arma
    # en el primer segundo, hay un destello a los 4.5, y el resto no se mueve—.
    # Repartido sobre una pantalla de scroll, eso es bajar y que no pase nada:
    # exactamente lo que se veia roto. Acelerado queda en 4 s de puro movimiento,
    # como los demas, y sin cortarle nada ni dejar saltos.
    ("flyer.mp4",   "flyersaanimar/MARIANO_FLYER_ANIMADO.mp4", None, "scale=720:720,setpts=PTS/2.5", False, True),
    ("kling.mp4",   "flyersaanimar/FLYER_kling_4s.mp4",        None,            "scale=720:720",   False, True),
    ("endcard.mp4", "mariano_ENDCARD_v1_4s.mp4",               None,            "scale=608:1080",  False, True),

    # EL RECORRIDO. Son los videos que Mariano mando por WhatsApp de la casa
    # muestra — la casa de verdad, no renders ni nada generado. Ya vienen
    # recortados a 3 s en casa-siena/recorrido/, en el orden en que se camina la
    # casa: se entra, se ve la sala, se sube, las dos recamaras, y se sale a la
    # terraza. Se recomprimen aqui igual que lo demas.
    ("rec1.mp4", "casa-siena/recorrido/1_entrada.mp4",    None, "scale=900:-2", False, True),
    ("rec2.mp4", "casa-siena/recorrido/2_sala.mp4",       None, "scale=900:-2", False, True),
    ("rec3.mp4", "casa-siena/recorrido/3_escalera.mp4",   None, "scale=900:-2", False, True),
    ("rec4.mp4", "casa-siena/recorrido/4_recamara.mp4",   None, "scale=900:-2", False, True),
    ("rec5.mp4", "casa-siena/recorrido/5_recamara2.mp4",  None, "scale=900:-2", False, True),
    ("rec6.mp4", "casa-siena/recorrido/6_terraza.mp4",    None, "scale=900:-2", False, True),
]

# Cada cuantos cuadros va un keyframe en los videos que se recorren con el dedo.
#
# Esto es LO QUE HACE que el scroll responda, y costo encontrarlo: los videos
# traian UN SOLO keyframe (el flyer, dos en 300 cuadros). Para pintar el cuadro
# 150 el navegador tenia que decodificar los 150 desde el principio, en cada
# movimiento del dedo. Por eso se sentia trabado aunque el archivo ya estuviera
# entero en memoria: no era la descarga, era el decodificador.
#
# Con 4, lo peor que puede pasar son 3 cuadros de decodificacion. Medido: g=1
# (todo keyframe) es lo ideal para rascar pero pesa 3.4x y no cabe en el limite
# de 15 MB del archivo publicado; g=4 pesa ~1.5x y ya no se nota la diferencia.
KEYFRAME_CADA = 4

# Los seis tramos: archivo, lo que se oye, y de donde viene esa linea.
# El texto es el transcrito de subs_mariano.json, no inventado.
TRAMOS = [
    ("00_gancho_precio.mp3", "Todos buscan casa nueva pensando que hay tiempo de sobra",
     "el gancho, 0:00"),
    ("01_intro.mp3", "En San Marino Residencial", "la entrada, 0:03"),
    ("02_siena.mp3", "Siena: tres niveles, recámaras con ventanal y escalera abierta, desde 4.4 millones",
     "la Siena, 0:09"),
    ("03_catania.mp3", "Catania: terraza en azotea y ventanales con vista abierta, desde 5 millones",
     "la Catania, 0:18"),
    ("04_brescia.mp3", "Brescia: sala amplia, terraza propia y recámara con vista, desde 3.8 millones",
     "la Brescia, 0:26"),
    ("05_cta.mp3", "Agenda tu visita de lunes a sábado de 9 a 6", "el cierre, 0:33"),
]

FUENTES = "/usr/share/fonts/opentype/urw-base35"
# Solo los signos que la pagina usa de verdad; la Nimbus completa son 80 KB y
# subconjunta baja a 5.
GLIFOS = ("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
          "áéíóúñÁÉÍÓÚÑ¿?¡!.,:;·—–-()/&%$'\" ")


def corre(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"fallo: {' '.join(cmd[:6])}…\n{r.stderr[-600:]}")


def prepara():
    """Recomprime el material. Se salta lo que ya esta hecho y sigue fresco."""
    os.makedirs(MEDIA, exist_ok=True)

    def vieja(dest, orig):
        d, o = os.path.join(MEDIA, dest), os.path.join(MARIANO, orig)
        return not os.path.exists(d) or os.path.getmtime(d) < os.path.getmtime(o)

    for dest, orig, corte, filtro, voz, scroll in RECETAS:
        if not vieja(dest, orig):
            continue
        print("  ·", dest, "· con keyframes densos" if scroll else "")
        cmd = ["ffmpeg", "-y", "-v", "error"]
        if corte:
            cmd += ["-ss", corte[0], "-to", corte[1]]
        cmd += ["-i", os.path.join(MARIANO, orig), "-vf", filtro,
                "-c:v", "libx264", "-profile:v", "main", "-pix_fmt", "yuv420p",
                # Los que se recorren con el dedo van un punto mas comprimidos:
                # los keyframes densos ya inflan lo suyo y hay que caber en 15 MB.
                "-crf", "28" if scroll else "26",
                "-preset", "slow", "-movflags", "+faststart"]
        if scroll:
            # `sc_threshold=0` para que no meta keyframes de mas por su cuenta y
            # el intervalo quede parejo; sin el, x264 los reparte donde quiere.
            cmd += ["-g", str(KEYFRAME_CADA), "-keyint_min", str(KEYFRAME_CADA),
                    "-sc_threshold", "0"]
        cmd += ["-c:a", "aac", "-b:a", "72k", "-ac", "1"] if voz else ["-an"]
        corre(cmd + [os.path.join(MEDIA, dest)])

    for archivo, _, _ in TRAMOS:
        if vieja("vo_" + archivo, "vo/" + archivo):
            print("  ·", "vo_" + archivo)
            corre(["ffmpeg", "-y", "-v", "error", "-i", os.path.join(MARIANO, "vo", archivo),
                   "-c:a", "libmp3lame", "-b:a", "64k", "-ac", "1",
                   os.path.join(MEDIA, "vo_" + archivo)])

    # Un cuadro fijo por video. Con preload="none" —que es lo que evita que el
    # telefono se baje cinco videos de golpe— el hueco se ve negro hasta que
    # entra en pantalla; el poster lo tapa. El de la Siena ademas nunca arranca
    # solo, porque trae voz.
    for dest, *_ in RECETAS:
        if dest == "casa.mp4":
            continue                      # la portada usa el frame limpio de la casa
        video = os.path.join(MEDIA, dest)
        poster = os.path.join(MEDIA, dest.replace(".mp4", "_poster.jpg"))
        if os.path.exists(poster) and os.path.getmtime(poster) >= os.path.getmtime(video):
            continue
        print("  ·", os.path.basename(poster))
        corre(["ffmpeg", "-y", "-v", "error", "-ss", "1.2", "-i", video,
               "-frames:v", "1", "-q:v", "5", poster])

    # `stride.jpg` ya no se hornea. Lo pedia la seccion "Quien te enseña la casa",
    # que se quito el 2026-08-11 porque ese cuadro es GENERADO —sirve para que
    # camine tres segundos, pero en grande y quieto no es Mariano—. El archivo
    # seguia produciendose para nadie, y cuando Carlos borro esa stride desde el
    # panel el constructor entero dejo de correr por una imagen que no se usa.

    if vieja("casa_poster.jpg", "flyersaanimar/FRAME_LIMPIO_casa.png"):
        print("  · casa_poster.jpg")
        from PIL import Image
        im = Image.open(os.path.join(MARIANO, "flyersaanimar/FRAME_LIMPIO_casa.png"))
        im.thumbnail((1100, 1100))
        im.convert("RGB").save(os.path.join(MEDIA, "casa_poster.jpg"), quality=78, optimize=True)

    for peso in ("Bold", "Regular"):
        d = os.path.join(MEDIA, f"narrow-{peso}.woff2")
        if os.path.exists(d):
            continue
        print("  ·", os.path.basename(d))
        corre([sys.executable, "-m", "fontTools.subset",
               f"{FUENTES}/NimbusSansNarrow-{peso}.otf", f"--text={GLIFOS}",
               "--layout-features=", "--no-hinting", "--desubroutinize",
               "--flavor=woff2", f"--output-file={d}"])


def uri(nombre):
    ruta = os.path.join(MEDIA, nombre)
    tipo = mimetypes.guess_type(ruta)[0] or "application/octet-stream"
    if nombre.endswith(".woff2"):
        tipo = "font/woff2"
    with open(ruta, "rb") as f:
        return f"data:{tipo};base64,{base64.b64encode(f.read()).decode()}"


def duraciones():
    """Los segundos salen de cartera-audios.json, que es donde los dejo el
    medidor. Escribirlos a mano en la plantilla es como se desincronizan."""
    ruta = os.path.join(RAIZ, "cartera-audios.json")
    medidas = {}
    try:
        with open(ruta, encoding="utf8") as f:
            datos = json.load(f)
        for a in datos.get("Mariano", {}).get("audios", []):
            medidas[os.path.basename(a["archivo"])] = a.get("segundos")
    except Exception as e:
        print(f"  aviso: no se pudo leer cartera-audios.json ({e}); se mide con ffprobe")
    for archivo, _, _ in TRAMOS:
        if not medidas.get(archivo):
            r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                "format=duration", "-of", "csv=p=0",
                                os.path.join(MARIANO, "vo", archivo)],
                               capture_output=True, text=True)
            medidas[archivo] = round(float(r.stdout.strip()), 2)
    return medidas


def main():
    print("preparando material…")
    prepara()

    medidas = duraciones()
    voces = [{"src": uri("vo_" + a), "texto": t, "nota": n, "segundos": medidas[a]}
             for a, t, n in TRAMOS]

    with open(os.path.join(AQUI, "plantilla.html"), encoding="utf8") as f:
        html = f.read()

    html = html.replace("{{VOCES_JSON}}", json.dumps(voces, ensure_ascii=False))

    pendientes = set(re.findall(r"\{\{([^}]+)\}\}", html))
    for nombre in pendientes:
        html = html.replace("{{" + nombre + "}}", uri(nombre))

    # Dos salidas del mismo contenido:
    #   casa-siena-landing.html  documento completo, para abrirlo o mandarlo tal cual
    #   casa-siena/artefacto.html  el mismo cuerpo SIN <html>/<head>, que es lo que
    #                              pide el publicador de artefactos (el pone el
    #                              esqueleto; si va duplicado, no lo acepta)
    with open(ARTEFACTO, "w", encoding="utf8") as f:
        f.write(html)
    with open(SALIDA, "w", encoding="utf8") as f:
        f.write('<!DOCTYPE html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n' + html + "\n</html>\n")

    mb = os.path.getsize(SALIDA) / 1e6
    print(f"\n{os.path.relpath(SALIDA, RAIZ)}  ·  {mb:.1f} MB  ·  "
          f"{len(pendientes)} archivos + {len(voces)} tramos de voz")
    print(f"{os.path.relpath(ARTEFACTO, RAIZ)}  ·  para publicar")
    if mb > 15:
        print("⚠ pasa de 15 MB: no se va a poder publicar. Bajale al crf.")


if __name__ == "__main__":
    main()
