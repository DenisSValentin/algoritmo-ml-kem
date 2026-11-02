import json

import pytest

from mlkem import MLKEM, PARAMETER_SETS
from visualizer.trace import _seeds, run_exchange


@pytest.mark.parametrize("name", list(PARAMETER_SETS))
def test_trace_matches_real_api(name):
    data = run_exchange(name, seed="tfg")
    d, z, m = _seeds("tfg")
    kem = MLKEM(PARAMETER_SETS[name])
    ek, _dk = kem.keygen_internal(d, z)
    K, c = kem.encaps_internal(ek, m)
    assert data["keygen"]["ek"] == ek.hex()
    assert data["encaps"]["c"] == c.hex()
    assert data["encaps"]["K"] == K.hex() == data["decaps"]["K_final"]
    assert data["decaps"]["bit_errors"] == 0
    assert data["decaps"]["max_noise"] < data["decaps"]["threshold"]
    assert len(data["keygen"]["a_hat"]) == data["params"]["k"]
    json.dumps(data)  # todo debe ser serializable


def test_tampered_exchange_is_rejected():
    data = run_exchange("ML-KEM-512", tamper=True)
    assert data["decaps"]["tampered"]
    assert not data["decaps"]["accepted"]
    assert not data["decaps"]["keys_match"]
    assert data["decaps"]["K_final"] == data["decaps"]["K_bar"]
