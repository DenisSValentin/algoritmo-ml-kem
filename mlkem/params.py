"""Conjuntos de parámetros de ML-KEM (FIPS 203, sección 8, tabla 2).

En vez de variables globales que se cambian en caliente (como en la versión del TFG),
cada conjunto de parámetros es un objeto inmutable que se pasa explícitamente. Así se
pueden usar ML-KEM-512 y ML-KEM-1024 a la vez sin que uno pise al otro.
"""

from __future__ import annotations

from dataclasses import dataclass

# Constantes comunes a los tres conjuntos de parámetros
N = 256  # número de coeficientes de cada polinomio
Q = 3329  # módulo primo: Z_q = {0, ..., 3328}


@dataclass(frozen=True)
class ParameterSet:
    name: str
    k: int  # rango del módulo: tamaño de los vectores y de la matriz A (k x k)
    eta1: int  # anchura de la distribución CBD para s, e e y
    eta2: int  # anchura de la distribución CBD para e1 y e2
    du: int  # bits por coeficiente al comprimir u
    dv: int  # bits por coeficiente al comprimir v

    @property
    def ek_size(self) -> int:
        """Bytes de la clave de encapsulamiento (pública)."""
        return 384 * self.k + 32

    @property
    def dk_size(self) -> int:
        """Bytes de la clave de desencapsulamiento (privada)."""
        return 768 * self.k + 96

    @property
    def ciphertext_size(self) -> int:
        return 32 * (self.du * self.k + self.dv)

    @property
    def lattice_dimension(self) -> int:
        """Dimensión del retículo subyacente: k polinomios de 256 coeficientes."""
        return self.k * N


ML_KEM_512 = ParameterSet("ML-KEM-512", k=2, eta1=3, eta2=2, du=10, dv=4)
ML_KEM_768 = ParameterSet("ML-KEM-768", k=3, eta1=2, eta2=2, du=10, dv=4)
ML_KEM_1024 = ParameterSet("ML-KEM-1024", k=4, eta1=2, eta2=2, du=11, dv=5)

PARAMETER_SETS = {p.name: p for p in (ML_KEM_512, ML_KEM_768, ML_KEM_1024)}
