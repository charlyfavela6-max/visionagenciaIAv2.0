#!/bin/bash
# Segunda pasada: repite los encargos cuya respuesta salio FLACA.
#
# Por que hace falta: con `--cli` solo se imprime el ULTIMO mensaje del agente.
# Si Hermes escribe el reporte "arriba" (en su propia sesion) y termina con un
# resumen, al archivo solo llega el resumen. Le paso 02 asi: 1.5 KB al lado de
# los 12.6 KB del 01. No es que el tema diera para poco.
# El arreglo es pedirle EXPRESAMENTE que el reporte entero vaya en el mensaje
# final, y de paso se le sube el minimo.
export PATH="$HOME/.local/bin:$PATH"
AQUI=/workspaces/visionagenciaIAv2.0/VisionagenciaIAv2.0-main/hermes/investigacion
MINIMO=${1:-4000}
cd "$AQUI"
while IFS='|' read -r nombre brief; do
  [ -z "$nombre" ] && continue
  out="$AQUI/$nombre.md"
  n=$( [ -s "$out" ] && wc -c < "$out" || echo 0 )
  [ "$n" -ge "$MINIMO" ] && continue
  echo "=== REPITO $nombre (tenia $n bytes)  $(date +%H:%M:%S)"
  timeout 900 hermes -z "$brief

Contesta en ESPANOL, en markdown, con encabezados. Nada de relleno ni disculpas:
puros hallazgos y numeros. Si algo no lo sabes, dilo en una linea en vez de
inventarlo.

MUY IMPORTANTE: el REPORTE COMPLETO tiene que ir DENTRO de tu mensaje final,
entero, no un resumen de el. Lo que no este en ese ultimo mensaje se pierde: no
hay nadie leyendo tu sesion. Nada de 'reporte entregado arriba'." --cli \
    > "$out.tmp" 2> "$AQUI/_log_$nombre.txt"
  n2=$( [ -s "$out.tmp" ] && wc -c < "$out.tmp" || echo 0 )
  if [ "$n2" -gt "$n" ]; then mv "$out.tmp" "$out"; echo "OK $nombre ($n2 bytes)"
  else rm -f "$out.tmp"; echo "SIGUE FLACO $nombre ($n2)"; fi
done < "$AQUI/_briefs.txt"
echo "=== SEGUNDA PASADA LISTA $(date +%H:%M:%S)"
