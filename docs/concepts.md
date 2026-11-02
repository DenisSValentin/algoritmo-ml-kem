# ML-KEM explicado paso a paso

Esta guía explica, sin dar nada por sabido, las matemáticas que hay detrás de ML-KEM y
cómo se traducen en el código. El visualizador (`python -m visualizer`) enseña lo mismo
con una ejecución real; conviene tenerlo abierto mientras se lee.

## 0. El problema: acordar una clave en público

Alice y Bob quieren cifrar una conversación con AES, para lo que necesitan la misma clave
de 256 bits. Pero solo pueden hablar por un canal que cualquiera escucha.

Hoy se resuelve con criptografía de clave pública: RSA o curvas elípticas (ECDH). Su
seguridad se basa en que factorizar números enormes o calcular logaritmos discretos es
muy difícil... para un ordenador clásico. El **algoritmo de Shor** los resuelve en un
ordenador cuántico suficientemente grande. Y como alguien puede grabar hoy el tráfico y
descifrarlo dentro de diez años ("*harvest now, decrypt later*"), el cambio tiene que
hacerse antes de que ese ordenador exista.

**ML-KEM** (antes CRYSTALS-Kyber) es el sustituto que estandarizó NIST en agosto de 2024
(FIPS 203). Es un **KEM**, *Key-Encapsulation Mechanism*, y consta de tres algoritmos:

| Algoritmo | Quién | Entrada | Salida |
|---|---|---|---|
| `KeyGen` | Alice | — | clave pública `ek`, clave privada `dk` |
| `Encaps` | Bob | `ek` | clave compartida `K`, texto cifrado `c` |
| `Decaps` | Alice | `dk`, `c` | `K` |

Por el canal solo viajan `ek` y `c`. Un espía que los vea no puede calcular `K`.

Diferencia con el cifrado de clave pública "clásico": en un KEM no eliges el mensaje. Bob
no cifra una clave que él haya decidido; el algoritmo *genera* `K` y a la vez el texto
cifrado que permite a Alice reconstruirla. Es más simple y más difícil de usar mal.

## 1. Aritmética modular: el reloj de 3329 horas

Todos los números de ML-KEM son **enteros módulo q = 3329**. Se escribe **Z_q**: el
conjunto {0, 1, ..., 3328} donde, al pasarse de 3328, se vuelve a empezar desde 0. Es como
un reloj, pero de 3329 horas en lugar de 12:

```
3000 + 500 = 3500 → 3500 − 3329 = 171
5 − 7 = −2 → −2 + 3329 = 3327
```

Dos ideas que se usan constantemente:

- **Números "pequeños".** 3327 es lo mismo que −2, así que es un número pequeño (está a
  2 pasos del 0 en el reloj). Lo que importa es la distancia al 0 dando la vuelta por el
  lado más corto. En el código, `centered()` convierte {0..3328} en {−1664..1664}.
- **0 y q/2 son los puntos más alejados.** 1665 está justo enfrente del 0 en el reloj. ML-KEM
  esconde cada bit del mensaje como 0 (bit 0) o 1665 (bit 1): aunque se les sume ruido, se
  siguen distinguiendo mientras el ruido no llegue a q/4 ≈ 832.

¿Por qué 3329? Es primo (así todo número distinto de 0 tiene inverso) y 3328 = 2⁸·13, lo
que hace que exista la NTT (sección 8). Además es pequeño: cabe en 12 bits.

## 2. Polinomios y el anillo R_q

En lugar de números sueltos, ML-KEM trabaja con **polinomios de 256 coeficientes**:

```
f(X) = f₀ + f₁·X + f₂·X² + ... + f₂₅₅·X²⁵⁵      con cada fᵢ en Z_q
```

En el código, un polinomio es simplemente un array de 256 enteros. Sumar dos polinomios es
sumar coeficiente a coeficiente (módulo q). Multiplicarlos es más interesante: el producto
de dos polinomios de grado 255 tiene grado 510, así que hay que "doblarlo" para volver a 256
coeficientes. La regla es

```
X²⁵⁶ = −1
```

Es decir, se trabaja en **R_q = Z_q[X] / (X²⁵⁶ + 1)**. Cuando un término "se sale" por
arriba, vuelve por abajo con el signo cambiado. Por ejemplo, con solo 4 coeficientes
(X⁴ = −1):

```
(1 + 2X + 3X² + 4X³) · X = X + 2X² + 3X³ + 4X⁴ = −4 + X + 2X² + 3X³
```

El paso 3 del visualizador tiene este mismo ejemplo con 8 coeficientes y un botón para
multiplicar por X.

¿Para qué tanto lío? Un polinomio de R_q se comporta como una matriz de 256×256 muy
especial: basta con guardar sus 256 coeficientes, no los 65 536 elementos de la matriz.
Eso es lo que hace que las claves de ML-KEM ocupen kilobytes y no megabytes.

## 3. Vectores y matrices de polinomios: el "módulo" y el parámetro k

ML-KEM usa **vectores de k polinomios** y **matrices de k×k polinomios**. Al conjunto de
vectores de k polinomios se le llama un **módulo** sobre R_q (R_q^k), y de ahí el nombre
*Module-Lattice-based KEM*.

**k es lo que se elige al escoger el conjunto de parámetros**, y es lo que en la interfaz
del TFG se podía cambiar:

| Conjunto | k | Matriz A | Dimensión del retículo (k·256) | Seguridad comparable a |
|---|---|---|---|---|
| ML-KEM-512 | 2 | 2×2 polinomios | 512 | AES-128 |
| ML-KEM-768 | 3 | 3×3 polinomios | 768 | AES-192 |
| ML-KEM-1024 | 4 | 4×4 polinomios | 1024 | AES-256 |

Multiplicar una matriz por un vector funciona igual que con números, solo que cada
producto es un producto de polinomios en R_q:

```
(A·s)ᵢ = Aᵢ₀·s₀ + Aᵢ₁·s₁ + ... + Aᵢ,ₖ₋₁·sₖ₋₁
```

## 4. Retículos

Un **retículo** (*lattice*) es el conjunto de todos los puntos que se obtienen combinando
unos vectores base con coeficientes **enteros**:

```
L = { a₁·b₁ + a₂·b₂ + ... + aₙ·bₙ  :  a₁, ..., aₙ enteros }
```

En 2 dimensiones es una rejilla de puntos, quizá inclinada (paso 2 del visualizador). Dos
problemas clásicos sobre retículos:

- **SVP** (*Shortest Vector Problem*): encontrar el punto del retículo más cercano al origen
  (sin contar el propio origen).
- **CVP** (*Closest Vector Problem*): dado un punto cualquiera, encontrar el punto del
  retículo más cercano a él.

En 2 dimensiones se resuelven a simple vista. El problema es que la dificultad crece de
forma exponencial con la dimensión, y con cientos de dimensiones los mejores algoritmos
conocidos, clásicos y cuánticos, tardarían más que la edad del universo. A diferencia de
la factorización, no se conoce ningún algoritmo cuántico tipo Shor que los acelere.

## 5. LWE: aprender con errores

Supón que te doy una matriz A y un vector t, y te digo que `t = A·s`. Encontrar s es
resolver un sistema de ecuaciones lineales: Gauss lo hace en un instante.

Ahora te doy `t = A·s + e`, donde **e es un vector de errores pequeños** que no conoces. De
repente el problema es dificilísimo: cada ecuación es "casi" cierta, y la eliminación de
Gauss amplifica los errores hasta que el resultado no sirve. Este es el problema
**LWE** (*Learning With Errors*, Regev, 2005).

La conexión con los retículos: los valores `A·s` (para todos los s posibles) forman un
retículo, y `t` es un punto *cercano* a ese retículo (está desplazado por e). Encontrar s
equivale a encontrar el punto del retículo más cercano a t: un CVP.

Variantes, de menos a más estructurada:

- **LWE**: A es una matriz de números. Claves enormes (cientos de kB).
- **Ring-LWE**: A es un único polinomio de R_q. Claves pequeñas, pero mucha estructura
  algebraica (que en teoría podría explotarse).
- **Module-LWE**: A es una matriz k×k de polinomios. El punto intermedio: claves pequeñas y
  menos estructura que Ring-LWE. Además, cambiar el nivel de seguridad es tan sencillo como
  cambiar k. **Es lo que usa ML-KEM.**

### Un ejemplo de juguete con números pequeños

Con q = 17 (así q/2 ≈ 9) y vectores de 2 números en lugar de polinomios:

```
A = | 3  5 |     s = ( 1, −1)     e = (1, 0)
    | 7  2 |

t = A·s + e = (3 − 5 + 1, 7 − 2 + 0) = (−1, 5) = (16, 5)   (mod 17)
```

La clave pública es (A, t); la privada, s. Para cifrar el bit m = 1, Bob elige su propio
secreto pequeño y = (1, 0) y errores pequeños e₁ = (0, 1), e₂ = −1:

```
u = Aᵀ·y + e₁ = (3, 5) + (0, 1)         = (3, 6)
v = tᵀ·y + e₂ + 9·m = 16 − 1 + 9 = 24   = 7      (mod 17)
```

Alice descifra con s:

```
w = v − sᵀ·u = 7 − (1·3 + (−1)·6) = 7 + 3 = 10
```

10 está a distancia 1 de 9 (q/2) y a distancia 7 de 0, así que el bit es **1**. ✓

¿Por qué funciona? Desarrollando:

```
w = v − sᵀ·u
  = (sᵀAᵀ + eᵀ)·y + e₂ + 9m − sᵀ·(Aᵀ·y + e₁)
  = eᵀ·y − sᵀ·e₁ + e₂ + 9m
```

El término `sᵀAᵀy` aparece en los dos lados y se cancela: esa era la **máscara**, lo que
hacía que v pareciera aleatorio. Lo que queda es el mensaje (9m) más un ruido formado solo
por productos de cosas pequeñas (e, y, s, e₁, e₂), que sigue siendo pequeño. En el ejemplo,
ese ruido vale 1·1 − (1·0 + (−1)·1) − 1 = 1, y por eso w = 9 + 1 = 10.

ML-KEM es exactamente esto, pero con polinomios de 256 coeficientes en lugar de números (así
cada cifrado transporta 256 bits a la vez) y con k polinomios por vector.

## 6. El ruido: distribución binomial centrada (CBD)

Los secretos y errores (s, e, y, e₁, e₂) deben ser pequeños pero impredecibles. ML-KEM los
saca de la **distribución binomial centrada** con parámetro η: se toman 2η bits aleatorios
y se calcula

```
(b₁ + b₂ + ... + b_η) − (b_η+1 + ... + b_2η)
```

El resultado está entre −η y η, y es más probable cerca de 0 (como lanzar η monedas dos
veces y restar el número de caras). Con η = 2 los valores van de −2 a 2 con probabilidades
1/16, 4/16, 6/16, 4/16, 1/16. Es fácil de calcular sin ramas ni tablas, lo que ayuda a
implementarlo en tiempo constante. En el código: `sample_poly_cbd`.

Aquí está el equilibrio de todo el esquema: **más ruido = más seguro, pero más probable que
el descifrado falle**. Los parámetros están elegidos para que la probabilidad de fallo sea
despreciable (2⁻¹³⁹ para ML-KEM-512, 2⁻¹⁶⁵ para ML-KEM-768).

## 7. Compresión

Cada coeficiente ocupa 12 bits. Para que el texto cifrado ocupe menos, Bob se queda solo con
los d bits más significativos de cada coeficiente de u (d_u = 10 u 11) y de v (d_v = 4 o 5):

```
Compress_d(x)   = ⌈(2^d / q) · x⌋ mod 2^d
Decompress_d(y) = ⌈(q / 2^d) · y⌋
```

Comprimir y descomprimir no devuelve el valor original, sino uno cercano: es como guardar
una foto en JPEG. Ese pequeño error se suma al ruido, y los parámetros ya lo tienen en
cuenta. El mensaje se "comprime" a 1 bit: `Compress₁(w)` vale 1 si w está más cerca de q/2
que de 0, que es justo la regla de descifrado.

Cuidado con el redondeo ⌈x⌋: FIPS 203 redondea los empates **hacia arriba** (1664,5 → 1665)
y prohíbe la coma flotante. Ese detalle es uno de los dos fallos que tenía el TFG
(ver [review.md](review.md)).

## 8. La NTT: multiplicar polinomios rápido

Multiplicar dos polinomios de 256 coeficientes "a mano" cuesta 256² = 65 536
multiplicaciones. La **NTT** (*Number-Theoretic Transform*) es la versión de la
transformada de Fourier (FFT) para aritmética modular, y reduce el coste a unos pocos miles.

La idea, igual que con la FFT: en vez de describir un polinomio por sus coeficientes, se
describe por lo que vale en ciertos puntos especiales. En esa representación, multiplicar
dos polinomios es multiplicar sus valores punto a punto.

Los "puntos especiales" son potencias de **ζ = 17**, que es una raíz 256-ésima de la unidad
módulo 3329 (17²⁵⁶ ≡ 1 y ninguna potencia menor da 1). Existe porque 256 divide a q − 1 =
3328. Lo que no existe es una raíz 512-ésima, y por eso la NTT de ML-KEM es "incompleta":
no llega a 256 valores sueltos, sino a **128 polinomios de grado 1**. Multiplicar en el
dominio NTT es multiplicar esos 128 pares (`BaseCaseMultiply`):

```
(a₀ + a₁X)(b₀ + b₁X) mod (X² − γ) = (a₀b₀ + a₁b₁γ) + (a₀b₁ + a₁b₀)X
```

Detalles que aparecen en el código:

- **BitRev₇**: las potencias de ζ se usan en orden de bits invertidos, igual que en la FFT.
  Las tablas `ZETAS` y `GAMMAS` del apéndice A del estándar se calculan en `ring.py` a partir
  de esa definición (y un test comprueba que coinciden con el apéndice).
- **3303**: es el inverso de 128 módulo q. La NTT inversa termina multiplicando por él.
- **Â se genera ya en dominio NTT**: como es aleatoria y uniforme, da igual generarla en un
  dominio u otro, y así se ahorra una transformación.

## 9. Las funciones hash

ML-KEM usa cuatro funciones de la familia SHA-3, cada una con un papel:

| Nombre | Función | Uso |
|---|---|---|
| `G` | SHA3-512 | Partir una semilla en dos: (ρ, σ) en KeyGen, (K, r) en Encaps |
| `H` | SHA3-256 | Resumen de la clave pública, H(ek) |
| `J` | SHAKE256 | Clave falsa del rechazo implícito, J(z ‖ c) |
| `PRF` | SHAKE256 | Bytes aleatorios para muestrear el ruido CBD |
| `XOF` | SHAKE128 | Flujo de bytes para generar la matriz Â (`SampleNTT`) |

SHAKE es un XOF (*extendable-output function*): un hash del que puedes sacar tantos bytes
como quieras. `SampleNTT` lee bytes de 3 en 3, saca dos números de 12 bits de cada grupo y
se queda con los que son menores que q (muestreo por rechazo) hasta tener 256.

## 10. De K-PKE a ML-KEM: la transformación de Fujisaki-Okamoto

Lo explicado hasta ahora (secciones 5–7) es **K-PKE**, un cifrado de clave pública. K-PKE es
seguro frente a un atacante que solo mira (seguridad *IND-CPA*), pero no frente a uno que
puede enviar textos cifrados manipulados y ver qué pasa (*IND-CCA*): modificando c poco a
poco y observando si Alice obtiene la misma clave, podría ir deduciendo s.

ML-KEM lo blinda con la **transformación de Fujisaki-Okamoto**:

1. **Encaps.** Bob no elige r al azar: lo deriva del mensaje, `(K, r) = G(m ‖ H(ek))`. Así el
   cifrado es determinista: el mismo m da siempre el mismo c.
2. **Decaps.** Alice descifra m′, recalcula `(K′, r′) = G(m′ ‖ H(ek))` y **vuelve a cifrar**
   m′ con r′. Si el resultado c′ es idéntico al c recibido, nadie lo ha tocado y devuelve K′.
3. **Rechazo implícito.** Si c′ ≠ c, Alice no devuelve un error (eso daría información al
   atacante), sino `K̄ = J(z ‖ c)`, una clave pseudoaleatoria que depende de un secreto z
   guardado en dk. Para el atacante, una clave basura es indistinguible de una buena.

Por eso dk guarda, además de s, la clave pública, su hash y z:

```
dk = s (384·k bytes) ‖ ek (384·k + 32) ‖ H(ek) (32) ‖ z (32)   →   768·k + 96 bytes
```

## 11. El algoritmo completo

**KeyGen** (Alice)

1. d, z ← 32 bytes aleatorios cada uno.
2. (ρ, σ) = G(d ‖ k).
3. Â[i, j] = SampleNTT(ρ ‖ j ‖ i) para i, j de 0 a k−1.
4. s, e ← CBD_η₁ usando PRF(σ, 0), PRF(σ, 1), ...
5. t̂ = Â·NTT(s) + NTT(e).
6. ek = ByteEncode₁₂(t̂) ‖ ρ.  dk = ByteEncode₁₂(ŝ) ‖ ek ‖ H(ek) ‖ z.

**Encaps(ek)** (Bob)

1. m ← 32 bytes aleatorios.
2. (K, r) = G(m ‖ H(ek)).
3. y ← CBD_η₁, e₁, e₂ ← CBD_η₂ usando PRF(r, ...).
4. u = NTT⁻¹(Âᵀ·NTT(y)) + e₁.
5. v = NTT⁻¹(t̂ᵀ·NTT(y)) + e₂ + Decompress₁(m).
6. c = ByteEncode(Compress_du(u)) ‖ ByteEncode(Compress_dv(v)). Devuelve (K, c).

**Decaps(dk, c)** (Alice)

1. u′, v′ ← descomprimir c.
2. w = v′ − NTT⁻¹(ŝᵀ·NTT(u′)).  m′ = ByteEncode₁(Compress₁(w)).
3. (K′, r′) = G(m′ ‖ H(ek)).  c′ = cifrar m′ con r′.
4. Si c′ = c devuelve K′; si no, J(z ‖ c).

## 12. Dónde está cada cosa en el código

| Concepto | Fichero | Funciones |
|---|---|---|
| Parámetros (k, η, d) | `mlkem/params.py` | `ParameterSet`, `ML_KEM_768`... |
| Z_q, R_q, NTT | `mlkem/ring.py` | `ntt`, `inverse_ntt`, `multiply_ntts`, `matrix_vector_ntt` |
| Bits, bytes, compresión | `mlkem/encoding.py` | `byte_encode`, `compress`, `decompress` |
| Muestreo | `mlkem/sampling.py` | `sample_ntt`, `sample_poly_cbd` |
| Hashes | `mlkem/hashes.py` | `g`, `h`, `j`, `prf`, `xof` |
| K-PKE | `mlkem/kpke.py` | `keygen`, `encrypt`, `decrypt` |
| ML-KEM + comprobaciones | `mlkem/kem.py` | `MLKEM.keygen`, `encaps`, `decaps` |

Cada función indica en su docstring el número de algoritmo de FIPS 203 que implementa.

## Glosario

- **KEM**: mecanismo de encapsulamiento de claves (KeyGen, Encaps, Decaps).
- **ek / dk**: clave de encapsulamiento (pública) / de desencapsulamiento (privada).
- **Z_q**: enteros módulo q = 3329.
- **R_q**: polinomios de 256 coeficientes en Z_q con X²⁵⁶ = −1.
- **T_q**: los mismos polinomios en representación NTT (se marcan con ^, como Â o ŝ).
- **k**: número de polinomios por vector (2, 3 o 4).
- **η₁, η₂**: tamaño máximo del ruido.
- **d_u, d_v**: bits por coeficiente al comprimir u y v.
- **LWE / Module-LWE**: el problema difícil en el que se basa la seguridad.
- **CBD**: distribución binomial centrada, para generar ruido pequeño.
- **NTT**: transformada que acelera la multiplicación de polinomios.
- **FO**: transformación de Fujisaki-Okamoto (re-cifrado + rechazo implícito).
- **ACVP / KAT**: vectores de prueba oficiales con entradas y salidas conocidas.
