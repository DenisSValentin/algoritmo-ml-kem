# Definition of done — algoritmo-ml-kem

Ficha para el revisor `qa-reviewer` (lo lanza `/revisar-y-cerrar`). Sólo dice **qué
comandos lanzar** y **dónde están las reglas**: aquí no se copia ninguna regla.

## Verificaciones

Comprobadas el 2026-11-13 en `main` (Python 3.15, NumPy 2.5). Todas en local y sin efectos
fuera. Son las mismas que la CI (`.github/workflows/ci.yml`).

| Cuándo | Comando | Tarda | Pasa si |
|---|---|---|---|
| Siempre | `git diff --check` | <1 s | sin salida |
| Si cambia un `.py` | `uv run ruff check .` | <1 s | «All checks passed!» |
| Si cambia un `.py` o `tests/vectors/` | `uv run pytest -q` | <1 s | todos en verde |
| Si cambia `mlkem/` o `benchmarks/` | `uv run python -m benchmarks.bench -n 50` | <1 s | sale con 0 |
| Si cambia un `.js` de `visualizer/static/` | `node --check <fichero>` | <1 s | sin salida |

- `ruff format --check` **no** forma parte de la CI y hoy ya marca dos ficheros: no es un
  fallo del cambio.
- La CI corre también con Python 3.11 y NumPy 1.26. En local sólo está la versión nueva: si
  el cambio usa algo de Python > 3.11 o de NumPy 2, márcalo como duda (⏭️, lo ve la CI).
- La interfaz del visualizador no tiene tests de navegador: si cambia `visualizer/static/`,
  queda como ⏭️ con `uv run ml-kem-visualizer` para probarlo a mano.

## Dónde están las reglas

1. **`CLAUDE.md`** del repo.
2. **`README.md`** (qué hay en cada carpeta y cómo se usa) y **`docs/review.md`** (los
   fallos del código de 2024 y por qué se corrigieron así).
3. **FIPS 203**: cada módulo de `mlkem/` sigue una sección del estándar; los vectores NIST
   de `tests/vectors/` son la referencia.

## Lo que los comandos no ven y aquí rompe más

- **El sitio de GitHub Pages** (se publica en cada push a `main`): `pages.yml` copia sólo
  `visualizer/static/`, `mlkem/*.py` y `visualizer/__init__.py` y `trace.py`. Un módulo
  nuevo que importe `trace.py` fuera de esa lista rompe el sitio aunque el servidor local
  funcione. `PY_FILES` de `pyodide-worker.js` lo vigila `tests/test_visualizer.py`; la copia
  de `pages.yml`, nadie.
- **`legacy/`** es el código de 2024 tal cual: no se toca ni se le aplica ruff.
- **`Memoria_TFG_Denis_Stoyanov.pdf`** es la memoria entregada: no se modifica.
- **Prototipos o carpetas de pruebas** dentro de `visualizer/static/` se publicarían al
  llegar a `main`.
