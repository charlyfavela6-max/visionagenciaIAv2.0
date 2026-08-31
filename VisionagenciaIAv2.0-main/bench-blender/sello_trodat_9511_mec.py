"""Sello Trodat Pocket Printy 9511 — la parte que se puede calcular.

Python puro, sin bpy: lo importan tanto `check_sello_trodat_9511.py` como
`sello_trodat_9511.py` (la escena). Unidades del bench: METROS, RADIANES, Z ARRIBA.

DE DONDE SALEN LOS NUMEROS
--------------------------
Hay dos clases de numero aqui y estan separados a proposito:

  CERTIFICADO — de la ficha del fabricante (Trodat Order Manager, producto 9511
  y cartucho 6/9511). Si algo de esto no cuadra con el plano en la mano, el
  plano manda y se corrige AQUI, no en la escena.

  DEDUCIDO — no viene en la ficha. Sale de una restriccion geometrica o de una
  practica normal de inyeccion, y cada uno dice de cual. Son los que hay que
  mirar con el plano al lado.

EL HALLAZGO QUE MANDA EN LA GEOMETRIA
-------------------------------------
La huella mide 38 x 14 mm y la seccion del cuerpo cerrado mide 28 x 23 mm.
38 no cabe en 28 ni en 23: LA PLACA NO PUEDE IR ATRAVESADA. Tiene que ir
tumbada a lo largo del cuerpo, sobre la cara grande de 77 x 28.

De ahi sale todo lo demas sin elegir nada:

  - Si la placa esta en la cara grande, el fieltro tambien (tiene que besarla
    para entintar). El cartucho mide 47 x 21: cabe en 77 x 28 y en ningun otro
    lado del aparato.
  - Placa y fieltro estan cara a cara y separados por nada cuando esta cerrado.
    Para estampar hay que voltear uno de los dos. Con una sola bisagra, el
    aparato SE DOBLA SOBRE SI MISMO: por eso el 9511 es un sello que se pliega
    y no un Printy 4911 en chico.
  - Cerrado, el fieltro queda tapado por la propia tapa: no hay capuchon que
    perder. Esa es la funcion del grueso de 23 mm.

Costo de falla (regla de SIMPLE.md): A=0 (el actuador es la mano), P=1 (una sola
bisagra), C=0 (nada tiene que pasar en el momento justo: el tope de abierto es
un tope duro), F=2 (inyeccion + placa de goma).
    Costo = 3(0) + 2(1) + 3(0) + 2 = 4.
Es el invento mas barato del bench, y no es un invento: es un producto que se
vende hace anios. Sirve como vara de medir para los demas.
"""

import math

MM = 0.001

# --------------------------------------------------------------------------
# CERTIFICADO — ficha Trodat del 9511 y del cartucho 6/9511
# --------------------------------------------------------------------------
CUERPO_LARGO  = 77.0 * MM     # el eje largo del aparato cerrado
CUERPO_ANCHO  = 28.0 * MM
CUERPO_GRUESO = 23.0 * MM

PLACA_X = 37.0 * MM           # placa de texto MAXIMA (el molde de goma)
PLACA_Y = 13.0 * MM
HUELLA_X = 38.0 * MM          # impresion que anuncia el fabricante
HUELLA_Y = 14.0 * MM

CART_X = 47.0 * MM            # cartucho de tinta 6/9511
CART_Y = 21.0 * MM
CART_Z = 7.0 * MM

LINEAS_MAX = 3                # lineas de texto que admite la ficha

# --------------------------------------------------------------------------
# DEDUCIDO — con el motivo pegado a cada numero
# --------------------------------------------------------------------------
# El grueso de 23 mm es la suma de las dos hojas. La que lleva el cartucho tiene
# que tragarse 7 mm de fieltro mas su piso; la de la placa solo la goma. Reparto
# 14 / 9: es el unico que deja >= 2 mm de piso bajo el cartucho con pared de 1.5.
HOJA_TINTA = 14.0 * MM
HOJA_PLACA = CUERPO_GRUESO - HOJA_TINTA        # 9.0 mm

PARED = 1.5 * MM              # pared tipica de PP/ABS inyectado a esta escala
RADIO_CANTO = 3.0 * MM        # se agarra con dos dedos: canto vivo no se usa

GOMA_ALTO = 2.2 * MM          # goma del sello: cuerpo + relieve
RELIEVE = 0.9 * MM            # lo que sobresale la letra sobre el fondo
PORTAPLACA = 1.6 * MM         # carton/plastico al que va pegada la goma

# La bisagra es un eje paralelo al ANCHO (Y), puesto en un extremo del largo.
# Su centro cae en el plano de la junta entre las dos hojas: es lo unico que
# deja que la tapa gire 180 grados y quede a ras contra el cuerpo.
BISAGRA_R = 2.4 * MM
BISAGRA_Z = HOJA_TINTA                              # el plano de la junta
# El nudillo va POR FUERA del extremo, no retranqueado: si se mete hacia dentro,
# al girar 180 grados la tapa barre el propio cuerpo (lo comprueba F10). Por eso
# en un sello que se pliega la bisagra siempre sobresale — no es adorno.
BISAGRA_X = -(CUERPO_LARGO / 2 + BISAGRA_R)

CORDON_D = 3.2 * MM           # agujero de cordon, en el extremo opuesto
CORDON_BORDE = 4.5 * MM       # centro del agujero al canto

# La placa va centrada a lo largo, no pegada a la bisagra: si estuviera pegada,
# el dedo que empuja caeria fuera de la huella y el sello imprimiria torcido.
PLACA_CENTRO = 0.0            # respecto al centro del cuerpo, sobre el eje largo
CART_CENTRO = 0.0

ABIERTO_RAD = math.pi         # 180 grados: tope duro, la tapa toca el cuerpo


def reparto_hojas():
    """Grueso de cada hoja. La suma es el grueso certificado, sin holgura."""
    return HOJA_TINTA, HOJA_PLACA


def cavidad_tinta():
    """Hueco que hay que vaciar para el cartucho: (x, y, z) interiores."""
    return (CART_X + 0.6 * MM, CART_Y + 0.6 * MM, CART_Z + 0.3 * MM)


def junta_z():
    """Plano donde se tocan las dos hojas. Cerrado, AQUI se besan goma y fieltro:
    la cara que imprime y la cara del fieltro caen las dos en este plano."""
    return HOJA_TINTA


def dorso_placa_z():
    """Z del dorso del portaplaca. Tiene que quedar dentro de la hoja de la placa."""
    return junta_z() + PORTAPLACA + GOMA_ALTO


def techo_cartucho_z():
    """Z de la cara del fieltro. Enrasada con la junta, o no entinta."""
    return junta_z()


def piso_cartucho_z():
    return junta_z() - CART_Z


def angulo(t):
    """Angulo de la bisagra para t en [0, 1]. t=0 cerrado, t=1 estampando."""
    t = max(0.0, min(1.0, t))
    # suavizado de mano: arranca y termina despacio, sin rebote
    return ABIERTO_RAD * (t * t * (3 - 2 * t))


def alcance_abierto():
    """Largo total del aparato abierto del todo, extremo a extremo."""
    return CUERPO_LARGO * 2 + BISAGRA_R * 2


def tapa_volteada_x():
    """Rango en X que ocupa la tapa despues de girar los 180 grados.

    Girar 180 sobre un eje paralelo a Y que pasa por (BISAGRA_X, BISAGRA_Z)
    manda cada punto (x, z) a (2*BISAGRA_X - x, 2*BISAGRA_Z - z)."""
    a = 2 * BISAGRA_X - (-CUERPO_LARGO / 2)
    b = 2 * BISAGRA_X - (CUERPO_LARGO / 2)
    return (min(a, b), max(a, b))


def punta_relieve_z():
    """Z de la punta de las letras una vez volteada la tapa."""
    return 2 * BISAGRA_Z - (junta_z() - RELIEVE)


def alto_por_linea():
    """Milimetros de alto que le tocan a cada renglon dentro de la placa."""
    return PLACA_Y / LINEAS_MAX
