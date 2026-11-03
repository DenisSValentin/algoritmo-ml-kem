"""Ejecuta un intercambio ML-KEM completo y devuelve todos los valores intermedios en JSON.

No reimplementa nada: llama a las funciones reales de `mlkem` pasándoles un diccionario
`trace` para que guarden lo que calculan.
"""

from __future__ import annotations

import hashlib
import secrets
import time
from functools import partial

import numpy as np

from mlkem import MLKEM, PARAMETER_SETS
from mlkem.encoding import bytes_to_bits, compress, decompress
from mlkem.params import Q
from mlkem.ring import centered


def _seeds(seed: str | None) -> tuple[bytes, bytes, bytes]:
    """d, z y m: aleatorios, o derivados de un texto para poder repetir una ejecución."""
    if seed is None:
        return secrets.token_bytes(32), secrets.token_bytes(32), secrets.token_bytes(32)
    stream = hashlib.shake_256(seed.encode()).digest(96)
    return stream[:32], stream[32:64], stream[64:]


def _list(a: np.ndarray) -> list:
    return np.asarray(a).tolist()


def run_exchange(params_name: str, tamper: bool = False, seed: str | None = None) -> dict:
    params = PARAMETER_SETS[params_name]
    kem = MLKEM(params)
    d, z, m = _seeds(seed)
    timings = {}

    keygen_trace: dict = {}
    start = time.perf_counter()
    ek, dk = kem.keygen_internal(d, z, keygen_trace)
    timings["keygen"] = time.perf_counter() - start

    encaps_trace: dict = {}
    start = time.perf_counter()
    K, c = kem.encaps_internal(ek, m, encaps_trace)
    timings["encaps"] = time.perf_counter() - start

    # Manipulación: se invierte un bit de la parte v del texto cifrado (la que lleva el mensaje)
    tampered_byte = None
    c_received = c
    if tamper:
        tampered_byte = len(c) - 1 - secrets.randbelow(32 * params.dv)
        flipped = bytearray(c)
        flipped[tampered_byte] ^= 1 << secrets.randbelow(8)
        c_received = bytes(flipped)

    decaps_trace: dict = {}
    start = time.perf_counter()
    K_prime = kem.decaps_internal(dk, c_received, decaps_trace)
    timings["decaps"] = time.perf_counter() - start

    u, v, mu = encaps_trace["u"], encaps_trace["v"], encaps_trace["mu"]
    w = decaps_trace["w"]
    message_bits = bytes_to_bits(m)
    recovered_bits = bytes_to_bits(decaps_trace["m_prime"])
    noise = centered(w - mu)
    # Error que introduce la compresión: lo que se pierde al guardar u y v con menos bits
    u_compression_error = centered(decompress(compress(u, params.du), params.du) - u)
    v_compression_error = centered(decompress(compress(v, params.dv), params.dv) - v)
    # La "máscara" que tapa el mensaje en v y que solo quien tiene s puede quitar
    mask = (decaps_trace["v_prime"] - w) % Q

    return {
        "params": {
            "name": params.name,
            "k": params.k,
            "eta1": params.eta1,
            "eta2": params.eta2,
            "du": params.du,
            "dv": params.dv,
            "q": Q,
            "n": 256,
            "ek_size": params.ek_size,
            "dk_size": params.dk_size,
            "ciphertext_size": params.ciphertext_size,
            "lattice_dimension": params.lattice_dimension,
        },
        "timings_ms": {key: value * 1000 for key, value in timings.items()},
        "keygen": {
            "d": d.hex(),
            "z": z.hex(),
            "rho": keygen_trace["rho"].hex(),
            "sigma": keygen_trace["sigma"].hex(),
            "a_hat": _list(keygen_trace["a_hat"]),
            "s": _list(centered(keygen_trace["s"])),
            "e": _list(centered(keygen_trace["e"])),
            "t": _list(keygen_trace["t"]),
            "ek": ek.hex(),
            "dk": dk.hex(),
        },
        "encaps": {
            "m": m.hex(),
            "message_bits": _list(message_bits),
            "r": encaps_trace["r"].hex(),
            "K": K.hex(),
            "y": _list(centered(encaps_trace["y"])),
            "e1": _list(centered(encaps_trace["e1"])),
            "e2": _list(centered(encaps_trace["e2"])),
            "u": _list(u),
            "v": _list(v),
            "mu": _list(mu),
            "u_compressed": _list(encaps_trace["u_compressed"]),
            "v_compressed": _list(encaps_trace["v_compressed"]),
            "u_compression_error": _list(u_compression_error),
            "v_compression_error": _list(v_compression_error),
            "c": c.hex(),
        },
        "decaps": {
            "tampered": tamper,
            "tampered_byte": tampered_byte,
            "c_received": c_received.hex(),
            "v_prime": _list(decaps_trace["v_prime"]),
            "mask": _list(mask),
            "w": _list(w),
            "noise": _list(noise),
            "max_noise": int(np.abs(noise).max()),
            "threshold": Q // 4,
            "recovered_bits": _list(recovered_bits),
            "bit_errors": int((recovered_bits != message_bits).sum()),
            "c_prime": decaps_trace["c_prime"].hex(),
            "accepted": decaps_trace["accepted"],
            "K_prime_candidate": decaps_trace["K_prime"].hex(),
            "K_bar": decaps_trace["K_bar"].hex(),
            "K_final": K_prime.hex(),
            "keys_match": K_prime == K,
        },
    }


def benchmark(repetitions: int = 30, batch: int = 1) -> list[dict]:
    """Mediana en ms de `repetitions` medidas de `batch` llamadas seguidas cada una.

    En el navegador el reloj solo tiene una precisión de 0,1–1 ms, así que allí se mide en tandas.
    """
    rows = []
    for params in PARAMETER_SETS.values():
        kem = MLKEM(params)
        ek, dk = kem.keygen()
        _, c = kem.encaps(ek)
        row = {"name": params.name}
        operations = (
            ("keygen", kem.keygen),
            ("encaps", partial(kem.encaps, ek)),
            ("decaps", partial(kem.decaps, dk, c)),
        )
        for label, fn in operations:
            times = []
            for _ in range(repetitions):
                start = time.perf_counter()
                for _ in range(batch):
                    fn()
                times.append((time.perf_counter() - start) / batch)
            row[label] = float(np.median(times) * 1000)
        rows.append(row)
    return rows
