#!/bin/bash
# Le pasa a Hermes los 9 briefs, UNO POR UNO.
# En serie a proposito: la llave de OpenRouter es tier gratis y 9 en paralelo
# se comen la cuota al instante (429). Cada salida es un .md aparte.
export PATH="$HOME/.local/bin:$PATH"
AQUI=/workspaces/visionagenciaIAv2.0/VisionagenciaIAv2.0-main/hermes/investigacion
cd "$AQUI"
while IFS='|' read -r nombre brief; do
  [ -z "$nombre" ] && continue
  out="$AQUI/$nombre.md"
  [ -s "$out" ] && { echo "SALTO $nombre"; continue; }
  echo "=== $nombre  $(date +%H:%M:%S)"
  timeout 900 hermes -z "$brief

Contesta en ESPANOL, en markdown, con encabezados. Nada de relleno ni disculpas: puros hallazgos y numeros. Si algo no lo sabes, dilo en una linea en vez de inventarlo." --cli > "$out.tmp" 2> "$AQUI/_log_$nombre.txt"
  if [ -s "$out.tmp" ]; then mv "$out.tmp" "$out"; echo "OK $nombre ($(wc -c < "$out") bytes)"
  else rm -f "$out.tmp"; echo "FALLO $nombre"; fi
done < "$AQUI/_briefs.txt"
echo "=== HERMES TERMINO $(date +%H:%M:%S)"
ls -l "$AQUI"/*.md 2>/dev/null
