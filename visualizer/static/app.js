"use strict";

// Visualizador de ML-KEM. Todos los datos vienen de la implementación real en Python, que se
// ejecuta en el propio navegador con Pyodide (pyodide-worker.js) y devuelve sus valores intermedios.

const Q = 3329;
const PARAMS = [
  { name: "ML-KEM-512", k: 2, category: 1, aes: "AES-128", failure: "2⁻¹³⁹" },
  { name: "ML-KEM-768", k: 3, category: 3, aes: "AES-192", failure: "2⁻¹⁶⁵" },
  { name: "ML-KEM-1024", k: 4, category: 5, aes: "AES-256", failure: "2⁻¹⁷⁵" },
];

// El reloj del navegador solo tiene una precisión de 0,1–1 ms: cada medida es una tanda de llamadas
const BENCH_REPETITIONS = 30;
const BENCH_BATCH = 10;

const state = { params: "ML-KEM-768", step: 0, tamper: false, data: null, bench: null, loading: false, latticeView: "2d" };

// ------------------------------------------------------------------ Python en el navegador

// python("exchange", ...) llama a la función de Python del mismo nombre en el worker y
// devuelve su resultado ya convertido de JSON
const python = (() => {
  const worker = new Worker("pyodide-worker.js", { type: "module" });
  const pending = new Map();
  let nextId = 0;
  worker.addEventListener("message", ({ data }) => {
    if (data.status) {
      const status = document.getElementById("loadStatus");
      if (status) status.textContent = data.status;
      return;
    }
    const { resolve, reject } = pending.get(data.id);
    pending.delete(data.id);
    if (data.error) reject(new Error(data.error));
    else resolve(JSON.parse(data.result));
  });
  worker.addEventListener("error", (event) => {
    event.preventDefault();
    for (const { reject } of pending.values()) reject(new Error(event.message || "el worker de Pyodide ha fallado"));
    pending.clear();
  });
  return (fn, ...args) => new Promise((resolve, reject) => {
    const id = nextId++;
    pending.set(id, { resolve, reject });
    worker.postMessage({ id, fn, args });
  });
})();

// ------------------------------------------------------------------ utilidades DOM

const $ = (id) => document.getElementById(id);

function h(tag, attrs, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value === null || value === undefined || value === false) continue;
    if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else if (key === "html") node.innerHTML = value;
    else node.setAttribute(key, value === true ? "" : value);
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

const fmt = (n) => n.toLocaleString("es-ES");
const short = (hex, n = 16) => (hex.length > 2 * n ? `${hex.slice(0, 2 * n)}…` : hex);
const paramInfo = () => PARAMS.find((p) => p.name === state.params);

function canvasFor(width, height) {
  // Lienzo nítido en pantallas retina que además se encoge en pantallas estrechas
  const canvas = h("canvas", { class: "chart" });
  const ratio = window.devicePixelRatio || 1;
  canvas.width = width * ratio;
  canvas.height = height * ratio;
  canvas.style.width = "100%";
  canvas.style.maxWidth = `${width}px`;
  canvas.style.aspectRatio = `${width} / ${height}`;
  const ctx = canvas.getContext("2d");
  ctx.scale(ratio, ratio);
  return { canvas, ctx };
}

function pointerPosition(event, canvas, width) {
  const rect = canvas.getBoundingClientRect();
  const scale = width / rect.width;
  return [(event.clientX - rect.left) * scale, (event.clientY - rect.top) * scale];
}

const tooltip = $("tooltip");
function showTip(event, text) {
  tooltip.textContent = text;
  tooltip.style.left = `${event.clientX + 12}px`;
  tooltip.style.top = `${event.clientY + 12}px`;
  tooltip.style.opacity = "1";
}
const hideTip = () => (tooltip.style.opacity = "0");

// ------------------------------------------------------------------ colores

let PAL = {};

function hexToRgb(hex) {
  const v = hex.replace("#", "");
  return [0, 2, 4].map((i) => parseInt(v.slice(i, i + 2), 16));
}

function readPalette() {
  const css = getComputedStyle(document.documentElement);
  const get = (name) => hexToRgb(css.getPropertyValue(name).trim());
  PAL = {
    neg: get("--neg"), pos: get("--pos"), zero: get("--zero"),
    bit0: get("--bit0"), bit1: get("--bit1"), accent: get("--accent"),
    text: css.getPropertyValue("--text").trim(), muted: css.getPropertyValue("--muted").trim(),
    border: css.getPropertyValue("--border").trim(), ok: css.getPropertyValue("--ok").trim(),
    bad: css.getPropertyValue("--bad").trim(), accentCss: css.getPropertyValue("--accent").trim(),
    negCss: css.getPropertyValue("--neg").trim(), posCss: css.getPropertyValue("--pos").trim(),
    surface2: css.getPropertyValue("--surface-2").trim(),
  };
}

const mix = (a, b, t) => a.map((x, i) => Math.round(x + (b[i] - x) * t));
// Paleta "plasma" para valores uniformes en [0, q)
const PLASMA = ["#0d0887", "#5b02a3", "#9a179b", "#cb4678", "#eb7852", "#fbb32f", "#f0f921"].map(hexToRgb);

function uniformColor(v, range = Q) {
  const t = (v / (range - 1)) * (PLASMA.length - 1);
  const i = Math.min(Math.floor(t), PLASMA.length - 2);
  return mix(PLASMA[i], PLASMA[i + 1], t - i);
}

function smallColor(v, maxAbs) {
  if (v === 0) return PAL.zero;
  const t = 0.3 + 0.7 * Math.min(Math.abs(v) / maxAbs, 1);
  return mix(PAL.zero, v < 0 ? PAL.neg : PAL.pos, t);
}

function colorFor(kind, v, maxAbs, range) {
  if (kind === "small") return smallColor(v, maxAbs);
  if (kind === "bits") return v ? PAL.bit1 : PAL.bit0;
  if (kind === "message") return v === 0 ? PAL.bit0 : PAL.bit1;
  return uniformColor(v, range);
}

// ------------------------------------------------------------------ polinomios

// Un polinomio de 256 coeficientes se dibuja como un cuadrado de 16 x 16 celdas
function poly(values, { kind = "uniform", name = "f", caption = null, scale = 4, maxAbs = 3, range = Q } = {}) {
  const canvas = h("canvas", { width: 16, height: 16 });
  canvas.style.width = canvas.style.height = `${16 * scale}px`;
  const ctx = canvas.getContext("2d");
  const image = ctx.createImageData(16, 16);
  values.forEach((v, i) => image.data.set([...colorFor(kind, v, maxAbs, range), 255], i * 4));
  ctx.putImageData(image, 0, 0);
  canvas.addEventListener("mousemove", (event) => {
    const rect = canvas.getBoundingClientRect();
    const col = Math.min(15, Math.floor(((event.clientX - rect.left) / rect.width) * 16));
    const row = Math.min(15, Math.floor(((event.clientY - rect.top) / rect.height) * 16));
    const i = row * 16 + col;
    showTip(event, `${name}, coeficiente ${i} = ${values[i]}`);
  });
  canvas.addEventListener("mouseleave", hideTip);
  return h("figure", { class: "poly", style: "margin:0" }, canvas, caption ? h("figcaption", {}, caption) : null);
}

function vector(polys, name, options) {
  return h("div", { class: "bracket" }, polys.map((p, i) => poly(p, { ...options, name: `${name}[${i}]` })));
}

function matrix(rows, name, options) {
  const grid = h("div", { class: "bracket", style: `grid-template-columns: repeat(${rows.length}, auto)` });
  rows.forEach((row, i) => row.forEach((p, j) => grid.append(poly(p, { ...options, name: `${name}[${i}][${j}]` }))));
  return grid;
}

const term = (node, label) => h("div", { class: "term" }, node, h("span", {}, label));
const op = (symbol) => h("span", { class: "op" }, symbol);

function legend(eta) {
  const plasma = `linear-gradient(90deg, ${PLASMA.map((c) => `rgb(${c})`).join(",")})`;
  const diverging = `linear-gradient(90deg, rgb(${PAL.neg}), rgb(${PAL.zero}), rgb(${PAL.pos}))`;
  return h("div", { class: "legend" },
    h("span", {}, "uniforme: 0", h("i", { style: `background:${plasma}` }), "3328"),
    h("span", {}, `pequeño: −${eta}`, h("i", { style: `background:${diverging}` }), `+${eta}`),
  );
}

// ------------------------------------------------------------------ gráficos

function histogram(values, { min, max, width = 420, height = 130, color, markers = [], bins = null, title = "" }) {
  const { canvas, ctx } = canvasFor(width, height);
  const integerBins = max - min + 1 <= 41;
  const count = bins || (integerBins ? max - min + 1 : 48);
  const binOf = (v) => Math.min(count - 1, Math.max(0, Math.floor(((v - min) / (max - min + 1)) * count)));
  const freq = new Array(count).fill(0);
  values.forEach((v) => freq[binOf(v)]++);
  const top = Math.max(...freq, 1);
  const pad = { l: 8, r: 8, t: 18, b: 22 };
  const plotW = width - pad.l - pad.r;
  const plotH = height - pad.t - pad.b;
  const barW = plotW / count;
  ctx.fillStyle = color || PAL.accentCss;
  freq.forEach((f, i) => {
    const barH = (f / top) * plotH;
    ctx.fillRect(pad.l + i * barW + 0.5, pad.t + plotH - barH, Math.max(1, barW - 1), barH);
  });
  ctx.strokeStyle = PAL.border;
  ctx.beginPath();
  ctx.moveTo(pad.l, pad.t + plotH + 0.5);
  ctx.lineTo(width - pad.r, pad.t + plotH + 0.5);
  ctx.stroke();
  const xOf = (v) => pad.l + ((v - min + 0.5) / (max - min + 1)) * plotW;
  ctx.font = "11px ui-monospace, Menlo, monospace";
  ctx.fillStyle = PAL.muted;
  ctx.textAlign = "left";
  ctx.fillText(String(min), pad.l, height - 6);
  ctx.textAlign = "right";
  ctx.fillText(String(max), width - pad.r, height - 6);
  if (min < 0 && max > 0) {
    ctx.textAlign = "center";
    ctx.fillText("0", xOf(0), height - 6);
  }
  ctx.textAlign = "left";
  ctx.fillStyle = PAL.text;
  ctx.fillText(title, pad.l, 12);
  for (const marker of markers) {
    const x = xOf(marker.value);
    ctx.strokeStyle = marker.color || PAL.bad;
    ctx.setLineDash([4, 3]);
    ctx.beginPath();
    ctx.moveTo(x, pad.t);
    ctx.lineTo(x, pad.t + plotH);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = marker.color || PAL.bad;
    ctx.textAlign = marker.value < 0 ? "left" : "right";
    ctx.fillText(marker.label, x + (marker.value < 0 ? 4 : -4), pad.t + 10);
  }
  return canvas;
}

// Z_q dibujado como un reloj: 0 arriba, q/2 abajo
function zqAngle(x) {
  return -Math.PI / 2 + (2 * Math.PI * x) / Q;
}

function drawClockFrame(ctx, cx, cy, radius, { regions = false } = {}) {
  if (regions) {
    ctx.lineWidth = 40;
    ctx.strokeStyle = `rgba(${PAL.neg}, 0.13)`;
    ctx.beginPath();
    ctx.arc(cx, cy, radius, zqAngle(-Q / 4), zqAngle(Q / 4));
    ctx.stroke();
    ctx.strokeStyle = `rgba(${PAL.pos}, 0.15)`;
    ctx.beginPath();
    ctx.arc(cx, cy, radius, zqAngle(Q / 4), zqAngle((3 * Q) / 4));
    ctx.stroke();
  }
  ctx.lineWidth = 1;
  ctx.strokeStyle = PAL.border;
  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, 2 * Math.PI);
  ctx.stroke();
  ctx.font = "11px ui-monospace, Menlo, monospace";
  ctx.fillStyle = PAL.muted;
  ctx.textAlign = "center";
  const labels = [[0, "0"], [Q / 4, "q/4 ≈ 832"], [Q / 2, "q/2 ≈ 1665"], [(3 * Q) / 4, "3q/4 ≈ 2497"]];
  for (const [value, text] of labels) {
    const a = zqAngle(value);
    const r = radius + 34;
    ctx.fillText(text, cx + r * Math.cos(a), cy + r * Math.sin(a) + 4);
  }
}

function clockDemo() {
  const width = 280;
  const height = 250;
  const { canvas, ctx } = canvasFor(width, height);
  const output = h("div", { class: "note mono" });
  const slider = h("input", { type: "range", min: 0, max: Q - 1, value: 3327, "aria-label": "valor en Z_q" });
  const draw = () => {
    const x = Number(slider.value);
    const centeredValue = x > Q / 2 ? x - Q : x;
    ctx.clearRect(0, 0, width, height);
    drawClockFrame(ctx, width / 2, height / 2, 80);
    const a = zqAngle(x);
    ctx.fillStyle = PAL.accentCss;
    ctx.beginPath();
    ctx.arc(width / 2 + 80 * Math.cos(a), height / 2 + 80 * Math.sin(a), 7, 0, 2 * Math.PI);
    ctx.fill();
    const distance = Math.min(x, Q - x);
    output.textContent = `x = ${x} ≡ ${centeredValue} (mod ${Q}) · distancia a 0 = ${distance} → ${distance <= 3 ? "pequeño" : distance < Q / 4 ? "más bien cerca de 0" : "lejos de 0"}`;
  };
  slider.addEventListener("input", draw);
  draw();
  return h("div", {}, canvas, h("div", { class: "controls-line" }, "x:", slider), output);
}

function ringDemo() {
  let f = [3, -1, 0, 2, 0, 0, 1, -2];
  const boxes = h("div", { class: "ring-boxes" });
  const indices = h("div", { class: "ring-boxes" }, f.map((_, i) => h("span", { class: "idx" }, `X${i ? toSup(i) : "⁰"}`)));
  const render = (flash = false) => {
    boxes.replaceChildren(...f.map((v, i) => h("div", { class: flash && i === 0 && v !== 0 ? "flash" : null }, v)));
  };
  render();
  const multiply = () => {
    f = [-f[7], ...f.slice(0, 7)]; // X·f: todo sube un grado y X⁸ = −1 vuelve con el signo cambiado
    render(true);
  };
  return h("div", {},
    boxes, indices,
    h("div", { class: "controls-line" },
      h("button", { onclick: multiply }, "Multiplicar por X"),
      h("button", { onclick: () => { f = [3, -1, 0, 2, 0, 0, 1, -2]; render(); } }, "Reiniciar")),
    h("p", { class: "note" }, "Cada coeficiente sube un grado. El de X⁷ pasaría a X⁸ = −1, así que entra por la izquierda con el signo cambiado (en rojo). En ML-KEM es igual pero con 256 coeficientes."),
  );
}

function toSup(n) {
  const sup = { 0: "⁰", 1: "¹", 2: "²", 3: "³", 4: "⁴", 5: "⁵", 6: "⁶", 7: "⁷", 8: "⁸", 9: "⁹" };
  return String(n).split("").map((d) => sup[d]).join("");
}

// Punto objetivo ★
function drawStar(ctx, x, y, outer = 10, inner = 4) {
  ctx.fillStyle = PAL.accentCss;
  ctx.beginPath();
  for (let k = 0; k < 10; k++) {
    const r = k % 2 ? inner : outer;
    const a = -Math.PI / 2 + (k * Math.PI) / 5;
    ctx.lineTo(x + r * Math.cos(a), y + r * Math.sin(a));
  }
  ctx.closePath();
  ctx.fill();
}

// La elección se compara con el punto más cercano a ★, que es lo que haría el
// descifrado. Si el ruido es grande, ese punto ya no es el original.
function guessMessage(guess, closest, secret, reveal) {
  let message;
  if (guess === closest) {
    message = closest === secret
      ? "¡Correcto! Ese es el punto más cercano a ★, y es el original."
      : "¡Correcto! Ese es el más cercano a ★, pero no es el original.";
  } else if (guess === secret) {
    message = "Ese es el punto original, pero con este ruido ★ ya está más cerca de otro.";
  } else {
    return "No es ese punto.";
  }
  // Con la solución visible, ese aviso ya lo da el texto de la solución
  return closest !== secret && !reveal ? `${message} Aquí el descifrado fallaría.` : message;
}

function latticeDemo(dimension) {
  const width = 560;
  const height = 340;
  const { canvas, ctx } = canvasFor(width, height);
  const b1 = [46, 9];
  const b2 = [17, 41];
  const origin = [width / 2, height / 2];
  const points = [];
  for (let i = -20; i <= 20; i++) {
    for (let j = -20; j <= 20; j++) {
      const x = origin[0] + i * b1[0] + j * b2[0];
      const y = origin[1] - (i * b1[1] + j * b2[1]);
      if (x > -30 && x < width + 30 && y > -30 && y < height + 30) points.push({ x, y, i, j });
    }
  }
  let shortest = Infinity;
  for (let i = -3; i <= 3; i++) for (let j = -3; j <= 3; j++) {
    if (i || j) shortest = Math.min(shortest, Math.hypot(i * b1[0] + j * b2[0], i * b1[1] + j * b2[1]));
  }
  const nearest = (x, y) => points.reduce((best, p) => (Math.hypot(p.x - x, p.y - y) < Math.hypot(best.x - x, best.y - y) ? p : best));

  let secret;
  let target;
  let guess = null;
  let reveal = false;
  let angle = 0;
  const slider = h("input", { type: "range", min: 5, max: 95, value: 30, "aria-label": "tamaño del ruido" });
  const status = h("p", { class: "note" });

  const placeTarget = () => {
    const noise = (Number(slider.value) / 100) * shortest;
    target = [secret.x + noise * Math.cos(angle), secret.y + noise * Math.sin(angle)];
  };
  const newPuzzle = () => {
    const central = points.filter((p) => Math.hypot(p.x - origin[0], p.y - origin[1]) < 110);
    secret = central[Math.floor(Math.random() * central.length)];
    angle = Math.random() * 2 * Math.PI;
    guess = null;
    reveal = false;
    placeTarget();
    draw();
  };

  function ring(p, color, r = 9) {
    ctx.strokeStyle = color;
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.arc(p.x, p.y, r, 0, 2 * Math.PI);
    ctx.stroke();
  }

  function draw() {
    ctx.clearRect(0, 0, width, height);
    // Vectores base desde el origen
    ctx.lineWidth = 2;
    for (const [b, name] of [[b1, "b₁"], [b2, "b₂"]]) {
      ctx.strokeStyle = PAL.muted;
      ctx.beginPath();
      ctx.moveTo(origin[0], origin[1]);
      ctx.lineTo(origin[0] + b[0], origin[1] - b[1]);
      ctx.stroke();
      ctx.fillStyle = PAL.muted;
      ctx.font = "12px system-ui";
      ctx.fillText(name, origin[0] + b[0] + 4, origin[1] - b[1] - 4);
    }
    ctx.fillStyle = PAL.muted;
    for (const p of points) {
      ctx.beginPath();
      ctx.arc(p.x, p.y, 2.6, 0, 2 * Math.PI);
      ctx.fill();
    }
    const closest = nearest(target[0], target[1]);
    if (reveal) {
      ctx.strokeStyle = PAL.ok;
      ctx.setLineDash([4, 3]);
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(secret.x, secret.y);
      ctx.lineTo(target[0], target[1]);
      ctx.stroke();
      ctx.setLineDash([]);
      ring(secret, PAL.ok, 11);
      if (closest !== secret) ring(closest, PAL.bad, 11);
    }
    if (guess) ring(guess, guess === closest ? PAL.ok : PAL.bad, 7);
    drawStar(ctx, target[0], target[1]);

    const parts = [];
    if (guess) parts.push(guessMessage(guess, closest, secret, reveal));
    if (reveal) {
      parts.push(closest === secret
        ? "Verde: punto original. La línea discontinua es el ruido e."
        : "Con tanto ruido, el punto más cercano a ★ (rojo) ya no es el original (verde): aquí el descifrado fallaría.");
    }
    if (!guess && !reveal) parts.push("Haz clic en el punto gris que creas que está más cerca de ★.");
    parts.push(`En ${state.params} esto mismo ocurre en ${fmt(dimension)} dimensiones.`);
    status.textContent = parts.join(" ");
  }

  canvas.style.cursor = "crosshair";
  canvas.addEventListener("click", (event) => {
    const [x, y] = pointerPosition(event, canvas, width);
    guess = nearest(x, y);
    draw();
  });
  slider.addEventListener("input", () => { placeTarget(); draw(); });
  newPuzzle();

  return h("div", {},
    canvas,
    h("div", { class: "controls-line" },
      "Tamaño del ruido:", slider,
      h("button", { onclick: newPuzzle }, "Nuevo punto"),
      h("button", { onclick: () => { reveal = !reveal; draw(); } }, "Mostrar / ocultar solución")),
    status,
  );
}

// El mismo juego en 3D. La pantalla es plana, así que se dibuja una proyección en
// perspectiva que se puede girar. El ángulo inicial se elige a propósito para que
// otro punto parezca más cercano a ★ que el correcto.
function lattice3dDemo(dimension) {
  const width = 560;
  const height = 340;
  const { canvas, ctx } = canvasFor(width, height);
  const basis = [[44, 6, 10], [10, 40, -8], [-6, 12, 42]];
  const radius = 120;
  const focal = 600;
  const zoom = 1.1;
  const combo = (i, j, k) => [0, 1, 2].map((a) => i * basis[0][a] + j * basis[1][a] + k * basis[2][a]);
  const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);

  const points = [];
  for (let i = -5; i <= 5; i++) for (let j = -5; j <= 5; j++) for (let k = -5; k <= 5; k++) {
    const p = combo(i, j, k);
    if (Math.hypot(...p) <= radius) points.push(p);
  }
  let shortest = Infinity;
  for (let i = -2; i <= 2; i++) for (let j = -2; j <= 2; j++) for (let k = -2; k <= 2; k++) {
    if (i || j || k) shortest = Math.min(shortest, Math.hypot(...combo(i, j, k)));
  }
  const nearest = (t) => points.reduce((best, p) => (dist(p, t) < dist(best, t) ? p : best));
  // Celda fundamental: el paralelepípedo que forman b₁, b₂ y b₃
  const corners = [0, 1, 2, 3, 4, 5, 6, 7].map((n) => combo(n & 1, (n >> 1) & 1, (n >> 2) & 1));
  const edges = [];
  for (let a = 0; a < 8; a++) for (const bit of [1, 2, 4]) if (!(a & bit)) edges.push([a, a | bit]);

  let yaw = 0;
  let pitch = 0;
  let secret;
  let target;
  let closest;
  let direction;
  let guess = null;
  let reveal = false;
  let dragged = false;
  const slider = h("input", { type: "range", min: 5, max: 95, value: 30, "aria-label": "tamaño del ruido" });
  const status = h("p", { class: "note" });

  // Gira (y alrededor del eje vertical, x alrededor del horizontal) y proyecta en perspectiva
  function project(p, y = yaw, x = pitch) {
    const x1 = p[0] * Math.cos(y) + p[2] * Math.sin(y);
    const z1 = -p[0] * Math.sin(y) + p[2] * Math.cos(y);
    const y2 = p[1] * Math.cos(x) - z1 * Math.sin(x);
    const z2 = p[1] * Math.sin(x) + z1 * Math.cos(x);
    const s = (zoom * focal) / (focal - z2);
    return { x: width / 2 + x1 * s, y: height / 2 - y2 * s, z: z2, s };
  }
  const screenDist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
  const apparentNearest = () => {
    const t = project(target);
    return points.reduce((best, p) => (screenDist(project(p), t) < screenDist(project(best), t) ? p : best));
  };

  // Busca el ángulo en el que el punto correcto parece más lejos de ★, en pantalla,
  // comparado con el impostor más cercano
  function trickyAngle() {
    let best = { score: -1, y: 0, x: 0 };
    for (let n = 0; n < 400; n++) {
      const y = Math.random() * 2 * Math.PI;
      const x = (Math.random() - 0.5) * 1.6;
      const t = project(target, y, x);
      let decoy = Infinity;
      for (const p of points) if (p !== closest) decoy = Math.min(decoy, screenDist(project(p, y, x), t));
      const score = screenDist(project(closest, y, x), t) / decoy;
      if (score > best.score) best = { score, y, x };
    }
    yaw = best.y;
    pitch = best.x;
  }

  const placeTarget = () => {
    const noise = (Number(slider.value) / 100) * shortest;
    target = secret.map((v, a) => v + noise * direction[a]);
    closest = nearest(target);
  };
  const newPuzzle = () => {
    const central = points.filter((p) => Math.hypot(...p) < 55);
    secret = central[Math.floor(Math.random() * central.length)];
    const z = 2 * Math.random() - 1;
    const phi = Math.random() * 2 * Math.PI;
    direction = [Math.sqrt(1 - z * z) * Math.cos(phi), Math.sqrt(1 - z * z) * Math.sin(phi), z];
    guess = null;
    reveal = false;
    placeTarget();
    trickyAngle();
    draw();
  };

  function ring(q, color, r = 11, dashed = false) {
    ctx.strokeStyle = color;
    ctx.lineWidth = 2.5;
    ctx.setLineDash(dashed ? [3, 3] : []);
    ctx.beginPath();
    ctx.arc(q.x, q.y, r, 0, 2 * Math.PI);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  function draw() {
    ctx.clearRect(0, 0, width, height);
    const cornersOnScreen = corners.map((c) => project(c));
    ctx.strokeStyle = PAL.border;
    ctx.lineWidth = 1;
    for (const [a, b] of edges) {
      ctx.beginPath();
      ctx.moveTo(cornersOnScreen[a].x, cornersOnScreen[a].y);
      ctx.lineTo(cornersOnScreen[b].x, cornersOnScreen[b].y);
      ctx.stroke();
    }
    const o = project([0, 0, 0]);
    ctx.font = "12px system-ui";
    basis.forEach((b, n) => {
      const q = project(b);
      ctx.strokeStyle = ctx.fillStyle = PAL.muted;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(o.x, o.y);
      ctx.lineTo(q.x, q.y);
      ctx.stroke();
      ctx.fillText(["b₁", "b₂", "b₃"][n], q.x + 4, q.y - 4);
    });

    // De atrás hacia delante; lo lejano, más pequeño y más tenue
    const items = points.map((p) => ({ p, q: project(p) }));
    items.push({ star: true, q: project(target) });
    items.sort((a, b) => a.q.z - b.q.z);
    for (const { star, q } of items) {
      ctx.globalAlpha = Math.min(1, Math.max(0.2, 0.25 + (0.75 * (q.z + radius)) / (2 * radius)));
      if (star) {
        ctx.globalAlpha = 1;
        drawStar(ctx, q.x, q.y, 10 * q.s, 4 * q.s);
        continue;
      }
      ctx.fillStyle = PAL.muted;
      ctx.beginPath();
      ctx.arc(q.x, q.y, 3.2 * q.s, 0, 2 * Math.PI);
      ctx.fill();
    }
    ctx.globalAlpha = 1;

    const apparent = apparentNearest();
    if (reveal) {
      const s = project(secret);
      const t = project(target);
      ctx.strokeStyle = PAL.ok;
      ctx.setLineDash([4, 3]);
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(s.x, s.y);
      ctx.lineTo(t.x, t.y);
      ctx.stroke();
      ctx.setLineDash([]);
      ring(s, PAL.ok);
      if (closest !== secret) ring(project(closest), PAL.bad);
      if (apparent !== closest) ring(project(apparent), PAL.text, 11, true);
    }
    if (guess) ring(project(guess), guess === closest ? PAL.ok : PAL.bad, 7);
    if (!dragged) {
      ctx.fillStyle = PAL.muted;
      ctx.fillText("Arrastra para girar", 10, height - 12);
    }

    const parts = [];
    if (guess) parts.push(guessMessage(guess, closest, secret, reveal));
    if (reveal) {
      parts.push(closest === secret
        ? "Verde: punto original. La línea discontinua es el ruido e."
        : "Con tanto ruido, el punto más cercano a ★ (rojo) ya no es el original (verde): aquí el descifrado fallaría.");
      parts.push(apparent !== closest
        ? "El círculo discontinuo es el punto que, desde este ángulo, parece más cercano en pantalla. Gira y verás cómo cambia."
        : "Desde este ángulo, lo que se ve en pantalla coincide con la realidad.");
    }
    if (!guess && !reveal) parts.push("Haz clic en el punto que creas más cercano a ★. Puedes girar el dibujo arrastrándolo o con las flechas.");
    parts.push(`En ${state.params} esto mismo ocurre en ${fmt(dimension)} dimensiones, y no hay ángulo desde el que mirar.`);
    status.textContent = parts.join(" ");
  }

  canvas.tabIndex = 0;
  canvas.setAttribute("aria-label", "Retículo en 3 dimensiones. Usa las flechas para girarlo.");
  canvas.classList.add("rotatable");
  let drag = null;
  canvas.addEventListener("pointerdown", (event) => {
    canvas.setPointerCapture(event.pointerId);
    drag = { x: event.clientX, y: event.clientY, moved: false };
  });
  canvas.addEventListener("pointermove", (event) => {
    if (!drag) return;
    const dx = event.clientX - drag.x;
    const dy = event.clientY - drag.y;
    if (!drag.moved && Math.hypot(dx, dy) < 4) return;
    drag.moved = dragged = true;
    yaw += dx * 0.01;
    pitch = Math.max(-1.4, Math.min(1.4, pitch + dy * 0.01));
    drag.x = event.clientX;
    drag.y = event.clientY;
    draw();
  });
  canvas.addEventListener("pointerup", (event) => {
    if (drag && !drag.moved) {
      const [x, y] = pointerPosition(event, canvas, width);
      guess = points.reduce((best, p) => (screenDist(project(p), { x, y }) < screenDist(project(best), { x, y }) ? p : best));
      draw();
    }
    drag = null;
  });
  canvas.addEventListener("keydown", (event) => {
    const turn = { ArrowLeft: [-0.12, 0], ArrowRight: [0.12, 0], ArrowUp: [0, -0.12], ArrowDown: [0, 0.12] }[event.key];
    if (!turn) return;
    event.preventDefault();
    event.stopPropagation(); // que las flechas giren el retículo y no cambien de paso
    dragged = true;
    yaw += turn[0];
    pitch = Math.max(-1.4, Math.min(1.4, pitch + turn[1]));
    draw();
  });
  slider.addEventListener("input", () => { placeTarget(); draw(); });
  newPuzzle();

  return h("div", {},
    canvas,
    h("div", { class: "controls-line" },
      "Tamaño del ruido:", slider,
      h("button", { onclick: newPuzzle }, "Nuevo punto"),
      h("button", { onclick: () => { reveal = !reveal; draw(); } }, "Mostrar / ocultar solución")),
    status,
  );
}

function latticeSection(dimension) {
  const views = [["2d", "2D"], ["3d", "3D"]];
  const select = (view) => {
    if (view === state.latticeView) return;
    state.latticeView = view;
    render();
    document.querySelector('.visual-head [aria-checked="true"]')?.focus();
  };
  const picker = h("div", { class: "segmented", role: "radiogroup", "aria-label": "Dimensiones del retículo de juguete" },
    views.map(([view, label]) => h("button", { role: "radio", "aria-checked": String(view === state.latticeView), onclick: () => select(view) }, label)));
  const is3d = state.latticeView === "3d";
  return h("section", {},
    h("div", { class: "visual-head" }, h("h4", {}, `Retículo de juguete en ${is3d ? 3 : 2} dimensiones`), picker),
    is3d ? lattice3dDemo(dimension) : latticeDemo(dimension));
}

// Coeficientes de v' (con máscara) y de w (sin máscara) en el reloj de Z_q
function maskClock(d) {
  const width = 420;
  const height = 400;
  const { canvas, ctx } = canvasFor(width, height);
  const cx = width / 2;
  const cy = height / 2;
  const radius = 140;
  const bits = d.encaps.message_bits;
  const series = { before: d.decaps.v_prime, after: d.decaps.w };
  let current = series.before.slice();
  let animation = null;

  function draw() {
    ctx.clearRect(0, 0, width, height);
    drawClockFrame(ctx, cx, cy, radius, { regions: true });
    ctx.font = "12px system-ui";
    ctx.textAlign = "center";
    ctx.fillStyle = PAL.negCss;
    ctx.fillText("se lee 0", cx, cy - radius + 52);
    ctx.fillStyle = PAL.posCss;
    ctx.fillText("se lee 1", cx, cy + radius - 44);
    current.forEach((value, i) => {
      const a = zqAngle(value);
      const r = radius + (((i * 37) % 15) - 7) * 2.2;
      ctx.fillStyle = bits[i] ? PAL.posCss : PAL.negCss;
      ctx.beginPath();
      ctx.arc(cx + r * Math.cos(a), cy + r * Math.sin(a), 3.2, 0, 2 * Math.PI);
      ctx.fill();
    });
  }

  function animateTo(which) {
    const from = current.slice();
    const to = series[which];
    // Cada punto recorre el camino más corto alrededor del reloj
    const delta = from.map((f, i) => ((((to[i] - f) % Q) + Q + Q / 2) % Q) - Q / 2);
    const start = performance.now();
    cancelAnimationFrame(animation);
    const tick = (now) => {
      const t = Math.min(1, (now - start) / 1100);
      const ease = t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2;
      current = from.map((f, i) => (((f + delta[i] * ease) % Q) + Q) % Q);
      draw();
      if (t < 1) animation = requestAnimationFrame(tick);
    };
    animation = requestAnimationFrame(tick);
    buttons.forEach((b) => b.classList.toggle("primary", b.dataset.which === which));
  }

  const buttons = [
    h("button", { "data-which": "before", onclick: () => animateTo("before") }, "v (con máscara)"),
    h("button", { "data-which": "after", onclick: () => animateTo("after") }, "w = v − sᵀ·u (sin máscara)"),
  ];
  draw();
  // La primera vez se anima solo, para que se vea el efecto sin tener que buscar el botón
  setTimeout(() => animateTo("after"), 700);
  return h("div", {},
    h("div", { class: "controls-line" }, ...buttons),
    canvas,
    h("div", { class: "legend" },
      h("span", { style: `color:${PAL.negCss}` }, "● bit original 0"),
      h("span", { style: `color:${PAL.posCss}` }, "● bit original 1")),
  );
}

function hexView(hex, { compareWith = null, focusByte = null, maxBytes = 48 } = {}) {
  const totalBytes = hex.length / 2;
  let start = 0;
  if (focusByte !== null) start = Math.max(0, Math.min(totalBytes - maxBytes, focusByte - Math.floor(maxBytes / 2)));
  const end = Math.min(totalBytes, start + maxBytes);
  const node = h("div", { class: "hex" });
  if (start > 0) node.append(h("span", { class: "more" }, `… (${start} bytes) `));
  for (let i = start; i < end; i++) {
    const byte = hex.slice(2 * i, 2 * i + 2);
    const differs = compareWith && compareWith.slice(2 * i, 2 * i + 2) !== byte;
    node.append(differs ? h("span", { class: "diff" }, byte) : byte);
  }
  if (end < totalBytes) node.append(h("span", { class: "more" }, ` … (${totalBytes - end} bytes más)`));
  return node;
}

// Tamaño de celda para que una ecuación con `columns` polinomios en fila quepa en el panel
function fitScale(columns, operators = 4) {
  const width = $("visual").clientWidth - 40;
  const perPoly = (width - operators * 34 - 40) / columns - 14;
  return Math.max(2, Math.min(6, Math.floor(perPoly / 16)));
}

const stat = (value, label, cls = "") => h("div", { class: `stat ${cls}` }, h("b", {}, value), h("span", {}, label));

// ------------------------------------------------------------------ pasos

const STEPS = [
  {
    title: "La idea",
    flow: {},
    render(d) {
      const p = d.params;
      const total = d.timings_ms.keygen + d.timings_ms.encaps + d.timings_ms.decaps;
      return {
        explain: `
          <h2>1. Acordar una clave en público</h2>
          <p>Alice y Bob quieren compartir una clave secreta de 32 bytes (256 bits) para cifrar después con AES, pero solo pueden hablar por un canal que cualquiera puede escuchar.</p>
          <p>Hoy eso se hace con RSA o con curvas elípticas (ECDH). Un ordenador cuántico suficientemente grande los rompería con el <b>algoritmo de Shor</b>. ML-KEM se basa en otro problema, <b>Module-LWE</b>, para el que no se conoce ningún ataque eficiente, ni clásico ni cuántico.</p>
          <p>Un <b>KEM</b> (mecanismo de encapsulamiento de claves) son tres algoritmos:</p>
          <ul>
            <li><b>KeyGen</b>: Alice crea un par de claves y publica <code>ek</code>.</li>
            <li><b>Encaps(ek)</b>: Bob genera una clave <code>K</code> y la "encapsula" en un texto cifrado <code>c</code>.</li>
            <li><b>Decaps(dk, c)</b>: Alice abre <code>c</code> con su clave privada y obtiene la misma <code>K</code>.</li>
          </ul>
          <p class="note">Todo lo que verás sale de una ejecución real de la implementación en Python. Usa <kbd>→</kbd> para avanzar.</p>`,
        visual: h("div", {},
          h("section", {},
            h("h4", {}, "Una ejecución completa"),
            h("table", { class: "compare plain" },
              h("tr", {}, h("th", {}, "Quién"), h("th", {}, "Hace"), h("th", {}, "Envía por el canal")),
              h("tr", {}, h("td", {}, "Alice"), h("td", {}, "KeyGen() → (ek, dk)"), h("td", {}, `ek → ${fmt(p.ek_size)} bytes`)),
              h("tr", {}, h("td", {}, "Bob"), h("td", {}, "Encaps(ek) → (K, c)"), h("td", {}, `← c ${fmt(p.ciphertext_size)} bytes`)),
              h("tr", {}, h("td", {}, "Alice"), h("td", {}, "Decaps(dk, c) → K′"), h("td", {}, "—")))),
          h("section", {},
            h("h4", {}, "Resultado"),
            h("div", { class: "keys" },
              h("div", { class: "keybox" }, h("h5", {}, "K de Bob"), h("div", { class: "hex" }, d.encaps.K)),
              h("div", { class: `keybox ${d.decaps.keys_match ? "ok" : "bad"}` }, h("h5", {}, "K′ de Alice"), h("div", { class: "hex" }, d.decaps.K_final))),
            h("div", { class: `verdict ${d.decaps.keys_match ? "ok" : "bad"}` },
              d.decaps.keys_match ? "✓ Las dos claves son idénticas" : "✗ Las claves no coinciden (texto cifrado manipulado)")),
          h("section", {},
            h("h4", {}, "Lo que ve un espía"),
            h("p", {}, "Solo ek y c. Ni dk ni K viajan nunca por el canal."),
            h("div", { class: "stat-row" },
              stat(`${fmt(p.ek_size)} B`, "clave pública ek"),
              stat(`${fmt(p.dk_size)} B`, "clave privada dk"),
              stat(`${fmt(p.ciphertext_size)} B`, "texto cifrado c"),
              stat(`${total.toFixed(2)} ms`, "las tres operaciones")))),
      };
    },
  },
  {
    title: "Retículos",
    flow: {},
    render(d) {
      const dim = d.params.lattice_dimension;
      const dimensions = state.latticeView === "3d"
        ? `
          <p>En 3 dimensiones ya no basta con mirar: la pantalla es plana y la profundidad se pierde. Desde el ángulo inicial, ★ parece pegada a un punto que no es el bueno. Gira el dibujo para comprobarlo.</p>
          <p>${d.params.name} trabaja en <b>${fmt(dim)} dimensiones</b>. Ahí no hay ángulo desde el que mirar: cualquier dibujo en pantalla descarta ${fmt(dim - 2)} de ellas. Y con cada dimensión hay muchos más vecinos entre los que dudar:</p>
          <table class="compare plain">
            <tr><th>Dimensiones</th><th>Vecinos a la distancia mínima</th></tr>
            <tr><td>2</td><td>6</td></tr>
            <tr><td>3</td><td>12</td></tr>
            <tr><td>8</td><td>240</td></tr>
            <tr><td>24</td><td>196&nbsp;560</td></tr>
          </table>
          <p class="note">Son los retículos más compactos de cada dimensión. En ${fmt(dim)} dimensiones no se conoce el número exacto, pero crece exponencialmente, y no se conoce ningún algoritmo eficiente para resolver CVP.</p>`
        : `
          <p>En 2 dimensiones se ve a simple vista. ${d.params.name} trabaja en un retículo de <b>${fmt(dim)} dimensiones</b>, y ahí no se conoce ningún algoritmo eficiente. Pasa a 3D para ver por qué mirar deja de funcionar.</p>`;
      return {
        explain: `
          <h2>2. ¿Qué es un retículo?</h2>
          <p>Un <b>retículo</b> es el conjunto de puntos que se obtienen sumando y restando un número entero de veces unos vectores base. A la derecha, ${state.latticeView === "3d" ? "b₁, b₂ y b₃ generan todos los puntos grises; la caja es la celda que se repite" : "b₁ y b₂ generan todos los puntos grises"}.</p>
          <p>El problema difícil: te doy un punto ★ que está <i>cerca</i> de un punto del retículo, pero no encima. ¿Cuál es el punto del retículo más cercano? Es el <b>problema del vector más cercano (CVP)</b>.</p>
          ${dimensions}
          <p>La relación con ML-KEM: la clave pública es</p>
          <div class="formula">t = A·s + e</div>
          <p>Sin el error <code>e</code>, se despejaría <code>s</code> por Gauss en microsegundos. Con <code>e</code>, <code>t</code> es "un punto cerca del retículo" y recuperar <code>s</code> equivale a resolver CVP. Eso es <b>LWE</b> (Learning With Errors).</p>
          <p class="note">Sube el ruido: si es demasiado grande, el punto más cercano deja de ser el original. Por eso en ML-KEM el ruido es pequeño: suficiente para esconder el secreto, insuficiente para estropear el descifrado.</p>`,
        visual: latticeSection(dim),
      };
    },
  },
  {
    title: "El anillo R_q",
    flow: {},
    render(d) {
      const p = d.params;
      const s0 = d.keygen.s[0];
      const t0 = d.keygen.t[0];
      return {
        explain: `
          <h2>3. Los números con los que trabaja</h2>
          <p><b>Z<sub>q</sub></b>: enteros módulo q = 3329. Al llegar a 3329 se vuelve a 0, como en un reloj. 3328 es lo mismo que −1: por eso se dice que 3328 es un número "pequeño".</p>
          <p><b>R<sub>q</sub> = Z<sub>q</sub>[X]/(X²⁵⁶ + 1)</b>: polinomios de 256 coeficientes en Z<sub>q</sub>. Al multiplicar, X²⁵⁶ se sustituye por −1.</p>
          <p><b>Módulo R<sub>q</sub><sup>k</sup></b>: vectores de k polinomios. Ese <b>k</b> es lo que eliges arriba con <kbd>1</kbd> <kbd>2</kbd> <kbd>3</kbd>: cuántos polinomios tiene cada vector y el tamaño de la matriz A (k×k). Ahora k = ${p.k}, así que el retículo tiene ${p.k} × 256 = ${fmt(p.lattice_dimension)} dimensiones.</p>
          <p>Por eso se llama <b>Module</b>-LWE: es LWE con matrices y vectores, pero cuyos elementos son polinomios. Así una matriz de ${fmt(p.lattice_dimension)}×${fmt(p.lattice_dimension)} números se describe con solo ${p.k}×${p.k} polinomios, y las claves son mucho más pequeñas.</p>
          <p class="note">En el resto de pasos cada polinomio se dibuja como un cuadrado de 16×16 celdas (256 coeficientes). Pasa el ratón por encima para ver cada valor.</p>`,
        visual: h("div", {},
          h("section", {}, h("h4", {}, "Z_q como un reloj de 3329 horas"), clockDemo()),
          h("section", {}, h("h4", {}, "Multiplicar por X en un anillo de juguete (8 coeficientes, X⁸ = −1)"), ringDemo()),
          h("section", {},
            h("h4", {}, "Polinomio pequeño frente a polinomio uniforme"),
            h("div", { class: "row" },
              poly(s0, { kind: "small", name: "s[0]", caption: "s[0]: secreto", scale: 7, maxAbs: p.eta1 }),
              histogram(s0, { min: -p.eta1, max: p.eta1, width: 220, height: 112, title: "valores de s[0]" })),
            h("div", { class: "row", style: "margin-top:12px" },
              poly(t0, { kind: "uniform", name: "t[0]", caption: "t[0]: público", scale: 7 }),
              histogram(t0, { min: 0, max: Q - 1, width: 220, height: 112, bins: 24, title: "valores de t[0]" })),
            legend(p.eta1))),
      };
    },
  },
  {
    title: "KeyGen",
    flow: { alice: true, ek: true },
    render(d) {
      const p = d.params;
      const kg = d.keygen;
      const scale = fitScale(p.k + 3);
      return {
        explain: `
          <h2>4. KeyGen: Alice crea sus claves</h2>
          <p>1. Toma 32 bytes aleatorios <code>d</code> y calcula <code>(ρ, σ) = G(d ‖ k)</code>. Añadir k lo introdujo la versión final del estándar (separación de dominio).</p>
          <p>2. A partir de <code>ρ</code> genera la matriz pública <b>Â</b> de ${p.k}×${p.k} polinomios uniformes, directamente en dominio NTT.</p>
          <p>3. A partir de <code>σ</code> genera el secreto <b>s</b> y el error <b>e</b>: coeficientes pequeños, entre −η₁ y η₁ (η₁ = ${p.eta1}).</p>
          <p>4. Calcula</p>
          <div class="formula">t = A·s + e</div>
          <p>Fíjate en los colores: s y e solo toman ${2 * p.eta1 + 1} valores (de −${p.eta1} a ${p.eta1}), pero t, que se calcula a partir de ellos, parece ruido uniforme. Ese es el corazón de LWE: t no revela s.</p>
          <div class="formula">ek = (t, ρ) → 384·${p.k} + 32 = ${fmt(p.ek_size)} bytes<br>dk = (s, ek, H(ek), z) → ${fmt(p.dk_size)} bytes</div>
          <p class="note">La <b>NTT</b> (transformada teórico-numérica) es a los polinomios lo que la FFT a las señales: convierte cada multiplicación de polinomios (256² productos) en 128 productos pequeños. Por eso Â se guarda "ya transformada".</p>`,
        visual: h("div", {},
          h("section", {},
            h("h4", {}, `t = A·s + e  (k = ${p.k})`),
            h("div", { class: "equation" },
              term(matrix(kg.a_hat, "Â", { kind: "uniform", scale }), "Â (dominio NTT)"),
              op("·"),
              term(vector(kg.s, "s", { kind: "small", scale, maxAbs: p.eta1 }), "s secreto"),
              op("+"),
              term(vector(kg.e, "e", { kind: "small", scale, maxAbs: p.eta1 }), "e error"),
              op("="),
              term(vector(kg.t, "t", { kind: "uniform", scale }), "t público")),
            legend(p.eta1)),
          h("section", {},
            h("h4", {}, "Semillas de esta ejecución"),
            h("div", { class: "stack mono" },
              h("div", {}, "d = ", short(kg.d)),
              h("div", {}, "ρ = ", short(kg.rho), "  (pública, va dentro de ek)"),
              h("div", {}, "σ = ", short(kg.sigma), "  (secreta, genera s y e)")),
            h("div", { class: "stat-row" },
              stat(`${fmt(p.ek_size)} B`, "ek (pública)"),
              stat(`${fmt(p.dk_size)} B`, "dk (privada)"),
              stat(`${d.timings_ms.keygen.toFixed(2)} ms`, "tiempo de KeyGen")))),
      };
    },
  },
  {
    title: "Encaps",
    flow: { bob: true, c: true },
    render(d) {
      const p = d.params;
      const en = d.encaps;
      const scale = Math.min(4, fitScale(4));
      return {
        explain: `
          <h2>5. Encaps: Bob encapsula una clave</h2>
          <p>1. Bob elige 32 bytes aleatorios <code>m</code> (256 bits) y calcula <code>(K, r) = G(m ‖ H(ek))</code>. <b>K es la clave compartida.</b></p>
          <p>2. Con <code>r</code> genera su propio secreto <code>y</code> y los errores <code>e₁</code>, <code>e₂</code> (pequeños).</p>
          <p>3. Calcula</p>
          <div class="formula">u = Aᵀ·y + e₁<br>v = tᵀ·y + e₂ + μ</div>
          <p><b>μ</b> es el mensaje escondido: cada bit 0 se convierte en 0 y cada bit 1 en ⌈q/2⌋ = 1665, el punto del reloj más alejado de 0.</p>
          <p>En <code>v</code>, el mensaje queda tapado por <code>tᵀ·y</code>, que parece aleatorio. Solo quien conoce <code>s</code> puede reconstruir esa "máscara" y quitarla.</p>
          <p>4. Comprime <code>u</code> y <code>v</code> y envía <code>c</code> a Alice.</p>`,
        visual: h("div", {},
          h("section", {},
            h("h4", {}, "El mensaje m y su codificación μ"),
            h("div", { class: "equation" },
              term(poly(en.message_bits, { kind: "bits", name: "m (bit)", scale: 6 }), "m: 256 bits"),
              op("→"),
              term(poly(en.mu, { kind: "message", name: "μ", scale: 6 }), "μ: 0 o 1665")),
            h("div", { class: "mono", style: "margin-top:8px" }, "K = ", short(en.K), "   r = ", short(en.r))),
          h("section", {},
            h("h4", {}, "u = Aᵀ·y + e₁"),
            h("div", { class: "equation" },
              term(h("div", { class: "bracket" }, h("span", { class: "mono" }, `Aᵀ (${p.k}×${p.k})`)), "la misma A, traspuesta"),
              op("·"),
              term(vector(en.y, "y", { kind: "small", scale, maxAbs: p.eta1 }), "y"),
              op("+"),
              term(vector(en.e1, "e₁", { kind: "small", scale, maxAbs: p.eta2 }), "e₁"),
              op("="),
              term(vector(en.u, "u", { kind: "uniform", scale }), "u"))),
          h("section", {},
            h("h4", {}, "v = tᵀ·y + e₂ + μ"),
            h("div", { class: "equation" },
              term(h("div", { class: "bracket" }, h("span", { class: "mono" }, "tᵀ·y")), "máscara"),
              op("+"),
              term(poly(en.e2, { kind: "small", name: "e₂", scale, maxAbs: p.eta2 }), "e₂"),
              op("+"),
              term(poly(en.mu, { kind: "message", name: "μ", scale }), "μ"),
              op("="),
              term(poly(en.v, { kind: "uniform", name: "v", scale }), "v")),
            h("p", { class: "note" }, "Aunque μ tiene un patrón clarísimo, v parece ruido: la máscara lo tapa por completo."),
            legend(p.eta1))),
      };
    },
  },
  {
    title: "Compresión",
    flow: { bob: true, c: true },
    render(d) {
      const p = d.params;
      const en = d.encaps;
      const uncompressed = 384 * (p.k + 1);
      const uMax = Math.ceil(Q / 2 ** (p.du + 1));
      const vMax = Math.ceil(Q / 2 ** (p.dv + 1));
      const flatU = en.u_compression_error.flat();
      const bar = (bytes, label) => h("div", {}, h("span", { class: "mono" }, `${label}: ${fmt(bytes)} B`), h("span", { class: "bar", style: `width:${(bytes / uncompressed) * 260}px` }));
      return {
        explain: `
          <h2>6. Compresión: menos bytes a cambio de un poco más de ruido</h2>
          <p>Cada coeficiente de <code>u</code> y <code>v</code> ocupa 12 bits (0…3328). Antes de enviarlos, Bob se queda solo con los d bits más significativos:</p>
          <div class="formula">Compress_d(x) = ⌈(2^d / q)·x⌋ mod 2^d</div>
          <p>En ${p.name}: <code>u</code> con d<sub>u</sub> = ${p.du} bits y <code>v</code> con d<sub>v</sub> = ${p.dv} bits. El texto cifrado pasa de ${fmt(uncompressed)} a ${fmt(p.ciphertext_size)} bytes.</p>
          <p>Al descomprimir no se recupera el valor exacto: queda un pequeño error extra (histogramas). No pasa nada mientras el error total siga lejos de q/4.</p>
          <p class="note">Aquí estaba uno de los dos fallos del TFG: el estándar redondea los empates hacia arriba (1664,5 → 1665), mientras que <code>round()</code> de Python redondea al par (1664). Con eso, parte de los textos cifrados no coincidían con los de otras implementaciones.</p>`,
        visual: h("div", {},
          h("section", {},
            h("h4", {}, "Tamaño del texto cifrado"),
            h("div", { class: "stack" }, bar(uncompressed, "sin comprimir"), bar(p.ciphertext_size, "comprimido"))),
          h("section", {},
            h("h4", {}, "Error que introduce la compresión"),
            histogram(flatU, { min: -uMax, max: uMax, title: `u (d_u = ${p.du} bits): error máximo ±${uMax}` }),
            histogram(en.v_compression_error, { min: -vMax, max: vMax, title: `v (d_v = ${p.dv} bits): error máximo ±${vMax}` })),
          h("section", {},
            h("h4", {}, "v antes y después de comprimir y descomprimir"),
            h("div", { class: "row" },
              poly(en.v, { kind: "uniform", name: "v", caption: "v (12 bits)", scale: 6 }),
              op("→"),
              poly(en.v_compressed, { kind: "uniform", name: `Compress(v) (${p.dv} bits)`, caption: `Compress(v): ${p.dv} bits`, scale: 6, range: 2 ** p.dv }),
              op("→"),
              poly(en.v.map((x, i) => (x + en.v_compression_error[i] + Q) % Q), { kind: "uniform", name: "Decompress(Compress(v))", caption: "lo que recibe Alice", scale: 6 }))),
        ),
      };
    },
  },
  {
    title: "Decaps",
    flow: { alice: true },
    render(d) {
      const p = d.params;
      const dc = d.decaps;
      const info = paramInfo();
      const recovered = 256 - dc.bit_errors;
      return {
        explain: `
          <h2>7. Decaps: Alice quita la máscara</h2>
          <p>Alice descomprime <code>c</code> y, con su secreto <code>s</code>, calcula</p>
          <div class="formula">w = v − sᵀ·u</div>
          <p>Si se desarrolla, <code>w = μ + (eᵀ·y − sᵀ·e₁ + e₂ + errores de compresión)</code>. Lo que hay entre paréntesis son productos de cosas pequeñas, así que sigue siendo pequeño.</p>
          <p>En el reloj, cada coeficiente de <code>w</code> cae cerca de 0 (bit 0) o cerca de q/2 (bit 1). Alice lee cada bit según la mitad del reloj en la que cae: eso es <code>Compress₁(w)</code>.</p>
          <p>Pulsa los botones para ver los 256 coeficientes antes y después de quitar la máscara.</p>
          <p class="note">El descifrado solo fallaría si algún error superase q/4 = 832. En esta ejecución el mayor ha sido ${dc.max_noise}. Para ${p.name} la probabilidad de fallo es ${info.failure}.</p>`,
        visual: h("div", {},
          h("section", {}, h("h4", {}, "Los 256 coeficientes en el reloj de Z_q"), maskClock(d)),
          h("section", {},
            h("h4", {}, "Ruido final: w − μ"),
            histogram(dc.noise, {
              min: -dc.threshold, max: dc.threshold, bins: 64, color: PAL.posCss,
              title: `máximo |ruido| = ${dc.max_noise}`,
              markers: [{ value: -dc.threshold + 1, label: "−q/4" }, { value: dc.threshold - 1, label: "q/4" }],
            }),
            h("div", { class: "stat-row" },
              stat(`${recovered}/256`, "bits recuperados", recovered === 256 ? "ok" : "bad"),
              stat(`${dc.max_noise} / ${dc.threshold}`, "ruido máximo / margen"),
              stat(`${d.timings_ms.decaps.toFixed(2)} ms`, "tiempo de Decaps")))),
      };
    },
  },
  {
    title: "Verificación",
    flow: { alice: true, c: true },
    render(d) {
      const dc = d.decaps;
      const en = d.encaps;
      const focus = dc.tampered ? dc.tampered_byte : null;
      return {
        explain: `
          <h2>8. ¿Alguien ha tocado c?</h2>
          <p>El cifrado K-PKE por sí solo es vulnerable: un atacante podría modificar <code>c</code>, observar cómo reacciona Alice y deducir poco a poco su clave privada. ML-KEM lo evita con la <b>transformación de Fujisaki-Okamoto</b>:</p>
          <p>1. Con el mensaje recuperado <code>m′</code>, Alice recalcula <code>(K′, r′) = G(m′ ‖ H(ek))</code>.</p>
          <p>2. Vuelve a cifrar <code>m′</code> con <code>r′</code> exactamente como lo hizo Bob y obtiene <code>c′</code>.</p>
          <p>3. Si <code>c′ = c</code>, devuelve <code>K′</code>. Si no, devuelve <code>K̄ = J(z ‖ c)</code>, una clave pseudoaleatoria: es el <b>rechazo implícito</b>. El atacante no recibe ningún error que le dé pistas.</p>
          <p>Pulsa <kbd>M</kbd> para invertir un bit de <code>c</code> en el canal y repetir.</p>`,
        visual: h("div", {},
          h("section", {},
            h("h4", {}, dc.tampered ? `c recibido (byte ${dc.tampered_byte} manipulado)` : "c recibido"),
            hexView(dc.c_received, { compareWith: en.c, focusByte: focus }),
            h("h4", { style: "margin-top:12px" }, "c′ recalculado por Alice"),
            hexView(dc.c_prime, { compareWith: dc.c_received, focusByte: focus }),
            h("div", { class: `verdict ${dc.accepted ? "ok" : "bad"}` },
              dc.accepted ? "✓ c′ = c: el texto cifrado es auténtico" : "✗ c′ ≠ c: rechazo implícito")),
          h("section", {},
            h("div", { class: "keys" },
              h("div", { class: "keybox" }, h("h5", {}, "K de Bob"), h("div", { class: "hex" }, en.K)),
              h("div", { class: `keybox ${dc.keys_match ? "ok" : "bad"}` },
                h("h5", {}, dc.accepted ? "K′ de Alice" : "K̄ = J(z ‖ c) que devuelve Alice"),
                h("div", { class: "hex" }, dc.K_final))),
            dc.tampered
              ? h("p", { class: "note" }, dc.bit_errors === 0
                ? "Curioso: Alice ha recuperado el mensaje m correcto (el bit cambiado no alteró ningún bit de m), pero al volver a cifrar sale el c original, no el manipulado. Así detecta la manipulación."
                : `El bit manipulado cambió ${dc.bit_errors} bit(s) del mensaje recuperado; al volver a cifrar sale un c′ distinto.`)
              : h("p", { class: "note" }, "Prueba a pulsar «Manipular c» (o la tecla M)."))),
      };
    },
  },
  {
    title: "Comparativa",
    flow: {},
    render(d) {
      const sizes = { "ML-KEM-512": [800, 1632, 768], "ML-KEM-768": [1184, 2400, 1088], "ML-KEM-1024": [1568, 3168, 1568] };
      const details = {
        "ML-KEM-512": [2, 3, 10, 4], "ML-KEM-768": [3, 2, 10, 4], "ML-KEM-1024": [4, 2, 11, 5],
      };
      const benchCell = (name, op) => (state.bench ? `${state.bench.find((r) => r.name === name)[op].toFixed(2)} ms` : "—");
      const table = h("table", { class: "compare" },
        h("tr", {}, ...["", "k", "η₁", "d_u", "d_v", "dimensión", "ek", "c", "nivel NIST", "KeyGen", "Encaps", "Decaps"].map((t) => h("th", {}, t))),
        PARAMS.map((p) => {
          const [ek, , c] = sizes[p.name];
          return h("tr", { class: p.name === state.params ? "current" : null },
            h("td", {}, p.name), ...details[p.name].map((v) => h("td", {}, v)),
            h("td", {}, fmt(p.k * 256)), h("td", {}, `${fmt(ek)} B`), h("td", {}, `${fmt(c)} B`),
            h("td", {}, `${p.category} (≈ ${p.aes})`),
            h("td", {}, benchCell(p.name, "keygen")), h("td", {}, benchCell(p.name, "encaps")), h("td", {}, benchCell(p.name, "decaps")));
        }));
      const button = h("button", { class: "primary" }, state.bench ? "Volver a medir" : "Medir en este navegador");
      button.addEventListener("click", async () => {
        button.disabled = true;
        button.textContent = "Midiendo…";
        try {
          state.bench = await python("bench", BENCH_REPETITIONS, BENCH_BATCH);
        } catch (error) {
          button.disabled = false;
          button.textContent = `No se pudo medir: ${error.message}`;
          throw error;
        }
        render();
      });
      const sizeBars = [["X25519", 32], ["RSA-3072", 384], ...PARAMS.map((p) => [p.name, sizes[p.name][0]])];
      return {
        explain: `
          <h2>9. Los tres niveles de seguridad</h2>
          <p>Pasar de ML-KEM-512 a ML-KEM-1024 cambia sobre todo <b>k</b>: un retículo de más dimensiones es más difícil de atacar, pero las claves y los textos cifrados son más grandes.</p>
          <p>Las categorías 1, 3 y 5 de NIST equivalen aproximadamente a la dificultad de romper AES-128, AES-192 y AES-256. ML-KEM-768 es la opción recomendada por defecto.</p>
          <p>Comparado con lo que se usa hoy, las claves son más grandes (una clave pública X25519 ocupa 32 bytes), pero las operaciones son muy rápidas. Chrome, Firefox y Cloudflare ya lo usan en TLS combinado con X25519 (<code>X25519MLKEM768</code>), por si algún día se descubre un ataque contra uno de los dos.</p>
          <p class="note">Los tiempos se miden en tu navegador: esta implementación en Python con NumPy, compilada a WebAssembly (Pyodide), mediana de ${BENCH_REPETITIONS} tandas de ${BENCH_BATCH} llamadas. No son comparables con las cifras nativas de <a href="https://github.com/DenisSValentin/algoritmo-ml-kem/blob/main/docs/review.md">docs/review.md</a> (<code>python -m benchmarks.bench</code>), que suelen ser más bajas. Una implementación en C o Go tarda en torno a 10–50 µs.</p>`,
        visual: h("div", {},
          h("section", {}, h("h4", {}, "Parámetros, tamaños y tiempos"), h("div", { style: "overflow-x:auto" }, table), h("div", { class: "controls-line" }, button)),
          h("section", {},
            h("h4", {}, "Tamaño de la clave pública"),
            h("div", { class: "stack" }, sizeBars.map(([name, bytes]) =>
              h("div", {}, h("span", { class: "mono", style: "display:inline-block;width:110px" }, name),
                h("span", { class: "bar", style: `width:${(bytes / 1568) * 280}px;${name.startsWith("ML") ? "" : "background:var(--muted)"}` }),
                h("span", { class: "mono", style: "margin-left:8px" }, `${fmt(bytes)} B`)))))),
      };
    },
  },
];

// ------------------------------------------------------------------ cabecera, flujo y navegación

function renderParamPicker() {
  const picker = $("paramPicker");
  picker.replaceChildren(...PARAMS.map((p, i) => h("button", {
    role: "radio",
    "aria-checked": String(p.name === state.params),
    title: `Tecla ${i + 1}`,
    onclick: () => selectParams(p.name),
  }, p.name, h("small", {}, `k = ${p.k} · ${fmt(p.k * 256)} dim.`))));
}

function renderStepper() {
  $("stepper").replaceChildren(...STEPS.map((s, i) => h("button", {
    "aria-current": i === state.step ? "step" : null,
    onclick: () => goTo(i),
  }, h("span", { class: "num" }, `${i + 1}`), ` ${s.title}`)));
  $("btnPrev").disabled = state.step === 0;
  $("btnNext").disabled = state.step === STEPS.length - 1;
}

function renderFlow(d) {
  const f = STEPS[state.step].flow;
  const dc = d.decaps;
  $("flow").replaceChildren(
    h("div", { class: `party ${f.alice ? "active" : ""}` },
      h("h3", {}, "Alice"), h("div", { class: "role" }, "receptora · KeyGen y Decaps"),
      h("div", { class: "secret" }, state.step >= 6 ? `K′ = ${short(dc.K_final, 8)}` : "guarda dk en secreto")),
    h("div", { class: "channel" },
      h("div", { class: `wire ${f.ek ? "active" : ""}` }, `ek · ${fmt(d.params.ek_size)} B`, h("span", { class: "arrow" }, "→")),
      h("div", { class: `wire ${f.c ? "active" : ""} ${state.tamper ? "tampered" : ""}` }, h("span", { class: "arrow" }, "←"), `c · ${fmt(d.params.ciphertext_size)} B`, state.tamper ? " ⚡ manipulado" : "")),
    h("div", { class: `party ${f.bob ? "active" : ""}` },
      h("h3", {}, "Bob"), h("div", { class: "role" }, "emisor · Encaps"),
      h("div", { class: "secret" }, state.step >= 4 ? `K = ${short(d.encaps.K, 8)}` : "recibe ek")),
  );
}

function render() {
  readPalette();
  renderParamPicker();
  renderStepper();
  const d = state.data;
  if (!d) return;
  $("banner").replaceChildren(state.tamper
    ? h("div", { class: "banner" }, `Modo manipulación: se ha invertido un bit del byte ${d.decaps.tampered_byte} del texto cifrado mientras viajaba por el canal. Pulsa M para desactivarlo.`)
    : "");
  renderFlow(d);
  const { explain, visual } = STEPS[state.step].render(d);
  $("explain").innerHTML = explain;
  $("visual").replaceChildren(visual);
}

function showLoader() {
  $("explain").replaceChildren(h("div", { class: "loader" },
    h("div", { class: "spinner", "aria-hidden": "true" }),
    h("div", {},
      h("h2", {}, "Preparando Python en tu navegador"),
      h("p", { id: "loadStatus", role: "status" }, "Arrancando…"),
      h("p", { class: "note" }, "El visualizador ejecuta la implementación real en Python dentro de la página, con Pyodide. La primera vez descarga unos 10 MB y tarda unos segundos; después el navegador lo guarda en caché."))));
}

function showError(error) {
  for (const id of ["banner", "flow", "visual"]) $(id).replaceChildren();
  $("explain").replaceChildren(
    h("h2", {}, "No se pudo ejecutar Python en el navegador"),
    h("p", { class: "banner" }, error.message),
    h("p", {}, "Pyodide se descarga de cdn.jsdelivr.net: comprueba la conexión y que ninguna extensión lo bloquee, y recarga la página."),
    h("p", { class: "note" }, "Si has abierto index.html directamente como fichero, arranca el servidor local con uv run ml-kem-visualizer."));
}

async function load() {
  state.loading = true;
  // La primera vez se ve el indicador de carga; después basta con atenuar la página
  if (state.data) document.body.classList.add("loading");
  else showLoader();
  try {
    state.data = await python("exchange", state.params, state.tamper, null);
  } catch (error) {
    state.data = null;
    showError(error);
    console.error(error);
  } finally {
    state.loading = false;
    document.body.classList.remove("loading");
  }
  render();
}

function goTo(step) {
  state.step = Math.max(0, Math.min(STEPS.length - 1, step));
  history.replaceState(null, "", `#paso-${state.step + 1}`);
  render();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function selectParams(name) {
  if (name === state.params) return;
  state.params = name;
  load();
}

function toggleTamper() {
  state.tamper = !state.tamper;
  $("btnTamper").setAttribute("aria-pressed", String(state.tamper));
  load();
}

$("btnPrev").addEventListener("click", () => goTo(state.step - 1));
$("btnNext").addEventListener("click", () => goTo(state.step + 1));
$("btnNew").addEventListener("click", load);
$("btnTamper").addEventListener("click", toggleTamper);

document.addEventListener("keydown", (event) => {
  if (event.metaKey || event.ctrlKey || event.altKey) return;
  const target = event.target;
  const typing = target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement;
  if (typing && (event.key.startsWith("Arrow") || target.type !== "range")) return;
  if (event.key === "ArrowRight") goTo(state.step + 1);
  else if (event.key === "ArrowLeft") goTo(state.step - 1);
  else if (["1", "2", "3"].includes(event.key)) selectParams(PARAMS[Number(event.key) - 1].name);
  else if (event.key.toLowerCase() === "n") load();
  else if (event.key.toLowerCase() === "m") toggleTamper();
  else return;
  event.preventDefault();
});

window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", render);

const initialStep = Number((location.hash.match(/paso-(\d+)/) || [])[1]);
if (initialStep) state.step = Math.min(STEPS.length, initialStep) - 1;
renderParamPicker();
renderStepper();
load();
