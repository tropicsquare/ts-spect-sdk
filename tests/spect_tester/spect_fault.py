# -*- coding: utf-8 -*-

import pandas as pd
import random as rn

#INST_NOP = 0x9513_6458
INST_NOP = 0b1_00_1010_111 << 22

class SpectFault:

    def __init__(self, inst_addr: int, inst_exec_cnt: int, fault_data: int, description: str = ""):
        self.inst_addr      = inst_addr
        self.inst_exec_cnt  = inst_exec_cnt
        self.fault_data     = fault_data
        self.description    = description

    def __str__(self) -> str:
        s  = f"0x{self.inst_addr:08x} "
        s += f"{self.inst_exec_cnt} "
        s += f"0x{self.fault_data:08x} "
        s += self.description
        return s

    def __repr__(self):
        return str(self)

    def dump(self, fault_file: str):
        with open(fault_file, 'w') as f:
            f.write(str(self)+'\n')

def generate_skip_faults(pd_inst):
    f_list = []

    for _, addr, exec_cnt, code, name in pd_inst.itertuples():
        f_list.append(SpectFault(addr, 1, INST_NOP, f"skip_{addr:04x}_1"))
        if exec_cnt > 1:
            f_list.append(SpectFault(addr, exec_cnt, INST_NOP, f"skip_{addr:04x}_{exec_cnt}"))
        if exec_cnt > 2:
            skip = rn.randint(2, exec_cnt-1)
            f_list.append(SpectFault(addr, rn.randint(2, exec_cnt-1), INST_NOP, f"skip_{addr:04x}_{skip}"))

    return f_list
