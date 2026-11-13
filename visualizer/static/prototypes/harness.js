"use strict";

// Selector de prototipos (método de la skill «prototype», PICKER.md). Cambia de diseño al
// instante: activa la hoja de estilos de la variante y vuelve a pintar (los lienzos leen los
// colores de CSS). Python no se recarga: los datos de la ejecución se conservan.
//
// Única desviación del contrato de PICKER.md: la app ya usa 1 2 3 y ← → (parámetros y pasos),
// así que el selector responde a Mayús + 1/2/3, Mayús + ←/→ y Mayús + R.

const VARIANTS = ["linea", "estandar", "vidrio"];
const THEME_COLOR = {
  linea: { light: "#f3f5f8", dark: "#0d1219" },
  estandar: { light: "#ffffff", dark: "#131416" },
  vidrio: { light: "#e8edf6", dark: "#07090f" },
};

const root = document.documentElement;
const picker = document.querySelector(".proto-picker");
const highlight = picker.querySelector(".proto-picker-highlight");
const items = [...picker.querySelectorAll(".proto-picker-item:not(.proto-picker-replay)")];
const replay = picker.querySelector(".proto-picker-replay");
const sheets = [...document.querySelectorAll("link[data-variant-css]")];
const darkScheme = window.matchMedia("(prefers-color-scheme: dark)");
let current = 0;

function moveHighlight() {
  const el = items[current];
  highlight.style.width = `${el.offsetWidth}px`;
  highlight.style.transform = `translateX(${el.offsetLeft}px)`;
}

function syncThemeColor() {
  const colors = THEME_COLOR[VARIANTS[current]];
  document.getElementById("themeColor").setAttribute("content", darkScheme.matches ? colors.dark : colors.light);
}

// Vuelve a montar: repinta y relanza las animaciones de entrada de la variante
// (data-entering dura lo justo para la entrada: los repintados de después no la repiten)
let enterTimer = null;
function mount() {
  root.removeAttribute("data-entering");
  clearTimeout(enterTimer);
  window.mlkemApp?.render();
  if (VARIANTS[current] === "vidrio") drawField();
  requestAnimationFrame(() => requestAnimationFrame(() => {
    root.setAttribute("data-entering", "");
    enterTimer = setTimeout(() => root.removeAttribute("data-entering"), 900);
  }));
}

function setActive(i) {
  if (i < 0 || i >= VARIANTS.length) return;
  current = i;
  const name = VARIANTS[i];
  // media="not all" en vez de disabled: así las tres hojas se descargan al principio y el cambio es instantáneo
  for (const sheet of sheets) sheet.media = sheet.dataset.variantCss === name ? "all" : "not all";
  root.dataset.variant = name;
  items.forEach((el, j) => {
    el.toggleAttribute("data-active", j === i);
    if (j === i) el.setAttribute("aria-current", "true");
    else el.removeAttribute("aria-current");
  });
  // Vidrio ocupa el centro inferior con su barra de pasos: el selector sube
  if (name === "vidrio") picker.setAttribute("data-position", "top");
  else picker.removeAttribute("data-position");
  moveHighlight();
  syncThemeColor();
  const url = new URL(location);
  url.searchParams.set("v", i + 1);
  history.replaceState(null, "", url);
  mount();
}

items.forEach((el, i) => el.addEventListener("click", () => setActive(i)));
replay?.addEventListener("click", mount);
window.addEventListener("resize", moveHighlight);
darkScheme.addEventListener("change", () => { syncThemeColor(); if (VARIANTS[current] === "vidrio") drawField(); });

document.addEventListener("keydown", (e) => {
  if (/^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName) || e.target.isContentEditable) return;
  if (!e.shiftKey || e.metaKey || e.ctrlKey || e.altKey) return;
  const num = /^Digit([1-9])$/.exec(e.code);
  if (num && Number(num[1]) <= VARIANTS.length) setActive(Number(num[1]) - 1);
  else if (e.key === "ArrowRight") setActive((current + 1) % VARIANTS.length);
  else if (e.key === "ArrowLeft") setActive((current - 1 + VARIANTS.length) % VARIANTS.length);
  else if (e.code === "KeyR") mount();
  else return;
  e.preventDefault();
});

// ------------------------------------------------------------------ fondo de Vidrio

// El retículo de fondo se dibuja una vez (y al cambiar el tamaño o el tema). Al cambiar de paso
// solo se desplaza con transform, así el desenfoque del vidrio no se recalcula en cada fotograma.
const fieldCanvas = document.getElementById("field");
function drawField() {
  if (!fieldCanvas || VARIANTS[current] !== "vidrio") return;
  const margin = 160;
  const width = window.innerWidth + 2 * margin;
  const height = window.innerHeight + 2 * margin;
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  fieldCanvas.width = width * ratio;
  fieldCanvas.height = height * ratio;
  fieldCanvas.style.width = `${width}px`;
  fieldCanvas.style.height = `${height}px`;
  const ctx = fieldCanvas.getContext("2d");
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.clearRect(0, 0, width, height);
  const css = getComputedStyle(root);
  const dot = css.getPropertyValue("--field-dot").trim() || "rgba(120,130,160,.5)";
  const line = css.getPropertyValue("--field-line").trim() || "rgba(120,130,160,.15)";
  // La misma base que el retículo de juguete del paso 2, más grande
  const b1 = [64, 12.5];
  const b2 = [23.5, 57];
  const origin = [width * 0.62, height * 0.42];
  const n = 40;
  ctx.strokeStyle = line;
  ctx.lineWidth = 1;
  ctx.beginPath();
  for (let i = -n; i <= n; i++) {
    // líneas de la celda fundamental, muy tenues: dan la sensación de cristal tallado
    ctx.moveTo(origin[0] + i * b1[0] - n * b2[0], origin[1] - (i * b1[1] - n * b2[1]));
    ctx.lineTo(origin[0] + i * b1[0] + n * b2[0], origin[1] - (i * b1[1] + n * b2[1]));
  }
  ctx.stroke();
  ctx.fillStyle = dot;
  for (let i = -n; i <= n; i++) for (let j = -n; j <= n; j++) {
    const x = origin[0] + i * b1[0] + j * b2[0];
    const y = origin[1] - (i * b1[1] + j * b2[1]);
    if (x < -10 || x > width + 10 || y < -10 || y > height + 10) continue;
    // Los puntos lejos del centro, más pequeños: profundidad sin perspectiva
    const d = Math.hypot(x - origin[0], y - origin[1]) / Math.hypot(width, height);
    ctx.beginPath();
    ctx.arc(x, y, Math.max(1.1, 3.2 - d * 3.4), 0, 2 * Math.PI);
    ctx.fill();
  }
}
let resizeTimer = null;
window.addEventListener("resize", () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(drawField, 150);
});

// Cada paso desplaza el retículo un poco: avanzar es moverse por él
document.addEventListener("mlkem:render", () => {
  const step = Number(root.dataset.step || 1) - 1;
  root.style.setProperty("--field-x", `${-step * 16}px`);
  root.style.setProperty("--field-y", `${-step * 7}px`);
});

// Brillo especular que sigue al puntero (solo ratón o trackpad). Una sola luz para todo el
// vidrio: cada superficie la refleja en su sitio porque el degradado va fijo a la ventana.
if (window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
  let frame = null;
  let last = null;
  document.addEventListener("pointermove", (event) => {
    last = event;
    if (frame || VARIANTS[current] !== "vidrio") return;
    frame = requestAnimationFrame(() => {
      frame = null;
      root.style.setProperty("--mx", `${last.clientX}px`);
      root.style.setProperty("--my", `${last.clientY}px`);
    });
  }, { passive: true });
}

// Refracción real (backdrop-filter con un filtro SVG) solo donde se sabe que se dibuja bien:
// Chromium. En Safari y Firefox el vidrio se queda con desenfoque y brillo, sin refracción.
const chromium = navigator.userAgentData?.brands?.some((b) => /Chromium/.test(b.brand));
if (chromium) root.classList.add("can-refract");

// ------------------------------------------------------------------ arranque

const requested = Number.parseInt(new URLSearchParams(location.search).get("v"), 10);
setActive(requested >= 1 && requested <= VARIANTS.length ? requested - 1 : 0);
requestAnimationFrame(() => requestAnimationFrame(() => picker.setAttribute("data-ready", "")));
