# ML-KEM: Module-Lattice-Based Key-Encapsulation Mechanism

<p align="center">
  <img src="https://img.shields.io/badge/Standard-FIPS%20203-003B36?style=for-the-badge" alt="FIPS 203">
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/NIST-Post--Quantum-FF6F00?style=for-the-badge" alt="NIST PQC">
  <img src="https://img.shields.io/badge/License-MIT-yellowgreen?style=for-the-badge" alt="License">
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

This implementation follows the **FIPS 203** specification and includes:

- **Complete ML-KEM-512, ML-KEM-768, and ML-KEM-1024** parameter sets
- **Pure Python implementation** using NumPy for vector/matrix operations
- **SHA3 / SHAKE** hash functions via hashlib
- **NTT (Number Theoretic Transform)** for efficient polynomial multiplication
- **Interactive CLI** for testing all operations

### Key Algorithms Implemented

| Algorithm | Description |
|-----------|-------------|
| `ML_KEM_KeyGen()` | Generates key pair (public key, secret key) |
| `ML_KEM_Encaps(ek)` | Encapsulates a shared secret using public key |
| `ML_KEM_Decaps(dk, c)` | Decapsulates the shared secret using secret key |

---

## Project Structure

```
Algoritmo_ML-KEM/
├── ml_kem.py           # Core ML-KEM implementation
├── ml_kem_main.py      # Interactive CLI interface
├── README.md           # This file
└── LICENSE             # MIT License
```

---

## Getting Started

### Prerequisites

- Python 3.8+
- NumPy

### Installation

```bash
git clone git@github.com:DenisSValentin/Algoritmo_ML-KEM.git
cd Algoritmo_ML-KEM
pip install numpy
```

### Usage

Run the interactive interface:

```bash
python ml_kem_main.py
```

The CLI provides options to:
1. Generate keypairs
2. Encapsulate secrets
3. Decapsulate ciphertexts
4. Verify correctness

---

## Academic Context

This implementation was developed as a **Final Degree Project (TFG)** at the [University of Granada](https://www.ugr.es), under the degree in Computer Engineering.

**Author:** Denis Stoyanov Valentin D'Antonio  
**Supervisor:** [To be added]  
**Date:** July 2025

---

## References

- [NIST FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism Standard](https://csrc.nist.gov/pubs/fips/203/final)
- [NIST Post-Quantum Cryptography Standardization](https://csrc.nist.gov/projects/post-quantum-cryptography)
- [CRYSTALS-Kyber Specification](https://pq-crystals.org/kyber/)

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <sub>Built with 🔐 for a quantum-safe future</sub>
</p>
