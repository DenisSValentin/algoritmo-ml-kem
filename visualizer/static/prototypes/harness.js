"use strict";

// Selector de prototipos (método de la skill «prototype», PICKER.md). Cambia de diseño al
// instante: activa la hoja de estilos de la variante y vuelve a pintar (los lienzos leen los
// colores de CSS). Python no se recarga: los datos de la ejecución se conservan.
//
// Única desviación del contrato de PICKER.md: la app ya usa 1 2 3 y ← → (parámetros y pasos),
// así que el selector responde a Mayús + 1/2/3, Mayús + ←/→ y Mayús + R.

const VARIANTS = ["riel", "capa", "hilo"];
const THEME_COLOR = {
  riel: { light: "#eef1f6", dark: "#0a0d14" },
  capa: { light: "#f4f5f8", dark: "#0b0d12" },
  hilo: { light: "#eef1f6", dark: "#0a0d14" },
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
  for (const sheet of sheets) sheet.media = sheet.dataset.variantCss.split(" ").includes(name) ? "all" : "not all";
  root.dataset.variant = name;
  items.forEach((el, j) => {
    el.toggleAttribute("data-active", j === i);
    if (j === i) el.setAttribute("aria-current", "true");
    else el.removeAttribute("aria-current");
  });
  placePicker();
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
darkScheme.addEventListener("change", syncThemeColor);

// Capa en móvil lleva los pasos en un dock abajo: ahí el selector sube
const narrow = window.matchMedia("(max-width: 900px)");
function placePicker() {
  if (VARIANTS[current] === "capa" && narrow.matches) picker.setAttribute("data-position", "top");
  else picker.removeAttribute("data-position");
}
narrow.addEventListener("change", placePicker);

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

// ------------------------------------------------------------------ fondo y vidrio

// Cada paso desplaza un poco las manchas de color del fondo: el vidrio lo refleja al avanzar
document.addEventListener("mlkem:render", () => {
  const step = Number(root.dataset.step || 1) - 1;
  root.style.setProperty("--field-x", `${-step * 22}px`);
  root.style.setProperty("--field-y", `${-step * 9}px`);
});

// Brillo especular que sigue al puntero (solo ratón o trackpad). Una sola luz para todo el
// vidrio: cada superficie la refleja en su sitio porque el degradado va fijo a la ventana.
if (window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
  let frame = null;
  let last = null;
  document.addEventListener("pointermove", (event) => {
    last = event;
    if (frame) return;
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
