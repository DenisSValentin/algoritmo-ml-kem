# ML-KEM: Module-Lattice-Based Key-Encapsulation Mechanism

<p align="center">
  <img src="https://img.shields.io/badge/Standard-FIPS%20203-003B36?style=for-the-badge" alt="FIPS 203">
  <img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/NIST-Post--Quantum-FF6F00?style=for-the-badge" alt="NIST PQC">
  <img src="https://img.shields.io/badge/NIST%20ACVP-passing-2E7D32?style=for-the-badge" alt="NIST ACVP vectors">
  <img src="https://img.shields.io/badge/License-GPL--3.0-yellowgreen?style=for-the-badge" alt="License">
</p>

<p align="center">
  <em>Secure key encapsulation based on module lattices — resistant to quantum attacks</em>
</p>

---

## Overview

This repository contains a complete Python implementation of **ML-KEM** (Module-Lattice-Based Key-Encapsulation Mechanism), the post-quantum cryptographic standard published by NIST as **FIPS 203** in August 2024.

ML-KEM is designed to secure communications against future quantum computers. Unlike classical algorithms such as RSA or ECDH, which can be broken by Shor's algorithm, ML-KEM's security is based on the hardness of the **Module Learning with Errors (MLWE)** problem — believed to be computationally infeasible even for quantum adversaries.

---

## Background

### The Quantum Threat

Quantum computers pose an existential threat to current cryptographic infrastructure. Specifically:

- **Shor's Algorithm**: Breaks RSA, DSA, and ECDH by efficiently factoring large integers and computing discrete logarithms.
- **Grover's Algorithm**: Accelerates brute-force searches, effectively halving the security strength of symmetric ciphers like AES.

### The Solution: Post-Quantum Cryptography

In 2017, NIST initiated a global competition to standardize quantum-resistant algorithms. After 6 years of evaluation, ML-KEM (formerly CRYSTALS-Kyber) was selected as the primary standard for key encapsulation.

ML-KEM offers:
- ✅ Security against classical and quantum attacks
- ✅ Efficient key sizes and fast operations
- ✅ Standardized by NIST (FIPS 203)
- ✅ Adopted by major browsers and protocols (Chrome, Firefox, OpenSSL)

---

## About ML-KEM

### What is a KEM?

A Key-Encapsulation Mechanism (KEM) enables two parties to establish a shared secret key over an insecure channel. Unlike traditional public-key encryption, KEMs are optimized for key exchange scenarios common in TLS handshakes.

### Security Foundation

ML-KEM's security relies on the **Module Learning with Errors (MLWE)** problem:

> Given a matrix **A** (public) and a vector **b = As + e** (with small error **e**), recover the secret vector **s**.

This problem is fundamentally different from number-theoretic problems (factoring, discrete logs) that quantum computers can solve efficiently.

### Parameter Sets

| Parameter Set | Security Level | Equivalency | Public Key | Ciphertext |
|---------------|----------------|-------------|------------|------------|
| ML-KEM-512    | Security Level 1 | AES-128    | 800 bytes  | 768 bytes  |
| ML-KEM-768    | Security Level 3 | AES-192    | 1184 bytes | 1088 bytes |
| ML-KEM-1024   | Security Level 5 | AES-256    | 1568 bytes | 1568 bytes |

---

## Implementation Details

This implementation follows the final **FIPS 203** specification and includes:

- **ML-KEM-512, ML-KEM-768 and ML-KEM-1024** as immutable parameter sets
- **Verified against the official NIST ACVP test vectors** (key generation, encapsulation, decapsulation, implicit rejection and input checks)
- **Vectorised NumPy** for polynomial arithmetic and the NTT (~0.2–0.5 ms per operation)
- **SHA3 / SHAKE** from `hashlib`, randomness from `secrets` (the OS CSPRNG)
- **Interactive visualizer** that runs the real implementation and shows every intermediate value

| Parameter set | KeyGen | Encaps | Decaps |
|---|---|---|---|
| ML-KEM-512 | 0.15 ms | 0.21 ms | 0.28 ms |
| ML-KEM-768 | 0.21 ms | 0.29 ms | 0.36 ms |
| ML-KEM-1024 | 0.29 ms | 0.37 ms | 0.45 ms |

<sub>Median on an Apple M5 Pro (`python -m benchmarks.bench`).</sub>

> **Educational code.** Python cannot guarantee constant-time execution or wipe secrets from memory. Use an audited library (Go `crypto/mlkem`, BoringSSL, OpenSSL 3.5+, liboqs) to protect real data.

---

## Project Structure

```
algoritmo-ml-kem/
├── mlkem/              # The ML-KEM implementation (one module per FIPS 203 section)
│   ├── params.py       #   Parameter sets
│   ├── ring.py         #   Z_q, R_q and the NTT
│   ├── encoding.py     #   ByteEncode/Decode, Compress/Decompress
│   ├── sampling.py     #   SampleNTT, SamplePolyCBD
│   ├── hashes.py       #   G, H, J, PRF, XOF
│   ├── kpke.py         #   K-PKE (KeyGen, Encrypt, Decrypt)
│   └── kem.py          #   ML-KEM (KeyGen, Encaps, Decaps + input checks)
├── visualizer/         # Step-by-step web visualizer (standard library server)
├── tests/              # Unit tests + NIST ACVP vectors
├── benchmarks/         # Timing script
├── docs/
│   ├── concepts.md     # The maths, explained step by step (Spanish)
│   └── review.md       # Review of the original 2024 code (Spanish)
├── legacy/             # Original TFG code, kept for reference
└── Memoria_TFG_Denis_Stoyanov.pdf
```

---

## Getting Started

### Prerequisites

- Python 3.9+
- NumPy (installed automatically)

### Installation

```bash
git clone git@github.com:DenisSValentin/algoritmo-ml-kem.git
cd algoritmo-ml-kem
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Usage

```python
from mlkem import MLKEM, ML_KEM_768

kem = MLKEM(ML_KEM_768)
ek, dk = kem.keygen()          # Alice publishes ek, keeps dk
K, c = kem.encaps(ek)          # Bob gets K and sends c
assert kem.decaps(dk, c) == K  # Alice recovers the same K
```

### Visualizer

```bash
python -m visualizer
```

Opens a step-by-step walkthrough in the browser (Spanish): lattices, the ring R_q, key generation, encapsulation, compression, decapsulation on the Z_q "clock", implicit rejection when the ciphertext is tampered with, and a comparison of the three parameter sets. Keyboard: `←` `→` steps, `1` `2` `3` parameter set, `N` new run, `M` tamper with the ciphertext.

### Tests and benchmark

```bash
pytest
python -m benchmarks.bench
```

---

## Academic Context

This implementation was developed as a **Final Degree Project (TFG)** at the [University of Granada](https://www.ugr.es), under the degree in Computer Engineering.

**Author:** Denis Stoyanov Valentin D'Antonio  
**Supervisor:** Jesús García Miranda  
**Date:** September 2024 (revised in 2026)

---

## References

- [NIST FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism Standard](https://csrc.nist.gov/pubs/fips/203/final)
- [NIST Post-Quantum Cryptography Standardization](https://csrc.nist.gov/projects/post-quantum-cryptography)
- [CRYSTALS-Kyber Specification](https://pq-crystals.org/kyber/)

---

## License

This project is licensed under the **GNU General Public License v3.0** — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <sub>Built with 🔐 for a quantum-safe future</sub>
</p>
