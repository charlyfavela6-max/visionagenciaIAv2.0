# Hermes en este Codespace

Hermes Agent (Nous Research) para **encargarle tareas en paralelo** con los
modelos gratis de OpenRouter, y opencode como el que programa.

## Donde vive que

| que | donde |
|---|---|
| el programa | `~/.hermes/hermes-agent/` |
| la configuracion | `~/.hermes/config.yaml` |
| **la llave** | `~/.hermes/.env` (permisos 600) — **fuera del repo, no se sube** |
| el comando | `~/.local/bin/hermes` |
| opencode | `~/.config/opencode/opencode.json` |
| el instalador ya revisado | `~/hermes.sh` |

Aqui dentro solo van **guiones y salidas**, nunca la llave.

## Los modelos, y por que estos

La llave de OpenRouter es de **tier gratis**: sin saldo, asi que solo corren los
modelos que acaban en `:free`. OpenRouter lista 18. **Probandolos uno por uno,
solo cinco contestaron**; el resto devolvio 429 (saturado), 502 (proveedor
caido) o 403 (solo para clientes de pago).

Y contestar no es bastante: `minimax-m3` responde bien a una pregunta suelta
pero **se cuelga cuando opencode le pide usar herramientas**. Por eso el que
programa y el que piensa no son el mismo.

| papel | modelo | por que |
|---|---|---|
| Hermes, el que orquesta | `minimax/minimax-m3:free` | **es el unico de los que sirven que VE IMAGENES**, y encima con 1M de contexto |
| subagentes de Hermes | `nvidia/nemotron-3.5-lightning:free` | rapido y barato; van 3 en paralelo |
| opencode | `nvidia/nemotron-3.5-lightning:free` | probado usando herramientas de verdad |
| respaldo | 4 mas, en cadena | cuando el primero da 429 pasa al siguiente en vez de morirse |

Ver la cadena: `hermes fallback list`

## Como se usa

    export PATH="$HOME/.local/bin:$PATH"

    hermes -z "tu pregunta" --cli          # una pregunta, sin interfaz
    hermes                                  # la conversacion completa
    hermes fallback list                    # la cadena de respaldo
    opencode run "arregla X"                # el que programa

Para mirar imagenes hay un guion aparte: `revisa_imagen.py` (ver abajo).

## Trampas

- **`hermes run` no existe.** El prompt suelto va con `-z` y `--cli`.
- Los `:free` se saturan a diario. Si algo falla con 429, no es la llave: es
  que ese modelo esta lleno. La cadena de respaldo esta justo para eso.
- El tier gratis tiene tope de peticiones al dia. Si se acaba, esperar o meter
  saldo en OpenRouter.
- `~/.hermes/` vive en el home, **no en `/workspaces`**: si se recrea el
  Codespace desde cero hay que reinstalar con `bash ~/hermes.sh --skip-setup`.
  Si solo se reinicia, sigue ahi.
