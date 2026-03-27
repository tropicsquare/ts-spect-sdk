# -*- coding: utf-8 -*-

__author__ = "Vit Masek"
__copyright__ = "Tropic Square s.r.o."
__license___ = "See LICENSE file"
__maintainer__ = "Vit Masek"

from abc import ABC, abstractmethod
from enum import IntEnum
import ctypes
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

INST_INFO = {
    "ADD"       : {'OPERAND_MASK': 0b111, '32BIT': True,  'R31_DEPEND' : False  },
    "SUB"       : {'OPERAND_MASK': 0b111, '32BIT': True,  'R31_DEPEND' : False  },
    "CMP"       : {'OPERAND_MASK': 0b011, '32BIT': True,  'R31_DEPEND' : False  },
    "AND"       : {'OPERAND_MASK': 0b111, '32BIT': False, 'R31_DEPEND' : False  },
    "OR"        : {'OPERAND_MASK': 0b111, '32BIT': False, 'R31_DEPEND' : False  },
    "XOR"       : {'OPERAND_MASK': 0b111, '32BIT': False, 'R31_DEPEND' : False  },
    "NOT"       : {'OPERAND_MASK': 0b110, '32BIT': False, 'R31_DEPEND' : False  },
    "SBIT"      : {'OPERAND_MASK': 0b111, '32BIT': False, 'R31_DEPEND' : False  },
    "CBIT"      : {'OPERAND_MASK': 0b111, '32BIT': False, 'R31_DEPEND' : False  },
    "LSL"       : {'OPERAND_MASK': 0b110, '32BIT': False, 'R31_DEPEND' : False  },
    "LSR"       : {'OPERAND_MASK': 0b110, '32BIT': False, 'R31_DEPEND' : False  },
    "ROL"       : {'OPERAND_MASK': 0b110, '32BIT': False, 'R31_DEPEND' : False  },
    "ROR"       : {'OPERAND_MASK': 0b110, '32BIT': False, 'R31_DEPEND' : False  },
    "ROL8"      : {'OPERAND_MASK': 0b110, '32BIT': False, 'R31_DEPEND' : False  },
    "ROR8"      : {'OPERAND_MASK': 0b110, '32BIT': False, 'R31_DEPEND' : False  },
    "ROLIN"     : {'OPERAND_MASK': 0b111, '32BIT': False, 'R31_DEPEND' : False  },
    "RORIN"     : {'OPERAND_MASK': 0b111, '32BIT': False, 'R31_DEPEND' : False  },
    "SWE"       : {'OPERAND_MASK': 0b110, '32BIT': False, 'R31_DEPEND' : False  },
    "MOV"       : {'OPERAND_MASK': 0b110, '32BIT': False, 'R31_DEPEND' : False  },
    "LDR"       : {'OPERAND_MASK': 0b110, '32BIT': True,  'R31_DEPEND' : False  },
    "STR"       : {'OPERAND_MASK': 0b110, '32BIT': True,  'R31_DEPEND' : False  },
    "CSWAP"     : {'OPERAND_MASK': 0b110, '32BIT': False, 'R31_DEPEND' : False  },
    "ZSWAP"     : {'OPERAND_MASK': 0b110, '32BIT': False, 'R31_DEPEND' : False  },
    "HASH"      : {'OPERAND_MASK': 0b110, '32BIT': False, 'R31_DEPEND' : False  },
    "GRV"       : {'OPERAND_MASK': 0b100, '32BIT': False, 'R31_DEPEND' : False  },
    "SCB"       : {'OPERAND_MASK': 0b111, '32BIT': False, 'R31_DEPEND' : True   },
    "MUL25519"  : {'OPERAND_MASK': 0b111, '32BIT': False, 'R31_DEPEND' : False  },
    "MUL256"    : {'OPERAND_MASK': 0b111, '32BIT': False, 'R31_DEPEND' : False  },
    "ADDP"      : {'OPERAND_MASK': 0b111, '32BIT': False, 'R31_DEPEND' : True   },
    "SUBP"      : {'OPERAND_MASK': 0b111, '32BIT': False, 'R31_DEPEND' : True   },
    "MULP"      : {'OPERAND_MASK': 0b111, '32BIT': False, 'R31_DEPEND' : True   },
    "REDP"      : {'OPERAND_MASK': 0b111, '32BIT': False, 'R31_DEPEND' : True   },
    "TMAC_IT"   : {'OPERAND_MASK': 0b010, '32BIT': False, 'R31_DEPEND' : False  },
    "TMAC_UP"   : {'OPERAND_MASK': 0b010, '32BIT': False, 'R31_DEPEND' : False  },
    "TMAC_RD"   : {'OPERAND_MASK': 0b100, '32BIT': False, 'R31_DEPEND' : False  },
    "ADDI"      : {'OPERAND_MASK': 0b111, '32BIT': True,  'R31_DEPEND' : False  },
    "SUBI"      : {'OPERAND_MASK': 0b111, '32BIT': True,  'R31_DEPEND' : False  },
    "CMPI"      : {'OPERAND_MASK': 0b011, '32BIT': True,  'R31_DEPEND' : False  },
    "ANDI"      : {'OPERAND_MASK': 0b111, '32BIT': True,  'R31_DEPEND' : False  },
    "ORI"       : {'OPERAND_MASK': 0b111, '32BIT': True,  'R31_DEPEND' : False  },
    "XORI"      : {'OPERAND_MASK': 0b111, '32BIT': True,  'R31_DEPEND' : False  },
    "MOVI"      : {'OPERAND_MASK': 0b101, '32BIT': False, 'R31_DEPEND' : False  },
    "HASH_IT"   : {'OPERAND_MASK': 0b000, '32BIT': False, 'R31_DEPEND' : False  },
    "TMAC_IS"   : {'OPERAND_MASK': 0b011, '32BIT': False, 'R31_DEPEND' : False  },
    "LDK"       : {'OPERAND_MASK': 0b111, '32BIT': False, 'R31_DEPEND' : False  },
    "STK"       : {'OPERAND_MASK': 0b111, '32BIT': False, 'R31_DEPEND' : False  },
    "KBO"       : {'OPERAND_MASK': 0b011, '32BIT': False, 'R31_DEPEND' : False  },
    "LD"        : {'OPERAND_MASK': 0b110, '32BIT': False, 'R31_DEPEND' : False  },
    "ST"        : {'OPERAND_MASK': 0b110, '32BIT': False, 'R31_DEPEND' : False  },
    "CALL"      : {'OPERAND_MASK': 0b100, '32BIT': False, 'R31_DEPEND' : False  },
    "RET"       : {'OPERAND_MASK': 0b000, '32BIT': False, 'R31_DEPEND' : False  },
    "BRZ"       : {'OPERAND_MASK': 0b100, '32BIT': False, 'R31_DEPEND' : False  },
    "BRNZ"      : {'OPERAND_MASK': 0b100, '32BIT': False, 'R31_DEPEND' : False  },
    "BRC"       : {'OPERAND_MASK': 0b100, '32BIT': False, 'R31_DEPEND' : False  },
    "BRNC"      : {'OPERAND_MASK': 0b100, '32BIT': False, 'R31_DEPEND' : False  },
    "BRE"       : {'OPERAND_MASK': 0b100, '32BIT': False, 'R31_DEPEND' : False  },
    "BRNE"      : {'OPERAND_MASK': 0b100, '32BIT': False, 'R31_DEPEND' : False  },
    "JMP"       : {'OPERAND_MASK': 0b100, '32BIT': False, 'R31_DEPEND' : False  },
    "END"       : {'OPERAND_MASK': 0b000, '32BIT': False, 'R31_DEPEND' : False  },
    "NOP"       : {'OPERAND_MASK': 0b000, '32BIT': False, 'R31_DEPEND' : False  },
}

def define_layout(layout):
    class Bits(ctypes.LittleEndianStructure):
        _fields_ = layout

    class Reg(ctypes.Union):
        _fields_ = [
            ("bits", Bits),
            ("val", ctypes.c_uint32)
        ]
        _anonymous_ = ("bits",)

        def __init__(self, x: int):
            self.val = ctypes.c_uint32(x & 0xFFFF_FFFF)

        def __int__(self) -> int:
            return int(self.val)

    return Reg

class SpectInstruction(ABC):

    _registry = {}

    Layout = define_layout([
        ("specific", ctypes.c_uint32, 22),  # [21: 0]
        ("func",     ctypes.c_uint32, 3),   # [24:22]
        ("opcode",   ctypes.c_uint32, 4),   # [28:25]
        ("type",     ctypes.c_uint32, 2),   # [30:29]
        ("parity",   ctypes.c_uint32, 1),   # [31:31]
    ])

    def __init__(self, cls_layout, itype: int, opcode: int, func: int):
        self.code = cls_layout(0)
        self.code.type   = itype
        self.code.opcode = opcode
        self.code.func   = func
        self.name = INST_MNEMO_MAP.mnemo[(itype, opcode, func)]

    def __init_subclass__(cls, class_id=None, **kwargs) -> None:
        super().__init_subclass__()
        if class_id is not None:
            cls._registry[class_id] = cls
            cls._type_id = class_id

    @abstractmethod
    def __str__(self) -> str:
        ...

    def __repr__(self) -> str:
        return f"0x{self.assemble():08x}\t{str(self)}"

    def __eq__(self, other) -> bool:
        return self.code.val == other.code.val

    @classmethod
    def disassemble(cls, inst_code: int):
        code = SpectInstruction.Layout(inst_code)

        if (code.type, code.opcode, code.func) not in INST_MNEMO_MAP.mnemo:
            return None

        target_class = cls._registry.get(code.type)
        assert target_class is not None # Should not happen

        return target_class.disassemble(inst_code)

    def assemble(self) -> int:
        return int(self.code.val)

    def update_parity(self):
        self.code.parity = 0
        self.code.parity = (bin(int(self.code)).count("1") & 1)

class SpectInstructionR(SpectInstruction, class_id=SpectInstructionType.R):

    Layout = define_layout([
        ("empty",    ctypes.c_uint32, 7),   # [ 6: 0]
        ("op3",      ctypes.c_uint32, 5),   # [11: 7]
        ("op2",      ctypes.c_uint32, 5),   # [16:12]
        ("op1",      ctypes.c_uint32, 5),   # [21:17]
        ("func",     ctypes.c_uint32, 3),   # [24:22]
        ("opcode",   ctypes.c_uint32, 4),   # [28:25]
        ("type",     ctypes.c_uint32, 2),   # [30:29]
        ("parity",   ctypes.c_uint32, 1),   # [31:31]
    ])

    def __init__(self, opcode: int, func: int, op1: int, op2: int, op3: int):
        super().__init__(self.Layout, SpectInstructionType.R, opcode, func)
        self.code.op1 = op1
        self.code.op2 = op2
        self.code.op3 = op3
        self.update_parity()

    def __str__(self) -> str:
        return f"{self.name}\tr{self.code.op1}, r{self.code.op2}, r{self.code.op3}"

    @classmethod
    def disassemble(cls, inst_code: int):
        code = SpectInstructionR.Layout(inst_code)
        return SpectInstructionR(
            opcode  = code.opcode,
            func    = code.func,
            op1     = code.op1,
            op2     = code.op2,
            op3     = code.op3
        )

class SpectInstructionI(SpectInstruction, class_id=SpectInstructionType.I):

    Layout = define_layout([
        ("imd",      ctypes.c_uint32, 12),  # [11: 0]
        ("op2",      ctypes.c_uint32, 5),   # [16:12]
        ("op1",      ctypes.c_uint32, 5),   # [21:17]
        ("func",     ctypes.c_uint32, 3),   # [24:22]
        ("opcode",   ctypes.c_uint32, 4),   # [28:25]
        ("type",     ctypes.c_uint32, 2),   # [30:29]
        ("parity",   ctypes.c_uint32, 1),   # [31:31]
    ])

    def __init__(self, opcode: int, func: int, op1: int, op2: int, imd: int):
        super().__init__(self.Layout, SpectInstructionType.I, opcode, func)
        self.code.op1 = op1
        self.code.op2 = op2
        self.code.imd = imd
        self.update_parity()

    def __str__(self) -> str:
        return f"{self.name}\tr{self.code.op1}, r{self.code.op2}, 0x{self.code.imd:03x}"

    @classmethod
    def disassemble(cls, inst_code: int):
        code = SpectInstructionI.Layout(inst_code)
        return SpectInstructionI(
            opcode  = code.opcode,
            func    = code.func,
            op1     = code.op1,
            op2     = code.op2,
            imd     = code.imd
        )

class SpectInstructionJ(SpectInstruction, class_id=SpectInstructionType.J):

    Layout = define_layout([
        ("addr",     ctypes.c_uint32, 16),  # [15: 0]
        ("empty",    ctypes.c_uint32, 6),   # [21:15]
        ("func",     ctypes.c_uint32, 3),   # [24:22]
        ("opcode",   ctypes.c_uint32, 4),   # [28:25]
        ("type",     ctypes.c_uint32, 2),   # [30:29]
        ("parity",   ctypes.c_uint32, 1),   # [31:31]
    ])

    def __init__(self, opcode: int, func: int, addr: int):
        super().__init__(self.Layout, SpectInstructionType.J, opcode, func)
        self.code.addr = addr
        self.code.parity = (bin(int(self.code)).count("1") & 1)
        self.update_parity()
        self.addr_effective = (addr & 0x3FFF) // 4

    def __str__(self) -> str:
        return f"{self.name}\t0x{self.code.addr:04x} ({self.addr_effective})"

    # We need to compare effective target addresses
    def __eq__(self, other):
        return (
            self.name           == other.name and
            self.addr_effective == other.addr_effective
        )

    @classmethod
    def disassemble(cls, inst_code: int):
        code = SpectInstructionJ.Layout(inst_code)
        return SpectInstructionJ(
            opcode  = code.opcode,
            func    = code.func,
            addr    = code.addr,
        )

class SpectInstructionM(SpectInstruction, class_id=SpectInstructionType.M):

    Layout = define_layout([
        ("addr",     ctypes.c_uint32, 16),  # [15: 0]
        ("empty",    ctypes.c_uint32, 1),   # [16:15]
        ("op1",      ctypes.c_uint32, 5),   # [21:17]
        ("func",     ctypes.c_uint32, 3),   # [24:22]
        ("opcode",   ctypes.c_uint32, 4),   # [28:25]
        ("type",     ctypes.c_uint32, 2),   # [30:29]
        ("parity",   ctypes.c_uint32, 1),   # [31:31]
    ])

    def __init__(self, opcode: int, func: int, op1: int, addr: int):
        super().__init__(self.Layout, SpectInstructionType.M, opcode, func)
        self.code.op1 = op1
        self.code.addr = addr
        self.update_parity()

    def __str__(self) -> str:
        return f"{self.name}\tr{self.code.op1}, 0x{self.code.addr:04x}"

    @classmethod
    def disassemble(cls, inst_code: int):
        code = SpectInstructionM.Layout(inst_code)
        return SpectInstructionM(
            opcode  = code.opcode,
            func    = code.func,
            op1     = code.op1,
            addr    = code.addr,
        )
