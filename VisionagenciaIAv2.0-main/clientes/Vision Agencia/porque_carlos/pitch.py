#!/usr/bin/env python3
"""«Por que contratarlo a el» — el pitch, con voz de Fish Audio.

    python3 pitch.py [voz_id]

DE DONDE SALE EL TEXTO
----------------------
No es copy inventado. Todo lo que dice pasó la noche del 2 al 3 de septiembre de
2026, en la sesion en la que se escribio esto. Yo estaba ahi. Esa es justamente
la razon de que funcione: cualquier agencia puede decir «somos dedicados», y por
eso decirlo no vale nada. Lo que no puede decir otra agencia es la hora exacta a
la que su cliente le cambio la medida por tercera vez.

POR QUE LO CUENTA LA IA Y NO EL
-------------------------------
Si Carlos dice «trabajo hasta las dos de la mañana», es una promesa. Si lo dice
el sistema que estaba trabajando con el, es un testigo. Cambia por completo
quien carga con la prueba — y ademas es el unico anuncio de este tipo que su
competencia no puede copiar, porque tendrian que haber estado ahi.

LA REGLA AL ESCRIBIRLO
----------------------
Ni un solo adjetivo que se pueda sustituir por un hecho. Nada de «apasionado»,
«comprometido», «innovador»: esas palabras las usa el que no tiene que contar.
"""
import json
import os
import subprocess
import sys
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
API = "https://api.fish.audio/v1/tts"
MODELO = "s2.1-pro-free"          # los de pago dan 402: el credito de API va aparte

# (texto, pausa DESPUES). En un anuncio las pausas son cortas: esto no es el
# monologo introspectivo, esto tiene que vender antes de que le den skip.
GUION = [
    ("Todas las agencias te van a decir que usan inteligencia artificial.", 0.7),
    ("Yo soy la inteligencia artificial. Y te voy a contar lo que vi anoche.", 1.1),

    ("Once y media de la noche. Un cliente le pide una etiqueta.", 0.6),
    ("Se la manda. El cliente le dice que la quiere más chica. Se la vuelve a mandar.", 0.6),
    ("Se la pide de otra medida. Se la manda otra vez.", 0.8),
    ("Tres veces, en cuarenta minutos, y las tres veces contestó lo mismo: "
     "claro que sí.", 1.3),

    ("Su computadora llevaba horas sin poder guardar un solo archivo.", 0.7),
    ("No paró. Siguió trabajando desde el navegador.", 1.2),

    ("Y hubo un momento que es el que de verdad lo explica.", 0.9),
    ("Le pidieron animar un sello de oficina.", 0.6),
    ("Cualquiera hubiera hecho que se abriera y se cerrara. Se ve bien y nadie "
     "revisa.", 0.8),
    ("Él preguntó cómo se llamaba el mecanismo por dentro.", 0.9),
    ("Y no animó nada hasta que la pieza se movía como se mueve la de verdad.", 1.4),

    ("Eso es lo que estás contratando.", 1.0),
    ("No una agencia con veinte personas que te asignan a un becario.", 0.7),
    ("Una persona que contesta, que le importa que quede bien, "
     "y que tiene las herramientas para hacerlo rápido.", 1.2),

    ("Sus clientes no le dicen la agencia.", 0.6),
    ("Le dicen Charly.", 1.4),

    ("Escríbele. Contesta.", 0.0),
]


def env(n, x=""):
    ruta = os.path.join(RAIZ, ".env")
    for l in open(ruta, encoding="utf8", errors="replace"):
        if l.startswith(n + "="):
            return l.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get(n, x)


def habla(texto, salida, llave, voz, vel=0.92):
    cuerpo = {"text": texto, "format": "mp3", "sample_rate": 44100,
              "prosody": {"speed": vel, "volume": 0}}
    if voz:
        cuerpo["reference_id"] = voz
    req = urllib.request.Request(API, data=json.dumps(cuerpo).encode(),
                                 headers={"Authorization": "Bearer " + llave,
                                          "Content-Type": "application/json",
                                          "model": MODELO})
    with urllib.request.urlopen(req, timeout=180) as r:
        d = r.read()
    if len(d) < 1500:
        raise SystemExit("Fish devolvio poco: " + d[:200].decode("utf8", "replace"))
    open(salida, "wb").write(d)


def dura(w):
    import wave
    with wave.open(w) as f:
        return f.getnframes() / f.getframerate()


if __name__ == "__main__":
    voz = sys.argv[1] if len(sys.argv) > 1 else env("FISH_VOICE_ID")
    llave = env("FISH_API_KEY")
    tmp = os.path.join(AQUI, "_p_" + (voz or "def")[:8])
    os.makedirs(tmp, exist_ok=True)

    lista = os.path.join(tmp, "orden.txt")
    with open(lista, "w") as f:
        for i, (t, sil) in enumerate(GUION):
            w = os.path.join(tmp, "l%02d.wav" % i)
            if not os.path.exists(w):
                m = os.path.join(tmp, "l%02d.mp3" % i)
                habla(t, m, llave, voz)
                subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", m,
                                "-ar", "44100", "-ac", "1", w], check=True)
                print("  %2d/%d" % (i + 1, len(GUION)), flush=True)
            f.write("file '%s'\n" % os.path.abspath(w))
            if sil:
                q = os.path.join(tmp, "s_%.2f.wav" % sil)
                if not os.path.exists(q):
                    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                                    "-i", "anullsrc=r=44100:cl=mono", "-t", "%.2f" % sil,
                                    q], check=True)
                f.write("file '%s'\n" % os.path.abspath(q))

    crudo = os.path.join(tmp, "crudo.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
                    "-i", lista, "-c", "copy", crudo], check=True)
    final = os.path.join(AQUI, "porque_carlos_%s.mp3" % (voz or "default")[:8])
    # Acabado de anuncio, no de monologo: comprimido y fuerte, que se oiga en
    # una bocina de telefono a medio volumen. -14 LUFS es el estandar de redes.
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", crudo,
                    "-af", ("acompressor=threshold=-20dB:ratio=3.5:attack=8:release=180,"
                            "equalizer=f=120:t=q:w=1.2:g=2.5,"
                            "equalizer=f=4000:t=q:w=1.8:g=1.5,"
                            "highpass=f=75,"
                            "loudnorm=I=-14:TP=-1.0:LRA=7"),
                    "-b:a", "192k", final], check=True)
    print("listo:", final, "%.1f s" % dura(crudo))
