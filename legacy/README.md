# Código original del TFG (septiembre de 2024)

Estos dos ficheros son la implementación tal y como se entregó con la memoria. Se conservan
como referencia (la memoria cita su código) y para comparar con la versión actual en
[`mlkem/`](../mlkem/).

No se deben usar: tienen dos desviaciones respecto a FIPS 203 final que los hacen
incompatibles con otras implementaciones, usan un generador aleatorio no criptográfico y no
funcionan con NumPy 2. Todo está explicado en [docs/review.md](../docs/review.md).

Para ejecutarlos hace falta NumPy 1.x. Con uv, sin tocar el entorno del proyecto:

```bash
cd legacy
uv run --no-project --python 3.11 --with "numpy<2" python ml_kem_main.py
```
