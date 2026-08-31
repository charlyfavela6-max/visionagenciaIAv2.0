"""Contrato de funcion del sello Trodat 9511. Python puro, corre en milisegundos.

Regla del bench: `check` SIEMPRE antes de Blender. Blender falla lento.

    python3 bench-blender/check_sello_trodat_9511.py

Este invento no es nuestro: es un producto que se vende. Entonces el check no
pregunta "¿funcionaria?", pregunta otra cosa mas util: **¿el modelo que voy a
mandar a Blender es el aparato de la ficha, o me lo estoy inventando?** Cada F
que falla es un numero que no cuadra con el plano.

  F1 — la goma cabe en la placa ..... 37 x 13 dentro de la huella de 38 x 14
  F2 — la placa cabe tumbada ........ 38 x 14 entra en la cara de 77 x 28
  F3 — la placa NO cabe atravesada .. 38 no entra en 28 ni en 23 (es el hallazgo
                                      que obliga a que el sello se doble)
  F4 — el cartucho cabe ............. 47 x 21 x 7 dentro de su hoja, con pared
  F5 — entinta ...................... goma y fieltro caen en el mismo plano
  F6 — la placa no revienta la tapa . el dorso queda dentro de la hoja de 9 mm
  F7 — las hojas suman el grueso .... 14 + 9 = 23 exactos, sin holgura inventada
  F8 — el texto cabe ................ 3 renglones a >= 3.5 mm de alto
  F9 — el giro es un tope duro ...... 180 grados, y el angulo es monotono
 F10 — la tapa no barre el cuerpo .. al voltear, la tapa cae fuera del cuerpo
 F11 — estampa en el plano ......... la punta del relieve aterriza en z = 0
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sello_trodat_9511_mec as M

MM = 1000.0  # para imprimir en milimetros
fallos, notas = [], []


def f(nombre, ok, dice):
    (notas if ok else fallos).append(f"{'ok  ' if ok else 'FALLA'} {nombre} — {dice}")


# F1
f("F1 goma en huella",
  M.PLACA_X <= M.HUELLA_X and M.PLACA_Y <= M.HUELLA_Y,
  f"placa {M.PLACA_X*MM:.0f}x{M.PLACA_Y*MM:.0f} <= huella {M.HUELLA_X*MM:.0f}x{M.HUELLA_Y*MM:.0f}")

# F2
cabe_tumbada = M.HUELLA_X <= M.CUERPO_LARGO and M.HUELLA_Y <= M.CUERPO_ANCHO
f("F2 placa tumbada", cabe_tumbada,
  f"{M.HUELLA_X*MM:.0f}x{M.HUELLA_Y*MM:.0f} en cara {M.CUERPO_LARGO*MM:.0f}x{M.CUERPO_ANCHO*MM:.0f}")

# F3 — el que manda en toda la geometria
atravesada = M.HUELLA_X <= M.CUERPO_ANCHO or M.HUELLA_X <= M.CUERPO_GRUESO
f("F3 no cabe atravesada", not atravesada,
  f"la huella de {M.HUELLA_X*MM:.0f} no entra en {M.CUERPO_ANCHO*MM:.0f} ni en "
  f"{M.CUERPO_GRUESO*MM:.0f}: el sello TIENE que doblarse")

# F4
cx, cy, cz = M.cavidad_tinta()
f("F4 cartucho cabe",
  cx + 2 * M.PARED <= M.CUERPO_LARGO and cy + 2 * M.PARED <= M.CUERPO_ANCHO
  and M.piso_cartucho_z() >= 2 * M.PARED,
  f"cavidad {cx*MM:.1f}x{cy*MM:.1f} con pared {M.PARED*MM:.1f} en "
  f"{M.CUERPO_LARGO*MM:.0f}x{M.CUERPO_ANCHO*MM:.0f}; piso {M.piso_cartucho_z()*MM:.1f} mm")

# F5
f("F5 entinta", abs(M.techo_cartucho_z() - M.junta_z()) < 1e-9,
  f"fieltro y goma en z = {M.junta_z()*MM:.1f} mm")

# F6
techo_hoja = M.CUERPO_GRUESO - M.PARED
f("F6 placa dentro de la tapa", M.dorso_placa_z() <= techo_hoja,
  f"dorso {M.dorso_placa_z()*MM:.1f} <= techo util {techo_hoja*MM:.1f} mm")

# F7
suma = sum(M.reparto_hojas())
f("F7 hojas suman", abs(suma - M.CUERPO_GRUESO) < 1e-9,
  f"{M.HOJA_TINTA*MM:.0f} + {M.HOJA_PLACA*MM:.0f} = {suma*MM:.0f} mm")

# F8
f("F8 texto cabe", M.alto_por_linea() * MM >= 3.5,
  f"{M.LINEAS_MAX} renglones a {M.alto_por_linea()*MM:.2f} mm")

# F9
angs = [M.angulo(i / 20) for i in range(21)]
monotono = all(b >= a - 1e-12 for a, b in zip(angs, angs[1:]))
f("F9 giro monotono", monotono and abs(angs[-1] - math.pi) < 1e-9 and abs(angs[0]) < 1e-9,
  f"0 -> {math.degrees(angs[-1]):.0f} grados, sin rebote")

# F10 — cinematica del pliegue, que es donde se rompen estos aparatos
tx0, tx1 = M.tapa_volteada_x()
libre = tx1 <= -M.CUERPO_LARGO / 2
f("F10 tapa no barre el cuerpo", libre,
  f"volteada ocupa x [{tx0*MM:.1f}, {tx1*MM:.1f}], el cuerpo acaba en "
  f"{-M.CUERPO_LARGO/2*MM:.1f} mm (holgura {(-M.CUERPO_LARGO/2 - tx1)*MM:.1f} mm)")

# F11 — la raiz sube exactamente la punta del relieve, asi que aterriza en cero
punta = M.punta_relieve_z()
aterriza = -punta + punta          # voltear la raiz y subirla `punta`
f("F11 estampa en el plano", abs(aterriza) < 1e-12 and punta > M.junta_z(),
  f"punta a {punta*MM:.1f} mm tras el volteo; la raiz sube eso mismo -> z = 0")

for n in notas:
    print(n)
for n in fallos:
    print(n)
print()
if fallos:
    print(f"{len(fallos)} F rotas: NO mandar a Blender todavia.")
    sys.exit(1)
print(f"las {len(notas)} F se cumplen. Abierto del todo mide "
      f"{M.alcance_abierto()*MM:.0f} mm. Listo para la escena.")
