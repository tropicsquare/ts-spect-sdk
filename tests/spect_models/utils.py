import hashlib
import binascii
import base64
import random as rn

from typing import Tuple

def random_bytes(n: int):
    if n == 0:
        return b''
    else:
        return rn.getrandbits(n*8).to_bytes(n, 'little')

def ROL32(value, shift):
    value &= 0xFFFFFFFF
    return ((value << shift) | (value >> (32 - shift))) & 0xFFFFFFFF

def ROR32(value, shift):
    value &= 0xFFFFFFFF
    return ((value >> shift) | (value << (32 - shift))) & 0xFFFFFFFF

def cut_bytes(b: bytes, i: int) -> Tuple[bytes, bytes]:
    return b[:i], b[i:]

def decode_le(b: bytes):
    return int.from_bytes(b, 'little')

def decode_be(b: bytes):
    return int.from_bytes(b, 'big')

def hex2bytes(s: str) -> bytes:
    return binascii.unhexlify(s)

def hex2int(s: str) -> int:
    return decode_le(hex2bytes(s))

def to_bytearray(data) -> bytearray:
    if isinstance(data, str):
        return bytearray(data, 'utf-8')
    return bytearray(data)

def LE32(x: int) -> bytearray:
    assert (x >= 0) and (x < 2**32)
    return int.to_bytes(x, length=4, byteorder='little')

def LE64(x: int) -> bytearray:
    assert (x >= 0) and (x < 2**64)
    return int.to_bytes(x, length=8, byteorder='little')

def LE256(x: int) -> bytearray:
    assert (x >= 0) and (x < 2**256)
    return int.to_bytes(x, length=32, byteorder='little')

def BE32(x: int) -> bytearray:
    assert (x >= 0) and (x < 2**32)
    return int.to_bytes(x, length=4, byteorder='big')

def BE64(x: int) -> bytearray:
    assert (x >= 0) and (x < 2**64)
    return int.to_bytes(x, length=8, byteorder='big')

def BE256(x: int) -> bytearray:
    assert (x >= 0) and (x < 2**256)
    return int.to_bytes(x, length=32, byteorder='big')

def CT_SELECT(v, u, cond):
    if cond:
        return v
    return u

def CSWAP(a, b, cond):
    if cond:
        return b, a
    return a, b

def INV0(x: int, mod: int) -> int:
    return pow(x, mod-2, mod)

def sha512(s: bytes) -> bytes:
    sha = hashlib.sha512(s).digest()
    return sha

def sha256(s: bytes) -> bytes:
    return hashlib.sha256(s).digest()

def hmac_sha512(k: bytes, text: bytes) -> bytes:
    B = 128
    HMAC_IPAD = b'\x36'*B
    HMAC_OPAD = b'\x5c'*B

    k_padded = k + b'\x00'*(B-len(k))
    k_xor_ipad = bytes(x ^ y for x, y in zip(k_padded, HMAC_IPAD))
    k_xor_opad = bytes(x ^ y for x, y in zip(k_padded, HMAC_OPAD))

    return sha512(k_xor_opad + sha512(k_xor_ipad + text))

def hmac_sha256(k: bytes, text: bytes) -> bytes:
    B = 64
    HMAC_IPAD = b'\x36'*B
    HMAC_OPAD = b'\x5c'*B

    k_padded = k + b'\x00'*(B-len(k))
    k_xor_ipad = bytes(x ^ y for x, y in zip(k_padded, HMAC_IPAD))
    k_xor_opad = bytes(x ^ y for x, y in zip(k_padded, HMAC_OPAD))

    return sha256(k_xor_opad + sha256(k_xor_ipad + text))
