# Catania en Seedream 5.0 — por que salio mal

Revisado el 1 sep 2026 con `hermes/revisa_imagen.py` (minimax-m3, que es el
unico modelo gratis que ve imagenes). Entradas: `catania_corte_base3d.png` (el
3D gris, la estructura buena) contra `casa_seedream.png` (lo que devolvio
Seedream 5.0 Pro).

## Lo que confirme mirando yo las dos imagenes

**1. Cambio el angulo de camara — este es el gordo.** El 3D esta en tres
cuartos, desde arriba y por la izquierda, y se le ve el cerro en terrazas, la
calle de la derecha, las vecinas y el jardin. Seedream lo devolvio **casi de
frente y casi ortogonal**: se perdio la profundidad, el volumen del conjunto y
casi todo el contexto. El prompt decia "Do not move the camera" y aun asi la
movio.

**2. La azotea contradice el prompt al pie de la letra.** El prompt pedia
*"one teak table with chairs"* y una terraza desnuda. Devolvio **dos** juegos de
comedor de madera. Y en el 3D esa terraza tiene una fila de macetas verdes que
desaparecieron.

**3. Se perdio la identidad de los muebles.** El sofa del salon de arriba es
naranja/terracota en el 3D y salio **blanco y curvo**. O sea que no respeto las
fotos de cuarto que se le dieron como referencia de acabados — que era todo el
punto de darle ocho imagenes.

**4. Invento acabados.** La pared de hexagonos de madera detras de la cama
principal no esta ni en el 3D ni en ninguna referencia.

## Lo que dijo el modelo y NO me cuadra

Dio una lista cuarto por cuarto muy segura, pero **se equivoca de piso varias
veces**: dice que el salon con sofa estaba en la planta baja cuando en el 3D
esta arriba. Tambien afirma cosas de la escalera que en el render gris no se
leen. En las plantas bajas el 3D esta muy oscuro y ahi el modelo rellena.

**Como usarlo entonces:** sirve de primera pasada para lo GRUESO — angulo,
azotea, muebles que cambian de color, cosas inventadas. Para el reparto cuarto
por cuarto hay que mirar a ojo, porque ahi alucina con mucho aplomo.

## Que hacer en el siguiente intento

Esto encaja con el metodo que ya estaba acordado en los pendientes y que no se
llego a aplicar:

- **Darle un pase de solo ARISTAS ademas del render gris.** Es lo que amarra la
  geometria y el angulo; sin el, el modelo se despega de la estructura. Era el
  punto (b) del plan y esta corrida no lo llevaba.
- **Una camara DENTRO de cada cuarto** en vez de una sola toma general, que es
  lo que hace que el reparto salga mal.
- Las plantas bajas del 3D salen casi negras. Si el modelo no las ve, se las
  inventa: **subir la luz del render gris** antes de mandarlo.
