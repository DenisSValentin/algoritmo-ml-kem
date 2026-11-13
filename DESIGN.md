# Design

Sistema visual del visualizador de ML-KEM (`visualizer/`). Producto y público: `PRODUCT.md`.
Crítica del diseño de partida: `docs/design-critique.md`.

> **Estado (2026-11-13): en exploración, tercera ronda.** Hay dos direcciones construidas y
> funcionando en `visualizer/static/prototypes/` (selector en local): Riel y Capa. Lo que Denis
> elige se apunta en «Decisiones de Denis» y se convierte en el diseño publicado. Hasta entonces
> lo publicado sigue siendo `visualizer/static/{index.html,style.css,app.js}` sin cambios.
> **Antes de mergear a `main`:** pasar el diseño elegido a esos ficheros y borrar
> `visualizer/static/prototypes/`; si no, `pages.yml` la publicaría en `/prototypes/`.

## Modo de la superficie

**Lectura (Read).** Quien entra quiere *entender* ML-KEM. Manda la pregunta de cada paso; el
diseño se queda con el marco (cabecera, navegación, cómo se ponen ecuaciones, tablas y figuras) y
la columna de lectura se mantiene tranquila: letra de lectura, contraste real, 60–70 caracteres.

## Reglas de Denis (gusto)

Salen de sus correcciones al comparar los prototipos y él las aprobó (`learn-taste`). Mandan sobre
cualquier preferencia del agente. Antes de cambiar la interfaz, léelas.

### Composición
- **Nunca un diseño de documento académico** (columna única en serif, índice como cabecera
  corrida, figuras debajo del texto «Figura N») para esta app.
  Por qué: *inferido y aceptado:* le quita la sensación de herramienta interactiva.
  <!-- 2026-11-13: «el b no me gusta nada» (sobre Estándar) -->
- **El progreso es siempre una línea del 1 al 9 con todos los pasos a la vista a la vez:**
  tramo recorrido pintado, parada actual marcada, pasos pendientes visibles. Puede ir en
  vertical u horizontal. Nunca un diseño en el que no se vea en qué paso estás ni cuántos quedan.
  Por qué: sus palabras, «para que no te pierdas».
  <!-- 2026-11-13: «me gusta mucho su avance para que no te pierdas … la linea que va desde el punto 1 al 9 en vertical, indicando donde estás»; luego «no hace falta que sea vertical»; sobre Hilo: «no sabes en que pasos estas ni cuales quedan» -->
- **Lo que flota no tapa lo importante ni deja huecos:** una barra fija ocupa lo mínimo, y
  entre la navegación y el contenido no quedan franjas vacías.
  <!-- 2026-11-13: sobre Capa: «hay demasiados espacios libres … entre la guideline de los pasos 1 a 9 y el contenido» y «el selector de la parte superior … cubre por encima al contenido que importa de verdad» -->

### Interacción
- **Botones y selectores siempre con relieve, nunca planos:** cara con degradado, filo de luz
  arriba, sombra con desplazamiento, y se hunden 1 px al pulsarlos (`cristal.css`). Vale para
  los parámetros (512/768/1024), «Anterior»/«Siguiente» y el resto de botones.
  Por qué: *inferido y aceptado:* que se note que se pueden pulsar.
  <!-- 2026-11-13: «no me gustan los botones, son muy planos, tanto para cambiar de ML-KEM-512 al 768 como los de Anterior y Siguiente» -->
- **En un selector segmentado, la opción elegida se desliza hasta la nueva; nunca salta.**
  Por qué: *inferido y aceptado:* así se ve qué ha cambiado.
  <!-- 2026-11-13: «me falta la animacion de transicion de uno a otro … se podria poner la animacion de deslizar» -->

### Material (liquid glass)
- **La luz del puntero es pequeña y solo en el filo del vidrio:** 100 px en el borde y 70 px de
  brillo tenue dentro, como máximo.
  <!-- 2026-11-13: «la luz brillante al rededor del raton es inmensamente grande»; con 150/110 px: «que sea un poco más pequeña» -->
- **El vidrio deja ver poco:** opacidad del tinte ≥ 64 % (fino), 78 % (normal), 88 % (grueso).
  <!-- 2026-11-13: «quizás podría ser un poco menos transparente» -->
- **Detrás del vidrio, nada que se confunda con él:** los puntitos pequeños del retículo sí se
  confundían. Un dibujo de fondo no está prohibido si se distingue bien del material (por
  ejemplo, para diferenciar a Alice y Bob): hay que probarlo y que Denis lo vea.
  <!-- 2026-11-13: «que el fondo tenga puntitos confunde con el liquid glass»; luego «quizas siendo ahora más opaco algun dibujo si encaje bien, para diferenciar a alice y bob» -->

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

## Segunda ronda (absorbida)

- **Riel** (Línea + Vidrio): gustó; sigue en el selector.
- **Capa** (vidrio solo en la navegación flotante, línea vertical flotando a la izquierda): gustó
  la idea de elementos flotantes, pero sobraba hueco entre la línea y el contenido y la cabecera
  fija tapaba el contenido. Rehecha en la ronda 3.
- **Hilo** (la línea atraviesa el contenido): descartada; no se veía en qué paso estabas ni
  cuántos quedaban.

## Tercera ronda: las dos direcciones en el selector

Comparten el material de `prototypes/cristal.css`: vidrio, botones con relieve, selector de
parámetros que se desliza y fondo de color que dice quién actúa.

### Riel — la línea vertical en su columna
- Cabecera de vidrio arriba; la línea del 1 al 9 con nombres y quién actúa (Alice/Bob) en una
  columna de vidrio fija a la izquierda; Alice/canal/Bob, texto y figura como láminas a la
  derecha. En tableta y móvil la línea se tumba y queda fija arriba.
- Overpass (señalética). Ecuaciones en placas oscuras de andén.

### Capa — elementos flotantes, contenido a todo el ancho
- Arriba, el título en la página y, flotando fija, **solo una píldora pequeña** con los
  parámetros (lente de vidrio que se desliza con rebote), «Nueva ejecución» y «Manipular c».
- Abajo, un **dock de vidrio con la línea horizontal** del 1 al 9 (nombres en pantallas anchas,
  números en las estrechas) entre «anterior» y «siguiente».
- El contenido es opaco y ocupa todo el ancho; lo único que pasa por debajo del vidrio al
  desplazar es el propio contenido.
- En móvil la píldora deja de flotar (se queda al principio) y el dock sigue abajo.
- Letra del sistema (SF en Apple).

### Común
- **Botones con relieve** y **selector de parámetros que se desliza** (ver Reglas de Denis).
- **Alice y Bob se distinguen por el lado y el color:** cuando actúa Alice se ilumina en azul la
  mitad izquierda del fondo (donde está Alice en el esquema) y cuando actúa Bob, en cálido la
  derecha; además el vidrio entero se tiñe un poco de ese color (`--phase-tint`, 700 ms).
- **En oscuro, ninguna sombra de color** (el detector lo marca como halo de neón).
- **Cifras sin caja** dentro de las figuras: número y etiqueta separados por una regla fina.

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
| Luz del puntero | Reflejo pequeño de una sola luz | en el filo, un círculo de **100 px**; dentro de la lámina, otro de **70 px** muy tenue (35 % en claro, 6 % en oscuro). Fijos a la ventana, así todas las láminas reflejan la misma luz. Solo con ratón |
| Refracción | La gota dobla lo de detrás | `backdrop-filter: url(#lg-refract)` (`feDisplacementMap`). Solo en Chromium; Safari y Firefox, desenfoque y brillo |
| Profundidad | Flota | sombra exterior suave con desplazamiento (`--glass-shadow`) |
| Adaptación | Se tiñe con quien actúa | fondo azul a la izquierda con Alice y cálido a la derecha con Bob, y el tinte del vidrio se mezcla con ese color (`--phase-tint`); 700 ms |

El vidrio va en el **pseudo-elemento**, no en el elemento: así el elemento no es «raíz de fondo» y
la gota que lleva dentro refracta la página de detrás y no solo el tinte de su lámina.

### Grosores (los únicos tres)
| Grosor | Uso | Claro | Oscuro | Desenfoque |
|---|---|---|---|---|
| Fino | Riel: cabecera, línea, Alice/canal/Bob | blanco 64 % | `#1a1f2e` 68 % | 16 px |
| Normal | Riel: figuras. Capa: píldora y dock | blanco 78 % | `#141825` 80 % | 24 px |
| Grueso | texto que se lee | blanco 88 % | `#10131e` 88 % | 30 px |

Ronda 1 usaba 42 / 58 / 76 %: era demasiado transparente. Controles dentro del vidrio: relleno
translúcido **sin** desenfoque propio (vidrio sobre vidrio destroza la legibilidad).

### Reglas
- **Detrás del vidrio, nada que se confunda con él** (los puntitos de la ronda 1 sí se
  confundían). Ahora solo hay color; un dibujo que se distinga bien está permitido si Denis lo
  aprueba al verlo.
- **Contraste:** medido con el peor fondo debajo (mancha de color más oscura y vidrio fino):
  texto ≥ 13,8:1, secundario ≥ 6,3:1, verde de «correcto» 4,5:1.
- **`prefers-reduced-transparency`:** láminas opacas (`--surface`), sin desenfoque ni refracción.
- **`prefers-contrast: more`:** láminas opacas con borde del color del texto.
- **`prefers-reduced-motion`:** el fondo no se desplaza, el vidrio no se materializa, la gota y
  la pieza de parámetros no se deslizan.
- **Rendimiento:** el fondo no se dibuja en un lienzo: son degradados de CSS que solo se desplazan
  con `translate` al cambiar de paso. El retículo 3D del paso 2 va **encima** del vidrio, así que
  girarlo no obliga a recalcular ningún desenfoque. Lo caro es desplazar la página (cada lámina
  vuelve a desenfocar lo de detrás): Riel tiene 5 láminas y Capa 2.
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

Ronda 2 (2026-11-13), con sus palabras:

- **Riel:** «me gusta A bastante».
- **Capa:** «me gusta la idea de elementos flotantes pero está muy mal ejecutada. hay demasiados
  espacios libres … entre la guideline de los pasos 1 a 9 y el contenido. Además, si scrolleas
  hacia abajo el selector de la parte superior de 512,768 etc cubre por encima al contenido que
  importa de verdad. Prueba a que la guideline sea horizontal en lugar de vertical y que esté
  abajo, ensanchando asi el espacio para el contenido. quizás dejando los selectores 512, 768 etc
  fijos arriba».
- **Hilo, descartado:** «no sabes en que pasos estas ni cuales quedan, no se ve bien».
- **Luz del puntero:** con 150/110 px, «que sea un poco más pequeña».
- **Alice y Bob en el fondo:** «me gusta la idea, pero no se diferencian bien».

Ronda 3: pendiente de que compare Riel y la nueva Capa.
