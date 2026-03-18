__author__ = "Vit Masek"
__copyright__ = "Tropic Square s.r.o."
__license___ = "See LICENSE file"
__maintainer__ = "Vit Masek"

import random as rn

from typing import Optional, Union, Type
from typing_extensions import Self

from spect_models.tmac import tmac_int
from spect_models.Curves.WeierstrassCurve_Base import WeierstrassCurve
from spect_models.Curves.secp256r1 import secp256r1, SECP256R1_BASE
from spect_models.utils import (
    decode_be,
    BE256,
    LE256,
    INV0,
    random_bytes,
)

from abc import ABC, abstractmethod

class KeyPair:
    P: WeierstrassCurve
    d: int
    w: int

    def __init__(self, P: WeierstrassCurve, d: int, w: int):
        self.P = P
        self.d = d
        self.w = w

    def PrivateBytes(self) -> bytes:
        return BE256(self.d)

    def PublicBytes(self, encoding="Raw") -> bytes:
        if encoding == "spect":
            return LE256(self.P.x.val) + LE256(self.P.y.val)
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
    r : int
    s : int

    def __init__(self, r: int, s: int):
        self.r = r
        self.s = s

    def to_bytes(self) -> bytes:
        return BE256(self.r) + BE256(self.s)

    @classmethod
    def from_bytes(cls, b: bytes) -> Self:
        if len(b) == 64:
            assert len(b) == 64
            r = decode_be(b[:32])
            s = decode_be(b[32:])
        else:
            raise Exception(f"Invalid signature length: {len(b)}")

        return Signature(r, s)

    def __str__(self):
        s = "r: " + BE256(self.r).hex() + '\n'
        s += "s: " + BE256(self.s).hex() + '\n'
        return s

    def __repr__(self):
        return self.__str__()

class ECDSA:

    KEY_GEN_TMAC_DST = b'\x0A'
    NONCE_TMAC_DST = b'\x0B'

    Curve : Type = None
    CurveBase : any = None

    @classmethod
    def KeyGen(cls, seed: Optional[bytes] = None) -> KeyPair:
        if seed is not None:
            d = decode_be(seed)
            assert (d > 0 and d < cls.Curve.Q)
        else:
            seed = random_bytes(32)
            d = decode_be(seed) % cls.Curve.Q

        w = tmac_int(d, b"", cls.KEY_GEN_TMAC_DST)

        P = cls.CurveBase.spm(d).to_affine()

        return KeyPair(P, d, w)

    @classmethod
    def __get_signature_nonce(cls, M: bytes, sch: bytes, scn: bytes, w: int) -> int:
        k1 = tmac_int(w, sch + scn + M, cls.NONCE_TMAC_DST)
        k2 = tmac_int(k1, b"", cls.NONCE_TMAC_DST)
        return (k1 | (k2 << 256)) % cls.Curve.Q

    @classmethod
    def Sign(cls, M: bytes, Key: KeyPair, sch: bytes, scn: bytes) -> Optional[Signature]:
        assert len(M) == 32

        k = cls.__get_signature_nonce(M, sch, scn, Key.w)
        if k == 0:
            print(f"{cls.__name__} Signature nonce is 0.")
            return None

        R = cls.CurveBase.spm(k).to_affine()
        r = R.x.val % cls.Curve.Q

        if r == 0:
            print(f"{cls.__name__} Signature r is 0.")
            return None

        z = decode_be(M)
        s = ((z + r*Key.d) * INV0(k, cls.Curve.Q)) % cls.Curve.Q

        if s == 0:
            print(f"{cls.__name__} Signature s is 0.")
            return None

        return Signature(r, s)


    @classmethod
    def Verify(cls, M: bytes, pub_key: any, signature: any) -> bool:
        assert len(M) == 32

        if isinstance(pub_key, bytes):
            P = cls.Curve.from_bytes(pub_key)
        elif isinstance(pub_key, KeyPair):
            P = pub_key.P
        elif isinstance(pub_key, cls.Curve):
            P = pub_key
        else:
            raise Exception(f"Unsupported public key type: {type(pub_key)}")

        if isinstance(signature, bytes):
            sig = Signature.from_bytes(signature)
        elif isinstance(signature, Signature):
            sig = signature
        else:
            raise Exception(f"Unsupported signature type: {type(signature)}")

        z = decode_be(M)
        s_inv = INV0(sig.s, cls.Curve.Q)

        assert ((sig.s * s_inv) % cls.Curve.Q) == 1

        u1 = (z * s_inv) % cls.Curve.Q
        u2 = (sig.r * s_inv) % cls.Curve.Q

        X = (cls.CurveBase.spm(u1) + P.spm(u2)).to_affine()

        x = X.x.val % cls.Curve.Q

        return sig.r == x

class ECDSA_SECP256R1(ECDSA):
    KEY_GEN_TMAC_DST = b'\x0A'
    NONCE_TMAC_DST = b'\x0B'

    Curve = secp256r1
    CurveBase = SECP256R1_BASE
