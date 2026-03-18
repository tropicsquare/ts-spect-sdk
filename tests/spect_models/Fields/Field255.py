__author__ = "Vit Masek"
__copyright__ = "Tropic Square s.r.o."
__license___ = "See LICENSE file"
__maintainer__ = "Vit Masek"

from spect_models.utils import LE256, CT_SELECT, decode_le

class Field:
    P = 2**255 - 19

    C1 = (P+3)//8
    C3 = pow(2, (P-1) // 4, P)
    C4 = (P - 5) // 8

    def __init__(self, x: int):
        self.x = x % Field.P

    def __str__(self):
        return hex(self.x)

    def __repr__(self):
        return self.__str__()

    def __add__(self, other):
        if isinstance(other, Field):
            return Field(self.x + other.x)
        elif isinstance(other, int):
            return Field(self.x + other)
        raise NotImplementedError

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if isinstance(other, Field):
            return Field(self.x - other.x)
        elif isinstance(other, int):
            return Field(self.x - other)
        raise NotImplementedError

    def __rsub__(self, other):
        if isinstance(other, int):
            return Field(other - self.x)
        raise NotImplementedError

    def __neg__(self):
        return Field(-self.x)

    def __mul__(self, other):
        if isinstance(other, Field):
            return Field(self.x * other.x)
        elif isinstance(other, int):
            return Field(self.x * other)
        raise NotImplementedError

    def __rmul__(self, other):
        return self.__mul__(other)

    def __eq__(self, other):
        if isinstance(other, Field):
            return self.x == other.x
        elif isinstance(other, int):
            return self.x == (other % Field.P)
        raise NotImplementedError

    def __req__(self, other):
        return self.__eq__(other)

    def __pow__(self, n: int):
        return Field(pow(self.x, n, Field.P))

    def inv(self):
        return pow(self, Field.P-2)

    def __truediv__(self, other):
        if isinstance(other, Field):
            return self * other.inv()
        elif isinstance(other, int):
            tmp = Field(other)
            return self * tmp.inv()
        raise NotImplementedError

    def __rtruediv__(self, other):
        return other * self.inv()

    def is_negative(self):
        return (self.x & 1) == 1

    def __abs__(self):
        return CT_SELECT(-self, self, self.is_negative())

    def to_bytes(self):
        return LE256(self.x)

    @property
    def val(self):
        return self.x

    @staticmethod
    def from_bytes(b: bytes):
        x = decode_le(b) % (2**255)
        return Field(x)

# Non class methods

def sqrt(f: Field):
    s = pow(f.x, Field.C1, Field.P)
    if ( (s*s) % Field.P ) != f.x :
        s = s * Field.C3
    sf = Field(s)
    return abs(sf)