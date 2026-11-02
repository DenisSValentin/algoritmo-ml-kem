"""Funciones hash y XOF de ML-KEM (FIPS 203, sección 4.1), todas de la familia SHA-3."""

from __future__ import annotations

import hashlib


def prf(eta: int, s: bytes, b: int) -> bytes:
    """PRF_eta(s, b) = SHAKE256(s || b), 64·eta bytes."""
    return hashlib.shake_256(s + bytes([b])).digest(64 * eta)


def h(s: bytes) -> bytes:
    """H(s) = SHA3-256(s)."""
    return hashlib.sha3_256(s).digest()


def j(s: bytes) -> bytes:
    """J(s) = SHAKE256(s), 32 bytes."""
    return hashlib.shake_256(s).digest(32)


def g(c: bytes) -> tuple[bytes, bytes]:
    """G(c) = SHA3-512(c), partido en dos mitades de 32 bytes."""
    out = hashlib.sha3_512(c).digest()
    return out[:32], out[32:]


def xof(seed: bytes, length: int) -> bytes:
    """Primeros `length` bytes de SHAKE128(seed).

    hashlib no permite ir "exprimiendo" (squeeze) el XOF poco a poco, pero como la salida
    de SHAKE es un flujo, digest(n) siempre es prefijo de digest(m) para m > n. Por eso
    pedir más bytes equivale a seguir exprimiendo. (En el TFG, llamar a digest(3) en cada
    iteración devolvía siempre los mismos 3 bytes: este es el motivo.)
    """
    return hashlib.shake_128(seed).digest(length)
