"""ML-KEM: KeyGen, Encaps y Decaps (FIPS 203, secciones 6 y 7).

Uso básico:

    kem = MLKEM(ML_KEM_768)
    ek, dk = kem.keygen()           # Alice publica ek y guarda dk
    K, c = kem.encaps(ek)           # Bob obtiene la clave K y envía c a Alice
    assert kem.decaps(dk, c) == K   # Alice recupera la misma K
"""

from __future__ import annotations

import hmac
import secrets

from . import kpke
from .encoding import byte_decode, byte_encode
from .hashes import g, h, j
from .params import ML_KEM_768, ParameterSet

Trace = dict | None


class InvalidInputError(ValueError):
    """Una clave o un texto cifrado no supera las comprobaciones de la sección 7."""


class MLKEM:
    def __init__(self, params: ParameterSet = ML_KEM_768):
        self.params = params

    # ------------------------------------------------------------------ API pública

    def keygen(self) -> tuple[bytes, bytes]:
        """Algoritmo 19: devuelve (ek, dk) con semillas de un generador criptográfico."""
        # secrets usa el CSPRNG del sistema operativo. np.random (lo que usaba el TFG) es un
        # Mersenne Twister: predecible a partir de su salida y no apto para criptografía.
        return self.keygen_internal(secrets.token_bytes(32), secrets.token_bytes(32))

    def encaps(self, ek: bytes) -> tuple[bytes, bytes]:
        """Algoritmo 20: devuelve (K, c), la clave compartida y el texto cifrado."""
        self.check_encapsulation_key(ek)
        return self.encaps_internal(ek, secrets.token_bytes(32))

    def decaps(self, dk: bytes, c: bytes) -> bytes:
        """Algoritmo 21: devuelve la clave compartida K'."""
        self.check_ciphertext(c)
        self.check_decapsulation_key(dk)
        return self.decaps_internal(dk, c)

    # ------------------------------------------------------- comprobaciones (sección 7)

    def check_encapsulation_key(self, ek: bytes) -> None:
        p = self.params
        if not isinstance(ek, bytes) or len(ek) != p.ek_size:
            raise InvalidInputError(f"ek debe tener {p.ek_size} bytes para {p.name}")
        # Comprobación de módulo: todos los coeficientes de t̂ deben estar en [0, q)
        t_bytes = ek[: 384 * p.k]
        if byte_encode(byte_decode(t_bytes, 12), 12) != t_bytes:
            raise InvalidInputError("ek contiene coeficientes fuera de [0, q)")

    def check_decapsulation_key(self, dk: bytes) -> None:
        p = self.params
        if not isinstance(dk, bytes) or len(dk) != p.dk_size:
            raise InvalidInputError(f"dk debe tener {p.dk_size} bytes para {p.name}")
        if h(dk[384 * p.k : 768 * p.k + 32]) != dk[768 * p.k + 32 : 768 * p.k + 64]:
            raise InvalidInputError("el hash H(ek) guardado en dk no coincide")

    def check_ciphertext(self, c: bytes) -> None:
        p = self.params
        if not isinstance(c, bytes) or len(c) != p.ciphertext_size:
            raise InvalidInputError(f"c debe tener {p.ciphertext_size} bytes para {p.name}")

    # --------------------------------------------- algoritmos internos (deterministas)

    def keygen_internal(self, d: bytes, z: bytes, trace: Trace = None) -> tuple[bytes, bytes]:
        """Algoritmo 16."""
        ek_pke, dk_pke = kpke.keygen(d, self.params, trace)
        ek = ek_pke
        dk = dk_pke + ek + h(ek) + z
        return ek, dk

    def encaps_internal(self, ek: bytes, m: bytes, trace: Trace = None) -> tuple[bytes, bytes]:
        """Algoritmo 17."""
        K, r = g(m + h(ek))
        c = kpke.encrypt(ek, m, r, self.params, trace)
        if trace is not None:
            trace.update(m=m, r=r, K=K)
        return K, c

    def decaps_internal(self, dk: bytes, c: bytes, trace: Trace = None) -> bytes:
        """Algoritmo 18.

        Descifra, vuelve a cifrar y compara (transformación de Fujisaki-Okamoto). Si el
        texto cifrado ha sido manipulado, no se devuelve un error sino una clave
        pseudoaleatoria K̄ = J(z || c) ("rechazo implícito"): el atacante no aprende nada.
        """
        k = self.params.k
        dk_pke = dk[: 384 * k]
        ek_pke = dk[384 * k : 768 * k + 32]  # el TFG cogía hasta 768k+64, arrastrando también H(ek)
        h_ek = dk[768 * k + 32 : 768 * k + 64]
        z = dk[768 * k + 64 : 768 * k + 96]

        m_prime = kpke.decrypt(dk_pke, c, self.params, trace)
        K_prime, r_prime = g(m_prime + h_ek)
        K_bar = j(z + c)
        c_prime = kpke.encrypt(ek_pke, m_prime, r_prime, self.params)
        # compare_digest compara en tiempo (casi) constante; ver docs/review.md sobre canales laterales
        accepted = hmac.compare_digest(c, c_prime)

        if trace is not None:
            trace.update(m_prime=m_prime, K_prime=K_prime, K_bar=K_bar, c_prime=c_prime, accepted=accepted)
        return K_prime if accepted else K_bar
