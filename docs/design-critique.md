# Crítica del diseño actual del visualizador

Revisión del visualizador publicado (`visualizer/static/`, noviembre de 2026) antes del rediseño.
Hecha con la skill `impeccable` (critique + audit), el detector de Impeccable y capturas reales en
escritorio (1440 px) y móvil (375 px), en claro y oscuro.

> ⚠️ Revisión en un solo contexto: la crítica de Impeccable pide dos subagentes independientes
> (diseño y detector); aquí se hizo todo en la misma sesión, primero la revisión de diseño y
> después el detector, sin mezclar resultados.

## Veredicto

Funciona y es honesto: todo lo que se ve sale de la ejecución real. Pero visualmente es «un
panel de administración genérico»: tarjetas blancas con borde fino, fuente del sistema y un azul
de acento. Tapando el título, podría ser cualquier herramienta interna. No hay nada que diga
«retículos», «estándar» o «el trabajo de alguien que entiende esto», y para un escaparate de CV
eso es lo que más falta.

## Lo que está bien (y hay que conservar)

1. **El contenido.** Un concepto por paso, notación del estándar, y las visualizaciones son
   buenas de verdad: el reloj de Z_q que quita la máscara, el retículo 3D con el ángulo trampa,
   el texto cifrado manipulado.
2. **Teclado completo** (← → 1 2 3 N M) y `aria` correcto en los grupos de radio y el paso actual.
3. **Estados de carga y error** con explicación de qué pasa y cómo arreglarlo.

## Problemas, por prioridad

| # | Problema | Dónde | Por qué importa |
|---|---|---|---|
| 1 | **Sin identidad visual.** Todo es la misma tarjeta con borde (cabecera de Alice/Bob, explicación, figura, estadísticas). | Todo | Para quien llega desde el CV, la primera impresión es «plantilla». |
| 2 | **Jerarquía plana.** El título del paso (20 px) compite con la cabecera (22 px); la explicación y la figura pesan lo mismo; los 9 pasos son botones idénticos sin estado de «visto». | Cabecera, pasos | No se sabe de un vistazo dónde estás ni cuánto queda. |
| 3 | **Móvil: el contenido empieza tarde.** En 375 px hay casi dos pantallas de cabecera, parámetros, pasos y Alice/Bob antes del primer párrafo; el texto dice «a la derecha» cuando la figura está debajo; «ML-KEM-512» se parte en dos líneas. | `@media (max-width: 900px)` | En el móvil (desde LinkedIn o GitHub) es donde más se abre un enlace. |
| 4 | **Contraste insuficiente en oscuro:** botón principal y parámetro elegido con texto blanco sobre `#8c9bff` = **2,5:1** (detector de Impeccable; AA pide 4,5:1). | `button.primary`, `.segmented` | Falla WCAG AA. |
| 5 | **Movimiento sin intención.** Cambiar de paso es un salto seco (y `scrollTo` suave aunque no haga falta); lo único animado es el reloj. La ficha de «ek viaja a Bob» no se ve viajar. | `goTo`, flujo | Se pierde la idea de recorrido y de canal. |
| 6 | **El lienzo recorta etiquetas.** «3q/4 ≈ 2497» se sale por la izquierda del reloj del paso 7. | `drawClockFrame` | Pequeño, pero se nota. |
| 7 | **Detalles de navegador sin tratar:** selección de texto, barras de desplazamiento, `theme-color`, `hover` sin `@media (hover: hover)` (se queda pegado en táctil), sin `viewport-fit=cover`, iconos hechos con caracteres (→ ↻ ⚡). | CSS global | Son las señales baratas de «hecho a mano» frente a «montado». |
| 8 | **Enlaces a pasos**: `#paso-4` solo se lee al cargar; cambiar el hash o usar atrás/adelante no cambia de paso. | `app.js` | Compartir un paso concreto falla a medias. |

## Mejoras propuestas (todas probadas en los prototipos)

- **Jerarquía:** el paso actual manda (título del paso más grande que la cabecera), la figura
  tiene su propia superficie y la explicación va en una columna de lectura de 60–70 caracteres.
- **Tipografía con intención:** una familia por diseño elegida por el mundo del diseño (señalética
  Overpass, STIX Two de edición científica, o la del sistema para el vidrio), cifras tabulares, y
  monoespaciada solo para datos.
- **Color:** un único acento con un trabajo concreto (lo que se puede tocar o el tramo activo),
  los colores de datos (azul/naranja, plasma) intactos, y texto oscuro sobre el acento en modo
  oscuro: todo ≥ 4,5:1 (medido).
- **Estado como marca, no solo color:** pasos vistos, actual y pendientes se distinguen por la
  forma (parada llena / bandera / hueca, o una marca de visto).
- **Móvil:** cabecera compacta, parámetros en tres columnas, pasos en una franja fija arriba (o un
  dock abajo), Alice/canal/Bob en una sola fila, «En la figura» en vez de «a la derecha».
- **Movimiento:** cambio de paso con View Transitions en la dirección del recorrido (240 ms,
  ease-out, la figura 40 ms después del texto), la marca del paso actual que se desliza, y la
  ficha de `ek` / `c` cruzando el canal cuando viaja. Todo desactivado con
  `prefers-reduced-motion`.
- **Navegador:** `theme-color` por esquema, `color-scheme`, selección y scrollbars con la paleta,
  `hover` solo con ratón, iconos SVG de un mismo trazo, `#paso-N` reactivo.
- **Corregir** la etiqueta recortada del reloj (dos líneas a los lados).

Todo esto está aplicado en el diseño definitivo (`visualizer/static/`), elegido tras tres rondas
de prototipos. Ver `DESIGN.md`.
