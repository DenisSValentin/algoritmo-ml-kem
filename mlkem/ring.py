"""Aritmética en el anillo R_q = Z_q[X]/(X^256 + 1) y en su dominio NTT T_q.

Un polinomio se representa como un array de NumPy de 256 enteros (int64) en [0, q).
Todas las funciones aceptan dimensiones extra delante, de modo que un vector de k
polinomios (forma (k, 256)) o una matriz k x k (forma (k, k, 256)) se procesan de una
sola vez, sin bucles de Python coeficiente a coeficiente.

Referencias: FIPS 203, sección 4.3 (algoritmos 9, 10, 11 y 12) y apéndice A.
"""

from __future__ import annotations

import numpy as np

from .params import N, Q

ZETA = 17  # raíz primitiva 256-ésima de la unidad módulo q


def bit_rev7(i: int) -> int:
    """Invierte los 7 bits de i (0 <= i < 128)."""
    return int(f"{i:07b}"[::-1], 2)


# En el TFG estas tablas estaban copiadas a mano del apéndice A. Aquí se calculan a
# partir de su definición; los tests comprueban que coinciden con las del estándar.
ZETAS = np.array([pow(ZETA, bit_rev7(i), Q) for i in range(128)], dtype=np.int64)
GAMMAS = np.array([pow(ZETA, 2 * bit_rev7(i) + 1, Q) for i in range(128)], dtype=np.int64)
N_INV = pow(128, -1, Q)  # 3303, el factor de escala de la NTT inversa


def ntt(f: np.ndarray) -> np.ndarray:
    """Algoritmo 9: representación NTT de f (forma (..., 256))."""
    f = np.array(f, dtype=np.int64, copy=True)
    shape = f.shape
    length = 128
    while length >= 2:
        blocks = N // (2 * length)
        # Cada bloque de 2*length coeficientes usa un único zeta: ZETAS[blocks : 2*blocks]
        zetas = ZETAS[blocks : 2 * blocks].reshape(blocks, 1)
        g = f.reshape(shape[:-1] + (blocks, 2, length))
        lo, hi = g[..., 0, :], g[..., 1, :]
        t = (zetas * hi) % Q
        g[..., 0, :], g[..., 1, :] = (lo + t) % Q, (lo - t) % Q
        f = g.reshape(shape)
        length //= 2
    return f


def inverse_ntt(f_hat: np.ndarray) -> np.ndarray:
    """Algoritmo 10: vuelve del dominio NTT a R_q."""
    f = np.array(f_hat, dtype=np.int64, copy=True)
    shape = f.shape
    length = 2
    while length <= 128:
        blocks = N // (2 * length)
        # El algoritmo recorre los zetas al revés: de ZETAS[2*blocks - 1] a ZETAS[blocks]
        zetas = ZETAS[blocks : 2 * blocks][::-1].reshape(blocks, 1)
        g = f.reshape(shape[:-1] + (blocks, 2, length))
        lo, hi = g[..., 0, :].copy(), g[..., 1, :].copy()
        g[..., 0, :] = (lo + hi) % Q
        g[..., 1, :] = (zetas * (hi - lo)) % Q
        f = g.reshape(shape)
        length *= 2
    return (f * N_INV) % Q


def multiply_ntts(f_hat: np.ndarray, g_hat: np.ndarray) -> np.ndarray:
    """Algoritmos 11 y 12: producto en T_q.

    En el dominio NTT el polinomio se parte en 128 polinomios de grado 1, y cada par
    (a0 + a1·X)(b0 + b1·X) se multiplica módulo (X^2 - gamma_i).
    """
    f_hat, g_hat = np.broadcast_arrays(np.asarray(f_hat), np.asarray(g_hat))
    a = f_hat.reshape(f_hat.shape[:-1] + (128, 2))
    b = g_hat.reshape(g_hat.shape[:-1] + (128, 2))
    a0, a1, b0, b1 = a[..., 0], a[..., 1], b[..., 0], b[..., 1]
    h = np.empty(a.shape, dtype=np.int64)
    h[..., 0] = (a0 * b0 + (a1 * b1 % Q) * GAMMAS) % Q
    h[..., 1] = (a0 * b1 + a1 * b0) % Q
    return h.reshape(f_hat.shape)


def matrix_vector_ntt(a_hat: np.ndarray, v_hat: np.ndarray, transpose: bool = False) -> np.ndarray:
    """Calcula Â·v̂ (o Â^T·v̂) con Â de forma (k, k, 256) y v̂ de forma (k, 256)."""
    if transpose:
        a_hat = a_hat.transpose(1, 0, 2)
    return multiply_ntts(a_hat, v_hat[np.newaxis, :, :]).sum(axis=1) % Q


def dot_ntt(u_hat: np.ndarray, v_hat: np.ndarray) -> np.ndarray:
    """Producto escalar û^T·v̂ de dos vectores de k polinomios en T_q."""
    return multiply_ntts(u_hat, v_hat).sum(axis=0) % Q


def centered(f: np.ndarray) -> np.ndarray:
    """Representa los coeficientes en (-q/2, q/2] en vez de [0, q). Útil para ver el ruido."""
    f = np.asarray(f) % Q
    return np.where(f > Q // 2, f - Q, f)
