// Ejecuta la implementación real de mlkem/ dentro del navegador con Pyodide (Python compilado
// a WebAssembly), así el visualizador funciona como página estática, sin servidor Python.
// Va en un Web Worker (de tipo módulo, el único que admite Pyodide) para que la página no se
// congele mientras Python calcula.

const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/";

// Los mismos ficheros del repositorio. Tanto GitHub Pages como server.py los sirven bajo py/.
// tests/test_visualizer.py comprueba que la lista no se quede atrás.
const PY_FILES = [
  "mlkem/__init__.py",
  "mlkem/encoding.py",
  "mlkem/hashes.py",
  "mlkem/kem.py",
  "mlkem/kpke.py",
  "mlkem/params.py",
  "mlkem/ring.py",
  "mlkem/sampling.py",
  "visualizer/__init__.py",
  "visualizer/trace.py",
];
const ROOT = "/app";

// Hace lo que hacían /api/exchange y /api/benchmark en server.py y devuelve el mismo JSON
const GLUE = `
import json
import sys

sys.path.insert(0, "${ROOT}")

from mlkem import PARAMETER_SETS
from visualizer.trace import benchmark, run_exchange


def exchange(params, tamper, seed):
    if params not in PARAMETER_SETS:
        raise ValueError(f"conjunto de parámetros desconocido: {params}")
    return json.dumps(run_exchange(params, tamper=tamper, seed=seed or None))


def bench(repetitions, batch):
    return json.dumps(benchmark(repetitions, batch))
`;

async function start() {
  postMessage({ status: "Descargando Python (Pyodide)…" });
  const { loadPyodide } = await import(`${PYODIDE_URL}pyodide.mjs`);
  const pyodide = await loadPyodide({ indexURL: PYODIDE_URL });
  postMessage({ status: "Cargando NumPy…" });
  await pyodide.loadPackage("numpy", { messageCallback: () => {} });
  postMessage({ status: "Cargando la implementación de ML-KEM…" });
  for (const file of PY_FILES) {
    const response = await fetch(`py/${file}`);
    if (!response.ok) throw new Error(`no se pudo descargar py/${file} (HTTP ${response.status})`);
    pyodide.FS.mkdirTree(`${ROOT}/${file.split("/")[0]}`);
    pyodide.FS.writeFile(`${ROOT}/${file}`, await response.text());
  }
  pyodide.runPython(GLUE);
  return pyodide.globals;
}

const ready = start();
ready.catch(() => {}); // el error se devuelve en cada llamada

onmessage = async ({ data: { id, fn, args } }) => {
  try {
    const python = await ready;
    postMessage({ id, result: python.get(fn)(...args) });
  } catch (error) {
    // De una excepción de Python basta con la última línea del traceback
    const message = String(error && error.message ? error.message : error).trim().split("\n").pop();
    postMessage({ id, error: message });
  }
};
