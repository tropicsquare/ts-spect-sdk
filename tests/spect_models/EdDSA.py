__author__ = "Vit Masek"
__copyright__ = "Tropic Square s.r.o."
__license___ = "See LICENSE file"
__maintainer__ = "Vit Masek"

import random as rn

from typing import (
    Optional,
    Union,
    Type,
    Literal,
)
from typing_extensions import Self

from spect_models.tmac import tmac_int
from spect_models.Curves.Ed25519 import Ed25519, ED25519_BASE
from spect_models.utils import (
    decode_le,
    LE256,
    sha512,
    random_bytes,
)

class KeyPair:
    P: Ed25519
    s: int
    prefix: int

    def __init__(self, P: Ed25519, s: int, prefix: int):
        self.P = P
        self.s = s
        self.prefix = prefix

    def PrivateBytes(self) -> bytes:
        return LE256(self.s)
    
    def PublicBytes(self, encoding: Literal['Compressed', 'Raw', "spect"] = "Compressed") -> bytes:
        if encoding == "spect":
            return self.P.to_bytes(encoding="Compressed")[::-1]
        else:
            return self.P.to_bytes(encoding)

    def __str__(self) -> str:
        s = ""
        s += "priv  : " + self.PrivateBytes().hex() + '\n'
        s += "pub   : " + self.PublicBytes().hex() + '\n'
        return s
    
    def __repr__(self):
        return self.__str__()
    
class Signature:
    r : bytes
    s : int

    def __init__(self, r: bytes, s: int):
        self.r = r
        self.s = s

    def to_bytes(self) -> bytes:
        return self.r + LE256(self.s)
    
    @classmethod
    def from_bytes(cls, b: bytes) -> Self:
        if len(b) == 64:
            r = b[:32]
            s = decode_le(b[32:])
        else:
            raise Exception(f"Invalid signature length: {len(b)}")

        return cls(r, s)
    
    def __str__(self):
        s = "r: " + self.r.hex() + '\n'
        s += "s: " + LE256(self.s).hex() + '\n'
        return s
    
    def __repr__(self):
        return self.__str__()

class EdDSA:

    NONCE_TMAC_DST = b'\x0C'

    @classmethod
    def KeyGen(cls, seed: Optional[bytes] = None) -> KeyPair:
        if seed is not None:
            assert len(seed) == 32
        else:
            seed = random_bytes(32)

        h = sha512(seed)

        s = decode_le(h[:32])
        prefix = decode_le(h[32:])

        s &= (1 << 254) - 8
        s |= (1 << 254)
        s %= Ed25519.Q

        P = ED25519_BASE.spm(s).to_affine()

        return KeyPair(P, s, prefix)
    
    @classmethod
    def __get_signature_nonce(cls, M: bytes, sch: bytes, scn: bytes, prefix: int) -> int:
        k1 = tmac_int(prefix, sch + scn + M, cls.NONCE_TMAC_DST)
        k2 = tmac_int(k1, b"", cls.NONCE_TMAC_DST)
        return (k1 | (k2 << 256)) % Ed25519.Q
    
    @classmethod
    def Sign(cls, M: bytes, Key: KeyPair, sch: bytes, scn: bytes) -> Signature:
        k = cls.__get_signature_nonce(M, sch, scn, Key.prefix)
        R = ED25519_BASE.spm(k).to_bytes()

        h = decode_le(sha512(R + Key.PublicBytes() + M)) % Ed25519.Q

        S = (k + h * Key.s) % Ed25519.Q

        return Signature(R, S)
    
    @classmethod
    def Verify(cls, M: bytes, pub_key: Union[bytes, KeyPair, Ed25519], signature: Union[bytes, Signature]) -> bool:
        if isinstance(pub_key, bytes):
            P = Ed25519.from_bytes(pub_key)
        elif isinstance(pub_key, KeyPair):
            P = pub_key.P
        elif isinstance(pub_key, Ed25519):
            P = pub_key
        else:
            raise Exception(f"Unsupported public key type: {type(pub_key)}")
        
        if isinstance(signature, bytes):
            sig = Signature.from_bytes(signature)
        elif isinstance(signature, Signature):
            sig = signature
        else:
            raise Exception(f"Unsupported signature type {type(signature)}")

        h = decode_le(sha512(sig.r + P.to_bytes() + M)) % Ed25519.Q

        sB = ED25519_BASE.spm(sig.s)
        hP = P.spm(h)

        return sig.r == (sB - hP).to_bytes()
