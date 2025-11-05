
# -*- coding: utf-8 -*-

import random as rn
import numpy as np

from .spect_instruction import (
    SpectInstruction,
    SpectInstructionType,
    SpectInstructionJ,
    INST_MNEMO_MAP
)

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

    # So we are able to sort the faults
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

    # Hash a tuple of the same attributes used in __eq__
    # Enables making a set of faults -> helps removing duplicates
    def __hash__(self) -> int:
        return hash((self.inst_addr, self.inst_exec_cnt, self.fault_data))

    def dump(self, fault_file: str):
        with open(fault_file, 'w') as f:
            f.write(str(self)+'\n')

def generate_skip_faults(pd_inst) -> set:
    _, opcode, func = INST_MNEMO_MAP.code["NOP"]
    NOP = SpectInstructionJ(opcode, func, 0x0).assamble()

    f_list = []

    for _, addr, exec_cnt, code, name in pd_inst.itertuples():
        faults_idxs = np.linspace(1, exec_cnt, min(exec_cnt, 5), dtype=int)
        f_list += [
            SpectFault(addr, fidx, NOP, f"skip_{addr:04x}_{fidx}")
            for fidx in faults_idxs
        ]

    return set(f_list)

def generate_bitflip_faults(pd_inst) -> set:
    f_list = []
    for _, addr, exec_cnt, code, name in pd_inst.itertuples():
        for i in range(31):
            inst = SpectInstruction.disassamble(code)

            f_code = code ^ (0b11 << i)
            f_inst = SpectInstruction.disassamble(f_code)

            # Prune invalid or equal instructions
            if f_inst is None or f_inst == inst:
                continue

            # If it is a J instruction, fix its target to the effective address to reflect the HW
            if f_inst.type == SpectInstructionType.J:
                # If the effective address is outside instruction ram, prune
                if f_inst.addr_effective > 3071:
                    continue
                else:
                    f_inst.addr = (f_inst.addr_effective*4)+0x8000
                    f_code = f_inst.assamble()

            faults_idxs = np.linspace(1, exec_cnt, min(exec_cnt, 5), dtype=int)
            f_list += [
                SpectFault(addr, fidx, f_code, f"bitflip_{addr:04x}_{i:02d}_{fidx}")
                for fidx in faults_idxs
            ]

    return set(f_list)
