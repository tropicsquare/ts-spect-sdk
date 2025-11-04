
# -*- coding: utf-8 -*-

import random as rn
import numpy as np

#INST_NOP = 0x9513_6458
INST_NOP = 0b1_00_1010_111 << 22

# Unused bits by given instruction type
# These bits are ignored by SPECT Instruction Decoder
# Fault here will have no effect
# Bits at the upper edge are not included, because the double-bitflip will take effect
INST_UNUSED_BITS = {
    0b00 : [16,17,18,19,20],    # J
    0b01 : [],                  # I
    0b10 : [],                  # M
    0b11 : [0,1,2,3,4,5]        # R
}

class SpectFault:

    def __init__(self, inst_addr: int, inst_exec_cnt: int, fault_data: int, description: str = ""):
        self.inst_addr      = inst_addr
        self.inst_exec_cnt  = inst_exec_cnt
        self.fault_data     = fault_data
        self.description    = description

    @staticmethod
    def load(fault_str: str):
        f_split = fault_str.split()
        return SpectFault(
            inst_addr      = int(f_split[0], 16),
            inst_exec_cnt  = int(f_split[1], 10),
            fault_data     = int(f_split[2], 16),
            description    = " ".join(f_split[3:])
        )

    def __str__(self) -> str:
        s  = f"0x{self.inst_addr:04x} "
        s += f"{self.inst_exec_cnt} "
        s += f"0x{self.fault_data:08x} "
        s += self.description
        return s

    def __repr__(self):
        return str(self)

    def __eq__(self, other) -> bool:
        if not isinstance(other, SpectFault):
            return NotImplemented

        return (
            (self.inst_addr == other.inst_addr) and
            (self.inst_exec_cnt == other.inst_exec_cnt) and
            (self.fault_data == other.fault_data)
        )

    def __gt__(self, other):
        if not isinstance(other, SpectFault):
            return NotImplemented

        if self.inst_addr != other.inst_addr:
            return self.inst_addr > other.inst_addr
        elif self.inst_exec_cnt != other.inst_exec_cnt:
            return self.inst_exec_cnt > other.inst_exec_cnt
        elif self.fault_data != other.fault_data:
            self.fault_data > other.fault_data
        return False

    def __lt__(self, other):
        if not isinstance(other, SpectFault):
            return NotImplemented

        if self.inst_addr != other.inst_addr:
            return self.inst_addr < other.inst_addr
        elif self.inst_exec_cnt != other.inst_exec_cnt:
            return self.inst_exec_cnt < other.inst_exec_cnt
        elif self.fault_data != other.fault_data:
            self.fault_data < other.fault_data
        return False

    def __hash__(self) -> int:
        # Hash a tuple of the same attributes used in __eq__
        return hash((self.inst_addr, self.inst_exec_cnt, self.fault_data))

    def dump(self, fault_file: str):
        with open(fault_file, 'w') as f:
            f.write(str(self)+'\n')

def generate_skip_faults(pd_inst) -> set:
    f_list = []

    for _, addr, exec_cnt, code, name in pd_inst.itertuples():
        faults_idxs = np.linspace(1, exec_cnt, min(exec_cnt, 5), dtype=int)
        f_list += [
            SpectFault(addr, fidx, INST_NOP, f"skip_{addr:04x}_{fidx}")
            for fidx in faults_idxs
        ]

    return set(f_list)

def generate_bitflip_faults(pd_inst) -> set:
    f_list = []
    for _, addr, exec_cnt, code, name in pd_inst.itertuples():
        for i in range(31):
            inst_type = (code>>29)&0b11
            if i in INST_UNUSED_BITS[inst_type]:
                continue

            f_code = code ^ (0b11 << i)

            faults_idxs = np.linspace(1, exec_cnt, min(exec_cnt, 5), dtype=int)
            f_list += [
                SpectFault(addr, fidx, f_code, f"bitflip_{addr:04x}_{i:02d}_{fidx}")
                for fidx in faults_idxs
            ]

    return set(f_list)
