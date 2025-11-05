# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from enum import IntEnum

def bitslice_get(x: int, slice: tuple) -> int:
    return (x >> slice[1]) & (2**(slice[0]-slice[1]+1)-1)

def bitslice_set(x: int, v: int, slice: tuple) -> int:
    v = v & (2**(slice[0]-slice[1]+1)-1)
    v = v << slice[1]
    return x | v

class SpectInstructionType(IntEnum):
    J = 0
    I = 1
    M = 2
    R = 3

class TwoWayMap:
    def __init__(self, mapping):
        self.code = mapping
        self.mnemo = {v: k for k, v in mapping.items()}

INST_MNEMO_MAP = TwoWayMap({
    # Mnemo     |  Type                   | Opcode | Func
    'ADD'       : (SpectInstructionType.R, 0b0001,   0b001),
    'SUB'       : (SpectInstructionType.R, 0b0010,   0b001),
    'CMP'       : (SpectInstructionType.R, 0b0100,   0b001),
    'AND'       : (SpectInstructionType.R, 0b0001,   0b010),
    'OR'        : (SpectInstructionType.R, 0b0010,   0b010),
    'XOR'       : (SpectInstructionType.R, 0b0100,   0b010),
    'NOT'       : (SpectInstructionType.R, 0b1000,   0b010),
    'SBIT'      : (SpectInstructionType.R, 0b0001,   0b011),
    'CBIT'      : (SpectInstructionType.R, 0b0010,   0b011),
    'LSL'       : (SpectInstructionType.R, 0b0001,   0b100),
    'LSR'       : (SpectInstructionType.R, 0b0010,   0b100),
    'ROL'       : (SpectInstructionType.R, 0b0101,   0b100),
    'ROR'       : (SpectInstructionType.R, 0b0110,   0b100),
    'ROL8'      : (SpectInstructionType.R, 0b1001,   0b100),
    'ROR8'      : (SpectInstructionType.R, 0b1010,   0b100),
    'ROLIN'     : (SpectInstructionType.R, 0b1110,   0b100),
    'RORIN'     : (SpectInstructionType.R, 0b1101,   0b100),
    'SWE'       : (SpectInstructionType.R, 0b1100,   0b100),
    'MOV'       : (SpectInstructionType.R, 0b0001,   0b101),
    'LDR'       : (SpectInstructionType.R, 0b0010,   0b101),
    'STR'       : (SpectInstructionType.R, 0b0100,   0b101),
    'CSWAP'     : (SpectInstructionType.R, 0b0011,   0b101),
    'ZSWAP'     : (SpectInstructionType.R, 0b0111,   0b101),
    'HASH'      : (SpectInstructionType.R, 0b0101,   0b111),
    'GRV'       : (SpectInstructionType.R, 0b1001,   0b111),
    'SCB'       : (SpectInstructionType.R, 0b1111,   0b111),
    'MUL25519'  : (SpectInstructionType.R, 0b0011,   0b110),
    'MUL256'    : (SpectInstructionType.R, 0b0111,   0b110),
    'ADDP'      : (SpectInstructionType.R, 0b1101,   0b110),
    'SUBP'      : (SpectInstructionType.R, 0b1110,   0b110),
    'MULP'      : (SpectInstructionType.R, 0b1111,   0b110),
    'REDP'      : (SpectInstructionType.R, 0b1100,   0b110),
    'TMAC_IT'   : (SpectInstructionType.R, 0b0001,   0b111),
    'TMAC_UP'   : (SpectInstructionType.R, 0b0100,   0b111),
    'TMAC_RD'   : (SpectInstructionType.R, 0b1000,   0b111),
    'ADDI'      : (SpectInstructionType.I, 0b0001,   0b001),
    'SUBI'      : (SpectInstructionType.I, 0b0010,   0b001),
    'CMPI'      : (SpectInstructionType.I, 0b0100,   0b001),
    'ANDI'      : (SpectInstructionType.I, 0b0001,   0b010),
    'ORI'       : (SpectInstructionType.I, 0b0010,   0b010),
    'XORI'      : (SpectInstructionType.I, 0b0100,   0b010),
    'MOVI'      : (SpectInstructionType.I, 0b0001,   0b101),
    'HASH_IT'   : (SpectInstructionType.I, 0b0110,   0b111),
    'TMAC_IS'   : (SpectInstructionType.I, 0b0010,   0b111),
    'LDK'       : (SpectInstructionType.I, 0b1010,   0b111),
    'STK'       : (SpectInstructionType.I, 0b1011,   0b111),
    'KBO'       : (SpectInstructionType.I, 0b1100,   0b111),
    'LD'        : (SpectInstructionType.M, 0b0010,   0b101),
    'ST'        : (SpectInstructionType.M, 0b0100,   0b101),
    'CALL'      : (SpectInstructionType.J, 0b0001,   0b000),
    'RET'       : (SpectInstructionType.J, 0b0010,   0b000),
    'BRZ'       : (SpectInstructionType.J, 0b0100,   0b000),
    'BRNZ'      : (SpectInstructionType.J, 0b0101,   0b000),
    'BRC'       : (SpectInstructionType.J, 0b0110,   0b000),
    'BRNC'      : (SpectInstructionType.J, 0b0111,   0b000),
    'BRE'       : (SpectInstructionType.J, 0b1110,   0b000),
    'BRNE'      : (SpectInstructionType.J, 0b1111,   0b000),
    'JMP'       : (SpectInstructionType.J, 0b1100,   0b000),
    'END'       : (SpectInstructionType.J, 0b1001,   0b111),
    'NOP'       : (SpectInstructionType.J, 0b1010,   0b111),
})


class SpectInstruction(ABC):

    TYPE    = (30, 29)
    OPCODE  = (28, 25)
    FUNC    = (24, 22)
    OP1     = (21, 17)
    OP2     = (16, 12)
    OP3     = (11, 7)
    IMD     = (11, 0)
    ADDR    = (15, 0)
    PARITY  = (31, 31)

    def __init__(self, opcode: int, func: int):
        self.opcode = opcode
        self.func = func

    @abstractmethod
    def __str__(self):
        pass

    @abstractmethod
    def __repr__(self):
        pass

    @abstractmethod
    def __eq__(self, other):
        pass

    @abstractmethod
    def assamble(self) -> int:
        pass

    @staticmethod
    def disassamble(inst_code: int):
        itype = bitslice_get(inst_code, SpectInstruction.TYPE)
        opcode = bitslice_get(inst_code, SpectInstruction.OPCODE)
        func = bitslice_get(inst_code, SpectInstruction.FUNC)

        if (itype, opcode, func) not in INST_MNEMO_MAP.mnemo.keys():
            return None

        if itype == SpectInstructionType.J:
            return SpectInstructionJ(
                opcode, func,
                bitslice_get(inst_code, SpectInstruction.ADDR),
            )
        if itype == SpectInstructionType.I:
            return SpectInstructionI(
                opcode, func,
                bitslice_get(inst_code, SpectInstruction.OP1),
                bitslice_get(inst_code, SpectInstruction.OP2),
                bitslice_get(inst_code, SpectInstruction.IMD),
            )
        if itype == SpectInstructionType.M:
            return SpectInstructionM(
                opcode, func,
                bitslice_get(inst_code, SpectInstruction.OP1),
                bitslice_get(inst_code, SpectInstruction.ADDR),
            )
        if itype == SpectInstructionType.R:
            return SpectInstructionR(
                opcode, func,
                bitslice_get(inst_code, SpectInstruction.OP1),
                bitslice_get(inst_code, SpectInstruction.OP2),
                bitslice_get(inst_code, SpectInstruction.OP3),
            )

        return None

class SpectInstructionR(SpectInstruction):

    def __init__(self, opcode: int, func: int, op1: int, op2: int, op3: int):
        super().__init__(opcode, func)
        self.type = SpectInstructionType.R
        self.op1 = op1
        self.op2 = op2
        self.op3 = op3

    def __str__(self) -> str:
        mnemo = INST_MNEMO_MAP.mnemo[(self.type, self.opcode, self.func)]
        return f"{mnemo}\tr{self.op1}, r{self.op2}, r{self.op3}"

    def __repr__(self) -> str:
        return f"0x{self.assamble():08x}\t{str(self)}"

    def __eq__(self, other):
        return self.assamble() == other.assamble()

    def assamble(self) -> int:
        inst_code = 0
        inst_code = bitslice_set(inst_code, self.type,      SpectInstruction.TYPE)
        inst_code = bitslice_set(inst_code, self.opcode,    SpectInstruction.OPCODE)
        inst_code = bitslice_set(inst_code, self.func,      SpectInstruction.FUNC)
        inst_code = bitslice_set(inst_code, self.op1,       SpectInstruction.OP1)
        inst_code = bitslice_set(inst_code, self.op2,       SpectInstruction.OP2)
        inst_code = bitslice_set(inst_code, self.op3,       SpectInstruction.OP3)

        parity = (bin(inst_code).count("1") & 1)
        inst_code = bitslice_set(inst_code, parity, SpectInstruction.PARITY)

        return inst_code

class SpectInstructionI(SpectInstruction):

    def __init__(self, opcode: int, func: int, op1: int, op2: int, imd: int):
        super().__init__(opcode, func)
        self.type = SpectInstructionType.I
        self.op1 = op1
        self.op2 = op2
        self.imd = imd

    def __str__(self) -> str:
        mnemo = INST_MNEMO_MAP.mnemo[(self.type, self.opcode, self.func)]
        return f"{mnemo}\tr{self.op1}, r{self.op2}, 0x{self.imd:03x}"

    def __repr__(self) -> str:
        return f"0x{self.assamble():08x}\t{str(self)}"

    def __eq__(self, other):
        return self.assamble() == other.assamble()

    def assamble(self) -> int:
        inst_code = 0
        inst_code = bitslice_set(inst_code, self.type,      SpectInstruction.TYPE)
        inst_code = bitslice_set(inst_code, self.opcode,    SpectInstruction.OPCODE)
        inst_code = bitslice_set(inst_code, self.func,      SpectInstruction.FUNC)
        inst_code = bitslice_set(inst_code, self.op1,       SpectInstruction.OP1)
        inst_code = bitslice_set(inst_code, self.op2,       SpectInstruction.OP2)
        inst_code = bitslice_set(inst_code, self.imd,       SpectInstruction.IMD)

        parity = (bin(inst_code).count("1") & 1)
        inst_code = bitslice_set(inst_code, parity, SpectInstruction.PARITY)

        return inst_code

class SpectInstructionJ(SpectInstruction):

    def __init__(self, opcode: int, func: int, addr: int):
        super().__init__(opcode, func)
        self.type = SpectInstructionType.J
        self.addr = addr
        self.addr_effective = (addr & 0x3FFF) // 4

    def __str__(self) -> str:
        mnemo = INST_MNEMO_MAP.mnemo[(self.type, self.opcode, self.func)]
        return f"{mnemo}\t0x{self.addr:04x} ({self.addr_effective})"

    def __repr__(self) -> str:
        return f"0x{self.assamble():08x}\t{str(self)}"

    def __eq__(self, other):
        return (
            self.type   == other.type and
            self.opcode == other.opcode and
            self.func   == other.func and
            self.addr_effective == other.addr_effective
        )

    def assamble(self) -> int:
        inst_code = 0
        inst_code = bitslice_set(inst_code, self.type,      SpectInstruction.TYPE)
        inst_code = bitslice_set(inst_code, self.opcode,    SpectInstruction.OPCODE)
        inst_code = bitslice_set(inst_code, self.func,      SpectInstruction.FUNC)
        inst_code = bitslice_set(inst_code, self.addr,      SpectInstruction.ADDR)

        parity = (bin(inst_code).count("1") & 1)
        inst_code = bitslice_set(inst_code, parity, SpectInstruction.PARITY)

        return inst_code

class SpectInstructionM(SpectInstruction):

    def __init__(self, opcode: int, func: int, op1: int, addr: int):
        super().__init__(opcode, func)
        self.type = SpectInstructionType.M
        self.op1 = op1
        self.addr = addr

    def __str__(self) -> str:
        mnemo = INST_MNEMO_MAP.mnemo[(self.type, self.opcode, self.func)]
        return f"{mnemo}\tr{self.op1}, 0x{self.addr:04x}"

    def __repr__(self) -> str:
        return f"0x{self.assamble():08x}\t{str(self)}"

    def __eq__(self, other):
        return self.assamble() == other.assamble()

    def assamble(self) -> int:
        inst_code = 0
        inst_code = bitslice_set(inst_code, self.type,      SpectInstruction.TYPE)
        inst_code = bitslice_set(inst_code, self.opcode,    SpectInstruction.OPCODE)
        inst_code = bitslice_set(inst_code, self.func,      SpectInstruction.FUNC)
        inst_code = bitslice_set(inst_code, self.op1,       SpectInstruction.OP1)
        inst_code = bitslice_set(inst_code, self.addr,      SpectInstruction.ADDR)

        parity = (bin(inst_code).count("1") & 1)
        inst_code = bitslice_set(inst_code, parity, SpectInstruction.PARITY)

        return inst_code
