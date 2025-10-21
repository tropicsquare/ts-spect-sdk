# -*- coding: utf-8 -*-

import abc

class MemorySpace(abc.ABC):
    base:   int
    src:    int
    depth:  int
    size:   int

    @classmethod
    def check_address(cls, addr: int) -> bool:
        mem_base = addr & 0xF000
        mem_off = (addr & 0xFFF) // 4

        return (mem_base == cls.base) and (mem_off < cls.depth)

class SpectMem:
    class DataRamIn(MemorySpace):
        base    = 0x0000
        src     = 0x0
        depth   = 512
        size    = 2048

    class DataRamOut(MemorySpace):
        base    = 0x1000
        src     = 0x1
        depth   = 128
        size    = 512

    class EmemIn(MemorySpace):
        base    = 0x4000
        src     = 0x4
        depth   = 36
        size    = 144

    class EmemOut(MemorySpace):
        base    = 0x5000
        src     = 0x5
        depth   = 32
        size    = 128
