
# -*- coding: utf-8 -*-

import numpy as np
from enum import IntEnum
from abc import ABC
import functools

from .spect_instruction import (
    SpectInstruction,
    SpectInstructionJ,
    INST_MNEMO_MAP,
)

class SpectFaultResponseSeverity(IntEnum):
    OK      = 0
    LOW     = 1
    HIGH    = 2
    FATAL   = 3

class SpectFaultType(IntEnum):
    INSTRUCTION = 0
    PC          = 1
    GPR         = 2
    MEMORY      = 3

SEVERITY_COLORS = {
    SpectFaultResponseSeverity.OK       : '\033[92m', # Green
    SpectFaultResponseSeverity.LOW      : '\033[93m', # Yellow
    SpectFaultResponseSeverity.HIGH     : '\033[93m', # Yellow
    SpectFaultResponseSeverity.FATAL    : '\033[91m', # Red
}

class SpectFaultResponseCategory:
    def __init__(self, name: str, severity: SpectFaultResponseSeverity):
        self.name = name
        self.severity = severity

@functools.total_ordering
class SpectFault(ABC):

    _registry = {}

    __slots__ = ('inst_addr', 'inst_exec_cnt', 'description')

    def __init__(self, inst_addr: int, inst_exec_cnt: int, description: str = ""):
        self.inst_addr      = inst_addr
        self.inst_exec_cnt  = inst_exec_cnt
        self.description    = description

    def __init_subclass__(cls, class_id=None, **kwargs) -> None:
        super().__init_subclass__()
        if class_id is not None:
            cls._registry[class_id] = cls
            cls._type_id = class_id

    @classmethod
    def from_string(cls, fault_str: str):
        parts = fault_str.split()

        fault_type      = int(parts[0])
        inst_addr       = int(parts[1], 0)
        inst_exec_cnt   = int(parts[2], 0)
        description     = parts[-1]

        fault_specific_args = [int(x, 0) for x in parts[3:-1]]

        target_class = cls._registry.get(fault_type)

        if not target_class:
            raise ValueError(f"Unknown Fault Type: {fault_type}")

        return target_class(inst_addr, inst_exec_cnt, description, *fault_specific_args)

    def __str__(self) -> str:
        return f"{self._type_id.value} 0x{self.inst_addr:04x} {self.inst_exec_cnt}"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other) -> bool:
        if not isinstance(other, SpectFault):
            return NotImplemented
        return (
            self._type_id.value == other._type_id.value and
            self.inst_addr == other.inst_addr and
            self.inst_exec_cnt == other.inst_exec_cnt
        )

    def __lt__(self, other):
        if not isinstance(other, SpectFault):
            return NotImplemented
        if self._type_id.value == other._type_id.value:
            if self.inst_addr == other.inst_addr:
                return self.inst_exec_cnt < other.inst_exec_cnt
            return self.inst_addr < other.inst_addr
        return self._type_id.value < other._type_id.value

    # Hash a tuple of the same attributes used in __eq__
    # Enables making a set of faults -> helps removing duplicates
    def __hash__(self) -> int:
        return hash((self._type_id.value, self.inst_addr, self.inst_exec_cnt))

    def dump(self, fault_file: str):
        with open(fault_file, 'a') as f:
            f.write(str(self)+'\n')

class SpectFaultInstruction(SpectFault, class_id=SpectFaultType.INSTRUCTION):

    __slots__ = ('new_instruction',)

    def __init__(self, inst_addr: int, inst_exec_cnt: int, description: str, new_instruction: int):
        super().__init__(inst_addr, inst_exec_cnt, description)
        self.new_instruction = new_instruction

    def __str__(self) -> str:
        return f"{super().__str__()} 0x{self.new_instruction:08x} {self.description}"

    def __eq__(self, other) -> bool:
        return super().__eq__(other) and self.new_instruction == other.new_instruction

    def __hash__(self) -> int:
        return hash((
            super().__hash__(),
            self.new_instruction
        ))

class SpectFaultPC(SpectFault, class_id=SpectFaultType.PC):

    __slots__ = ('skip_cnt',)

    def __init__(self, inst_addr: int, inst_exec_cnt: int, description: str, skip_cnt: int):
        super().__init__(inst_addr, inst_exec_cnt, description)
        self.skip_cnt = skip_cnt

    def __str__(self) -> str:
        return f"{super().__str__()} {self.skip_cnt} {self.description}"

    def __eq__(self, other) -> bool:
        return super().__eq__(other) and self.skip_cnt == other.skip_cnt

    def __hash__(self) -> int:
        return hash((
            super().__hash__(),
            self.skip_cnt
        ))

class SpectFaultGPR(SpectFault, class_id=SpectFaultType.GPR):

    __slots__ = ('gpr_index', 'bitflip_pos', 'bitflip_mask', 'is_transient')

    def __init__(self, inst_addr: int, inst_exec_cnt: int, description: str, gpr_index: int, bitflip_pos: int, bitflip_mask: int, is_transient: bool):
        super().__init__(inst_addr, inst_exec_cnt, description)
        self.gpr_index = gpr_index
        self.bitflip_pos = bitflip_pos
        self.bitflip_mask = bitflip_mask
        self.is_transient = is_transient

    def __str__(self) -> str:
        return f"{super().__str__()} {self.gpr_index} {self.bitflip_pos} 0x{self.bitflip_mask:08x}  {int(self.is_transient)} {self.description}"

    def __eq__(self, other) -> bool:
        return (
            super().__eq__(other) and
            self.gpr_index == other.gpr_index and
            self.bitflip_pos == other.bitflip_pos and
            self.bitflip_mask == other.bitflip_mask and
            self.is_transient == other.is_transient
        )

    def __hash__(self) -> int:
        return hash((
            super().__hash__(),
            self.gpr_index,
            self.bitflip_pos,
            self.bitflip_mask,
            self.is_transient
        ))

class SpectFaultMemory(SpectFault, class_id=SpectFaultType.MEMORY):

    __slots__ = ('mem_address', 'bitflip_mask', 'is_transient')

    def __init__(self, inst_addr: int, inst_exec_cnt: int, description: str, mem_address: int, bitflip_mask: int, is_transient: bool):
        super().__init__(inst_addr, inst_exec_cnt, description)
        self.mem_address = mem_address
        self.bitflip_mask = bitflip_mask
        self.is_transient = is_transient

    def __str__(self) -> str:
        return f"{super().__str__()} 0x{self.mem_address:04x} 0x{self.bitflip_mask:08x} {int(self.is_transient)} {self.description}"

    def __eq__(self, other) -> bool:
        return (
            super().__eq__(other) and
            self.mem_address == other.mem_address and
            self.bitflip_mask == other.bitflip_mask and
            self.is_transient == other.is_transient
        )

    def __hash__(self) -> int:
        return hash((
            super().__hash__(),
            self.mem_address,
            self.bitflip_mask,
            self.is_transient
        ))

####################################################################################################
#   Fault Generators
####################################################################################################
def fault_generator_inst_skip(**kwargs) -> set:
    df_inst = kwargs['df_inst']

    f_list = []
    skip_cnt = kwargs['skip_cnt']

    for _, addr, exec_cnt, code, name in df_inst.itertuples():
        faults_idxs = np.linspace(1, exec_cnt, min(exec_cnt, 5), dtype=int)
        f_list += [
            SpectFaultPC(
                inst_addr       = addr,
                inst_exec_cnt   = fidx,
                skip_cnt        = skip_cnt,
                description     = f"inst_skip_{addr:04x}_{fidx}_{skip_cnt}"
            )
            for fidx in faults_idxs
        ]

    return set(f_list)

def fault_generator_inst_bitflip(pd_inst, **kwargs) -> set:
    f_list = []
    bitflips = kwargs['bitflips']
    xor_mask = int('1'*bitflips, 2)

    for _, addr, exec_cnt, code, name in pd_inst.itertuples():
        for i in range(32-bitflips+1):
            inst = SpectInstruction.disassamble(code)

            f_code = code ^ (xor_mask << i)
            f_inst = SpectInstruction.disassamble(f_code)

            # Prune invalid or equal instructions
            if f_inst is None or f_inst == inst:
                continue

            # If it is a J instruction, fix its target to the effective address to reflect the HW
            if type(f_inst) == SpectInstructionJ:
                # If the effective address is outside instruction ram, prune
                if f_inst.addr_effective > 3071:
                    continue
                else:
                    f_inst.addr = (f_inst.addr_effective*4)+0x8000
                    f_code = f_inst.assamble()

            faults_idxs = np.linspace(1, exec_cnt, min(exec_cnt, 5), dtype=int)
            f_list += [
                SpectFaultInstruction(
                    inst_addr = addr,
                    inst_exec_cnt = fidx,
                    new_instruction = f_code,
                    description = f"inst_bitflip_{addr:04x}_{i:02d}_{fidx}"
                )
                for fidx in faults_idxs
            ]

    return set(f_list)

def fault_generator_gpr_bitflip(pd_inst, **kwargs) -> set:
    raise NotImplementedError

def fault_generator_memory_bitflip(pd_inst, **kwargs) -> set:
    raise NotImplementedError

FAULT_GEN_DICT = {
    "inst_skip"         : fault_generator_inst_skip,
    "inst_bitflip"      : fault_generator_inst_bitflip,
    "gpr_bitflip"       : fault_generator_gpr_bitflip,
    "memory_bitflip"    : fault_generator_memory_bitflip,
}
