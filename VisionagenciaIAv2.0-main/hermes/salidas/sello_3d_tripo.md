# El sello en 3D con WaveSpeed — 1 sep 2026

`tripo3d/h3.1/image-to-3d`, geometria `detailed`, textura + PBR. **$0.20.**
Tardo ~14 min. Salida: `bench-blender/_ref_sello/mesh/sello_9511_tripo.glb`
(56 MB, 1 malla, **1.95 M caras**).

Entrada: **una sola** imagen — la foto de catalogo del 9511 cerrado, recortada
sobre blanco (`_ref_sello/multi/v1_frente.png`).

## Lo que salio bien

La cara de enfrente esta muy bien: el logo "trodat pocket printy 9511", las
rayas del boton de deslizar, el clip del costado, la carcasa redondeada y el
panel hundido. Todo con su textura.

## Lo que salio mal, y por que

- **La espalda esta lisa y vacia.** No es un fallo del modelo: solo vio UNA
  foto y de la parte de atras no tenia nada, asi que la relleno con una
  superficie sin detalle. Se arregla con multiview y fotos del otro lado.
- **Es una cascara, no un mecanismo.** No tiene cojin, ni placa, ni carro, ni se
  abre. Para animar el Slide & Stamp no sirve.
- **1.95 M caras** es demasiado para animar. Habria que decimar.
- Sale en **rojo y negro** (el del catalogo), no en el verde y azul de Carlos.

## Conclusion: los dos modelos no compiten, se reparten el trabajo

| | el de Blender | el de Tripo |
|---|---|---|
| mecanismo | si, y comprobado con 41 F | no, es una cascara |
| aspecto | cajas redondeadas, color plano | textura, logo, relieves |
| animable | si | no sin decimar |

Lo sensato es **el rig de Blender para el movimiento** y **el mesh de Tripo
como referencia de forma** — o como cuerpo quieto en tomas de producto donde no
se abra.

## Como se lanza otro

Ver `hacer_3d.py`. Detalle que ahorra trabajo: **WaveSpeed SI acepta data URI**
para los endpoints de 3D, aunque el CLAUDE.md diga que los de video no. No hace
falta montar el servidor de puertos publicos.

## Lo que hace falta para el siguiente intento

Fotos de Carlos del sello **cerrado, sobre una hoja blanca, girandolo**, sin la
mano tapando: frente, izquierda, espalda, derecha. Las de sus videos no sirven
— salen con la mano encima y movidas. Con eso va
`tripo3d/h3.1/multiview-to-3d`, que cuesta **$0.10**, la mitad.
