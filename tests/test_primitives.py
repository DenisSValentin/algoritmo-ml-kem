import numpy as np
import pytest

from mlkem.encoding import byte_decode, byte_encode, compress, decompress
from mlkem.params import N, Q
from mlkem.ring import GAMMAS, ZETAS, inverse_ntt, multiply_ntts, ntt

rng = np.random.default_rng(0)


def random_poly(*shape):
    return rng.integers(0, Q, size=shape + (N,), dtype=np.int64)


def schoolbook_multiply(f, g):
    """Multiplicación directa en Z_q[X]/(X^256 + 1): X^256 = -1, así que lo que "se sale" vuelve con signo cambiado."""
    full = np.convolve(f, g)  # grado hasta 510
    low, high = full[:N], np.append(full[N:], 0)
    return (low - high) % Q


def test_zeta_tables_match_appendix_a():
    assert ZETAS[:8].tolist() == [1, 1729, 2580, 3289, 2642, 630, 1897, 848]
    assert ZETAS[-3:].tolist() == [2935, 885, 2154]
    assert GAMMAS[:6].tolist() == [17, 3312, 2761, 568, 583, 2746]
    assert GAMMAS[-2:].tolist() == [2154, 1175]


def test_ntt_roundtrip():
    f = random_poly(3)
    assert np.array_equal(inverse_ntt(ntt(f)), f)


def test_ntt_multiplication_matches_schoolbook():
    f, g = random_poly(), random_poly()
    assert np.array_equal(inverse_ntt(multiply_ntts(ntt(f), ntt(g))), schoolbook_multiply(f, g))


def test_rounding_ties_go_up():
    # q/2 = 1664,5 -> 1665 (el round() de Python da 1664)
    assert decompress(1, 1) == 1665
    assert decompress(512, 10) == 1665
    assert decompress(8, 4) == 1665


@pytest.mark.parametrize("d", [1, 4, 5, 10, 11])
def test_compress_matches_exact_rational_definition(d):
    from fractions import Fraction

    def exact_round(x):  # ⌈x⌋ con empates hacia arriba, en racionales
        return int(np.floor(x + Fraction(1, 2)))

    x = np.arange(Q)
    expected = [exact_round(Fraction(2**d * int(v), Q)) % 2**d for v in x]
    assert compress(x, d).tolist() == expected
    y = np.arange(2**d)
    assert decompress(y, d).tolist() == [exact_round(Fraction(Q * int(v), 2**d)) for v in y]


@pytest.mark.parametrize("d", [1, 4, 5, 10, 11, 12])
def test_byte_encode_roundtrip(d):
    m = Q if d == 12 else 2**d
    f = rng.integers(0, m, size=(2, N))
    data = byte_encode(f, d)
    assert len(data) == 2 * 32 * d
    assert np.array_equal(byte_decode(data, d), f)
