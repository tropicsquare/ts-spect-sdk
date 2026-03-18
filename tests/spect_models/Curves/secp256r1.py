import random as rn

import spect_models.Fields.Field_secp256r1 as R1Field
from spect_models.Curves.WeierstrassCurve_Base import WeierstrassCurve
from spect_models.utils import CT_SELECT

class secp256r1(WeierstrassCurve):
    name = "secp256k1"
    Field = R1Field.Field
    Q = 0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551
    A = R1Field.Field(0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFC)
    B = R1Field.Field(0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b)

    Z = 0xffffffff00000001000000000000000000000000fffffffffffffffffffffff5

    def _add(self, other):
        t0 = self.x * other.x
        t1 = self.y * other.y
        t2 = self.z * other.z
        t3 = self.x + self.y
        t4 = other.x + other.y
        t3 = t3 * t4
        t4 = t0 + t1
        t3 = t3 - t4
        t4 = self.y + self.z
        X3 = other.y + other.z
        t4 = t4 * X3
        X3 = t1 + t2
        t4 = t4 - X3
        X3 = self.x + self.z
        Y3 = other.x + other.z
        X3 = X3 * Y3
        Y3 = t0 + t2
        Y3 = X3 - Y3
        Z3 = secp256r1.B * t2
        X3 = Y3 - Z3
        Z3 = X3 + X3
        X3 = X3 + Z3
        Z3 = t1 - X3
        X3 = t1 + X3
        Y3 = secp256r1.B * Y3
        t1 = t2 + t2
        t2 = t1 + t2
        Y3 = Y3 - t2
        Y3 = Y3 - t0
        t1 = Y3 + Y3
        Y3 = t1 + Y3
        t1 = t0 + t0
        t0 = t1 + t0
        t0 = t0 - t2
        t1 = t4 * Y3
        t2 = t0 * Y3
        Y3 = X3 * Z3
        Y3 = Y3 + t2
        X3 = t3 * X3
        X3 = X3 - t1
        Z3 = t4 * Z3
        t1 = t3 * t0
        Z3 = Z3 + t1
        return secp256r1(X3, Y3, Z3)

    def _dbl(self):
        t0 = self.x * self.x
        t1 = self.y * self.y
        t2 = self.z * self.z
        t3 = self.x * self.y
        t3 = t3 + t3
        Z3 = self.x * self.z
        Z3 = Z3 + Z3
        Y3 = secp256r1.B * t2
        Y3 = Y3 - Z3
        X3 = Y3 + Y3
        Y3 = X3 + Y3
        X3 = t1 - Y3
        Y3 = t1 + Y3
        Y3 = X3 * Y3
        X3 = X3 * t3
        t3 = t2 + t2
        t2 = t2 + t3
        Z3 = secp256r1.B * Z3
        Z3 = Z3 - t2
        Z3 = Z3 - t0
        t3 = Z3 + Z3
        Z3 = Z3 + t3
        t3 = t0 + t0
        t0 = t3 + t0
        t0 = t0 - t2
        t0 = t0 * Z3
        Y3 = Y3 + t0
        t0 = self.y * self.z
        t0 = t0 + t0
        Z3 = t0 * Z3
        X3 = X3 - Z3
        Z3 = t0 * t1
        Z3 = Z3 + Z3
        Z3 = Z3 + Z3
        return secp256r1(X3, Y3, Z3)

    @classmethod
    def from_bytes(cls, b: bytes):
        if len(b) == 32:
            x = cls.Field.from_bytes(b)
            is_negative = False

        elif len(b) == 33:
            x = cls.Field.from_bytes(b[1:])
            if b.startswith(b'\x03'):
                is_negative = True
            elif b.startswith(b'\x02'):
                is_negative = False
            else:
                print("Invalid sign for Compressed encoding!")
                return None

        elif len(b) == 65 and b.startswith(b'\x04'):
            x = cls.Field.from_bytes(b[1:33])
            y = cls.Field.from_bytes(b[33:])
            return cls(x, y)

        elif len(b) == 64:
            x = cls.Field.from_bytes(b[:32])
            y = cls.Field.from_bytes(b[32:])
            return cls(x, y)

        else:
            print("Invalid point encoding!")
            return None

        rhs = x**3 + cls.B
        was_square, y = R1Field.sqrt(rhs)

        if not was_square:
            print("Invalid X-Coordinate!")
            return None

        if y.is_negative() == is_negative:
            return cls(x, y)
        else:
            y = -y
            return cls(x, y)

SECP256R1_BASE = secp256r1(
    x = R1Field.Field(0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296),
    y = R1Field.Field(0x4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5)
)