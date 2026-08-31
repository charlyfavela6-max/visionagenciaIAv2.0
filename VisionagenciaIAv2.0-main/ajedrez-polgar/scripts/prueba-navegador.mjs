import puppeteer from '/workspaces/visionagenciaIAv2.0/VisionagenciaIAv2.0-main/node_modules/puppeteer/lib/esm/puppeteer/puppeteer.js';
const OUT = process.env.OUT || '/tmp/claude-1000/-workspaces-visionagenciaIAv2-0/76662ecb-9024-45a4-9e0a-3a7bf7cfa110/scratchpad';
const b = await puppeteer.launch({ args: ['--no-sandbox'], defaultViewport: { width: 1320, height: 980 } });
const p = await b.newPage();
const errores = [];
p.on('console', (m) => { if (m.type() === 'error') errores.push(m.text()); });
p.on('pageerror', (e) => errores.push('PAGEERROR ' + e.message));
await p.goto(process.env.URL || 'http://localhost:3000', { waitUntil: 'networkidle0' });
await p.waitForFunction(() => document.getElementById('consejo-san').textContent !== '…', { timeout: 20000 });

const leer = () => p.evaluate(() => ({
  san: document.getElementById('consejo-san').textContent,
  chip: document.getElementById('chip-fuente').textContent,
  fuente: document.getElementById('consejo-fuente').innerText.slice(0, 120),
  porques: [...document.querySelectorAll('#consejo-porques li')].map((l) => l.innerText.slice(0, 70)),
  plan: document.getElementById('consejo-plan').innerText.slice(0, 90),
  kasparov: document.getElementById('kasparov-san').textContent,
  kfuente: document.getElementById('kasparov-fuente').innerText.slice(0, 100),
  fantasmas: document.querySelectorAll('.fantasma-pieza').length,
  flechas: document.querySelectorAll('#capa-flechas line').length,
  piezas: document.querySelectorAll('.pieza').length,
  jugadas: document.querySelectorAll('#lista-jugadas li').length,
  precision: document.getElementById('st-precision').textContent,
  eval: document.getElementById('eval-txt').textContent,
}));

console.log('--- inicio ---'); console.log(await leer());
await p.screenshot({ path: `${OUT}/ajedrez-1.png` });

// modo plan: debe mostrar 3 fantasmas
await p.select('#sel-fantasma', 'plan');
await new Promise((r) => setTimeout(r, 400));
console.log('modo plan, fantasmas:', (await leer()).fantasmas);

for (let i = 0; i < 4; i++) {
  await p.click('#btn-jugar-sugerida');
  await p.waitForFunction(() => document.getElementById('consejo-san').textContent !== '…', { timeout: 30000 });
  await new Promise((r) => setTimeout(r, 700));
  const e = await leer();
  console.log(`\n--- tras jugar (${i + 1}) ---`);
  console.log(`yo: ${e.san} [${e.chip}] fantasmas=${e.fantasmas} flechas=${e.flechas} piezas=${e.piezas} eval=${e.eval}`);
  console.log(`kasparov: ${e.kasparov} | ${e.kfuente.replace(/\n/g, ' ')}`);
  console.log(`porque: ${e.porques[0] || '—'}`);
  console.log(`plan: ${e.plan.replace(/\n/g, ' ')}`);
}
await p.screenshot({ path: `${OUT}/ajedrez-2.png` });

// jugada propia distinta a la sugerida: arrastrar un peon lateral
const jugarClic = async (desde, hasta) => {
  await p.click(`[data-casilla="${desde}"]`);
  await p.click(`[data-casilla="${hasta}"]`);
};
const antes = (await leer()).jugadas;
await jugarClic('a2', 'a3').catch(() => {});
await new Promise((r) => setTimeout(r, 3500));
const desp = await leer();
console.log('\n--- desvio deliberado a2a3 ---');
console.log('lista de jugadas:', antes, '->', desp.jugadas, '| precision:', desp.precision);
console.log('aviso:', await p.evaluate(() => document.getElementById('aviso').innerText.replace(/\n/g, ' ').slice(0, 220)));
await p.screenshot({ path: `${OUT}/ajedrez-3.png` });

// movil
await p.setViewport({ width: 390, height: 844, deviceScaleFactor: 2 });
await new Promise((r) => setTimeout(r, 500));
await p.screenshot({ path: `${OUT}/ajedrez-movil.png`, fullPage: true });

console.log('\nerrores de consola:', errores.length ? errores.slice(0, 8) : 'ninguno');
await b.close();
