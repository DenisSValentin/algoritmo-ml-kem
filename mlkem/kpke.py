"""K-PKE: el esquema de cifrado de clave pública que hay debajo de ML-KEM (FIPS 203, sección 5).

K-PKE por sí solo no es seguro frente a ataques de texto cifrado elegido; ML-KEM lo
envuelve con la transformación de Fujisaki-Okamoto (ver kem.py).

Todas las funciones aceptan un diccionario `trace` opcional. Si se pasa, se guardan en
él los valores intermedios (matriz Â, secretos, ruido...) para que el visualizador
muestre exactamente lo que calcula el algoritmo real, sin reimplementarlo aparte.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from .encoding import byte_decode, byte_encode, compress, decompress
from .hashes import g, prf
from .params import N, ParameterSet, Q
from .ring import dot_ntt, inverse_ntt, matrix_vector_ntt, ntt
from .sampling import sample_ntt, sample_poly_cbd

Trace = Optional[dict]


def expand_matrix(rho: bytes, k: int) -> np.ndarray:
    """Genera Â (k x k polinomios en T_q) a partir de la semilla pública ρ.

    Â[i, j] = SampleNTT(ρ || j || i). El borrador (ipd) usaba ρ || i || j por error; la
    versión final lo corrigió (apéndice C.2). Este era el fallo principal del TFG.
    """
    a_hat = np.empty((k, k, N), dtype=np.int64)
    for i in range(k):
        for j in range(k):
            a_hat[i, j] = sample_ntt(rho + bytes([j, i]))
    return a_hat


def sample_vector(seed: bytes, eta: int, k: int, first_n: int) -> np.ndarray:
    """k polinomios CBD_eta con contadores N = first_n, first_n + 1, ..."""
    return np.stack([sample_poly_cbd(prf(eta, seed, first_n + i), eta) for i in range(k)])


def _decode_vector(data: bytes, d: int, k: int) -> np.ndarray:
    return byte_decode(data, d).reshape(k, N)


def keygen(d: bytes, params: ParameterSet, trace: Trace = None) -> tuple[bytes, bytes]:
    """Algoritmo 13: genera (ek_PKE, dk_PKE) a partir de una semilla d de 32 bytes."""
    k = params.k
    # Separación de dominio: añadir k evita reutilizar la misma semilla en otro nivel de seguridad
    rho, sigma = g(d + bytes([k]))
    a_hat = expand_matrix(rho, k)
    s = sample_vector(sigma, params.eta1, k, 0)
    e = sample_vector(sigma, params.eta1, k, k)
    s_hat, e_hat = ntt(s), ntt(e)
    t_hat = (matrix_vector_ntt(a_hat, s_hat) + e_hat) % Q  # t = A·s + e

    ek_pke = byte_encode(t_hat, 12) + rho
    dk_pke = byte_encode(s_hat, 12)

    if trace is not None:
        trace.update(rho=rho, sigma=sigma, a_hat=a_hat, s=s, e=e, t_hat=t_hat, t=inverse_ntt(t_hat))
    return ek_pke, dk_pke


def encrypt(ek_pke: bytes, m: bytes, r: bytes, params: ParameterSet, trace: Trace = None) -> bytes:
    """Algoritmo 14: cifra un mensaje m de 32 bytes con aleatoriedad r."""
    k, du, dv = params.k, params.du, params.dv
    t_hat = _decode_vector(ek_pke[: 384 * k], 12, k)
    rho = ek_pke[384 * k : 384 * k + 32]
    a_hat = expand_matrix(rho, k)

    y = sample_vector(r, params.eta1, k, 0)
    e1 = sample_vector(r, params.eta2, k, k)
    e2 = sample_poly_cbd(prf(params.eta2, r, 2 * k), params.eta2)
    y_hat = ntt(y)

    u = (inverse_ntt(matrix_vector_ntt(a_hat, y_hat, transpose=True)) + e1) % Q  # u = A^T·y + e1
    # Cada bit del mensaje se convierte en 0 o en ⌈q/2⌋ = 1665: lo más lejos posible entre sí
    mu = decompress(byte_decode(m, 1), 1)
    v = (inverse_ntt(dot_ntt(t_hat, y_hat)) + e2 + mu) % Q  # v = t^T·y + e2 + mu

    u_compressed, v_compressed = compress(u, du), compress(v, dv)
    c = byte_encode(u_compressed, du) + byte_encode(v_compressed, dv)

    if trace is not None:
        trace.update(y=y, e1=e1, e2=e2, u=u, v=v, mu=mu, u_compressed=u_compressed, v_compressed=v_compressed)
    return c


def decrypt(dk_pke: bytes, c: bytes, params: ParameterSet, trace: Trace = None) -> bytes:
    """Algoritmo 15: recupera el mensaje m de 32 bytes."""
    k, du, dv = params.k, params.du, params.dv
    split = 32 * du * k
    u_prime = decompress(_decode_vector(c[:split], du, k), du)
    v_prime = decompress(byte_decode(c[split:], dv), dv)
    s_hat = _decode_vector(dk_pke, 12, k)

    # w = v' - s^T·u' = mu + (ruido pequeño). Cada coeficiente cerca de 0 es un 0, cerca de q/2 un 1
    w = (v_prime - inverse_ntt(dot_ntt(s_hat, ntt(u_prime)))) % Q
    m = byte_encode(compress(w, 1), 1)

    if trace is not None:
        trace.update(u_prime=u_prime, v_prime=v_prime, w=w)
    return m
