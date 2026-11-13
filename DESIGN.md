# Design

Sistema visual del visualizador de ML-KEM (`visualizer/`). Producto y público: `PRODUCT.md`.
Crítica del diseño de partida: `docs/design-critique.md`.

> **Estado (2026-11-13): en exploración.** Hay tres direcciones construidas y funcionando en
> `visualizer/static/prototypes/` (selector en local). Denis elige qué le gusta de cada una; lo
> elegido se apunta en «Decisiones de Denis» y se convierte en el diseño publicado. Hasta entonces
> lo publicado sigue siendo `visualizer/static/{index.html,style.css,app.js}` sin cambios.
> **Antes de mergear a `main`:** pasar el diseño elegido a esos ficheros y borrar
> `visualizer/static/prototypes/`; si no, `pages.yml` la publicaría en `/prototypes/`.

## Modo de la superficie

**Lectura (Read).** Quien entra quiere *entender* ML-KEM. Manda la pregunta de cada paso; el
diseño se queda con el marco (cabecera, navegación, cómo se ponen ecuaciones, tablas y figuras) y
la columna de lectura se mantiene tranquila: letra de lectura, contraste real, 60–70 caracteres.

## Lo común a cualquier dirección (decidido)

### Contenido y estructura
- 9 pasos fijos, un concepto por paso; texto primero, figura después (al lado en escritorio,
  debajo en móvil). En el texto se dice «en la figura», nunca «a la derecha».
- Alice · canal público · Bob siempre visible encima del paso: quién actúa y qué viaja (`ek`, `c`).
- Los datos salen de la ejecución real (Pyodide). Las demos de juguete (retículo 2D/3D, anillo de
  8 coeficientes) lo dicen en su título.

### Color
- Estrategia **contenida**: neutros + **un** acento con un trabajo concreto (lo que se puede tocar,
  el tramo activo o el elemento elegido). El acento nunca colorea datos.
- Colores de datos, iguales en todas las direcciones: negativo azul (`--neg`), positivo naranja
  (`--pos`), uniforme en paleta *plasma*, bits en tinta/neutro. Correcto en verde (`--ok`), error
  y manipulación en rojo (`--bad`).
- Claro y oscuro siguen al sistema (`prefers-color-scheme`); `theme-color` por esquema.
- En oscuro el acento es claro y el texto sobre él, oscuro (`--on-accent`): nunca blanco sobre un
  acento pastel (era 2,5:1 en el diseño de partida).
- Contraste medido en las tres direcciones, claro y oscuro: texto ≥ 14:1, secundario ≥ 5,8:1,
  texto sobre acento ≥ 5,6:1; en el vidrio, peor caso con el resplandor más oscuro debajo.

### Tipografía
- Monoespaciada solo para datos (hex, polinomios, fórmulas, tamaños). Cifras tabulares siempre.
- Títulos con `text-wrap: balance`, párrafos con `pretty`; tracking negativo solo en tamaños grandes
  (−0,01 a −0,02 em).

### Estado
- El estado es una **marca**, no solo un color: paso visto / actual / pendiente se distinguen por
  forma. Manipulación: icono de rayo + rojo + texto.

### Movimiento
- Curva base `--ease-out: cubic-bezier(0.23, 1, 0.32, 1)`; nada de `ease-in` en entradas.
- **Cambio de paso** (View Transitions): sale el texto 16 px hacia atrás en 160 ms; entra 24 px
  desde delante en 240 ms; la figura, 40 ms después. Dirección según se avance o se retroceda.
  El resto de la interfaz cambia al instante. Pulsaciones rápidas cortan la transición anterior.
- **Marca del paso actual** se desliza a la nueva posición (cada dirección la suya).
- **Ficha de `ek` / `c`** cruza el canal (900 ms, ease-in-out) la primera vez que se llega a un
  paso donde viaja; no se repite al repintar.
- Todo el movimiento va dentro de `@media (prefers-reduced-motion: no-preference)`: con
  movimiento reducido, cambios instantáneos y el reloj del paso 7 sigue funcionando.

### Móvil
- `viewport-fit=cover`, `hover` solo con `@media (hover: hover) and (pointer: fine)`,
  `touch-action: manipulation` en botones, `pan-y` en lienzos que no se arrastran,
  `touch-action: none` solo en el retículo 3D. Parámetros en tres columnas iguales; acciones a
  todo el ancho.

### Navegador
- Selección, foco, scrollbars y `color-scheme` con la paleta. Iconos SVG de un mismo trazo
  (1,75 px), no caracteres. `#paso-N` reacciona a enlaces y a atrás/adelante.

## Las tres direcciones

Las tres comparten lo de arriba, el mismo HTML y los mismos datos; cambian el mundo visual, la
composición y el movimiento propio. Se eligieron con `impeccable` (lista de 7 mundos del público,
tirada `seed:090010ae7dfc278d`) y el método de `prototype` (un eje distinto para cada una).

### A · Línea — eje: orientación y recorrido

- **Idea:** el protocolo es un viaje en una línea de transporte entre dos terminales, Alice y Bob.
  Los 9 pasos son paradas.
- **Composición:** escritorio con la línea vertical fija a la izquierda (paradas con quién actúa
  en cada una), terminales y canal arriba como un plano de línea, texto y figura a dos columnas.
  En tableta y móvil la línea se tumba y queda fija arriba, como el plano del vagón.
- **Color:** gris frío de andén `#f3f5f8`, tinta azul noche `#0f1724`, un único color de línea
  violeta `#5432d3` (oscuro: `#a790ff`) que solo pinta el tramo recorrido y el activo.
- **Tipografía:** Overpass (inspirada en la señalética de carreteras) y Overpass Mono.
- **Firma:** ecuaciones en placas oscuras como carteles de andén; la bandera de la parada actual
  se desliza por la línea; `ek` y `c` cruzan el canal como un tren.
- **Préstamos de la tirada:** del mapa de orientación, «un solo color reservado al tramo activo»;
  del banco de montaje, «el estado es una marca» (parada llena, bandera, hueca).

### B · Estándar — eje: estructura de lectura

- **Idea:** el visualizador como documento técnico, igual que el propio FIPS 203.
- **Composición:** una sola columna de lectura (68 caracteres) con portada y regla gruesa, el
  índice como cabecera corrida fija, el protocolo Alice/canal/Bob entre reglas como en un artículo,
  y cada visualización como «Figura N» a ancho de página debajo del texto. Anterior/siguiente al
  final, como secciones.
- **Color:** papel blanco (no crema), tinta negra `#141414`, un azul de estándar `#1b4f9c` solo
  para lo que se toca. Oscuro: `#131416` con tinta `#e9e7e2`.
- **Tipografía:** STIX Two Text (la de la edición científica y matemática) para leer y titular;
  la del sistema para controles.
- **Firma:** ecuaciones entre reglas y numeradas «(1), (2)…» como los algoritmos del estándar;
  marca de visto dibujada en el índice; el subrayado del índice se desliza al paso actual.
- **Préstamo de la tirada:** de la cinta de procedencia, distinguir lo calculado de verdad de lo
  ilustrativo: las figuras de datos reales van sin adorno y las demos llevan «de juguete» en el
  título.

### C · Vidrio — eje: material y profundidad (liquid glass)

- **Idea:** en LWE el ruido esconde el punto del retículo como un cristal esmerilado; aquí la
  interfaz entera es ese cristal flotando sobre un retículo de verdad.
- **Composición:** cabecera, Alice/canal/Bob, explicación y figura como láminas de vidrio sobre el
  retículo; los pasos en un *dock* flotante abajo con anterior/siguiente a los lados, como la barra
  de pestañas de iOS 26.
- **Color:** fondo `#e6ebf4` (oscuro `#06080e`) con resplandores que cambian según quién actúa:
  frío con Alice, cálido con Bob, violeta en los pasos generales. Acento azul sistema `#0a5fe0`
  (oscuro `#6e9bff` con texto oscuro).
- **Tipografía:** la del sistema (SF en Apple), con peso 450 sobre el vidrio (vibrancia).
- **Firma:** la lente (el paso y el parámetro elegidos son una gota de vidrio que refracta lo de
  detrás y se desliza con un pelín de rebote); el vidrio se materializa al entrar.
- **Préstamo de la tirada:** del registro de exposición, «solo una rampa fija de tonos»: tres
  grosores de vidrio y ninguno más.

## Liquid glass (solo en la dirección C, solo en esta app)

No es un estándar global ni de otros proyectos: es una prueba aquí. Ninguna skill instalada lo
define (`apple-design` solo cubre materiales translúcidos en general), así que esta es la
definición.

### Qué es
El material de iOS 26: vidrio translúcido que deja ver lo de detrás desenfocado, lo **refracta**
en los bordes, **refleja** la luz con un brillo especular, tiene **profundidad** (sombra y borde
iluminado arriba) y **se adapta** al contenido de detrás.

### Cómo se construye (`prototypes/vidrio.css`)
| Capa | Qué hace | Cómo |
|---|---|---|
| Tinte + desenfoque | La lámina | `::before` con `background` del grosor y `backdrop-filter: blur() saturate()` |
| Borde iluminado | Luz que entra por arriba y se apaga abajo | `::after` con `box-shadow` inset: 1 px claro arriba, contorno tenue, sombra interior abajo |
| Brillo especular | Reflejo de una sola luz que sigue al puntero | `::after` con un `radial-gradient` en `--mx/--my` y `background-attachment: fixed` (todas las láminas reflejan la misma luz en su sitio); solo con ratón |
| Refracción | La lente dobla lo de detrás en los bordes | `backdrop-filter: url(#lg-refract)`: `feDisplacementMap` con un mapa de bordes. Solo en Chromium (`.can-refract`); Safari y Firefox se quedan con desenfoque y brillo |
| Profundidad | Flota | sombra exterior suave con desplazamiento (`--glass-shadow`) |
| Adaptación | Se tiñe según quién actúa | resplandores del fondo por fase (`data-phase`), fundido de 700 ms |

El vidrio va en el **pseudo-elemento** y no en el elemento: así el elemento no es «raíz de fondo»
y la lente que tiene dentro puede refractar la página de detrás y no solo el tinte de su lámina.

### Grosores (los únicos tres)
| Grosor | Uso | Claro | Oscuro | Desenfoque |
|---|---|---|---|---|
| Fino | cabecera, dock, Alice/canal/Bob | blanco 42 % | `#1e2436` 42 % | 14 px |
| Normal | figuras | blanco 58 % | `#161b2a` 56 % | 24 px |
| Grueso | texto que se lee | blanco 76 % | `#101420` 72 % | 34 px |

Controles dentro del vidrio: relleno translúcido **sin** desenfoque propio (vidrio sobre vidrio
destroza la legibilidad).

### Reglas
- **Contraste:** el texto solo va sobre el grosor normal o grueso; medido con el peor fondo debajo
  (resplandor más oscuro): texto ≥ 15:1, secundario ≥ 6,9:1.
- **`prefers-reduced-transparency`:** láminas opacas (`--surface`), sin desenfoque ni refracción,
  retículo al 35 %.
- **`prefers-contrast: more`:** láminas opacas con borde del color del texto.
- **`prefers-reduced-motion`:** el retículo no se desplaza, el vidrio no se materializa, la lente
  no se desliza.
- **Rendimiento:** el retículo de fondo se dibuja una sola vez (y al redimensionar o cambiar de
  tema) en un `<canvas>`; al cambiar de paso solo se desplaza con `translate` (900 ms), nunca en
  bucle. El retículo 3D del paso 2 se dibuja **encima** del vidrio, así que girarlo no obliga a
  recalcular ningún desenfoque (redibujarlo cuesta < 1 ms). Lo caro es desplazar la página, porque
  cada lámina vuelve a desenfocar lo de detrás: hay 7 láminas como máximo y la refracción solo en
  dos piezas pequeñas.
- **Pendiente de comprobar en hardware real:** fluidez al desplazar en un iPhone y en un portátil
  con gráfica integrada (la pestaña de pruebas de esta sesión estaba en segundo plano y no daba
  tiempos de fotograma fiables).

## Decisiones de Denis

*(Vacío hasta que Denis compare los tres diseños. Aquí irá qué se queda de cada uno; cuando
corrija algo, se apunta también con `learn-taste`.)*
