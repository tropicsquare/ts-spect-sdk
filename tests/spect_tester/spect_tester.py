# -*- coding: utf-8 -*-

import yaml
import os
import sys
import numpy as np
import random as rn
import struct
from argparse import SUPPRESS, ArgumentParser
import logging

from .spect_config import (
    TS_REPO_ROOT
)
from .helpers import (
    set_seed
)
from .spect_memory import SpectMem
from .spect_context import SpectContext
from .key_memory import KeyMem

#############################################################
#   PARSER
#############################################################
parser = ArgumentParser(description='TS SPECT tests scripts')

parser.add_argument(
    "--seed",
    type=int,
    default=SUPPRESS,
    help="Seed for randomization. Optional"
)

#############################################################
#   Test Run
#############################################################
class SpectTestRun:

    DEFAULT_FW_FILE    = os.path.join(TS_REPO_ROOT, "build", "main.hex")
    DEFAULT_S_FILE     = os.path.join(TS_REPO_ROOT, "src",   "main.s")
    DEFAULT_CONST_FILE = os.path.join(TS_REPO_ROOT, "build", "constants.hex")

    FW_PARITY       = 2
    ISA             = 2
    FIRST_ADDR      = 0x8000
    CFG_WORD_ADDR   = 0x0100

    class SpectTestRunLogger:
        def __init__(self, name: str, log_file: str, verbosity = logging.INFO):
            self.logger = logging.getLogger(name)
            self.logger.setLevel(verbosity)
            self.logger.propagate = False
            hndl = logging.FileHandler(log_file)
            formatter = logging.Formatter(
                '%(levelname)s - %(message)s'
            )
            hndl.setFormatter(formatter)
            if not self.logger.handlers:
                self.logger.addHandler(hndl)

    def __init__(self, run_name: str, test_dir: str):
        self.run_name = run_name
        self.run_dir = os.path.join(test_dir, self.run_name)
        os.system(f"mkdir {self.run_dir}")

        ############################################################################################
        #   Files
        ############################################################################################
        self.cmd_file_path   = os.path.join(self.run_dir, 'iss_cmd')
        self.cmd_file        = open(self.cmd_file_path, 'w')

        self.data_out_file   = os.path.join(self.run_dir, "data_out.hex")
        self.emem_out_file   = os.path.join(self.run_dir, "emem_out.hex")
        self.keymem_file     = os.path.join(self.run_dir, "keymem")
        self.exec_info_file  = os.path.join(self.run_dir, "exec_info")
        self.rng_file        = os.path.join(self.run_dir, "rng_file.hex")
        self.context_file    = os.path.join(self.run_dir, "context")

        self.fw_file         = SpectTestRun.DEFAULT_FW_FILE

        ############################################################################################
        #   Data
        ############################################################################################
        self.data_out = None
        self.emem_out = None
        self.keymem   = None

        self.insrc    = SpectMem.EmemIn.src
        self.outsrc   = SpectMem.EmemOut.src
        self.insize   = 0

        self.op_dict  = None

        ############################################################################################
        #   Input Files
        ############################################################################################
        self.input_keymem_file  = None
        self.input_fault_file   = None
        self.input_context_file = None

        ############################################################################################
        #   Logger
        ############################################################################################
        self.log_file = os.path.join(self.run_dir, "test_run.log")

        self.logger = logging.getLogger(self.run_name)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        hndl = logging.FileHandler(self.log_file)
        formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        hndl.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(hndl)

        ############################################################################################
        #   Status
        ############################################################################################
        self.warn_cnt = 0
        self.err_cnt = 0

        ############################################################################################
        #   Other
        ############################################################################################
        self.max_instr_cnt   = 200_000
        self.break_str = ""

    def info(self, s: str):
        self.logger.info(s)

    def warning(self, s: str):
        self.logger.warning(s)
        self.warn_cnt += 1

    def error(self, s: str):
        print(f"\033[91m{s}\033[00m")
        self.logger.error(s)
        self.err_cnt += 1

    def critical(self, s: str):
        print(f"\033[91m{s}\033[00m")
        self.logger.critical(s)
        sys.exit(1)

    def status_summary(self):
        self.info(f"Number of Warnings: {self.warn_cnt}")
        self.info(f"Number of Errors: {self.err_cnt}")

    def parse_data_out(self):
        with open(self.data_out_file, 'r') as data_out_hex:
            self.data_out = np.loadtxt(data_out_hex, dtype=int, usecols=1, converters={1: lambda s: int(s, 16)})

    def parse_emem_out(self):
        with open(self.emem_out_file, 'r') as emem_out_hex:
            self.emem_out = np.loadtxt(emem_out_hex, dtype=int,  usecols=1, converters={1: lambda s: int(s, 16)})

    def get_context(self) -> SpectContext:
        ctx = SpectContext()
        ctx.load(self.context_file)
        return ctx

    def parse_keymem(self):
        self.keymem = KeyMem(self.keymem_file)

    def cmd_start(self):
        self.cmd_file.write("start\n")

    def cmd_run(self):
        self.cmd_file.write("run\n")

    def cmd_exit(self):
        self.cmd_file.write("exit\n")

    def set_input_source(self, insrc):
        self.insrc = insrc

    def set_output_source(self, outsrc):
        self.outsrc = outsrc

    def set_input_size(self, insize):
        self.insize = insize

    def set_op(self, op_name: str):
        with open(SpectTester.OPS_CONFIG, 'r') as ca_file:
            ops_cfg = yaml.safe_load(ca_file)

        for item in ops_cfg:
            if item["name"] == op_name:
                self.op_dict = item

        if self.op_dict is None:
            self.critical(f"SPECT Op '{op_name}' was not found in {SpectTester.OPS_CONFIG}!")

        self.info(f"SPECT Op set to '{op_name}', OP_ID: {self.op_dict['id']}")

    def set_op_dict(self, op_dict: dict):
        self.op_dict = op_dict

    def write_word(self, addr: int, word: int):
        if (SpectMem.DataRamIn.check_address(addr) or
            SpectMem.EmemIn.check_address(addr)
        ):
            self.cmd_file.write(f"set mem[0x{addr:08x}] 0x{word:08x}\n")
        else:
            self.warning(f"Address {hex(addr)} is invalid input address!")

    def write_bytes(self, addr: int, data: bytes):
        self.info(f"Writing {len(data)} bytes to 0x{addr:04x}")

        padd_len = (4 - (len(data) % 4)) % 4
        data_padd = data + (b'\x00' * padd_len)
        words = np.frombuffer(data_padd, dtype=np.uint32)

        for i, w in enumerate(words):
            self.write_word(addr+(i*4), w)

    def read_word(self, addr: int) -> int:
        mem_base = addr & 0xF000
        mem_off = (addr & 0xFFF) // 4

        if SpectMem.DataRamOut.check_address(addr):
            return self.data_out[mem_off]
        elif SpectMem.EmemOut.check_address(addr):
            return self.emem_out[mem_off]
        else:
            self.warning(f"Address {hex(addr)} is invalid output address!")
            return None

    def read_bytes(self, addr: int, lenght: int) -> bytes:
        self.info(f"Reading {lenght} bytes from 0x{addr:04x}")

        mem_off = (addr & 0xFFF) // 4

        if SpectMem.DataRamOut.check_address(addr):
            data = self.data_out[mem_off:mem_off+(lenght//4)]
        elif SpectMem.EmemOut.check_address(addr):
            data = self.emem_out[mem_off:mem_off+(lenght//4)]
        else:
            self.warning(f"Address {hex(addr)} is invalid output address!")
            data = []

        return b''.join(struct.pack('<I', d) for d in data)

    def set_cfg_word(self):
        self.info(
            f"Seting CFG Word:\n"+
            f"\tOP_ID {self.op_dict['id']}\n"+
            f"\tOutSrc {self.outsrc}\n"+
            f"\tInSrc {self.insrc}\n"+
            f"\tInputSize {self.insize}"
        )
        cfg_word = self.op_dict["id"] + (self.outsrc << 8) + (self.insrc << 12) + (self.insize << 16)
        self.write_word(SpectTestRun.CFG_WORD_ADDR, cfg_word)

    def set_rng(self, rng_list: list = None):
        self.info("Seting RNG")
        if rng_list is None:
            rng_list = [rn.randint(0, 2**256 - 1) for _ in range(32)]
        with open(self.rng_file, mode='w') as rng_hex:
            for r in rng_list:
                for i in range(8):
                    rng_word = (r >> i*32) & 0xffffffff
                    rng_hex.write(f"{rng_word:08x}\n")

    def get_res_word(self):
        res_word = self.read_word(0x1100)
        status = res_word & 0xFF
        data_out_size = (res_word >> 16) & 0xFFFF
        return status, data_out_size

    def set_key(self, key: bytes, ktype: int, slot: int, offset: int):
        assert len(key) % 4 == 0
        self.info(f"Setting key: Type {ktype}, Slot {slot}, Offset {offset}")

        val = [x[0] for x in struct.iter_unpack('<I', key)]
        for i, word in enumerate(val):
            self.cmd_file.write(f"set keymem[{ktype}][{slot}][{offset+i}] 0x{word:08x}\n")

    def key_slot_status(self, ktype, slot) -> KeyMem.SlotStatus:
        return self.keymem.slot_status(ktype, slot)

    def read_key(self, ktype: int, slot: int, offset: int, size: int = 32) -> bytes:
        self.info(f"Reading key: Type {ktype}, Slot {slot}, Offset {offset}")
        return self.keymem.read(ktype, slot, offset, size)

    def break_on(self, bp: str):
        self.info(f"Seting breakpoint on {bp}")
        self.cmd_file.write(f"break {bp}\n")

    def dump_gpr_on(self, bp: str, gpr: list):
        self.cmd_file.write(f"break {bp}\n")
        for r in gpr:
            self.break_str += f"get R{r}\n"
        self.break_str += "run\n"

    def set_fw_file(self, file: str):
        self.info(f"Seting FW file to: {file}")
        self.fw_file = file

    def set_input_keymem_file(self, file: str):
        self.info(f"Seting input keymem file to: {file}")
        self.input_keymem_file = file

    def set_input_fault_file(self, file: str):
        self.info(f"Seting input fault file to: {file}")
        self.input_fault_file = file

    def set_input_context_file(self, file: str):
        self.info(f"Seting input context file to: {file}")
        self.input_context_file = file

    def run(self):
        self.set_cfg_word()
        self.cmd_run()
        if self.break_str != "":
            self.cmd_file.write(self.break_str)
        self.cmd_exit()
        self.cmd_file.close()

        cmd = SpectTester.ISS
        fw_file_type = self.fw_file.split('.')[-1]
        if fw_file_type == "hex":
            cmd += f" --instruction-mem={self.fw_file}"
            cmd += f" --parity={SpectTestRun.FW_PARITY}"
        elif fw_file_type == "s":
            cmd += f" --program={self.fw_file}"
        else:
            self.critical(f"Invalid fw file type '{fw_file_type}'!")

        cmd += f" --max-instr-cnt={self.max_instr_cnt}"
        cmd += f" --isa-version={SpectTestRun.ISA}"
        cmd += f" --first-address={hex(SpectTestRun.FIRST_ADDR)}"
        cmd += f" --const-rom={SpectTestRun.DEFAULT_CONST_FILE}"
        cmd += f" --data-ram-out={self.data_out_file}"
        cmd += f" --emem-out={self.emem_out_file}"
        cmd += f" --dump-keymem={self.keymem_file}"
        cmd += f" --dump-context={self.context_file}"
        cmd += f" --grv-hex={self.rng_file}"
        cmd += f" --dump-exec-info={self.exec_info_file}"

        if self.input_keymem_file:
            cmd += f" --load-keymem={self.input_keymem_file}"

        if self.input_fault_file:
            cmd += f" --inject-fault={self.input_fault_file}"

        if self.input_context_file:
            cmd += f" --load-context={self.input_context_file}"

        cmd += f" --shell --cmd-file={self.cmd_file_path}"
        cmd += f" > {self.run_dir}/iss.log"

        print(f"\033[94mRunning {self.run_name}\033[00m")
        self.info("Running SPECT_ISS")

        if os.system(cmd):
            self.critical("SPECT_ISS Failed")
            sys.exit(2)

        self.info("SPECT_ISS finished")

        self.parse_data_out()
        self.parse_emem_out()
        self.parse_keymem()

class SpectTester:

    ISS = "spect_iss"
    OPS_CONFIG = os.path.join(TS_REPO_ROOT, "spect_ops_config.yml")

    def __init__(self, test_name: str):
        # Create test directory
        self.test_dir = f"{TS_REPO_ROOT}/tests/test_{test_name}"
        os.system(f"rm -rf {self.test_dir}")
        os.system(f"mkdir {self.test_dir}")

        # Set and store seed
        args = parser.parse_args()
        seed = set_seed(args)
        rn.seed(seed)
        print(f"Seed: {seed}")
        with open(os.path.join(self.test_dir, "seed"), 'w') as f:
            f.write(f"{seed}")

        self.test_runs = {}

    def create_test_run(self, run_name: str) -> SpectTestRun:
        self.test_runs[run_name] = (SpectTestRun(run_name, self.test_dir))
        return self.test_runs[run_name]

    def run_all(self):
        for run_name, run in self.test_runs.items():
            print(f"Running {run_name}")
            run.run()

    @staticmethod
    def print_passed():
        print("\033[92m{}\033[00m".format("PASSED"))

    @staticmethod
    def print_failed():
        print("\033[91m{}\033[00m".format("FAILED"))

    @staticmethod
    def print_warning(text: str):
        print(f"\033[93mWarning: {text}\033[00m")

    @staticmethod
    def print_test_skipped(text: str):
        print(f"\033[93mSKIPPED {text}\033[00m")
