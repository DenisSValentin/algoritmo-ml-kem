# Design

Sistema visual del visualizador de ML-KEM (`visualizer/`). Producto y público: `PRODUCT.md`.
Crítica del diseño de partida: `docs/design-critique.md`.

> **Estado (2026-11-13): en exploración, segunda ronda.** Hay tres direcciones construidas y
> funcionando en `visualizer/static/prototypes/` (selector en local): Riel, Capa e Hilo. Lo que
> Denis elige se apunta en «Decisiones de Denis» y se convierte en el diseño publicado. Hasta entonces
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

## Primera ronda (descartada o absorbida)

Tres direcciones construidas el 2026-11-13 (commit `9e2742f`, ya no están en el selector):

- **A · Línea:** el recorrido como línea de transporte, con la línea vertical del 1 al 9 a la
  izquierda. Se quedó la línea; los botones eran demasiado planos.
- **B · Estándar:** el visualizador como documento técnico tipo FIPS (STIX Two, columna única).
  Descartada.
- **C · Vidrio:** liquid glass sobre un retículo de puntos. Se quedó el material; el brillo del
  ratón era enorme, los puntos del fondo se confundían con el vidrio y era demasiado transparente.

## Segunda ronda: las tres direcciones en el selector

Comparten el material de `prototypes/cristal.css` (vidrio, botones con relieve, fondo de color)
y la línea vertical de pasos con la parada actual como gota de vidrio. Cambia **dónde vive la
línea y qué es de vidrio**.

### Riel — eje: la línea en su columna (Línea + Vidrio)

- **Idea:** el diseño A tal cual en estructura, pero con el material de C.
- **Composición:** cabecera de vidrio arriba; la línea con nombres y quién actúa (Alice/Bob) en
  una columna de vidrio fija a la izquierda; Alice/canal/Bob, texto y figura como láminas de
  vidrio a la derecha. En tableta y móvil, la línea se tumba y queda fija arriba.
- **Tipografía:** Overpass (señalética). Ecuaciones en placas oscuras de andén.
- **Cuándo gana:** si lo que más te gustó de A fue la sensación de «mapa de línea».

### Capa — eje: el vidrio solo en la navegación (como iOS 26)

- **Idea:** el contenido es opaco y tranquilo; lo único de vidrio es lo que flota encima: la
  cabecera fija con los parámetros, la línea de pasos a la izquierda y los botones de avanzar
  abajo a la derecha. Al desplazar, el texto y las figuras pasan por debajo del vidrio: eso es lo
  que se ve refractado, nunca un dibujo de fondo.
- **Composición:** la línea flota centrada a la izquierda (con nombres desde 1260 px; solo
  números por debajo). En móvil la línea pasa a un dock abajo, entre «anterior» y «siguiente».
- **Parámetros:** la opción elegida es una lente de vidrio que se desliza con un pequeño rebote.
- **Tipografía:** la del sistema (SF en Apple).
- **Cuándo gana:** si quieres el liquid glass más fiel a Apple y el texto más legible.

### Hilo — eje: la línea atraviesa el contenido

- **Idea:** la misma línea vertical, pero el paso actual se abre dentro de ella: arriba quedan
  las paradas hechas (compactas, con marca de visto), luego la parada actual y su contenido
  pegado a la línea, y debajo las que faltan.
- **Composición:** una sola columna. Funciona igual en móvil, donde la línea se estrecha.
- **Tipografía:** Atkinson Hyperlegible Next (diseñada para leer bien).
- **Cuándo gana:** si quieres que el recorrido se lea de arriba abajo como una historia.

### Común a las tres
- **Botones con relieve:** cara con degradado, filo iluminado arriba, sombra con desplazamiento;
  al pulsar se hunden 1 px. Lo elegido y lo principal, en el color de la línea con la misma luz.
  «Manipular c» activo queda hundido, como un interruptor.
- **Selector de parámetros:** pista hundida y la opción elegida sobresale; al cambiar de 512 a
  768 o 1024, la pieza elegida **se desliza** (320 ms, ease-out; en Capa 380 ms con rebote).
- **En oscuro, ninguna sombra de color** (el detector lo marca como halo de neón): las sombras
  son negras.

## Liquid glass (solo en esta app)

No es un estándar global ni de otros proyectos: es una prueba aquí. Ninguna skill instalada lo
define (`apple-design` solo cubre materiales translúcidos en general), así que esta es la
definición, corregida tras la primera ronda.

### Qué es
El material de iOS 26: vidrio translúcido que deja ver lo de detrás desenfocado, lo **refracta**
en los bordes, **refleja** la luz con un brillo especular, tiene **profundidad** (sombra y filo
iluminado arriba) y **se adapta** a lo que tiene detrás.

### Cómo se construye
| Capa | Qué hace | Cómo |
|---|---|---|
| Lámina | Tinte + desenfoque | `::before` con el tinte del grosor y `backdrop-filter: blur() saturate(1.6)` |
| Filo | Luz que entra por arriba y se apaga abajo | `::after` de 1 px (máscara que solo deja el borde) con degradado vertical |
| Luz del puntero | Reflejo pequeño de una sola luz | en el filo, un círculo de **150 px**; dentro de la lámina, otro de **110 px** muy tenue (14 % en claro, 6 % en oscuro). Fijos a la ventana, así todas las láminas reflejan la misma luz. Solo con ratón |
| Refracción | La gota dobla lo de detrás | `backdrop-filter: url(#lg-refract)` (`feDisplacementMap`). Solo en Chromium; Safari y Firefox, desenfoque y brillo |
| Profundidad | Flota | sombra exterior suave con desplazamiento (`--glass-shadow`) |
| Adaptación | Se tiñe con quien actúa | Riel e Hilo: manchas de color de fondo, frías con Alice y cálidas con Bob (700 ms). Capa: lo que pasa por debajo es el propio contenido |

El vidrio va en el **pseudo-elemento**, no en el elemento: así el elemento no es «raíz de fondo» y
la gota que lleva dentro refracta la página de detrás y no solo el tinte de su lámina.

### Grosores (los únicos tres)
| Grosor | Uso | Claro | Oscuro | Desenfoque |
|---|---|---|---|---|
| Fino | cabecera, línea, Alice/canal/Bob | blanco 64 % | `#1a1f2e` 68 % | 16 px |
| Normal | figuras; en Capa, toda la navegación | blanco 78 % | `#141825` 80 % | 24 px |
| Grueso | texto que se lee | blanco 88 % | `#10131e` 88 % | 30 px |

Ronda 1 usaba 42 / 58 / 76 %: era demasiado transparente. Controles dentro del vidrio: relleno
translúcido **sin** desenfoque propio (vidrio sobre vidrio destroza la legibilidad).

### Reglas
- **Detrás del vidrio, nunca un dibujo** (puntos, rejillas, líneas): se confunde con el propio
  material. Solo color suave o el contenido real.
- **Contraste:** medido con el peor fondo debajo (mancha de color más oscura y vidrio fino):
  texto ≥ 13,8:1, secundario ≥ 6,3:1, verde de «correcto» 4,5:1.
- **`prefers-reduced-transparency`:** láminas opacas (`--surface`), sin desenfoque ni refracción.
- **`prefers-contrast: more`:** láminas opacas con borde del color del texto.
- **`prefers-reduced-motion`:** el fondo no se desplaza, el vidrio no se materializa, la gota y
  la pieza de parámetros no se deslizan.
- **Rendimiento:** el fondo no se dibuja en un lienzo: son degradados de CSS que solo se desplazan
  con `translate` al cambiar de paso. El retículo 3D del paso 2 va **encima** del vidrio, así que
  girarlo no obliga a recalcular ningún desenfoque. Lo caro es desplazar la página (cada lámina
  vuelve a desenfocar lo de detrás): Riel tiene 5 láminas, Capa 3 e Hilo 4.
- **Pendiente de comprobar en hardware real:** fluidez al desplazar en un iPhone y en un portátil
  con gráfica integrada (la pestaña de pruebas de estas sesiones estaba en segundo plano y no daba
  tiempos de fotograma fiables).

## Decisiones de Denis

Ronda 1 (2026-11-13), con sus palabras:

- **Estándar (B), descartado:** «el b no me gusta nada».
- **De Línea (A) se queda la línea vertical de pasos:** «me gusta mucho su avance para que no te
  pierdas, es decir, la línea que va desde el punto 1 al 9 en vertical, indicando donde estás».
- **De Línea (A) no, los botones planos:** «no me gustan los botones, son muy planos, tanto para
  cambiar de ML-KEM-512 al 768 como los de Anterior y Siguiente».
- **De Vidrio (C) se queda el liquid glass**, con tres correcciones: «la luz brillante al rededor
  del raton es inmensamente grande»; «que el fondo tenga puntitos confunde con el liquid glass»;
  «quizás podría ser un poco menos transparente».
- **Cambio de parámetros animado:** «al pasar de ml-kem-512, a 768 o a 1024 me falta la animacion
  de transicion … se podria poner la animacion de deslizar».

Ronda 2: pendiente de que compare Riel, Capa e Hilo.
