# -*- coding: utf-8 -*-

import subprocess
import random as rn
from enum import Enum
from typing import Type

from .spect_config import (
    KeySlotType,
    CurveType,
)
from .spect_memory import (
    MemorySpace,
    SpectMem,
)


def random_bytes(n: int):
    if n == 0:
        return b''
    else:
        return rn.getrandbits(n*8).to_bytes(n, 'little')

def int2bytes(x: int, length: int = 32, endianity: str = 'little'):
    return int.to_bytes(x, length, endianity)

def bytes2int(b: bytes, endianity: str = 'little'):
    return int.from_bytes(b, endianity)

class SlotMetadataErrType(Enum):
    NO_ERR     = 0
    TYPE_ERR   = 1
    NUMBER_ERR = 2
    ORIGIN_ERR = 3
    CURVE_ERR  = 4

def get_input_source(defines_set: set) -> MemorySpace:
    if "IN_SRC_EN" in defines_set and rn.randint(0, 1):
        return SpectMem.DataRamIn
    else:
        return SpectMem.EmemIn

def get_output_source(defines_set: set) -> MemorySpace:
    if "OUT_SRC_EN" in defines_set and rn.randint(0, 1):
        return SpectMem.DataRamOut
    else:
        return SpectMem.EmemOut

def create_metadata(curve: CurveType, slot: int, origin: int, invalid_metadata=None):

    pub_slot_type = KeySlotType.SLOT_PUBLIC
    priv_slot_type = KeySlotType.SLOT_PRIVATE
    slot_number = slot
    origin_in = origin
    curve_in = curve

    if invalid_metadata == SlotMetadataErrType.TYPE_ERR:
        pub_slot_type = 0xFF
        priv_slot_type = 0xFF
    elif invalid_metadata == SlotMetadataErrType.NUMBER_ERR:
        slot_number = slot+1
    elif invalid_metadata == SlotMetadataErrType.ORIGIN_ERR:
        origin_in = 0xFF
    elif invalid_metadata == SlotMetadataErrType.CURVE_ERR:
        curve_in = 0x42

    pub_metadata_ref   = ((slot_number<<24) | (pub_slot_type<<16)  | (origin_in<<8) | curve_in)
    priv_metadata_ref  = ((slot_number<<24) | (priv_slot_type<<16) | (origin_in<<8) | curve_in)

    return int2bytes(pub_metadata_ref, length=4), int2bytes(priv_metadata_ref, length=4)

def get_release_version():
    try:
        result = subprocess.run(
            ['git', 'describe', '--dirty'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            return output
        else:
            print("Error running 'git describe --dirty':", result.stderr.strip())
            return None

    except FileNotFoundError:
        print("Git command not found. Make sure Git is installed.")
        return None

def get_main_defines(main_file: str) -> set:
    defines_set = set()
    with open(main_file, 'r') as fmain:
        in_defines = False
        for line in fmain:
            if not in_defines:
                in_defines = "DEFINES START" in line
                continue
            if in_defines:
                if line.startswith(".define"):
                    defines_set.add(line.split()[1])
                elif "DEFINES END" in line:
                    return defines_set

def set_seed(args) -> int:
    if hasattr(args, "seed"):
        return args.seed
    else:
        return rn.randint(0, 2**16-1)
