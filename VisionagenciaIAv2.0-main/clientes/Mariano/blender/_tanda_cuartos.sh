#!/bin/bash
# Los 16 cuartos de la Catania, cada uno en sus DOS pases que se le dan a la IA:
#   <cuarto>_gris.png     — Workbench solido (luz y volumen)
#   <cuarto>_aristas.png  — plano de lineas, sacado del pase blanco con un
#                           Sobel de ffmpeg. Blender NO lo puede dar: el
#                           WIREFRAME del visor no existe al renderizar.
# El pase blanco intermedio se queda en _blanco/ por si hace falta.
# Un cuarto por Blender, N a la vez, 1 hilo cada uno (mismo trato que el sello).
#   ./_tanda_cuartos.sh [trabajadores]
BL=/tmp/blender-3.3.21-linux-x64/blender
RAIZ=/workspaces/visionagenciaIAv2.0/VisionagenciaIAv2.0-main
BLEND=$RAIZ/clientes/Mariano/de_whatsapp/catania_MEJORADO.blend
GUION=$RAIZ/clientes/Mariano/blender/cuartos_camara.py
SAL=$RAIZ/clientes/Mariano/referencias_3d/cuartos_cam
N=${1:-3}
mkdir -p "$SAL/_log" "$SAL/_blanco"
CUARTOS=$(grep -oP '^\s+"\K[a-z0-9_]+(?=":)' "$GUION")
uno() {
  local c=$1 pase=$2
  local out="$SAL/${c}_${pase}.png"
  [ "$pase" = blanco ] && out="$SAL/_blanco/${c}.png"
  local lineas="$SAL/${c}_aristas.png"
  if [ "$pase" = blanco ] && [ -s "$lineas" ]; then return; fi
  [ "$pase" = gris ] && [ -s "$out" ] && return
  LP_NUM_THREADS=1 OMP_NUM_THREADS=1 xvfb-run -a "$BL" -b -noaudio -t 1 "$BLEND" \
    -P "$GUION" -- "$c" "$out" 810 1440 "$pase" > "$SAL/_log/${c}_${pase}.txt" 2>&1
  if [ "$pase" = blanco ] && [ -s "$out" ]; then
    # el Sobel sobre el blanco: linea negra sobre blanco, cuadrada al gris
    ffmpeg -y -loglevel error -i "$out" \
      -vf "format=gray,sobel,negate,eq=contrast=3.2:brightness=0.30,format=gray" "$lineas"
  fi
  [ -s "$out" ] && echo "OK $c $pase" || echo "FALLO $c $pase"
}
for c in $CUARTOS; do
  for pase in gris blanco; do
    while [ "$(jobs -rp | wc -l)" -ge "$N" ]; do wait -n; done
    uno "$c" "$pase" &
  done
done
wait
echo "TANDA CUARTOS: $(ls "$SAL"/*.png 2>/dev/null | wc -l) imagenes"
