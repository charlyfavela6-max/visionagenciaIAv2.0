// Avisos por WhatsApp con WAAPI (el mismo puente que ya usa el resto del
// repo). Si faltan las credenciales la app corre igual: los mensajes se
// quedan en la bitácora y se ven en la web.
const {
  WAAPI_TOKEN = '', WAAPI_INSTANCE = '',
  WAAPI_BASE = 'https://waapi.app/api/v1',
  REPORTE_TEL = '',
} = process.env;

export const activo = Boolean(WAAPI_TOKEN && WAAPI_INSTANCE && REPORTE_TEL);
export const bitacora = [];

// WAAPI tumba la instancia si le llegan ráfagas, así que los mensajes salen
// de uno en uno con un respiro entre cada uno.
let cola = Promise.resolve();

async function manda(texto) {
  const r = await fetch(
    `${WAAPI_BASE}/instances/${WAAPI_INSTANCE}/client/action/send-message`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${WAAPI_TOKEN}`,
        'Content-Type': 'application/json', Accept: 'application/json',
      },
      body: JSON.stringify({
        chatId: `${REPORTE_TEL.replace(/\D/g, '')}@c.us`, message: texto,
      }),
    });
  if (!r.ok) throw new Error(`${r.status} ${(await r.text()).slice(0, 200)}`);
}

export function avisa(texto) {
  const registro = { hora: Date.now(), texto, enviado: false, error: null };
  bitacora.unshift(registro);
  if (bitacora.length > 200) bitacora.pop();
  console.log('[whatsapp]', texto.replace(/\n/g, ' | '));

  cola = cola.then(async () => {
    if (!activo) return;
    try {
      await manda(texto);
      registro.enviado = true;
    } catch (e) {
      registro.error = String(e.message ?? e);
      console.error('[whatsapp] no salió:', registro.error);
    }
    await new Promise((r) => setTimeout(r, 1200));
  });
  return cola;
}
