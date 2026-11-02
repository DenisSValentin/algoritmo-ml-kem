"""Mide KeyGen, Encaps y Decaps para los tres conjuntos de parámetros.

python -m benchmarks.bench            # 200 repeticiones
python -m benchmarks.bench -n 1000
"""

from __future__ import annotations

import argparse
import statistics
import time
from functools import partial

from mlkem import MLKEM, PARAMETER_SETS


def measure(fn, repetitions: int) -> float:
    """Mediana en milisegundos (la media se distorsiona con cualquier pausa del sistema)."""
    times = []
    for _ in range(repetitions):
        start = time.perf_counter()
        fn()
        times.append(time.perf_counter() - start)
    return statistics.median(times) * 1000


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--repetitions", type=int, default=200)
    args = parser.parse_args()

    print(f"{'Conjunto':<12} {'KeyGen':>9} {'Encaps':>9} {'Decaps':>9}   (mediana en ms, n={args.repetitions})")
    for params in PARAMETER_SETS.values():
        kem = MLKEM(params)
        ek, dk = kem.keygen()
        _, c = kem.encaps(ek)
        operations = (kem.keygen, partial(kem.encaps, ek), partial(kem.decaps, dk, c))
        row = [measure(f, args.repetitions) for f in operations]
        print(f"{params.name:<12} " + " ".join(f"{t:>9.2f}" for t in row))


if __name__ == "__main__":
    main()
