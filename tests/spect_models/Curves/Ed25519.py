__author__ = "Vit Masek"
__copyright__ = "Tropic Square s.r.o."
__license___ = "See LICENSE file"
__maintainer__ = "Vit Masek"

import copy

from typing import (
    Literal,
    Optional,
)
from typing_extensions import Self

from spect_models.Fields.Field255 import Field, sqrt
from spect_models.utils import (
    CSWAP,
    decode_le,
    LE256,
)

class Ed25519:

    D = Field(37095705934669439343138083508754565189542113879843219016388785533085940283555)
    A = Field(-1)
    Q = 2**252 + 27742317777372353535851937790883648493

    def is_valid(self):
        return Ed25519.A * self.x**2 + self.y**2 == 1 + Ed25519.D * self.x**2 * self.y**2

    def __init__(self, x: Field, y: Field, z: Field = Field(1), t: Optional[Field] = None):
        self.x = x
        self.y = y
        self.z = z
        if t is None:
            self.t = (x * y)
        else:
            self.t = t

    def __str__(self):
        s = ""
        s += "X: " + str(self.x) + "\n"
        s += "Y: " + str(self.y) + "\n"
        s += "Z: " + str(self.z) + "\n"
        s += "T: " + str(self.t) + "\n"
        return s

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        X = (self.x * other.y) == (self.y * other.x)
        Y = (self.y * other.y) == (self.x * other.x) # a = -1
        return X or Y

    def __neg__(self):
        return Ed25519(-self.x, self.y, self.z, -self.t)

    def __add__(self, other):
        A = ((self.y - self.x) * (other.y - other.x))
        B = ((self.y + self.x) * (other.y + other.x))
        C = (self.t * 2 * Ed25519.D * other.t)
        D = (self.z * 2 * other.z)
        E = B-A
        F = D-C
        G = D+C
        H = B+A
        X3 = E*F
        Y3 = G*H
        T3 = E*H
        Z3 = F*G
        return Ed25519(X3, Y3, Z3, T3)

    def __sub__(self, other):
        return self + (-other)

    @classmethod
    def __recover_x(cls, y: Field, sign: int) -> Field:
        x = sqrt((y**2 - 1) / (cls.D * y**2 + 1))

        if sign == 0 and x.is_negative():
            x = -x

        return x

    def to_affine(self):
        z_inv = self.z.inv()
        self.x = self.x * z_inv
        self.y = self.y * z_inv
        self.t = self.t * z_inv
        self.z = Field(1)
        return self

    def spm(self, k: int):
        Q1 = copy.deepcopy(self)
        Q0 = Ed25519(Field(0), Field(1), Field(1), Field(0))

        for i in range(255, -1, -1):
            sw = (k >> i) & 1
            Q0, Q1 = CSWAP(Q0, Q1, sw)

            Q1 = Q0 + Q1
            Q0 = Q0 + Q0

            Q0, Q1 = CSWAP(Q0, Q1, sw)

        return Q0

    def to_bytes(self, encoding: Literal['Compressed', 'Raw'] = "Compressed"):
        self.to_affine()
        if encoding == "Compressed":
            sign = self.x.val & 1
            return LE256(self.y.val | (sign << 255))
        if encoding == "Raw":
            return self.x.to_bytes() + self.y.to_bytes()

        raise Exception(f"Unsupported encoding {encoding}")

    @classmethod
    def from_bytes(cls, b: bytes) -> Self:
        if len(b) == 32: # Comporessed point
            tmp = decode_le(b)
            sign = (tmp >> 255) & 1
            y = Field(tmp & (2**255 - 1))
            x = cls.__recover_x(y, sign)
            return cls(x, y)

        if len(b) == 64: # Raw point
            x = Field.from_bytes(b[:32])
            y = Field.from_bytes(b[32:])
            return cls(x, y)

        raise Exception("Unsupported encoding")

ED25519_BASE = Ed25519(
    Field(0x216936d3cd6e53fec0a4e231fdd6dc5c692cc7609525a7b2c9562d608f25d51a),
    Field(0x6666666666666666666666666666666666666666666666666666666666666658),
    Field(0x0000000000000000000000000000000000000000000000000000000000000001),
    Field(0x67875f0fd78b766566ea4e8e64abe37d20f09f80775152f56dde8ab3a5b7dda3)
)
