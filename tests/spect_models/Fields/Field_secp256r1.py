__author__ = "Vit Masek"
__copyright__ = "Tropic Square s.r.o."
__license___ = "See LICENSE file"
__maintainer__ = "Vit Masek"

from spect_models.utils import CT_SELECT, decode_be, decode_le, BE256, LE256

######################################################################
#   Field Math
######################################################################
class Field:
    P = 0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff

    C1 = (P+1)//4
    C2 = 0xda538e3be1d89b99c978fc675180aab27b8d1ff84c55d5b62ccd3427e433c47f
    C3 = (P-3)//4

    x: int

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
        return NotImplemented

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if isinstance(other, Field):
            return Field(self.x - other.x)
        elif isinstance(other, int):
            return Field(self.x - other)
        return NotImplemented

    def __rsub__(self, other):
        if isinstance(other, int):
            return Field(other - self.x)
        return NotImplemented

    def __neg__(self):
        return Field(-self.x)

    def __mul__(self, other):
        if isinstance(other, Field):
            return Field(self.x * other.x)
        elif isinstance(other, int):
            return Field(self.x * other)
        return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)

    def __eq__(self, other):
        if isinstance(other, Field):
            return self.x == other.x
        elif isinstance(other, int):
            return self.x == (other % Field.P)
        return NotImplemented

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
        return NotImplemented

    def __rtruediv__(self, other):
        return other * self.inv()

    def is_negative(self):
        return (self.x & 1) == 1

    @property
    def val(self):
        return self.x

    def __abs__(self):
        return CT_SELECT(-self, self, self.is_negative())

    def to_bytes(self, encoding='big'):
        if encoding == 'big':
            return BE256(self.x)
        elif encoding == 'little':
            return LE256(self.x)
        else:
            raise Exception(f"Invalid encoding '{encoding}'")

    @staticmethod
    def from_bytes(b: bytes, encoding='big'):
        if encoding == 'big':
            return Field(decode_be(b))
        elif encoding == 'little':
            return Field(decode_le(b))
        else:
            raise Exception(f"Invalid encoding '{encoding}'")

# Non class methods
def sqrt(f: Field):
    s = pow(f.x, Field.C1, Field.P)
    if ( (s*s) % Field.P ) != f.x :
        return (False, Field(s))
    return ( (s*s) % Field.P ) == f.x, Field(s)


def sqrt_ratio_3mod4(u: Field, v: Field):
    tv1 = v * v
    tv2 = u * v
    tv1 = tv1 * tv2
    y1 = tv1**Field.C3
    y1 = y1 * tv2
    y2 = y1 * Field.C2
    tv3 = y1 * y1
    tv3 = tv3 * v
    isQR = tv3 == u
    y = CT_SELECT(y1, y2, isQR)

    return (isQR, y)