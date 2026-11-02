"""Conversión entre bits, bytes y enteros, y compresión (FIPS 203, secciones 4.2.1 y 4.2.2).

Las cadenas de bytes se manejan como `bytes` de Python; los polinomios como arrays de
NumPy. Las conversiones usan np.packbits/np.unpackbits en orden little-endian, que es
exactamente el orden de bits que define el estándar.
"""

from __future__ import annotations

import numpy as np

from .params import N, Q


def bits_to_bytes(bits: np.ndarray) -> bytes:
    """Algoritmo 3."""
    return np.packbits(np.asarray(bits, dtype=np.uint8), bitorder="little").tobytes()


def bytes_to_bits(data: bytes) -> np.ndarray:
    """Algoritmo 4."""
    return np.unpackbits(np.frombuffer(data, dtype=np.uint8), bitorder="little")


def byte_encode(f: np.ndarray, d: int) -> bytes:
    """Algoritmo 5: serializa enteros de d bits (forma (..., 256)) en 32·d bytes por polinomio."""
    f = np.asarray(f, dtype=np.int64)
    bits = (f[..., np.newaxis] >> np.arange(d)) & 1
    return bits_to_bytes(bits.reshape(-1))


def byte_decode(data: bytes, d: int) -> np.ndarray:
    """Algoritmo 6: inversa de byte_encode. Devuelve forma (256,) o (k, 256) según la longitud."""
    bits = bytes_to_bits(data).reshape(-1, N, d).astype(np.int64)
    f = (bits << np.arange(d)).sum(axis=-1)
    if d == 12:
        f %= Q
    return f[0] if f.shape[0] == 1 else f


def compress(x: np.ndarray, d: int) -> np.ndarray:
    """Compress_d(x) = ⌈(2^d / q)·x⌋ mod 2^d, con aritmética entera exacta.

    ⌈a/b⌋ (redondeo con empates hacia arriba) = ⌊(2a + b) / 2b⌋. El TFG usaba floats y la
    función round() de Python, que redondea los empates al par ("banker's rounding").
    """
    x = np.asarray(x, dtype=np.int64)
    return (((x << (d + 1)) + Q) // (2 * Q)) & ((1 << d) - 1)


def decompress(y: np.ndarray, d: int) -> np.ndarray:
    """Decompress_d(y) = ⌈(q / 2^d)·y⌋, con aritmética entera exacta.

    Aquí sí hay empates (p. ej. q·1/2 = 1664,5): el estándar exige 1665 y round() da 1664.
    """
    y = np.asarray(y, dtype=np.int64)
    return (y * Q + (1 << (d - 1))) >> d
