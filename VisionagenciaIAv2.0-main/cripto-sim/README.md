# Cripto Sim

Simulador de operaciones en criptomonedas con **precios reales** y **dinero de
mentiras**. Pones un monto, le das a EJECUTAR y una estrategia cargada empieza a
abrir y cerrar posiciones simuladas contra el mercado en vivo, avisándote por
WhatsApp cada operación y un resumen cada hora.

**No hay llaves de exchange en ninguna parte y el motor no sabe mandar órdenes.**
Todo el resultado es aritmética sobre el precio que publica Coinbase.

## Arrancar

```bash
cp .env.example .env      # WAAPI_TOKEN, WAAPI_INSTANCE, REPORTE_TEL
npm install
npm start                 # http://localhost:8080
```

Sin credenciales de WhatsApp la app corre igual: los avisos se quedan en la web.

## Los datos

Coinbase Exchange, API pública sin llave: WebSocket `ticker` para el precio tick
a tick y `/candles` para la historia. **Binance no sirve desde un servidor en la
nube** — contesta `451 restricted location`. Kraken queda de respaldo.

## La estrategia cargada

Vela de **4 horas**. Tres tácticas long-only a la vez sobre el mismo capital,
cada una etiquetada para poder ver cuál gana y podar la que no:

| táctica | entra | sale |
|---|---|---|
| `tendencia` | EMA20 cruza arriba de la EMA50 | el precio cierra bajo la EMA20 |
| `reversion` | RSI(14) < 30 | el RSI vuelve a 55 |
| `ruptura` | máximo de 5 días con 1.4× volumen | trailing de 4 ATR |

Máximo 4 posiciones, una por moneda, 20% del capital en cada una, comisión 0.1%
por lado más 0.03% de deslizamiento, y un stop de emergencia por operación.

### Lo que dice la historia

`node historia.js 3600 120 && node compara.js` — 116 días reales, 6 monedas:

| táctica | ops | en verde | retorno | ventaja vs comprar y esperar |
|---|---|---|---|---|
| tendencia | 27 | 9/27 | **+20.94%** | **+19.04** |
| ruptura | 28 | 13/28 | +8.95% | +7.06 |
| reversion | 73 | 44/73 | −9.76% | −11.65 |
| las tres juntas | 96 | 50/96 | +3.76% | +1.86 |
| comprar y esperar | — | — | +1.89% | — |

`reversion` está ahí para vigilarla, no porque funcione. Ése es el primer
candidato a podar cuando perfeccionemos.

### Dos cosas que costaron la primera versión entera

1. **La vela tiene que ser larga.** Con velas de 1 minuto el ATR de BTC es ~0.05%
   del precio, así que un objetivo de 2 ATR quedaba en 0.1% — por *debajo* del
   0.2% que se va en comisiones. Perdía por construcción.
2. **Operar poco es la mitad del resultado.** Las versiones que hacían 400–500
   operaciones en 125 días perdían ~20% **sólo en comisiones**. Ésta hace 27.
3. **El trailing stop empeoró todas las variantes** de `tendencia` que se
   probaron (de +21% a +7%): el ruido normal de cripto lo salta antes de que
   corra el movimiento. Por eso `tendencia` sale por la EMA, no por trailing.

## Herramientas para seguir perfeccionando

```bash
node historia.js 3600 120   # baja 120 días de velas de 1 h a estado/
node backtest.js            # corre la estrategia tal como está
node compara.js             # cada táctica sola, contra comprar y esperar
```

## Endpoints

| | |
|---|---|
| `GET /api/estado` | todo: capital, posiciones, cerradas, avisos |
| `POST /api/ejecutar` `{monto}` | arranca una corrida |
| `POST /api/detener` | cierra todo y para |
| `GET /api/salud` | fuente de precios y último tick |
