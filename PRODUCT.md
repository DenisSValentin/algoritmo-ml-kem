# Product

<!-- impeccable:product-schema 1 -->

Alcance: el **visualizador web** de ML-KEM (`visualizer/`), publicado en
<https://denissvalentin.github.io/algoritmo-ml-kem/>. La biblioteca `mlkem/` y la memoria del TFG
quedan fuera salvo como fuente de datos y de contenido.

> Origen de lo que hay aquí: el encargo de Denis (herramienta didáctica de criptografía
> post-cuántica; su TFG, que hace de escaparate en su CV y su GitHub) y el propio repositorio.
> Lo que no está confirmado por Denis lleva la marca *(inferido)*.

## Platform

web

## Users

- **Quien evalúa a Denis** (reclutadores, equipos técnicos, el tribunal del TFG): llega desde el
  CV, el perfil de GitHub o el README, casi siempre en un portátil y a veces desde el móvil. Tiene
  pocos minutos y quiere ver, sin instalar nada, que el autor entiende ML-KEM a fondo y sabe
  construir software cuidado. *(inferido del encargo: «escaparate en su CV y su GitHub»)*
- **Estudiantes y desarrolladores que aprenden ML-KEM**: siguen los 9 pasos con calma, juegan con
  el retículo, cambian el conjunto de parámetros y manipulan el texto cifrado para ver el rechazo.
  Suelen tener al lado `docs/concepts.md` o el estándar FIPS 203. *(inferido de docs/concepts.md)*

## Product Purpose

Enseñar qué pasa por dentro de ML-KEM (FIPS 203) ejecutando la implementación real en Python en
el navegador (Pyodide) y mostrando sus valores intermedios: el retículo y el problema CVP/LWE, el
anillo R_q, KeyGen, Encaps, la compresión, Decaps («quitar la máscara») y la verificación
Fujisaki-Okamoto. Éxito: alguien sin base en retículos sale entendiendo por qué Alice recupera la
clave y un espía no, y quien evalúa a Denis se queda con la sensación de rigor y oficio.

## Positioning

No es una animación ni un diagrama de manual: cada número, polinomio e histograma sale de una
ejecución real de la propia implementación de Denis, verificada con los vectores ACVP de NIST, y
se recalcula al cambiar parámetros o manipular `c`. Ese «es el código de verdad, no un dibujo» es
lo que ninguna otra explicación de Kyber puede copiar.

## Operating Context

- Página estática en GitHub Pages; Python corre en un Web Worker con Pyodide (≈10 MB la primera
  vez, luego en caché). En local: `uv run ml-kem-visualizer`.
- Se recorre con teclado (← → pasos, 1 2 3 parámetros, N nueva ejecución, M manipular) o con
  ratón/táctil.
- Se enlaza desde el README, el CV de Denis y su perfil de GitHub.

## Capabilities and Constraints

- HTML, CSS y JavaScript sin frameworks ni build; fuentes y librerías externas, mínimas.
- Los datos de cada paso vienen de `visualizer/trace.py`; la lógica criptográfica (`mlkem/`) y los
  tests no se tocan desde el visualizador.
- 9 pasos fijos: La idea, Retículos, El anillo R_q, KeyGen, Encaps, Compresión, Decaps,
  Verificación, Comparativa. Tres conjuntos de parámetros (512, 768, 1024).
- Visualizaciones en `<canvas>`: polinomios como cuadrículas 16×16, histogramas, el «reloj» de
  Z_q, el retículo 2D y el 3D que se gira con el ratón o las flechas.
- Cada push a `main` publica la web (workflow `pages.yml`).
- Idioma de la interfaz: español.

## Brand Commitments

- Autoría visible: «TFG de Denis Valentin Stoyanov D'Antonio, Universidad de Granada».
- Tono: explicaciones paso a paso, sin dar nada por sabido, en español claro; nada de bombo.
- Honestidad técnica: el aviso de que es código educativo (no constante en tiempo) y de que los
  tiempos medidos en el navegador no son comparables con implementaciones nativas.

## Evidence on Hand

- La implementación y sus vectores ACVP de NIST (`tests/vectors/acvp_subset.json`).
- La memoria del TFG (`Memoria_TFG_Denis_Stoyanov.pdf`), `docs/concepts.md` y `docs/review.md`.
- Mediciones reales en el navegador (paso 9).
- No hay testimonios, usuarios ni cifras de uso: no inventarlos.

## Product Principles

1. **Lo real por delante.** Lo que se ve es la ejecución de verdad; la interfaz lo deja claro y
   nunca lo adorna con datos de mentira.
2. **Un concepto por paso.** Cada paso responde a una pregunta y lo visual la demuestra.
3. **Tocar para entender.** Los controles (ruido, giro, manipular `c`, parámetros) son el
   aprendizaje, no un extra.
4. **Rigor visible.** Nombres y notación del estándar FIPS 203 (ek, dk, c, K, Â, η₁, d_u…).
5. **Funciona en cualquier sitio.** Teclado, táctil, móvil, modo oscuro y movimiento reducido.

## Accessibility & Inclusion

WCAG 2.2 AA como objetivo: contraste de texto ≥ 4,5:1, foco visible, todo manejable con teclado,
respeto a `prefers-reduced-motion` y `prefers-reduced-transparency`, y los colores de los datos
distinguibles también sin color (forma o etiqueta). *(inferido)*
