#!/usr/bin/env python3
"""La cama de musica de la landing: se sintetiza aqui, no se descarga.

Por que sintetizada y no de un catalogo: ElevenLabs Music quedo sin creditos y
Epidemic Sound pide una cuenta que hay que abrir a mano. Una pista hecha aqui no
cuesta nada, no tiene licencia que vigilar, y como es nuestra se puede volver a
generar con otra duracion o otro tono cambiando una linea.

Lo que se busca NO es una cancion. Es una cama: tiene que poder sonar debajo de
la voz de Mariano sin que uno la note. Por eso:

  - Acordes largos con ataque lento (nada de percusion ni de golpes).
  - Los armonicos altos van pesados hacia abajo, que es lo que hace que suene
    "suave" y no a sintetizador de los ochenta.
  - Se mezcla a -26 dBFS RMS: por debajo de la voz, que anda en -16.
  - Empieza y acaba en el mismo punto del ciclo para que el loop no se oiga.

Correr:  python3 clientes/Mariano/casa-siena/_musica.py
Salida:  clientes/Mariano/casa-siena/media/cama.mp3
"""
import os
import subprocess
import sys

import numpy as np
from scipy.signal import fftconvolve

AQUI = os.path.dirname(os.path.abspath(__file__))
MEDIA = os.path.join(AQUI, "media")
SR = 44100

# 68 pulsos por minuto: el paso al que camina alguien que esta enseñando una
# casa, no el de un anuncio.
BPM = 68
COMPAS = 4 * 60 / BPM          # 3.53 s

# Re mayor. La vuelta es I - vi - IV - V, que es la que no pide resolverse: se
# puede repetir sin que el oido espere un final.
def nota(n):
    """MIDI -> Hz."""
    return 440.0 * 2 ** ((n - 69) / 12)

VUELTA = [
    [50, 57, 62, 66, 69],      # Re mayor 9
    [47, 54, 59, 62, 66],      # si menor 7
    [43, 50, 55, 59, 62],      # Sol mayor 7
    [45, 52, 57, 61, 64],      # La sus -> mayor
]
VUELTAS = 4                    # 4 x 4 compases = ~56 s


def pad(frec, dur, ataque, caida):
    """Un acorde sostenido. La voz es una suma de armonicos con el peso cayendo
    rapido: sin eso suena a onda de sierra y se pelea con la locucion."""
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    v = np.zeros_like(t)
    for k, peso in enumerate((1.0, 0.38, 0.16, 0.07, 0.03), start=1):
        # Dos voces desafinadas 4 centesimas: es lo que da el ancho sin coro.
        for desvio in (-0.04, 0.04):
            v += peso * np.sin(2 * np.pi * frec * k * 2 ** (desvio / 12) * t
                               + np.random.rand() * 6.28)
    # Un vibrato lentisimo para que no suene a nota pegada de una maquina.
    v *= 1 + 0.012 * np.sin(2 * np.pi * 0.23 * t + np.random.rand() * 6.28)

    sobre = np.ones_like(t)
    na, nc = int(SR * ataque), int(SR * caida)
    sobre[:na] = np.linspace(0, 1, na) ** 1.6          # entra despacio
    sobre[-nc:] = np.linspace(1, 0, nc) ** 1.4
    return v * sobre


def campana(frec, dur, cuando, largo=2.4):
    """Una nota suelta que cae. Son las que hacen que la cama tenga a donde
    mirar; van solo en la primera y la tercera vuelta, muy separadas."""
    n = int(SR * largo)
    t = np.linspace(0, largo, n, endpoint=False)
    v = (np.sin(2 * np.pi * frec * t)
         + 0.30 * np.sin(2 * np.pi * frec * 2 * t)
         + 0.10 * np.sin(2 * np.pi * frec * 3.01 * t))
    v *= np.exp(-t * 2.1)
    salida = np.zeros(int(SR * dur))
    i = int(SR * cuando)
    fin = min(len(salida), i + n)
    salida[i:fin] += v[: fin - i]
    return salida


def reverb(x, seg=1.9, mezcla=0.34):
    """Reverb por convolucion con ruido que decae. No es una sala de verdad,
    pero es lo que despega el sonido de la bocina y lo manda al fondo — que es
    justo donde tiene que estar.

    Va por FFT y no con `np.convolve`: son 56 s contra un impulso de 1.9 s, o
    sea 2.5 millones de muestras por 84 mil. Directo son 2e11 multiplicaciones y
    el script no termina ni en cinco minutos; por FFT tarda menos de un segundo.
    """
    n = int(SR * seg)
    imp = np.random.randn(n) * np.exp(-np.linspace(0, 7, n))
    imp[0] = 1.0
    # Se corta lo agudo del impulso promediando de a poco: un reverb brillante
    # se oye por encima de la voz aunque este bajito.
    imp = fftconvolve(imp, np.ones(28) / 28, mode="same")
    mojado = fftconvolve(x, imp, mode="full")[: len(x)]
    mojado /= np.max(np.abs(mojado)) + 1e-9
    return (1 - mezcla) * x + mezcla * mojado


def main():
    np.random.seed(7)                      # que salga igual cada vez que se corra
    dur = COMPAS * len(VUELTA) * VUELTAS
    n = int(SR * dur)
    izq = np.zeros(n)
    der = np.zeros(n)

    for vuelta in range(VUELTAS):
        for i, acorde in enumerate(VUELTA):
            arranque = (vuelta * len(VUELTA) + i) * COMPAS
            # Los acordes se encabalgan medio compas: asi nunca hay un hueco
            # donde se oiga el silencio entre uno y otro.
            largo = COMPAS * 1.5
            trozo = np.zeros(int(SR * largo))
            for j, midi in enumerate(acorde):
                voz = pad(nota(midi), largo, ataque=1.1, caida=1.3)
                trozo += voz * (0.55 if j == 0 else 0.32)
            ini = int(SR * arranque)
            fin = min(n, ini + len(trozo))
            # Las notas de arriba abiertas a los lados, la de abajo al centro.
            izq[ini:fin] += trozo[: fin - ini] * 0.92
            der[ini:fin] += trozo[: fin - ini] * 1.00

        # Campanas solo en la 1a y la 3a vuelta: si van en todas, dejan de ser
        # un detalle y se vuelven la melodia, y entonces compiten con la voz.
        if vuelta % 2 == 0:
            base = vuelta * len(VUELTA) * COMPAS
            for cuando, midi in ((COMPAS * 0.5, 81), (COMPAS * 2.25, 78),
                                 (COMPAS * 3.1, 74)):
                c = campana(nota(midi), dur, base + cuando) * 0.16
                izq += c * 1.00
                der += c * 0.86

    mezcla = np.stack([reverb(izq), reverb(der)])

    # ── Que el loop no se oiga ──────────────────────────────────────────────
    # La pista da la vuelta cada 56 s y una visita a la landing dura mas que
    # eso. Con un fundido de salida y otro de entrada, cada vuelta se oiria como
    # un bache: la musica desaparece y vuelve.
    #
    # Asi que la cola se CRUZA sobre la cabeza: los ultimos 3.5 s se mezclan
    # encima de los primeros 3.5 s y luego se recortan. El final ya no acaba —
    # se convierte en el principio, y como los acordes se encabalgan, ahi hay
    # cola de reverb de los dos lados y el empalme no se distingue.
    cruce = int(SR * 3.5)
    baja = np.linspace(1, 0, cruce) ** 0.5      # curva de potencia constante:
    sube = np.linspace(0, 1, cruce) ** 0.5      # lineal deja un hueco en medio
    mezcla[:, :cruce] = mezcla[:, :cruce] * sube + mezcla[:, -cruce:] * baja
    mezcla = mezcla[:, :-cruce]
    # El fundido de entrada NO va aqui: lo hace la pagina subiendo el volumen
    # cuando uno le da al boton. Si viniera horneado, se oiria en cada vuelta.

    # -26 dBFS RMS. La locucion de Mariano anda por -16, asi que la cama queda
    # 10 dB por debajo: se oye que hay musica, no se oye QUE musica.
    rms = np.sqrt((mezcla ** 2).mean())
    mezcla *= 10 ** (-26 / 20) / (rms + 1e-9)
    pico = np.max(np.abs(mezcla))
    if pico > 0.95:
        mezcla *= 0.95 / pico

    os.makedirs(MEDIA, exist_ok=True)
    salida = os.path.join(MEDIA, "cama.mp3")
    crudo = (np.clip(mezcla.T, -1, 1) * 32767).astype("<i2").tobytes()
    r = subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(SR), "-ac", "2",
         "-i", "pipe:0", "-c:a", "libmp3lame", "-b:a", "96k", salida],
        input=crudo, capture_output=True)
    if r.returncode:
        sys.exit(r.stderr.decode()[-500:])

    print(f"{os.path.relpath(salida, AQUI)}  ·  {dur:.1f} s  ·  "
          f"{os.path.getsize(salida) / 1000:.0f} KB")


if __name__ == "__main__":
    main()
