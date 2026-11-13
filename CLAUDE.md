# algoritmo-ml-kem

Implementación educativa de ML-KEM (FIPS 203) en Python, con un visualizador que se publica
en GitHub Pages en cada push a `main`. Qué hay en cada carpeta y cómo se usa: `README.md`.

## Comandos
- `uv sync` para el entorno; `uv run pytest -q`, `uv run ruff check .` y
  `uv run ml-kem-visualizer` para el visualizador en local.

## Revisión antes de cerrar (2026-11-13, en prueba hasta el 27-11)
**Antes del commit final de una tarea que cambie código: `/revisar-y-cerrar`.** Lanza el
subagente `qa-reviewer` (global, contexto limpio, sólo lectura), se corrige lo que encuentre
y el resultado va en el commit (`QA-Review:` / `QA-Hallazgo:`). No para cambios de sólo
docs, textos o contenido. Qué comandos lanza y qué mira:
`.claude/checklists/definition-of-done.md`.
