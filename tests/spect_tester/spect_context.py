# -*- coding: utf-8 -*-

from binascii import unhexlify

from .spect_config import (
    RAR_STACK_DEPTH,
)
from .spect_memory import SpectMem

class SpectContext:
    def __init__(
        self,
        gpr:            list  = None,
        sha:            bytes = None,
        tmac:           bytes = None,
        rar_stack:      list  = None,
        rar_pointer:    int   = None,
        flags:          dict  = None,
        data_in:        list  = None,
        data_out:       list  = None
    ):
        self.gpr            = gpr
        self.sha            = sha
        self.tmac           = tmac
        self.rar_stack      = rar_stack
        self.rar_pointer    = rar_pointer
        self.flags          = flags
        self.data_in        = data_in
        self.data_out       = data_out

    def load(self, context_file: str):

        self.gpr            = []
        self.sha            = b''
        self.tmac           = b''
        self.rar_stack      = []
        self.rar_pointer    = 0
        self.flags          = {"Z" : 0, "C" : 0, "E" : 0}
        self.data_in        = []
        self.data_out       = []

        with open(context_file, 'r') as ctx:
            data = ctx.read().split('\n')
            for i in range(len(data)):
                line = data[i]
                if not line:
                    continue
                if line[0] == "*":
                    continue

                if line == "GPR registers:":
                    i += 1  # skip next "**..**" line
                    for _ in range(32):
                        i += 1
                        line = data[i]
                        r = int.from_bytes(unhexlify(line), 'big')
                        self.gpr.append(r)

                if line == "SHA 512 context:":
                    i += 1  # skip next "**..**" line
                    for _ in range(8):
                        i += 1
                        line = data[i]
                        self.sha += unhexlify(line)
                    continue

                if line[:4] == "TMAC":
                    i += 1 # skip next "**..**" line
                    for _ in range(5):
                        i += 1
                        line = data[i]
                        self.tmac += unhexlify(line)
                    i += 3  # skip rate, byteIOIndex and squeezing
                    continue

                if line == "RAR stack:":
                    i += 1  # skip next "**..**" line
                    for _ in range(RAR_STACK_DEPTH):
                        i +=1
                        line = data[i]
                        val = int.from_bytes(unhexlify(line), 'big')
                        self.rar_stack.append(val)
                    continue

                if line == "RAR stack pointer:":
                    i += 2
                    line = data[i]
                    self.rar_pointer = int.from_bytes(unhexlify(line), 'big')
                    continue

                if line == "FLAGS (Z, C, E):":
                    i += 2
                    line = data[i]
                    self.flags["Z"] = int(line)
                    i += 1
                    line = data[i]
                    self.flags["C"] = int(line)
                    i += 1
                    line = data[i]
                    self.flags["E"] = int(line)
                    continue

                if line == "Data RAM In:":
                    i += 1
                    for _ in range(SpectMem.DataRamIn.depth):
                        i += 1
                        line = data[i]
                        val = int.from_bytes(unhexlify(line), 'big')
                        self.data_in.append(val)

                if line == "Data RAM Out:":
                    i += 1
                    for _ in range(SpectMem.DataRamOut.depth):
                        i += 1
                        line = data[i]
                        val = int.from_bytes(unhexlify(line), 'big')
                        self.data_out.append(val)

    def dump(self, context_file: str):
        def __coment_bar(s: str):
            lines = []
            lines.append("********************************************************************************\n")
            lines.append(s+'\n')
            lines.append("********************************************************************************\n")
            return lines

        lines = []

        # GPR
        lines += __coment_bar("GPR registers:")
        for gpr in self.gpr:
            lines.append(f"{gpr:064x}\n")

        # SHA
        lines += __coment_bar("SHA 512 context:")
        for i in range(8):
            lines.append(f"{self.sha[(i*8) : (i*8)+8].hex()}\n")

        # TMAC
        lines += __coment_bar("TMAC context: (state (5 lines), rate, byteIOIndex, squeezing)")
        for i in range(5):
            lines.append(f"{self.tmac[(i*10) : (i*10)+10].hex()}\n")
        lines.append("0\n")
        lines.append("0\n")
        lines.append("0\n")

        # RAR Stack
        lines += __coment_bar("RAR stack:")
        for r in self.rar_stack:
            lines.append(f"{r:04x}\n")

        # RAR Stack Pointer
        lines += __coment_bar("RAR stack pointer:")
        lines.append(f"{self.rar_pointer:04x}\n")

        # Flags
        lines += __coment_bar("FLAGS (Z, C, E):")
        for flag, val in self.flags.items():
            lines.append(f"{val}\n")

        # Data RAM In
        lines += __coment_bar("Data RAM In:")
        for w in self.data_in:
            lines.append(f"{w:08x}\n")

        # Data RAM Out
        lines += __coment_bar("Data RAM Out:")
        for w in self.data_out:
            lines.append(f"{w:08x}\n")

        with open(context_file, 'w') as ctx:
            ctx.writelines(lines)
