# El salto que suelta la cuerda en la palabra clave

## Lo que se buscó y lo que hay

Se bajaron **23 videos** de `@charlyfavela1` con `yt-dlp` (Apify se quedó sin
cuota mensual el 2026-08-19) y se revisaron muestreando cuatro cuadros de cada
uno, más un barrido a 2 cuadros/segundo del único candidato —el del gimnasio,
`C0ikTGZsnaH`, que resultó ser un recorrido con espejos, no cuerda.

**Ninguno de los 23 tiene cuerda.** Están en
`clientes/Vision Agencia/ig_videos/`.

Faltan ~17 publicaciones cuyos enlaces no se alcanzaron a guardar. Y no se pueden
volver a pedir:

- **Apify**: `403 platform-feature-disabled · Monthly usage hard limit exceeded`.
- **yt-dlp sobre el perfil o sobre `/reels/`**: `429 Too Many Requests`.
  Instagram no deja listar un perfil sin sesión. Sobre un **post suelto sí baja**
  —así salieron los 23—, pero hace falta el enlace de cada uno.
- **Graph API de Meta**: el token ve 7 páginas y ninguna trae
  `instagram_business_account`. `@charlyfavela1` es cuenta personal, así que por
  ahí no salen sus medios.

**Lo que hace falta de Carlos:** los enlaces de los reels de la cuerda, o los
videos. Con el enlace, `yt-dlp` los baja en segundos.

---

## Por qué no salió filmándolo

El salto no es el problema. El problema es que **soltar la cuerda tiene que caer
en una sílaba**, y esa ventana es de dos o tres cuadros — una décima de segundo.
Acertarle en vivo, saltando y sin aire, es cuestión de suerte; por eso se repite
veinte veces y ninguna queda.

**La regla que lo arregla: no se sincroniza al grabar, se sincroniza al editar.**

Y un detalle que decide si se ve bien o se ve raro: **la cuerda tiene que salir
de las manos DOS O TRES CUADROS ANTES de la consonante, no encima.** El ojo va
por delante del oído; soltando exactamente en el golpe se siente tarde.

---

## Camino A — sólo editando. Gratis, y es el que yo haría primero

1. Graba **dos tomas sueltas**, sin intentar cuadrar nada:
   una saltando parejo, y otra **sólo el suelte** (parado, tira la cuerda al
   piso y se queda viendo a cámara).
2. Graba **el audio aparte**, hablando sentado. Sin aire entrecortado.
3. Saca el instante exacto de la palabra clave:
   ```
   python3 _palabras_whisper.py <audio> palabras.json es
   ```
   Devuelve `{w, t, f}` por palabra: el `t` de la clave es el ancla.
4. Corre el clip del suelte para que la cuerda salga de las manos en
   `t − 0.08 s` (≈ 2 cuadros a 25 fps).
5. **El golpe se pega a mano.** El video-to-audio no clava el instante e inventa
   voces: el impacto va con `adelay` en el cuadro exacto y el ambiente aparte.
6. Y el corte del salto al suelte **va pegado al beat** de la pista, no donde
   caiga: rejilla de 128 BPM (ver `edicionviral.md`).

Coste: **$0**. Todo con ffmpeg.

---

## Camino B — Kling desde una foto, que es lo que pediste

Se puede, pero hay una trampa que decide el resultado:

> **El movimiento sale del CUADRO DE ARRANQUE, no del prompt.**
> Una foto tuya parado te da un clip tieso por mucho que el prompt pida un salto.
> Y con `end_image` la gente no avanza aunque se le ordene.

Así que la foto de entrada **ya tiene que estar en movimiento**: cuerda arriba o
a media vuelta, peso en las puntas de los pies, rodillas dobladas, la mirada ya
en cámara. Eso sale de tu hoja de personaje (`CARLOS_CHARACTER_SHEET.png`)
pidiéndole a GPT Image esa pose exacta — ahí sí es imagen, y es barata.

Después:

- **Kling hace el movimiento**, clip de 5 s (`$0.048/s`). El fondo se ancla con
  objetos reales o se va a la deriva. `pro` no arregla nada.
- **Y lo que va al final del prompt se ignora**: el salto va al principio, el
  lugar y la luz separados y después.
- **El lip sync se encima al final**, no lo hace Kling: `$0.013/s`, no pierde el
  movimiento, y **recorta al audio** — que es justo lo que deja cuadrar la frase
  con el suelte en post en vez de rezar porque Kling lo cronometre.

Coste estimado: ~$0.24 el clip de 5 s + ~$0.07 de lip sync + $0.11 la foto.
**Unos $0.42.**

---

## Cuál conviene

El **A** si tienes las tomas: sale gratis, es tu cuerpo de verdad y el suelte se
puede correr cuadro a cuadro hasta que quede.

El **B** si no quieres volver a grabar, o si el fondo tiene que ser otro.

**Se pueden mezclar**, y probablemente es lo mejor: el salto real tuyo (A) y el
remate hablando generado (B), unidos con un corte al beat.

---

## Lo de la composición de trucos

Para armar una composición con tus trucos hace falta primero **verlos**. Cuando
llegue el material, el orden no se elige a ojo: se mide.

- **Dónde está cada truco**: diferencia entre cuadros consecutivos. Un truco
  cambia mucho más que un salto parejo, así que los picos de esa curva son los
  trucos y los valles el relleno.
- **Cuántos cuadros dura cada uno**, para saber cuáles caben en un corte corto.
- **El orden**: de menor a mayor dificultad no funciona en video corto — el
  primero tiene que ser el segundo mejor, porque los tres primeros segundos
  deciden si se quedan. El mejor va al final.
