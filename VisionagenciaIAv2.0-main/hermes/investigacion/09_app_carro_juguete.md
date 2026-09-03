Tengo confirmado: Hunyuan 3D v3.1 Rapid cuesta $0.0225/run con37s de mediana. Tengo todo para el informe.

# App para restaurar carros de juguete con generacion 3D + WaveSpeed

## (a) Que quiere de verdad el restaurador y donde se traba

Lo que realmente busca la persona que restaura Hot Wheels, Matchbox, Majorette o carros de lata:

- Identificar el modelo exacto (casting, año, serie) para saber si la pieza vale o no. Los foros Jalopy Journal, el MG Experience y los grupos de Facebook de diecast coinciden en este dolor.
- Diagnosticar daños con fotos: óxido, pintura saltada, tampo (calca) perdido, ejes torcidos, mecanismo de fricción trabado, plásticos amarillentos, partes faltantes (parachoques, espejos, vidrios, antena, ruedas).
- Saber qué partes conseguir. El mercado está fragmentado en 3-5 vendedores principales: Model-Supplies (UK), ModelCarParts (Países Bajos), Recovertoy (Australia), y para calcomanías Black Square (UK) y Toydecals (USA). Eso es lo que mencionan en vbd3.co.uk y en el Jalopy Journal.
- Visualizar el resultado antes de pintar. El proceso tradicional es pintar, arrepentirse, lijar, volver a pintar. Quieren "verlo" antes.
- Llevar un registro del proyecto porque un proyecto dura semanas o meses. Hoy usan blogs, hojas Word, o Excel.

Donde se traban (los "pain points" reales):

1. No encuentran piezas faltantes. Los originales son caros ($25-100+) o no existen.
2. Las calcas originales se rompen al despegarlas o no se consiguen para modelos viejos. Por eso recurren a reimpresiones ($9-24 por set en mycustomhotwheels.com).
3. No saben cómo va a quedar la combinación color + calca antes de pintar.
4. La documentación del proyecto se pierde o se vuelve un caos. iON Classic (gratis pero con anuncios) y Restaurator ($5.99 una vez, no sub) son las apps que existen pero solo documentan; no proponen.
5. Quitar óxido sin picar el metal (los agresivos lo dañan, según eathealthy365.com).
7. Imprimir piezas en 3D que encajen a escala1:64, 1:43, 1:24 (las piezas pequeñas de Hot Wheels tienen ~10.5 mm de diámetro de rueda, tolerancia mínima).

## (b) Flujo de la app

Cinco pasos, una pantalla por paso o un wizard:

1. Foto del carro. Subir3-8 fotos: lateral, otro lateral, frente, atrás, arriba, base, interior, primer plano de tampo. Opcional: foto de referencia del modelo original (catálogo, internet).
2. Estado actual. L'app detecta con vision: pintura, óxido, calcas existentes, partes visibles, faltantes. El usuario confirma/edita (checklist de partes). Guarda el VIN/casting number si lo reconoce.
3. Propuesta de restauración. La app genera 3 variantes (conservador, medio, restauración total) usando text-to-image en modelos como Seedream 4.5 ($0.04/img en WaveSpeed). El usuario elige.
4. Color + calcomanías. Selector de color con código (RAL, Testors, Tamiya). Selector o importador de calca (PNG del usuario o de un pack). La app coloca la calca sobre la propuesta renderizada.
5. Modelo 3D + utilidades. Con la foto aprobada, corre image-to-3D en WaveSpeed (ver sección c). Salidas:
   - STL/OBJ para imprimir piezas faltantes.
   - Vista 3D rotable "antes/después" en el navegador.
   - Plantilla de calca en PNG transparente escalada a la geometría del coche (unwrapping de la malla).

Pantalla adicional: log del proyecto (fotos, costos, partes), galería, valor estimado.

## (c) Modelos para foto→3D, qué sirven y cuáles están en WaveSpeed

No todos los modelos sirven para un carro de juguete pequeño. Los carros son objetos rígidos, hard-surface, escala 1:64 a 1:18, y el usuario sube una sola foto (o pocas). Hay tres cosas que importan: que la geometría sea coherente (no blobs amorfos), que se pueda exportar a STL/OBJ limpio para imprimir, y que el costo por generación sea bajo porque va a iterar varias veces por carro.

Modelos recomendados para este caso, todos disponibles en WaveSpeed AI con precios verificados (USD por corrida):

| Modelo | API en WaveSpeed | Precio/run | Tiempo mediana | Para qué sirve aquí |
|---|---|---|---|---|
| Hunyuan 3D v3.1 Rapid | hunyuan-3d-v3.1/image-to-3d-rapid | $0.0225 | 37 s | Iteración rápida, drafts. Lo más barato. |
| Tripo3D H3.1 Multiview | tripo3d/h3.1/multiview-to-3d | $0.20 | 254 s | El que mejor rinde con 2-4 fotos (recomendado). |
| Tripo3D H3.1 Image | tripo3d/h3.1/image-to-3d | $0.30 | 197 s | Una sola foto, quad topology, PBR. |
| Hunyuan3D V3 | wavespeed-ai/hunyuan3d-v3/image-to-3d | $0.25 | 102 s | PBR, hard-surface bueno. |
| Hunyuan3D V2.1 | wavespeed-ai/hunyuan3d/v2.1 | $0.40 | 120 s | Alternativa más barata al V3. |
| Hyper3D Rodin v2 | hyper3d/rodin-v2/image-to-3d | $0.30 | 147 s | Topología limpia, mejor para edición. |
| Tripo3D V2.5 | tripo3d/v2.5/image-to-3d | $0.30 | 133 s | Rápido, hard-surface decente. |
| Meshy 6 | wavespeed-ai/meshy6/image-to-3d | $0.80 | 212 s | Mejor para PBR fotorrealista. Caro. |
| Hyper3D Rodin v2.5 | hyper3d/rodin-v2.5/image-to-3d | (consultar) | n/d | Más nuevo que v2, mejor detalle. |
| TripoSplat | tripo3d/triposplat/image-to-3d | (consultar) | n/d | Gaussian splat, no imprimible, solo vista. |

Para un carro de juguete, el sweet spot es: Tripo3D H3.1 Multiview (con 2-4 fotos, $0.20) si el usuario puede girar el carro; Hunyuan 3D V3 ($0.25) si solo tiene una foto. Iterar cuesta pocos centavos.

Por qué no los demás para imprimir: TripoSplat devuelve Gaussian splats (no malla imprimible). Meshy 6 es4x más caro ($0.80) y tarda más. Rodin v2 da mejor topología pero cuesta lo mismo que H3.1 y tarda menos, que para hard-surface simple no compensa.

Fuentes verificadas: wavespeed.ai/models/{modelo}, costgoat.com/pricing/hunyuan-3d (cross-check con Fal.ai).

## (d) Para qué sirve el 3D aquí

Tres usos concretos, ordenados por valor para el usuario:

1. Imprimir piezas faltantes en3D. STL/OBJ descargable, escala precisa. Hoy los usuarios bajan piezas sueltas de Printables, Thingiverse, Cults3D ($0-5 por pieza) o imprimen sus propios diseños. El problema es que las réplicas no encajan a la primera porque la geometría base no se conoce. Con un3D scan del carro entero, la pieza faltante se diseña sobre la malla real y encaja. Materiales típicos: resina (SLM) para piezas pequeñas tipo 1:64, FDM (PLA/PETG) para escala 1:24+. Coste de resina por pieza<$0.50, FDM <$0.10.
2. Vista antes/después interactiva. Render WebGL en el navegador (three.js, model-viewer de Google). El usuario gira el modelo en3D, compara con la foto original. Esto vale oro porque evita pintar y arrepentirse.
3. Plantilla de calca. Unwrap UV del modelo, exportar como PNG a escala con transparencias. El usuario la imprime en papel water-slide decal (láminas especiales laser printer, no inkjet) y la pega. Alternativa: enviar el archivo a un servicio como Fusion Scale Graphics ($hasta $39.95 por hoja A6/A5) o mycustomhotwheels.com ($9-24 por set) que imprime las calcas por ti.

Uso extra que se puede vender: medición exacta de partes para identificar el casting y cruzar con bases de datos (Redline Price Guide, WorthPoint, etc.).

## (e) Competencia y precios

No hay un competidor directo que haga foto→3D→restauración de carros de juguete. Lo más cercano:

| Producto | Qué hace | Precio |
|---|---|---|
| baremetalHW (YouTube) | Canal de referencia, 700k+ subs. Restauraciones paso a paso, dónde conseguir partes, qué pintura usar. Es contenido, no producto. | Gratis |
| Restaurator (App Store/Play) | Logbook digital de proyecto: fotos, partes, costos, facturas, documentos, valoración. NO genera propuestas ni 3D. | $5.99 pago único (iOS), $4.99-6.99 en EU |
| iON Classic | Documentación de restauración, comunidad de talleres y dueños. App móvil + web app para talleres. | Gratis con anuncios |
| RestoMag | Documentación de builds para talleres de carros reales (no juguetes), genera "build magazines". | Founding members free; precio público no publicado |
| Resto-Rat (LLC, Texas) | App móvil para coleccionistas y restauradores. Mantenimiento, records, fotos antes/después, presupuesto. NO es 3D. | Fundada 2017, 1 empleado, Free Trial |
| Hy3D Studio (Tencent) | Pipeline3D: image-to-3D, retopología, UVs, texturización, rig, animación. No enfocado a restauración de juguetes. | 20 generaciones gratis/día en plan free |
| Sorceress 3D Studio | Multi-modelo 3D picker (8 modelos). Tampoco enfocado a restauración. | Créditos: TRELLIS 8, Hunyuan 25, Tripo 30-45, Meshy 50-88, Rodin 50 |
| Trify3D,3D AI Studio, Cinevva | Multi-engine 3D. Genéricos, no restauración. | Variable |

Lo que NO existe: una app que tome la foto de un carro de juguete, proponga color + calca, y genere el 3D imprimible + plantilla de calca en un solo flujo.

Servicios de partes sueltas (referencia de mercado para tu pricing):

- mycustomhotwheels.com: calcas 1:64-1:18, $9-24 por set.
- redlineshop.com: calcas Redline, precio variable.
- fsdecals.com (Fusion Scale Graphics): impresión custom de calcas, $hasta $39.95 por hoja.
- randystoyshop.com: partes custom de lata, desde $25 por pieza.
- ModelCarParts (NL), Model-Supplies (UK), Recovertoy (AU): partes reproducción, $5-50 por pieza.
- Cults3D, Printables: modelos 3D 1:64, $0-5 por archivo (varios gratis).
- Servicios de impresión 3D (Craftcloud, Treatstock, Xometry): resina para pieza 1:64 ~$5-15.

Costos de generación 3D en WaveSpeed que pesan en tu economía: por cada carro restaurado el usuario va a iterar 5-10 veces (distintos ángulos, distintas propuestas). Con Hunyuan 3D v3.1 Rapid ($0.0225/run) eso son $0.11-0.22 por carro. Con Tripo3D H3.1 Multiview ($0.20/run) son $1-2 por carro. Margen cómodo para cobrar $5-15 por "render pack" o incluirlo en suscripción.

No verifiqué: precios exactos de Rodin v2.5 y TripoSplat en WaveSpeed (la página mostraba "consultar" al cierre de la búsqueda), ni el plan enterprise de WaveSpeed (Contact Sales). Tampoco el revenue o número de usuarios activos de Resto-Rat. Lo que sí está verificado contra la fuente: precios por run de Hunyuan v3.1 Rapid, Tripo v2.5, Tripo H3.1 image y multiview, Hunyuan v3, Hunyuan v2.1, Rodin v2, Meshy 6; precios de Restaurator en App Store y Play Store ($5.99 y $4.99-6.99).
