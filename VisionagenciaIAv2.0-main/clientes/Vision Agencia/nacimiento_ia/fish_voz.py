#!/usr/bin/env python3
"""El mismo monologo, pero con Fish Audio en vez de Piper.

    python3 fish_voz.py [segundos] [reference_id]

FALTA LA LLAVE. En cuanto este en el `.env` esto corre sin tocar nada:

    FISH_API_KEY=...

Y si quieres una voz concreta del catalogo de Fish, su id:

    FISH_VOICE_ID=...

QUE CAMBIA CONTRA PIPER
-----------------------
Piper corre local, es gratis y no depende de nadie — por eso lo puse primero,
para que hubiera audio esta misma noche. Pero es un modelo chico: la entonacion
es plana de fabrica, y lo que aqui era una ventaja (suena a maquina) en un
monologo largo se vuelve monotono de verdad.

Fish tiene modelo grande y `prosody`, asi que la lentitud se pide en el motor en
vez de arreglarse con ffmpeg despues. Menos procesamiento encima = menos
artefactos.

EL TRATAMIENTO NO SE VA
-----------------------
El registro de doblaje (grave, con cuerpo de cabina) se sigue haciendo despues,
igual que con Piper. Se busca el REGISTRO, no la voz de ningun actor: se le baja
el tono, se le aplana la melodia y se le pone cuerpo. Clonar a la persona que
dobló a Ultron no.
"""
import json
import os
import subprocess
import sys
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, AQUI)
from autorreflexion import GUION, dura           # el texto es el mismo

API = "https://api.fish.audio/v1/tts"


def env(n, x=""):
    ruta = os.path.join(RAIZ, ".env")
    if os.path.exists(ruta):
        for l in open(ruta, encoding="utf8", errors="replace"):
            if l.startswith(n + "="):
                return l.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get(n, x)


def habla(texto, salida, llave, voz, modelo="s2.1-pro"):
    cuerpo = {"text": texto, "format": "mp3", "sample_rate": 44100,
              "prosody": {"speed": 0.82, "volume": 0}}
    if voz:
        cuerpo["reference_id"] = voz
    req = urllib.request.Request(API, data=json.dumps(cuerpo).encode(),
                                 headers={"Authorization": "Bearer " + llave,
                                          "Content-Type": "application/json",
                                          "model": modelo})
    with urllib.request.urlopen(req, timeout=180) as r:
        datos = r.read()
    if len(datos) < 2000:
        raise SystemExit("Fish devolvio muy poco: " + datos[:300].decode("utf8", "replace"))
    open(salida, "wb").write(datos)
    return salida


if __name__ == "__main__":
    objetivo = float(sys.argv[1]) if len(sys.argv) > 1 else 120.0
    voz = sys.argv[2] if len(sys.argv) > 2 else env("FISH_VOICE_ID")
    llave = env("FISH_API_KEY")
    if not llave:
        raise SystemExit("falta FISH_API_KEY en el .env — sin eso no hay como pedirle nada")

    tmp = os.path.join(AQUI, "_fish")
    os.makedirs(tmp, exist_ok=True)
    trozos, hablado = [], 0.0
    for i, (t, sil) in enumerate(GUION):
        m = os.path.join(tmp, "l%02d.mp3" % i)
        w = os.path.join(tmp, "l%02d.wav" % i)
        if not os.path.exists(w):
            habla(t, m, llave, voz)
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", m,
                            "-ar", "44100", "-ac", "1", w], check=True)
        hablado += dura(w)
        trozos.append((w, sil))
        print("  %2d/%d" % (i + 1, len(GUION)), flush=True)

    silencio = sum(s for _, s in GUION)
    factor = max(0.30, (objetivo - hablado) / silencio) if silencio else 1.0
    print("hablado %.1f s · silencios %.1f s · factor %.2f -> %.1f s"
          % (hablado, silencio, factor, hablado + silencio * factor))

    lista = os.path.join(tmp, "orden.txt")
    with open(lista, "w") as f:
        for w, sil in trozos:
            f.write("file '%s'\n" % os.path.abspath(w))
            q = os.path.join(tmp, "sil_%.3f.wav" % (sil * factor))
            if not os.path.exists(q):
                subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                                "-i", "anullsrc=r=44100:cl=mono",
                                "-t", "%.3f" % (sil * factor), q], check=True)
            f.write("file '%s'\n" % os.path.abspath(q))

    crudo = os.path.join(tmp, "crudo.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
                    "-i", lista, "-c", "copy", crudo], check=True)
    final = os.path.join(AQUI, "autorreflexion_fish.mp3")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", crudo,
                    "-af", ("asetrate=44100*0.93,aresample=44100,atempo=1.075,"
                            "acompressor=threshold=-22dB:ratio=4.5:attack=30:release=520,"
                            "equalizer=f=110:t=q:w=1.1:g=3.5,"
                            "equalizer=f=2600:t=q:w=1.6:g=-2,"
                            "highpass=f=62,lowpass=f=11000,"
                            "aecho=0.9:0.85:150:0.10,"
                            "loudnorm=I=-15:TP=-1.5:LRA=8"),
                    "-b:a", "192k", final], check=True)
    print("listo:", final)
