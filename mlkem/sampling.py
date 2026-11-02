"""Muestreo de polinomios (FIPS 203, sección 4.2.2, algoritmos 7 y 8)."""

from __future__ import annotations

import numpy as np

from .encoding import bytes_to_bits
from .hashes import xof
from .params import N, Q


def sample_ntt(seed: bytes) -> np.ndarray:
    """Algoritmo 7: polinomio uniforme en T_q a partir de 34 bytes (ρ || j || i).

    Cada 3 bytes dan dos candidatos de 12 bits; se aceptan los que son < q (muestreo
    por rechazo). 840 bytes (280 iteraciones, apéndice B) bastan salvo con probabilidad
    2^-261; si no bastaran, se piden más bytes al XOF en vez de fallar, como recomienda
    el estándar ("should not bound this loop").
    """
    length = 840
    while True:
        c = np.frombuffer(xof(seed, length), dtype=np.uint8).astype(np.int64).reshape(-1, 3)
        d1 = c[:, 0] + 256 * (c[:, 1] % 16)
        d2 = c[:, 1] // 16 + 16 * c[:, 2]
        candidates = np.stack([d1, d2], axis=1).reshape(-1)  # d1, d2 en orden de aparición
        accepted = candidates[candidates < Q]
        if accepted.size >= N:
            return accepted[:N]
        length *= 2


def sample_poly_cbd(data: bytes, eta: int) -> np.ndarray:
    """Algoritmo 8: polinomio con coeficientes pequeños en [-eta, eta] (distribución binomial centrada).

    Cada coeficiente es (suma de eta bits) - (suma de otros eta bits).
    """
    bits = bytes_to_bits(data).reshape(N, 2, eta).astype(np.int64)
    x, y = bits[:, 0, :].sum(axis=1), bits[:, 1, :].sum(axis=1)
    return (x - y) % Q
