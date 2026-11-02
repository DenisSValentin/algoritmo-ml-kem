import pytest

from mlkem import MLKEM, PARAMETER_SETS, InvalidInputError

ALL = list(PARAMETER_SETS.values())


@pytest.mark.parametrize("params", ALL, ids=lambda p: p.name)
def test_roundtrip_and_sizes(params):
    kem = MLKEM(params)
    ek, dk = kem.keygen()
    K, c = kem.encaps(ek)
    assert (len(ek), len(dk), len(c), len(K)) == (params.ek_size, params.dk_size, params.ciphertext_size, 32)
    assert kem.decaps(dk, c) == K


@pytest.mark.parametrize("params", ALL, ids=lambda p: p.name)
def test_tampered_ciphertext_gives_implicit_rejection(params):
    kem = MLKEM(params)
    ek, dk = kem.keygen()
    K, c = kem.encaps(ek)
    tampered = bytes([c[0] ^ 1]) + c[1:]
    trace = {}
    K_prime = kem.decaps_internal(dk, tampered, trace)
    assert not trace["accepted"]
    assert K_prime != K
    assert K_prime == trace["K_bar"]


def test_parameter_sets_are_independent():
    small, big = MLKEM(PARAMETER_SETS["ML-KEM-512"]), MLKEM(PARAMETER_SETS["ML-KEM-1024"])
    ek_small, _ = small.keygen()
    ek_big, dk_big = big.keygen()
    K, c = big.encaps(ek_big)
    assert big.decaps(dk_big, c) == K
    with pytest.raises(InvalidInputError):
        big.encaps(ek_small)


def test_input_checks():
    kem = MLKEM()
    ek, dk = kem.keygen()
    _, c = kem.encaps(ek)
    with pytest.raises(InvalidInputError):
        kem.encaps(ek[:-1])
    with pytest.raises(InvalidInputError):
        kem.encaps(b"\xff" * len(ek))  # coeficientes de 12 bits = 4095 >= q
    with pytest.raises(InvalidInputError):
        kem.decaps(dk, c + b"\x00")
    with pytest.raises(InvalidInputError):
        corrupted = bytearray(dk)
        corrupted[-40] ^= 1  # dentro de H(ek)
        kem.decaps(bytes(corrupted), c)
