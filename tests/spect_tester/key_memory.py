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

    def __init__(self, file: str):
        self.kmem_data   = np.empty(shape=(16, 256, 256), dtype=np.uint32)
        self.kmem_status = np.empty(shape=(16, 256),      dtype=int)

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

    def slot_status(self, ktype, slot) -> SlotStatus:
        return self.kmem_status[ktype][slot]
