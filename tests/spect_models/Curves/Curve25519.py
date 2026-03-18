import copy

from typing import Optional, Literal
from typing_extensions import Self

from spect_models.Fields.Field255 import Field, sqrt
from spect_models.utils import CSWAP

class Curve25519:

    A = Field(486662)
    A2D4 = (A + 2) / 4
    A2_SQRT = Field(0x141b0b6806563d503de05885280b59109ca5ee38d7b56c9c165db7106377bbd8)
    A2_SQRT_INV = Field(0x1fb58aa1280baf7747fd932ef6d98b8c0d0547929c2a02bf22f6d78daa702f61)

    Q = 2**252 + 27742317777372353535851937790883648493

    def is_valid(self):
        lhs = self.z * self.y * self.y
        rhs = self.x * (self.x**2 + self.z*(Curve25519.A * self.x + self.z))
        return lhs == rhs

    def __init__(self, x: Field, y: Optional[Field] = None, z: Field = Field(1)):
        self.x = x
        self.z = z
        if y is None:
            y_sqr_z = self.x * (self.x**2 + self.z*(Curve25519.A * self.x + self.z))
            y_sqr = y_sqr_z / self.z
            self.y = sqrt(y_sqr)
            if not self.y.is_negative():
                self.y = -self.y
        else:
            self.y = y

    def __str__(self):
        s = ""
        s += "X: " + str(self.x) + "\n"
        s += "Y: " + str(self.y) + "\n"
        s += "Z: " + str(self.z) + "\n"
        return s

    def __repr__(self):
        return self.__str__()

    def __int__(self) -> int:
        self.to_affine()
        return self.x.val

    def __eq__(self, other):
        s_X = self.x * other.z
        s_Y = self.y * other.z
        o_X = other.x * self.z
        o_Y = other.y * self.z

        return (s_X == o_X) and (s_Y == o_Y)
    
    def __neg__(self):
        return Curve25519(self.x, -self.y, self.z)
    
    def __add__(self, other):
        # 1. Denominators
        U1 = self.x * other.z
        U2 = other.x * self.z

        S1 = self.y * other.z
        S2 = other.y * self.z

        Z1Z2 = self.z * other.z

        if U1 == U2:
            if S1 == S2:
                raise NotImplementedError("Full doubling on Curve25519 is not supported")
            else:
                return Curve25519(Field(0), Field(1), Field(0))

        H = U2 - U1
        R = S2 - S1                     # Last S2
        U12 = U1 + U2                   # Last U2

        H2 = H * H
        H3 = H2 * H

        Z3 = H3*Z1Z2

        T3 = S1 * H3                    # Last S1 and H3

        T1 = R * R
        T1 = T1 * Z1Z2
        T2 = Curve25519.A * Z1Z2        # Last Z1Z2
        T2 = T2 + U12                   # Last U12
        T2 = T2 * H2
        NX = T1 - T2

        X3 = H * NX                     # Last H

        T1 = U1 * H2                    # Last U1 H2
        T1 = T1 - NX                    # Last NX
        T1 = T1 * R                     # Last R

        Y3 = T1 - T3

        return Curve25519(X3, Y3, Z3)
    
    def __sub__(self, other):
        return self + (-other)
    
    def xADD(self, other, diff):
        V0 = self.x + self.z
        V1 = other.x - other.z
        V1 = V1 * V0
        V0 = self.x - self.z
        V2 = other.x + other.z
        V2 = V2 * V0
        V3 = V1 + V2
        V3 = V3 * V3
        V4 = V1 - V2
        V4 = V4 * V4
        XQ = diff.z * V3
        ZQ = diff.x * V4

        return Curve25519(x=XQ, z=ZQ)

    def xDBL(self):
        V1 = self.x + self.z
        V1 = V1 * V1
        V2 = self.x - self.z
        V2 = V2 * V2
        XP = V1 * V2
        V1 = V1 - V2
        V3 = Curve25519.A2D4 * V1
        V3 = V3 + V2
        ZP = V1 * V3

        return Curve25519(x=XP, z=ZP)
    
    def to_affine(self):
        z_inv = self.z.inv()
        self.x = self.x * z_inv
        self.y = self.y * z_inv
        self.z = Field(1)
        return self
        
    def spm(self, k: int):
        Q1 = copy.deepcopy(self)
        Q0 = Curve25519(x=Field(1), z=Field(0))

        for i in range(255, -1, -1):
            sw = (k >> i) & 1
            Q0, Q1 = CSWAP(Q0, Q1, sw)

            Q1 = Q0.xADD(Q1, self)
            Q0 = Q0.xDBL()

            Q0, Q1 = CSWAP(Q0, Q1, sw)

        return Q0

    def to_bytes(self, encoding: Literal['X-Only', 'Raw'] = "X-Only"):
        self.to_affine()
        if encoding == "X-Only":
            return self.x.to_bytes()
        if encoding == "Raw":
            return self.x.to_bytes() + self.y.to_bytes()

        raise Exception(f"Unsupported encoding '{encoding}'")

    @classmethod
    def from_bytes(cls, b: bytes) -> Self:
        if len(b) == 32: # X-Only point
            x = decode_le(b)
            return cls(x)

        if len(b) == 64: # Raw point
            x = Field.from_bytes(b[:32])
            y = Field.from_bytes(b[32:])
            return cls(x, y)

        raise Exception("Unsupported encoding")


CURVE25519_BASE = Curve25519(Field(9))

def int2scalar(s: int) -> int:
    s_ = s & (1 << 254) - 8
    s_ |= (1 << 254)
    return s_
