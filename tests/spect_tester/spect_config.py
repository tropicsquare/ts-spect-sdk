# -*- coding: utf-8 -*-

from enum import IntEnum
import os

TS_REPO_ROOT = os.environ["TS_REPO_ROOT"]
SPECT_FW_MAIN = TS_REPO_ROOT+"/src/main.s"

RAR_STACK_DEPTH = 5

class SpectMem:
    DATA_RAM_IN         = 0x0000
    DATA_RAM_IN_SRC     = DATA_RAM_IN>>12
    DATA_RAM_IN_DEPTH   = 512
    DATA_RAM_IN_SIZE    = DATA_RAM_IN_DEPTH*8

    DATA_RAM_OUT        = 0x1000
    DATA_RAM_OUT_SRC    = DATA_RAM_OUT>>12
    DATA_RAM_OUT_DEPTH  = 128
    DATA_RAM_OUT_SIZE   = DATA_RAM_OUT_DEPTH*8

    EMEM_IN             = 0x4000
    EMEM_IN_SRC         = EMEM_IN>>12
    EMEM_IN_DEPTH       = 36
    EMEM_IN_SIZE        = EMEM_IN_DEPTH*8

    EMEM_OUT            = 0x5000
    EMEM_OUT_SRC        = EMEM_OUT>>12
    EMEM_OUT_DEPTH      = 32
    EMEM_OUT_SIZE       = EMEM_OUT_DEPTH*8

class EccSlot:
    PRIV_SLOT_LAYOUT = {
        "k1" : 0*8,
        "k2" : 1*8,
        "k3" : 2*8,
        "k4" : 3*8
    }
    PUB_SLOT_LAYOUT = {
        "x" : 5*8,
        "y" : 6*8
    }
    METADATA_OFFSET = 4*8

class SpectOpStatus(IntEnum):
    RET_OP_SUCCESS              = 0x00
    RET_CTX_ERR                 = 0xf1
    RET_KEY_ERR                 = 0xf2
    RET_OP_ID_ERR               = 0xf3
    RET_CURVE_TYPE_ERR          = 0xf4
    RET_GRV_ERR                 = 0xf5
    RET_SLOT_METADATA_ERR       = 0xf6
    RET_X25519_ERR_INV_PRIV_KEY = 0x11
    RET_X25519_ERR_INV_PUB_KEY  = 0x12
    RET_ECDSA_ERR_GENERIC       = 0x20
    RET_ECDSA_ERR_INV_NONCE     = 0x21
    RET_ECDSA_ERR_INV_R         = 0x22
    RET_ECDSA_ERR_INV_S         = 0x23
    RET_ECDSA_ERR_FINAL_VERIFY  = 0x24
    RET_EDDSA_ERR_GENERIC       = 0x30
    RET_EDDSA_ERR_INV_PRIV_KEY  = 0x34
    RET_EDDSA_ERR_INV_PUB_KEY   = 0x35
    RET_EDDSA_ERR_FINAL_VERIFY  = 0x36
    RET_POINT_INTEGRITY_ERR     = 0x41

class L3Result(IntEnum):
    L3_RESULT_OK                = 0xc3
    L3_RESULT_FAIL              = 0x3c
    L3_RESULT_INVALID_CMD       = 0x02
    L3_RESULT_INVALID_KEY       = 0x12

class CurveType(IntEnum):
    P256    = 0x01
    ED25519 = 0x02
    INVALID = 0xee

class KeySlotType(IntEnum):
    SLOT_PUBLIC     = 0xAA
    SLOT_PRIVATE    = 0x55

class KeyTypes(IntEnum):
    STPRIV = 0x00
    STPUB  = 0x01
    SHPUB  = 0x02
    ECC    = 0x04
