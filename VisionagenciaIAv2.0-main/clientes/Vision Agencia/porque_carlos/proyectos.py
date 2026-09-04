#!/usr/bin/env python3
"""«Sus mejores proyectos» — el pitch corto, con registro de Ultron.

    python3 proyectos.py [voz_id]

QUE CAMBIO CONTRA EL LARGO
--------------------------
· BREVE: 1:51 -> ~1:05. Un anuncio compite contra el pulgar.
· Ya no cuenta lo que HACE, cuenta lo que HIZO. Los proyectos son la prueba,
  y una prueba concreta vale mas que cinco adjetivos.
· Registro de Ultron, no la VOZ de Ultron. Lo que hace que ese personaje suene
  como suena no es el timbre del actor: es que habla despacio, sin subir nunca
  la voz, y con el cuerpo metalico encima. Eso es procesamiento, y se consigue
  con cualquier voz grave.

EL TRATAMIENTO, PIEZA POR PIEZA
-------------------------------
1. TONO 14 % abajo, con el tempo devuelto — grave sin sonar a cinta lenta;
2. un DOBLAJE de 18 ms casi inaudible: eso es lo que da el «cuerpo de maquina»
   sin caer en el robot de caricatura;
3. una SEGUNDA VOZ una quinta abajo, muy suave, mezclada debajo. Es el truco de
   verdad: dos alturas a la vez es lo que el oido lee como «esto no es una
   persona»;
4. COMPRESOR lento que aplana la melodia. Lo que suena a maquina no es el
   timbre, es la falta de musicalidad;
5. realce en 95 Hz para el pecho, hoyo en 2.6 kHz para quitarle la nasalidad;
6. cola de reverb corta y metalica, no de catedral.
"""
import json
import os
import subprocess
import sys
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
API = "https://api.fish.audio/v1/tts"
MODELO = "s2.1-pro-free"
VOZ_DEF = "048e8b1c52aa4d88bc2d46babcf2a672"     # «A deep strong voice of male»

# Los proyectos son reales y verificables: viven en el repo o estan en vivo.
GUION = [
    ("Deja que te cuente lo que este hombre ha construido.", 1.0),

    ("Una casa que se arma sola.", 0.55),
    ("Los muebles brotan del piso, los muros se desvanecen, "
     "y la cámara sale al mar.", 0.7),
    ("El terreno no está inventado. Lo midió: cuatrocientos sesenta y un metros "
     "hasta el Pacífico.", 1.2),

    ("Un sello de oficina, por dentro.", 0.55),
    ("No lo animó hasta saber cómo se llamaba el mecanismo.", 0.6),
    ("La carrera de la placa no la eligió él. Son cuarenta y cuatro milímetros, "
     "y salen de la geometría.", 1.2),

    ("Una invitación de cumpleaños que se abre con dos dedos, "
     "y los personajes entran cuando la niña los nombra.", 1.0),

    ("Y un sistema que produce video publicitario por medio dólar.", 1.3),

    ("Nada de eso lo hace una agencia de veinte personas.", 0.8),
    ("Lo hace uno solo, con las herramientas correctas, "
     "a las dos de la mañana.", 1.3),

    ("Sus clientes no le dicen la agencia.", 0.55),
    ("Le dicen Charly.", 1.1),
    ("Escríbele.", 0.0),
]


def env(n, x=""):
    for l in open(os.path.join(RAIZ, ".env"), encoding="utf8", errors="replace"):
        if l.startswith(n + "="):
            return l.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get(n, x)


def habla(texto, salida, llave, voz):
    cuerpo = {"text": texto, "format": "mp3", "sample_rate": 44100,
              "reference_id": voz, "prosody": {"speed": 0.84, "volume": 0}}
    req = urllib.request.Request(API, data=json.dumps(cuerpo).encode(),
                                 headers={"Authorization": "Bearer " + llave,
                                          "Content-Type": "application/json",
                                          "model": MODELO})
    with urllib.request.urlopen(req, timeout=180) as r:
        d = r.read()
    if len(d) < 1500:
        raise SystemExit("Fish devolvio poco: " + d[:200].decode("utf8", "replace"))
    open(salida, "wb").write(d)


if __name__ == "__main__":
    voz = sys.argv[1] if len(sys.argv) > 1 else VOZ_DEF
    llave = env("FISH_API_KEY")
    tmp = os.path.join(AQUI, "_pr_" + voz[:8])
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

    # La segunda voz, una quinta abajo. Es lo que el oido lee como «no es una
    # persona»: dos alturas sonando a la vez, cosa que una garganta no hace.
    grave = os.path.join(tmp, "grave.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", crudo,
                    "-af", "asetrate=44100*0.667,aresample=44100,atempo=1.499,volume=0.30",
                    grave], check=True)

    final = os.path.join(AQUI, "proyectos_%s.mp3" % voz[:8])
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", crudo, "-i", grave,
                    "-filter_complex",
                    ("[0:a]asetrate=44100*0.86,aresample=44100,atempo=1.163,"
                     "aecho=0.94:0.42:18:0.28[a];"
                     "[a][1:a]amix=inputs=2:weights=1 0.34:normalize=0,"
                     "acompressor=threshold=-21dB:ratio=5:attack=25:release=460,"
                     "equalizer=f=95:t=q:w=1.0:g=5,"
                     "equalizer=f=2600:t=q:w=1.7:g=-3,"
                     "highpass=f=58,lowpass=f=8200,"
                     "aecho=0.9:0.75:120:0.14,"
                     "loudnorm=I=-14:TP=-1.0:LRA=7"),
                    "-b:a", "192k", final], check=True)
    d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", final], capture_output=True, text=True).stdout.strip()
    print("listo:", final, d + " s")
