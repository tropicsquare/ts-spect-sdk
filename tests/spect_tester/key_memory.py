# -*- coding: utf-8 -*-

import re
import struct
import numpy as np
from enum import IntEnum

class KeyMem:

    FILE_COMMENT = "********************************************************************************\n"
    FILE_HEAD = "Key Memory:\n"

    class SlotStatus(IntEnum):
        EMPTY = 0
        FULL  = 1

    STATUS_MAP = {
        'EMPTY' : SlotStatus.EMPTY,
        'FULL'  : SlotStatus.FULL
    }

    def __init__(self):
        self.kmem_data   = np.empty(shape=(16, 256, 256), dtype=np.uint32)
        self.kmem_status = np.zeros(shape=(16, 256),      dtype=int)

    def load(self, file: str):
        type_slot_pattern = re.compile(r"Type: (\d+) Slot: (\d+)\n")
        status_pattern = re.compile(r"Status: (.*)\n")

        with open(file, 'r') as f:
            ktype = 0
            slot = 0
            offset = 0
            for line in f:
                if (
                    not line or
                    line == KeyMem.FILE_COMMENT or
                    line == KeyMem.FILE_HEAD
                ):
                    continue

                match = type_slot_pattern.search(line)
                if match:
                    ktype = int(match.group(1))
                    slot  = int(match.group(2))
                    offset = 0
                    continue

                match = list(status_pattern.finditer(line))
                if len(match) == 1:
                    self.kmem_status[ktype][slot] = KeyMem.STATUS_MAP[match[0].group(1)]
                    continue

                d = int(line, 16)
                self.kmem_data[ktype][slot][offset] = d
                offset += 1

    def read(self, ktype: int, slot: int, offset: int, size: int) -> bytes:
        assert size % 4 == 0
        if self.kmem_status[ktype][slot] == KeyMem.SlotStatus.EMPTY:
            return None

        data = self.kmem_data[ktype][slot][offset:offset+(size//4)]
        return b''.join(struct.pack('<I', d) for d in data)

    def write(self, key: bytes, ktype: int, slot: int, offset: int):
        assert len(key) % 4 == 0

        val = [x[0] for x in struct.iter_unpack('<I', key)]
        for i, word in enumerate(val):
            self.kmem_data[ktype][slot][offset+i] = word

        self.kmem_status[ktype][slot] = KeyMem.SlotStatus.FULL

    def slot_status(self, ktype, slot) -> SlotStatus:
        return self.kmem_status[ktype][slot]

    def dump(self, file: str):
        def __dump_slot(ktype: int, slot: int) -> list:
            lines = []
            lines.append(KeyMem.FILE_COMMENT)
            lines.append(f"Type: {ktype} Slot {slot}\n")
            lines.append(KeyMem.FILE_COMMENT)

            status = self.kmem_status[ktype][slot]
            if status == KeyMem.SlotStatus.EMPTY:
                lines.append(f"Status: EMPTY\n")
                return lines
            else:
                lines.append(f"Status: FULL\n")
                for w in self.kmem_data[ktype][slot]:
                    lines.append(f"{w:08x}\n")
                return lines

        lines = []
        lines.append(KeyMem.FILE_COMMENT)
        lines.append(KeyMem.FILE_HEAD)
        lines.append(KeyMem.FILE_COMMENT)

        for ktype in range(16):
            for slot in range(256):
                lines += __dump_slot(ktype, slot)

        with open(file, 'w') as f:
            f.writelines(lines)
