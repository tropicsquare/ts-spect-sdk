# -*- coding: utf-8 -*-

import subprocess
import os
import random as rn
from enum import Enum
import numpy as np
import pandas as pd
import time
import datetime
import sys
import binascii

from .spect_config import (
    KeySlotType,
    CurveType,
)
from .spect_memory import (
    MemorySpace,
    SpectMem,
)

from .spect_default_fw import (
    SpectFw,
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

def str2bytes(s: str):
    return binascii.unhexlify(s)

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

def parse_exec_info(test_dir: str, run_name: str) -> pd.DataFrame:
    exec_info_file = os.path.join(test_dir, run_name, "exec_info")
    exec_info_list = []
    with open(exec_info_file, 'r') as f:
        for line in f:
            split = line.split(":")
            exec_info_list.append({
                "INST_ADDR" : int(split[0], 16),
                "EXEC_CNT"  : int(split[1], 10),
                "INST_CODE" : int(split[2], 16),
                "INST_NAME" : split[3].strip()
            })

    return pd.DataFrame(exec_info_list)

def get_inst_code(fw_file: SpectFw, addr: int) -> int:
    fw = np.loadtxt(fw_file.hex_file, dtype=str, usecols=0)
    return int(fw[(addr-0x8000)//4], 16)

def lines2str(lines: list, indent: int = 0):
    return "\n".join(('\t'*indent)+line.rstrip("\n") for line in lines)

# Custom Progress Bar, if TQDM is not available in the environment
class ProgressBar:
    def __init__(self, it_cnt, it_name: str = "Iteration"):
        self.start_t = time.time()
        self.it_cnt = it_cnt
        self.it = 0
        self.it_name = it_name

    def update(self):
        self.it += 1

        it_t = time.time()
        elapsed = (it_t - self.start_t)
        s_per_is = elapsed / (self.it)
        remaining = (s_per_is * self.it_cnt) - elapsed
        percent = 100*(self.it)/self.it_cnt
        progress_s = (
            '\r\033[K'
            f"{self.it_name} {self.it}/{self.it_cnt} {percent:0.0f} % | "
            f"Elapsed {datetime.timedelta(seconds=int(elapsed))} | "
            f"Remaining {datetime.timedelta(seconds=int(remaining))}\t"
        )
        sys.stdout.write(progress_s)
        sys.stdout.flush()

    def finish(self):
        sys.stdout.write('\r\033[K')
        sys.stdout.flush()
