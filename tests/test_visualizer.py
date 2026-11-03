import json
import re
from pathlib import Path

import pytest

from mlkem import MLKEM, PARAMETER_SETS
from visualizer.trace import _seeds, run_exchange

ROOT = Path(__file__).parent.parent


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


def test_browser_downloads_every_module():
    """El worker de Pyodide descarga una lista fija de ficheros: que no se quede atrás."""
    worker = (ROOT / "visualizer" / "static" / "pyodide-worker.js").read_text()
    listed = set(re.findall(r'"((?:mlkem|visualizer)/\w+\.py)"', worker))
    expected = {f"mlkem/{path.name}" for path in (ROOT / "mlkem").glob("*.py")}
    assert listed == expected | {"visualizer/__init__.py", "visualizer/trace.py"}
