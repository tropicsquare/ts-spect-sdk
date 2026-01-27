# -*- coding: utf-8 -*-

import yaml
import os
import subprocess
import signal
import sys
import numpy as np
import random as rn
import struct
import logging
import shutil

from enum import IntEnum
from datetime import datetime
from typing import (
    Dict,
    List,
    Type,
    Optional,
)
from argparse import (
    SUPPRESS,
    ArgumentParser,
)
from .spect_config import (
    TS_REPO_ROOT,
)
from .helpers import (
    set_seed,
)
from .spect_memory import SpectMem
from .spect_context import SpectContext
from .key_memory import KeyMem
from .spect_default_fw import (
    SpectFw,
    RELEASE_TAG,
    RELEASE_DIR,
    get_release_version,
)

#############################################################
#   ISS Verbosity Levels
#############################################################
class IssVerbosity(IntEnum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3

#############################################################
#   TIMESTAMP
#############################################################
def time_stamp():
    return datetime.now().strftime('%Y-%m-%dT%H-%M-%SZ')

#############################################################
#   PARSER
#############################################################
parser = ArgumentParser(description='TS SPECT Tester')

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
    FW_PARITY       = 2
    ISA             = 2
    FIRST_ADDR      = 0x8000
    CFG_WORD_ADDR   = 0x0100

    def __init__(
        self,
        test_name: str,
        run_name: str,
        test_dir: str,
        spect_fw: Type[SpectFw],
        iss_verbosity: IssVerbosity = IssVerbosity.HIGH
    ):
        self.run_name = run_name
        self.run_dir = os.path.join(test_dir, self.run_name)
        os.system(f"mkdir {self.run_dir}")

        ############################################################################################
        #   Logger
        ############################################################################################
        self.log_file = os.path.join(self.run_dir, "test_run.log")

        self.logger = logging.getLogger(f"{test_name}_{run_name}")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        hndl = logging.FileHandler(self.log_file)
        formatter = logging.Formatter(
            fmt='%(asctime)s,%(msecs)03d [%(levelname)s] - %(message)s',
            datefmt='%H:%M:%S'
        )
        hndl.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(hndl)

        self.errors: List[str] = []
        self.warnings: List[str] = []

        ############################################################################################
        #   Files
        ############################################################################################
        self.cmd_file_path   = os.path.join(self.run_dir, 'iss_cmd')
        self.cmd_file        = open(self.cmd_file_path, 'w')

        self.data_out_file   = os.path.join(self.run_dir, "data_out.hex32")
        self.emem_out_file   = os.path.join(self.run_dir, "emem_out.hex32")
        self.keymem_file     = os.path.join(self.run_dir, "keymem")
        self.exec_info_file  = os.path.join(self.run_dir, "exec_info.csv")
        self.mem_access_file = os.path.join(self.run_dir, "mem_access.csv")
        self.rng_file        = os.path.join(self.run_dir, "rng_file.hex32")
        self.context_file    = os.path.join(self.run_dir, "context")

        self.iss_log_file    = os.path.join(self.run_dir, "iss.log")

        self.spect_fw = spect_fw
        if RELEASE_TAG in os.environ.keys():
            self.fw_file, self.constfile = self.spect_fw.get_release_files()
        else:
            if not spect_fw.check_exists():
                self.critical(f"Default FW Sources of {spect_fw.__name__} does not exist")
            self.fw_file         = spect_fw.hex_file
            self.constfile       = spect_fw.const_rom_file

        ############################################################################################
        #   Data
        ############################################################################################
        self.data_out = None
        self.emem_out = None
        self.keymem   = None

        self.insrc    = SpectMem.EmemIn.src
        self.outsrc   = SpectMem.EmemOut.src
        self.insize   = 0

        self.op_dict  = {}

        ############################################################################################
        #   Input Files
        ############################################################################################
        self.input_keymem_file  = None
        self.input_fault_file   = None
        self.input_context_file = None

        ############################################################################################
        #   Status
        ############################################################################################
        self.warn_cnt = 0
        self.err_cnt = 0

        self.iss_fatal_lines = []
        self.iss_fatals = 0

        ############################################################################################
        #   Other
        ############################################################################################
        self.max_instr_cnt   = 200_000
        self.break_str = ""
        self.iss_verbosity = iss_verbosity
        self.dump_keymem = True

    def destroy_logger(self):
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)

    def info(self, s: str, printout: bool = False):
        if self.iss_verbosity > IssVerbosity.NONE:
            self.logger.info(s)
            if printout:
                print(f"INFO: {s}")

    def warning(self, s: str, printout: bool = False):
        self.logger.warning(s)
        self.warnings.append(s)
        self.warn_cnt += 1
        if printout:
            print(f"\033[93mWarning: {s}\033[00m")

    def error(self, s: str, printout: bool = True):
        self.logger.error(s)
        self.errors.append(s)
        self.err_cnt += 1
        if printout:
            print(f"\033[91mError: {s}\033[00m")

    def critical(self, s: str, printout: bool = True):
        self.logger.critical(s)
        if printout:
            print(f"\033[91mCritical: {s}\033[00m")
        sys.exit(1)

    def print_warnings(self):
        for s in self.warnings:
            print(f"\033[93mWarning: {s}\033[00m")

    def print_errors(self):
        for s in self.warnings:
            print(f"\033[91mError: {s}\033[00m")

    def status_summary(self):
        self.info(f"Number of Warnings: {self.warn_cnt}")
        self.info(f"Number of Errors: {self.err_cnt}")

    def parse_data_out(self):
        with open(self.data_out_file, 'r') as data_out_hex:
            self.data_out = np.loadtxt(data_out_hex, dtype=int, usecols=1, converters={1: lambda s: int(s, 16)})

    def parse_emem_out(self):
        with open(self.emem_out_file, 'r') as emem_out_hex:
            self.emem_out = np.loadtxt(emem_out_hex, dtype=int,  usecols=1, converters={1: lambda s: int(s, 16)})

    def parse_keymem(self):
        self.keymem = KeyMem()
        self.keymem.load(self.keymem_file)

    def get_context(self) -> SpectContext:
        ctx = SpectContext()
        ctx.load(self.context_file)
        return ctx

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

        self.info(f"SPECT Op set to '{op_name}', OP_ID: 0x{self.op_dict['id']:02x}")

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

    def read_word(self, addr: int) -> Optional[int]:
        mem_off = (addr & 0xFFF) // 4

        if self.data_out is not None and SpectMem.DataRamOut.check_address(addr):
            return self.data_out[mem_off]
        elif self.emem_out is not None and SpectMem.EmemOut.check_address(addr):
            return self.emem_out[mem_off]
        else:
            self.warning(f"Failed to read address {hex(addr)}!")
            return None

    def read_bytes(self, addr: int, lenght: int) -> bytes:
        self.info(f"Reading {lenght} bytes from 0x{addr:04x}")

        mem_off = (addr & 0xFFF) // 4

        if self.data_out is not None and SpectMem.DataRamOut.check_address(addr):
            data = self.data_out[mem_off:mem_off+(lenght//4)]
        elif self.emem_out is not None and SpectMem.EmemOut.check_address(addr):
            data = self.emem_out[mem_off:mem_off+(lenght//4)]
        else:
            self.warning(f"Failed to read address {hex(addr)}!")
            data = []

        return b''.join(struct.pack('<I', d) for d in data)

    def set_cfg_word(self):
        self.info(
            f"Seting CFG Word:\n"+
            f"\tOP_ID:    0x{self.op_dict['id']:02x}\n"+
            f"\tOutSrc:   0x{self.outsrc:01x}\n"+
            f"\tInSrc:    0x{self.insrc:01x}\n"+
            f"\tInputSize {self.insize}"
        )
        cfg_word = self.op_dict["id"] + (self.outsrc << 8) + (self.insrc << 12) + (self.insize << 16)
        self.write_word(SpectTestRun.CFG_WORD_ADDR, cfg_word)

    def set_rng(self, rng_list: Optional[list] = None):
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
        assert res_word is not None

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
        assert self.keymem is not None
        return self.keymem.slot_status(ktype, slot)

    def read_key(self, ktype: int, slot: int, offset: int, size: int = 32) -> Optional[bytes]:
        assert self.keymem is not None
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
        if RELEASE_TAG in os.environ.keys():
            self.info("Cannot set FW file when running Release tests")
            return
        self.info(f"Seting FW file to: {file}")
        self.fw_file = file

    def set_const_file(self, file: str):
        if RELEASE_TAG in os.environ.keys():
            self.info("Cannot set Constants file when running Release tests")
            return
        self.info(f"Seting Constants file to: {file}")
        self.constfile = file

    def set_input_keymem_file(self, file: str):
        self.info(f"Seting input keymem file to: {file}")
        if not os.path.exists(file):
            self.critical(f"File {file} does not exist!")
        self.input_keymem_file = file

    def set_input_fault_file(self, file: str):
        self.info(f"Seting input fault file to: {file}")
        if not os.path.exists(file):
            self.critical(f"File {file} does not exist!")
        self.input_fault_file = file

    def set_input_context_file(self, file: str):
        self.info(f"Seting input context file to: {file}")
        if not os.path.exists(file):
            self.critical(f"File {file} does not exist!")
        self.input_context_file = file

    def run(self, **kwargs):
        self.set_cfg_word()
        self.cmd_run()
        if self.break_str != "":
            self.cmd_file.write(self.break_str)
        self.cmd_exit()
        self.cmd_file.close()

        if not os.path.exists(self.constfile):
            self.critical(f"File {self.constfile} does not exist!")
        if not os.path.exists(self.fw_file):
            self.critical(f"File {self.fw_file} does not exist!")

        cmd = SpectTester.ISS
        fw_file_type = self.fw_file.split('.')[-1]
        if fw_file_type == "hex32":
            cmd += f" --instruction-mem={self.fw_file}"
            cmd += f" --parity={SpectTestRun.FW_PARITY}"
        elif fw_file_type == "s":
            cmd += f" --program={self.fw_file}"
        else:
            self.critical(f"Invalid fw file type '{fw_file_type}'!")

        cmd += f" --max-instr-cnt={self.max_instr_cnt}"
        cmd += f" --isa-version={SpectTestRun.ISA}"
        cmd += f" --first-address={hex(SpectTestRun.FIRST_ADDR)}"
        cmd += f" --const-rom={self.constfile}"
        cmd += f" --data-ram-out={self.data_out_file}"
        cmd += f" --emem-out={self.emem_out_file}"
        cmd += f" --dump-context={self.context_file}"
        cmd += f" --grv-hex={self.rng_file}"
        cmd += f" --dump-exec-info={self.exec_info_file}"
        cmd += f" --verbosity={self.iss_verbosity}"
        if self.dump_keymem == True:
            cmd += f" --dump-keymem={self.keymem_file}"

        if self.input_keymem_file:
            cmd += f" --load-keymem={self.input_keymem_file}"

        if self.input_fault_file:
            cmd += f" --inject-fault={self.input_fault_file}"

        if self.input_context_file:
            cmd += f" --load-context={self.input_context_file}"

        for arg, val in kwargs.items():
            cmd += f" --{arg.replace('_', '-')}={val}"

        cmd += f" --shell --cmd-file={self.cmd_file_path}"
        cmd += f" > {self.iss_log_file}"

        self.info(f"Running {self.run_name}", printout=True)
        self.info(
            "Running SPECT_ISS\n"+
            "CMD: {}".format(cmd.replace(' ', '\n\t'))
        )

        proc = None
        out, err = b"", b""
        try:
            proc = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL
            )
            out, err = proc.communicate()
        except KeyboardInterrupt:
            if proc:
                proc.send_signal(signal.SIGINT)
                proc.wait()

        if proc and proc.returncode != 0:
            self.critical("SPECT_ISS Failed")

        self.info("SPECT_ISS finished")

        with open(self.iss_log_file) as f:
            self.iss_fatal_lines = [line for line in f if "FATAL:" in line]
            self.iss_fatals = len(self.iss_fatal_lines)

        self.parse_data_out()
        self.parse_emem_out()
        if self.dump_keymem == True:
            self.parse_keymem()

class SpectTester:

    ISS = "spect_iss"
    OPS_CONFIG = os.path.join(TS_REPO_ROOT, "spect_ops_config.yml")
    TESTER_DIR = os.path.join(TS_REPO_ROOT, "tests", "test_results")

    def __init__(
        self,
        test_name: str,
        spect_fw: Type[SpectFw],
    ):
        self.test_runs: Dict[str, SpectTestRun] = {}
        self.test_name = test_name
        self.err_cnt = 0

        self.print_baner()

        ############################################################################################
        #   Create test directory
        ############################################################################################
        test_dir_name = f"test_{self.test_name}_{time_stamp()}"
        self.test_dir = os.path.join(SpectTester.TESTER_DIR, test_dir_name)
        os.system(f"rm -rf {self.test_dir}")
        os.makedirs(self.test_dir)

        ############################################################################################
        #   Logger
        ############################################################################################
        self.log_file = os.path.join(self.test_dir, "tester.log")

        self.logger = logging.getLogger(f"{self.test_name}_tester")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        hndl = logging.FileHandler(self.log_file)
        formatter = logging.Formatter(
            fmt='%(asctime)s,%(msecs)03d [%(levelname)s] - %(message)s',
            datefmt='%H:%M:%S'
        )
        hndl.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(hndl)

        self.errors = []
        self.warnings = []

        ############################################################################################
        #   Set and store seed
        ############################################################################################
        args = parser.parse_args()
        seed = set_seed(args)
        rn.seed(seed)
        self.info(f"Seed {seed}", printout=True)

        ############################################################################################
        #   Set and log FW type
        ############################################################################################
        self.spect_fw = spect_fw
        self.info(f"FW: {self.spect_fw.__name__}")

        ############################################################################################
        #   Check if Release Run
        ############################################################################################
        if RELEASE_TAG in os.environ.keys() and not os.path.exists(RELEASE_DIR):
            self.critical("Release directory does not exists!")

    def print_baner(self, width: int = 50):
        s = self.test_name
        l = len(s)
        num_spaces = (width-2-l)//2
        before = ' '*num_spaces
        after = ' '*(width-2-l-num_spaces)

        print(f"\033[94m{'*'*width}\033[00m")
        print(f"\033[94m*{before}{self.test_name}{after}*\033[00m")
        if RELEASE_TAG in os.environ.keys():
            s = get_release_version()
            assert s is not None

            l = len(s)
            num_spaces = (width-2-l)//2
            before = ' '*num_spaces
            after = ' '*(width-2-l-num_spaces)
            print(f"\033[94m*{before}{s}{after}*\033[00m")
        print(f"\033[94m{'*'*width}\033[00m")

    def info(self, s: str, printout: bool = False):
        self.logger.info(s)
        if printout:
            print(f"INFO: {s}")

    def warning(self, s: str, printout: bool = False):
        self.logger.warning(s)
        self.warnings.append(s)
        self.warn_cnt += 1
        if printout:
            print(f"\033[93mWarning: {s}\033[00m")

    def error(self, s: str, printout: bool = True):
        self.logger.error(s)
        self.errors.append(s)
        self.err_cnt += 1
        if printout:
            print(f"\033[91mError: {s}\033[00m")

    def critical(self, s: str, printout: bool = True):
        self.logger.critical(s)
        if printout:
            print(f"\033[91mCritical: {s}\033[00m")

    def create_test_run(
        self,
        run_name: str,
        spect_fw: Optional[Type[SpectFw]] = None,
        iss_verbosity: IssVerbosity = IssVerbosity.HIGH
    ) -> SpectTestRun:
        self.info(f"Creating TestRun: {run_name}")
        if spect_fw is None:
            spect_fw = self.spect_fw
        self.test_runs[run_name] = (SpectTestRun(self.test_name, run_name, self.test_dir, self.spect_fw, iss_verbosity))
        return self.test_runs[run_name]

    def get_test_run(self, run_name: str) -> SpectTestRun:
        return self.test_runs[run_name]

    def destroy_test_run(self, run_name: str):
        self.info(f"Destroying TestRun: {run_name}")
        shutil.rmtree(self.test_runs[run_name].run_dir)
        del self.test_runs[run_name]

    def run_all(self):
        for run_name, run in self.test_runs.items():
            print(f"Running {run_name}")
            self.info(f"Running {run_name}")
            run.run()

    def count_errors(self) -> int:
        err_cnt = self.err_cnt

        for run_name, run in self.test_runs.items():
            err_cnt += run.err_cnt
            if run.err_cnt > 0:
                self.error(f"{run_name}: FAILED (Error Count: {run.err_cnt})")
            else:
                self.info(f"{run_name}: PASSED")

        return err_cnt

    def print_warnings(self):
        for s in self.warnings:
            print(f"\033[93mWarning: {s}\033[00m")
        for run_name, run in self.test_runs.items():
            if len(run.warnings) == 0:
                continue
            print(f"\t\033[93m{run_name} warnings\033[00m")
            run.print_warnings()

    def print_errors(self):
        for s in self.warnings:
            print(f"\033[91mError: {s}\033[00m")
            for run_name, run in self.test_runs.items():
                if len(run.errors) == 0:
                    continue
                print(f"\033[91m{run_name} errors\033[00m")
                run.print_errors()

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

