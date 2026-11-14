# Design

Sistema visual del visualizador de ML-KEM (`visualizer/`). Producto y público: `PRODUCT.md`.
Crítica del diseño de partida: `docs/design-critique.md`.

> **Estado (2026-11-14): diseño definitivo elegido por Denis** tras tres rondas de prototipos,
> ya aplicado en `visualizer/static/{index.html,style.css,app.js}` en la rama
> `claude/redesign-3-propuestas-c212d3`. Se publica al mergear a `main`.

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
- **En la animación solo se ve lo que se mueve:** ni esquinas, ni rayas, ni restos alrededor.
  Nada de `backdrop-filter` en piezas pequeñas que se deslizan, y cada animación se comprueba
  fotograma a fotograma (a mitad y al llegar), no solo el antes y el después.
  <!-- 2026-11-14: «yo quiero que solo se vea la bola, que no haya nada más alrededor» (salían las esquinas del filtro); antes, «aparece una rayita horizontal» -->
- **El vidrio deja ver poco:** opacidad del tinte ≥ 64 % (fino), 78 % (normal), 88 % (grueso).
  <!-- 2026-11-13: «quizás podría ser un poco menos transparente» -->
- **Detrás del vidrio, nada que se confunda con él:** los puntitos pequeños del retículo sí se
  confundían. Un dibujo de fondo no está prohibido si se distingue bien del material (por
  ejemplo, para diferenciar a Alice y Bob): hay que probarlo y que Denis lo vea.
  <!-- 2026-11-13: «que el fondo tenga puntitos confunde con el liquid glass»; luego «quizas siendo ahora más opaco algun dibujo si encaje bien, para diferenciar a alice y bob» -->

## Comportamiento

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

## Composición

- **Cabecera** (lámina de vidrio fina): título y descripción a la izquierda (qué es en una línea
  y de quién es en otra); a la derecha, en la misma fila, el selector de parámetros (512 / 768 /
  1024) y centrados debajo «Nueva ejecución» y «Manipular c». Por debajo de 900 px se apila.
- **Contenido a todo el ancho** (máx. 1240 px): Alice · canal · Bob en una lámina fina; debajo,
  texto (lámina gruesa) y figura (lámina normal) en dos columnas, una sola por debajo de 1100 px.
- **Dock flotante abajo**, de vidrio: «anterior» · línea horizontal del 1 al 9 · «siguiente».
  Nombres de los pasos en pantallas anchas; números en las estrechas (el paso actual con nombre
  hasta 640 px). La parada actual es una gota de vidrio que se desliza por la línea.
- **El dock no se anima en el cambio de paso** y queda por encima del contenido: tiene nombre
  propio de View Transition (`dock`, `dock-line`) y durante la transición su lámina se vuelve
  casi opaca, porque el navegador lo pinta como una foto sin desenfoque en vivo.

## Colors (color)

Tokens en `visualizer/static/style.css` (`:root`, con su versión `prefers-color-scheme: dark`).

| Token | Claro | Oscuro | Uso |
|---|---|---|---|
| `--bg` | `#eef1f6` | `#0a0d14` | fondo bajo el vidrio |
| `--text` | `#0c1222` | `#eef1f8` | texto |
| `--muted` | `#4a5468` | `#aab3c5` | texto secundario |
| `--accent` | `#5432d3` | `#a996ff` | la línea: tramo recorrido, lo elegido, «siguiente» |
| `--on-accent` | `#ffffff` | `#150c38` | texto sobre el acento |
| `--ok` / `--bad` | `#0f7a49` / `#bf2a1c` | `#55d394` / `#ff8070` | correcto / error y manipulación |
| `--neg` / `--pos` | `#1f6feb` / `#e2590f` | `#5b9bff` / `#ff8a45` | coeficientes negativos / positivos |
| `--plate` | `#0f1724` | `#e8edf4` | placas de las ecuaciones |
| `--glow-alice-*` | azul y turquesa | | fondo cuando actúa Alice (mitad izquierda) |
| `--glow-bob-*` | naranja y coral | | fondo cuando actúa Bob (mitad derecha) |

Uniformes en paleta *plasma* (en `app.js`). Contraste medido: texto ≥ 13,8:1 sobre el vidrio,
secundario ≥ 6,3:1, texto sobre el acento ≥ 7,4:1, verde «correcto» ≥ 4,5:1.

## Typography (tipografía)

- **Overpass** (señalética) para todo; **Overpass Mono** para datos, hex y ecuaciones. Desde
  Google Fonts.
- El punto medio «·» sale de la letra del sistema (`@font-face` «Punto medio» con
  `unicode-range: U+00B7`): el de Overpass no ocupa ancho y se comía el espacio siguiente.
- Títulos 800, 1,75 rem (1,375 rem en móvil), tracking −0,02 em; cuerpo 1 rem / 1,6.

## Components (componentes)

- **Botones con relieve** (`button`): cara con degradado `--btn-face-1 → --btn-face-2`, filo
  `--btn-hi` arriba, sombra `--btn-shadow`; al pulsar bajan 1 px con `--btn-pressed`.
  Principal (`.primary`): cara del color del acento. «Manipular c» activo queda hundido.
- **Selectores segmentados** (parámetros y 2D/3D): pista hundida (`--track`, `--track-shadow`),
  opciones de igual ancho y texto centrado, y una pieza `.seg-thumb` del color del acento, sin
  filo blanco y con una sombra suave, que se desliza solo con `transform` (320 ms, ease-out). Los
  botones de dentro no tienen cara propia (ni hundirse, ni filo al pasar el ratón). Al cambiar
  de parámetros, los datos nuevos se pintan cuando la pieza ha llegado, para no entrecortarla.
- **Aviso de manipulación** (`.tamper-banner`): fijo arriba, por encima de todo, como el dock
  abajo, con botón «Desactivar» (en el móvil no hay tecla M).
- **Controles del retículo:** ruido, «Nuevo punto» y «Mostrar / ocultar solución» en una línea;
  la barra encoge lo necesario y solo en móvil los botones bajan juntos.
- **Láminas de vidrio**: ver «Liquid glass».
- **Ecuaciones** (`.formula`): placa oscura `--plate` con Overpass Mono, como un cartel de andén.
- **Cifras de las figuras** (`.stat`): sin caja; número y etiqueta separados por una regla fina.
- **Alice · canal · Bob** (`.flow`): la parte que actúa lleva anillo del acento; `ek` y `c`
  cruzan el canal como una ficha la primera vez que se llega a un paso donde viajan.

## Cómo se llegó aquí (prototipos)

- **Ronda 1:** Línea (recorrido como línea de transporte), Estándar (documento tipo FIPS),
  Vidrio (liquid glass sobre puntos). De Línea quedó la línea de pasos; de Vidrio, el material.
- **Ronda 2:** Riel (Línea + vidrio), Capa (vidrio solo en la navegación flotante), Hilo (la línea
  atraviesa el contenido, descartada).
- **Ronda 3:** Riel y Capa rehecha (línea horizontal abajo). **Definitivo:** cabecera y contenido
  de Riel, ancho y dock de Capa.

Los commits `9e2742f`, `87fd80a` y `35eba51` guardan cada ronda.

## Liquid glass (solo en esta app)

No es un estándar global ni de otros proyectos: es una prueba aquí. Ninguna skill instalada lo
define (`apple-design` solo cubre materiales translúcidos en general), así que esta es la
definición, corregida tras la primera ronda.

### Qué es
El material de iOS 26: vidrio translúcido que deja ver lo de detrás desenfocado, **refleja** la luz con un brillo especular, tiene **profundidad** (sombra y filo
iluminado arriba) y **se adapta** a lo que tiene detrás.

### Cómo se construye
| Capa | Qué hace | Cómo |
|---|---|---|
| Lámina | Tinte + desenfoque | `::before` con el tinte del grosor y `backdrop-filter: blur() saturate(1.6)` |
| Filo | Luz que entra por arriba y se apaga abajo | `::after` de 1 px (máscara que solo deja el borde) con degradado vertical |
| Luz del puntero | Reflejo pequeño de una sola luz | en el filo, un círculo de **100 px**; dentro de la lámina, otro de **70 px** muy tenue (35 % en claro, 6 % en oscuro). Fijos a la ventana, así todas las láminas reflejan la misma luz. Solo con ratón |
| Profundidad | Flota | sombra exterior suave con desplazamiento (`--glass-shadow`) |
| Adaptación | Se tiñe con quien actúa | fondo azul a la izquierda con Alice y cálido a la derecha con Bob, y el tinte del vidrio se mezcla con ese color (`--phase-tint`); 700 ms |

El vidrio va en el **pseudo-elemento** (`::before`), no en el elemento, para que el filo y la
luz (`::after`) queden encima de la lámina.

**Sin refracción y sin `backdrop-filter` en piezas pequeñas que se mueven** (la gota del paso
actual): el filtro trabaja sobre un cuadrado y, al moverse o al llegar a su sitio en una
transición, se veían sus cuatro esquinas. Su aspecto de cristal sale del brillo y el anillo.

### Grosores (los únicos tres)
| Grosor | Uso | Claro | Oscuro | Desenfoque |
|---|---|---|---|---|
| Fino | cabecera, Alice/canal/Bob | blanco 64 % | `#1a1f2e` 68 % | 16 px |
| Normal | figura y dock (grueso en móvil) | blanco 78 % | `#141825` 80 % | 24 px |
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
  vuelve a desenfocar lo de detrás): hay 5 láminas (cabecera, Alice/Bob, texto, figura y dock).
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

Ronda 3 (2026-11-14), con sus palabras — **diseño definitivo**:

- «La seccion superior de Riel pero que el selector de 512, 768 etc aparezca a la derecha del
  titulo y descripcion del ml-kem, es decir, en la misma fila en lugar de debajo.»
- «El contenido de Riel, me gusta la opacidad que tiene y como se ve, pero como el guideline se
  va a quedar abajo, horizontal y flotante, aplicale la anchura que tiene el diseño B Capa.»
- «el guideline se queda abajo horizontal, como lo tiene Capa, pero arregla ese bug de que
  aparece y desaparece» (el dock se escondía detrás del contenido al cambiar de paso).
- «El fondo me gusta el que hay … con los colores diferenciados para bob y alice.»
- Luz del puntero de 100 / 70 px: «me gusta».
