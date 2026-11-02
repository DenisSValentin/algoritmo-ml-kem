# ML-KEM: Module-Lattice-Based Key-Encapsulation Mechanism

<p align="center">
  <img src="https://img.shields.io/badge/Standard-FIPS%20203-003B36?style=for-the-badge" alt="FIPS 203">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/NIST-Post--Quantum-FF6F00?style=for-the-badge" alt="NIST PQC">
  <img src="https://img.shields.io/badge/NIST%20ACVP-passing-2E7D32?style=for-the-badge" alt="NIST ACVP vectors">
  <img src="https://img.shields.io/badge/License-MIT-yellowgreen?style=for-the-badge" alt="License">
</p>

<p align="center">
  <em>An educational Python implementation of the post-quantum key-exchange standard, with an interactive visualizer</em>
</p>

---

## What is this?

This repository started as my **Final Degree Project (TFG)** at the University of Granada, presented in September 2024: a from-scratch Python implementation of **ML-KEM**, the post-quantum key-encapsulation mechanism that NIST published as **FIPS 203** in August 2024.

It contains:

- **`mlkem/`** — the implementation, one module per section of the standard, verified against the official NIST test vectors.
- **`visualizer/`** — a step-by-step web app that runs the real implementation and shows what happens inside: the lattice problem, the polynomials, the noise, and how the receiver removes the "mask" to recover the message.
- **`docs/`** — the maths explained step by step, and an errata for the original thesis code.
- **`Memoria_TFG_Denis_Stoyanov.pdf`** — the thesis (Spanish), as it was submitted.
- **`legacy/`** — the original 2024 code, kept for reference.

> **Educational code.** Python cannot guarantee constant-time execution or wipe secrets from memory. To protect real data, use an audited library (Go `crypto/mlkem`, BoringSSL, OpenSSL 3.5+, liboqs).

---

## Background

### Why post-quantum cryptography?

Today's key exchanges (RSA, ECDH) rely on factoring and discrete logarithms. A large enough quantum computer running **Shor's algorithm** would break both. Since encrypted traffic can be recorded today and decrypted years later ("harvest now, decrypt later"), the migration has to happen before such a computer exists.

In 2017 NIST launched a competition to standardise quantum-resistant algorithms. **CRYSTALS-Kyber** was selected and standardised in 2024 as **ML-KEM**. Chrome, Firefox and Cloudflare already use it in TLS, combined with X25519 (`X25519MLKEM768`).

### What is a KEM?

A **Key-Encapsulation Mechanism** lets two parties agree on a shared 32-byte secret over a public channel. It has three algorithms:

| Algorithm | Who | Input | Output |
|---|---|---|---|
| `KeyGen` | Alice | — | public key `ek`, private key `dk` |
| `Encaps` | Bob | `ek` | shared key `K`, ciphertext `c` |
| `Decaps` | Alice | `dk`, `c` | shared key `K` |

Only `ek` and `c` travel over the channel.

### Why it is secure

ML-KEM's security relies on the **Module Learning with Errors (MLWE)** problem:

> Given a public matrix **A** and **t = A·s + e**, where **e** is a small random error, recover the secret **s**.

Without the error this is a linear system that Gaussian elimination solves instantly. With it, it becomes a closest-vector problem in a lattice of hundreds of dimensions, for which no efficient classical or quantum algorithm is known.

### Parameter sets

The parameter **k** is the number of polynomials per vector (and the size of the k×k matrix A). Each polynomial has 256 coefficients modulo 3329, so the underlying lattice has k·256 dimensions.

| Parameter set | k | Lattice dimension | Security (NIST category) | Public key | Ciphertext |
|---|---|---|---|---|---|
| ML-KEM-512 | 2 | 512 | 1 (≈ AES-128) | 800 bytes | 768 bytes |
| ML-KEM-768 | 3 | 768 | 3 (≈ AES-192) | 1184 bytes | 1088 bytes |
| ML-KEM-1024 | 4 | 1024 | 5 (≈ AES-256) | 1568 bytes | 1568 bytes |

A full explanation of the maths (modular arithmetic, the ring R_q, lattices, LWE, the NTT, compression and the Fujisaki-Okamoto transform), with a worked example you can do by hand, is in **[docs/concepts.md](docs/concepts.md)** (Spanish).

---

## Getting Started

### Installation

The project is managed with [uv](https://docs.astral.sh/uv/), which also installs the right Python version (3.15, set in `.python-version`). Python 3.11 or newer is supported.

```bash
git clone git@github.com:DenisSValentin/algoritmo-ml-kem.git
cd algoritmo-ml-kem
uv sync
```

`uv sync` creates `.venv/` with the exact versions from `uv.lock`. Prefix any command with `uv run` to use that environment, e.g. `uv run python`.

<details>
<summary>Without uv</summary>

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e . --group dev   # pip 25.1 or newer
```

</details>

### Using the library

```python
from mlkem import MLKEM, ML_KEM_768

kem = MLKEM(ML_KEM_768)
ek, dk = kem.keygen()          # Alice publishes ek, keeps dk
K, c = kem.encaps(ek)          # Bob gets K and sends c to Alice
assert kem.decaps(dk, c) == K  # Alice recovers the same K
```

`ML_KEM_512` and `ML_KEM_1024` work the same way. Invalid keys or ciphertexts raise `InvalidInputError`. A tampered ciphertext does not raise an error: following the standard, `decaps` returns an unrelated pseudorandom key ("implicit rejection").

The deterministic algorithms from the standard (`keygen_internal`, `encaps_internal`, `decaps_internal`) are also available, which is how the NIST test vectors are checked.

### Visualizer

```bash
uv run python -m visualizer
```

It opens `http://127.0.0.1:8000` in the browser with a nine-step walkthrough (in Spanish):

1. **The idea** — what a KEM does, with the result of a real run.
2. **Lattices** — a 2D lattice where you try to find the closest point, and see what happens when the noise grows.
3. **The ring R_q** — the Z_q "clock", multiplication with X²⁵⁶ = −1, small vs. uniform polynomials.
4. **KeyGen** — the k×k matrix A, the secret s and the error e as heatmaps, and t = A·s + e.
5. **Encaps** — how the 256-bit message is hidden inside v.
6. **Compression** — how many bytes it saves and how much noise it adds.
7. **Decaps** — the 256 coefficients on the Z_q clock, before and after removing the mask.
8. **Verification** — re-encryption, and implicit rejection when the ciphertext is tampered with.
9. **Comparison** — the three parameter sets, with timings measured on your machine.

Keyboard: `←` `→` change step, `1` `2` `3` change parameter set, `N` new run, `M` flip a bit of the ciphertext in transit.

### Tests and benchmark

```bash
uv run pytest
uv run python -m benchmarks.bench
```

The tests include a subset of the official **NIST ACVP vectors** (key generation, encapsulation, decapsulation with modified ciphertexts, and key checks), plus unit tests that compare the NTT with schoolbook multiplication and the rounding with its exact rational definition. CI runs them on the oldest supported combination (Python 3.11 with NumPy 1.26) and the newest (Python 3.15 with NumPy 2).

| Parameter set | KeyGen | Encaps | Decaps |
|---|---|---|---|
| ML-KEM-512 | 0.13 ms | 0.19 ms | 0.25 ms |
| ML-KEM-768 | 0.19 ms | 0.25 ms | 0.33 ms |
| ML-KEM-1024 | 0.27 ms | 0.33 ms | 0.41 ms |

<sub>Median on an Apple M5 Pro, Python 3.15, NumPy 2.5.</sub>

---

## Project Structure

```
algoritmo-ml-kem/
├── mlkem/              # The ML-KEM implementation
│   ├── params.py       #   Parameter sets (k, η, d_u, d_v)
│   ├── ring.py         #   Z_q, R_q and the NTT              (FIPS 203 §4.3)
│   ├── encoding.py     #   ByteEncode/Decode, Compress       (§4.2.1)
│   ├── sampling.py     #   SampleNTT, SamplePolyCBD          (§4.2.2)
│   ├── hashes.py       #   G, H, J, PRF, XOF                 (§4.1)
│   ├── kpke.py         #   K-PKE: KeyGen, Encrypt, Decrypt   (§5)
│   └── kem.py          #   ML-KEM: KeyGen, Encaps, Decaps    (§6, §7)
├── visualizer/         # Web visualizer (standard-library HTTP server + plain JS)
├── tests/              # Unit tests and NIST ACVP vectors
├── benchmarks/         # Timing script
├── docs/
│   ├── concepts.md     # The maths, step by step (Spanish)
│   └── review.md       # Errata for the 2024 thesis code (Spanish)
├── legacy/             # Original 2024 code
└── Memoria_TFG_Denis_Stoyanov.pdf
```

---

## Academic Context

Final Degree Project (TFG), Degree in Computer Engineering, [University of Granada](https://www.ugr.es).

**Title:** Criptografía basada en retículos: el cifrado del futuro  
**Author:** Denis Valentin Stoyanov D'Antonio  
**Supervisor:** Jesús García Miranda  
**Date:** September 2024

The thesis and the code in `legacy/` are kept exactly as they were submitted. Corrections found afterwards are documented in [docs/review.md](docs/review.md), which takes precedence where the two differ.

---

## Changes since the thesis (September 2024 → November 2026)

The 2024 code worked end to end (both parties always obtained the same key), but it had not been checked against the official test vectors. Doing so revealed that it was not interoperable with other FIPS 203 implementations. Everything below is explained in detail in [docs/review.md](docs/review.md).

**Correctness**
- The matrix Â is now generated with `SampleNTT(ρ‖j‖i)`, as in the final standard. The 2024 code still used the draft's index order (`ρ‖i‖j`), which NIST reverted in the final version (FIPS 203, Appendix C.2). Because of this, no generated key matched the NIST vectors.
- `Compress` and `Decompress` now use exact integer arithmetic, rounding ties up. The 2024 code used floating point and Python's `round()`, which rounds ties to even (1664.5 → 1664 instead of 1665). This changed part of the ciphertexts.
- With both fixes the original code already passes all NIST vectors; the new implementation is tested against them.

**Security**
- Random seeds come from `secrets` (the operating system's CSPRNG) instead of `np.random`, which is predictable.
- `encaps` and `decaps` always run the input checks of FIPS 203 §7 (key length, modulus check, hash check) and raise `InvalidInputError`. Previously only the command-line interface ran them.
- Ciphertexts are compared with `hmac.compare_digest`.

**Compatibility**
- Works with NumPy 2. The 2024 code fails with an `OverflowError` because of NumPy 2's new type-promotion rules.

**Design and performance**
- Split into one module per section of the standard, with immutable parameter sets instead of global state, so different parameter sets can be used at the same time.
- NumPy is now used on whole arrays (vectorised NTT, encoding, sampling and matrix products) instead of element by element: **120–190× faster**.
- Keys and ciphertexts are Python `bytes` instead of `uint8` arrays.

**Tooling**
- Tests with the NIST ACVP vectors, `pyproject.toml`, GitHub Actions CI, `ruff` and a benchmark script.
- Managed with uv, with a lock file (`uv.lock`). Minimum Python raised from 3.9 (end of life since October 2025) to 3.11.

**Interface**
- The keyboard-driven terminal menu, which only reported whether each step succeeded, has been replaced by the web visualizer described above.

**Documentation and licence**
- New [docs/concepts.md](docs/concepts.md) (the maths, step by step) and [docs/review.md](docs/review.md) (errata).
- The code is now released under the MIT License. The previous README said MIT while the `LICENSE` file contained the GPL-3.0.

---

## References

- [NIST FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism Standard](https://csrc.nist.gov/pubs/fips/203/final)
- [NIST ACVP test vectors](https://github.com/usnistgov/ACVP-Server/tree/master/gen-val/json-files)
- [NIST Post-Quantum Cryptography Standardization](https://csrc.nist.gov/projects/post-quantum-cryptography)
- [CRYSTALS-Kyber](https://pq-crystals.org/kyber/)

---

## License

The code is licensed under the **MIT License** — see [LICENSE](LICENSE). The thesis (`Memoria_TFG_Denis_Stoyanov.pdf`) is not covered by this license; all rights reserved by the author.
