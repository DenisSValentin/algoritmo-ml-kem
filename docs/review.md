# Fe de erratas y revisión del TFG

La memoria (`Memoria_TFG_Denis_Stoyanov.pdf`) y el código de [`legacy/`](../legacy/) se
conservan tal y como se entregaron y defendieron en septiembre de 2024. Este documento
recoge lo que una revisión posterior encontró en ese código, contrastándolo con
[FIPS 203 final](https://csrc.nist.gov/pubs/fips/203/final) (agosto de 2024), con su
borrador (`ipd`, agosto de 2023) y con los vectores de prueba oficiales de NIST (ACVP), y
cómo se ha corregido en la versión actual ([`mlkem/`](../mlkem/)).

Las figuras de código de los capítulos 7 y 8 de la memoria corresponden a la versión de
2024. Donde la memoria y este documento no coincidan, vale lo que dice este documento.

## Resumen

**La implementación tenía sentido y la parte matemática estaba bien entendida.** NTT,
NTT inversa, multiplicación en el dominio NTT, muestreo CBD, `SampleNTT`, las funciones
hash, la estructura de K-PKE y la transformación de Fujisaki-Okamoto eran correctas.

Pero **no era interoperable**: ninguna clave generada coincidía con la de otra
implementación de FIPS 203. Había dos causas, y con solo esas dos correcciones el código
original pasa el 100 % de los vectores de NIST:

| Prueba con vectores ACVP de NIST | Original | + arreglo 1 | + arreglos 1 y 2 |
|---|---|---|---|
| KeyGen (75 casos) | 0/75 | 75/75 | 75/75 |
| Encaps, texto cifrado ML-KEM-512 | — | 16/25 | 25/25 |
| Encaps, texto cifrado ML-KEM-768 | — | 12/25 | 25/25 |
| Encaps, texto cifrado ML-KEM-1024 | — | 5/25 | 25/25 |

¿Por qué en el TFG "funcionaba"? Porque la prueba era que `K == K'` entre dos llamadas del
mismo programa. Si Alice y Bob usan el mismo código con el mismo fallo, el fallo se
cancela. Esa prueba no puede detectar este tipo de errores: hacen falta **vectores de
prueba conocidos** (KAT), que es la infraestructura que más se echaba en falta.

## Hallazgos

Los números de línea se refieren a [`legacy/ml_kem.py`](../legacy/ml_kem.py).

### 1. Índices de la matriz Â del borrador, no de la versión final (crítico)

- **Dónde:** líneas 665 y 760: `np.concatenate((rho, i_byte, j_byte))`.
- **Qué pasa:** el borrador definía `Â[i, j] = SampleNTT(XOF(ρ, i, j))`, es decir, `ρ‖i‖j`.
  La versión final usa `ρ‖j‖i` (algoritmos 13 y 14). El apéndice C.2 lo explica: el
  borrador había intercambiado los índices por error y la versión final volvió a lo que hacía
  CRYSTALS-Kyber.
- **Por qué se coló:** al adaptar el código a la versión final se incorporó el otro cambio
  del apéndice C.2 (la separación de dominio `G(d‖k)`, línea 652) pero no este. Y como
  KeyGen y Encrypt usaban el mismo orden, la matriz era la traspuesta de la correcta en los
  dos lados y todo cuadraba.
- **Arreglo:** [`mlkem/kpke.py`](../mlkem/kpke.py), función `expand_matrix`.

### 2. Redondeo con `float` y `round()` (crítico para interoperabilidad)

- **Dónde:** `_Compress` (línea 299) y `_Decompress` (línea 323).
- **Qué pasa:** FIPS 203 define ⌈x⌋ redondeando los empates **hacia arriba** (sección 2.3) y
  avisa expresamente de no usar coma flotante (sección 4.2.1). `round()` de Python redondea
  los empates **al par** ("banker's rounding"). En `Compress` nunca hay empates (q es primo),
  pero en `Decompress` sí: `Decompress₁(1) = ⌈3329/2⌋` debe ser 1665 y el código daba 1664.
  Lo mismo con `Decompress₁₀(512)` o `Decompress₄(8)`. Así, μ y la recompresión en Decaps
  salían distintos y una parte de los textos cifrados no coincidía.
- **Consecuencia real:** si Bob usase el código del TFG y Alice OpenSSL, Alice detectaría
  `c′ ≠ c` y devolvería la clave de rechazo implícito. Según la tabla de arriba, fallarían
  entre un tercio (ML-KEM-512) y cuatro de cada cinco (ML-KEM-1024) intercambios.
- **Arreglo:** aritmética entera exacta en [`mlkem/encoding.py`](../mlkem/encoding.py):
  `Compress_d(x) = ⌊(2^(d+1)·x + q) / 2q⌋ mod 2^d` y `Decompress_d(y) = (q·y + 2^(d−1)) >> d`.

### 3. Generador aleatorio no criptográfico (crítico para seguridad)

- **Dónde:** líneas 1265, 1266 y 1301: `np.random.randint`.
- **Qué pasa:** `np.random` es un Mersenne Twister. Con unos cientos de salidas observadas se
  puede reconstruir su estado y predecir todas las siguientes: d, z y m, es decir, las claves
  privadas y las claves compartidas. FIPS 203 exige un generador aprobado (sección 3.3).
- **Arreglo:** `secrets.token_bytes(32)`, que usa el CSPRNG del sistema operativo.

### 4. Las comprobaciones de entrada no estaban en la API pública (importante)

- `ML_KEM_Encaps` no comprobaba `ek` (tipo y módulo, sección 7.2) y `ML_KEM_Decaps` no
  comprobaba `dk` (tipo y hash, sección 7.3). Las funciones existían (`_comprobarEkValida`,
  `_comprobarDkValida`) pero solo las llamaba la interfaz. El estándar dice que Encaps
  *no debe* ejecutarse con una clave sin comprobar.
- Además imprimían por pantalla y devolvían `False` en vez de lanzar una excepción.
- **Arreglo:** `MLKEM.encaps` y `MLKEM.decaps` comprueban siempre y lanzan `InvalidInputError`.
  Los tests usan los casos de NIST `encapsulationKeyCheck` y `decapsulationKeyCheck`.

### 5. Con NumPy 2 el código no arranca (importante)

- **Dónde:** `_SamplePolyCBD`, línea 484: `f[i] = (x - y) % ML_KEM.q`.
- **Qué pasa:** `x` e `y` acaban siendo `np.uint8`. Con NumPy 1.x se promocionaban
  silenciosamente a `int64`; NumPy 2 (junio de 2024) cambió las reglas de promoción
  (NEP 50) y ahora `uint8 % 3329` lanza `OverflowError`. Hoy `pip install numpy` instala
  NumPy 2, así que el repositorio tal y como estaba no funciona.
- Es justo el riesgo que la memoria menciona en la sección 7.1 (conversiones automáticas de
  tipos). La solución de fondo: no mezclar tipos de NumPy pequeños con aritmética modular,
  fijar las versiones de las dependencias y tener CI que pruebe varias.

### 6. Estado global mutable (diseño)

- Los parámetros (`k`, `eta_1`, `d_u`...) y las claves eran atributos de clase que
  `establecer_parametros` modificaba. No se podían usar dos conjuntos de parámetros a la vez,
  ni en paralelo, y cambiar de conjunto borraba las claves.
- **Arreglo:** `ParameterSet` inmutable ([`mlkem/params.py`](../mlkem/params.py)) y una
  instancia `MLKEM(params)` por conjunto.

### 7. Detalles menores

- Línea 1022: `ekPKE = decaps_k[384k : 768k+64]` coge 32 bytes de más (incluye `H(ek)`).
  No rompía nada porque K-PKE.Encrypt ignora lo que sobra, pero el corte correcto es `768k+32`.
- `if d is None or z is None` (líneas 1269 y 1304) nunca puede cumplirse.
- `SampleNTT` pedía 840 bytes fijos: es válido (el apéndice B permite limitar a ≥ 280
  iteraciones), pero si se agotaban daba un `IndexError` en vez del comportamiento que pide el
  estándar. La nueva versión pide más bytes al XOF si hace falta.
- La comparación `c == c′` usaba `np.array_equal`. Ahora usa `hmac.compare_digest`, que
  compara en tiempo constante (aunque en Python el resto del código no lo es; ver abajo).
- Interfaz: `int(input())` se cae si se escribe una letra; al cambiar de parámetros no se
  borraban `K`, `K′` ni `c`; y la variable `bloqueo` era difícil de seguir.

## NumPy (y Pandas): ¿se usaron mal?

**Pandas** no aparece en el código, y está bien que no aparezca: sirve para datos tabulares
(tablas con columnas, CSV, estadísticas), no para aritmética de polinomios. **NumPy** sí era
la herramienta adecuada, pero se usaba como si fuera una lista de Python:

```python
# Original: bucle de Python que accede elemento a elemento a un array de NumPy
for i in range(n):
    for j in range(8):
        b[8*i + j] = C[i] % 2
        C[i] = C[i] // 2

# Vectorizado: una sola llamada que hace el bucle en C
bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8), bitorder="little")
```

Acceder a `array[i]` en un bucle es incluso **más lento** que usar una lista normal, porque
cada acceso crea un objeto escalar de NumPy. NumPy solo es rápido cuando una operación
trabaja sobre el array entero. En la versión nueva:

- Bits ↔ bytes: `np.packbits` / `np.unpackbits`.
- `Compress`, `Decompress`, `ByteEncode`, `ByteDecode`, `SamplePolyCBD`: operaciones sobre
  los 256 coeficientes (o los k·256) a la vez.
- NTT: en cada una de las 7 capas, todas las "mariposas" se hacen a la vez cambiando la
  forma del array (`reshape(..., bloques, 2, longitud)`).
- `Â·ŝ`: un único producto con *broadcasting* sobre la matriz k×k, en vez de dos bucles.
- Las cadenas de bytes (claves, textos cifrados, semillas) son `bytes` de Python, no arrays de
  `uint8`. Así se concatenan con `+`, se comparan con `==` y se pasan directamente a `hashlib`.

### Rendimiento (MacBook Pro M5 Pro, mediana en milisegundos)

| | KeyGen antes | KeyGen ahora | Encaps antes | Encaps ahora | Decaps antes | Decaps ahora |
|---|---|---|---|---|---|---|
| ML-KEM-512 | 18,6 | 0,15 | 24,4 | 0,21 | 44,4 | 0,28 |
| ML-KEM-768 | 24,9 | 0,21 | 33,8 | 0,29 | 62,5 | 0,36 |
| ML-KEM-1024 | 33,6 | 0,29 | 45,4 | 0,37 | 84,8 | 0,45 |

Entre 120 y 190 veces más rápido. "Antes" se midió con NumPy 1.26 (con NumPy 2 no arranca).
Se puede repetir con `python -m benchmarks.bench`.

## ¿Python o Go?

En la defensa se preguntó por qué Python y no Go. La respuesta, en resumen:

> Se eligió Python porque el objetivo del TFG era **entender y verificar** el estándar, no
> producir una librería para usar en producción. En Python el código se lee casi igual que el
> pseudocódigo de FIPS 203, lo que permite comprobar algoritmo por algoritmo que se ha
> implementado lo que dice el documento. Para producción nadie debería usar una
> implementación propia, sino una auditada (Go, BoringSSL, OpenSSL, liboqs).

Dicho eso, conviene conocer qué habría aportado cada opción:

| | Python | Go | Rust / C |
|---|---|---|---|
| Legibilidad frente al pseudocódigo | La mejor | Buena | Regular |
| Velocidad (Decaps ML-KEM-768) | ~0,4 ms con NumPy | ~0,03–0,05 ms | ~0,01–0,03 ms |
| Enteros de tamaño fijo (`uint16`, `uint32`) | No (enteros ilimitados) | Sí | Sí |
| Tipado estático (habría evitado el fallo de NumPy 2) | No | Sí | Sí |
| Tiempo constante (contra ataques de canal lateral) | Imposible de garantizar | Posible | Posible |
| Borrar secretos de memoria | No se puede | Parcialmente | Sí |
| ML-KEM en la biblioteca estándar | No | `crypto/mlkem` desde Go 1.24 | — |

- **Go** habría sido una elección muy natural: tiene tipos de tamaño fijo, es rápido, es
  sencillo y su biblioteca estándar incluye ML-KEM (`crypto/mlkem`, febrero de 2025; en 2024 ya
  estaba de forma interna para TLS). Tener la implementación oficial al lado permite comparar
  resultados directamente.
- **Rust o C** son lo que se usa en las implementaciones de referencia y de producción
  (`pq-crystals/kyber` está en C), pero son más difíciles de leer y, en C, más fáciles de
  equivocarse con la memoria.
- **Python** tiene una limitación de fondo: no se puede garantizar tiempo constante (los
  enteros grandes, las ramas y la memoria los gestiona el intérprete) ni borrar los secretos
  de memoria. Para una implementación didáctica no importa; para producción, sí.

Como posible ampliación, una segunda implementación en Go que pase los mismos
vectores de NIST sería un buen complemento: mostraría las dos caras (didáctica y de producción).

## Infraestructura que faltaba (y que ahora tiene)

| Qué | Para qué | Dónde |
|---|---|---|
| Vectores de prueba oficiales (ACVP) | Saber que el resultado coincide con el estándar, no solo consigo mismo | `tests/test_vectors.py` |
| Tests unitarios | NTT frente a multiplicación directa, redondeo frente a la definición exacta en racionales, codificación, manipulación de `c` | `tests/` |
| Dependencias declaradas | `pip install -e .` instala exactamente lo necesario | `pyproject.toml` |
| Integración continua | Pasa tests y linter en Python 3.9 + NumPy 1.x y Python 3.13 + NumPy 2.x en cada push | `.github/workflows/ci.yml` |
| Benchmark reproducible | Mediana de N repeticiones de las tres operaciones | `benchmarks/bench.py` |
| Separar librería e interfaz | El algoritmo no imprime nada ni lee del teclado | `mlkem/` frente a `visualizer/` |
| Linter / formateador | Estilo uniforme, detectar errores comunes | `ruff` |
| `.gitignore` | No subir `.venv`, `__pycache__`... | `.gitignore` |

## Lo que sigue sin resolver (a propósito)

- No es de tiempo constante ni borra los secretos de memoria. Es una implementación
  **educativa**; no debe usarse para proteger datos reales.
- No hace la comprobación de consistencia del par de claves (sección 7.1), que es opcional.
