# -*- coding: utf-8 -*-

class SpectInstruction:

    TYPE_POS = 29
    OPCODE_POS = 25
    FUNC_POS = 22
    OP1_POS = 17
    OP2_POS = 12
    OP3_POS = 7
    IMD_POS = 0
    ADDR_POS = 0
    PARITY_POS = 31

    def __init__(self, inst_code: int):
        self.inst_code = inst_code

class SpectInstructionR(SpectInstruction):
    TYPE = 0b11

    def __init__(self, opcode: int, func: int, op1: int, op2: int, op3: int):
        self.inst_code = 0
        self.inst_code |= SpectInstructionR.TYPE << SpectInstruction.TYPE_POS
        self.inst_code |= opcode << SpectInstruction.OPCODE_POS
        self.inst_code |= func << SpectInstruction.FUNC_POS
        self.inst_code |= op1 << SpectInstruction.OP1_POS
        self.inst_code |= op2 << SpectInstruction.OP2_POS
        self.inst_code |= op3 << SpectInstruction.OP3_POS
        self.inst_code |= (bin(self.inst_code).count("1") & 1) << SpectInstruction.PARITY_POS

class SpectInstructionI(SpectInstruction):
    TYPE = 0b01

    def __init__(self, opcode: int, func: int, op1: int, op2: int, imd: int):
        self.inst_code = 0
        self.inst_code |= SpectInstructionR.TYPE << SpectInstruction.TYPE_POS
        self.inst_code |= opcode << SpectInstruction.OPCODE_POS
        self.inst_code |= func << SpectInstruction.FUNC_POS
        self.inst_code |= op1 << SpectInstruction.OP1_POS
        self.inst_code |= op2 << SpectInstruction.OP2_POS
        self.inst_code |= imd << SpectInstruction.IMD_POS
        self.inst_code |= (bin(self.inst_code).count("1") & 1) << SpectInstruction.PARITY_POS

class SpectInstructionJ(SpectInstruction):
    TYPE = 0b00

    def __init__(self, opcode: int, func: int, op1: int, addr: int):
        self.inst_code = 0
        self.inst_code |= SpectInstructionR.TYPE << SpectInstruction.TYPE_POS
        self.inst_code |= opcode << SpectInstruction.OPCODE_POS
        self.inst_code |= func << SpectInstruction.FUNC_POS
        self.inst_code |= op1 << SpectInstruction.OP1_POS
        self.inst_code |= addr << SpectInstruction.IMD_POS
        self.inst_code |= (bin(self.inst_code).count("1") & 1) << SpectInstruction.PARITY_POS

class SpectInstructionM(SpectInstruction):
    TYPE = 0b10

    def __init__(self, opcode: int, func: int, op1: int, addr: int):
        self.inst_code = 0
        self.inst_code |= SpectInstructionR.TYPE << SpectInstruction.TYPE_POS
        self.inst_code |= opcode << SpectInstruction.OPCODE_POS
        self.inst_code |= func << SpectInstruction.FUNC_POS
        self.inst_code |= op1 << SpectInstruction.OP1_POS
        self.inst_code |= addr << SpectInstruction.IMD_POS
        self.inst_code |= (bin(self.inst_code).count("1") & 1) << SpectInstruction.PARITY_POS
