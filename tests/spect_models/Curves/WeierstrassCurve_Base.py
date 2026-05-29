__author__ = "Vit Masek"
__copyright__ = "Tropic Square s.r.o."
__license___ = "See LICENSE file"
__maintainer__ = "Vit Masek"

from abc import ABC, abstractmethod
import copy

from typing import Type

from spect_models.utils import CT_SELECT, CSWAP

class WeierstrassCurve(ABC):
    name    : str = ""
    Q       : int = 0

    A       : any = None
    B       : any = None

    Field   : Type = None

    def __init__(self, x, y, z = None):
        self.x = x
        self.y = y
        self.z = z if z is not None else self.Field(1)

    def is_infinity(self) -> bool:
        return self.z == 0

    def is_valid(self) -> bool:
        if self.is_infinity():
            return True

        lhs = self.y**2 * self.z
        rhs = self.x**3 + self.A * self.x * self.z**2 + self.B * self.z**3
        return lhs == rhs

    def __str__(self) -> str:
        s = ""
        s += "X: " + str(self.x) + "\n"
        s += "Y: " + str(self.y) + "\n"
        if self.z != 1:
            s += "Z: " + str(self.z) + "\n"
        return s

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        X = self.x * other.z == other.x * self.z
        Y = self.y * other.z == other.y * self.z
        return X and Y

    def __neg__(self):
        return self.__class__(self.x, -self.y, self.z)

    def __add__(self, other):
        if self == other:
            return self._dbl()
        else:
            return self._add(other)

    def __sub__(self, other):
        return self + (-other)

    def spm(self, k: int):
        Q1 = copy.deepcopy(self)
        Q0 = self.__class__(self.Field(0), self.Field(1), self.Field(0))

        for i in range(255, -1, -1):
            sw = (k >> i) & 1
            Q0, Q1 = CSWAP(Q0, Q1, sw)

            Q1 = Q0 + Q1
            Q0 = Q0 + Q0

            Q0, Q1 = CSWAP(Q0, Q1, sw)

        return Q0

    def to_affine(self):
        z_inv = self.z.inv()
        self.x = self.x * z_inv
        self.y = self.y * z_inv
        self.z = self.Field(1)
        return self

    def to_bytes(self, encoding="Raw"):
        self.to_affine()

        if encoding == "BIP340":
            return self.x.to_bytes()
        elif encoding == "Compressed":
            if self.y.is_negative():
                b = b'\x03'
            else:
                b = b'\x02'
            return b + self.x.to_bytes()
        elif encoding == "Uncompressed":
            return b'\x04' + self.x.to_bytes() + self.y.to_bytes()
        elif encoding == "Raw":
            return self.x.to_bytes() + self.y.to_bytes()
        else:
            raise Exception(f"Unsupported encoding '{encoding}'")

    @classmethod
    def from_bytes(cls, b: bytes):
        pass

    @abstractmethod
    def _add(self, other):
        """Curve specific addition logic"""
        pass

    @abstractmethod
    def _dbl(self):
        """Curve specific doubling logic"""
        pass

