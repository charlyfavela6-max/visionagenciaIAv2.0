# Catania — estado del recorrido en Blender

**Fecha:** 2026-08-28 (remate v4, calcado del dron de Mariano). **Archivo de trabajo:** `/Users/juancarlos/catania_LIGERA.blend`
(Blender **3.3.1**, motor **Workbench**, 24 fps).

> **Copia de seguridad con TODO lo de abajo aplicado:**
> `~/Desktop/catania_LIGERA_conclaude.blend` (~12.7 MB).
> Se guardó con `save_as_mainfile(copy=True)`, así que el archivo abierto no se tocó.
> Si Blender se traba y hay que matarlo, **ese es el archivo bueno**.

---

## Lo que quedó aplicado

| # | Qué | Dónde vive |
|---|-----|-----------|
| 1 | Vecinas visibles y blancas como la foto de EasyBroker | colecciones `VECINAS` (45 obj) y `VECINAS_FACHADA` (448 obj), antes ocultas |
| 2 | Calle de concreto claro, banqueta, guarnición, losetas menos amarillas | materiales `VEC_calle`, `VEC_banqueta`, `VEC_guarnicion`, `frente_loseta` |
| 3 | Terreno real hasta el Pacífico | `TER_real`, `TER_escenica`, `MAR`, colección `TERRENO_MAR` |
| 4 | Colonia real de OSM (392 edificios + 79 calles) y relleno | `COLONIA_osm`, `COLONIA_calles`, `COLONIA_relleno` |
| 5 | Las casas que faltaban en la propia calle Catania | `VEC_fila_extra`, `VEC_enfrente_extra`, `frente_losa_extra`, `frente_pasto_extra` |
| 6 | Muebles que brotan del piso, cuarto por cuarto | 65 empties `AP_*` en la colección `APARICION`; los 326 muebles cuelgan de ellos |
| 7 | Muros que se desvanecen en vez de moverse | los 13 de `CEBOLLA_muros`, de vuelta en su sitio real, con Alpha animado |
| 8 | Acercamiento al cuarto de lavado, 2.3× más lento | punto **#13** de la spline del addon |
| 9 | Remate **visto desde el mar**, como el dron de Mariano: la cámara se voltea y retrocede de espaldas los 620 m mirando la casa | puntos con nota `remate al mar`, los pone `remate_al_mar.py` |
| 9b | El vuelo **termina en t 38.0 s**, justo cuando la voz dice "te la enseño cuando quieras". Timeline: **1 → 1021 (42.5 s)**, antes 48 s | `al_mar(duracion=3.4, espera=4.5, desde_t=34.0, arranca_en=34.6)` |
| 9c | Playa y tres líneas de espuma; el DEM hundido donde ya es océano | `remate_al_mar.espuma()` y `hundir_el_oceano()` |
| 10 | **La escena es 9:16 (1080x1920)** y el encuadre del remate está calculado para ese formato | `remate_al_mar.vertical()`; con `sensor_fit AUTO` el formato cambia el FOV, no es un recorte |
| 11 | Mar turquesa, cielo azul y terreno color arena | `remate_al_mar.ambiente()` / `ambiente_deshacer(previo)` |
| 12 | Muebles pintados con la paleta de los clips reales (173 piezas) | `muebles_referencia.pintar()` |
| 13 | El estudio amueblado: librero con libros, monitor, teclado, lámpara, tapete, planta | `muebles_referencia.amueblar_estudio()` |
| 14 | Las vecinas se apagan durante los interiores (t 5–39.5 s) | `muebles_referencia.vecinas_fuera()` / `vecinas_siempre()` |
| 15 | Los muebles que `aplicar()` no "ve" ya brotan en su cuarto, no al final | `muebles_referencia.brotes()` |
| 16 | **Los cuartos, reencuadrados para 9:16**: lente −30% y cámara 1.4 m atrás en los 16 puntos de interiores | `muebles_referencia.abrir_interiores()` |
| 17 | **El mar con olas**: rejilla de 12,382 caras con swell de 1.9 m horneado, avanzando 42 m a lo largo del video, color por profundidad y por pendiente | `mar_y_terreno.mar_de_verdad()` / `mar_liso()` |
| 18 | El terreno pintado por zonas como el video de dron: arena, seco, ocre y manchas verdes | `mar_y_terreno.terreno_como_el_dron()` |
| 22 | **El balcón**: la losa de 1.05 m se conserva (Carlos confirmó que sí se sale; el clip 16 está grabado desde ahí) y se le puso **barandal perimetral** en los 3 lados libres, en las 5 casas | `balcon_frances.arreglar()` / `deshacer()` |
| 23 | **Talud detrás del patio**: había 3 m sin geometría y un salto de 2.4 m entre el jardín (y 19, z −2.85) y el DEM (y 22, z −0.47) | `talud_patio.rellenar()` |
| 24 | Las vecinas vuelven en el frame **827** (t 34.4), no en el 949: el alejamiento arranca en t 34.6 y salía sin las casas de la calle | `muebles_referencia.vecinas_fuera()` |
| 21 | El arranque del remate (t 34.6) mira a la CASA, no al mar: antes había un giro de 180° en 1 s entre ese punto y el siguiente | apuntado con `splineaudio.encarar` |
| 20 | **Giroscopio en el addon**: Giro / Inclinación / Distancia por punto, con flechas y botón "apuntar a lo seleccionado". Reconstruye en vivo | `blender-addon/seedance_blender.py`, `splineaudio.girar` · `encarar` · `leer_orientacion` |
| 19 | **Paredes finas**: 203 muros de 15→7 cm y losas de 20→10 cm. Los de contención y el talud NO se tocan | `paredes_delgadas.adelgazar()` / `engordar()` |

Timeline: **1 → 1021** (42.5 s a 24 fps). El audio dura 38.3 s.

## Los números reales (Google Maps + OSM + SRTM)

- C. Catania: **32.4164301, -117.0912259**.
- El Pacífico queda a **461 m**, rumbo **261°** (≈ oeste) — que en la escena es **+Y**.
  El `MAR` viejo estaba a 88 m: cinco veces más cerca de lo real.
- La calle está a **37 m sobre el nivel del mar**. Equivalencias:
  `escena X = x_real + 3.5`, `escena Y = y_real − 4.5`, `escena Z = z_real − 37`.
- Perfil hacia el mar: 37 m en la calle → 24 m a los 200 m → orilla a los ~490 m.
- La calle **baja 16 m** a lo largo de la fila, por eso las casas nuevas escalonan.

## Peso

| | triángulos |
|---|---|
| visible antes de empezar | 57,000 |
| terreno + colonia | +21,200 |
| fila nueva de la calle | +3,100 |
| **total visible** | **~81,000** |

El `.blend` pasó de 12.4 a 12.7 MB. Las vecinas no pesan: ya existían, sólo estaban ocultas.

---

## Scripts (todos con `deshacer()`)

| archivo | qué hace |
|---|---|
| `terreno_mar.py` | malla SRTM, escénica, mar, colonia de relleno |
| `datos_osm.py` | huellas y calles reales de OSM + sus constructores |
| `fila_calle.py` | las 12+12 casas que faltaban en la calle, escalonadas |
| `muebles_aparecen.py` | los muebles brotan del piso, estilo del reel de Jahaziel Treviño |
| `paredes_y_ritmo.py` | muros que se desvanecen; `solo_ritmo()` estira tramos de tiempo |
| `camara_alejada.py` | remate como llaves sueltas (**ya no se usa**: ahora va en la spline) |
| `remate_al_mar.py` | el remate final, como **puntos del addon** + `Construir`. `listar()`, `al_mar()`, `deshacer()`, `vertical()`, `ambiente()` |
| `muebles_referencia.py` | paleta de los clips reales, estudio amueblado, vecinas fuera, estorbos, brotes y `abrir_interiores()` |
| `mar_y_terreno.py` | el mar con olas y el terreno pintado por zonas |
| `paredes_delgadas.py` | adelgaza muros y losas por la malla, con el espesor previo guardado |
| `balcon_frances.py` | el barandal perimetral del balcón (la losa se conserva) |
| `talud_patio.py` | cose el agujero entre el jardín y el cerro |

Se mandan pegando el texto al conector:

```python
import json, urllib.request
src = open("muebles_aparecen.py").read() + "\n\nresponder(aplicar())\n"
d = json.dumps({"python": src, "meta": {"tipo": "libre"}}).encode()
r = urllib.request.Request("https://conectorblender.onrender.com/api/blender/execute",
                           data=d, headers={"Content-Type": "application/json"})
print(json.loads(urllib.request.urlopen(r, timeout=900).read()))
```

`terreno_mar.py` necesita que `datos_osm.py` vaya pegado **antes**.

---

## Trampas que ya costaron caro

0. **El giroscopio trabaja sobre el punto del CUADRO ACTUAL, no sobre el de la
   lista.** Se apuntó a un objeto bien seleccionado y "no pasaba nada": lo que
   giraba era el punto activo de la lista, que era el último del remate allá
   sobre el mar. Ahora `_punto_objetivo()` toma el punto del frame en el que
   estás y lo selecciona en la lista; el panel además escribe cuál es y avisa
   en rojo si no coincide con el cuadro.

0b. **Apuntar "al mueble más cercano" NO funciona en esta casa.** Se mira en
   SECCIÓN, así que en el cono de visión de cada punto caen muebles de tres
   cuartos: el estudio acabó apuntando al lavabo del baño y el jardín a una
   pata de cama. Se probó y se revirtió; los ángulos buenos están en
   `muebles_referencia.ANGULOS_BASE`. Para reapuntar, el giroscopio.

0a. **El formato NO es un ajuste de salida.** Con `sensor_fit AUTO` los 36 mm
   del sensor se van al lado LARGO. Al pasar de 3:2 a 9:16 el campo horizontal
   de cada punto se cayó de ~60° a ~35° con el mismo lente: por eso todos los
   cuartos se veían cerrados. Cualquier encuadre hay que recalcularlo.

0b. **En Workbench el agua tiene que ser geometría.** No hay reflejos ni
   texturas, así que un plano es siempre una cartulina. Y el modificador Wave
   NO sirve para oleaje: con `height=1.9` sólo levantaba 0.64 m medidos en la
   malla evaluada, porque su envolvente amortigua todo lo que no es el frente
   del pulso. Lo que funciona: hornear senos en la malla y deslizar el objeto.

0c. **El SRTM sobre el océano no da 0, da ruido de 0 a 5 m.** En la escena eso
   queda POR ENCIMA del nivel del mar (−37), así que al poner la cámara sobre el
   agua el primer plano entero salía de tierra café. `hundir_el_oceano()` baja
   esos vértices a −39.5. Mientras se miraba desde tierra no se notaba.

0b. **Lo que tapa un cuarto casi nunca es un muro.** En el estudio eran, en este
   orden: un **closet de la recámara** en la línea de vista, el muro este (que
   `solo_muros()` ignora porque está a 6.7 m y su límite es `CUARTO_M = 6.0`), y
   la **casa vecina**, porque la cámara mira desde x = −1.9 y las casas van cada
   7 m: ese punto cae dentro de la vecina. Antes de mover nada, tirar un rayo
   desde la cámara y ver qué objeto contesta.

1. **Ctrl+Z borra lo que manda el puente.** Se perdieron las vecinas, el remate y un
   estirón de tiempo. Después de cada tanda, guardar.
2. **"Construir / actualizar" del panel rehace la acción de la cámara.** Todo lo que
   se anime *sobre las llaves* de `CAM_RECORRIDO` se pierde. Por eso el remate ahora
   son **puntos de la spline** y no llaves — `remate_al_mar.py` v2 ya los pone así. Después de reconstruir hay que volver a
   correr `paredes_y_ritmo.solo_muros()` y `muebles_aparecen.aplicar()`, porque sus
   tiempos se calculan del recorrido.
3. **Workbench ignora el Alpha del nodo.** Para que un muro se vea desvanecerse hay
   que animar TAMBIÉN `material.diffuse_color[3]` y poner
   `scene.display.shading.color_type = 'MATERIAL'`.
4. **`ob.matrix_world = otro.matrix_world` no se lee de inmediato**: hay que llamar
   `bpy.context.view_layer.update()` antes de medir cajas, o se miden las viejas.
5. **`_visibilidad()` es lo que trabó Blender.** Mueve la cámara y llama
   `world_to_camera_view` una vez por mueble y por muestra (65 × 577 ≈ 37,000
   evaluaciones del depsgraph sobre 1129 objetos). **Hay que reescribirlo** para
   proyectar a mano con la matriz (`M.inverted() @ punto` y la fórmula del lente),
   sin tocar el objeto cámara. Mientras tanto: subir `PASO` de 2 a 6.
6. Al concatenar módulos por el puente, **los nombres chocan**: `fila_calle.aplicar`
   y `paredes_y_ritmo.aplicar` se pisaron y se ejecutó el equivocado. Mandar uno
   por uno, o ejecutar cada archivo en su propio diccionario.

## Lo que falta

- **Iluminación.** En Cycles la escena sale casi de noche: sol en 2.18, mundo casi
  negro, exposición −0.55 con Filmic. Para que se vea como la foto de mediodía hay
  que rehacerla. En Workbench no se nota, pero el render final sí.
- Reescribir `_visibilidad()` (punto 5 de arriba) antes de volver a correrlo.
- Los muros `pb_muro_este_vestidor` y `pb_muro_este_bano` se desvanecen en f435;
  revisar que sea el momento correcto.
