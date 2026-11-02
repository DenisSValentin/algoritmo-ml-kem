"""Comprobación contra los vectores oficiales de NIST (ACVP).

Es la única forma de saber que la implementación es *interoperable*: que sus claves y
textos cifrados los entiende cualquier otra implementación de FIPS 203 (OpenSSL,
BoringSSL, Go...). Que K == K' en una ejecución propia no lo demuestra: el TFG lo
cumplía y aun así no coincidía con el estándar.
"""

import json
from pathlib import Path

import pytest

from mlkem import MLKEM, PARAMETER_SETS, InvalidInputError

VECTORS = json.loads((Path(__file__).parent / "vectors" / "acvp_subset.json").read_text())


def _id(t):
    return f"{t['parameterSet']}-{t['tcId']}"


def _kem(t):
    return MLKEM(PARAMETER_SETS[t["parameterSet"]])


def _b(hex_string):
    return bytes.fromhex(hex_string)


@pytest.mark.parametrize("t", VECTORS["keyGen"], ids=_id)
def test_keygen(t):
    ek, dk = _kem(t).keygen_internal(_b(t["d"]), _b(t["z"]))
    assert ek == _b(t["ek"])
    assert dk == _b(t["dk"])


@pytest.mark.parametrize("t", VECTORS["encapsulation"], ids=_id)
def test_encapsulation(t):
    K, c = _kem(t).encaps_internal(_b(t["ek"]), _b(t["m"]))
    assert c == _b(t["c"])
    assert K == _b(t["k"])


@pytest.mark.parametrize("t", VECTORS["decapsulation"], ids=_id)
def test_decapsulation(t):
    # Incluye textos cifrados modificados: ahí la clave esperada es la de rechazo implícito
    assert _kem(t).decaps(_b(t["dk"]), _b(t["c"])) == _b(t["k"])


@pytest.mark.parametrize("t", VECTORS["encapsulationKeyCheck"], ids=_id)
def test_encapsulation_key_check(t):
    kem = _kem(t)
    if t["testPassed"]:
        kem.check_encapsulation_key(_b(t["ek"]))
    else:
        with pytest.raises(InvalidInputError):
            kem.check_encapsulation_key(_b(t["ek"]))


@pytest.mark.parametrize("t", VECTORS["decapsulationKeyCheck"], ids=_id)
def test_decapsulation_key_check(t):
    kem = _kem(t)
    if t["testPassed"]:
        kem.check_decapsulation_key(_b(t["dk"]))
    else:
        with pytest.raises(InvalidInputError):
            kem.check_decapsulation_key(_b(t["dk"]))
