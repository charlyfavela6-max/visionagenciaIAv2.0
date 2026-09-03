# Dónde quedó todo — 3 sep 2026, noche

## ✅ Cerrado y ENVIADO por WhatsApp

### Librito de Rar~Amore (Ángel, 360 Salud Óptima)
Lo que pidió hoy 15:32–16:04 y **necesitaba para imprimir hoy**.

- Letras chicas +25 a +40 % (`INGREDIENTES`, `CONTENIDO`, `PEDIDOS WHATSAPP`,
  «precio normal», `C Á P S U L A S`, `BIENESTAR…`). Las grandes no se movieron.
- «Extracto» en vez de «Cáscara» · «(Resveratrol)» · se agregó **Boswelia serrata**
- Se agregó **CADUCIDAD: DIC 2028**
- Archivos: `RarAmore_librito_CARTA_4up.pdf` (5×10, el que él marcó),
  `RarAmore_5x8_9_CARTA_6up.pdf`, `RarAmore_5x5_CARTA_10up.pdf`
- Scripts: `etiqueta_librito_gpt.py` (el 5×10) y `etiqueta_libro.py` (los demás)

**Bug arreglado de paso en `etiqueta_libro.py`**: `dibuja_panel()` repartía el
sobrante sin comprobar que fuera positivo, así que al crecer la letra los bloques
se ENCIMABAN sin avisar (el 5×5 salió con «CONTIENE» encima del primer
ingrediente). Ahora, si no cabe, encoge el panel completo con un factor global.

### Cake topper de Erick (Stefani)
Tres renders en GPT Image: fondo blanco, montado en pastel y fondo negro.
`clientes/_stefani/topper_erick/topper_erick_gpt_v{1,2,3}.png` + `topper_erick_gpt.py`.
Dicen **ERICK** y **4 AÑOS** (su referencia decía 3; el número va repetido tres
veces en el prompt porque si no lo copia mal). El SVG de 27 capas para Cricut
sigue siendo el de cortar.

## ⚠️ HECHO PERO SIN REVISAR NI ENVIAR

### Etiquetas de BOTE de 360 (`etiqueta_bote.py`)
Se generaron `360_KUIRABA30_IMPRENTA_v6.pdf`, `360_RARAMORE30_…` y
`360_RARAMORE60_…` (164.0 × 66.0 mm, la misma medida de su v5).
**NO se han visto ni mandado.** Hay que abrirlos y revisarlos antes.

Cómo están hechas: las guirnaldas de oro, el sello «100% NATURAL» y el icono de
WhatsApp se **recortan de su propio PDF v5** a 600 dpi (`bote_sprites/`), así que
el arte es idéntico al que ya aprobó y sólo cambia el texto.

Se reacomodó porque con SIETE ingredientes y más grandes ya no cabía como antes:
izquierda ingredientes + modo de uso, derecha útil para + legales, y al pie
`CONTENIDO … · CADUCIDAD: DIC 2028`.

### TRES PREGUNTAS ABIERTAS PARA ÁNGEL
1. **Vitamina D** y **Cáscara de toronja** salieron del librito porque su lista
   nueva ya no las trae. ¿Regresan?
2. Su archivo se llama `RARAMORE_VERDE_**60**` pero adentro dice
   **«CONTENIDO: 30 CÁPSULAS»**. ¿Cuál es?
3. El **Bálsamo** (`44_…pdf`, 254 × 56 mm) **no se tocó**: es un fotomontaje
   (bosque, la figura tarahumara, código de barras) y no hay script suyo en el
   repo — se hizo en el Mac el 24 ago. Para subirle las letras chicas hay que
   reconstruirlo o parchar encima de su PDF. Falta decidir.

## 🔧 A MEDIAS — Catania

`clientes/Mariano/blender/corte_mascaras.py` (nuevo) ya saca del cuadro 1021:
`corte_gris.png` y `corte_blanco.png` en `referencias_3d/corte/`.

**Las máscaras por cuarto TODAVÍA NO SIRVEN.** Van dos bugs, uno arreglado:

1. ~~Los muros son de **7 cm** y la cuadrícula de 15, así que preguntando si el
   CENTRO de la celda caía dentro del muro casi ninguna se marcaba: los 16
   cuartos daban el nivel entero (52 m²).~~ **Arreglado**: ahora se pregunta si
   la celda CRUZA el muro.
2. **Falta**: sólo se apuntan **22 muros** de los ~158 visibles. El filtro por
   nombre (`muro`/`div`) se queda corto — la casa también parte con `ext_*`,
   `a2_muro_*`, `esc_*`, `lam_*` y los `pta_*_marco`. Con 22 la planta baja da
   sólo 2 manchas de 6 cuartos, y la planta alta y la azotea siguen en 1.
   **Siguiente paso: ampliar `apunta_muros()`** para tomar todo lo que sea
   delgado (`min(dx,dy) < 0.35`) y alto (`dz > 1.5`) dentro de la casa, en vez
   de filtrar por nombre.

También quedó guardado `cuartos_camara.py` con `if __name__ == "__main__":`
para poder importarle `CUARTOS` y `limpia()` sin disparar un render.
`_tanda_cuartos.sh` no cambia (Blender corre los `-P` como `__main__`).

**El plan completo** (por qué room-by-room y no una sola pasada) está en la
conversación: ControlNet-union para la geometría → `genfill` con máscara por
cuarto → un pase de nano-banana-pro/edit-multi para unificar luz. ≈ $0.75.

Blender 3.3.21 está de vuelta en `/tmp/blender-3.3.21-linux-x64/` (se borra al
reiniciar el Codespace).

## 🆕 NO EMPEZADO — simulador del algoritmo Andrómeda

Lo pidió esta noche: **jalar las métricas de sus anuncios y del anuncio GANADOR
(el que está desplegado)**, para subir anuncios nuevos y ver cuál puede alcanzar
esas métricas.

Ya se lo había contado a Ángel por WhatsApp (3 sep 02:04 y 04:10: «ya lo logré»),
así que hay algo hecho — **primero hay que encontrarlo en el repo**.

Para las métricas de Meta hay **dos conectores MCP ya montados en la sesión**:
Supermetrics y Windsor.ai. Ése es el camino, no scrapear.
